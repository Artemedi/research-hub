"""Replay retained, corrected and withdrawn snapshots across Wiki_PG generations."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
HOST, PEER, ALIAS = "FixtureAlpha", "FixtureBeta", "fixture-alpha-alias"
EARLY, LATE = "2026-11-23T00:00:00Z", "2026-11-25T00:00:00Z"
FIELD = ["memory.total_ram"]


def snapshot(root, host, stamp, value):
    directory = root / "raw" / "sysconfig-report" / "fixture" / host
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (stamp.replace(":", "-") + ".json")
    path.write_text(json.dumps({
        "report_meta": {"timestamp_utc": stamp, "script_version": "fixture"},
        "memory": {"total_ram": value},
    }), encoding="utf-8")
    return path


def read(query, host, **kwargs):
    result = query.state(host, fields=FIELD, **kwargs)
    sources = {row["source_id"]: row for row in result["sources"]}
    return [{"value": row["value_num"], "observed_at": sources[row["source_id"]]["observed_at"],
             "source": sources[row["source_id"]]["source_file"],
             "sha256": sources[row["source_id"]]["sha256"]} for row in result["data"]]


def expected(root, path, value, stamp):
    return {"value": value, "observed_at": stamp, "source": path.relative_to(root).as_posix(),
            "sha256": sha256(path.read_bytes()).hexdigest()}


def check(query, rows):
    history = dict(mode="history", after=EARLY, before="2026-11-26T00:00:00Z")
    if read(query, HOST, **history) != rows or read(query, ALIAS) != rows[:1]:
        raise AssertionError("Host history or alias disagrees with the fixture")
    if read(query, HOST, at=EARLY) != rows[-1:]:
        raise AssertionError("Earlier observation changed after a later update")


def stage(build, Query, root, old, initial, name, fresh, incremental, wanted_state):
    updated = build(root)
    if updated["state"] != wanted_state or updated["parse_errors"]:
        raise AssertionError((name, updated))
    query = Query(root)
    try:
        check(query, incremental)
        check(old, initial)
        current_generation = query.generation
    finally:
        query.close()
    with TemporaryDirectory() as directory:
        full_root = Path(directory)
        for subdirectory in ("raw", "operations"):
            shutil.copytree(root / subdirectory, full_root / subdirectory)
        if build(full_root)["state"] != "complete":
            raise AssertionError("Independent full rebuild failed")
        clean = Query(full_root)
        try:
            check(clean, fresh)
        finally:
            clean.close()
    if (current_generation == old.generation) != (name == "initial"):
        raise AssertionError("Unexpected generation relationship")
    return {"phase": name, "index_state": updated["state"], "incremental_latest": incremental[0]["value"],
            "fresh_latest": fresh[0]["value"], "open_reader_latest": initial[0]["value"],
            "incremental_history": incremental, "fresh_history": fresh}


def trial(build, Query, base):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        registry = root / "operations/clusters/registry.yaml"
        registry.parent.mkdir(parents=True)
        registry.write_text(f"clusters:\n  {HOST}: fixture\n  {PEER}: fixture\n"
                            f"aliases:\n  {ALIAS}: {HOST}\n", encoding="utf-8")
        early = snapshot(root, HOST, EARLY, base)
        late = snapshot(root, HOST, LATE, base + 1)
        retained = expected(root, early, base, EARLY)
        original = [expected(root, late, base + 1, LATE), retained]
        build(root)
        old = Query(root)
        try:
            rows = [stage(build, Query, root, old, original, "initial", original, original, "unchanged")]
            snapshot(root, PEER, LATE, base + 300)
            rows.append(stage(build, Query, root, old, original, "interference", original, original, "complete"))
            snapshot(root, HOST, LATE, base + 100)
            amended = [expected(root, late, base + 100, LATE), retained]
            rows.append(stage(build, Query, root, old, original, "changed_size", amended, amended, "complete"))
            stat = late.stat()
            snapshot(root, HOST, LATE, base + 101)
            os.utime(late, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            now = late.stat()
            if (stat.st_mtime_ns, stat.st_size) != (now.st_mtime_ns, now.st_size):
                raise AssertionError("Fixture could not preserve size and timestamp")
            hidden = [expected(root, late, base + 101, LATE), retained]
            rows.append(stage(build, Query, root, old, original, "same_size_and_mtime", hidden, amended, "unchanged"))
            snapshot(root, PEER, EARLY, base + 301)
            rows.append(stage(build, Query, root, old, original, "next_visible_update", hidden, hidden, "complete"))
            late.unlink()
            rows.append(stage(build, Query, root, old, original, "withdrawn", [retained], [retained], "complete"))
            return rows
        finally:
            old.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_checkout", type=Path)
    source = parser.parse_args().wiki_checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        parser.error(f"Expected clean Wiki_PG checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "Wiki_PG/ingestion"))
    from build_system_store import build
    from system_queries import SystemQueries

    rows = {base: trial(build, SystemQueries, base) for base in (11, 24, 63)}
    if rows != {base: trial(build, SystemQueries, base) for base in rows}:
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "repeat_count": 2, "status": "PASS_WITH_OBSERVED_LIMIT",
                      "fixtures": rows}, indent=2))


if __name__ == "__main__":
    main()
