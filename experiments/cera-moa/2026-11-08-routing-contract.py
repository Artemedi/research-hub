#!/usr/bin/env python3
"""Synthetic contract check for CERA-MoA cumulative-threshold routing.

This tests the published selection rule only. It does not implement the
familiarity learner, LoRA experts, RL training, model inference, or benchmarks.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

SEED = 20261108
CASE_COUNT = 10_000
SOURCE_SHA256 = "13f6536287ff7ebec0a21663f4d21fc61ce05c82d14ab14448f4080bed18bf0f"
OUTPUT = Path("data/results/cera-moa/2026-11-08-routing-contract.json")


def select_agents(familiarity: list[float], priority: list[float], threshold: float) -> list[int]:
    """Apply the paper's priority ordering and familiarity-sum cutoff."""
    if not familiarity or len(familiarity) != len(priority):
        raise ValueError("familiarity and priority must be non-empty and equal length")
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be finite and positive")
    if any(not math.isfinite(x) or x < 0 or x > 1 for x in familiarity):
        raise ValueError("familiarity scores must be finite and in [0, 1]")
    if any(not math.isfinite(x) for x in priority):
        raise ValueError("priority scores must be finite")

    order = sorted(range(len(familiarity)), key=lambda i: (-priority[i], i))
    if sum(familiarity) < threshold:
        return order

    selected: list[int] = []
    cumulative = 0.0
    for index in order:
        selected.append(index)
        cumulative += familiarity[index]
        if cumulative >= threshold:
            break
    return selected


def make_case(rng: random.Random, index: int) -> tuple[str, list[float], list[float], float]:
    n_agents = 3 if index % 5 == 0 else 4
    distances = [rng.uniform(0.0, 2.0) for _ in range(n_agents)]
    familiarity = [math.exp(-2.0 * distance) for distance in distances]
    threshold = 0.7 if index % 3 else rng.choice((0.5, 0.6, 0.8, 0.9))

    if index % 4 == 0:
        mode = "inference"
        priority = list(familiarity)  # exploration bonuses are disabled at inference
    else:
        mode = "training"
        total_routed = rng.randint(1, 6000)
        allocated = [rng.randint(0, total_routed) for _ in range(n_agents)]
        entropy = [rng.random() for _ in range(n_agents)]
        entropy_weight = 0.2 if n_agents == 3 else 2.0
        priority = [
            familiarity[i]
            + 2.0 * math.sqrt(math.log(total_routed) / (allocated[i] + 1))
            + entropy_weight * entropy[i]
            for i in range(n_agents)
        ]
        if index % 37 == 0:
            priority = [round(value, 4) for value in priority]  # deterministic tie coverage
    return mode, familiarity, priority, threshold


def canonical_record(index: int, mode: str, familiarity: list[float], priority: list[float], threshold: float, selected: list[int]) -> bytes:
    record = {
        "i": index,
        "mode": mode,
        "f": [round(x, 12) for x in familiarity],
        "p": [round(x, 12) for x in priority],
        "tau": round(threshold, 12),
        "selected": selected,
    }
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def arithmetic_checks() -> dict[str, float | bool]:
    qwen_cera = mean([83.0, 82.5, 71.3, 92.7, 65.6, 41.6])
    qwen_at_grpo = mean([78.6, 84.4, 69.1, 93.2, 64.8, 38.9])
    hetero_cera = mean([83.4, 77.3, 71.1, 92.7, 62.4, 44.1])
    hetero_at_grpo = mean([81.3, 83.8, 67.8, 92.9, 50.9, 37.6])
    adaptive_tokens, top2_tokens, top1_tokens = 367.77, 666.37, 325.70
    router_ms, native_ms, vllm_ms = 11.87, 1350.32, 154.09
    return {
        "qwen_ood_cera_mean": round(qwen_cera, 4),
        "qwen_ood_at_grpo_mean": round(qwen_at_grpo, 4),
        "qwen_ood_delta_pp": round(qwen_cera - qwen_at_grpo, 4),
        "heterogeneous_ood_cera_mean": round(hetero_cera, 4),
        "heterogeneous_ood_at_grpo_mean": round(hetero_at_grpo, 4),
        "heterogeneous_ood_delta_pp": round(hetero_cera - hetero_at_grpo, 4),
        "adaptive_vs_top2_token_reduction_pct": round((top2_tokens - adaptive_tokens) / top2_tokens * 100, 4),
        "adaptive_vs_top2_id_delta_pp": -0.1,
        "adaptive_vs_top2_ood_delta_pp": 0.3,
        "adaptive_vs_top1_token_increase_pct": round((adaptive_tokens - top1_tokens) / top1_tokens * 100, 4),
        "router_vs_native_batch1_pct": round(router_ms / native_ms * 100, 4),
        "router_vs_vllm_batch32_pct": round(router_ms / vllm_ms * 100, 4),
        "vllm_comparison_batch_sizes_match": False,
        "reported_qwen_ood_mean_rounds_to_72_8": round(qwen_cera, 1) == 72.8,
        "reported_heterogeneous_ood_mean_rounds_to_71_8": round(hetero_cera, 1) == 71.8,
        "reported_top2_token_reduction_rounds_to_44_8_pct": round((top2_tokens - adaptive_tokens) / top2_tokens * 100, 1) == 44.8,
    }


