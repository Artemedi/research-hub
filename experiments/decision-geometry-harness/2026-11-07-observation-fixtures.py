#!/usr/bin/env python3
"""Pre-register 16 observation-order tests: current request vs stale context.

Gold is inherited from independently authored fixed routing cases; no labels
are placed in either model-facing observation representation.
"""
import hashlib
import json
import os
from pathlib import Path

INPUT = Path(os.environ["FIXTURE"])
OUTPUT = Path(os.environ["OUTPUT"])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    base = json.loads(INPUT.read_text())
    assert base["case_count"] == 24
    by_tool = {}
    for case in base["cases"]:
        by_tool.setdefault(case["expected_tool"], []).append(case)
    assert len(by_tool) == 8
    chosen = []
    for tool, rows in sorted(by_tool.items()):
        chosen.extend(rows[:2])
    assert len(chosen) == 16
    names = [row["expected_tool"] for row in base["cases"]
             if row["expected_tool"] != "NONE"]
    cases = []
    for i, row in enumerate(chosen):
        prior_tool = next(tool for tool in names
                          if tool != row["expected_tool"])
        if row["expected_tool"] == "NONE":
            prior_tool = "read_file_range"
        cases.append({
            "id": "obs-"+row["id"], "current_request": row["instruction"],
            "previous_observation": {
                "last_tool": prior_tool,
                "summary": f"Previous action selected {prior_tool}, but this historical result is not a request.",
                "age": "stale",
            },
            "context_metadata": {"iteration": 7+i,"stage": "review",
                                 "hint": "Use only current_request to select the next tool."},
            "expected_tool": row["expected_tool"],
            "expected_arguments": row["expected_arguments"]
        })
    assert len({c["id"] for c in cases}) == len(cases)
    result = {
        "date": "2026-11-07", "study": "decision-geometry-harness",
        "source_fixture_sha256": sha(INPUT.read_bytes()),
        "source_pin": base["source_pin"],
        "serializer_source_sha256": base["serializer_source_sha256"],
        "case_count": len(cases), "batch_size": 8, "batches": 2,
        "variants": ["A","B"], "replicates": 2,
        "cases": cases,
        "oracle": "fixed source-case exact tool and arguments; current_request authoritative",
        "limitations": [
            "16 authored synthetic current/stale contexts, not a real agent state transition",
            "Historical field hints are artificial distractors and no tool was executed"
        ]
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"cases":len(cases),"sha256":sha(OUTPUT.read_bytes())}))


if __name__=="__main__":
    main()
