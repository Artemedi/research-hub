#!/usr/bin/env python3
"""Pinned-public-corpus retrieval A/B for ExperienceIndex's artifact-pair idea.

Measures exact linked-review navigation, NOT the full LLM/embedding paper method.
Source is a read-only Git archive; no network, production, private data or agents.
"""
from collections import Counter
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tarfile
from time import perf_counter_ns

ROOT = Path(os.environ["RESEARCH_HUB"])
REV = os.environ["RESEARCH_HUB_REV"]
OUTPUT = Path(os.environ["OUTPUT"])
TOKENS = re.compile(r"[\w]+", re.UNICODE)
LINKS = re.compile(r"\]\((\.\./reviews/[^)#]+\.md)(?:#[^)]*)?\)")


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def words(value):
    return [x for x in TOKENS.findall(value.casefold()) if len(x) > 1]


def snapshot():
    assert re.fullmatch(r"[0-9a-f]{40}", REV)
    tar = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar",
                          REV, "studies", "reviews"], check=True,
                         capture_output=True).stdout
    docs = {}
    with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
        for entry in archive:
            if entry.isfile() and entry.name.endswith(".md") and (
                entry.name.startswith(("studies/", "reviews/"))
            ):
                docs[entry.name] = archive.extractfile(entry).read().decode()
    return docs, len(tar)


def build_oracle(docs):
    graph = {}
    cases = []
    excluded = Counter()
    for name, body in sorted(docs.items()):
        if not name.startswith("studies/") or name == "studies/INDEX.md":
            continue
        slug = name.removeprefix("studies/").removesuffix(".md")
        targets = []
        for link in LINKS.findall(body):
            target = os.path.normpath(os.path.join("studies", link))
            if not target.startswith("reviews/" + slug + "/"):
                excluded["out_of_namespace"] += 1
            elif target not in docs:
                excluded["missing_target"] += 1
            else:
                targets.append(target)
        if not targets:
            excluded["no_same_source_edge"] += 1
            continue
        title = body.splitlines()[0].lstrip("# ").strip()
        if not title:
            excluded["empty_title"] += 1
            continue
        target = max(targets)
        graph[name] = {"target": target, "source_sha": sha(body),
                       "target_sha": sha(docs[target])}
        cases.append({"source": name, "target": target, "query": title,
                      "source_sha256": sha(body), "target_sha256": sha(docs[target])})
    assert len(cases) >= 20
    return cases, graph, dict(excluded)


def build_index(docs):
    bags = {name: Counter(words(text)) for name, text in docs.items()}
    df = Counter(token for bag in bags.values() for token in bag)
    size = {name: sum(bag.values()) for name, bag in bags.items()}
    average = sum(size.values()) / len(size)
    return bags, df, size, average


def bm25(index, query, k=5):
    bags, df, size, avg = index
    terms = set(words(query))
    scores = []
    total = len(bags)
    for name, bag in bags.items():
        score = 0.0
        for token in terms:
            frequency = bag.get(token, 0)
            if frequency:
                idf = math.log1p((total - df[token] + 0.5)/(df[token] + 0.5))
                score += idf * frequency * 2.2 / (
                    frequency + 1.2 * (0.25 + 0.75 * size[name] / avg)
                )
        if score > 0:
            scores.append((name, score))
    return [name for name, _ in sorted(scores, key=lambda x: (-x[1], x[0]))[:k]]


def expand(base, graph, docs):
    seed = next((name for name in base[:3] if name in graph), None)
    if seed is None:
        return base, "no_seed"
    edge = graph[seed]
    target = edge["target"]
    if seed not in docs or target not in docs:
        return base, "missing_target"
    if sha(docs[seed]) != edge["source_sha"]:
        return base, "stale_source_hash"
    if sha(docs[target]) != edge["target_sha"]:
        return base, "stale_target_hash"
    if not target.startswith("reviews/" + seed.removeprefix("studies/").removesuffix(".md") + "/"):
        return base, "wrong_namespace"
    if target in base:
        return base, "already_found"
    updated = base[:]
    updated.insert(min(updated.index(seed)+1, 4), target)
    return updated[:5], "expanded"