def main() -> None:
    rng = random.Random(SEED)
    digest = hashlib.sha256()
    selected_counts: Counter[int] = Counter()
    mode_counts: Counter[str] = Counter()
    fallback_count = 0
    minimal_prefix_checks = 0

    for index in range(CASE_COUNT):
        mode, familiarity, priority, threshold = make_case(rng, index)
        selected = select_agents(familiarity, priority, threshold)
        order = sorted(range(len(familiarity)), key=lambda i: (-priority[i], i))
        assert selected == order[: len(selected)]
        assert len(selected) == len(set(selected))
        if sum(familiarity) < threshold:
            assert selected == order
            fallback_count += 1
        else:
            assert sum(familiarity[i] for i in selected) >= threshold
            assert len(selected) == 1 or sum(familiarity[i] for i in selected[:-1]) < threshold
        if mode == "inference":
            assert priority == familiarity
        digest.update(canonical_record(index, mode, familiarity, priority, threshold, selected))
        selected_counts[len(selected)] += 1
        mode_counts[mode] += 1
        minimal_prefix_checks += 1

    edge_cases = {
        "priority_order_not_familiarity_order": select_agents([0.6, 0.5, 0.1], [0.2, 0.9, 0.1], 0.7) == [1, 0],
        "below_threshold_selects_all": select_agents([0.1, 0.2], [2.0, 1.0], 0.7) == [0, 1],
        "stable_tie_break_by_index": select_agents([0.4, 0.4, 0.4], [1.0, 1.0, 1.0], 0.7) == [0, 1],
        "inference_uses_familiarity_order": select_agents([0.9, 0.5, 0.2], [0.9, 0.5, 0.2], 0.7) == [0],
    }
    assert all(edge_cases.values())

    result = {
        "status": "PASS",
        "experiment_id": "cera-moa-routing-contract-20261108",
        "source_url": "https://arxiv.org/html/2609.18779v1",
        "source_sha256": SOURCE_SHA256,
        "seed": SEED,
        "case_count": CASE_COUNT,
        "mode_counts": dict(sorted(mode_counts.items())),
        "selected_agent_count_histogram": {str(k): selected_counts[k] for k in sorted(selected_counts)},
        "below_threshold_all_agents_fallback_count": fallback_count,
        "minimal_prefix_contract_checks": minimal_prefix_checks,
        "case_digest_sha256": digest.hexdigest(),
        "edge_controls": edge_cases,
        "author_reported_arithmetic_checks": arithmetic_checks(),
        "scope": "Synthetic deterministic routing-rule contract plus arithmetic recomputation of values printed in the paper tables.",
        "limitations": [
            "No author code, weights, datasets, hidden states, LoRA adapters, RL training, or benchmark tasks were executed.",
            "Synthetic familiarity values are generated from bounded distances; they do not model a trained familiarity estimator.",
            "Arithmetic checks verify only the calculation from author-reported table values, not the underlying measurements.",
            "No target project or production runtime was modified or exercised.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "case_count", "mode_counts", "below_threshold_all_agents_fallback_count", "case_digest_sha256", "author_reported_arithmetic_checks")}, indent=2))


if __name__ == "__main__":
    main()
