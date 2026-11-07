#!/usr/bin/env python3
"""Independent contract assertions for the pinned GAD-inspired offline lab.

Verifies each recorded graph oracle and acceptance scenario by a separate
declarative decision table. This is not an independent GAD implementation.
"""
import hashlib
import json
import os
from pathlib import Path

SOURCE = Path(os.environ["DSH_RUNTIME_SOURCE"])
RESULT = Path(os.environ["EVIDENCE"])
OUTPUT = Path(os.environ["OUTPUT"])
GRAPH = SOURCE / "packages/experimental/agent-team/src/task-graph.ts"
PIN = "3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc"
DIGEST = "a726081289a2f7a848f69109a750db3ead0d95b88ab0adfdae0477f749b8f490"
EXPECTED_GRAPH = {
    "linear": "PASS", "diamond": "PASS", "duplicate": "duplicate",
    "self": "cycle", "missing": "missing", "deleted": "missing",
    "cycle": "cycle",
}
EXPECTED_WORKFLOW = {
    "clean": {"accept": True, "root": True, "error": False, "scoped": 2},
    "unverified": {"accept": False, "root": True, "error": True, "scoped": 1},
    "stale": {"accept": False, "root": True, "error": True, "scoped": 1},
    "crossscope": {"accept": False, "root": True, "error": True, "scoped": 1},
    "rootfail": {"accept": False, "root": False, "error": False, "scoped": 2},
    "missing_dep": {"accept": False, "root": True, "error": True, "scoped": 2},
    "missing_acceptance": {"accept": False, "root": True, "error": True, "scoped": 2},
}


def main():
    import subprocess
    head = subprocess.run(["git", "-C", str(SOURCE), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    assert head == PIN
    assert hashlib.sha256(GRAPH.read_bytes()).hexdigest() == DIGEST
    data = json.loads(RESULT.read_text(encoding="utf-8"))
    assert data["dsh_runtime_pin"] == PIN
    assert data["source_sha256"] == DIGEST
    graph = data["vectors"]
    cases = data["trials"]
    assert len(graph) == len(cases) == 35
    assert len({x["id"] for x in graph}) == 35
    assert len({x["id"] for x in cases}) == 35
    for row in graph:
        kind, num = row["id"].rsplit("-", 1)
        assert num in "01234" and len(num) == 1
        expected = EXPECTED_GRAPH[kind]
        assert row["observed"] == row["expected"] == expected, row
        assert row["matched"] is True
    for row in cases:
        kind, num = row["id"].rsplit("-", 1)
        assert num in "01234" and len(num) == 1
        expectation = EXPECTED_WORKFLOW[kind]
        assert row["expected"] == row["guarded_accepted"] == expectation["accept"], row
        assert row["root_verified"] == expectation["root"], row
        assert bool(row["errors"]) == expectation["error"], row
        assert row["scoped_context_items"] == expectation["scoped"], row
        assert row["flat_context_items"] >= row["scoped_context_items"], row
        assert row["naive_accepted"] is True
        assert row["irrelevant_flat_items"] >= 3
    assert data["graph_vectors_passed"] == 35
    assert data["graph_negative_vectors"] == 25
    assert data["workflow_guarded_accept"] == 5
    assert data["naive_false_accept"] == 30
    assert data["guarded_false_accept"] == 0
    assert data["all_global_evidence_items"] == sum(x["flat_context_items"] for x in cases)
    assert data["scoped_verified_evidence_items"] == sum(x["scoped_context_items"] for x in cases)
    assert data["flat_unrelated_items"] == sum(x["irrelevant_flat_items"] for x in cases)

    # A negative control must demonstrably fail the independent oracle.
    mutated = [dict(x) for x in cases]
    mutated[0]["guarded_accepted"] = not mutated[0]["guarded_accepted"]
    mutation_rejected = any(row["guarded_accepted"] != EXPECTED_WORKFLOW[
        row["id"].rsplit("-", 1)[0]]["accept"] for row in mutated)
    assert mutation_rejected
    result = {
        "date": "2026-11-07",
        "study": "goal-aware-dynamic-collaboration",
        "original_experiment_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
        "source_pin": PIN, "source_file_sha256": DIGEST,
        "graph_checked": len(graph), "workflow_checked": len(cases),
        "oracle_checks_passed": len(graph) + len(cases),
        "mutation_rejected": mutation_rejected,
        "status": "PASS_SEPARATE_DECLARATIVE_ORACLE",
        "limitations": [
            "Verifier checks pinned source hash and recorded per-case outputs, not graph algorithm independently",
            "All expectations are predefined synthetic categories, not external human expert judgments",
            "No genuine GAD model workers or production system exercised"
        ]
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cases": result["oracle_checks_passed"],
                      "mutation_rejected": result["mutation_rejected"]}))


if __name__ == "__main__":
    main()
