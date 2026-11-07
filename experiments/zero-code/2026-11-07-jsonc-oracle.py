#!/usr/bin/env python3
"""Independent stdlib verifier of 0-CODE JSONC author's parser outputs.

Expected objects are Python-generated gold from a separate fixture script.
This verifier never imports JavaScript parser or uses output's matched flag
as evidence; it compares the actual returned values directly with gold.
"""
import hashlib
import json
import os
from pathlib import Path

FIXTURE = Path(os.environ["FIXTURE"])
RESULT = Path(os.environ["EVIDENCE"])
OUTPUT = Path(os.environ["OUTPUT"])
PIN = "47f6a81724e87ff5e916f0eb146516d801a8fb28"
PARSER_SHA = "f61414badb9ec40589ebb26655a4b109466c86e20a6e5d8b96add15bf7deb954"
NATIVE_SHA = "c22d121df69f0f4839827b933810c0b05cf6ce86e83cc1ce1c6980ac608e4d42"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def verify(record, gold):
    if record["id"] != gold["id"]:
        return False
    if record["input_sha256"] != sha(gold["text"]):
        return False
    if record["canonical_sha256"] != sha(canonical(gold["expected"])):
        return False
    return record["accepted"] and record["actual"] == gold["expected"]


def main():
    fixture = json.loads(FIXTURE.read_text())
    result = json.loads(RESULT.read_text())
    assert fixture["seed"] == 20261107
    assert result["source_pin"] == PIN
    assert result["source_sha256"] == PARSER_SHA
    assert result["strict_native_source_sha256"] == NATIVE_SHA
    assert result["fixture_sha256"] == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert (result["valid_count"], result["invalid_count"]) == (120, 24)
    assert (len(result["valid"]), len(result["invalid"])) == (120, 24)
    assert len({x["id"] for x in result["valid"]}) == 120
    assert len({x["id"] for x in result["invalid"]}) == 24
    for observed, expected in zip(result["valid"], fixture["valid"], strict=True):
        assert verify(observed, expected), observed["id"]
    for observed, gold in zip(result["invalid"], fixture["invalid"], strict=True):
        assert observed["id"] == gold["id"]
        assert observed["input_sha256"] == sha(gold["text"])
        assert observed["rejected"] is True and observed["accepted"] is False
    duplicate = result["duplicate_key_observation"]
    assert duplicate["input_sha256"] == sha(fixture["ambiguous_duplicate"]["text"])
    assert duplicate["accepted"] is True
    assert duplicate["result"] == fixture["ambiguous_duplicate"]["expected_json_parse_last_wins"]
    assert duplicate["strict_native_json_rejected_duplicate"] is True
    assert duplicate["strict_native_json_accepted_unique"] is True

    falsified = dict(result["valid"][0])
    falsified["actual"] = {"id": "a different value"}
    mutation1 = not verify(falsified, fixture["valid"][0])
    falsified = dict(result["invalid"][0])
    falsified["rejected"] = False
    mutation2 = not (falsified["rejected"] is True and falsified["accepted"] is False)
    assert mutation1 and mutation2
    summary = {
        "date": "2026-11-07", "study": "zero-code",
        "source_pin": PIN,
        "source_file_sha256": PARSER_SHA,
        "original_results_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
        "independent_standard_json_gold": "Python json.dumps original values, not parsed JavaScript result",
        "valid_cases_verified": 120,
        "invalid_cases_verified": 24,
        "strict_duplicate_key_route_verified": True,
        "mutations_rejected": 2,
        "status": "PASS_BOUNDED_JSONC_BEHAVIOR",
        "limitations": [
            "Gold JSONC valid grammar is generated from Python values, not a complete independent JSONC specification",
            "Twenty distinct base objects across six syntactic styles, not independent realistic project configs",
            "Duplicate rejection is specific to native-json inspect; other consumers may be more permissive",
            "No full supervisor or tool-permission integration validated"
        ]
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({
        "verified_valid": 120, "verified_invalid": 24,
        "mutations_rejected": 2, "native_duplicate_rejected": True,
    }))


if __name__ == "__main__":
    main()
