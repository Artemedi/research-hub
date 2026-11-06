#!/usr/bin/env python3
"""RRSI official select_round on synthetic source-claim tasks across sealed holdouts.

A: training-score-only source selector. B: same selector + external validation
domain gate. Includes an overfitting memorizer negative control and separate
Harness^2 selection_pool sanity checks. No LLM calls, paid APIs or deployment.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import resource
import runpy
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

GROUPS = ("valid_exact", "valid_neighbor", "wrong_line",
          "fabricated_quote", "false_behavior")
SPLITS = {
    "train": [8, 8, 8, 8, 8],
    "validation": [5, 5, 5, 5, 5],
}
HOLDOUT_MIXES = (
    [4, 4, 10, 10, 12],
    [6, 3, 8, 11, 12],
    [3, 5, 12, 9, 11],
    [5, 5, 7, 11, 12],
    [4, 3, 13, 8, 12],
)


def check_git(root, sha):
    value = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                           check=True, capture_output=True, text=True).stdout.strip()
    if value != sha:
        raise ValueError(f"Source revision mismatch: {root}, {value} != {sha}")


def proc_io():
    path = Path("/proc/self/io")
    if not path.is_file():
        return None
    return {name: int(value.strip()) for name, value in
            (l.split(":", 1) for l in path.read_text().splitlines())
            if name in ("rchar", "wchar", "read_bytes", "write_bytes")}


def generate(root, rng, mix, split, checker):
    out = []
    for kind, count in zip(GROUPS, mix):
        for i in range(count):
            threshold = rng.randrange(2000, 900000)
            name = f"{split}-{kind}-{i:02d}"
            path = root / f"{name}.py"
            source = (["def gate(value):", f"    return value >= {threshold}"]
                      + [f"# generated-{j:02d}" for j in range(3, 38)])
            text = "\n".join(source) + "\n"
            path.write_text(text)
            line = (1 if kind == "valid_neighbor"
                    else 27 if kind == "wrong_line" else 2)
            quote = (f"    return value < -{threshold}"
                     if kind == "fabricated_quote" else source[1])
            value = threshold - 1 if kind == "false_behavior" else threshold
            actual = runpy.run_path(str(path))["gate"](value)
            assert actual == (value >= threshold)
            true = abs(line - 2) <= 1 and quote == source[1] and actual is True
            finding = {"file": str(path), "line": line, "evidence": quote}
            checked = checker.check_findings([copy.deepcopy(finding)],
                                             [(str(path), text)])[0]
            baseline = checked["location_ok"] and checked["evidence_found"]
            local_norm = " ".join(
                " ".join(source[max(0, line - 2):line + 1]).split()
            )
            locality = baseline and " ".join(quote.split()) in local_norm
            out.append({
                "name": name, "kind": kind, "truth": true,
                "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "baseline": baseline, "locality": locality,
            })
    rng.shuffle(out)
    return out


def score(rows, arm, known=None):
    correct = 0
    predictions = []
    for r in rows:
        prediction = (known.get(r["name"], r["baseline"])
                      if arm == "memorizer" else r[arm])
        predictions.append(prediction)
        correct += prediction == r["truth"]
    fp = sum(p and not r["truth"] for r, p in zip(rows, predictions))
    return {
        "n": len(rows), "correct": correct, "accuracy": round(correct / len(rows), 6),
        "false_accept": fp, "negative_count": sum(not r["truth"] for r in rows),
    }


def run_trial(seed, holdout_mix, targets):
    checker, cfg, Candidate, select_round, aggregate, TaskResult, selection_pool, assign_ids = targets
    rng = random.Random(seed)
    start_io, start_wall, start_cpu = proc_io(), time.perf_counter_ns(), time.process_time_ns()
    tracemalloc.start()
    with tempfile.TemporaryDirectory(prefix="rrsi-ab-synthetic-") as tmp:
        root = Path(tmp)
        data = {
            group: generate(root, rng, mix, group, checker)
            for group, mix in [*SPLITS.items(), ("holdout", holdout_mix)]
        }
        fixture_hashes = {
            group: hashlib.sha256("\n".join(sorted(
                f'{r["name"]}:{r["source_sha256"]}:{int(r["truth"])}:{int(r["baseline"])}:{int(r["locality"])}'
                for r in rows
            )).encode()).hexdigest()
            for group, rows in data.items()
        }
        assert len({r["name"] for g in data.values() for r in g}) == 105
        known = {r["name"]: r["truth"] for r in data["train"]}
        assert not any(r["name"] in known for name in ("validation", "holdout")
                       for r in data[name])
        # Training-only reward is produced by the actual RRSI aggregate().
        def evaluation(arm):
            return aggregate(arm, 1, {
                item["name"]: TaskResult(
                    rewards=[float(
                        (known.get(item["name"], item["baseline"]) if arm == "memorizer"
                         else item[arm]) == item["truth"]
                    )])
                for item in data["train"]
            })

        base = evaluation("baseline")
        assert base.C is None  # No real inference or token-cost gate.
        candidates = [
            Candidate("memorizer", [{"component": "memory", "hypothesis": "cache training labels"}],
                      ev=evaluation("memorizer")),
            Candidate("locality", [{"component": "prompt", "hypothesis": "require nearby citation"}],
                      ev=evaluation("locality")),
        ]
        delta = 0.02
        # Holdout is sealed; only baseline and proposal training reward visible.
        tic = time.perf_counter_ns()
        naive, naive_explain = select_round(
            candidates, base, base.S, delta, cfg, incumbent_counts={}
        )
        naive_us = (time.perf_counter_ns() - tic) / 1e3
        assert naive and naive.variant == "memorizer", (seed, naive)
        validation = {
            name: score(data["validation"], name, known=known)
            for name in ("baseline", "memorizer", "locality")
        }
        # Explicit owner-designed validation guard NOT automatic in RRSI.
        def validation_guard(incumbent, proposal):
            gain = validation[proposal.job]["accuracy"] - validation["baseline"]["accuracy"]
            return [] if gain >= 0.10 else ["held-out validation gain < 0.10"]

        tic = time.perf_counter_ns()
        guarded, guard_explain = select_round(
            candidates, base, base.S, delta, cfg, incumbent_counts={},
            guard_fn=validation_guard
        )
        guarded_us = (time.perf_counter_ns() - tic) / 1e3
        assert guarded and guarded.variant == "locality", (seed, guarded)

        # Open held-out results strictly AFTER selection, never inside guard.
        holdout = {
            name: score(data["holdout"], name, known=known)
            for name in ("baseline", "memorizer", "locality")
        }
        assert holdout["memorizer"]["accuracy"] == holdout["baseline"]["accuracy"]
        assert holdout["locality"]["accuracy"] > holdout["baseline"]["accuracy"]
        # Real Harness^2 functions are checked for the baseline pool negative
        # control, not used to produce the A/B outcome above.
        sentinel = object()
        pool = {"base1": sentinel, "agg1": object(), "agg2": object(),
                "c1": object(), "c2": object()}
        parallel = list(selection_pool("agg", 2, pool, [sentinel]))
        sequential = list(selection_pool("sequential", 2, pool, [sentinel]))
        assert parallel == ["agg1", "agg2"] and sequential == ["c1", "c2"]
        assert "base1" not in parallel + sequential
        assert assign_ids(["agg1","agg2"], task_id="T", k=2, mode="agg") == (
            assign_ids(["agg1","agg2"], task_id="T", k=2, mode="agg")
        )
        # Synthetic token budget negative control; those numbers are NOT measured tokens.
        from rrsi.selection import cost_rule
        assert cost_rule(0.20, 0.0, 0, delta, cfg)[0] is True
        assert cost_rule(0.20, 9.0, 0, delta, cfg)[0] is False

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_io = proc_io()
    result = {
        "seed": seed, "holdout_mix": dict(zip(GROUPS,holdout_mix)),
        "fixture_hashes": fixture_hashes,
        "training": {
            arm: score(data["train"], arm, known=known)
            for arm in ("baseline","memorizer","locality")
        },
        "validation": validation, "holdout": holdout,
        "naive_selected": naive.variant,
        "validation_guard_selected": guarded.variant,
        "selector_latency_us": {"naive":round(naive_us,3),"guarded":round(guarded_us,3)},
        "selection_decisions": {
            "naive": {d.variant: {"admissible":d.admissible,"reason":d.reason}
                      for d in naive_explain},
            "guarded": {d.variant: {"admissible":d.admissible,"reason":d.reason}
                        for d in guard_explain},
        },
        "harness2_pool": {"parallel":parallel,"sequential":sequential,
                          "baseline_in_pool": False},
        "wall_ms": round((time.perf_counter_ns()-start_wall)/1e6,3),
        "cpu_ms": round((time.process_time_ns()-start_cpu)/1e6,3),
        "python_peak_alloc_bytes":peak,
        "rss_process_highwater_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "proc_io_delta":({key:end_io[key]-start_io[key] for key in start_io}
                         if start_io and end_io else None),
    }
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rrsi-root",type=Path,required=True)
    parser.add_argument("--rrsi-sha",required=True)
    parser.add_argument("--harness2-root",type=Path,required=True)
    parser.add_argument("--harness2-sha",required=True)
    parser.add_argument("--agent-config",type=Path,required=True)
    parser.add_argument("--agent-sha",required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--seeds",type=int,default=5)
    args=parser.parse_args()
    assert 3 <= args.seeds <= 5
    for path,sha in ((args.rrsi_root,args.rrsi_sha),
                     (args.harness2_root,args.harness2_sha),
                     (args.agent_config,args.agent_sha)):
        check_git(path,sha)
    sys.path[:0]=[str(args.rrsi_root.resolve()),str(args.harness2_root.resolve())]
    spec=importlib.util.spec_from_file_location(
        "agent_checker",args.agent_config/"tools/review.py")
    checker=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(checker)
    from rrsi.config import RRSIConfig
    from rrsi.evaluate import aggregate,TaskResult
    from rrsi.selection import Candidate,select_round
    from harness2.core.selection import selection_pool,assign_ids
    targets=(checker,RRSIConfig(),Candidate,select_round,aggregate,
             TaskResult,selection_pool,assign_ids)
    runs=[
        run_trial(20261106+i,HOLDOUT_MIXES[i],targets)
        for i in range(args.seeds)
    ]
    mean={
        name: round(statistics.mean(x["holdout"][name]["accuracy"] for x in runs),6)
        for name in ("baseline","memorizer","locality")
    }
    all_negative_controls = all(
        r["training"]["memorizer"]["accuracy"]==1.0
        and r["naive_selected"]=="memorizer"
        and r["validation_guard_selected"]=="locality"
        and r["holdout"]["memorizer"]["accuracy"]==r["holdout"]["baseline"]["accuracy"]
        and r["holdout"]["locality"]["accuracy"]>r["holdout"]["baseline"]["accuracy"]
        for r in runs
    )
    assert all_negative_controls
    out={
        "experiment":"RRSI real selector + explicit validation guard; Harness2 pool negative control",
        "source_revisions":{
            "rrsi":args.rrsi_sha,"harness2":args.harness2_sha,
            "agent_config":args.agent_sha
        },
        "run_count":len(runs),"samples_per_run":{
            "training":40,"validation":25,"sealed_holdout":40
        },
        "host":{"python":os.sys.version.split()[0],
                "kernel":os.uname().release},
        "scores_mean_sealed_holdout":mean,
        "all_negative_controls_pass":all_negative_controls,
        "runs":runs,
        "llm_calls":0,"tokens":"N/A","api_cost_usd":0,"vram":"N/A; CPU-only",
        "limitations":[
            "No RRSI proposal-generation models, evolutionary loop, or original benchmark replicated.",
            "Memorizer intentionally overfits synthetic task IDs; not generated by a real agent.",
            "Validation guard is external and was NOT activated by upstream default.",
            "Holdout is synthetic deterministic class-distribution shift; no blind human labels.",
            "Harness2 original selection_pool only; no probes, model execution or compose.",
            "Synthetic token cost rule is a unit negative control, NOT observed inference usage.",
            "Microsecond selector latency depends on Python runtime, filesystem fixtures, instrumentation.",
            "Process RSS highwater is shared, not per-arm; VRAM/tokens N/A, real cost not measured."
        ]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
        "output":str(args.output),
        "mean_heldout":mean,
        "selection_pairs":[
            (r["naive_selected"],r["validation_guard_selected"]) for r in runs
        ]
    },ensure_ascii=False))


if __name__=="__main__":
    main()
