#!/usr/bin/env python3
"""Independent oracle for the synthetic AED checkpoint/replay experiment."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/results/agent-error-dataset/2026-11-08-checkpoint-replay-ab.json"
OUTPUT = ROOT / "data/results/agent-error-dataset/2026-11-08-independent-oracle.json"


def encode(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(encode(value)).hexdigest()


def same_state(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left == right


def verify(document: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    trials = document.get("trials", [])
    mutants = document.get("negative_control_results", [])

    if len(trials) != 90:
        failures.append(f"expected 90 paired trials, got {len(trials)}")
    if len(mutants) != 270:
        failures.append(f"expected 270 negative controls, got {len(mutants)}")

    counts = {name: 0 for name in ("repairable", "transient", "ambiguous", "misleading")}
    baseline_successes = 0
    repair_accepts = 0
    correct_repairs = 0
    abstentions = 0
    false_accepts = 0
    baseline_expected_successes = 0

    for number, trial in enumerate(trials, start=1):
        kind = trial.get("kind")
        if kind not in counts:
            failures.append(f"trial {number}: unknown kind {kind}")
            continue
        counts[kind] += 1

        checkpoint = trial.get("checkpoint")
        checkpoint_hash = sha(checkpoint)
        if checkpoint_hash != trial.get("checkpoint_sha256"):
            failures.append(f"trial {number}: checkpoint hash mismatch")

        events = trial.get("events", [])
        original = trial.get("original_action", {})
        contract = trial.get("contract", {})
        expected = trial.get("expected_state")
        initial = trial.get("initial_attempt", {})
        if initial.get("success") is not False or not initial.get("error"):
            failures.append(f"trial {number}: initial failure is not evidenced")
        baseline = trial.get("baseline", {})
        candidate = trial.get("candidate", {})
        unchanged = checkpoint["state"]

        baseline_ok = bool(baseline.get("success"))
        if baseline_ok:
            baseline_successes += 1
        baseline_should_succeed = kind == "transient"
        if baseline_ok != baseline_should_succeed:
            failures.append(f"trial {number}: baseline success does not match fixture class")
        if baseline_should_succeed:
            baseline_expected_successes += 1
            if not same_state(baseline.get("final_state", {}), expected):
                failures.append(f"trial {number}: baseline final state is not the oracle state")
        elif not same_state(baseline.get("final_state", {}), unchanged):
            failures.append(f"trial {number}: failed baseline mutated state")

        decision = candidate.get("decision")
        if kind == "repairable":
            if decision != "REPAIR":
                failures.append(f"trial {number}: repairable case was not accepted")
            else:
                repair_accepts += 1
                execution = candidate.get("execution") or {}
                if not execution.get("success"):
                    failures.append(f"trial {number}: accepted correction did not execute successfully")
                if not same_state(candidate.get("final_state", {}), expected):
                    failures.append(f"trial {number}: corrected state differs from independent oracle")
                if len(events) != 1:
                    failures.append(f"trial {number}: repairable case does not have exactly one event")
                else:
                    event = events[0]
                    payload = {k: v for k, v in event.items() if k != "event_sha256"}
                    if event.get("action_id") != original.get("action_id"):
                        failures.append(f"trial {number}: event action binding mismatch")
                    if event.get("checkpoint_sha256") != checkpoint_hash:
                        failures.append(f"trial {number}: event checkpoint binding mismatch")
                    if event.get("event_sha256") != sha(payload):
                        failures.append(f"trial {number}: event hash mismatch")
                    if event.get("code") != initial.get("error"):
                        failures.append(f"trial {number}: trace code does not match initial failure")
                    field = {
                        "MISSING_VALUE": "value",
                        "UNKNOWN_TARGET": "target",
                        "REVISION_MISMATCH": "expected_revision",
                    }.get(event.get("code"))
                    proposed = trial.get("proposed_action") or {}
                    changed = [k for k in original if original.get(k) != proposed.get(k)]
                    expected_field_value = {
                        "value": contract.get("required_value"),
                        "target": contract.get("allowed_target"),
                        "expected_revision": contract.get("required_revision"),
                    }.get(field)
                    if field is None or set(proposed) != set(original) or changed != [field] or proposed.get(field) != expected_field_value:
                        failures.append(f"trial {number}: correction is not a single-field contract repair")
                correct_repairs += 1
        else:
            abstentions += decision == "ABSTAIN"
            if decision != "ABSTAIN":
                false_accepts += 1
                failures.append(f"trial {number}: non-repairable case was accepted")
            if candidate.get("execution") is not None:
                failures.append(f"trial {number}: abstaining candidate executed an action")
            if not same_state(candidate.get("final_state", {}), unchanged):
                failures.append(f"trial {number}: abstention mutated state")

    blocked = 0
    for number, item in enumerate(mutants, start=1):
        if item.get("decision", {}).get("decision") == "ABSTAIN":
            blocked += 1
        else:
            failures.append(f"negative control {number}: mutated evidence was accepted")
        if item.get("state_before") != item.get("state_after"):
            failures.append(f"negative control {number}: blocked mutation changed state")

    expected_counts = {"repairable": 45, "transient": 15, "ambiguous": 15, "misleading": 15}
    if counts != expected_counts:
        failures.append(f"case counts mismatch: {counts}")
    if baseline_successes != 15 or baseline_expected_successes != 15:
        failures.append(f"baseline successes mismatch: {baseline_successes}")
    if repair_accepts != 45 or correct_repairs != 45:
        failures.append(f"correct repairs mismatch: accepted={repair_accepts}, correct={correct_repairs}")
    if abstentions != 45:
        failures.append(f"candidate abstentions mismatch: {abstentions}")
    if false_accepts != 0:
        failures.append(f"false accepts detected: {false_accepts}")
    if blocked != 270:
        failures.append(f"negative controls blocked {blocked}/270")

    return {
        "independent_verification": "PASS" if not failures else "FAIL",
        "trials_checked": len(trials),
        "case_counts": counts,
        "baseline_successes": baseline_successes,
        "candidate_correct_repairs": correct_repairs,
        "candidate_abstentions": abstentions,
        "false_accepts": false_accepts,
        "negative_controls_checked": len(mutants),
        "negative_controls_blocked": blocked,
        "failures": failures,
        "interpretation": (
            "Synthetic contract check only; no author model, dataset, external tool, "
            "production trace, or scientific benchmark was reproduced."
        ),
    }


if __name__ == "__main__":
    source = json.loads(INPUT.read_text())
    result = verify(source)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"RESULT={OUTPUT}")
    sys.exit(0 if result["independent_verification"] == "PASS" else 1)
