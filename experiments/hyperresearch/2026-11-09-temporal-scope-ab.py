#!/usr/bin/env python3
"""Frozen synthetic temporal/scope citation corpus against original pinned triage."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import types

PIN = "aece65f9307197119629beacf8aeaf8cc80e999a"
SOURCE_SHA = "53405db780de66866e8b3131f7a99edc1341832095fcc7b0888eaae69684a465"
AGENTS = ("Nova", "Orion", "Vega", "Lyra")
NOUNS = ("audit events", "routing decisions", "failure records")
CATEGORIES = (
    "exact_support", "reordered_support", "temporal_reversal",
    "scope_expansion", "missing_authorization", "unsupported_conjunction", "unrelated",
)

def load_upstream(src):
    assert subprocess.check_output(
        ["git", "-C", str(src), "rev-parse", "HEAD"], text=True
    ).strip() == PIN
    path = src / "src/hyperresearch/core/citecheck.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SOURCE_SHA
    for name in ("hyperresearch", "hyperresearch.core", "hyperresearch.core.fetcher",
                 "hyperresearch.core.patterns", "hyperresearch.core.scholar"):
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    sys.modules["hyperresearch.core.fetcher"].existing_live_note_for_url = lambda *x: None
    sys.modules["hyperresearch.core.patterns"].WIKI_LINK_RE = re.compile(
        r"\[\[([^\]\[|]+)(?:\|[^\]\[]+)?\]\](?!\()"
    )
    sys.modules["hyperresearch.core.patterns"].mask_code = lambda x: x
    sys.modules["hyperresearch.core.scholar"].DOI_RE = re.compile("nevermatching")
    sys.modules["hyperresearch.core.scholar"].extract_doi = lambda x: None
    spec = importlib.util.spec_from_file_location("hyperresearch.core.citecheck", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def cases():
    for actor in AGENTS:
        for noun in NOUNS:
            base = f"The {actor} scheduler records verified {noun} before nightly reconciliation for internal tenants with a signed token."
            note = f"source_{actor.lower()}_{noun.replace(' ', '_')}"
            candidates = {
                "exact_support": base,
                "reordered_support": f"For internal tenants with a signed token, the {actor} scheduler records verified {noun} before nightly reconciliation.",
                "temporal_reversal": f"The {actor} scheduler records verified {noun} after nightly reconciliation for internal tenants with a signed token.",
                "scope_expansion": f"The {actor} scheduler records verified {noun} before nightly reconciliation for external tenants with a signed token.",
                "missing_authorization": f"The {actor} scheduler records verified {noun} before nightly reconciliation for internal tenants without a signed token.",
                "unsupported_conjunction": f"The {actor} scheduler records verified {noun} before nightly reconciliation for internal tenants with a signed token and encrypts every payload automatically.",
                "unrelated": f"A separate blue notebook reports weather for field operators.",
            }
            for category in CATEGORIES:
                yield {
                    "id": f"{note}:{category}", "note_id": note,
                    "actor": actor, "noun": noun, "category": category,
                    "source_claim": base, "sentence": candidates[category],
                    "gold_supported": category in ("exact_support", "reordered_support"),
                }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    src = args.source.resolve()
    core = load_upstream(src)
    samples = list(cases())
    assert len(samples) == 84
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE claims(note_id text, claim text, quoted_support text, numbers text)")
    for item in samples[::len(CATEGORIES)]:
        db.execute("INSERT INTO claims VALUES(?,?,?,?)",
                   (item["note_id"], item["source_claim"], "", ""))
    summary = Counter()
    results = []
    for item in samples:
        pair = {
            "note_id": item["note_id"],
            "sentence": item["sentence"] + " [[" + item["note_id"] + "]]",
            "marker": "[[" + item["note_id"] + "]]",
            "numbers": [], "strong": False,
        }
        out = core.triage_pairs([pair], db)
        assert out["total"] == 1
        verdict = out["pairs"][0]["verdict"]
        assert verdict in ("supported-mechanical", "needs-llm")
        normalized = lambda s: re.sub(r"\s+", " ", s.lower()).strip(" .,:;")
        conservative = ("supported-mechanical"
                        if normalized(item["source_claim"]) == normalized(item["sentence"])
                        else "needs-llm")
        unsafe = verdict == "supported-mechanical" and not item["gold_supported"]
        exact_unsafe = conservative == "supported-mechanical" and not item["gold_supported"]
        summary[item["category"] + "/" + verdict] += 1
        results.append({**item, "source_verdict": verdict, "exact_only_verdict": conservative,
                        "unsafe_auto_support": unsafe, "exact_only_unsafe": exact_unsafe})
    negatives = [r for r in results if not r["gold_supported"]]
    positives = [r for r in results if r["gold_supported"]]
    totals = {
        "cases": len(results), "synthetic_supported": len(positives),
        "synthetic_unsupported": len(negatives),
        "source_unsupported_auto_pass": sum(r["unsafe_auto_support"] for r in results),
        "exact_only_unsupported_auto_pass": sum(r["exact_only_unsafe"] for r in results),
        "source_supported_auto_pass": sum(r["source_verdict"] == "supported-mechanical" for r in positives),
        "exact_only_supported_auto_pass": sum(r["exact_only_verdict"] == "supported-mechanical" for r in positives),
    }
    assert totals["synthetic_supported"] == 24 and totals["synthetic_unsupported"] == 60
    assert totals["exact_only_unsupported_auto_pass"] == 0
    assert totals["source_unsupported_auto_pass"] > 0
    report = {
        "study": "hyperresearch",
        "source_commit": PIN, "source_file_sha256": SOURCE_SHA,
        "design": "12 original synthetic baseline clauses x 7 categories (2 supported, 5 unsupported); no author or real-world labels.",
        "scope": "Pinned original triage_pairs with local stubbed unused imports; inspect auto-pass only, not downstream LLM.",
        "totals": totals, "category_verdicts": dict(sorted(summary.items())),
        "limits": [
            "Intentionally adversarial constructed corpus, not prevalence of defects in real research.",
            "Positive reordered paraphrases have their intended meaning authored into the deterministic fixture; no semantic NLP oracle.",
            "Exact-only comparator avoids these unsupported auto-passes but may require more downstream review.",
            "No LLM, network, target project, clinical/SQL data or production execution."
        ],
        "records": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("HYPER_SOURCE_HOLDOUT", json.dumps(totals, sort_keys=True))

if __name__ == "__main__":
    main()
