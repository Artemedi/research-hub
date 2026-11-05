#!/usr/bin/env python3
"""A/B: real agent-config citation checker vs a locality gate, synthetic oracle only."""
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
import tempfile
import time
import tracemalloc

CLASSES = ("valid_exact", "valid_neighbor", "wrong_line", "fabricated_quote", "false_behavior")


def process_io():
    path = Path("/proc/self/io")
    if not path.exists():
        return None
    return {key: int(val) for key, val in
            (line.split(":", 1) for line in path.read_text().splitlines())
            if key in ("rchar", "wchar", "read_bytes", "write_bytes")}


def build_cases(root, seed, per_class):
    rng = random.Random(seed)
    items = []
    for group in CLASSES:
        for idx in range(per_class):
            threshold = rng.randrange(1000, 900000)
            name = f"{seed}_{group}_{idx:03d}"
            path = root / f"{name}.py"
            lines = ["def gate(n):", f"    return n >= {threshold}"]
            lines.extend(f"# fixture-padding-{n:02d}" for n in range(3, 38))
            text = "\n".join(lines) + "\n"
            path.write_text(text, encoding="utf-8")
            claimed_line = (1 if group == "valid_neighbor" else
                            26 if group == "wrong_line" else 2)
            evidence = (f"    return n < -{threshold}" if group == "fabricated_quote"
                        else lines[1])
            test_value = threshold - 1 if group == "false_behavior" else threshold
            actual = runpy.run_path(str(path))["gate"](test_value)
            assert actual == (test_value >= threshold), "Oracle/generator disagree"
            # Independent truth is a contract over generated file lines plus
            # the executable behavior, never the checker under evaluation.
            supported = (abs(claimed_line - 2) <= 1
                         and evidence == lines[1] and actual is True)
            items.append({
                "group": group, "file": str(path), "line": claimed_line,
                "evidence": evidence, "text": text, "supported": supported,
            })
    rng.shuffle(items)
    assert len(items) == len(CLASSES) * per_class
    return items


def check(review, item, arm):
    finding = {"file": item["file"], "line": item["line"],
               "evidence": item["evidence"]}
    result = review.check_findings(
        [copy.deepcopy(finding)], [(item["file"], item["text"])]
    )[0]
    accepted = bool(result["location_ok"] and result["evidence_found"])
    if arm == "locality" and accepted:
        lines = item["text"].splitlines()
        index = item["line"] - 1
        neighborhood = " ".join(
            " ".join(lines[max(0, index - 1):index + 2]).split()
        )
        accepted = " ".join(item["evidence"].split()) in neighborhood
    return accepted


def summarize(truths, predictions, timings_ns):
    tp = sum(x and y for x, y in zip(truths, predictions))
    fp = sum(not x and y for x, y in zip(truths, predictions))
    tn = sum(not x and not y for x, y in zip(truths, predictions))
    fn = sum(x and not y for x, y in zip(truths, predictions))
    latency_us = sorted(ns / 1000 for ns in timings_ns)
    p95_index = max(0, int(len(latency_us) * .95 + .999999) - 1)
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(tp / (tp + fp), 6) if tp + fp else None,
        "recall": round(tp / (tp + fn), 6) if tp + fn else None,
        "negative_false_accept_rate": round(fp / (fp + tn), 6) if fp + tn else None,
        "latency_us_p50": round(statistics.median(latency_us), 3),
        "latency_us_p95": round(latency_us[p95_index], 3),
    }


