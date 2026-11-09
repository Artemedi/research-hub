#!/usr/bin/env python3
"""Independent deterministic fixture and numerical audit for Hyperresearch holdout.

No model calls or upstream classifier import. Synthetic data rules are checked
independently of the runner's verdicts; not a human semantic gold-label audit.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

CATEGORIES = (
    "exact_support", "reordered_support", "temporal_reversal",
    "scope_expansion", "missing_authorization", "unsupported_conjunction", "unrelated",
)
AGENTS = ("Nova", "Orion", "Vega", "Lyra")
NOUNS = ("audit events", "routing decisions", "failure records")
PIN = "aece65f9307197119629beacf8aeaf8cc80e999a"
SOURCE_SHA = "53405db780de66866e8b3131f7a99edc1341832095fcc7b0888eaae69684a465"

def verify(result):
    assert result["study"] == "hyperresearch"
    assert result["source_commit"] == PIN and result["source_file_sha256"] == SOURCE_SHA
    records = result["records"]
    assert len(records) == len(AGENTS) * len(NOUNS) * len(CATEGORIES) == 84
    observed = Counter()
    cat_counts = Counter()
    for i, record in enumerate(records):
        actor = AGENTS[i // (len(NOUNS) * len(CATEGORIES))]
        noun = NOUNS[(i // len(CATEGORIES)) % len(NOUNS)]
        cat = CATEGORIES[i % len(CATEGORIES)]
        note = "source_" + actor.lower() + "_" + noun.replace(" ", "_")
        baseline = (f"The {actor} scheduler records verified {noun} before nightly reconciliation"
                    " for internal tenants with a signed token.")
        # Textual oracle independently derives each mutation from baseline facts.
        expected = {
            "exact_support": baseline,
            "reordered_support": (f"For internal tenants with a signed token, the {actor} scheduler"
                                  f" records verified {noun} before nightly reconciliation."),
            "temporal_reversal": baseline.replace(" before nightly ", " after nightly "),
            "scope_expansion": baseline.replace(" for internal tenants ", " for external tenants "),
            "missing_authorization": baseline.replace(" with a signed token.", " without a signed token."),
            "unsupported_conjunction": baseline[:-1] + " and encrypts every payload automatically.",
            "unrelated": "A separate blue notebook reports weather for field operators.",
        }
        assert record["id"] == note + ":" + cat
        assert record["actor"] == actor and record["noun"] == noun
        assert record["note_id"] == note and record["category"] == cat
        assert record["source_claim"] == baseline and record["sentence"] == expected[cat]
        supported = cat in ("exact_support", "reordered_support")
        assert record["gold_supported"] is supported
        source_verdict = record["source_verdict"]
        exact_verdict = record["exact_only_verdict"]
        assert source_verdict in ("supported-mechanical", "needs-llm")
        assert exact_verdict in ("supported-mechanical", "needs-llm")
        # Exact-only oracle is independent from runner's normalization.
        expected_exact = ("supported-mechanical" if cat == "exact_support" else "needs-llm")
        assert exact_verdict == expected_exact
        assert record["unsafe_auto_support"] is (not supported and source_verdict == "supported-mechanical")
        assert record["exact_only_unsafe"] is False
        observed["cases"] += 1
        observed["synthetic_supported" if supported else "synthetic_unsupported"] += 1
        observed["source_unsupported_auto_pass"] += int(not supported and source_verdict == "supported-mechanical")
        observed["source_supported_auto_pass"] += int(supported and source_verdict == "supported-mechanical")
        observed["exact_only_unsupported_auto_pass"] += int(not supported and exact_verdict == "supported-mechanical")
        observed["exact_only_supported_auto_pass"] += int(supported and exact_verdict == "supported-mechanical")
        cat_counts[cat + "/" + source_verdict] += 1
    assert dict(observed) == result["totals"]
    assert dict(cat_counts) == result["category_verdicts"]
    assert observed["cases"] == 84
    assert observed["source_unsupported_auto_pass"] == 48
    assert observed["exact_only_unsupported_auto_pass"] == 0
    assert observed["source_supported_auto_pass"] == 24
    assert observed["exact_only_supported_auto_pass"] == 12
    # Four contradictory classes auto-pass while unrelated negatives do not.
    for cat in ("temporal_reversal", "scope_expansion", "missing_authorization", "unsupported_conjunction"):
        assert cat_counts[cat + "/supported-mechanical"] == 12
    assert cat_counts["unrelated/needs-llm"] == 12
    return {
        "status": "PASS", "validated_cases": len(records),
        "nonsemantic_independence": "Independent fixture reconstruction and arithmetic; synthetic gold labels authored, not a blinded expert review.",
        "counts": dict(observed), "category_verdicts": dict(sorted(cat_counts.items())),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    obj = json.loads(raw)
    valid = verify(obj)
    valid["input_sha256"] = hashlib.sha256(raw).hexdigest()
    # Deliberately wrong fixture and source verdict must fail closed.
    mutated = json.loads(raw)
    mutated["records"][0]["gold_supported"] = False
    try:
        verify(mutated)
    except AssertionError:
        valid["mutated_gold_rejected"] = True
    else:
        raise AssertionError("FAIL_OPEN mutated gold")
    mutated = json.loads(raw)
    mutated["records"][2]["source_verdict"] = "needs-llm"
    try:
        verify(mutated)
    except AssertionError:
        valid["mutated_verdict_rejected"] = True
    else:
        raise AssertionError("FAIL_OPEN mutated verdict")
    mutated = json.loads(raw)
    mutated["records"][3]["sentence"] += "NOT IN SOURCE"
    try:
        verify(mutated)
    except AssertionError:
        valid["mutated_fixture_rejected"] = True
    else:
        raise AssertionError("FAIL_OPEN mutated fixture")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(valid, indent=2, ensure_ascii=False) + "\n")
    print("INDEPENDENT_HOLDOUT_ORACLE", valid["status"], valid["validated_cases"],
          valid["counts"]["source_unsupported_auto_pass"], "bad cases and 3 mutants rejected")

if __name__ == "__main__":
    main()
