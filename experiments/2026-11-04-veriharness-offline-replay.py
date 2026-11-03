#!/usr/bin/env python3
"""Reproducible *offline* replay of evidence-bound review guards, not a VeriHarness LLM run."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import random
import runpy
import statistics
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--agent-config", type=Path, required=True)
parser.add_argument("--veriharness", type=Path, required=True)
args = parser.parse_args()
agent = args.agent_config.resolve()
veri = args.veriharness.resolve()
sys.path.insert(0, str(agent / "tools"))
sys.path.insert(0, str(veri))
spec = importlib.util.spec_from_file_location("review", agent / "tools" / "review.py")
review = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(review)
from harness.driver import complete_bundle, validate_delivery

rng = random.Random(20261104)
groups = ("valid_exact", "valid_neighbor", "wrong_line", "fabricated_quote", "false_behavior")
measures = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))  # TP FP TN FN
# The "oracle" truth is constructed independently from the verifier's citation checks.
records = []
started = time.perf_counter()

def update(bucket, truth, accept):
    tp, fp, tn, fn = bucket
    bucket[:] = [tp + int(truth and accept),
                 fp + int(not truth and accept),
                 tn + int(not truth and not accept),
                 fn + int(truth and not accept)]

with tempfile.TemporaryDirectory(prefix="veri-offline-") as workspace:
    root = Path(workspace)
    for group in groups:
        for i in range(10):
            threshold = rng.randrange(2, 90000)
            source = root / f"{group}-{i:02d}.py"
            lines = [
                "def gate(n):",
                f"    return n >= {threshold}",
            ] + [f"# padding {j:02d}" for j in range(3, 31)]
            source.write_text("\n".join(lines) + "\n", encoding="utf-8")
            quoted = lines[1]
            claim_line = 2
            expected_input = threshold
            expected_output = True
            if group == "valid_neighbor":
                claim_line = 1
            elif group == "wrong_line":
                claim_line = 22
            elif group == "fabricated_quote":
                quoted = f"    return n < -{threshold}"
            elif group == "false_behavior":
                expected_input = threshold - 1
                expected_output = True
            real_output = runpy.run_path(str(source))["gate"](expected_input)
            supported = (
                group not in {"wrong_line", "fabricated_quote"}
                and real_output == expected_output
            )
            finding = {
                "severity": "high", "title": "gate behavior assertion",
                "file": str(source), "line": claim_line, "evidence": quoted,
                "why": "Synthetic claim", "suggestion": "Recheck evidence",
                "confidence": "high",
            }
            checked = review.check_findings([copy.deepcopy(finding)], [(str(source), source.read_text())])[0]
            baseline_accept = checked["location_ok"] and checked["evidence_found"]

            evidence = " ".join(quoted.split())
            near = " ".join(" ".join(lines[max(0, claim_line-2):min(len(lines), claim_line+1)]).split())
            local_evidence = bool(evidence) and evidence in near and 1 <= claim_line <= len(lines)
            stronger_accept = bool(baseline_accept and local_evidence)
            with_oracle_accept = bool(stronger_accept and real_output == expected_output)

            for name, decision in (
                ("agent_config_existing", baseline_accept),
                ("citation_locality_guard", stronger_accept),
                ("citation_plus_execution_oracle", with_oracle_accept),
            ):
                update(measures[name][group], supported, decision)
                update(measures[name]["total"], supported, decision)
            records.append((group, supported, baseline_accept, stronger_accept, with_oracle_accept))

    # Actual VeriHarness driver's content-blind file-delivery contract, not its model verifier.
    vh = defaultdict(int)
    for group in ("complete_correct", "missing_file", "empty_file", "complete_wrong"):
        for index in range(4):
            task = root / f"veriharness-{group}-{index}"
            base = task / "rollouts" / "r01" / "deliverables"
            out = task / "out" / "deliverables"
            base.mkdir(parents=True)
            out.mkdir(parents=True)
            (base / "app.py").write_text("def gate(n):\n    return n >= 5\n")
            (base / "README.md").write_text("Gate passes for n>=5.\n")
            (out / "app.py").write_text(
                "def gate(n):\n    return False\n" if group == "complete_wrong"
                else "def gate(n):\n    return n >= 5\n"
            )
            if group != "missing_file":
                (out / "README.md").write_text(
                    "" if group == "empty_file" else "Gate passes for n>=5.\n"
                )
            before = validate_delivery(task, "r01")["valid"]
            recovered = complete_bundle(task, "r01")
            after = validate_delivery(task, "r01")["valid"]
            correct_behavior = runpy.run_path(str(out / "app.py"))["gate"](5) is True
            vh["total"] += 1
            vh["valid_before"] += int(before)
            vh["valid_after"] += int(after)
            vh["missing_or_empty_restored"] += len(recovered)
            vh["semantically_wrong_accepted_before"] += int(before and not correct_behavior)
            vh["semantically_wrong_accepted_after"] += int(after and not correct_behavior)
    assert len(records) == 50
    assert [*measures["agent_config_existing"]["total"]] == [20, 20, 10, 0]
    assert [*measures["citation_locality_guard"]["total"]] == [20, 10, 20, 0]
    assert [*measures["citation_plus_execution_oracle"]["total"]] == [20, 0, 30, 0]
    assert dict(vh) == {
        "total": 16, "valid_before": 8, "valid_after": 16,
        "missing_or_empty_restored": 8,
        "semantically_wrong_accepted_before": 4,
        "semantically_wrong_accepted_after": 4,
    }

def render_metrics(vals):
    tp, fp, tn, fn = vals
    return {"true_positive": tp, "false_positive": fp,
            "true_negative": tn, "false_negative": fn,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "recall": round(tp / (tp + fn), 4) if tp + fn else None}

result = {
    "experiment": "synthetic citation + executable oracle replay",
    "not_a_Veriharness_model_run": True,
    "seed": 20261104,
    "synthetic_claims": 50,
    "scenario_types": {group: 10 for group in groups},
    "existing_and_controls": {
        name: render_metrics(data["total"]) for name, data in measures.items()
    },
    "per_class": {
        name: {group: render_metrics(data[group]) for group in groups}
        for name, data in measures.items()
    },
    "real_veriharness_content_blind_gate": dict(vh),
    "llm_calls": 0,
    "elapsed_seconds": round(time.perf_counter() - started, 3),
    "limits": [
        "Claims are procedurally generated, not real agent trajectories.",
        "The execution oracle is supplied by the evaluator, not discovered by an LLM.",
        "The VeriHarness model investigator, consensus challenger, and adjudicator were NOT run.",
        "No inference about reduction of real-world false accepts or tokens is supported."
    ]
}
print(json.dumps(result, indent=2, ensure_ascii=False))
