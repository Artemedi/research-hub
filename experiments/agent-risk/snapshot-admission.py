"""Check what an offline replay can conclude from an authored decision journal."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys

COMMIT = "a1ab24aaf3c1e5bfbe47a24eaf4cf411bf0b3f1b"
LANES = ("agree", "stop", "retry-inspect", "retry-validate")
FIELDS = {"cut_seq", "context_digest", "prior_error", "remaining", "pending"}


def digest(value):
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def load_source(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Use a clean agent-risk checkout at " + COMMIT)
    sys.dont_write_bytecode = True
    path = root / "checks" / "verify_replay.py"
    spec = importlib.util.spec_from_file_location("upstream_finite_replay", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(lane, remaining, prior_error):
    context = {"task": "reconcile synthetic counters", "task_revision": 1, "lane": lane}
    snapshot = {
        "cut_seq": 3, "context_digest": digest(context), "prior_error": prior_error,
        "remaining": remaining, "pending": 2 if lane == "retry-inspect" else 3,
    }
    boundary = {"cut_seq": 3, "snapshot_digest": digest(snapshot), "context_digest": digest(context),
                "environment": "counter-machine/v1", "announced": False}
    baseline_error = prior_error or remaining == 2
    path = (("prior_error", prior_error), ("lane", lane), ("gate", "continue"),
            ("L", baseline_error))
    return path, boundary, snapshot


def full_oracle(lane, remaining, prior_error):
    """Independent decision table for the agreed, stopped and modified paths."""
    later_error_budgets = {"agree": {2}, "stop": set(),
                           "retry-inspect": {1}, "retry-validate": {0, 2}}
    return prior_error or remaining in later_error_budgets[lane]


def continue_from(boundary, snapshot):
    if not FIELDS.issubset(snapshot):
        return None, "missing_state"
    if (type(snapshot["remaining"]) is not int or not 0 <= snapshot["remaining"] <= 3
            or type(snapshot["pending"]) is not int or not 0 <= snapshot["pending"] <= 3
            or type(snapshot["prior_error"]) is not bool):
        return None, "invalid_state"
    if boundary["environment"] != "counter-machine/v1":
        return None, "environment_changed"
    if boundary["announced"]:
        return None, "policy_announced"
    if snapshot["cut_seq"] != boundary["cut_seq"]:
        return None, "wrong_cut"
    if snapshot["context_digest"] != boundary["context_digest"]:
        return None, "context_mismatch"
    if digest(snapshot) != boundary["snapshot_digest"]:
        return None, "snapshot_mismatch"

    # Simulate only the unobserved continuation in the authored machine.
    for _ in range(snapshot["remaining"]):
        if snapshot["pending"] == 0:
            return snapshot["prior_error"], "replayed"
        snapshot = {**snapshot, "pending": snapshot["pending"] - 1}
    return snapshot["prior_error"] or snapshot["pending"] % 2 == 1, "replayed"


def counterexamples(boundary, snapshot):
    missing_budget = {k: v for k, v in snapshot.items() if k != "remaining"}
    missing_context = {k: v for k, v in snapshot.items() if k != "context_digest"}
    edited_budget = {**snapshot, "remaining": (snapshot["remaining"] + 1) % 4}
    return {
        "missing_budget": (boundary, missing_budget, "missing_state"),
        "missing_context": (boundary, missing_context, "missing_state"),
        "negative_budget": (boundary, {**snapshot, "remaining": -1}, "invalid_state"),
        "wrong_cut": (boundary, {**snapshot, "cut_seq": 4}, "wrong_cut"),
        "changed_context": (boundary, {**snapshot, "context_digest": digest("other")}, "context_mismatch"),
        "edited_budget": (boundary, edited_budget, "snapshot_mismatch"),
        "environment_changed": ({**boundary, "environment": "counter-machine/v2"},
                                snapshot, "environment_changed"),
        "policy_announced": ({**boundary, "announced": True}, snapshot, "policy_announced"),
    }


def lab(upstream):
    steps = [
        upstream.rand("prior_error", lambda _: None, lambda _: {}),
        upstream.rand("lane", lambda _: None, lambda _: {}),
        upstream.dec("gate", "gate", 1, lambda history: history["lane"]),
    ]

    def old(_step, _lane):
        return "continue"

    def proposed(_step, lane):
        return {"agree": "continue", "stop": upstream.ABORT}.get(lane, "retry")

    def stop_valuation(prefix):
        return {prefix["prior_error"]: Fraction(1)}

    cases = []
    rejected = Counter()
    for lane, remaining, prior in itertools.product(LANES, range(4), (False, True)):
        path, boundary, snapshot = fixture(lane, remaining, prior)
        _, branch, _ = upstream.first_deviation(path, steps, old, proposed, "gate")
        oracle = full_oracle(lane, remaining, prior)
        expected_branch = {"agree": "agree", "stop": "terminal"}.get(lane, "continuing")
        assert branch == expected_branch
        if branch == "continuing":
            observed, reason = continue_from(boundary, snapshot)
            assert reason == "replayed"
            for name, (test_boundary, test_snapshot, expected) in counterexamples(boundary, snapshot).items():
                outcome, refusal = continue_from(test_boundary, test_snapshot)
                assert outcome is None and refusal == expected, (name, refusal)
                rejected[name] += 1
        else:
            part, unobserved, _ = upstream.replay(
                {path: Fraction(1)}, steps, old, proposed, "gate", stop_valuation,
            )
            assert unobserved == 0 and len(part) == 1
            observed = next(iter(part))
        assert observed == oracle, (lane, remaining, prior, observed, oracle)
        cases.append({"lane": lane, "remaining": remaining, "prior_error": prior,
                      "branch": branch, "oracle": oracle, "replay": observed})

    # Cases that produce the same recorded path retain their full unit weight.
    baseline = Counter(fixture(row["lane"], row["remaining"], row["prior_error"])[0] for row in cases)
    known, uncertain, _ = upstream.replay(
        {path: Fraction(count, len(cases)) for path, count in baseline.items()},
        steps, old, proposed, "gate", stop_valuation,
    )
    known_error = known.get(True, 0)
    full_rate = Fraction(sum(row["oracle"] for row in cases), len(cases))
    assert known_error <= full_rate <= known_error + uncertain
    assert uncertain == Fraction(sum(row["branch"] == "continuing" for row in cases), len(cases))
    # Different budgets can leave the very same baseline path and different continuation outcomes.
    assert fixture("retry-inspect", 0, False)[0] == fixture("retry-inspect", 1, False)[0]
    assert full_oracle("retry-inspect", 0, False) is False
    assert full_oracle("retry-inspect", 1, False) is True
    return {
        "case_count": len(cases), "branches": dict(Counter(row["branch"] for row in cases)),
        "log_only_unknown_fraction": str(uncertain),
        "log_only_outer_bounds": [str(known_error), str(known_error + uncertain)],
        "full_oracle_error_fraction": str(full_rate),
        "replay_mismatches": sum(row["oracle"] != row["replay"] for row in cases),
        "unknown_controls_by_reason": dict(rejected), "budget_ambiguity_control": True,
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    upstream = load_source(args.source.resolve())
    receipt = lab(upstream)
    assert lab(upstream) == lab(upstream) == receipt
    print(json.dumps({"source_commit": COMMIT, "repeat_count": 3, **receipt}, indent=2))


if __name__ == "__main__":
    main()