def run_arm(review, items, arm):
    tracemalloc.start()
    start_io = process_io()
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    predictions, times = [], []
    for row in items:
        start = time.perf_counter_ns()
        predictions.append(check(review, row, arm))
        times.append(time.perf_counter_ns() - start)
    cpu_ms = (time.process_time_ns() - cpu_start) / 1e6
    elapsed_ms = (time.perf_counter_ns() - wall_start) / 1e6
    _, peak = tracemalloc.get_traced_memory()
    finish_io = process_io()
    tracemalloc.stop()
    io = ({key: finish_io[key] - start_io[key] for key in start_io}
          if start_io is not None and finish_io is not None else None)
    return {
        **summarize([row["supported"] for row in items], predictions, times),
        "wall_ms": round(elapsed_ms, 3),
        "cpu_ms": round(cpu_ms, 3),
        "python_peak_alloc_bytes": peak,
        "proc_io_counters_delta": io,
        "rss_max_kib_process_wide": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--per-class", type=int, default=40)
    args = parser.parse_args()
    assert 2 <= args.seeds <= 10 and 10 <= args.per_class <= 100
    agent = args.agent_config.resolve()
    source = agent / "tools/review.py"
    assert source.is_file()
    spec = importlib.util.spec_from_file_location("source_review", source)
    review = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(review)
    result = []
    fixture_hashes = []
    with tempfile.TemporaryDirectory(prefix="agent-config-locality-ab-") as temp:
        for iteration in range(args.seeds):
            seed = 20261106 + iteration
            cases = build_cases(Path(temp), seed, args.per_class)
            fixture_hashes.append(hashlib.sha256(
                "\n".join(f'{x["group"]}:{x["evidence"]}:{x["line"]}'
                          for x in cases).encode()
            ).hexdigest())
            # Avoid allocating fixture files inside the timed comparison.
            # Reverse order on alternate seeds to expose gross warm-cache bias.
            arms = ("baseline", "locality") if iteration % 2 == 0 else (
                "locality", "baseline")
            scores = {arm: run_arm(review, cases, arm) for arm in arms}
            assert scores["baseline"]["tp"] == scores["locality"]["tp"] == 2 * args.per_class
            assert scores["baseline"]["fn"] == scores["locality"]["fn"] == 0
            assert scores["baseline"]["fp"] == 2 * args.per_class
            assert scores["locality"]["fp"] == args.per_class
            assert scores["baseline"]["tn"] == args.per_class
            assert scores["locality"]["tn"] == 2 * args.per_class
            result.append({"seed": seed, "cases": len(cases),
                           "order": list(arms), "arms": scores})
    output = {
        "experiment": "agent-config citation locality A/B, restricted VeriHarness-related mechanism",
        "scope": "real source check_findings; synthetic generated claims; no LLM verifier",
        "source_file": "tools/review.py",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "host": {"python": os.sys.version.split()[0], "os": os.uname().release},
        "seeds": [x["seed"] for x in result],
        "fixture_sha256": fixture_hashes,
        "total_cases": sum(x["cases"] for x in result),
        "per_class_per_seed": args.per_class,
        "controls": list(CLASSES),
        "runs": result,
        "mean_false_accept_rate": {
            arm: round(statistics.mean(x["arms"][arm]["negative_false_accept_rate"]
                                       for x in result), 6)
            for arm in ("baseline", "locality")
        },
        "mean_wall_ms_per_seed": {
            arm: round(statistics.mean(x["arms"][arm]["wall_ms"] for x in result), 3)
            for arm in ("baseline", "locality")
        },
        "llm_calls": 0,
        "tokens": "N/A: no LLM calls; not an estimate of inference token usage",
        "api_spend_usd": 0,
        "vram": "N/A: CPU/Python benchmark, no model or GPU",
        "limitations": [
            "Fixture labels and file contents are generated; no independent human coding claims.",
            "The oracle executes only self-generated Python threshold functions.",
            "The locality guard checks citation location, NOT semantic correctness.",
            "Both algorithms run in one process, with alternating order, CPU/cache noise remains.",
            "Python tracemalloc peak is not process RSS or kernel memory.",
            "No original VeriHarness resolver/challenger/LLM integration was tested.",
            "Results do not imply real-project precision or measured inference savings.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(args.output), "cases": output["total_cases"],
        "mean_false_accept_rate": output["mean_false_accept_rate"],
        "mean_wall_ms_per_seed": output["mean_wall_ms_per_seed"],
        "source_sha256": output["source_sha256"]
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
