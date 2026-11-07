#!/usr/bin/env python3
"""Pinned HRP author solver vs independent analytic two-action bandit oracle.

Reproduces Appendix D.5 ceiling/mismatch/reversal in 30 synthetic bandits.
No model inference, training, natural agent tasks, production input or network.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

import numpy as np
from environment.hrp_miniwob.oracle import evaluate, solve

ROOT = Path(os.environ["HRP_ROOT"]).resolve()
OUTPUT = Path(os.environ["OUTPUT"]).resolve()
PIN = "c91d859c21f38f10e358091265eea6e571e23e47"
SOURCE = ROOT / "environment/hrp_miniwob/oracle.py"
SOURCE_HASH = "485f954eddf8b674f842ff7dbb723e17600d755ae47417a93bd9a8e8e565d15d"
REF = np.array([[0.5, 0.5]])
END = np.array([[-1, -1]], dtype=np.int64)
GAMMA = 0.8
REPETITIONS = 20000


def check_source():
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    assert commit == PIN and sha == SOURCE_HASH


def soft_entropy_cost(p, tau):
    return tau * (p * math.log(2*p) + (1-p) * math.log(2*(1-p)))


def manual_case(tau, u):
    # Appendix D.5, independent scalar implementation (no author functions).
    p = 1 / (1 + math.exp(-1/tau))
    z1 = math.log1p(math.exp(1/tau)) - math.log(2)
    z2 = math.log1p(math.exp(u/tau)) - math.log(2)
    c1, c2 = tau * z1, tau * z2
    penalty = soft_entropy_cost(p, tau)
    j1 = p - penalty
    j2 = u * (1-p) - penalty
    q1 = 1 / (1 + math.exp(u/tau))
    mismatch = tau * (p * math.log(p/q1) +
                      (1-p)*math.log((1-p)/(1-q1)))
    return {
        "p_first": p, "C_source": c1, "C_target": c2,
        "J_source": j1, "J_frozen_target": j2,
        "M_frozen_target": mismatch,
        "J_adapted_target": c2,
        "threshold": math.exp(1/tau),
        "reversal": c2 > c1 and j2 < j1,
    }


def one(tau, u, seed):
    first = solve(END, np.array([[1., 0.]]), REF, GAMMA, tau)
    target_rewards = np.array([[0., u]])
    last = solve(END, target_rewards, REF, GAMMA, tau)
    before = evaluate(END, np.array([[1., 0.]]), REF,
                      first.policy, 0, GAMMA, tau)
    frozen = evaluate(END, target_rewards, REF, first.policy, 0, GAMMA, tau)
    adapted = evaluate(END, target_rewards, REF, last.policy, 0, GAMMA, tau)
    expected = manual_case(tau, u)
    observed = {
        "p_first": float(first.policy[0, 0]),
        "C_source": float(first.value[0]),
        "C_target": float(last.value[0]),
        "J_source": before.return_value,
        "J_frozen_target": frozen.return_value,
        "J_adapted_target": adapted.return_value,
        "M_frozen_target": float(last.value[0] - frozen.return_value),
    }
    residual = {key: abs(observed[key]-expected[key]) for key in observed}
    assert max(residual.values()) < 2e-10, (tau, u, residual)
    assert abs(observed["C_target"]-observed["J_frozen_target"]-
               expected["M_frozen_target"]) < 2e-10
    assert expected["reversal"] == (
        observed["C_target"] > observed["C_source"] and
        observed["J_frozen_target"] < observed["J_source"]
    )
    # Metamorphic semantic relabeling: reward and policy columns are moved
    # together. The value remains invariant when action semantics stay fixed.
    swap = np.array([1, 0])
    reordered = solve(END, target_rewards[:, swap],
                      REF[:, swap], GAMMA, tau)
    eval_reordered = evaluate(END, target_rewards[:, swap], REF[:, swap],
                              first.policy[:, swap], 0, GAMMA, tau)
    assert abs(reordered.value[0]-last.value[0]) < 2e-10
    assert abs(eval_reordered.return_value-frozen.return_value) < 2e-10
    # Independent stochastic action sampling of a frozen policy; used only
    # as a check on the exact analytic return, not as a separate model.
    rng = np.random.default_rng(seed)
    actions = rng.choice(2, p=first.policy[0], size=REPETITIONS)
    costs = tau * np.log(first.policy[0, actions] / REF[0, actions])
    sampled = float(np.mean(target_rewards[0, actions]-costs))
    std = float(np.std(target_rewards[0, actions]-costs, ddof=1))
    se = std / math.sqrt(REPETITIONS)
    assert abs(sampled-expected["J_frozen_target"]) < max(0.015, 5*se)
    return {
        "tau": tau, "target_reward_second": u, "seed": seed,
        "oracle": expected, "author": observed,
        "max_formula_error": max(residual.values()),
        "permutation_invariant": True,
        "monte_carlo_return": sampled,
        "monte_carlo_standard_error": se,
    }


def negatives():
    controls = {}
    source = np.array([[1., 0.]])
    invalid = (
        ("zero_tau", lambda: solve(END, source, REF, GAMMA, 0)),
        ("non_normalized_reference", lambda: solve(
            END, source, np.array([[0.7, 0.7]]), GAMMA, 0.5)),
        ("negative_reference", lambda: solve(
            END, source, np.array([[-0.1, 1.1]]), GAMMA, 0.5)),
        ("bad_successor", lambda: solve(
            np.array([[0, -1]]), source, REF, GAMMA, 0.5)),
        ("bad_policy", lambda: evaluate(
            END, source, REF, np.array([[0.3, 0.3]]), 0, GAMMA, 0.5)),
    )
    for title, call in invalid:
        try:
            call()
        except ValueError as error:
            controls[title] = {"rejected": True, "error_type": type(error).__name__}
        else:
            controls[title] = {"rejected": False}
    assert all(record["rejected"] for record in controls.values())
    return controls


def main():
    check_source()
    taus = (0.35, 0.5, 0.75, 1.0, 1.25)
    cases = []
    for i, tau in enumerate(taus):
        limit = math.exp(1/tau)
        for j, u in enumerate((0.8, 1.0, 1.2, 1.3, (1+limit)/2,
                               limit*1.05)):
            cases.append(one(tau, u, 20261107+i*10+j))
    assert len(cases) == 30
    reversals = sum(c["oracle"]["reversal"] for c in cases)
    controls = negatives()
    result = {
        "date": "2026-11-07",
        "study": "decision-geometry-harness",
        "paper_url": "https://arxiv.org/html/2610.37255v2",
        "paper_html_sha256": "5e37b2455cbe94cf1abbf932d28c96e5ee9f9bff18a547c76f1541387a58e4ce",
        "author_repo_pin": PIN,
        "author_solver_path": "environment/hrp_miniwob/oracle.py",
        "author_solver_sha256": SOURCE_HASH,
        "oracle": "Independent scalar logsumexp and KL from Appendix D.5; author finite-MDP solver is separate implementation",
        "cases": len(cases),
        "reversal_cases": reversals,
        "author_vs_closed_form": "30/30 PASS",
        "semantic_action_relabeling_invariants": "30/30 PASS",
        "monte_carlo_checks": "30/30 PASS",
        "n_per_case": REPETITIONS,
        "negative_controls": controls,
        "negative_controls_passed": sum(v["rejected"] for v in controls.values()),
        "details": cases,
        "disposition": "ACCEPT_BOUNDED_EXACT_BANDIT_THEORY",
        "limitations": [
            "The tiny one-state two-action discounted-terminating bandit is not MiniWoB++",
            "No trained agent weights, frozen language model or actual interface presentation changed",
            "Return is a KL-regularized analytic objective, not real downstream task success",
            "Exact analytic and numerical agreement does not establish prevalence in deployed systems",
            "Monte Carlo checks use synthetic sampled semantic decisions, not ZCode/LLM inference",
            "Actual author MiniWoB training and Terminal-Bench teacher runs require GPUs and services not used here",
            "No changes to any target project or production"
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({
        "cases": len(cases), "reversals": reversals,
        "invalid_inputs_rejected": result["negative_controls_passed"],
        "max_abs_error": max(c["max_formula_error"] for c in cases)
    }))


if __name__ == "__main__":
    main()
