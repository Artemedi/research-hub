"""Compare a reversible, source-bound feedback index against native Wiki_PG search."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
TARGET, DISTRACTOR = "operations/measurement.md", "operations/unrelated.md"
KEYS = ("source_file", "sha256", "location", "text")
META = """---
status: stable
updated_at: 2020-01-01
stale_after: 2099-01-01
verified:
 - by: human:fixture
   at: 2020-01-02
---
"""
OUTCOMES = {
    "approved_alias": (False, True, "recalled"),
    "direct_query": (True, True, "baseline"),
    "unreviewed_feedback": (False, False, "no_confirmed_binding"),
    "conflicting_feedback": (False, False, "ambiguous"),
    "source_changed_after_index": (False, False, "stale_binding"),
}


def identity(chunk):
    return {key: chunk[key] for key in KEYS}


def retrieve(search, root, query, alias, sidecar):
    baseline = search(root, query, semantic=False)["chunks"]
    if baseline or not sidecar.exists():
        return baseline, "baseline"
    bindings = [item for item in json.loads(sidecar.read_text(encoding="utf-8"))
                if item["alias"] == alias and item["approved"]]
    if not bindings:
        return baseline, "no_confirmed_binding"
    if len(bindings) != 1:
        return baseline, "ambiguous"
    binding = bindings[0]
    evidence = search(root, binding["lookup"], semantic=False,
                      source_file=binding["evidence"]["source_file"])["chunks"]
    current = [chunk for chunk in evidence if identity(chunk) == binding["evidence"]
               and chunk["knowledge_quality"]["current_state_eligible"]]
    return (current, "recalled") if len(current) == 1 else (baseline, "stale_binding")


def binding(search, root, alias, lookup, approved):
    source, = search(root, lookup, semantic=False)["chunks"]
    if not source["knowledge_quality"]["current_state_eligible"]:
        raise AssertionError("Initial synthetic source is not eligible")
    return {"alias": alias, "lookup": lookup, "approved": approved, "evidence": identity(source)}


def sources(root):
    return {name: sha256((root / name).read_bytes()).hexdigest() for name in (TARGET, DISTRACTOR)}


def signature(chunks):
    return [identity(chunk) for chunk in chunks]


def trial(build, search, seed):
    with TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "raw").mkdir()
        (root / "operations").mkdir()
        alias, lookup, unrelated = f"shortcut{seed}", f"measurement{seed}", f"inventory{seed}"
        (root / TARGET).write_text(META + f"# Observation\n{lookup} calibration value {seed}.\n", encoding="utf-8")
        (root / DISTRACTOR).write_text(META + f"# Observation\n{unrelated} warehouse value {seed}.\n", encoding="utf-8")
        build(root)
        accepted = binding(search, root, alias, lookup, True)
        conflicting = binding(search, root, alias, unrelated, True)
        if (accepted["evidence"]["source_file"], conflicting["evidence"]["source_file"]) != (TARGET, DISTRACTOR):
            raise AssertionError("Fixture returned unexpected source paths")
        sidecar = root / "derived-feedback.json"
        rows = []
        for case, expected in OUTCOMES.items():
            query = f"please retrieve {alias}" if case != "direct_query" else lookup
            entries = [accepted]
            if case == "unreviewed_feedback":
                entries = [{**accepted, "approved": False}]
            if case == "conflicting_feedback":
                entries = [accepted, conflicting]
            if case == "source_changed_after_index":
                (root / TARGET).write_text(META + f"# Observation\n{lookup} corrected value {seed + 1}.\n",
                                           encoding="utf-8")
                indexed, = search(root, lookup, semantic=False, source_file=TARGET)["chunks"]
                if indexed["knowledge_quality"]["source_alignment"] != "changed":
                    raise AssertionError("The stale-source control did not reproduce")
            before = sources(root)
            baseline = search(root, query, semantic=False)["chunks"]
            sidecar.write_text(json.dumps(entries), encoding="utf-8")
            actual, reason = retrieve(search, root, query, alias, sidecar)
            if (bool(baseline), bool(actual), reason) != expected:
                raise AssertionError((seed, case, bool(baseline), bool(actual), reason))
            if actual and signature(actual) != [accepted["evidence"]]:
                raise AssertionError("Feedback returned a different source or excerpt")
            sidecar.unlink()
            rollback, _ = retrieve(search, root, query, alias, sidecar)
            if signature(rollback) != signature(baseline) or sources(root) != before:
                raise AssertionError("Rollback or source preservation failed")
            rows.append({"case": case, "baseline_hit": bool(baseline), "feedback_hit": bool(actual),
                         "reason": reason, "rollback_restored_baseline": True, "source_bytes_preserved": True})
        return {"fixture": seed, "cases": rows}


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
    from evidence_search import search

    fixtures = (2, 11, 19, 23, 39, 47)
    rows = [trial(build, search, seed) for seed in fixtures]
    if any(rows != [trial(build, search, seed) for seed in fixtures] for _ in range(2)):
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "repeat_count": 3, "status": "PASS", "fixtures": rows}, indent=2))


if __name__ == "__main__":
    main()
