#!/usr/bin/env python3
"""Independent Python replay oracle for JavaScript's synthetic KV event traces."""
import hashlib
import json
import os
from pathlib import Path

EVIDENCE = Path(os.environ["EVIDENCE"])
OUTPUT = Path(os.environ["OUTPUT"])
PRIMITIVES = ["append", "fork", "pin", "one_off", "spawn",
              "replace", "remove", "unpin"]


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def main():
    experiment = json.loads(EVIDENCE.read_text())
    assert (experiment["synthetic_sequences"], experiment["events_per_sequence"]) == (25, 8)
    assert experiment["negative_controls_passed"] == 5
    for row in experiment["sequences"]:
        assert row["id"] in range(25)
        assert row["context"] == f"synthetic-context-{row['id']}"
        assert sorted(row["transport_order"]) == list(range(8))
        assert row["transport_order"] != list(range(8))
        event_order = {ev["seq"]: ev for ev in row["events"]}
        assert sorted(event_order) == list(range(8))
        previous = "GENESIS"
        for index, primitive in enumerate(PRIMITIVES):
            ev = event_order[index]
            assert (ev["context"], ev["op"], ev["prev"], ev["version"]) == (
                row["context"], primitive, previous, row["id"] + 1)
            # Match JS's JSON.stringify formatting and insertion order.
            data = json.dumps([ev["context"], ev["seq"], ev["op"],
                               ev["prev"], ev["version"]],
                              separators=(",", ":")).encode()
            assert ev["digest"] == sha(data)
            previous = ev["digest"]
        assert row["ordered_validation"] == "PASS"
        assert row["naive_validation"] != "PASS"
    expected_negative = {"duplicate", "missing", "wrong_prev",
                         "wrong_context", "wrong_payload"}
    assert set(experiment["negative_controls"]) == expected_negative
    assert all(x["rejected"] and x["observed"] != "PASS"
               for x in experiment["negative_controls"].values())
    changed = dict(experiment["sequences"][0]["events"][0])
    changed["op"] = "remove"
    data = json.dumps([changed["context"],changed["seq"],changed["op"],
                       changed["prev"],changed["version"]],
                      separators=(",", ":")).encode()
    mutation_rejected = sha(data) != changed["digest"]
    assert mutation_rejected
    result = {
        "date": "2026-11-07", "study": "kvtether",
        "original_result_sha256": sha(EVIDENCE.read_bytes()),
        "sequences_replayed": 25,
        "events_checked": 200,
        "negative_controls": 5,
        "mutation_rejected": mutation_rejected,
        "status": "PASS_INDEPENDENT_SYNTHETIC_CHAIN_ORACLE",
        "limitation": "Verifies synthetic ordering/hash reconstruction, not KVTether source or real KV engine"
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"sequences": 25, "events": 200,
                      "negative_controls": 5}))


if __name__ == "__main__":
    main()