def main():
    docs, tar_bytes = snapshot()
    cases, graph, excluded = build_oracle(docs)
    index = build_index(docs)
    detailed = []
    base_times = []
    edge_times = []
    for case in cases:
        start = perf_counter_ns()
        base = bm25(index, case["query"])
        base_times.append((perf_counter_ns()-start)//1000)
        start = perf_counter_ns()
        augmented, reason = expand(base, graph, docs)
        edge_times.append((perf_counter_ns()-start)//1000)
        target = case["target"]
        detailed.append({
            "source": case["source"], "target": target,
            "source_sha256": case["source_sha256"],
            "target_sha256": case["target_sha256"],
            "query_sha256": sha(case["query"]),
            "baseline_review_at5": target in base,
            "augmented_review_at5": target in augmented,
            "seed_at3": case["source"] in base[:3],
            "reason": reason, "baseline_top5": base, "augmented_top5": augmented,
        })
    # Negative oracles: reject stale/unauthorized relation, never silently expand.
    sample = cases[0]
    source = sample["source"]
    mismatch = next(n for n in sorted(docs) if n.startswith("reviews/") and
                    not n.startswith("reviews/" + source.removeprefix("studies/").removesuffix(".md") + "/"))
    trials = {
        "stale_source_hash": {"source_sha": "0"*64},
        "stale_target_hash": {"target_sha": "0"*64},
        "missing_target": {"target": "reviews/unknown/1900-01-01.md"},
        "wrong_namespace": {"target": mismatch, "target_sha": sha(docs[mismatch])}
    }
    negative = {}
    for expected, mutation in trials.items():
        edge = dict(graph[source]) | mutation
        out, reason = expand([source], {source: edge}, docs)
        negative[expected] = {"observed": reason, "passed": reason == expected and out == [source]}
    assert all(x["passed"] for x in negative.values())
    # A digest-valid, same-source, but different linked review passes the
    # structural gate: semantic and recency relevance are NOT established.
    alternate_case = next((c for c in cases if len({
        os.path.normpath(os.path.join("studies", link))
        for link in LINKS.findall(docs[c["source"]])
        if os.path.normpath(os.path.join("studies", link)).startswith(
            "reviews/" + c["source"].removeprefix("studies/").removesuffix(".md") + "/"
        ) and os.path.normpath(os.path.join("studies", link)) in docs
    }) > 1), None)
    assert alternate_case is not None
    alternate_source = alternate_case["source"]
    alternate_target = next(
        os.path.normpath(os.path.join("studies", link))
        for link in LINKS.findall(docs[alternate_source])
        if os.path.normpath(os.path.join("studies", link)) != alternate_case["target"] and
        os.path.normpath(os.path.join("studies", link)).startswith(
            "reviews/" + alternate_source.removeprefix("studies/").removesuffix(".md") + "/") and
        os.path.normpath(os.path.join("studies", link)) in docs
    )
    valid_but_wrong = dict(graph[alternate_source]) | {
        "target": alternate_target, "target_sha": sha(docs[alternate_target])
    }
    alternative, alternative_reason = expand(
        [alternate_source], {alternate_source: valid_but_wrong}, docs
    )
    assert alternative_reason == "expanded" and alternate_target in alternative
    before = sum(x["baseline_review_at5"] for x in detailed)
    after = sum(x["augmented_review_at5"] for x in detailed)
    result = {
        "date": "2026-11-07", "source": "experienceindex",
        "status": "BOUNDED_EXPLICIT_LINK_RETRIEVAL",
        "research_hub_pin": REV,
        "full_paper_url": "https://arxiv.org/html/2610.10091v1",
        "full_paper_html_sha256": os.environ.get("PAPER_SHA256"),
        "corpus_docs": len(docs), "corpus_archive_bytes": tar_bytes,
        "study_docs": sum(k.startswith("studies/") for k in docs),
        "review_docs": sum(k.startswith("reviews/") for k in docs),
        "cases": len(cases), "baseline_review_at5": before,
        "augmented_review_at5": after,
        "new_recovered": sum(not x["baseline_review_at5"] and x["augmented_review_at5"] for x in detailed),
        "regressions": sum(x["baseline_review_at5"] and not x["augmented_review_at5"] for x in detailed),
        "negative_oracles": negative, "excluded": excluded,
        "structural_valid_but_not_latest_control": {
            "source": alternate_source, "accepted_alternate_target": alternate_target,
            "expected_latest_target": alternate_case["target"],
            "structural_gate_accepted": alternative_reason == "expanded",
            "semantic_relevance_established": False,
            "disposition": "REQUIRES_RELEVANCE_AND_RECENCY_GATE"
        },
        "median_bm25_us": sorted(base_times)[len(base_times)//2],
        "median_link_us": sorted(edge_times)[len(edge_times)//2],
        "retrieval_design": "BM25 full Markdown text top5, with one explicit verified linked review after first top3 study card; both top5",
        "oracle": "Exact link/path/sha of latest explicitly linked same-source review; not semantic or scientific relevance",
        "cases_detail": detailed,
        "limitations": [
            "Explicit Markdown links substitute for learned artifact pair relations",
            "Queries are source card headings; not a holdout human relevance taskset",
            "No embeddings, LLM relevance gate, prompt injection, online learning or author method reproduction",
            "A linked review need not be semantically relevant to any given query",
            "This is navigation accuracy, not model answer accuracy, factual truth, or integration benefit",
            "One pinned public hub snapshot, no private indexed project data"
        ]
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k:result[k] for k in (
        "research_hub_pin","corpus_docs","cases","baseline_review_at5",
        "augmented_review_at5","new_recovered","regressions"
    )}))


if __name__ == "__main__":
    main()
