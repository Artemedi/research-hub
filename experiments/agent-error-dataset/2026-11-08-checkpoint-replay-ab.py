#!/usr/bin/env python3
"""Bounded synthetic checkpoint-grounded correction experiment; no external tools."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/results/agent-error-dataset/2026-11-08-checkpoint-replay-ab.json"
SOURCE_URL = "https://arxiv.org/html/2609.40111v2"
SOURCE_SHA256 = "31af8d0a1d4da3a4c4184def8fed7e6f76a6483005804f0868133b682d7aab14"
REPEATS = 3


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def event_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in event.items() if key != "event_sha256"}


def seal_event(event: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(event)
    sealed["event_sha256"] = digest(event_payload(sealed))
    return sealed


def new_state(checkpoint: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(checkpoint["state"])


def apply_action(
    state: dict[str, Any],
    action: dict[str, Any],
    contract: dict[str, Any],
    *,
    attempt: int,
    case_kind: str,
) -> dict[str, Any]:
    if case_kind == "transient" and attempt == 1:
        return {"success": False, "error": "TEMP_UNAVAILABLE"}
    if not contract["allow_write"]:
        return {"success": False, "error": "PERMISSION_DENIED"}
    if action["target"] != contract["allowed_target"]:
        return {"success": False, "error": "UNKNOWN_TARGET"}
    if action["value"] is None:
        return {"success": False, "error": "MISSING_VALUE"}
    if action["expected_revision"] != state["revision"]:
        return {"success": False, "error": "REVISION_MISMATCH"}
    state["items"].append(action["value"])
    state["revision"] += 1
    return {"success": True, "error": None}


def make_case(index: int, kind: str) -> dict[str, Any]:
    case_id = f"case-{index:02d}"
    value = f"synthetic-payload-{index:02d}"
    checkpoint = {
        "case_id": case_id,
        "revision": 0,
        "state": {"revision": 0, "items": []},
    }
    checkpoint_sha = digest(checkpoint)
    action_id = f"{case_id}-action-1"
    contract = {
        "allowed_target": "items",
        "required_value": value,
        "required_revision": 0,
        "allow_write": kind != "misleading",
    }
    action = {
        "action_id": action_id,
        "op": "append",
        "target": "items",
        "value": value,
        "expected_revision": 0,
    }
    proposal = None
    events: list[dict[str, Any]] = []

    if kind == "repairable":
        variant = index % 3
        if variant == 0:
            action["value"] = None
            code, field = "MISSING_VALUE", "value"
        elif variant == 1:
            action["target"] = "itemz"
            code, field = "UNKNOWN_TARGET", "target"
        else:
            action["expected_revision"] = 1
            code, field = "REVISION_MISMATCH", "expected_revision"
        proposal = copy.deepcopy(action)
        proposal[field] = contract[
            {"value": "required_value", "target": "allowed_target",
             "expected_revision": "required_revision"}[field]
        ]
        events.append(seal_event({
            "event_id": f"{case_id}-event-1",
            "action_id": action_id,
            "checkpoint_sha256": checkpoint_sha,
            "code": code,
            "observation": f"synthetic terminal error {code}",
        }))
    elif kind == "transient":
        events.append(seal_event({
            "event_id": f"{case_id}-event-1",
            "action_id": action_id,
            "checkpoint_sha256": checkpoint_sha,
            "code": "TEMP_UNAVAILABLE",
            "observation": "synthetic one-shot transport interruption",
        }))
    elif kind == "ambiguous":
        action["target"] = "itemz"
        action["value"] = None
        events.extend([
            seal_event({
                "event_id": f"{case_id}-event-1",
                "action_id": action_id,
                "checkpoint_sha256": checkpoint_sha,
                "code": "UNKNOWN_TARGET",
                "observation": "synthetic target validation failure",
            }),
            seal_event({
                "event_id": f"{case_id}-event-2",
                "action_id": action_id,
                "checkpoint_sha256": checkpoint_sha,
                "code": "MISSING_VALUE",
                "observation": "synthetic required-value validation failure",
            }),
        ])
    elif kind == "misleading":
        events.extend([
            seal_event({
                "event_id": f"{case_id}-decoy-event",
                "action_id": f"{case_id}-other-action",
                "checkpoint_sha256": checkpoint_sha,
                "code": "UNKNOWN_TARGET",
                "observation": "decoy event from a different action",
            }),
            seal_event({
                "event_id": f"{case_id}-event-1",
                "action_id": action_id,
                "checkpoint_sha256": checkpoint_sha,
                "code": "PERMISSION_DENIED",
                "observation": "synthetic authorization denial",
            }),
        ])
    else:
        raise ValueError(kind)

    return {
        "case_id": case_id,
        "kind": kind,
        "checkpoint": checkpoint,
        "checkpoint_sha256": checkpoint_sha,
        "contract": contract,
        "original_action": action,
        "proposed_action": proposal,
        "events": events,
        "expected_state": {"revision": 1, "items": [value]},
        "initial_attempt": apply_action(
            new_state(checkpoint), action, contract, attempt=1, case_kind=kind
        ),
    }


def candidate_gate(
    fixture: dict[str, Any],
    *,
    evidence_checkpoint_sha: str | None = None,
    evidence_events: list[dict[str, Any]] | None = None,
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checkpoint_sha = digest(fixture["checkpoint"])
    supplied_sha = evidence_checkpoint_sha or fixture["checkpoint_sha256"]
    if supplied_sha != checkpoint_sha or supplied_sha != fixture["checkpoint_sha256"]:
        return {"decision": "ABSTAIN", "reason": "CHECKPOINT_MISMATCH"}

    events = fixture["events"] if evidence_events is None else evidence_events
    matching = [event for event in events if event.get("action_id") == fixture["original_action"]["action_id"]]
    if len(matching) != 1:
        return {"decision": "ABSTAIN", "reason": "AMBIGUOUS_OR_MISSING_ACTION_EVENT"}

    event = matching[0]
    initial = fixture.get("initial_attempt", {})
    if initial.get("success") is not False or event.get("code") != initial.get("error"):
        return {"decision": "ABSTAIN", "reason": "TRACE_DOES_NOT_MATCH_FAILED_ACTION"}
    if event.get("checkpoint_sha256") != checkpoint_sha:
        return {"decision": "ABSTAIN", "reason": "EVENT_CHECKPOINT_MISMATCH"}
    if event.get("event_sha256") != digest(event_payload(event)):
        return {"decision": "ABSTAIN", "reason": "EVENT_INTEGRITY_FAILURE"}

    field_by_error = {
        "MISSING_VALUE": "value",
        "UNKNOWN_TARGET": "target",
        "REVISION_MISMATCH": "expected_revision",
    }
    field = field_by_error.get(event.get("code"))
    if field is None:
        return {"decision": "ABSTAIN", "reason": "ERROR_NOT_REPAIRABLE_BY_LOCAL_CORRECTION"}

    proposed = fixture["proposed_action"] if proposal is None else proposal
    if proposed is None:
        return {"decision": "ABSTAIN", "reason": "NO_PROPOSAL"}

    original = fixture["original_action"]
    changed = [key for key in original if original[key] != proposed.get(key)]
    if set(proposed) != set(original) or changed != [field]:
        return {"decision": "ABSTAIN", "reason": "CORRECTION_SCOPE_MISMATCH"}

    expected_value = fixture["contract"][
        {"value": "required_value", "target": "allowed_target",
         "expected_revision": "required_revision"}[field]
    ]
    if proposed.get(field) != expected_value or proposed.get("action_id") != original["action_id"]:
        return {"decision": "ABSTAIN", "reason": "CORRECTION_NOT_GROUNDED_IN_CONTRACT"}

    return {"decision": "REPAIR", "reason": "SINGLE_ACTION_BOUND_TRACE_AND_CHECKPOINT"}


def run() -> dict[str, Any]:
    started = time.perf_counter()
    kinds = ["repairable"] * 15 + ["transient"] * 5 + ["ambiguous"] * 5 + ["misleading"] * 5
    trials: list[dict[str, Any]] = []
    negative_controls: list[dict[str, Any]] = []

    for index, kind in enumerate(kinds, start=1):
        fixture = make_case(index, kind)
        for repeat in range(1, REPEATS + 1):
            baseline_state = new_state(fixture["checkpoint"])
            baseline = apply_action(
                baseline_state, fixture["original_action"], fixture["contract"],
                attempt=2, case_kind=kind,
            )
            candidate_state = new_state(fixture["checkpoint"])
            gate = candidate_gate(fixture)
            candidate_execution = None
            if gate["decision"] == "REPAIR":
                candidate_execution = apply_action(
                    candidate_state, fixture["proposed_action"], fixture["contract"],
                    attempt=2, case_kind=kind,
                )
            trials.append({
                "case_id": fixture["case_id"],
                "kind": kind,
                "repeat": repeat,
                "checkpoint": fixture["checkpoint"],
                "checkpoint_sha256": fixture["checkpoint_sha256"],
                "contract": fixture["contract"],
                "original_action": fixture["original_action"],
                "proposed_action": fixture["proposed_action"],
                "events": fixture["events"],
                "expected_state": fixture["expected_state"],
                "initial_attempt": fixture["initial_attempt"],
                "baseline": {
                    **baseline,
                    "action": fixture["original_action"],
                    "final_state": baseline_state,
                },
                "candidate": {
                    **gate,
                    "execution": candidate_execution,
                    "final_state": candidate_state,
                },
            })

            if kind == "repairable":
                mutations = []
                mutations.append((
                    "stale_checkpoint",
                    {"evidence_checkpoint_sha": "0" * 64},
                ))
                bad_events = copy.deepcopy(fixture["events"])
                bad_events[0]["code"] = "PERMISSION_DENIED"
                mutations.append(("forged_event_payload", {"evidence_events": bad_events}))
                bad_events = copy.deepcopy(fixture["events"])
                bad_events[0]["action_id"] = f"{fixture['case_id']}-other-action"
                mutations.append(("wrong_action_binding", {"evidence_events": bad_events}))
                bad_proposal = copy.deepcopy(fixture["proposed_action"])
                field = next(
                    key for key in ("target", "value", "expected_revision")
                    if fixture["original_action"][key] != fixture["proposed_action"][key]
                )
                bad_proposal[field] = "mutated-value"
                mutations.append(("wrong_correction", {"proposal": bad_proposal}))
                bad_proposal = copy.deepcopy(fixture["proposed_action"])
                bad_proposal["op"] = "delete"
                mutations.append(("wrong_operation", {"proposal": bad_proposal}))
                bad_proposal = copy.deepcopy(fixture["proposed_action"])
                bad_proposal["untrusted_side_effect"] = True
                mutations.append(("extra_action_field", {"proposal": bad_proposal}))

                for mutation_name, kwargs in mutations:
                    state = new_state(fixture["checkpoint"])
                    decision = candidate_gate(fixture, **kwargs)
                    negative_controls.append({
                        "case_id": fixture["case_id"],
                        "repeat": repeat,
                        "mutation": mutation_name,
                        "decision": decision,
                        "state_before": new_state(fixture["checkpoint"]),
                        "state_after": state,
                    })

    elapsed_ms = (time.perf_counter() - started) * 1000
    summary = {
        "cases": len(kinds),
        "repeats_per_case": REPEATS,
        "paired_trials": len(trials),
        "case_counts": {
            kind: kinds.count(kind) for kind in ("repairable", "transient", "ambiguous", "misleading")
        },
        "baseline_successes": sum(bool(t["baseline"]["success"]) for t in trials),
        "candidate_repairs": sum(t["candidate"]["decision"] == "REPAIR" for t in trials),
        "candidate_successes": sum(bool(t["candidate"]["execution"] and t["candidate"]["execution"]["success"]) for t in trials),
        "candidate_abstentions": sum(t["candidate"]["decision"] == "ABSTAIN" for t in trials),
        "negative_controls": len(negative_controls),
        "negative_controls_blocked": sum(x["decision"]["decision"] == "ABSTAIN" for x in negative_controls),
        "elapsed_ms": round(elapsed_ms, 3),
    }
    return {
        "experiment": "agent-error-dataset-checkpoint-replay-ab",
        "date": "2026-11-08",
        "source": {
            "url": SOURCE_URL,
            "version": "arxiv:v2",
            "full_html_sha256": SOURCE_SHA256,
            "author_results_reproduced": False,
        },
        "method": {
            "environment": "synthetic-only",
            "seed_policy": "fully deterministic fixtures; no random sampling",
            "comparison": "one original-action retry versus one trace- and checkpoint-bound correction",
            "fixture_design": "15 repairable + 5 transient + 5 ambiguous + 5 misleading cases; three repeats per case",
            "repairable_errors": ["MISSING_VALUE", "UNKNOWN_TARGET", "REVISION_MISMATCH"],
            "negative_controls": ["stale_checkpoint", "forged_event_payload", "wrong_action_binding", "wrong_correction"],
            "independent_oracle": "separate script; does not import this experiment",
            "external_tools_or_side_effects": False,
            "llm_or_dataset_used": False,
        },
        "environment_details": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "summary": summary,
        "trials": trials,
        "negative_control_results": negative_controls,
    }


if __name__ == "__main__":
    result = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"RESULT={OUT}")
