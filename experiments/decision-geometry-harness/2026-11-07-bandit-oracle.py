#!/usr/bin/env python3
"""Decimal/stdlib independent audit of HRP's pinned 30-bandit result.

This validator does not import the author's NumPy solver nor the runner.
It checks all 30 exact KL formulas and catches a deliberately corrupted value.
"""
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path

EVIDENCE = Path(os.environ["EVIDENCE"])
OUTPUT = Path(os.environ["OUTPUT"])
PAPER_SHA = "5e37b2455cbe94cf1abbf932d28c96e5ee9f9bff18a547c76f1541387a58e4ce"
SOURCE_SHA = "485f954eddf8b674f842ff7dbb723e17600d755ae47417a93bd9a8e8e565d15d"
TOL = Decimal("0.00000000001")


def value(number):
    return Decimal(str(number))


def close(observed, truth):
    return abs(value(observed) - truth) < TOL


def check(row):
    tau, u = value(row["tau"]), value(row["target_reward_second"])
    exp_a = (Decimal(1) / tau).exp()
    exp_b = (u / tau).exp()
    p = exp_a / (Decimal(1) + exp_a)
    q = Decimal(1) / (Decimal(1) + exp_b)
    c_source = tau * ((Decimal(1) + exp_a)/2).ln()
    c_target = tau * ((Decimal(1) + exp_b)/2).ln()
    entropy_cost = tau*(p*(2*p).ln()+(1-p)*(2*(1-p)).ln())
    j_source = p - entropy_cost
    j_target = u*(1-p)-entropy_cost
    mismatch = tau*(p*(p/q).ln()+(1-p)*((1-p)/(1-q)).ln())
    expected = {
        "p_first": p,
        "C_source": c_source,
        "C_target": c_target,
        "J_source": j_source,
        "J_frozen_target": j_target,
        "M_frozen_target": mismatch,
        "J_adapted_target": c_target,
        "threshold": exp_a,
    }
    for key, truth in expected.items():
        if not close(row["oracle"][key], truth):
            return False, "scalar_formula_oracle_" + key
        if key in row["author"] and not close(row["author"][key], truth):
            return False, "author_solver_" + key
    reversal = c_target > c_source and j_target < j_source
    if row["oracle"]["reversal"] != reversal:
        return False, "incorrect_reversal_label"
    if row["permutation_invariant"] is not True:
        return False, "permutation_failed"
    if row["monte_carlo_standard_error"] < 0:
        return False, "negative_mc_se"
    if abs(row["monte_carlo_return"] - float(j_target)) > max(
            0.015, 5*row["monte_carlo_standard_error"]):
        return False, "mc_outside_declared_bound"
    if row["seed"] < 20261107 or row["seed"] > 20261157:
        return False, "unexpected_seed"
    return True, "PASS"


def main():
    with localcontext() as context:
        context.prec = 70
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        assert data["paper_html_sha256"] == PAPER_SHA
        assert data["author_solver_sha256"] == SOURCE_SHA
        assert data["author_repo_pin"] == "c91d859c21f38f10e358091265eea6e571e23e47"
        assert data["cases"] == 30 and len(data["details"]) == 30
        assert data["n_per_case"] == 20000
        assert len({(x["tau"], x["target_reward_second"])
                    for x in data["details"]}) == 30
        verdicts = [check(row) for row in data["details"]]
        assert all(v[0] for v in verdicts), verdicts
        assert sum(x["oracle"]["reversal"] for x in data["details"]) == 15
        assert data["reversal_cases"] == 15
        assert data["negative_controls_passed"] == 5
        assert len(data["negative_controls"]) == 5
        assert all(x["rejected"] for x in data["negative_controls"].values())

        changed = json.loads(json.dumps(data["details"][0]))
        changed["author"]["J_frozen_target"] += 0.1
        passed, reason = check(changed)
        assert not passed and reason.startswith("author_solver_")
        changed = json.loads(json.dumps(data["details"][0]))
        changed["oracle"]["reversal"] = not changed["oracle"]["reversal"]
        passed2, reason2 = check(changed)
        assert not passed2 and reason2 == "incorrect_reversal_label"
        result = {
            "study": "decision-geometry-harness",
            "date": "2026-11-07",
            "source_pin": data["author_repo_pin"],
            "source_sha256": SOURCE_SHA,
            "paper_html_sha256": PAPER_SHA,
            "input_results_sha256": hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(),
            "verified_cases": len(verdicts),
            "reversals_verified": 15,
            "mutation_controls_rejected": 2,
            "independent_math": "decimal.Decimal prec=70 scalar KL/logsumexp; does not import official solver",
            "status": "PASS_EXACT_DECIMAL_ORACLE",
            "limitations": [
                "Rechecks mathematical bandit outputs, not model-training outcomes",
                "Checks reported stochastic samples against expected 5SE interval rather than replaying their RNG draws",
                "Shared theorem assumptions are not an independent scientific peer review"
            ],
        }
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
        print(json.dumps({
            "verified": result["verified_cases"],
            "reversals": result["reversals_verified"],
            "mutation_rejections": result["mutation_controls_rejected"],
        }))


if __name__ == "__main__":
    main()
