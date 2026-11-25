"""Replay explicitly linked synthetic documents through Wiki_PG's lexical search."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from unittest.mock import patch

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
AS_OF = "2026-11-25"
QUERY = "fixturequestion"
ORIGIN = "operations/origin.md"
TARGET = "operations/target.md"
DISTRACTOR = "operations/other.md"
LINK = re.compile(r"^\[Evidence\]\(([-a-z]+\.md)\)$", re.M)


class FixedClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 25, 12, tzinfo=tz)


def document(path, body, expiry="2026-12-01", update="2026-11-20", status="stable"):
    deadline = f"stale_after: {expiry}\n" if expiry else ""
    path.write_text(
        f"---\nstatus: {status}\n{deadline}updated_at: {update}\n"
        "verified:\n - by: human:fixture\n   at: 2026-11-21\n---\n"
        f"# Fixture\n{body}\n", encoding="utf-8",
    )


def case(build, search, scenario):
    with TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "operations").mkdir()
        (root / "raw").mkdir()
        expected_path = DISTRACTOR if scenario == "same_scope_wrong_target" else TARGET
        origin = root / ORIGIN
        target = root / TARGET
        document(origin, f"{QUERY}\n[Evidence]({PurePosixPath(expected_path).name})",
                 expiry=AS_OF if scenario == "expired_origin" else "2026-12-01")
        expiry = {"expired_target": AS_OF, "unknown_deadline": None}
        document(target, "fixtureevidence intended fact", expiry=expiry.get(scenario, "2026-12-01"),
                 update="2026-11-22" if scenario == "review_predates_revision" else "2026-11-20",
                 status="deprecated" if scenario == "deprecated_target" else "stable")
        document(root / DISTRACTOR, "fixtureevidence unrelated fact")
        build(root)
        if scenario == "edited_after_index":
            document(target, "fixtureevidence replacement")
        if scenario == "deleted_after_index":
            target.unlink()

        baseline = search(root, QUERY, semantic=False)["chunks"]
        links = [(row, link) for row in baseline if row["source_file"] == ORIGIN
                 for link in LINK.findall(row["text"])]
        if len(links) != 1:
            raise AssertionError("Expected exactly one link in the indexed origin")
        origin_row, link = links[0]
        path = (PurePosixPath(origin_row["source_file"]).parent / link).as_posix()
        if path != expected_path:
            raise AssertionError(f"Expected link to {expected_path}, got {path}")
        # The fixed term represents a target-section selector supplied with the link.
        result = search(root, "fixtureevidence", semantic=False, source_file=path)
        rows = result["chunks"]
        if len(rows) != 1 or rows[0]["source_file"] != path:
            raise AssertionError("Expected exactly one indexed target chunk")
        origin_quality = origin_row["knowledge_quality"]
        target_quality = rows[0]["knowledge_quality"]
        eligible = origin_quality["current_state_eligible"] and target_quality["current_state_eligible"]
        return {
            "case": scenario,
            "baseline_contains_intended_target": any(row["source_file"] == TARGET for row in baseline),
            "link_returns_indexed_chunk": bool(rows),
            "intended_target": rows[0]["source_file"] == TARGET,
            "eligible": eligible,
            "origin_freshness": origin_quality["freshness"],
            "target_freshness": target_quality["freshness"],
            "target_alignment": target_quality["source_alignment"],
            "target_review": target_quality["review"],
            "target_warning": f"curated_not_current:{path}" in result["warnings"],
        }


def replay(build, search):
    # Independent expectations fixed before retrieval. The last control is a deliberate false positive.
    expectations = {
        "current": (True, True, "within_declared_validity", "matched", "human_review_recorded"),
        "expired_target": (False, True, "expired", "matched", "human_review_recorded"),
        "unknown_deadline": (False, True, "unknown", "matched", "human_review_recorded"),
        "review_predates_revision": (False, True, "within_declared_validity", "matched", "human_review_predates_revision"),
        "deprecated_target": (False, True, "within_declared_validity", "matched", "human_review_recorded"),
        "edited_after_index": (False, True, "unknown", "changed", "unknown"),
        "deleted_after_index": (False, True, "unknown", "unverified", "unknown"),
        "expired_origin": (False, True, "within_declared_validity", "matched", "human_review_recorded"),
        "same_scope_wrong_target": (True, False, "within_declared_validity", "matched", "human_review_recorded"),
    }
    with patch("curated_quality.datetime", FixedClock):
        rows = [case(build, search, name) for name in expectations]
    for row in rows:
        name = row["case"]
        eligible, intended, freshness, alignment, review = expectations[name]
        expected_target_warning = not eligible and name != "expired_origin"
        expected_origin_freshness = "expired" if name == "expired_origin" else "within_declared_validity"
        observed = (row["eligible"], row["intended_target"], row["target_freshness"],
                    row["target_alignment"], row["target_review"], row["target_warning"],
                    row["origin_freshness"])
        if (observed != (eligible, intended, freshness, alignment, review, expected_target_warning,
                         expected_origin_freshness) or row["baseline_contains_intended_target"]
                or not row["link_returns_indexed_chunk"]):
            raise AssertionError(row)
    return rows


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("wiki_pg_checkout", type=Path)
    args = cli.parse_args()
    source = args.wiki_pg_checkout.resolve()
    revision = subprocess.check_output(["git", "-C", source, "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", source, "status", "--porcelain"], text=True)
    if revision != REVISION or dirty:
        cli.error(f"Expected clean Wiki_PG checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "Wiki_PG" / "ingestion"))
    from build_system_store import build
    from evidence_search import search

    first = replay(build, search)
    if first != replay(build, search):
        raise AssertionError("Repeat did not reproduce the first run")
    print(json.dumps({
        "wiki_pg_revision": REVISION, "as_of": AS_OF, "repeat_count": 2,
        "status": "PASS", "cases": first,
    }, indent=2))


if __name__ == "__main__":
    main()
