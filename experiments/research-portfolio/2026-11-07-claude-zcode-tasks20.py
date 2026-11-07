#!/usr/bin/env python3
"""Pin 20 distinct, author-labelled source-backed tasks for A/B/C swarm pilot.

Reads 4 previously full-reviewed official arXiv HTMLs, checks exact SHA-256,
and prepares a private runtime file with source excerpts. Public manifest
contains only passage digests, citations and our authored claims, not HTML text.
"""
import hashlib
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup

PINS = {
    "2610.22195": "db0746b460b880aab51e9a9d3878a32ae6690bacc3807774ba581963b970f7db",
    "2610.30418": "80b01bba9c64a4bee86dec3badaccc39e8e801121c0610544affb5e67cfe190a",
    "2609.40111": "31af8d0a1d4da3a4c4184def8fed7e6f76a6483005804f0868133b682d7aab14",
    "2609.11028": "36ae9bbdd32fb65d502a9644f7e2905b166cdc620d843b8724ce47b510da74b6",
}
# Each distinct task is one paragraph and a true/false claim pair. Labels are
# written before any model call and must NOT be included in model prompts.
FIXTURES = [
    ("htn-dual-layer", "2610.22195", "1 Introduction",
     "We propose HTN-Orchestrate, a two-layer orchestration framework",
     "Global task planning and local multi-worker subtask execution are separated.",
     "Every worker performs global task planning; no local orchestrator exists."),
    ("htn-rebuild", "2610.22195", "1 Introduction",
     "We combine result-informed planning",
     "Rebuilding the task network retains supported evidence from completed work.",
     "Rebuilding discards all evidence from previously completed subtasks."),
    ("htn-benchmarks", "2610.22195", "1 Introduction",
     "We evaluate HTN-Orchestrate on five benchmarks",
     "The evaluation spans five benchmarks including web research and scientific reasoning.",
     "The evaluation only measures one benchmark from a single domain."),
    ("htn-readiness", "2610.22195", "3 Method",
     "Each node stores its task description",
     "A leaf must be pending and have completed prerequisites before execution.",
     "A leaf may execute while its required prerequisites remain pending."),
    ("htn-waves", "2610.22195", "3 Method",
     "To execute the resulting network, the Planner first processes ready planning nodes",
     "Ready executable leaves are dispatched in a parallel wave before the next planning round.",
     "The next planning round begins before the current execution wave settles."),
    ("mosaic-acl", "2610.30418", "1 Introduction",
     "An LLM agent can respect every document’s access permissions",
     "Compliance with individual document permissions does not preclude revealing an unauthorized composite conclusion.",
     "Access controls on each document make inferential disclosure impossible."),
    ("mosaic-filter", "2610.30418", "1 Introduction",
     "Agents assemble context by retrieving documents",
     "Filtering documents alone may leave information leakage through combinations of authorized facts.",
     "Retrieval filtering always eliminates compositional confidentiality risks."),
    ("mosaic-safeguard", "2610.30418", "1 Introduction",
     "Forbidden composites appear under benign queries in simulation",
     "Under both tested safeguards roughly one-third of simulated answers still exposed the composite.",
     "Both safeguards eliminated every simulated composite disclosure."),
    ("mosaic-factor", "2610.30418", "3 Benchmark and Experimental Design",
     "Four factors are crossed: intent",
     "Three intents and three binary factors produce 24 configurations.",
     "The benchmark experiment has only eight configurations with no intent variation."),
    ("mosaic-examples", "2610.30418", "3 Benchmark and Experimental Design",
     "Our benchmark contains 30 synthetically generated",
     "The thirty generated examples are distributed ten each across three domains.",
     "All thirty examples are drawn from actual classified records."),
    ("aed-size", "2609.40111", "1 Introduction",
     "We introduce the Agent Error Dataset",
     "AED is described as containing 50,228 error-diagnosis pairs across 33 environments.",
     "The reported AED release contains only 5,228 error-diagnosis pairs."),
    ("aed-replay-gain", "2609.40111", "1 Introduction",
     "Our contributions connect failure analysis",
     "First-proposal correction improved matched replay pass rate by 32.7 percentage points.",
     "First-proposal correction reduced matched replay pass rate by 32.7 percentage points."),
    ("aed-failure-scope", "2609.40111", "3 Agent Error Dataset",
     "We count a run as failed when its environment adapter reports",
     "An unsuccessful terminal outcome alone does not identify a trace-supported avoidable agent decision.",
     "An unsuccessful terminal outcome automatically pinpoints the precise avoidable agent action."),
    ("aed-record-fields", "2609.40111", "3 Agent Error Dataset",
     "A record links a failed action–observation trace",
     "Each record links a failed trace with a diagnosis, proposed correction and review data.",
     "AED stores only final rewards and contains no action-observation traces."),
    ("aed-pair-versus-run", "2609.40111", "3 Agent Error Dataset",
     "We check source linkage, error-step presence and trace citations",
     "Additional diagnoses of a single failed run increase the pair count but not run count.",
     "Every new diagnosis necessarily corresponds to a new independently executed run."),
    ("bench-boundary", "2609.11028", "1. Introduction",
     "Interactivity changes what a benchmark score must attest to",
     "Even a mathematically correct scoring function may report a misleading result if its inputs were compromised.",
     "A mathematically correct score formula alone guarantees benchmark reward integrity."),
    ("bench-complexity", "2609.11028", "1. Introduction",
     "This question presents four challenges",
     "A useful lifecycle abstraction must be finite yet detailed enough for recorded evidence to check.",
     "The framework models every container operation because doing so is computationally trivial."),
    ("bench-bindings", "2609.11028", "1. Introduction",
     "We introduce BenchShield, a model-backed instrumentation layer",
     "BenchShield derives infrastructure facts from backend configuration rather than replacing the backend.",
     "BenchShield requires replacing the entire benchmark backend with a new one."),
    ("bench-runtime-events", "2609.11028", "1. Introduction",
     "During execution, infrastructure probes emit a structural event stream",
     "Runtime lifecycle checking processes structural events as they arrive to identify violations early.",
     "Structural events are checked only after reward calculation has finished."),
    ("bench-semantics", "2609.11028", "1. Introduction",
     "A lifecycle model of benchmark reward integrity",
     "The model enforces six structural invariants but records a seventh semantic obligation without enforcing it.",
     "The model checker fully enforces the seventh semantic obligation along with the six structural ones."),
]


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def paragraph(soup, heading, needle):
    matches = []
    for section in soup.select("section"):
        h = section.find(["h2", "h3", "h4"], recursive=False)
        if h and heading in h.get_text(" ", strip=True):
            for p in section.find_all("p"):
                raw = " ".join(p.get_text(" ", strip=True).split())
                if needle in raw:
                    matches.append((section.get("id", ""), raw))
    if len(matches) != 1:
        raise AssertionError(f"Expected unique anchor {heading}/{needle}: {len(matches)}")
    return matches[0]


