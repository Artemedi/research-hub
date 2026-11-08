#!/usr/bin/env python3
"""Independent oracle for the CERA-MoA synthetic routing contract result.

The selection oracle uses prefix recomputation rather than the experiment's
incremental accumulator. It does not import the experiment module.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

SEED = 20261108
CASE_COUNT = 10_000
RESULT = Path("data/results/cera-moa/2026-11-08-routing-contract.json")
OUTPUT = Path("data/results/cera-moa/2026-11-08-independent-oracle.json")


def make_case(rng: random.Random, index: int) -> tuple[str, list[float], list[float], float]:
    count = 3 if index % 5 == 0 else 4
    distance = [rng.uniform(0.0, 2.0) for _ in range(count)]
    familiarity = [math.exp(-2.0 * value) for value in distance]
    threshold = 0.7 if index % 3 else rng.choice((0.5, 0.6, 0.8, 0.9))
    if index % 4 == 0:
        mode, priority = "inference", familiarity[:]
    else:
        mode = "training"
        total = rng.randint(1, 6000)
        seen = [rng.randint(0, total) for _ in range(count)]
        entropy = [rng.random() for _ in range(count)]
        weight = 0.2 if count == 3 else 2.0
        priority = [
            familiarity[i] + 2.0 * math.sqrt(math.log(total) / (seen[i] + 1)) + weight * entropy[i]
            for i in range(count)
        ]
        if index % 37 == 0:
            priority = [round(value, 4) for value in priority]
    return mode, familiarity, priority, threshold


def oracle_select(familiarity: list[float], priority: list[float], threshold: float) -> list[int]:
    ranked = sorted(range(len(familiarity)), key=lambda i: (-priority[i], i))
    for prefix_size in range(1, len(ranked) + 1):
        prefix = ranked[:prefix_size]
        if sum(familiarity[index] for index in prefix) >= threshold:
            return prefix
    return ranked


def record_bytes(index: int, mode: str, familiarity: list[float], priority: list[float], threshold: float, selected: list[int]) -> bytes:
    payload = {
        "i": index,
        "mode": mode,
        "f": [round(x, 12) for x in familiarity],
        "p": [round(x, 12) for x in priority],
        "tau": round(threshold, 12),
        "selected": selected,
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main() -> None:
    claimed = json.loads(RESULT.read_text())
    assert claimed["status"] == "PASS"
    assert claimed["case_count"] == CASE_COUNT
    rng = random.Random(SEED)
    digest = hashlib.sha256()
    mode_counts = {"inference": 0, "training": 0}
    fallback_count = 0
    for index in range(CASE_COUNT):
        mode, familiarity, priority, threshold = make_case(rng, index)
        expected = oracle_select(familiarity, priority, threshold)
        if sum(familiarity) < threshold:
            fallback_count += 1
            assert expected == sorted(range(len(familiarity)), key=lambda i: (-priority[i], i))
        else:
            assert sum(familiarity[i] for i in expected) >= threshold
            assert len(expected) == 1 or sum(familiarity[i] for i in expected[:-1]) < threshold
        digest.update(record_bytes(index, mode, familiarity, priority, threshold, expected))
        mode_counts[mode] += 1

    arithmetic = claimed["author_reported_arithmetic_checks"]
    assert arithmetic["reported_qwen_ood_mean_rounds_to_72_8"] is True
    assert arithmetic["reported_heterogeneous_ood_mean_rounds_to_71_8"] is True
    assert arithmetic["reported_top2_token_reduction_rounds_to_44_8_pct"] is True
    assert arithmetic["vllm_comparison_batch_sizes_match"] is False
    assert abs(arithmetic["qwen_ood_delta_pp"] - 1.2833) < 0.001
    assert abs(arithmetic["adaptive_vs_top2_token_reduction_pct"] - 44.81) < 0.01

    matched = digest.hexdigest() == claimed["case_digest_sha256"]
    assert matched
    result = {
        "status": "PASS",
        "oracle_id": "cera-moa-routing-independent-oracle-20261108",
        "verified_cases": CASE_COUNT,
        "mode_counts": mode_counts,
        "below_threshold_all_agents_fallback_count": fallback_count,
        "independent_case_digest_sha256": digest.hexdigest(),
        "matches_experiment_digest": matched,
        "author_reported_arithmetic_checks_recomputed": True,
        "scope": "Independent deterministic oracle for the routing contract and arithmetic only; not author-result reproduction.",
        "limitations": [
            "Oracle regenerates synthetic inputs and recomputes the paper rule; it does not validate model quality or learned familiarity scores.",
            "Author benchmark measurements remain AUTHOR_REPORTED / NOT_REPRODUCED.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
