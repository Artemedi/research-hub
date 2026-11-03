#!/usr/bin/env python3
"""Verify pgbot 0.9.0 synthetic PostgreSQL state transitions from JSON snapshots."""
import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

parser = argparse.ArgumentParser(description=__doc__)
for key in ("baseline", "blocked", "fixed", "no_monitor", "schema", "overhead"):
    parser.add_argument("--" + key.replace("_", "-"), type=Path, required=True)
args = parser.parse_args()

schema = json.loads(args.schema.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)


def read_context(path):
    context = json.loads(path.read_text(encoding="utf-8"))
    errors = list(validator.iter_errors(context))
    if errors:
        raise AssertionError(f"{path}: JSON Schema violations: {errors[:3]}")
    assert context["schema_version"] == "1.5.0"
    return context


baseline = read_context(args.baseline)
blocked = read_context(args.blocked)
fixed = read_context(args.fixed)
no_monitor = read_context(args.no_monitor)
ids = lambda ctx: {finding["id"] for finding in ctx["findings"]}

assert baseline["server"]["has_pg_monitor"] is True
assert blocked["server"]["has_pg_monitor"] is True
assert fixed["server"]["has_pg_monitor"] is True
assert no_monitor["server"]["has_pg_monitor"] is False

assert "autovacuum_disabled_on_table" in ids(baseline)
assert "table_bloat" in ids(baseline)
assert baseline["locks"]["blocked_count"] == 0
assert blocked["locks"]["blocked_count"] >= 1
assert "blocking_chains" in ids(blocked)
assert fixed["locks"]["blocked_count"] == 0
assert "blocking_chains" not in ids(fixed)
assert "autovacuum_disabled_on_table" not in ids(fixed)
assert "table_bloat" not in ids(fixed)

overhead = json.loads(args.overhead.read_text(encoding="utf-8"))
assert len(overhead["times_ms"]) == 5
assert overhead["fixture_hash_same"] is True
assert overhead["counters_before"] == overhead["counters_after"]
assert overhead["schema_valid"] == 5

print(json.dumps({
    "status": "PASS",
    "schema_validated": 4,
    "initial_findings": len(baseline["findings"]),
    "blocked_count": blocked["locks"]["blocked_count"],
    "blocking_finding": "blocking_chains" in ids(blocked),
    "clean_blocked_count": fixed["locks"]["blocked_count"],
    "monitor_guard": not no_monitor["server"]["has_pg_monitor"],
    "repeated_inspects": 5,
    "median_wall_ms_including_podman": overhead["median_ms"],
    "dml_counters_unchanged": True,
    "fixture_checksum_unchanged": True,
}, ensure_ascii=False, indent=2))
