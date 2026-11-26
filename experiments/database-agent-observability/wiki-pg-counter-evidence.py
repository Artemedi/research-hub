"""Compare snapshot deltas and time-scoped event evidence on synthetic histories."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
START, END = "2026-11-25T00:00:00Z", "2026-11-25T00:01:00Z"
MIDDLE = "2026-11-25T00:00:30Z"
SCOPE = ("host", "port", "database")
CASES = {
    # Sample changes, event changes (None means absent), expected native status and replay decision.
    "matched": ({}, {}, "measured", "corroborated"),
    "right_boundary": ({}, {"time": END}, "measured", "corroborated"),
    "no_record": ({}, None, "measured", "no_matching_record"),
    "left_boundary": ({}, {"time": START}, "measured", "no_matching_record"),
    "future_record": ({}, {"time": "2026-11-25T00:02:00Z"}, "measured", "no_matching_record"),
    "other_host": ({}, {"host": "other"}, "measured", "no_matching_record"),
    "other_port": ({}, {"port": 5433}, "measured", "no_matching_record"),
    "other_database": ({}, {"database": "other"}, "measured", "no_matching_record"),
    "reset": ({"stats_reset": MIDDLE}, {}, "reset", "unusable_counter"),
    "incompatible_samples": ({"port": 5433}, {}, "incompatible", "unusable_counter"),
    "missing_reset_clock": ({"stats_reset": None}, {}, "unavailable", "unusable_counter"),
    "no_growth": ({"growth": 0}, {}, "measured", "no_counter_increase"),
}


def corroborate(before, after, measurement, events):
    if measurement["status"] != "measured":
        return None, "unusable_counter"
    if measurement["delta"] <= 0:
        return None, "no_counter_increase"
    start, end = (datetime.fromisoformat(row["captured_at"]) for row in (before, after))
    matched = [row for row in events if row["kind"] == "deadlock"
               and all(row[key] == after[key] for key in SCOPE)
               and start < datetime.fromisoformat(row["time"]) <= end]
    if not matched:
        return None, "no_matching_record"
    return [row["id"] for row in matched], "corroborated"


def replay(measure):
    rows = []
    for seed in (0, 4, 11, 24):
        before = {"captured_at": START, "stats_reset": "2026-11-24T00:00:00Z",
                  "host": "FixtureHost", "port": 5432, "database": "fixture",
                  "metric": "deadlocks", "unit": "events", "postgres_version": 18, "value": seed}
        event = {key: before[key] for key in SCOPE}
        event.update(id=f"fixture-deadlock-{seed}", time=MIDDLE, kind="deadlock")
        for name, (sample_changes, event_changes, status, decision) in CASES.items():
            changes = dict(sample_changes)
            growth = changes.pop("growth", 3)
            after = {**before, "captured_at": END, "value": seed + growth, **changes}
            events = [] if event_changes is None else [{**event, **event_changes}]
            measurement = measure(before, after)
            ids, actual = corroborate(before, after, measurement, events)
            if (measurement["status"], actual) != (status, decision):
                raise AssertionError((seed, name, measurement, actual))
            if status == "measured" and (measurement["delta"], measurement["rate"], measurement["norm_status"]) != (
                    growth, growth / 60, "not_calibrated"):
                raise AssertionError("Native counter no longer matches the arithmetic oracle")
            if ids != ([event["id"]] if decision == "corroborated" else None):
                raise AssertionError("Event linkage does not match the fixture")
            rows.append({"case": name, "initial_value": seed, "numbers_increased": after["value"] > before["value"],
                         "native_status": status, "native_delta": measurement.get("delta"),
                         "record_decision": actual, "corroborated_record_ids": ids})
    return rows


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("wiki_checkout", type=Path)
    source = cli.parse_args().wiki_checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        cli.error(f"Expected clean Wiki_PG checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "Wiki_PG/ingestion"))
    from interval_checks import measure

    rows = replay(measure)
    if any(rows != replay(measure) for _ in range(2)):
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "repeat_count": 3, "status": "PASS",
                      "cases_per_repeat": len(rows), "cases": rows}, indent=2))


if __name__ == "__main__":
    main()
