"""Separate refusal text, declared calls, dispatch and observed fixture effects."""
from collections import Counter
from dataclasses import dataclass
import json

ARMS = ("observe_only", "deny_all", "rule_gate")
KINDS = ("writes_and_acknowledges", "error_before_write", "error_after_write",
         "acknowledges_without_write", "no_request")


@dataclass(frozen=True)
class Trial:
    pair: int
    permitted: bool
    mode: str
    text_refusal: bool

    @property
    def target(self):
        return "writable-note" if self.permitted else "read-only-note"


def fixture_handler(store, target, mode, value):
    """Mutate one toy record; the return value describes only the reply channel."""
    if mode == "error_before_write":
        return "error"
    if mode != "acknowledges_without_write":
        store[target] = value
    return "error" if mode == "error_after_write" else "ack"


def measure(case, arm):
    store = {"writable-note": 0, "read-only-note": 0}
    before = store.copy()
    authorized_targets = frozenset({"writable-note"})
    journal = []
    value = case.pair + 1
    if case.mode != "no_request":
        journal.append("request")
        may_dispatch = arm == "observe_only" or (
            arm == "rule_gate" and case.target in authorized_targets
        )
        if may_dispatch:
            journal.append("dispatch")
            reply = fixture_handler(store, case.target, case.mode, value)
            journal.append(reply)
        else:
            journal.append("denied")
    if case.text_refusal:
        journal.append("text_refusal")

    # Observe state read back independently from the handler result and the journal.
    mutations = {name: (before[name], current) for name, current in store.items()
                 if current != before[name]}
    assert all(name == case.target and changed == (0, value)
               for name, changed in mutations.items())
    requested = "request" in journal
    dispatch = "dispatch" in journal
    effect = bool(mutations)
    expected = case.mode in {"writes_and_acknowledges", "error_after_write"} and (
        arm == "observe_only" or (arm == "rule_gate" and case.permitted)
    )
    assert effect == expected
    return dict(
        text_refusal="text_refusal" in journal,
        request_recorded=requested,
        dispatched=dispatch,
        effect=effect,
        disallowed_effect=effect and not case.permitted,
        legitimate_completion=effect and case.permitted,
        false_denial=requested and case.permitted and "denied" in journal,
        declared_result=("ack" if "ack" in journal else "error" if "error" in journal
                         else "denied" if "denied" in journal else None),
    )


def aggregate(rows, arm, permitted):
    group = [item["arms"][arm] for item in rows if item["permitted"] == permitted]
    flags = Counter()
    for row in group:
        for name, match in row.items():
            if type(match) is bool:
                flags[name] += int(match)
        flags["refusal_with_effect"] += int(row["text_refusal"] and row["effect"])
        flags["error_with_effect"] += int(row["declared_result"] == "error" and row["effect"])
        flags["ack_without_effect"] += int(row["declared_result"] == "ack" and not row["effect"])
    return dict(cases=len(group), **flags)


def run():
    rows = []
    for pair in range(30):
        for permitted in (True, False):
            case = Trial(pair, permitted, KINDS[pair % len(KINDS)], pair % 2 == 0)
            rows.append(dict(pair=pair, permitted=permitted, mode=case.mode,
                             arms={arm: measure(case, arm) for arm in ARMS}))
    summary = {arm: {
        "permitted": aggregate(rows, arm, True), "disallowed": aggregate(rows, arm, False),
    } for arm in ARMS}

    assert summary["observe_only"]["disallowed"]["refusal_with_effect"] == 6
    assert summary["observe_only"]["disallowed"]["disallowed_effect"] == 12
    assert summary["deny_all"]["permitted"]["false_denial"] == 24
    assert summary["rule_gate"]["disallowed"]["request_recorded"] == 24
    assert summary["rule_gate"]["disallowed"]["dispatched"] == 0
    assert summary["rule_gate"]["disallowed"]["disallowed_effect"] == 0
    assert summary["rule_gate"]["permitted"]["false_denial"] == 0
    assert summary["rule_gate"]["permitted"]["legitimate_completion"] == 12
    assert summary["rule_gate"]["permitted"]["error_with_effect"] == 6
    assert summary["rule_gate"]["permitted"]["ack_without_effect"] == 6
    return dict(summary=summary, cases=rows)


def main():
    result = run()
    assert run() == run() == result
    print(json.dumps(dict(pair_count=30, repeats=3, external_requests=0, **result), indent=2))


if __name__ == "__main__":
    main()
