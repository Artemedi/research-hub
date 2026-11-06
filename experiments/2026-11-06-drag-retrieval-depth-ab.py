#!/usr/bin/env python3
"""DRAG-inspired, retrieval-only offline A/B. NOT author's DRAG_QPP/SFT.

The static and routed arms share the same output budget and a fixed synthetic
DBA relevance oracle. No LLM, production data, privileged calls, or network.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
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

# Synthetic textbook-like vocabulary; these are NOT clinical or operational
# instructions and were not extracted from an AKUZ production database.
TOPICS = [
    ("xid wraparound", "transaction age rollover", "relfrozenxid",
     "vacuum freeze", "transactional slot"),
    ("wal retention", "replication slot backlog", "restart_lsn",
     "slot advancement", "logical decoding"),
    ("replica replay", "standby redo delay", "redo_queue_size",
     "redo monitoring", "read scale"),
    ("query store", "plan variant selection", "query_plan_hash",
     "plan regression review", "runtime statistics"),
    ("tempdb pressure", "temporary database stall", "PAGELATCH_UP",
     "tempdb file layout", "row versioning"),
    ("checkpoint pressure", "dirty page flush burst", "checkpoint_write_time",
     "checkpoint pacing", "background writer"),
    ("vacuum bloat", "dead tuple accumulation", "n_dead_tup",
     "vacuum scheduling", "visibility map"),
    ("lock contention", "blocked transaction chain", "wait_event_type",
     "blocking session inspection", "connection churn"),
    ("buffer cache", "cold page read storm", "shared_buffers",
     "cache warmup analysis", "sequential scan"),
    ("index health", "fragmented key lookup", "page_split_count",
     "index design audit", "table partitioning"),
    ("backup recovery", "restore chain mismatch", "last_log_backup_lsn",
     "backup chain validation", "retention policy"),
    ("query planning", "cardinality estimate drift", "estimated_rows",
     "statistics refresh", "join elimination"),
]

STOPWORDS = frozenset(
    "a an the and for of to in on what why how when is are from using with"
    " after before do should please by about where which diagnose explain"
    " compare show but not".split()
)
K = 3


def tok(s):
    return [w for w in re.findall(r"[a-z0-9_]+", s.lower())
            if w not in STOPWORDS]


def build_fixture(seed):
    rng = random.Random(seed)
    documents, questions = [], []
    for i, (canon, alias, symptom, action, noise) in enumerate(TOPICS):
        p = f"topic-{i:02d}"
        rows = [
            (f"{p}-symptom",
             f"PostgreSQL SQL Server {canon}. Symptom indicator {symptom}. "
             f"Diagnostic observation {symptom} increases during incident. "
             "Inspect signal and its timeline."),
            (f"{p}-resolution",
             f"PostgreSQL SQL Server {canon}. Resolution action {action}. "
             f"Recovery approach {action} addresses the symptom. "
             "Verify remediation with a reproducible check."),
            (f"{p}-glossary",
             f"Glossary nickname {alias} maps to {canon}. "
             "Synonym reference only, without an incident observation."),
            (f"{p}-noise",
             f"PostgreSQL SQL Server {canon}. Background note on {noise}. "
             f"Not a diagnosis of {symptom}; unrelated operational example."),
            (f"{p}-overview",
             f"Index overview {canon} {symptom} {action} {noise}. "
             "List of terms, not concrete incident evidence."),
        ]
        documents.extend({"id":did, "text":body}
                         for did, body in rows)
        # Gold labels are authored from the synthetic scenario contract,
        # NOT computed from either retriever or the routing policy.
        questions.extend([
            {"id":f"{p}-easy", "class":"easy",
             "query":f"{canon} symptom indicator {symptom}",
             "gold":[f"{p}-symptom"]},
            {"id":f"{p}-alias", "class":"alias",
             "query":f"why {alias} symptom",
             "gold":[f"{p}-symptom"]},
            {"id":f"{p}-multi", "class":"multi_hop",
             "query":f"for {canon} compare {symptom} and {action}",
             "gold":[f"{p}-symptom", f"{p}-resolution"]},
            {"id":f"{p}-misleading", "class":"misleading",
             "query":f"for {canon} symptom {symptom} but not {noise}",
             "gold":[f"{p}-symptom"]},
            {"id":f"{p}-no_match", "class":"no_match",
             "query":f"for {canon} explain zircondelta antigravity hyperindex",
             "gold":[]},
        ])
    # Negative distractors: shared terms may swamp a lexical retriever.
    for n in range(24):
        chosen = rng.sample(TOPICS, 2)
        documents.append({
            "id":f"cross-decoy-{n:02d}",
            "text": (
                f"Glossary index {chosen[0][0]} {chosen[1][0]} "
                f"{chosen[0][2]} {chosen[1][3]} {chosen[0][4]}. "
                "Mixed unrelated entries; not evidence of an incident."
            ),
        })
    rng.shuffle(documents)
    rng.shuffle(questions)
    assert len(documents) == 84 and len(questions) == 60
    # IDs are used by the evaluator only; scores use text and term statistics.
    return documents, questions


class BM25:
    def __init__(self, documents):
        self.documents = documents
        self.rows = [tok(d["text"]) for d in documents]
        self.tf = [Counter(r) for r in self.rows]
        self.lengths = [len(r) for r in self.rows]
        self.avglen = statistics.mean(self.lengths)
        self.df = Counter()
        for tokens in self.rows:
            self.df.update(set(tokens))
        self.n = len(documents)
        self.idf = {
            term: math.log(1 + (self.n - count + 0.5) / (count + 0.5))
            for term, count in self.df.items()
        }
        # Parse a corpus-visible glossary. This does not read gold judgments.
        self.alias_map = {}
        for item in documents:
            m = re.search(
                r"Glossary nickname (.+?) maps to (.+?)\. Synonym reference",
                item["text"]
            )
            if m:
                self.alias_map[m.group(1).lower()] = m.group(2).lower()

    def score(self, query):
        terms = tok(query)
        scores = []
        for tf, doclen in zip(self.tf, self.lengths):
            total = 0.0
            for term in terms:
                f = tf.get(term, 0)
                if not f:
                    continue
                denom = f + 1.2 * (0.25 + 0.75 * doclen / self.avglen)
                total += self.idf[term] * f * 2.2 / denom
            scores.append(total)
        return scores

    def ranked(self, q):
        s = self.score(q)
        return [idx for idx in sorted(range(len(s)),
                key=lambda j: (-s[j], self.documents[j]["id"]))
                if s[idx] > 0.0]


def routed_mode(q, bm):
    # Pre-retrieval proxy: lexical alias/complex connective, no relevance labels.
    # The policy was fixed before running the first benchmark; no gold is read.
    q = q.lower()
    alias = any(a in q for a in bm.alias_map)
    complex_query = bool(re.search(r"\b(compare|and|but)\b", q))
    return "deep" if alias or complex_query else "cheap"


def expanded(q, bm):
    result = q.lower()
    for alias in sorted(bm.alias_map, key=len, reverse=True):
        if alias in result:
            result = result.replace(alias, bm.alias_map[alias])
    return result


def cheap_search(q, bm):
    return bm.ranked(q)[:K], 1


def deep_search(q, bm):
    canonical = expanded(q, bm)
    views = [canonical]
    # A second retrieval is a query decomposition proxy, not an LLM model.
    if re.search(r"\b(compare|and|but)\b", canonical):
        bits = re.split(r"\b(?:compare|and|but)\b", canonical)
        views += [b.strip() for b in bits if len(tok(b)) > 1]
    # A retrieval variation with relevance-intent terms, fixed in advance.
    if "symptom" in canonical or "why" in canonical:
        views.append(canonical + " symptom indicator")
    if "compare" in canonical or "resolution" in canonical:
        views.append(canonical + " resolution action")
    # Deduplicate views without label leakage.
    views = list(dict.fromkeys(views))
    candidates = Counter()
    for qv in views:
        for rank, doc_idx in enumerate(bm.ranked(qv)):
            if rank < 15:
                candidates[doc_idx] += 1.0 / (15 + rank)
    selected = [i for i, _ in sorted(
        candidates.items(),
        key=lambda x: (-x[1], bm.documents[x[0]]["id"])
    )[:K]]
    return selected, len(views)


def measure(result, questions):
    gold_by_id = {row["id"]: set(row["gold"]) for row in questions}
    found = 0
    relevant = 0
    complete = 0
    no_match_false_citation = 0
    no_match_count = 0
    first_cited = 0
    for query in questions:
        predicted = result[query["id"]]["docs"]
        gold = gold_by_id[query["id"]]
        hit = len(gold.intersection(predicted))
        relevant += len(gold)
        found += hit
        if gold:
            complete += int(hit == len(gold))
        else:
            no_match_count += 1
            no_match_false_citation += int(bool(predicted))
        first_cited += int(bool(gold) and predicted and predicted[0] in gold)
    pos = sum(bool(r["gold"]) for r in questions)
    return {
        "recall_at_3": round(found / relevant, 6) if relevant else None,
        "complete_evidence_rate": round(complete / pos, 6) if pos else None,
        "relevant_items_found": found,
        "relevant_items_total": relevant,
        "first_citation_accuracy_on_positives": round(first_cited / pos, 6) if pos else None,
        "no_match_false_citation": no_match_false_citation,
        "no_match_count": no_match_count,
        "no_match_abstention_rate": round(
            (no_match_count - no_match_false_citation) / no_match_count, 6
        ) if no_match_count else None,
    }


def io_snapshot():
    p = Path("/proc/self/io")
    if not p.exists():
        return None
    return {name: int(v) for name, v in
            (line.split(":", 1) for line in p.read_text().splitlines())
            if name in ("read_bytes", "write_bytes", "rchar", "wchar")}


def execute_arm(arm, bm, queries, seed, expensive_ids):
    tracemalloc.start()
    before = io_snapshot()
    start_cpu = time.process_time_ns()
    start_wall = time.perf_counter_ns()
    records = {}
    times = []
    deep = 0
    scored_docs = 0
    for q in queries:
        start = time.perf_counter_ns()
        if arm == "static_bm25":
            method = "cheap"
        elif arm == "always_deep":
            method = "deep"
        elif arm == "adaptive_proxy":
            method = routed_mode(q["query"], bm)
        elif arm == "random_budget_control":
            method = ("deep" if q["id"] in expensive_ids else "cheap")
        else:
            raise ValueError(arm)
        indices, passes = (cheap_search(q["query"], bm)
                          if method == "cheap" else deep_search(q["query"], bm))
        docs = [bm.documents[j]["id"] for j in indices]
        assert len(docs) <= K and len(set(docs)) == len(docs)
        scored_docs += passes * bm.n
        deep += int(method == "deep")
        records[q["id"]] = {"docs":docs, "tier":method, "passes":passes}
        times.append((time.perf_counter_ns() - start) / 1e6)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    cpu = (time.process_time_ns() - start_cpu) / 1e6
    wall = (time.perf_counter_ns() - start_wall) / 1e6
    after = io_snapshot()
    iodelta = ({k: after[k] - before[k] for k in before}
               if before and after else None)
    ordered = sorted(times)
    metrics = measure(records, queries)
    metrics.update({
        "deep_routes":deep, "cheap_routes":len(queries) - deep,
        "bm25_doc_score_operations":scored_docs,
        "wall_ms":round(wall,3), "cpu_ms":round(cpu,3),
        "latency_ms_p50":round(statistics.median(ordered),5),
        "latency_ms_p95":round(ordered[math.ceil(.95 * len(ordered))-1],5),
        "python_peak_alloc_bytes":peak,
        "process_rss_highwater_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "proc_io_delta":iodelta,
        "by_class":{},
    })
    for category in sorted({x["class"] for x in queries}):
        sample = [q for q in queries if q["class"] == category]
        metrics["by_class"][category] = measure(records, sample)
    return metrics, records


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument("--output",type=Path,required=True)
    pa.add_argument("--seeds",type=int,default=5)
    args=pa.parse_args()
    assert 3<=args.seeds<=10
    arms=("static_bm25","adaptive_proxy","always_deep","random_budget_control")
    runs=[]
    for number in range(args.seeds):
        seed=20261106+number
        documents, queries=build_fixture(seed)
        bm=BM25(documents)
        adaptive_count=sum(routed_mode(q["query"],bm)=="deep" for q in queries)
        # Random control matches the exact adaptive deep-query budget per seed.
        rng=random.Random(seed+1000)
        random_ids=set(rng.sample([x["id"] for x in queries],adaptive_count))
        order=arms[number%len(arms):]+arms[:number%len(arms)]
        run={}
        raw={}
        for arm in order:
            run[arm],raw[arm]=execute_arm(arm,bm,queries,seed,random_ids)
        assert run["adaptive_proxy"]["deep_routes"]==run["random_budget_control"]["deep_routes"]
        assert run["static_bm25"]["deep_routes"]==0
        assert run["always_deep"]["deep_routes"]==len(queries)
        # Negative controls are actual coverage checks, not forced success.
        assert all(set(r["docs"]) <= {d["id"] for d in documents}
                   for items in raw.values() for r in items.values())
        data_hash=hashlib.sha256(json.dumps({
            "documents":sorted(documents,key=lambda d:d["id"]),
            "queries":sorted(queries,key=lambda q:q["id"]),
        },ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        runs.append({"seed":seed,"fixture_sha256":data_hash,
                     "documents":len(documents),"questions":len(queries),
                     "adaptive_deep_budget":adaptive_count,
                     "order":list(order),"arms":run,
                     "per_query":[{"id":q["id"],"class":q["class"],
                                   "query":q["query"],"gold":q["gold"],
                                   "arms":{arm:raw[arm][q["id"]] for arm in arms}}
                                  for q in sorted(queries,key=lambda r:r["id"])]})
    out={
        "experiment":"DRAG-inspired retrieval depth QPP proxy: OFFLINE, not DRAG_QPP or DRAG_SFT",
        "paper":"arxiv:2609.17709v1",
        "environment":{"python":os.sys.version.split()[0],"kernel":os.uname().release},
        "method":"Deterministic BM25 lexical retrieval vs query-adaptive alias and decomposition heuristic; no pretrained model or upstream DRAG code",
        "corpus":"12 DBA topics, 60 author-labelled queries per seed, 84 synthetic docs, 5 query classes",
        "output_budget_docs":K,
        "negative_controls":["unanswerable queries","cross-topic high-overlap decoys",
                             "misleading exclusions","random routing matched to adaptive deep budget"],
        "seeds":[r["seed"] for r in runs],
        "runs":runs,
        "mean_by_arm":{
            a:{metric:round(statistics.mean(
                r["arms"][a][metric] for r in runs),6)
               for metric in ("recall_at_3","complete_evidence_rate",
                              "no_match_false_citation","deep_routes",
                              "bm25_doc_score_operations","wall_ms","cpu_ms",
                              "latency_ms_p50","latency_ms_p95")}
            for a in arms
        },
        "llm_calls":0,"tokens":"N/A (no tokenizer for language model was run)",
        "api_cost_usd":0,"vram":"N/A (CPU-only, no model)",
        "limitations":[
            "Synthetic self-authored DBA examples, not real AKUZ/production or human-blinded labels.",
            "The DRAG study selects both retriever and generator; this experiment implements neither its GPP/perplexity nor supervised DRAG_SFT.",
            "The adaptive policy is a fixed DRAG-inspired heuristic, NOT the published DRAG_QPP implementation or author benchmark.",
            "Manual glossary synonym mappings derived only from corpus text may favor the expanded arm.",
            "The BM25 hand-implementation is shared by all arms, not calibrated against an external search engine.",
            "No learned reranker, dense embeddings, multi-hop answer generation or measured LLM token savings.",
            "One process with shared index and page cache; p95 and CPU microbenchmarks are workload-local, not production SLAs.",
            "RAM highwater is process-wide, Python allocation peak is not resident memory; physical IO may stay zero due to page cache.",
            "No-match cases may still return false citations. Any observed loss is retained, not hidden by oracle routing.",
        ],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"output":str(args.output),"means":out["mean_by_arm"]},
                     ensure_ascii=False))


if __name__=="__main__":
    main()
