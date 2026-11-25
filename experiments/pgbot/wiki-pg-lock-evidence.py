"""Compare PGBot and Wiki_PG lock evidence on disposable PostgreSQL instances."""

import argparse
from contextlib import ExitStack
from hashlib import file_digest
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
ARCHIVE_SHA = "adf0f08fbdd212a8c6b1e0462f872916866968c25e6e35ba1b5bba22a39841bc"
IMAGES = {
    "15.20": "sha256:91b9edc40277faf94bc1e3d7ae621b185fa70f3099b94309c4731a8296114870",
    "18.3": "sha256:7e32e9833a6fb1c92c32552794cb6ed569d51b445a54907d35fc112ef39684db",
}
ORACLE = """SELECT count(*) || '|' || coalesce(sum(cardinality(pg_blocking_pids(pid))), 0)
            FROM pg_stat_activity WHERE application_name='fixture_waiter'
            AND cardinality(pg_blocking_pids(pid)) > 0"""
# The lock section's projection from Scripts/SystemReport.sh, without query text.
LOCK_EDGES = """SELECT blocked.pid AS blocked_pid, blocker.pid AS blocking_pid
                FROM pg_stat_activity blocked
                CROSS JOIN LATERAL unnest(pg_blocking_pids(blocked.pid)) AS b(blocking_pid)
                JOIN pg_stat_activity blocker ON blocker.pid = b.blocking_pid
                WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0"""


def command(*args):
    return subprocess.check_output(args, text=True, timeout=35).strip()


def psql(container, sql, role="postgres", csv=False):
    return command("docker", "exec", container, "psql", "-Xq", "-v", "ON_ERROR_STOP=1",
                   "--csv" if csv else "-At", "-U", role, "-d", "lab", "-c", sql)


def wait_for(predicate):
    for _ in range(60):
        if predicate():
            return
        time.sleep(0.1)
    raise RuntimeError("Disposable database did not reach the expected state")


