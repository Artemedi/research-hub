"""Measure what Wiki_PG's snapshot preserves from isolated PostgreSQL servers."""

import argparse
import csv
import importlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from types import SimpleNamespace
from unittest.mock import patch


TARGET = "d55721bb99bff25fae352341cfd630c048693d6b"
VERSIONS = (150019, 150020, 180006, 180007)
INVENTORY = """
SELECT c.relname, a.amname, o.opcname
FROM pg_index i
JOIN pg_class c ON c.oid = i.indexrelid
JOIN pg_am a ON a.oid = c.relam
JOIN pg_opclass o ON o.oid = i.indclass[0]
WHERE i.indrelid = 'public.documents'::regclass
ORDER BY c.relname;
"""


def docker(*args, sql=None, timeout=40, check=True):
    return subprocess.run(["docker", *args], input=sql, capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout, check=check)


def run_image(image, version, collector, parser, store_class):
    if not re.fullmatch(r"(?:docker.io/library/)?postgres@sha256:[0-9a-f]{64}", image):
        raise ValueError("Expected an official PostgreSQL image pinned by digest")

    container = docker("run", "--detach", "--pull=never", "--network=none", "--cpus=2",
                       "--memory=1g", "--env", "POSTGRES_HOST_AUTH_METHOD=trust", image,
                       "-c", "listen_addresses=").stdout.strip()
    try:
        def psql(db, sql, *options, check=True, timeout=30):
            return docker("exec", "-i", container, "psql", "-Xq", "-v", "ON_ERROR_STOP=1",
                          "-U", "postgres", "-d", db, *options, sql=sql, check=check, timeout=timeout)

        deadline = monotonic() + 45
        while monotonic() < deadline:
            if docker("exec", container, "cat", "/proc/1/comm", check=False).stdout.strip() == "postgres":
                result = psql("postgres", "SHOW server_version_num;", "-At", check=False)
                if result.returncode == 0:
                    break
            sleep(0.4)
        else:
            raise RuntimeError("PostgreSQL did not reach final startup")
        actual_version = int(result.stdout.strip())
        if actual_version != version:
            raise ValueError(f"Image returned {actual_version}, expected {version}")

        psql("postgres", "CREATE DATABASE lab_index; CREATE DATABASE lab_control;")
        for database in ("lab_index", "lab_control"):
            psql(database, "CREATE EXTENSION pg_trgm; CREATE TABLE documents(value text);")
        psql("lab_index", "CREATE INDEX trgm_gist ON documents USING gist(value gist_trgm_ops);")
        psql("lab_control", "CREATE INDEX trgm_gin ON documents USING gin(value gin_trgm_ops);")

        def collect_sql(port, sql, db=None, timeout=30):
            result = psql(db or "postgres", sql, "--csv", check=False, timeout=timeout)
            return list(csv.reader(io.StringIO(result.stdout))), result.stderr if result.returncode else None

        def collect_command(args):
            if args != ["psql", "--version"]:
                raise ValueError("Unexpected collector command")
            result = docker("exec", container, *args)
            return result.stdout.strip(), result.stderr, result.returncode

        with patch.multiple(collector, discover_pg_ports=lambda: [5432], psql_csv=collect_sql,
                            run_command=collect_command,
                            os=SimpleNamespace(path=SimpleNamespace(isdir=lambda _: False))):
            runtime = collector.gather_postgres_runtime(True)
        instance, = runtime["instances"]
        boards = instance["extensions_by_database"]
        installed = [[row for row in boards[db] if row["name"] == "pg_trgm"]
                     for db in ("lab_index", "lab_control")]
        if installed[0] != installed[1] or len(installed[0]) != 1 or installed[0][0]["state"] != "installed":
            raise AssertionError("Expected the same installed pg_trgm evidence in both databases")

        index = psql("lab_index", INVENTORY, "-At").stdout.strip()
        control = psql("lab_control", INVENTORY, "-At").stdout.strip()
        if (index, control) != ("trgm_gist|gist|gist_trgm_ops", "trgm_gin|gin|gin_trgm_ops"):
            raise AssertionError("The catalog did not distinguish the synthetic index and control")

        with TemporaryDirectory(prefix="wiki-pg-maintenance-") as directory:
            root = Path(directory)
            source = root / "raw/sysconfig-report/lab/host/runtime.json"
            source.parent.mkdir(parents=True)
            source.write_text(json.dumps({"report_meta": {"timestamp_utc": "2026-11-25T00:00:00Z"},
                                          "postgres_runtime": runtime}), encoding="utf-8")
            store = store_class(root / "observations.sqlite3")
            try:
                if not store.write(parser(source, root)):
                    raise AssertionError("Fresh observation snapshot rejected")
                retained = store.connection.execute(
                    "SELECT pg_port, value_text FROM observations WHERE scope='pg_instance' AND key='server_version_num'"
                ).fetchall()
                keys = store.connection.execute("SELECT DISTINCT scope, key FROM observations").fetchall()
            finally:
                store.close()
        if retained != [("5432", str(actual_version))] or any("extension" in part or "index" in part for row in keys for part in row):
            raise AssertionError("Unexpected version or extension/index coverage in SQLite")
        return dict(image=image, server_version_num=actual_version, version_in_sqlite=True,
                    same_pg_trgm_in_raw=True, extension_or_index_in_structured_observations=False,
                    catalog_gist=True, catalog_gin_control=True)
    finally:
        docker("rm", "-fv", container)


def main():
    argument = argparse.ArgumentParser(description=__doc__)
    argument.add_argument("wiki_pg_checkout", type=Path)
    argument.add_argument("images", nargs=len(VERSIONS), help="Pinned images in order 15.19 15.20 18.6 18.7")
    args = argument.parse_args()
    source = args.wiki_pg_checkout.resolve()
    git = ["git", "-C", str(source)]
    if subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != TARGET:
        raise ValueError("Use the pinned Wiki_PG checkout")
    if subprocess.check_output([*git, "status", "--porcelain"], text=True).strip():
        raise ValueError("Use a clean Wiki_PG checkout")
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(source / "Scripts"), str(source / "Wiki_PG/ingestion")]
    collector = importlib.import_module("sysconfig_gather")
    parser = importlib.import_module("structured_metrics").parse_sysconfig
    store = importlib.import_module("metrics_store").SQLiteMetricsStore
    results = [run_image(image, version, collector, parser, store) for image, version in zip(args.images, VERSIONS)]
    sys.stdout.buffer.write((json.dumps(dict(wiki_pg_commit=TARGET, results=results), indent=2) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
