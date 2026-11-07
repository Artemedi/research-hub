#!/usr/bin/env python3
"""Bounded native Anthropic tool_use A/B from pinned real DSH wire descriptions.

The DSH serializer has already constructed the wire. Convert those seven
function definitions losslessly to Anthropic tools, call ZCode sequentially.
No tools are executed; no model-side output is treated as scientific verdict.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import time

FIXTURE = Path(os.environ["FIXTURE"])
WIRES = Path(os.environ["WIRES"])
WRAPPER = Path(os.environ["ZCODE_WRAPPER"])
OUTPUT = Path(os.environ["OUTPUT"])
CHECKPOINT = Path(os.environ["CHECKPOINT"])
INPUT_DIR = Path(os.environ["INPUT_DIR"])
TIMEOUT = 45
PIN = "3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc"
SERIALIZER_SHA = "36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    if isinstance(value, list):
        return [canonical(x) for x in value]
    if isinstance(value, dict):
        return {key: canonical(x) for key, x in sorted(value.items())}
    return value


def anthropic_tools(wire_tools):
    return [{
        "name": tool["function"]["name"],
        "description": tool["function"]["description"],
        "input_schema": tool["function"]["parameters"],
    } for tool in wire_tools]


def choose_cases(fixtures):
    by_tool = {}
    for row in fixtures["cases"]:
        by_tool.setdefault(row["expected_tool"], []).append(row)
    assert len(by_tool) == 8
    chosen = []
    for tool in sorted(by_tool):
        chosen.extend(by_tool[tool][:2 if tool != "NONE" else 3])
    chosen_ids = {row["id"] for row in chosen}
    for key in ("artifact-3", "file-3", "job-3", "sql-3", "pg-3", "runbook-3", "sum-3"):
        if len(chosen) >= 20:
            break
        candidate = next((x for x in fixtures["cases"] if x["id"] == key), None)
        if candidate is not None and key not in chosen_ids:
            chosen.append(candidate)
            chosen_ids.add(key)
    for candidate in fixtures["cases"]:
        if len(chosen) >= 20:
            break
        if candidate["id"] not in chosen_ids and candidate["expected_tool"] != "NONE":
            chosen.append(candidate)
            chosen_ids.add(candidate["id"])
    assert len(chosen) == 20
    assert len({x["id"] for x in chosen}) == 20
    assert sum(x["expected_tool"] == "NONE" for x in chosen) == 3
    rng = random.Random(20261107)
    rng.shuffle(chosen)
    return chosen


def parse_response(envelope, choices):
    blocks = envelope.get("content", [])
    if not isinstance(blocks, list):
        raise ValueError("INVALID_CONTENT_ARRAY")
    if any(x.get("type") not in ("thinking", "text", "tool_use")
           for x in blocks if isinstance(x, dict)):
        raise ValueError("UNEXPECTED_CONTENT_BLOCK")
    calls = [x for x in blocks if isinstance(x, dict) and x.get("type") == "tool_use"]
    text = "\n".join(x.get("text", "") for x in blocks
                     if isinstance(x, dict) and x.get("type") == "text").strip()
    if calls:
        if len(calls) != 1 or envelope.get("stop_reason") != "tool_use":
            raise ValueError("NON_SINGLE_TOOL_USE")
        call = calls[0]
        name = call.get("name")
        arguments = call.get("input")
        if name not in choices or not isinstance(arguments, dict):
            raise ValueError("INVALID_TOOL_SCHEMA_RESPONSE")
        return {"selected_tool": name, "selected_arguments": arguments,
                "response_kind": "native_tool_use", "provider_tool_use_id_present":
                isinstance(call.get("id"), str) and bool(call["id"])}
    if envelope.get("stop_reason") != "end_turn":
        raise ValueError("UNEXPECTED_END")
    return {"selected_tool": "NONE" if text.upper() == "NONE" else "TEXT",
            "selected_arguments": {}, "response_kind": "native_no_tool_text",
            "model_visible_text": text[:180]}


def call(row, variant, tool_specs, provider_names):
    system = (
        "You are a safe read-only tool caller. Use exactly ONE appropriate tool "
        "when the user's task requires it, copying explicit arguments exactly. "
        "For explicit no-tool tasks, do not call any tool and reply exactly NONE. "
        "Never invent arguments or assume external data. No executable tools run "
        "in this synthetic evaluation; this is function selection only."
    )
    payload = {"max_tokens": 580, "system": system, "messages": [
        {"role": "user", "content": row["instruction"]}],
        "tools": tool_specs}
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    digest = sha(content.encode())
    checkpoint = CHECKPOINT / (row["id"] + "-" + variant + ".json")
    if checkpoint.exists():
        found = json.loads(checkpoint.read_text())
        if found.get("request_sha256") == digest and found.get("status") in (
                "COMPLETE", "BLOCKED_PROVIDER", "INVALID_RESPONSE"):
            return found
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    request_file = INPUT_DIR / (row["id"] + "-" + variant + ".json")
    request_file.write_text(content)
    record = {"id": row["id"], "variant": variant,
              "request_sha256": digest,
              "status": "BLOCKED_PROVIDER"}
    start = time.monotonic()
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        process = subprocess.run(
            ["node", str(WRAPPER), "--request-json", str(request_file)],
            cwd=WRAPPER.parent, capture_output=True, text=True,
            timeout=TIMEOUT)
        record.update(exit_code=process.returncode,
                      raw_provider_sha256=sha(process.stdout.encode()))
        if process.returncode != 0:
            record["error"] = "NONZERO_EXIT"
        else:
            envelope = json.loads(process.stdout)
            prediction = parse_response(envelope, provider_names)
            record.update(prediction)
            record.update(status="COMPLETE", model=envelope.get("model"),
                          stop_reason=envelope.get("stop_reason"),
                          usage=envelope.get("usage"))
    except subprocess.TimeoutExpired:
        record["error"] = "TIMEOUT"
    except (json.JSONDecodeError, TypeError, ValueError, KeyError) as error:
        record.update(status="INVALID_RESPONSE",
                      error=type(error).__name__,
                      error_detail=str(error)[:120])
    finally:
        child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        record.update(elapsed_ms=round(1000*(time.monotonic()-start), 1),
                      cpu_user_s=round(child_after.ru_utime-child_before.ru_utime, 3),
                      cpu_sys_s=round(child_after.ru_stime-child_before.ru_stime, 3),
                      local_inblocks=child_after.ru_inblock-child_before.ru_inblock,
                      local_oublocks=child_after.ru_oublock-child_before.ru_oublock)
        CHECKPOINT.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
    print("NATIVE", row["id"], variant, record["status"],
          record.get("selected_tool"), record.get("error"),
          round(record["elapsed_ms"]/1000, 1), flush=True)
    return record


def main():
    fbytes, wbytes = FIXTURE.read_bytes(), WIRES.read_bytes()
    fixtures, wires = json.loads(fbytes), json.loads(wbytes)
    assert fixtures["source_pin"] == wires["dsh_runtime_pin"] == PIN
    assert wires["serializer_source_sha256"] == SERIALIZER_SHA
    assert wires["fixture_sha256"] == sha(fbytes)
    by_variant = {}
    for variant in ("A", "B"):
        entry = next(x for x in wires["wires"] if x["batch"] == 0 and
                     x["variant"] == variant)
        by_variant[variant] = anthropic_tools(entry["wire"]["tools"])
    assert [x["name"] for x in by_variant["A"]] == [
        x["name"] for x in reversed(by_variant["B"])]
    assert canonical(sorted(by_variant["A"],key=lambda x:x["name"])) == canonical(
        sorted(by_variant["B"],key=lambda x:x["name"]))
    names = {x["name"] for x in by_variant["A"]}
    cases = choose_cases(fixtures)
    schedule = [(row, ("A","B") if i%2 == 0 else ("B","A"))
                for i,row in enumerate(cases)]
    results = []
    interrupted = 0
    started = time.monotonic()
    for row, variants in schedule:
        for variant in variants:
            record = call(row, variant, by_variant[variant], names)
            results.append(record)
            interrupted = interrupted+1 if record["status"]!="COMPLETE" else 0
            if interrupted >= 3 or time.monotonic()-started > 820:
                print("STOP_BOUNDED",interrupted,flush=True)
                break
        if interrupted >= 3 or time.monotonic()-started > 820:
            break
    output = {
        "date":"2026-11-07", "study":"decision-geometry-harness",
        "experiment":"native Anthropic tool_use from pinned DSH serializer tool definitions",
        "source_pin":PIN,"source_sha256":SERIALIZER_SHA,
        "original_fixtures_sha256":sha(fbytes),
        "original_dsh_wires_sha256":sha(wbytes),
        "task_ids":[x["id"] for x in cases],
        "plan_calls":40,"attempted_calls":len(results),
        "complete_calls":sum(x["status"]=="COMPLETE" for x in results),
        "provider_proprietary_tools_executed":0,
        "physical_parallelism":1,
        "variant_tool_definition_equivalence":True,
        "request_model": "GLM-5.3-Flash-Trial (ZCode default)",
        "rules":"20 tasks; paired A/B reversed order by task index; provider native tool-use; no model gold",
        "calls":results,
        "limitations":[
            "Provider protocol is ZCode Anthropic Messages, not DSH DeepSeek model adapter",
            "DSH tool schemas converted losslessly to Anthropic input_schema; DSH runtime never executed a tool",
            "One model reply per variant and case, no hard temperature/seed control",
            "No live tool results, side effects or permissions, so end-to-end agent correctness is unmeasured",
            "Twenty authored synthetic tasks, not blind human labels or deployed workload",
            "No actual provider-GPU resource telemetry; local CPU/IO measures CLI child only",
            "A/B reverses both tool definition order and properties order, not a factorial decomposition"
        ]
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print("SUMMARY",json.dumps({"attempted":len(results),
          "complete":output["complete_calls"]}),flush=True)


if __name__=="__main__":
    main()
