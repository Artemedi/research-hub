"""Check version and setting preservation on Wiki_PG's actual snapshot modules."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

from metrics_store import SQLiteMetricsStore
from structured_metrics import parse_sysconfig

TARGET = "d55721bb99bff25fae352341cfd630c048693d6b"
OLD = "io_workers"
NEW = ("io_min_workers", "io_max_workers", "io_worker_idle_timeout", "io_worker_launch_interval")
KEYS = (OLD, *NEW)
V18 = (180007, {OLD: "3"})
V19 = (190000, dict(zip(NEW, ("2", "8", "60000", "10"))))
FIXTURES = {
    "v18": ({"5432": V18}, ("present", *("not_in_major",) * 4)),
    "v19": ({"5432": V19}, ("not_in_major", *("present",) * 4)),
    "capture_gap": ({"5432": (190000, {NEW[0]: "2"})},
                    ("not_in_major", "present", *("missing_capture",) * 3)),
    "contradiction": ({"5432": (180007, {OLD: "3", NEW[0]: "2"})},
                      ("present", "inconsistent", *("not_in_major",) * 3)),
    "unknown": ({"5432": (None, {NEW[0]: "2"})}, ("unknown_major",) * 5),
    # The target scope is port 5432. Port 5433 has its own contrasting facts.
    "mixed_ports": ({"5432": V18, "5433": V19}, ("present", *("not_in_major",) * 4)),
}


def make_snapshot(instances, second):
    settings, runtime, expected = [], [], set()
    for port, (version, values) in instances.items():
        settings.append({"port": port, "settings": [
            {"name": key, "setting": value} for key, value in values.items()
        ]})
        identity = {"port": port}
        if version is not None:
            identity["server_version_num"] = version
            expected.add((port, "pg_instance", "server_version_num", str(version)))
        runtime.append(identity)
        expected.update((port, "pg_setting", key, value) for key, value in values.items())
    body = {
        "report_meta": {"timestamp_utc": f"2026-11-25T11:00:{second:02}Z"},
        "postgres_settings": {"instances": settings},
        "postgres_runtime": {"instances": runtime},
    }
    return json.dumps(body, sort_keys=True).encode(), expected


def classify(facts):
    version = facts.get(("pg_instance", "server_version_num"))
    major = int(version) // 10000 if version else None
    out = []
    for key in KEYS:
        seen = ("pg_setting", key) in facts
        applicable = (major == 18 and key == OLD) or (major == 19 and key in NEW)
        if major not in (18, 19):
            out.append("unknown_major")
        elif applicable:
            out.append("present" if seen else "missing_capture")
        else:
            out.append("inconsistent" if seen else "not_in_major")
    return tuple(out)


def run(repository):
    def git(*args):
        return subprocess.check_output(["git", "-C", repository, *args], text=True).strip()

    if git("rev-parse", "HEAD") != TARGET or git("status", "--porcelain"):
        raise ValueError("Use the clean, pinned Wiki_PG project.")

    runs = []
    for repeat in range(3):
        raw_ok = matched = port_mutant_errors = 0
        outcomes = Counter()
        baseline_ms = candidate_ms = 0.0
        with TemporaryDirectory(prefix="wiki-pg19-lab-") as directory:
            root = Path(directory)
            store = SQLiteMetricsStore(root / "metrics.sqlite3")
            try:
                for family, (instances, expected_status) in FIXTURES.items():
                    for second in range(5):
                        snapshot, expected_rows = make_snapshot(instances, second)
                        path = root / "raw/sysconfig-report/lab" / family / f"snapshot-{second}.json"
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(snapshot)
                        started = perf_counter()
                        parsed = parse_sysconfig(path, root)
                        if not store.write(parsed):
                            raise AssertionError("Fresh snapshot was refused")
                        rows = store.connection.execute(
                            """SELECT o.pg_port, o.scope, o.key, o.value_text, s.sha256
                               FROM observations o JOIN sources s USING(source_id)
                               WHERE s.source_id=? ORDER BY o.pg_port, o.scope, o.key""",
                            (parsed.source.source_id,),
                        ).fetchall()
                        baseline_ms += (perf_counter() - started) * 1000
                        digest = hashlib.sha256(snapshot).hexdigest()
                        recorded = {(port, scope, key, value) for port, scope, key, value, _ in rows}
                        raw_ok += recorded == expected_rows and {row[4] for row in rows} == {digest}
                        started = perf_counter()
                        scoped = {(scope, key): value for port, scope, key, value, _ in rows if port == "5432"}
                        actual = classify(scoped)
                        candidate_ms += (perf_counter() - started) * 1000
                        matched += sum(a == b for a, b in zip(actual, expected_status))
                        outcomes.update(actual)
                        unscoped = {(scope, key): value for _, scope, key, value, _ in rows}
                        port_mutant_errors += classify(unscoped) != expected_status
            finally:
                store.close()
        runs.append({
            "raw_snapshots_exact": raw_ok, "classifications_exact": matched,
            "port_mutant_failed_fixtures": port_mutant_errors, "classification_counts": outcomes,
            "timing_ms": {"parse_store_read": round(baseline_ms, 3), "classify": round(candidate_ms, 3)},
            "passed": raw_ok == 30 and matched == 150 and port_mutant_errors == 5,
        })
    print(json.dumps({
        "target": TARGET, "python": platform.python_version(), "fixture_families": list(FIXTURES),
        "snapshots_per_repeat": 30, "classifications_per_repeat": 150, "runs": runs,
    }, indent=2))
    return 0 if all(result["passed"] for result in runs) else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1]))
