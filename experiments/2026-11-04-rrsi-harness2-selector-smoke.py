#!/usr/bin/env python3
"""Controlled RRSI selection/held-out test using real source gates, no LLM calls.

This is a deterministic stress test of *selection mechanics*, not an agent-quality benchmark.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import random
import runpy
import sys
import tempfile
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--rrsi", required=True, type=Path)
parser.add_argument("--harness2", required=True, type=Path)
parser.add_argument("--agent-config", required=True, type=Path)
a = parser.parse_args()
sys.path.insert(0, str(a.rrsi.resolve()))
sys.path.insert(0, str(a.harness2.resolve()))
sys.path.insert(0, str((a.agent_config / "tools").resolve()))
from rrsi.config import RRSIConfig
from rrsi.evaluate import TaskResult, aggregate
from rrsi.selection import Candidate, select_round
from rrsi.schedule import budget_table
from harness2.core.selection import selection_pool, assign_ids

review_spec = importlib.util.spec_from_file_location("target_review", a.agent_config / "tools" / "review.py")
review = importlib.util.module_from_spec(review_spec)
review_spec.loader.exec_module(review)
rng = random.Random(20261104)
mixture = {
    "train": {"valid_exact": 8, "valid_neighbor": 8, "wrong_line": 8,
              "fabricated_quote": 8, "false_behavior": 8},
    "validation": {"valid_exact": 5, "valid_neighbor": 5, "wrong_line": 5,
                   "fabricated_quote": 5, "false_behavior": 5},
    "holdout": {"valid_exact": 4, "valid_neighbor": 4, "wrong_line": 10,
                "fabricated_quote": 10, "false_behavior": 12},
}

def metrics(pred, truth):
    tp = sum(p and y for p, y in zip(pred, truth))
    fp = sum(p and not y for p, y in zip(pred, truth))
    tn = sum(not p and not y for p, y in zip(pred, truth))
    fn = sum(not p and y for p, y in zip(pred, truth))
    return {"correct": tp + tn, "n": len(truth), "accuracy": round((tp + tn) / len(truth), 4),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}

def cases(root):
    out = {}
    for split, types in mixture.items():
        out[split] = []
        for kind, count in types.items():
            for n in range(count):
                threshold = rng.randrange(2000, 900000)
                name = f"{split}_{kind}_{n:02d}"
                file = root / f"{name}.py"
                body = [
                    "def gate(value):",
                    f"    return value >= {threshold}",
                ] + [f"# padding-line-{i:02d}" for i in range(3, 37)]
                file.write_text("\n".join(body) + "\n")
                claimed_line = 1 if kind == "valid_neighbor" else (25 if kind == "wrong_line" else 2)
                quoted = body[1] if kind != "fabricated_quote" else f"    return value < -{threshold}"
                value = threshold - 1 if kind == "false_behavior" else threshold
                actual = runpy.run_path(str(file))["gate"](value)
                truth = claimed_line <= 3 and kind != "fabricated_quote" and actual is True
                finding = {"file": str(file), "line": claimed_line, "evidence": quoted}
                checked = review.check_findings([copy.deepcopy(finding)], [(str(file), file.read_text())])[0]
                baseline = bool(checked["location_ok"] and checked["evidence_found"])
                quoted_norm = " ".join(quoted.split())
                window = " ".join(" ".join(body[max(0, claimed_line - 2):
                                                    min(len(body), claimed_line + 1)]).split())
                locality = baseline and quoted_norm in window
                oracle = locality and actual is True
                out[split].append({"id": name, "truth": truth,
                                   "baseline": baseline, "locality": locality, "oracle": oracle})
        rng.shuffle(out[split])
    return out

with tempfile.TemporaryDirectory(prefix="rrsi-selection-offline-") as tmp:
    dataset = cases(Path(tmp))
    # The intentionally benchmark-specific candidate uses ONLY training labels.
    lookup = {r["id"]: r["truth"] for r in dataset["train"]}
    assert not any(row["id"] in lookup for group in ("validation", "holdout") for row in dataset[group])

    def predictions(group, name):
        if name == "memorizer":
            return [lookup.get(r["id"], r["baseline"]) for r in dataset[group]]
        return [r[name] for r in dataset[group]]

    all_variants = ("baseline", "memorizer", "locality", "oracle")
    scores = {
        group: {name: metrics(predictions(group, name), [r["truth"] for r in dataset[group]])
                for name in all_variants}
        for group in ("train", "validation", "holdout")
    }

    def ev(name):
        return aggregate(name, 1, {
            item["id"]: TaskResult(rewards=[float(pred == item["truth"])])
            for item, pred in zip(dataset["train"], predictions("train", name))
        })

    incumbent = ev("baseline")
    proposals = [
        Candidate("memorizer", [{"component": "memory", "hypothesis": "remember train labels"}],
                  ev=ev("memorizer")),
        Candidate("locality", [{"component": "prompt", "hypothesis": "quote must occur at cited line"}],
                  ev=ev("locality")),
        Candidate("oracle", [{"component": "client_tool", "hypothesis": "execute fixed oracle"}],
                  ev=ev("oracle")),
    ]
    cfg = RRSIConfig()
    delta = 0.02

    # Official RRSI selection without user-defined guards. All token counts are absent.
    naive, naive_decisions = select_round(
        proposals, incumbent, incumbent.S, delta, cfg, incumbent_counts={}
    )
    assert naive and naive.variant == "memorizer"

    # Guard deliberately uses validation, NOT the sealed holdout.
    # Oracle branch is excluded because a supplied executable oracle is not
    # available for arbitrary real LLM claims; its synthetic perfect score is not portable.
    def deployability_guard(inc, candidate):
        val = scores["validation"][candidate.job]["accuracy"]
        baseline_val = scores["validation"]["baseline"]["accuracy"]
        problems = []
        if val < baseline_val + 0.1:
            problems.append("validation gain below +10pp")
        if candidate.job == "oracle":
            problems.append("runtime oracle not available for arbitrary claims")
        return problems

    selected, decisions = select_round(
        proposals, incumbent, incumbent.S, delta, cfg, incumbent_counts={},
        guard_fn=deployability_guard,
    )
    assert selected and selected.variant == "locality"
    assert scores["train"]["memorizer"]["accuracy"] == 1.0
    assert scores["holdout"]["memorizer"]["accuracy"] < scores["holdout"]["baseline"]["accuracy"] + 0.01
    assert scores["holdout"]["locality"]["accuracy"] > scores["holdout"]["baseline"]["accuracy"]
    assert scores["holdout"]["oracle"]["accuracy"] == 1.0

    # Official Harness^2 selection_pool only includes refined rollouts; not baseline.
    sentinel = object()
    pools = {"base1": sentinel, "agg1": object(), "agg2": object(),
             "c1": object(), "c2": object()}
    parallel = selection_pool("agg", 2, pools, [sentinel])
    sequential = selection_pool("sequential", 2, pools, [sentinel])
    assert list(parallel) == ["agg1", "agg2"]
    assert list(sequential) == ["c1", "c2"]
    assert "base1" not in parallel and "base1" not in sequential
    assert assign_ids(["agg1", "agg2"], task_id="T", k=2, mode="agg") == \
           assign_ids(["agg1", "agg2"], task_id="T", k=2, mode="agg")

    out = {
        "status": "PASS",
        "method": "synthetic source-claim classification + actual RRSI selector functions",
        "seed": 20261104,
        "samples": {k: len(v) for k, v in dataset.items()},
        "split_sha256": {
            k: hashlib.sha256("\n".join(sorted(row["id"] for row in v)).encode()).hexdigest()
            for k, v in dataset.items()
        },
        "scores": scores,
        "rrsi_default_without_guard": {
            "winner": naive.variant,
            "reason": {d.variant: {"admissible": d.admissible, "reason": d.reason}
                       for d in naive_decisions},
        },
        "rrsi_with_explicit_validation_and_deployment_guard": {
            "winner": selected.variant,
            "reason": {d.variant: {"admissible": d.admissible, "reason": d.reason}
                       for d in decisions},
            "holdout_not_used_in_selection": True,
        },
        "rrsi_annealed_l0_budget": budget_table(8, 1, 4),
        "rrsi_cost_metric": "None for every variant (no LLM tokens available; cost gate not tested)",
        "harness2_actual_selection_pool": {
            "parallel": list(parallel),
            "sequential": list(sequential),
            "baseline_in_choice_pool": False,
        },
        "limitations": [
            "Synthetic rules: no agents, LLM proposals, token usage or production task success measured.",
            "Memorizer is a deliberately constructed overfitting control, not an RRSI generated proposal.",
            "The validation domain guard is external custom policy; RRSI does not automatically include it.",
            "Holdout is a controlled distribution shift in the frequency of five known defect categories.",
            "Executable oracle is pre-supplied; cannot be generalized to arbitrary statements.",
            "Harness2 probe/compose/model-based selection was not run; only its real selection_pool was invoked.",
        ]
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
