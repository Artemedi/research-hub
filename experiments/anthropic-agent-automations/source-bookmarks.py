"""Offline comparison of source watermarks and publication acknowledgement."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

SOURCES = ("alpha", "beta")
CHANGES = (
    ("alpha", "A1", "open", 105, 106),
    ("alpha", "A2", "open", 108, 119),
    ("alpha", "A3", "open", 123, 123),
    ("alpha", "A-old", "open", 101, 129),
    ("beta", "B1", "open", 105, 105),
    ("beta", "B2", "open", 116, 129),
    ("alpha", "A1", "closed", 135, 135),
    ("alpha", "A1", "open", 145, 145),
)
RUNS = (
    (110, {"beta"}, "confirmed"),
    (120, set(), "missing_receipt"),
    (121, set(), "confirmed"),
    (124, set(), "dry_run"),
    (125, set(), "held"),
    (126, set(), "confirmed"),
    (130, set(), "confirmed"),
    (140, set(), "confirmed"),
    (150, set(), "confirmed"),
    (160, set(), "silence"),
)
COMMON = [("alpha", "A1", "open", 105), ("alpha", "A3", "open", 123),
          ("alpha", "A1", "closed", 135), ("alpha", "A1", "open", 145)]
EXPECTED = {
    "shared_no_overlap": set(COMMON),
    "per_source_no_overlap": set(COMMON) | {("beta", "B1", "open", 105)},
    "per_source_overlap_10": set(COMMON) | {
        ("beta", "B1", "open", 105), ("alpha", "A2", "open", 108),
        ("beta", "B2", "open", 116),
    },
}


def read_source(source, start, now, failed):
    if source in failed:
        # An API body can report failure even on a successful transport.
        return {"ok": False}
    visible = {}
    for origin, ident, status, changed, visible_at in sorted(CHANGES, key=lambda row: row[3]):
        if origin == source and changed <= now and visible_at <= now:
            visible[ident] = (source, ident, status, changed)
    return {"ok": True, "items": sorted(row for row in visible.values() if row[3] >= start)}


def prepare(state, now, failed, overlap):
    success = []
    selected = []
    fetched = 0
    for source in SOURCES:
        response = read_source(source, state["bookmarks"][source] - overlap, now, failed)
        if not response["ok"]:
            continue
        success.append(source)
        fetched += len(response["items"])
        for item in response["items"]:
            _, ident, status, _ = item
            if state["ledger"].get(f"{source}/{ident}") != status:
                selected.append(item)
    return success, selected, fetched


def publish(selected, mode, now, published):
    """Synthetic publication service with independent state for committed effects."""
    if mode == "dry_run":
        return {"status": "dry_run"}
    if mode == "held":
        return {"status": "held", "ok": False}
    if mode == "missing_receipt":
        return {"status": "unknown", "ok": True}
    if not selected:
        return {"status": "silence"}
    published.extend(selected)
    return {"status": "posted", "ok": True, "ts": f"fixture-{now}"}


def commit(state, now, success, selected, publication, shared):
    confirmed = publication.get("ok") is True and bool(publication.get("ts"))
    silent = publication["status"] == "silence" and not selected
    if not (confirmed or silent):
        return False
    for source in (SOURCES if shared and success else success):
        state["bookmarks"][source] = now
    for source, ident, status, _ in selected:
        state["ledger"][f"{source}/{ident}"] = status
    return True


def trial(path, arm):
    path.write_text(json.dumps({"bookmarks": dict.fromkeys(SOURCES, 100), "ledger": {}}),
                    encoding="utf-8")
    shared = arm == "shared_no_overlap"
    overlap = 10 if arm == "per_source_overlap_10" else 0
    published = []
    records = []
    for now, failed, mode in RUNS:
        previous = path.read_bytes()
        state = json.loads(previous)
        successful, selected, fetched = prepare(state, now, failed, overlap)
        publication = publish(selected, mode, now, published)
        applied = commit(state, now, successful, selected, publication, shared)
        if applied:
            path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        after = path.read_bytes()
        if mode in {"held", "dry_run", "missing_receipt"}:
            assert not applied and after == previous
        if failed and not shared:
            assert all(state["bookmarks"][source] == json.loads(previous)["bookmarks"][source]
                       for source in failed)
        records.append({
            "minute": now, "successful_sources": successful, "failed_sources": sorted(failed),
            "fetched": fetched, "proposed": selected, "publication": publication["status"],
            "state_committed": applied, "state_sha256": hashlib.sha256(after).hexdigest(),
            "bookmarks": state["bookmarks"],
        })

    assert len(published) == len(set(published)), (arm, published)
    assert set(published) == EXPECTED[arm], (arm, published)
    expected_events = {row[:4] for row in CHANGES}
    assert records[-1]["publication"] == "silence"
    assert records[-1]["bookmarks"] == dict.fromkeys(SOURCES, 160)
    return {
        "delivered": published, "missed": sorted(expected_events - set(published)),
        "fetched_total": sum(row["fetched"] for row in records),
        "duplicate_deliveries": len(published) - len(set(published)), "runs": records,
    }


def main():
    with TemporaryDirectory(prefix="synthetic-bookmarks-") as scratch:
        path = Path(scratch) / "bookmarks.json"
        results = {arm: trial(path, arm) for arm in EXPECTED}
        for _ in range(2):
            assert {arm: trial(path, arm) for arm in EXPECTED} == results
    print(json.dumps({
        "fixture_changes": CHANGES, "repeats": 3, "runs_per_arm": len(RUNS),
        "external_requests": 0, "results": results,
    }, indent=2))


if __name__ == "__main__":
    main()