def main():
    root = Path(os.environ["PAPER_HTML_DIR"])
    private = Path(os.environ["TASKS_PRIVATE"])
    public = Path(os.environ["TASKS_MANIFEST"])
    papers = {}
    parsed = {}
    for key, expected in PINS.items():
        payload = (root / (key + ".html")).read_bytes()
        assert sha(payload) == expected, "FULL_SOURCE_HASH_MISMATCH:" + key
        soup = BeautifulSoup(payload, "html.parser")
        parsed[key] = soup
        titles = [x.get_text(" ", strip=True).lower() for x in soup.select("h2,h3")]
        assert any("method" in x or "benchmark" in x or "dataset" in x for x in titles)
        assert any("evaluation" in x or "experiment" in x or "results" in x for x in titles)
        papers[key] = {"url": f"https://arxiv.org/html/{key}", "html_sha256": expected}
    tasks = []
    for name, paper_id, heading, needle, yes, no in FIXTURES:
        anchor, source = paragraph(parsed[paper_id], heading, needle)
        assert len(source) <= 1300, (name, len(source))
        claims = [{"id": name + "-yes", "source": source,
                   "claim": yes, "url": papers[paper_id]["url"]},
                  {"id": name + "-no", "source": source,
                   "claim": no, "url": papers[paper_id]["url"]}]
        assert all(len(c["claim"]) <= 300 for c in claims)
        tasks.append({
            "id": name, "paper": paper_id, "section": heading,
            "section_id": anchor, "paragraph_sha256": sha(source.encode()),
            "paragraph_length": len(source),
            "gold": {name + "-yes": "SUPPORTED", name + "-no": "NOT_SUPPORTED"},
            "cases": claims,
        })
    assert len(tasks) == 20 and len({x["id"] for x in tasks}) == 20
    assert len({x["paragraph_sha256"] for x in tasks}) == 20, "Not twenty distinct paragraphs"
    assert len({x["paper"] for x in tasks}) == 4
    assert all(len(json.dumps({"id":"batch-1","cases":x["cases"]})) < 9200 for x in tasks)
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_text(json.dumps({"papers": papers, "tasks": tasks}, indent=2)+"\n")
    private.chmod(0o600)
    manifest = {
        "date": "2026-11-07",
        "purpose": "20 distinct research claim-evidence tasks, two authored claims per source passage",
        "oracle_kind": "author-written labels before ZCode; not blinded expert adjudication",
        "papers": papers, "task_count": len(tasks),
        "source_passages_distinct": len({x["paragraph_sha256"] for x in tasks}),
        "claims_total": len(tasks)*2, "gold_supported": len(tasks),
        "gold_not_supported": len(tasks),
        "tasks": [
            {k: t[k] for k in
             ("id", "paper", "section", "section_id",
              "paragraph_sha256", "paragraph_length", "gold")}
            | {"claims": [{"id": c["id"], "claim": c["claim"]}
                          for c in t["cases"]]}
            for t in tasks
        ],
        "limits": [
            "The complete source HTML is verified by SHA and stays outside published Git",
            "Only 20 deliberately selected paragraphs; task labels are author-written",
            "Model input excludes gold labels; no private or clinical records",
            "Multiple tasks from each paper may share context and are not independent sampling units"
        ],
    }
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({
        "tasks": len(tasks), "claims":len(tasks)*2,
        "papers":sorted(papers), "private_bytes":private.stat().st_size
    }))


if __name__ == "__main__":
    main()
