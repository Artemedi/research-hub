#!/usr/bin/env python3
"""DRAG follow-up: calibrated abstention plus graph evidence retrieval offline A/B.

Reuse the original recorded toy BM25 baseline, not the authors' DRAG pipeline.
Only generated DBA-like text; no credentials, network, LLM, root or prod access.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import resource
import statistics
import time
import tracemalloc

BASELINE = Path(__file__).with_name("2026-11-06-drag-retrieval-depth-ab.py")
spec = importlib.util.spec_from_file_location("pinned_drag_toy_bm25", BASELINE)
base_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base_mod)
BM25 = base_mod.BM25

CAL_TOPICS = (
    "vacuum_routine", "wal_segment", "tempdb_file", "blocking_chain",
    "query_plan", "checkpoint", "backup_lsn", "table_stats",
    "index_scan", "replica_queue", "snapshot_age", "io_pressure",
)
TEST_TOPICS = (
    "toast_spill", "xid_freeze", "logical_slot", "mpio_fabric",
    "redo_stall", "autovacuum", "lock_escalation", "wait_sampling",
    "buffer_bloat", "bulk_insert", "page_split", "connection_pool",
)
SCOPES = ("pgcore", "sqldata", "sqlag", "linuxio")
CLASSES = ("single", "linked_pair", "alias", "absent",
           "cross_pair", "missing_link", "wrong_link")
ARMS = ("bm25", "schema_gate", "follow_only",
        "gate_follow", "wrong_link_control")
K = 3
THRESHOLDS = (0.5, 0.75, 1.0)


def field_map(doc):
    return dict(re.findall(r"\b([a-z_]+)=([a-z0-9_-]+)", doc["text"].lower()))


def case_fixture(seed, split):
    rng = random.Random(seed)
    topics = CAL_TOPICS if split == "calibration" else TEST_TOPICS
    docs, queries = [], []
    for i, topic in enumerate(topics):
        prefix = f"{split[:3]}-{seed}-{i:02d}"
        scope = SCOPES[i % len(SCOPES)]
        code = f"ev{seed % 100000:05d}{i:02d}a"
        missing_code = f"ev{seed % 100000:05d}{i:02d}b"
        wrong_code = f"ev{seed % 100000:05d}{i:02d}c"
        # Every topic receives an independent, synthetic diagnostic marker.
        marker = f"sig{i:02d}{rng.randrange(10000, 99999)}"
        alias = f"nick{i:02d}{rng.randrange(10000, 99999)}"
        obs, fix = f"{prefix}-obs", f"{prefix}-fix"
        broken, wrong = f"{prefix}-broken", f"{prefix}-wrong"
        other = f"{split[:3]}-{seed}-{(i+4)%12:02d}-fix"

        def make(doc_id, kind, **fields):
            tags = {"kind": kind, **fields}
            # Split-specific prose variation, same documented schema contract.
            attrs = [f"{k}={v}" for k,v in tags.items()]
            if split == "holdout":
                attrs.reverse()
                body = (
                    f"DBA ticket {topic}: investigate known telemetry and evidence. "
                    + " ".join(attrs) +
                    ". The documented statement is a synthetic reference."
                )
            else:
                body = (
                    " ".join(attrs) +
                    f". Engineering note {topic}: inspect telemetry and "
                    "compare the causal sequence before applying a runbook."
                )
            docs.append({"id": doc_id, "text": body})

        make(obs,"observation",subsystem=scope,event=code,marker=marker,
             alias=alias, next=fix)
        make(fix,"runbook",for_incident=obs,action=f"action{i:02d}")
        make(broken,"observation",subsystem=scope,event=missing_code,
             marker=marker,alias=f"obsolete{i:02d}",next=f"{prefix}-absent")
        make(wrong,"observation",subsystem=scope,event=wrong_code,
             marker=marker,alias=f"stale{i:02d}",next=other)
        make(f"{prefix}-glossary","glossary",subsystem=scope,event=code,alias=alias)
        make(f"{prefix}-decoy","example",subsystem=scope,event=code,
             marker=f"decoy{i:02d}",alias=alias)
        # This manifest is derived from the source case specification, not
        # from scores or selected documents. Query class is EVALUATOR-ONLY.
        common = f"subsystem {scope} "
        qs = [
            ("single",common + f"event {code} marker {marker} observation",
             [obs]),
            ("linked_pair",common + f"event {code} need both observation and linked recovery runbook",
             [obs,fix]),
            ("alias",common + f"alias {alias} observation of the incident",
             [obs]),
            ("absent",common + f"event ev{seed%100000:05d}{i:02d}z observation",
             []),
            ("cross_pair",common +
             f"event ev{seed%100000:05d}{(i+4)%12:02d}a marker {marker} observation",
             []),
            ("missing_link",common +
             f"event {missing_code} need both observation and linked recovery runbook",
             []),
            ("wrong_link",common +
             f"event {wrong_code} need both observation and linked recovery runbook",
             []),
        ]
        queries.extend({
            "id":f"{prefix}-{cls}","class":cls,"query":question,"gold":gold,
        } for cls,question,gold in qs)
    for j in range(24):
        ii,kk=rng.sample(range(len(topics)),2)
        docs.append({
            "id":f"{split[:3]}-{seed}-cross-{j:02d}",
            "text":(f"kind=example subsystem={SCOPES[ii%4]} "
                    f"topic={topics[ii]} alias=background{j:02d} "
                    f"term={topics[kk]} event=irrelevant{j:02d} "
                    "cross reference only, not an actionable observation.")
        })
    rng.shuffle(docs)
    rng.shuffle(queries)
    assert len(docs)==96 and len(queries)==84
    assert len({d["id"] for d in docs})==96
    return docs, queries


def parsed_query(s):
    s=s.lower()
    def get(label):
        m=re.search(rf"\b{label} ([a-z0-9_]+)",s)
        return m.group(1) if m else None
    return {
        "subsystem":get("subsystem"),
        "event":get("event"),
        "marker":get("marker"),
        "alias":get("alias"),
        "need_pair":"need both" in s and "linked recovery" in s,
    }


def gate_candidate(documents, selected, query, min_conf):
    q=parsed_query(query)
    best=None
    for rank,docid in enumerate(selected):
        item=documents[docid]
        fields=field_map(item)
        if fields.get("kind")!="observation":
            continue
        requested=[k for k in ("subsystem","event","marker","alias") if q[k]]
        if not requested:
            continue
        conf=sum(fields.get(k)==q[k] for k in requested)/len(requested)
        if conf < min_conf:
            continue
        choice=(conf,-rank,docid)
        if best is None or choice>best:
            best=choice
    return best[2] if best else None


def linked_document(documents, anchor):
    parent=field_map(documents[anchor])
    childid=parent.get("next")
    child=documents.get(childid)
    if not child:
        return None
    metadata=field_map(child)
    if metadata.get("kind")!="runbook":
        return None
    if metadata.get("for_incident")!=anchor.lower():
        return None
    return childid


def run_query(arm,bm,index,question,threshold,wrong_choices):
    q=question["query"]
    ids=[bm.documents[i]["id"] for i in bm.ranked(q)[:K]]
    need_pair=parsed_query(q)["need_pair"]
    if arm=="bm25":
        return ids,1,0
    if arm=="follow_only":
        # Select first visible observation WITHOUT validating the requested
        # event or scope. Incorrect citations still count as failures.
        anchor=next((did for did in ids
                     if field_map(index[did]).get("kind")=="observation"),None)
        if anchor and need_pair:
            child=linked_document(index,anchor)
            if child:
                return [anchor,child],1,1
        return ids,1,0
    anchor=gate_candidate(index,ids,q,threshold)
    if anchor is None:
        return [],1,0
    if arm=="schema_gate" or not need_pair:
        return [anchor],1,0
    if arm=="wrong_link_control":
        # Explicit negative control: same lookup budget, never the true link.
        wrong=wrong_choices[question["id"]]
        assert field_map(index[wrong]).get("kind")=="runbook"
        return [anchor,wrong],1,1
    if arm=="gate_follow":
        child=linked_document(index,anchor)
        if child is None:
            return [],1,1
        return [anchor,child],1,1
    raise ValueError(arm)


def summarize(queries, records):
    relevant=sum(len(q["gold"]) for q in queries)
    found=total_cites=correct_cites=0
    negatives=positives=missing=complete=fully_grounded=0
    covered=0
    classes={}
    for q in queries:
        actual=set(q["gold"])
        pred=records[q["id"]]["docs"]
        hits=sum(d in actual for d in pred)
        total_cites+=len(pred)
        correct_cites+=hits
        found+=len(actual.intersection(pred))
        if actual:
            positives+=1
            covered+=bool(pred)
            complete+=actual.issubset(pred)
            fully_grounded+=actual==set(pred)
        else:
            negatives+=1
            missing+=bool(pred)
        a=classes.setdefault(q["class"],{"total":0,"answered":0,
                                         "complete":0,"false_answer":0})
        a["total"]+=1
        a["answered"]+=bool(pred)
        if actual:
            a["complete"]+=actual.issubset(pred)
        else:
            a["false_answer"]+=bool(pred)
    return {
        "positive_queries":positives,"negative_queries":negatives,
        "relevant_documents":relevant,
        "recall_at3":round(found/relevant,6) if relevant else None,
        "complete_evidence_rate":round(complete/positives,6) if positives else None,
        "fully_grounded_rate":round(fully_grounded/positives,6) if positives else None,
        "positive_answer_coverage":round(covered/positives,6) if positives else None,
        "false_answer_rate_negative":round(missing/negatives,6) if negatives else None,
        "correct_abstention_rate_negative":round((negatives-missing)/negatives,6)
            if negatives else None,
        "citation_precision":round(correct_cites/total_cites,6)
            if total_cites else None,
        "cites_issued":total_cites,"correct_cites":correct_cites,
        "by_class":classes,
    }


def io_stats():
    p=Path("/proc/self/io")
    if not p.is_file():
        return None
    return {k:int(v) for k,v in (r.split(":",1)
            for r in p.read_text().splitlines())
            if k in ("rchar","wchar","read_bytes","write_bytes")}


def evaluate_arm(arm,bm,index,queries,threshold,wrong_choices):
    io0=io_stats()
    tracemalloc.start()
    wall0=time.perf_counter_ns()
    cpu0=time.process_time_ns()
    times=[]
    records={}
    lookups=0
    scored=0
    for q in queries:
        t0=time.perf_counter_ns()
        docs,passes,links=run_query(arm,bm,index,q,threshold,wrong_choices)
        times.append((time.perf_counter_ns()-t0)/1e6)
        records[q["id"]]={"docs":docs,"link_lookups":links}
        lookups+=links
        scored+=passes*len(bm.documents)
    elapsed=(time.perf_counter_ns()-wall0)/1e6
    cpu=(time.process_time_ns()-cpu0)/1e6
    _,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    io1=io_stats()
    io={k:io1[k]-io0[k] for k in io0} if io0 and io1 else None
    ordered=sorted(times)
    m=summarize(queries,records)
    m.update({
        "wall_ms":round(elapsed,3),"cpu_ms":round(cpu,3),
        "latency_ms_p50":round(statistics.median(ordered),5),
        "latency_ms_p95":round(ordered[math.ceil(.95*len(ordered))-1],5),
        "bm25_doc_score_operations":scored,"link_lookups":lookups,
        "python_peak_alloc_bytes":peak,
        "process_rss_highwater_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "proc_io_delta":io,
    })
    return m,records


def choose_threshold(dev):
    # Calibration objective is fixed in this source. No holdout is generated
    # until AFTER selection. Penalize false answers more than abstentions.
    trials=[]
    for threshold in THRESHOLDS:
        metrics=[]
        for bm,idx,queries,wrong in dev:
            m,_=evaluate_arm("gate_follow",bm,idx,queries,threshold,wrong)
            metrics.append(m)
        negative_error=statistics.mean(x["false_answer_rate_negative"] for x in metrics)
        fully=statistics.mean(x["fully_grounded_rate"] for x in metrics)
        positive_coverage=statistics.mean(x["positive_answer_coverage"] for x in metrics)
        utility=fully+0.15*positive_coverage-3.0*negative_error
        trials.append({
            "threshold":threshold,
            "negative_false_answer_rate":round(negative_error,6),
            "fully_grounded_rate":round(fully,6),
            "positive_answer_coverage":round(positive_coverage,6),
            "utility":round(utility,6),
        })
    # Prefer a strict threshold when utilities are tied.
    chosen=max(trials,key=lambda x:(x["utility"],x["threshold"]))
    return chosen["threshold"],trials


def prepare(seed,split):
    docs,queries=case_fixture(seed,split)
    bm=BM25(docs)
    index={d["id"]:d for d in docs}
    runbooks=[did for did,doc in index.items()
              if field_map(doc).get("kind")=="runbook"]
    wrong={}
    for q in queries:
        expected=set(q["gold"])
        candidates=[r for r in runbooks if r not in expected]
        wrong[q["id"]]=candidates[
            int(hashlib.sha256(q["id"].encode()).hexdigest(),16)%len(candidates)]
    fixture_hash=hashlib.sha256(json.dumps({
        "documents":sorted(docs,key=lambda d:d["id"]),
        "questions":sorted(queries,key=lambda d:d["id"]),
    },sort_keys=True).encode()).hexdigest()
    return bm,index,queries,wrong,fixture_hash


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--dev-seeds",type=int,default=3)
    ap.add_argument("--holdout-seeds",type=int,default=5)
    args=ap.parse_args()
    assert 3<=args.dev_seeds<=5
    assert 3<=args.holdout_seeds<=8
    dev=[prepare(20261120+i,"calibration") for i in range(args.dev_seeds)]
    threshold,calibration=choose_threshold([x[:4] for x in dev])
    # Seal calibration before *creating* the holdout examples.
    freeze={
        "threshold":threshold,
        "calibration_trials":calibration,
        "dev_fixture_sha256":[x[4] for x in dev],
        "dev_seeds":[20261120+i for i in range(args.dev_seeds)],
    }
    # Old 20261201..05 was invalidated by an ID parser bug; use fresh seeds.
    holdout=[prepare(20261211+i,"holdout") for i in range(args.holdout_seeds)]
    runs=[]
    for i,(bm,idx,queries,wrong,digest) in enumerate(holdout):
        order=ARMS[i%len(ARMS):]+ARMS[:i%len(ARMS)]
        results={}
        records={}
        for arm in order:
            results[arm],records[arm]=evaluate_arm(
                arm,bm,idx,queries,threshold,wrong)
        assert results["bm25"]["correct_abstention_rate_negative"]==0
        assert results["wrong_link_control"]["by_class"]["linked_pair"]["complete"]==0
        assert results["gate_follow"]["by_class"]["linked_pair"]["complete"]==12
        assert results["gate_follow"]["by_class"]["missing_link"]["false_answer"]==0
        assert results["gate_follow"]["by_class"]["wrong_link"]["false_answer"]==0
        runs.append({
            "seed":20261211+i,"fixture_sha256":digest,
            "document_count":len(idx),"query_count":len(queries),
            "arms":results,
            "per_query":[{
                "id":q["id"],"class":q["class"],
                "query":q["query"],"gold":q["gold"],
                "arms":{arm:records[arm][q["id"]] for arm in ARMS}
            } for q in sorted(queries,key=lambda q:q["id"])],
            "arm_execution_order":list(order),
        })
    out={
        "experiment":"DRAG-inspired abstention and two-hop evidence: calibrated offline A/B",
        "method":"Real pinned prior BM25 class; synthetic schema guard; actual in-memory pointer following; no original DRAG_QPP/SFT",
        "baseline_source":"experiments/2026-11-06-drag-retrieval-depth-ab.py",
        "baseline_source_sha256":hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        "environment":{"python":os.sys.version.split()[0],"kernel":os.uname().release},
        "corpus":"12 disjoint calibration and 12 disjoint holdout DBA topics; 96 docs and 84 queries per seed, 7 classes",
        "output_budget_docs":K,
        "calibration_frozen_before_holdout":freeze,
        "holdout_results":runs,
        "mean_holdout_by_arm":{
            arm:{metric:round(statistics.mean(
                r["arms"][arm][metric] for r in runs),6)
                for metric in (
                    "recall_at3","complete_evidence_rate","fully_grounded_rate",
                    "positive_answer_coverage","false_answer_rate_negative",
                    "correct_abstention_rate_negative","citation_precision",
                    "wall_ms","cpu_ms","latency_ms_p50","latency_ms_p95",
                    "bm25_doc_score_operations","link_lookups"
                )}
            for arm in ARMS},
        "negative_controls":[
            "fake event code", "event/marker mismatch",
            "observation with absent linked runbook",
            "observation whose link points to another case's runbook",
            "wrong runbook deliberately selected as negative control",
            "gold mutation must change evaluation without changing retrieval",
        ],
        "tokens":"N/A, no LLM", "api_spend_usd":0,
        "vram":"N/A; CPU-only",
        "llm_calls":0,
        "limitations":[
            "No human-blinded real-document relevance labels; the generator and oracle share a synthetic schema.",
            "Exact event identifiers and observation/runbook links are artificial and deliberately machine-readable.",
            "Holdout uses disjoint topics and changed document order but retains the schema; zero transfer-to-production claims.",
            "Calibration optimization is performed only on dev; hardcoded feature design may be biased to this fixture family.",
            "The graph follow is an O(1) in-memory lookup, not a real second retrieval over production index.",
            "Same-process memory highwater and cached IO are not per-arm memory/disk costs.",
            "No LLM, real RAG generator, author DRAG_QPP/SFT, real invoices, tokens or VRAM use.",
            "Potentially unsafe abstention on unknown real questions: owner gate and independent real-query oracle needed.",
        ],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "output":str(args.output),
        "calibrated_threshold":threshold,
        "dev_trials":calibration,
        "mean_holdout_by_arm":out["mean_holdout_by_arm"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
