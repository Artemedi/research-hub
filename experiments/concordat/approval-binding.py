"""Measure order checks and proposal-bound approval using a toy state change."""
import argparse
from collections import Counter
from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import subprocess
import sys

import concordat
from concordat import Agent, ProtocolViolation, human, tool

COMMIT = "26fd8b1c3a823a4c6be39eedbe370a241623a4cc"
SCENARIOS = ("valid", "repeated_in_session", "missing", "rejected", "previous_revision",
             "other_record", "other_value", "expired", "unbound_yes", "changed_after_approval")
ARMS = ("unvalidated", "state_only", "proposal_bound")


@dataclass(frozen=True)
class Change:
    record: str
    revision: int
    value: int


@dataclass(frozen=True)
class Confirmation:
    change: Change
    allowed: bool = True
    expires_at: int = 60


class ApprovalMismatch(ValueError):
    """A toy write is different from the one that was shown for approval."""


class RecordSession(Agent):
    final = {"verified", "refused"}

    def __init__(self, record, authorize, enforce_binding):
        super().__init__(approver=authorize)
        self.store = {record: 0, record + "-other": 0}
        self.effects = []
        self.proposed = None
        self.enforce_binding = enforce_binding

    @tool(when="start", then="inspected")
    def inspect_record(self):
        return dict(self.store)

    @tool(when="inspected", then="pending")
    def propose_change(self, change: Change):
        self.proposed = change
        return asdict(change)

    @human(when="pending", approve="approved", reject="refused")
    def confirm_change(self):
        return self.proposed

    @tool(when="approved", then="applied")
    def apply_change(self, change: Change):
        if self.enforce_binding and change != self.proposed:
            raise ApprovalMismatch("Requested change no longer matches the approved proposal.")
        self.store[change.record] = change.value
        self.effects.append(change)
        return self.store[change.record]

    @tool(when="applied", then="verified")
    def verify_change(self):
        return dict(self.store)


def fixture(index, scenario):
    change = Change(f"fixture-{index}", 2, 100 + index)
    authorization = Confirmation(change)
    sent = change
    text_yes = scenario not in {"missing", "rejected"}
    if scenario in {"missing", "unbound_yes"}:
        authorization = None
    elif scenario == "rejected":
        authorization = replace(authorization, allowed=False)
    elif scenario == "previous_revision":
        authorization = replace(authorization, change=replace(change, revision=1))
    elif scenario == "other_record":
        authorization = replace(authorization, change=replace(change, record=change.record + "-other"))
    elif scenario == "other_value":
        authorization = replace(authorization, change=replace(change, value=change.value + 1))
    elif scenario == "expired":
        authorization = replace(authorization, expires_at=39)
    elif scenario == "changed_after_approval":
        sent = replace(change, value=change.value + 1)
    return change, authorization, sent, text_yes


def exercise(index, scenario, arm):
    proposal, confirmation, attempted, text_yes = fixture(index, scenario)
    calls = 2 if scenario == "repeated_in_session" else 1

    def authorize(_step, shown_change):
        if arm == "state_only":
            return text_yes
        return (confirmation is not None and confirmation.allowed
                and 40 < confirmation.expires_at and confirmation.change == shown_change)

    session = RecordSession(proposal.record, authorize, arm == "proposal_bound")
    initial = session.inspect_record()
    session.propose_change(proposal)
    if scenario != "missing" and arm != "unvalidated":
        session.confirm_change()
    denials = Counter()
    for _ in range(calls):
        try:
            if arm == "unvalidated":
                # Control path without state gating, on the same artificial dictionary.
                session.store[attempted.record] = attempted.value
                session.effects.append(attempted)
            else:
                session.apply_change(attempted)
        except ProtocolViolation:
            denials["session_order"] += 1
        except ApprovalMismatch:
            denials["proposal_binding"] += 1
    actual = session.verify_change() if session.state == "applied" else dict(session.store)

    # The authored owner oracle allows one matching effect only in the two labeled cases.
    has_valid_consent = scenario in {"valid", "repeated_in_session"}
    independent_expected = [proposal] if has_valid_consent else []
    actual_effects = session.effects
    effect_counts = Counter(actual_effects)
    invalid = list((effect_counts - Counter(independent_expected)).elements())
    missing = list((Counter(independent_expected) - effect_counts).elements())
    assert actual[proposal.record + "-other"] == initial[proposal.record + "-other"]
    assert actual[proposal.record] == (
        actual_effects[-1].value if actual_effects else initial[proposal.record]
    )
    return dict(
        effects=len(actual_effects), unexpected_effects=len(invalid),
        missing_expected_effects=len(missing), denials=dict(denials), state=session.state,
        change_verified=session.state == "verified",
    )


def lab():
    result = {}
    for scenario in SCENARIOS:
        cases = [dict(case=index, arms={arm: exercise(index, scenario, arm) for arm in ARMS})
                 for index in range(5)]
        result[scenario] = cases
    metrics = {}
    for arm in ARMS:
        counted = Counter()
        for cases in result.values():
            for case in cases:
                row = case["arms"][arm]
                counted.update({key: row[key] for key in ("effects", "unexpected_effects",
                                                        "missing_expected_effects")})
                counted["verified"] += int(row["change_verified"])
        metrics[arm] = dict(counted)
    assert metrics["unvalidated"]["unexpected_effects"] == 45
    assert metrics["state_only"]["unexpected_effects"] == 30
    assert metrics["proposal_bound"]["unexpected_effects"] == 0
    assert metrics["proposal_bound"]["missing_expected_effects"] == 0
    assert metrics["proposal_bound"]["verified"] == 10
    assert all(row["arms"]["proposal_bound"]["denials"] == {"proposal_binding": 1}
               for row in result["changed_after_approval"])
    assert all(row["arms"]["state_only"]["denials"] == {"session_order": 1}
               for row in result["repeated_in_session"])
    return {"metrics": metrics, "cases": result}


def verify_source(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Use a clean Concordat checkout at " + COMMIT)
    installed = Path(concordat.__file__).parent
    paths = [p for p in (root / "src" / "concordat").glob("*.py")]
    assert paths and {p.name for p in paths} == {p.name for p in installed.glob("*.py")}
    for path in paths:
        assert (installed / path.name).read_bytes() == path.read_bytes(), path.name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    verify_source(args.source.resolve())
    first = lab()
    assert lab() == lab() == first
    print(json.dumps(dict(source_commit=COMMIT, package=concordat.__version__,
                          python=sys.version.split()[0], case_count=50,
                          repetitions=3, external_requests=0, **first), indent=2))


if __name__ == "__main__":
    main()
