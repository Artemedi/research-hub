#!/usr/bin/env python3
"""Verify and summarize exact three-mode ZCode/Claude Swarm 20-task experiment.

Machine-readable artifact. All gold labels are author-generated, never
independent human annotation, and prompt equality is verified for each batch.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path

RESULTS = Path(os.environ["RESULTS"]).resolve()
CHECKPOINT_ROOT = Path(os.environ["CHECKPOINT_ROOT"]).resolve()
OUT = Path(os.environ["OUTPUT"]).resolve()


def load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    manifest = load("2026-11-07-claude-zcode-tasks20-manifest.json")
    results = {
        mode: load("2026-11-07-claude-zcode-20-" + mode + ".json")
        for mode in "abc"
    }
    fault = load("2026-11-07-claude-zcode-failure-recovery.json")
    race = load("2026-11-07-claude-zcode-tmux-race.json")
    initial_c = load("2026-11-07-claude-zcode-20-c-initial.json")
    assert manifest["task_count"] == 20
    assert manifest["claims_total"] == 40
    assert manifest["source_passages_distinct"] == 20
    assert len(manifest["papers"]) == 4
    assert len({t["paragraph_sha256"] for t in manifest["tasks"]}) == 20

    for mode, record in results.items():
        assert record["mode"] == mode
        assert record["task_count"] == 20, (mode, record["task_count"])
        assert record["claim_count"] == 40
        assert len(record["batches"]) == 10
        assert len(record["role_receipts"]) == record["provider_calls"]
        assert len({t["task_id"] for b in record["batches"] for t in b["tasks"]}) == 20
        assert all(not any(c["observed"] == "BLOCKED" for c in t["decisions"])
                   for b in record["batches"] for t in b["tasks"]
                   if not t["blocked"])
        # Public manifest pin is exact source/claim content commitment.
        assert record["task_manifest_public_id"].endswith("-tasks20-manifest.json")

    first = []
    for batch in range(10):
        per_mode = {}
        for mode in "abc":
            roles = [x for x in results[mode]["role_receipts"] if x["batch"] == batch]
            assert roles
            if mode == "a":
                assert len(roles) == 1
            elif mode == "b":
                assert len(roles) == 2
            else:
                assert len(roles) in (1, 2)
            per_mode[mode] = roles[0]["prompt_sha256"]
        first.append(per_mode["a"] == per_mode["b"] == per_mode["c"])
    assert all(first), "A/B/C did not receive equal first-call prompts"

    replay = {
        mode: json.loads((CHECKPOINT_ROOT / ("replay-" + mode + ".json")).read_text())
        for mode in ("a", "b", "c")
    }
    assert replay["a"]["checkpoint_hits"] == 10
    assert replay["b"]["checkpoint_hits"] == 20
    assert replay["c"]["checkpoint_hits"] == 17
    assert all(r["new_provider_calls_this_run"] == 0 for r in replay.values())
    assert "CHECKPOINT_INPUT_MISMATCH:a-00-solo" in (
        CHECKPOINT_ROOT / "reject.log"
    ).read_text()
    assert fault["cases_total"] == fault["matched_oracle"] == 17
    assert race["cases_total"] == race["passed"] == 5
    assert (initial_c["verified_tasks"], initial_c["blocked_calls"]) == (18, 1)
    blocked = [x for x in initial_c["role_receipts"] if x["status"] != "COMPLETE"]
    assert len(blocked) == 1
    assert (blocked[0]["batch"], blocked[0]["reason"]) == (8, "not_found")
    assert results["c"]["blocked_calls"] == 0
    assert results["c"]["verified_tasks"] == 20

    metrics = {}
    for mode, r in results.items():
        status_counts = Counter(x["status"] for x in r["role_receipts"])
        metrics[mode] = {
            "task_pass": r["verified_tasks"],
            "task_total": r["task_count"],
            "claim_correct": r["all_claims_correct"],
            "claim_total": r["total_claims"],
            "false_supported": r["false_supported"],
            "abstentions": r["abstentions"],
            "provider_calls": r["provider_calls"],
            "completed_calls": r["completed_calls"],
            "blocked_calls": r["blocked_calls"],
            "status_counts": dict(status_counts),
            "call_p50_ms": r["call_elapsed_ms_p50"],
            "call_p95_ms": r["call_elapsed_ms_p95"],
            "batch_p50_ms": r["batch_wall_ms_p50"],
            "batch_p95_ms": r["batch_wall_ms_p95"],
            "sum_call_elapsed_ms": r["summed_call_wall_ms"],
            "reported_usage": r["reported_usage"],
            "adaptive_escalations": sum(b["escalated"] for b in r["batches"])
            if mode == "c" else None,
            "task_files": [t["task_id"] for b in r["batches"] for t in b["tasks"]],
            "runner_rusage": r["local_runner_rusage_delta"],
        }

    all_pass = all(m["task_pass"] == 20 and m["false_supported"] == 0 and
                   m["blocked_calls"] == 0 for m in metrics.values())
    summary = {
        "date": "2026-11-07",
        "study": "Claude Swarm plus ZCode research task scheduler A/B/C",
        "source_upstream": results["c"]["source_pin"],
        "source_paper_pins": manifest["papers"],
        "fixture_manifest_sha256": sha(
            RESULTS / "2026-11-07-claude-zcode-tasks20-manifest.json"
        ),
        "tasks_unique": 20,
        "source_paragraphs_distinct": 20,
        "claim_labels": 40,
        "source_papers": 4,
        "model_family": "glm-5.3-flash",
        "tool_permissions": "no model tools, public research paragraphs only",
        "concurrency": 1,
        "first_prompt_digest_same_a_b_c": all(first),
        "oracle": "author-annotated claim entailment in full arXiv HTML; not blinded independent expert",
        "metrics": metrics,
        "crash_injection": {
            "reproduced_cases": fault["cases_total"],
            "matched_oracle": fault["matched_oracle"],
            "not_security_attestation": True,
            "source": "2026-11-07-claude-zcode-failure-recovery.json",
            "tmux_race_injection_cases": race["cases_total"],
            "tmux_race_reproduced": race["passed"],
        },
        "checkpoint_resume": {
            "a_hits": replay["a"]["checkpoint_hits"],
            "b_hits": replay["b"]["checkpoint_hits"],
            "c_hits": replay["c"]["checkpoint_hits"],
            "a_new_provider_calls": replay["a"]["new_provider_calls_this_run"],
            "b_new_provider_calls": replay["b"]["new_provider_calls_this_run"],
            "c_new_provider_calls": replay["c"]["new_provider_calls_this_run"],
            "tampered_prompt_hash_rejected": True,
        },
        "initial_adaptive_failure": {
            "task_count_blocked": initial_c["blocked_tasks"],
            "batch": blocked[0]["batch"],
            "reason": blocked[0]["reason"],
            "initial_elapsed_ms": blocked[0]["elapsed_ms"],
            "rework": "bounded retry of transient WorkerManager not_found; same input checksum",
            "additional_historical_worker_attempts": 1,
            "final_adaptive_verified": results["c"]["verified_tasks"],
        },
        "decision": "ACCEPT_BOUNDED_20_TASK_PILOT_AFTER_REWORK" if all_pass
        else "REWORK_OR_BLOCKED",
        "project_adoption_approved": False,
        "caveats": [
            "Twenty unique paragraphs drawn from four known papers, not 20 independent sources",
            "Author labels do not constitute blinded independent human adjudication",
            "The fixed council repeats the same prompt with the same model family",
            "Adaptive logic uses predeclared risk routing, not a validated multi-project scheduler",
            "Batch latency and per-task success are correlated and cannot be treated as 20 independent latency samples",
            "Cache effects and sequential A then B then C order confound performance comparison",
            "CPU/RSS figures cover Node orchestrator only, not full ZCode or tmux child processes",
            "Marker/exit files and checkpoints are same-UID writable and not security proofs",
            "Only synthetic crash injection and manual recovery; no real power loss or distributed failure",
            "No private data, target repo mutation, clinical text, production approval or full-paper re-review"
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "decision": summary["decision"],
        "tasks": summary["tasks_unique"],
        "claims": summary["claim_labels"],
        "metrics": {k: {field: v[field] for field in
                        ("task_pass", "false_supported", "provider_calls",
                         "blocked_calls", "sum_call_elapsed_ms")}
                    for k, v in metrics.items()}
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
