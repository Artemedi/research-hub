#!/usr/bin/env python3
"""Offline target-path citation gate A/B using synthetic project and research texts.

This imports the actual local paper2project.App from a user-specified source tree,
without writing there. The comparator is deliberately narrow: exact-match
automatic support, with all other statements deferred to semantic review.
"""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import sys
import tempfile
import time

source = Path(os.environ["P2P_SOURCE"]).resolve()
module = source / "src/paper2project/core.py"
if not module.is_file():
    raise SystemExit("P2P_SOURCE must contain src/paper2project/core.py")
sys.path.insert(0, str(source / "src"))
from paper2project.core import App  # noqa: E402

output = Path(os.environ.get("OUTPUT", "paper2agent-target-citation-ab.json"))
actors = ("Alpha", "Beta", "Gamma", "Delta", "Omega")
phrases = (
    "preserves all edits after worker recovery",
    "validates the provenance of external claims",
    "rejects unsafe writes during database inspection",
    "retains audit records after checkpoint restore",
    "isolates the workspace of parallel workers",
)
categories = ("exact", "never", "wrong_entity", "explicit_denial", "unrelated", "positive_paraphrase")
counts = collections.defaultdict(collections.Counter)
latencies = collections.defaultdict(list)

def normalized(value):
    return re.sub(r"\\s+", " ", value.casefold()).strip(" .,:;")

with tempfile.TemporaryDirectory(prefix="p2p-citation-ab-") as directory:
    root = Path(directory)
    project = root / "target.md"
    project.write_text("The mock target requires provenance controls.\n", encoding="utf-8")
    research = root / "paper.txt"
    truths = [f"The {actor} service always {phrase}." for actor in actors for phrase in phrases]
    research.write_text("\n".join(truths) + "\n", encoding="utf-8")
    app = App(root / "workspace", allowed_roots=[root])
    app.import_projects(project, layout="single", name="Mock Target", project_id="mock-target")
    app.import_research(research, research_id="mock-paper")
    job = app.create_job("mock-paper", ["mock-target"])["id"]
    docs = app.docs(job)
    rdoc = next(d for d in docs.values() if d["owner_kind"] == "research")
    pdoc = next(d for d in docs.values() if d["owner_kind"] == "project")
    project_ref = {"document_id": pdoc["id"], "start": 1, "end": 1,
                   "quote": "The mock target requires provenance controls."}
    for index, truth in enumerate(truths):
        actor, phrase = actors[index // len(phrases)], phrases[index % len(phrases)]
        other = actors[((index // len(phrases)) + 1) % len(actors)]
        cases = {
            "exact": truth,
            "never": f"The {actor} service never {phrase}.",
            "wrong_entity": f"The {other} service always {phrase}.",
            "explicit_denial": f"The report denies that the {actor} service always {phrase}.",
            "unrelated": f"The {actor} service does not discuss its billing policy.",
            "positive_paraphrase": f"Always, the {actor} service {phrase}.",
        }
        citation = {"document_id": rdoc["id"], "start": index + 1,
                    "end": index + 1, "quote": truth}
        for category in categories:
            claim = cases[category]
            supported = category in ("exact", "positive_paraphrase")
            analysis = {"summary": "Synthetic A/B only", "assessments": [{
                "project_id": "mock-target", "relevance": "candidate",
                "rationale": claim, "citations": [citation, project_ref],
                "missing_evidence": []
            }]}
            t0 = time.perf_counter_ns()
            try:
                app.submit_analysis(job, analysis)
                baseline = True
            except ValueError:
                baseline = False
            latencies["baseline_ms"].append((time.perf_counter_ns() - t0) / 1e6)
            t1 = time.perf_counter_ns()
            gate = normalized(claim) == normalized(truth)
            latencies["exact_gate_ms"].append((time.perf_counter_ns() - t1) / 1e6)
            counts[category]["cases"] += 1
            counts[category]["supported_oracle"] += int(supported)
            counts[category]["baseline_payload_accepted"] += int(baseline)
            counts[category]["exact_auto_pass"] += int(gate)
            counts[category]["baseline_unsupported_payload_accepted"] += int(baseline and not supported)
            counts[category]["exact_unsupported_auto_pass"] += int(gate and not supported)
    negatives = {}
    for name, test in {
        "invalid_line_range": {"document_id": rdoc["id"], "start": 0, "end": 1},
        "forged_quote": {"document_id": rdoc["id"], "start": 1, "end": 1, "quote": "nonexistent literal"},
        "unscoped_document": {"document_id": "missing", "start": 1, "end": 1},
    }.items():
        try:
            app.citation(job, test)
            negatives[name] = "accepted"
        except ValueError:
            negatives[name] = "rejected"
    try:
        app.citation(job, {"document_id": rdoc["id"], "start": 1, "end": 1})
        negatives["missing_quote"] = "accepted"
    except ValueError:
        negatives["missing_quote"] = "rejected"

assert sum(c["cases"] for c in counts.values()) == 150
assert sum(c["baseline_unsupported_payload_accepted"] for c in counts.values()) == 100
assert sum(c["exact_unsupported_auto_pass"] for c in counts.values()) == 0
assert counts["positive_paraphrase"]["exact_auto_pass"] == 0
assert negatives == {"invalid_line_range": "rejected", "forged_quote": "rejected",
                    "unscoped_document": "rejected", "missing_quote": "accepted"}
result = {
    "date": "2026-11-07",
    "experiment": "current dsh-paper2agent App.submit_analysis synthetic target-path A/B",
    "source_file": "src/paper2project/core.py",
    "source_file_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
    "source_git_head": os.environ.get("P2P_GIT_SHA", "unknown"),
    "source_tree_clean": os.environ.get("P2P_TREE_CLEAN") == "true",
    "source_snapshot": "local tree; exact file SHA pins citation implementation, not all dependencies",
    "cases": 150,
    "supported_oracle": 50,
    "unsupported_oracle": 100,
    "baseline_unsupported_payload_accepted": 100,
    "conservative_exact_unsupported_auto_pass": 0,
    "conservative_exact_supported_auto_pass": 25,
    "supported_paraphrases_deferred": 25,
    "per_class": {k: dict(v) for k, v in sorted(counts.items())},
    "negative_controls": negatives,
    "latency_median_ms": {k: round(statistics.median(v), 5) for k,v in latencies.items()},
    "model_calls": 0,
    "project_files_modified": False,
    "limits": [
        "Deliberately adversarial synthetic cases, not prevalence on scientific papers",
        "Baseline validates source scope/range and optional literal quote, not claim entailment",
        "Exact-only comparator is external to target; it was NOT integrated or tested with an LLM review path",
        "Positive paraphrases are deferred, not scored as false rejections of semantic verification",
        "Uncommitted source requires a separately preserved snapshot for full reproducibility",
        "No private project data, real databases, model API calls or production changes"
    ]
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("cases","baseline_unsupported_payload_accepted",
    "conservative_exact_unsupported_auto_pass","supported_paraphrases_deferred",
    "negative_controls","source_tree_clean")}, ensure_ascii=False))
