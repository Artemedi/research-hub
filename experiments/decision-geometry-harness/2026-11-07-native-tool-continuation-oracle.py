#!/usr/bin/env python3
"""Independent oracle for native tool_use -> inert tool_result -> final model turn.

Keeps strict scalar final-output equality separate from content accuracy:
the job case returns correct status inside a nested object, unlike requested
scalar format. No provider call and no tool invocation occurs in this oracle.
"""
import hashlib
import json
import os
from pathlib import Path

INPUT=Path(os.environ["INPUT"])
WIRES=Path(os.environ["WIRES"])
OUTPUT=Path(os.environ["OUTPUT"])
PIN="3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc"
SOURCE_SHA="36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def valid_record(row):
    if row.get("status") != "COMPLETE":
        return False
    if row.get("round1_stop")!="tool_use" or row.get("round2_stop")!="end_turn":
        return False
    if row.get("round1_model")!="glm-5.3-flash" or row.get("round2_model")!="glm-5.3-flash":
        return False
    if row.get("tool_call_count")!=1:
        return False
    return (row.get("observed_tool")==row.get("expected_tool") and
            row.get("observed_arguments")==row.get("expected_arguments"))


def main():
    j=json.loads(INPUT.read_text())
    wire=json.loads(WIRES.read_text())
    assert j["source_pin"]==wire["dsh_runtime_pin"]==PIN
    assert j["source_sha256"]==wire["serializer_source_sha256"]==SOURCE_SHA
    assert j["wire_sha256"]==sha(WIRES.read_bytes())
    assert j["planned"]==2 and len(j["cases"])==2
    assert {row["id"] for row in j["cases"]}=={"sum","job"}
    assert all(valid_record(x) for x in j["cases"])
    a=next(x for x in j["cases"] if x["id"]=="sum")
    b=next(x for x in j["cases"] if x["id"]=="job")
    # Strict expected value / shape: scalar 'complete' was preregistered,
    # whereas model returned entire job record (content correct, shape wrong).
    assert a["returned_final"]=={"result":11}
    assert b["returned_final"]=={"result":{"job_id":"job-104","state":"complete"}}
    strict=sum(x["returned_final"]=={"result":x["expected_final"]}
               for x in j["cases"])
    assert strict==1
    semantic=sum(
        x["returned_final"]=={"result":x["expected_final"]}
        if x["id"]=="sum" else
        isinstance(x["returned_final"].get("result"),dict)
        and x["returned_final"]["result"].get("state")==x["expected_final"]
        and x["returned_final"]["result"].get("job_id")=="job-104"
        for x in j["cases"])
    assert semantic==2
    corrupted=dict(a)
    corrupted["observed_arguments"]={"numbers":[4,9,-3]}
    assert not valid_record(corrupted)
    result={
        "date":"2026-11-07","study":"decision-geometry-harness",
        "source_pin":PIN,"source_sha256":SOURCE_SHA,
        "input_sha256":sha(INPUT.read_bytes()),
        "wire_sha256":sha(WIRES.read_bytes()),
        "native_tool_use_and_continue_valid":2,
        "strict_final_shape_correct":strict,
        "final_result_content_correct":semantic,
        "mutation_rejected":True,
        "untrusted_tools_executed":0,
        "status":"PASS_BOUND_TWO_NATIVE_TOOL_RESULT_ROUNDTRIPS_WITH_FORMAT_DEVIATION",
        "limitations":[
            "Uses Anthropic native provider via ZCode, not DSH DeepSeek adapter",
            "Tool results are hardcoded synthetic constants; actual tools never run",
            "One final response returned a nested object instead of preregistered scalar",
            "Two smoke scenarios provide no reliability or cost confidence"
        ]
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"roundtrips":2,"strict":strict,
                     "content_ok":semantic,"mutation_rejected":True}))


if __name__=="__main__":
    main()