def session(container, stack, name, sql):
    process = stack.enter_context(subprocess.Popen(
        ["docker", "exec", "-i", "-e", f"PGAPPNAME={name}", container,
         "psql", "-Xq", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "lab"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    ))
    process.stdin.write(sql + "\n")
    process.stdin.flush()
    return process


def wiki_report(reporting, csv_rows):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        state = reporting.begin(root, None)
        name = "raw/deep-report/fixture/FixtureHost/FixtureHost_pg_deep_report_2026-11-25_00-00-00.md"
        path = root / name
        path.parent.mkdir(parents=True)
        path.write_text("## A. PostgreSQL\n### Инстанс на порту 5432\n"
                        "#### Блокировки: кто кого блокирует прямо сейчас (pg_blocking_pids)\n"
                        f"```csv\n{csv_rows}\n```\n", encoding="utf-8")
        events = root / "events/processed_index.jsonl"
        events.parent.mkdir(exist_ok=True)
        events.write_text(json.dumps({"file": name}) + "\n", encoding="utf-8")
        report = reporting.finish(root, state, 0, '{"step":"fixture"}')
        output = root / reporting.publish(root, report) / "report.json"
        stored = json.loads(output.read_text(encoding="utf-8"))
        diagnostic, = stored["diagnostics"]
        if diagnostic["source_file"] != name or diagnostic["captured_at"] != "2026-11-25T00:00:00":
            raise AssertionError("Wiki_PG did not retain the fixture observation source and timestamp")
        host, = stored["host_state"]
        instance, = host["instances"]
        return instance


def collect(container, reporting, expected, phase):
    oracle = psql(container, ORACLE)
    csv_rows = psql(container, LOCK_EDGES, role="pgbot_ro", csv=True)
    pgbot = json.loads(command("docker", "exec", container, "/tmp/pgbot", "inspect",
                               "host=/var/run/postgresql dbname=lab user=pgbot_ro",
                               "--json", "--no-store", "--interval", "500ms", "--window", "1s",
                               "--ash-hz", "0", "--fail-on", "none"))
    if psql(container, ORACLE) != oracle:
        raise AssertionError("Lock state changed during observation")
    sessions, edges = map(int, oracle.split("|"))
    if (sessions, edges) != expected or not pgbot["server"]["has_pg_monitor"]:
        raise AssertionError("Incomplete or unexpected fixture")
    instance = wiki_report(reporting, csv_rows)
    state = instance["state"]
    wiki_finding = any(row["rule_id"] == "pg.locks.blocked.dba_baseline"
                       for row in instance["flags"])
    pgbot_finding = any(row["id"] == "blocking_chains" for row in pgbot["findings"])
    count = pgbot["locks"]["blocked_count"]
    if (pgbot_finding, wiki_finding) != (bool(sessions), bool(sessions)) or state["blocked_sessions"] != edges:
        raise AssertionError("Lock finding or Wiki_PG row count was inconsistent")
    if count not in {sessions, edges}:
        raise AssertionError("PGBot count disagrees with both oracle units")
    return {"phase": phase, "oracle_blocked_sessions": sessions, "oracle_wait_edges": edges,
            "wiki_blocked_sessions": state["blocked_sessions"], "pgbot_blocked_count": count,
            "wiki_lock_finding": wiki_finding, "pgbot_lock_finding": pgbot_finding,
            "wiki_source_and_capture_retained": True}


def blocked(container, reporting, holders):
    with ExitStack() as stack:
        owners, waiter = [], None
        try:
            for _ in range(holders):
                owners.append(session(container, stack, "fixture_owner",
                                      "BEGIN; LOCK TABLE public.fixture IN ACCESS SHARE MODE;"))
            expected = f"1|{holders}"
            wait_for(lambda: psql(container, """
                SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a USING(pid)
                WHERE a.application_name='fixture_owner' AND l.granted
                  AND l.relation='public.fixture'::regclass AND l.mode='AccessShareLock'""") == str(holders))
            waiter = session(container, stack, "fixture_waiter",
                             "BEGIN; LOCK TABLE public.fixture IN ACCESS EXCLUSIVE MODE; ROLLBACK;")
            wait_for(lambda: psql(container, ORACLE) == expected)
            return collect(container, reporting, (1, holders), f"{holders}_blocker")
        finally:
            for child in (*owners, *([waiter] if waiter is not None else [])):
                try:
                    child.communicate("ROLLBACK;\n", timeout=8)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate()


def trial(version, image, binary, reporting):
    container = command("docker", "run", "--detach", "--rm", "--name", "research-hub-pgbot-" + uuid4().hex[:12],
                        "--pull", "never", "--network", "none", "--memory", "512m", "--cpus", "1", "--pids-limit", "120",
                        "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-e", "POSTGRES_DB=lab", image)
    try:
        wait_for(lambda: subprocess.run(["docker", "exec", container, "pg_isready", "-h", "127.0.0.1", "-d", "lab"],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5).returncode == 0)
        major, minor = map(int, version.split("."))
        if int(psql(container, "SHOW server_version_num")) != major * 10000 + minor:
            raise AssertionError("Wrong PostgreSQL image")
        psql(container, "CREATE ROLE pgbot_ro LOGIN; GRANT pg_monitor TO pgbot_ro; "
             "ALTER ROLE pgbot_ro SET default_transaction_read_only TO on; "
             "ALTER ROLE pgbot_ro SET statement_timeout TO 15000; CREATE TABLE public.fixture (id integer)")
        command("docker", "cp", str(binary), container + ":/tmp/pgbot")
        command("docker", "exec", container, "chmod", "700", "/tmp/pgbot")
        return [collect(container, reporting, (0, 0), "baseline"),
                blocked(container, reporting, 1), blocked(container, reporting, 2),
                collect(container, reporting, (0, 0), "recovered")]
    finally:
        command("docker", "stop", "--timeout", "4", container)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_checkout", type=Path)
    parser.add_argument("pgbot_archive", type=Path)
    args = parser.parse_args()
    wiki = args.wiki_checkout.resolve()
    git = ("git", "-C", str(wiki))
    if command(*git, "rev-parse", "HEAD") != REVISION or command(*git, "status", "--porcelain"):
        parser.error(f"Expected clean Wiki_PG checkout at {REVISION}")
    with args.pgbot_archive.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != ARCHIVE_SHA:
            parser.error("PGBot archive SHA-256 did not match")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(wiki / "Wiki_PG/ingestion"))
    import ingestion_report as reporting

    with TemporaryDirectory() as folder:
        binary = Path(folder) / "pgbot"
        with tarfile.open(args.pgbot_archive) as archive, binary.open("wb") as target:
            member = archive.getmember("pgbot")
            if not member.isfile():
                raise ValueError("Expected a regular PGBot binary")
            with archive.extractfile(member) as source:
                shutil.copyfileobj(source, target)
        rows = {version: trial(version, image, binary, reporting) for version, image in IMAGES.items()}
        if rows != {version: trial(version, image, binary, reporting) for version, image in IMAGES.items()}:
            raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "pgbot_archive_sha256": ARCHIVE_SHA,
                      "postgres_images": IMAGES, "repeat_count": 2, "versions": rows}, indent=2))


if __name__ == "__main__":
    main()
