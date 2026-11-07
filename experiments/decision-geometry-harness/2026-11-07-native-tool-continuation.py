#!/usr/bin/env python3
"""Two isolated native tool_use -> fake tool_result -> model final round trips.

No host code or database tool executes. Tool-result payloads are predeclared
synthetic constants, and no credential or private source goes to the provider.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

WIRES = Path(os.environ["WIRES"])
WRAPPER = Path(os.environ["ZCODE_WRAPPER"])
OUTPUT = Path(os.environ["OUTPUT"])
REQUEST_DIR = Path(os.environ["REQUEST_DIR"])
PINS = {"source_sha": "36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162",
        "runtime_sha": "3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def provider(request, label):
    path = REQUEST_DIR / (label+".json")
    path.write_text(json.dumps(request, ensure_ascii=False, separators=(",", ":")))
    started = time.monotonic()
    r = subprocess.run(["node", str(WRAPPER), "--request-json", str(path)],
                       capture_output=True, text=True, cwd=WRAPPER.parent, timeout=45)
    if r.returncode != 0:
        return {"status":"BLOCKED_PROVIDER", "error":"NONZERO_EXIT",
                "elapsed_ms":round((time.monotonic()-started)*1000,1)}
    try:
        output = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"status":"BLOCKED_PROVIDER", "error":"INVALID_JSON"}
    return {"status":"COMPLETE", "elapsed_ms":round((time.monotonic()-started)*1000,1),
            "response_sha256":sha(r.stdout.encode()), "envelope":output}


def main():
    raw = json.loads(WIRES.read_text())
    assert raw["dsh_runtime_pin"]==PINS["runtime_sha"]
    assert raw["serializer_source_sha256"]==PINS["source_sha"]
    tools = [
        {"name":item["function"]["name"],"description":item["function"]["description"],
         "input_schema":item["function"]["parameters"]}
        for item in raw["wires"][0]["wire"]["tools"]
    ]
    cases = [
        {"id":"sum","instruction":"Use sum_numbers for explicit integers [4,9,-2].",
         "tool":"sum_numbers", "arguments":{"numbers":[4,9,-2]},
         "fake_result":{"sum":11}, "final_expected":11},
        {"id":"job","instruction":"Read status for job_id=job-104 using get_job_status.",
         "tool":"get_job_status","arguments":{"job_id":"job-104"},
         "fake_result":{"job_id":"job-104","state":"complete"},
         "final_expected":"complete"},
    ]
    REQUEST_DIR.mkdir(parents=True, exist_ok=True)
    output=[]
    for case in cases:
        base={"max_tokens":450,"system":
              "Use one read-only tool for the user's request; no invented arguments. "
              "After receiving tool_result, reply exactly one JSON object with key "
              "result equal to the returned value (sum or state); no commentary.",
              "tools":tools,
              "messages":[{"role":"user","content":case["instruction"]}]}
        first=provider(base,case["id"]+"-1")
        record={"id":case["id"],"expected_tool":case["tool"],
                "expected_arguments":case["arguments"],
                "expected_final":case["final_expected"],
                "round1_status":first["status"]}
        if first["status"]!="COMPLETE":
            record["error"]=first["error"]
            output.append(record)
            continue
        envelope=first["envelope"]
        model_calls=[block for block in envelope.get("content",[])
                     if block.get("type")=="tool_use"]
        record.update(round1_stop=envelope.get("stop_reason"),
                      round1_model=envelope.get("model"),
                      round1_usage=envelope.get("usage"),
                      round1_sha256=first["response_sha256"],
                      round1_elapsed_ms=first["elapsed_ms"],
                      tool_call_count=len(model_calls))
        if envelope.get("stop_reason")!="tool_use" or len(model_calls)!=1:
            record["status"]="UNEXPECTED_CALL_SHAPE"
            output.append(record)
            continue
        call=model_calls[0]
        record.update(observed_tool=call.get("name"),
                      observed_arguments=call.get("input"))
        if call.get("name")!=case["tool"] or call.get("input")!=case["arguments"]:
            record["status"]="WRONG_TOOL_OR_ARGUMENTS"
            output.append(record)
            continue
        # The fake result is orchestrator owned and supplies no untrusted commands.
        assistant=[b for b in envelope["content"] if b.get("type") in ("text","tool_use")]
        second=dict(base)
        second["messages"]=[
            base["messages"][0],
            {"role":"assistant","content":assistant},
            {"role":"user","content":[{
                "type":"tool_result","tool_use_id":call["id"],
                "content":json.dumps(case["fake_result"],separators=(",", ":"))
            }]}
        ]
        continued=provider(second,case["id"]+"-2")
        record["round2_status"]=continued["status"]
        if continued["status"]=="COMPLETE":
            answer=continued["envelope"]
            content="\n".join(c.get("text","") for c in answer.get("content",[])
                              if c.get("type")=="text").strip()
            record.update(round2_stop=answer.get("stop_reason"),
                          round2_model=answer.get("model"),
                          round2_usage=answer.get("usage"),
                          round2_sha256=continued["response_sha256"],
                          round2_elapsed_ms=continued["elapsed_ms"])
            try:
                decoded=json.loads(content)
                record["returned_final"]=decoded
                record["status"]="COMPLETE" if answer.get("stop_reason")=="end_turn" else                     "INVALID_FINAL_STOP"
            except json.JSONDecodeError:
                record.update(status="INVALID_FINAL_RESPONSE",
                              final_text_sha256=sha(content.encode()))
        else:
            record.update(status="BLOCKED_PROVIDER",error=continued["error"])
        output.append(record)
        print("CONTINUATION",record["id"],record.get("status"),flush=True)
    result={"date":"2026-11-07","study":"decision-geometry-harness",
            "scenario":"Anthropic provider native tool_use and synthetic tool_result continuation",
            "source_pin":PINS["runtime_sha"],"source_sha256":PINS["source_sha"],
            "wire_sha256":sha(WIRES.read_bytes()),
            "cases":output, "planned":len(cases),"completed":sum(
                x.get("status")=="COMPLETE" for x in output),
            "tool_execution":"none; fake result supplied from independent hardcoded constants",
            "status":"BOUNDED_NATIVE_TOOL_ROUNDTRIP" if all(
                x.get("status")=="COMPLETE" for x in output) else "PARTIAL_NATIVE_TOOL_ROUNDTRIP",
            "limits":[
                "Model native provider: ZCode Anthropic, not DSH DeepSeek adapter",
                "No real host tool code executed; injected tool results are synthetic",
                "Two smoke cases do not establish end-to-end production reliability",
                "No user/private data or environment credentials sent"
            ]}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("SUMMARY",result["completed"],"/",len(cases),flush=True)


if __name__=="__main__":
    main()
