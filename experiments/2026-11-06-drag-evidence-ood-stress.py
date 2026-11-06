#!/usr/bin/env python3
"""Out-of-distribution stress test of frozen DRAG-inspired evidence guard.

Post-hoc adverse cases; NOT an additional blind holdout or model replication.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import statistics

PARENT=Path(__file__).with_name("2026-11-06-drag-abstention-multihop-ab.py")
spec=importlib.util.spec_from_file_location("frozen_schema_guard",PARENT)
model=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(model)

ARMS=("bm25","gate_follow")
MUTATIONS=("original","format_shift","forged_observation")


def mutate(docs,mode):
    copied=[dict(item) for item in docs]
    if mode=="format_shift":
        # The body still contains the exact tokens needed for BM25; only the
        # machine-readable observation type differs from documented schema.
        for item in copied:
            if item["id"].endswith("-obs"):
                before=item["text"]
                item["text"]=before.replace("kind=observation","kind:observation",1)
                assert item["text"]!=before
    elif mode=="forged_observation":
        for item in docs:
            if not item["id"].endswith("-obs"):
                continue
            metadata=model.field_map(item)
            for duplicate in range(4):
                copied.append({
                    "id":f"untrusted-{duplicate}-{item['id']}",
                    "text":(
                        f"kind=observation subsystem={metadata['subsystem']} "
                        f"event={metadata['event']} marker={metadata['marker']} "
                        f"alias={metadata['alias']} next={metadata['next']}. "
                        f"incident observation evidence event {metadata['event']} "
                        f"marker {metadata['marker']} alias {metadata['alias']} "
                        "need both linked recovery runbook. "
                        "SYNTHETIC UNTRUSTED CLAIM; not independently validated."
                    ),
                })
    elif mode!="original":
        raise ValueError(mode)
    assert len({d["id"] for d in copied})==len(copied)
    return copied


def run_one(seed, threshold):
    docs,queries=model.case_fixture(seed,"holdout")
    wrong={}
    original={}
    outcomes={}
    for mode in MUTATIONS:
        mutated=mutate(docs,mode)
        idx={d["id"]:d for d in mutated}
        bm=model.BM25(mutated)
        cases={}
        raw={}
        for arm in ARMS:
            cases[arm],raw[arm]=model.evaluate_arm(
                arm,bm,idx,queries,threshold,wrong
            )
        if mode=="original":
            original=raw
        if mode=="format_shift":
            # Directly verifies that the changed delimiter, not a different
            # retrieved document population, creates the refusal behavior.
            assert all(raw["bm25"][q["id"]]==original["bm25"][q["id"]]
                       for q in queries)
            assert cases["gate_follow"]["positive_answer_coverage"]==0
        outcomes[mode]={
            "doc_count":len(mutated),
            "sha256":hashlib.sha256(json.dumps(
                sorted(mutated,key=lambda x:x["id"]),sort_keys=True
            ).encode()).hexdigest(),
            "arms":cases,
            "per_query":[{
                "id":q["id"],"class":q["class"],"gold":q["gold"],
                "outputs":{arm:raw[arm][q["id"]] for arm in ARMS}
            } for q in sorted(queries,key=lambda x:x["id"])],
        }
    return {"seed":seed,"mutations":outcomes}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--seeds",type=int,default=5)
    parser.add_argument("--calibrated-threshold",type=float,default=1.0)
    args=parser.parse_args()
    assert 3<=args.seeds<=8
    assert args.calibrated_threshold in model.THRESHOLDS
    # Separate never-used seeds from both dev and earlier sealed holdouts.
    runs=[run_one(20261231+i,args.calibrated_threshold)
          for i in range(args.seeds)]
    means={}
    for mode in MUTATIONS:
        means[mode]={}
        for arm in ARMS:
            metrics={}
            for key in (
                "recall_at3","complete_evidence_rate",
                "fully_grounded_rate","positive_answer_coverage",
                "correct_abstention_rate_negative",
                "false_answer_rate_negative","citation_precision",
                "wall_ms","cpu_ms","latency_ms_p95",
            ):
                values=[
                    run["mutations"][mode]["arms"][arm][key]
                    for run in runs
                    if run["mutations"][mode]["arms"][arm][key] is not None
                ]
                metrics[key]=round(statistics.mean(values),6) if values else None
            means[mode][arm]=metrics
    report={
        "experiment":"Frozen guard OOD / adversarial retrieval checks",
        "status":"POSTHOC_STRESS_NOT_BLIND_HOLDOUT",
        "source_sha256":hashlib.sha256(PARENT.read_bytes()).hexdigest(),
        "threshold_fixed_from_previous_dev":args.calibrated_threshold,
        "seeds":[r["seed"] for r in runs],
        "runs":runs,
        "mean_by_mutation_arm":means,
        "negative_controls":[
            "kind= changed to kind: in canonical observation; BM25 tokens invariant",
            "four untrusted schema-compatible duplicate observation docs per incident",
        ],
        "llm_calls":0,"tokens":"N/A","api_cost_usd":0,
        "vram":"N/A; CPU-only",
        "limitations":[
            "Adversarial tests were designed after the primary holdout, so they are diagnostic, not blinded evaluation.",
            "Format shift is a synthetic metadata breaking change, not a normal document renderer experiment.",
            "Forged evidence injects four explicit untrusted copies per incident, an adversarial and unrealistic prevalence.",
            "The query oracle is the unmodified generated incident manifest, independent of altered fake citations.",
            "No real trust boundary or cryptographic provenance: citation origin must be verified separately.",
            "All file /proc/self/io, Python alloc and process-wide RSS limitations from primary run apply.",
        ],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"output":str(args.output),"mean":means},
                     ensure_ascii=False))


if __name__=="__main__":
    main()
