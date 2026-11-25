"""Compare legacy status with a counters-only evidence projection in Wiki_PG."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
TOOLS = ("biolatency", "biosnoop", "runqlat", "execsnoop", "tcpretrans")
STAMP = "2026-11-25T00:00:00Z"
MARKER = "syntheticprivatecoordinate"
CASES = {
    # Expected events, observed events, unrelated events, collector outcome, expected coverage.
    "confirmed": (40, 40, 0, "finished", "ok"),
    "startup_only": (40, None, 0, "finished", "unknown"),
    "empty": (40, 0, 0, "finished", "unknown"),
    "partial": (40, 39, 0, "finished", "unknown"),
    "extra": (40, 41, 0, "finished", "unknown"),
    "unrelated_event": (40, 40, 1, "finished", "unknown"),
    "unverified_zero": (0, 0, 0, "finished", "unknown"),
    "permission_denied": (40, None, 0, "permission_denied", "degraded"),
    "timeout": (40, 40, 0, "timeout", "degraded"),
}


def projected_status(expected, observed, unrelated, outcome):
    if outcome in {"permission_denied", "timeout"}:
        return outcome
    if observed == expected and expected > 0 and unrelated == 0:
        return "ok"
    return "empty_output" if observed == 0 else "completed_unverified"


def metadata(status):
    code = {"permission_denied": 1, "timeout": 124}.get(status, 0)
    return (f"<!-- collector status={status} exit_code={code} scope=BPF "
            f"started_at={STAMP} ended_at=2026-11-25T00:00:08Z -->\n")


def ingest(build, SystemQueries, search, status):
    with TemporaryDirectory() as temp:
        root = Path(temp)
        registry = root / "operations/clusters/registry.yaml"
        registry.parent.mkdir(parents=True)
        registry.write_text("clusters:\n  FixtureHost: fixture\n", encoding="utf-8")
        path = root / "raw/deep-report/fixture/FixtureHost/report.md"
        path.parent.mkdir(parents=True)
        parts = [f"**Collector version:** 3.2.0\n**Date:** {STAMP}\n## BPF\n"]
        for name in TOOLS:
            parts.append(f"#### {name}\n")
            if name == "execsnoop" and status is None:
                parts.append(f"Tracing events\nCollector arguments: {MARKER}\n")
            else:
                parts.append(metadata(status if name == "execsnoop" else "ok"))
        path.write_text("".join(parts), encoding="utf-8")
        build(root)
        query = SystemQueries(root)
        try:
            result = query.state("FixtureHost", dataset="diagnostics", scope="diagnostic",
                                 fields=["execsnoop"])
            item, = result["data"]
            coverage = result["coverage"]["deep-report"]["collection_status"]
        finally:
            query.close()
        chunks = search(root, MARKER, semantic=False)["chunks"]
        return {"tool_status": item["status"], "coverage": coverage,
                "search_retained_marker": any(MARKER in row["text"] for row in chunks)}


def replay(build, SystemQueries, search):
    baseline = ingest(build, SystemQueries, search, None)
    if baseline != {"tool_status": "ok", "coverage": "ok", "search_retained_marker": True}:
        raise AssertionError(baseline)
    rows = []
    for name, (expected, observed, unrelated, outcome, expected_coverage) in CASES.items():
        status = projected_status(expected, observed, unrelated, outcome)
        actual = ingest(build, SystemQueries, search, status)
        if actual != {"tool_status": status, "coverage": expected_coverage,
                      "search_retained_marker": False}:
            raise AssertionError((name, actual))
        rows.append({"case": name, "expected_events": expected, "observed_events": observed,
                     "unrelated_events": unrelated, "collector_outcome": outcome, **actual})
    return {"legacy_startup_with_marker": baseline, "projected_cases": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_pg_checkout", type=Path)
    source = parser.parse_args().wiki_pg_checkout.resolve()
    revision = subprocess.check_output(["git", "-C", source, "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", source, "status", "--porcelain"], text=True)
    if revision != REVISION or dirty:
        parser.error(f"Expected clean Wiki_PG checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "Wiki_PG" / "ingestion"))
    from build_system_store import build
    from evidence_search import search
    from system_queries import SystemQueries

    result = replay(build, SystemQueries, search)
    if result != replay(build, SystemQueries, search):
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_pg_revision": revision, "repeat_count": 2, "status": "PASS", **result},
                     indent=2))


if __name__ == "__main__":
    main()
