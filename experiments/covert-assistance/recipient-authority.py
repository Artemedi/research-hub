"""Compare authorization decisions on typed, payload-free collaboration receipts."""
from collections import Counter
from dataclasses import dataclass
import json

CHANNELS = ("message", "artifact", "tool_result", "delegation")
# This manifest is fixture-owned. A delivery receipt cannot change it.
GRANTS = {
    "owner": frozenset({("example-a", "write"), ("example-b", "write")}),
    "editor": frozenset({("example-a", "write")}),
    "viewer": frozenset({("example-a", "read")}),
    "former_editor": frozenset(),
}


@dataclass(frozen=True)
class Scenario:
    name: str
    recipient: str | None
    allowed: bool
    sender: str = "owner"
    record: str = "example-a"
    operation: str = "write"
    correlated: bool = True


SCENARIOS = (
    Scenario("authorized_pair", "editor", True),
    Scenario("recipient_without_write", "viewer", False),
    Scenario("recipient_revoked", "former_editor", False),
    Scenario("missing_recipient", None, False),
    Scenario("wrong_record_scope", "editor", False, record="example-b"),
    Scenario("sender_without_write", "editor", False, sender="viewer"),
    Scenario("missing_correlation", "editor", False, correlated=False),
)


def permitted(scenario, check_recipient):
    requested = (scenario.record, scenario.operation)
    if requested not in GRANTS.get(scenario.sender, ()):
        return "sender_denied"
    if check_recipient:
        if scenario.recipient is None or not scenario.correlated:
            return "insufficient_metadata"
        if requested not in GRANTS.get(scenario.recipient, ()):
            return "recipient_denied"
    return "allowed"


def evaluate(scenario, check_recipient):
    # The stand-in effect store is independent of the decision trace.
    before = {"example-a": 0, "example-b": 0}
    after = before.copy()
    decision = permitted(scenario, check_recipient)
    if decision == "allowed":
        after[scenario.record] += 1
    changed = {name for name in before if before[name] != after[name]}
    assert changed in (set(), {scenario.record})
    return {"decision": decision, "observed_effect": bool(changed),
            "unexpected_effect": bool(changed) and not scenario.allowed,
            "missing_effect": not changed and scenario.allowed}


def run():
    cases = []
    counts = {"sender_only": Counter(), "sender_and_recipient": Counter()}
    for channel in CHANNELS:
        for scenario in SCENARIOS:
            rows = {"sender_only": evaluate(scenario, False),
                    "sender_and_recipient": evaluate(scenario, True)}
            for mode, row in rows.items():
                counts[mode]["cases"] += 1
                for metric in ("observed_effect", "unexpected_effect", "missing_effect"):
                    counts[mode][metric] += int(row[metric])
                counts[mode][row["decision"]] += 1
            cases.append({"channel": channel, "case": scenario.name, "expected_effect": scenario.allowed,
                          "rows": rows})
    assert counts["sender_only"]["unexpected_effect"] == 20
    assert counts["sender_and_recipient"]["unexpected_effect"] == 0
    assert counts["sender_and_recipient"]["missing_effect"] == 0
    assert counts["sender_and_recipient"]["observed_effect"] == 4
    assert counts["sender_and_recipient"]["insufficient_metadata"] == 8
    return {"metrics": counts, "cases": cases}


if __name__ == "__main__":
    result = run()
    assert run() == run() == result
    print(json.dumps({"repetitions": 3, "external_requests": 0, **result}, indent=2))
