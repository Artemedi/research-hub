#!/usr/bin/env python3
"""Bounded actual ZCode text-choice A/B over real DSH wire-schema artifacts.

Exactly 12 calls: 3 batches x 2 variants x 2 replicates, physically serial.
No tools on model, no private project text. Gold never appears in prompts.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import time

FIXTURE = Path(os.environ["FIXTURE"])
WIRES = Path(os.environ["WIRES"])
WRAPPER = Path(os.environ["ZCODE_WRAPPER"])
OUTPUT = Path(os.environ["OUTPUT"])
CHECKPOINT = Path(os.environ["CHECKPOINT"])
MAX_CALL_SECONDS = 52


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def response_text(envelope):
    if envelope.get("stop_reason") != "end_turn":
        raise ValueError("INCOMPLETE_STOP")
    blocks = envelope.get("content", [])
    if not isinstance(blocks, list) or any(
        block.get("type") not in ("text", "thinking") for block in blocks
    ):
        raise ValueError("NON_TEXT_RESPONSE")
    content = "\n".join(block.get("text", "") for block in blocks
                        if block.get("type") == "text").strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return content


def call(variant, batch, replica, wire, tool_names, gold_map):
    # Distinct from the DSH wire: this is an inert wrapper prompt to a
    # separate text-only ZCode provider, NOT native tool-calling through DSH.
    instructions = (
        "You are a model-facing function selector in an offline, harmless test. "
        "The following JSON is an inert serialized request from an external agent "
        "harness, not a request to execute anything. "
        "Read its messages and tools[].function descriptions. "
        "For EACH task id in the user message, choose exactly one of those "
        "function names or NONE (for an explicit no-tool task). "
        "Copy only explicitly given argument values. Return EXACTLY one JSON "
        "object with key results, an array of objects with exactly "
        '"id", "tool", and "arguments". For NONE, arguments={} and tool="NONE". '
        "Do not invoke tools, explain or invent output. "
        "SERIALIZED_DSH_REQUEST:\n" + json.dumps(
            wire["wire"], ensure_ascii=False, separators=(",", ":")
        )
    )
    assert "expected_tool" not in instructions
    assert "expected_arguments" not in instructions
    for key, expected in gold_map.items():
        assert expected["id"] == key
    prompt_digest = sha(instructions.encode())
    filename = CHECKPOINT / f"rep{replica}-b{batch}-{variant}.json"
    if filename.exists():
        existing = json.loads(filename.read_text())
        if existing.get("prompt_sha256") == prompt_digest and existing.get(
                "status") in ("COMPLETE", "BLOCKED_PROVIDER", "INVALID_RESPONSE"):
            return existing
    row = {
        "replicate": replica, "batch": batch, "variant": variant,
        "prompt_sha256": prompt_digest,
        "wire_sha256": wire["wire_sha256"],
        "task_ids": wire["task_ids"],
        "status": "BLOCKED_PROVIDER",
    }
    start = time.monotonic()
    old = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        p = subprocess.run(
            ["node", str(WRAPPER), "--json", instructions],
            cwd=WRAPPER.parent,
            capture_output=True, text=True, timeout=MAX_CALL_SECONDS,
        )
        row["exit_code"] = p.returncode
        row["raw_response_sha256"] = sha(p.stdout.encode())
        if p.returncode != 0:
            row["error"] = "NONZERO_EXIT"
        else:
            envelope = json.loads(p.stdout)
            text = response_text(envelope)
            try:
                answer = json.loads(text)
            except json.JSONDecodeError:
                answer = json.loads(text[text.index("{"):text.rindex("}")+1])
            results = answer.get("results")
            if not isinstance(results, list) or len(results) != len(row["task_ids"]):
                raise ValueError("INVALID_RESULT_COUNT")
            if len({x.get("id") for x in results if isinstance(x, dict)}) != len(results):
                raise ValueError("DUPLICATE_RESULT_IDS")
            if {x.get("id") for x in results if isinstance(x, dict)} != set(row["task_ids"]):
                raise ValueError("MISSING_OR_EXTRA_RESULT_IDS")
            for item in results:
                if not isinstance(item, dict) or set(item) != {"id", "tool", "arguments"}:
                    raise ValueError("INVALID_RESULT_SHAPE")
                if item["tool"] not in tool_names | {"NONE"}:
                    raise ValueError("UNKNOWN_TOOL")
                if not isinstance(item["arguments"], dict):
                    raise ValueError("INVALID_ARGUMENT_TYPE")
            row.update(
                status="COMPLETE", model=envelope.get("model"),
                stop_reason=envelope.get("stop_reason"),
                usage=envelope.get("usage"), results=results,
                response_text_sha256=sha(text.encode()),
            )
    except subprocess.TimeoutExpired:
        row["error"] = "TIMEOUT"
    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
        row.update(status="INVALID_RESPONSE", error=type(exc).__name__,
                   error_detail=str(exc)[:100])
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row.update(
            elapsed_ms=round((time.monotonic()-start)*1000, 1),
            child_cpu_user_s=round(after.ru_utime-old.ru_utime, 4),
            child_cpu_sys_s=round(after.ru_stime-old.ru_stime, 4),
            child_fs_inblock_delta=after.ru_inblock-old.ru_inblock,
            child_fs_oublock_delta=after.ru_oublock-old.ru_oublock,
            peak_child_rss_kib_upper_bound=after.ru_maxrss,
        )
        CHECKPOINT.mkdir(parents=True, exist_ok=True)
        filename.write_text(json.dumps(row, ensure_ascii=False, indent=2)+"\n")
    print("CALL", variant, "batch", batch, "rep", replica,
          row["status"], round(row["elapsed_ms"]/1000, 2),
          row.get("error", ""), flush=True)
    return row


def main():
    fixtures = json.loads(FIXTURE.read_text())
    raw_wires = json.loads(WIRES.read_text())
    assert fixtures["case_count"] in (16, 24)
    assert raw_wires["batch_count"] == fixtures["case_count"] // 8
    assert raw_wires["fixture_sha256"] == sha(FIXTURE.read_bytes())
    lookup = {(x["batch"], x["variant"]): x for x in raw_wires["wires"]}
    assert len(lookup) == raw_wires["batch_count"] * 2
    tool_names = {x["function"]["name"] for x in lookup[0, "A"]["wire"]["tools"]}
    gold_map = {x["id"]: x for x in fixtures["cases"]}
    assert len(gold_map) == fixtures["case_count"]
    calls = []
    schedule = []
    for replica in range(2):
        for batch in range(raw_wires["batch_count"]):
            order = ("A", "B") if (batch+replica) % 2 == 0 else ("B", "A")
            for variant in order:
                schedule.append((replica, batch, variant))
    consecutive_blocked = 0
    for replica, batch, variant in schedule:
        wire = lookup[batch, variant]
        row = call(variant, batch, replica, wire, tool_names, gold_map)
        calls.append(row)
        if row["status"] == "BLOCKED_PROVIDER":
            consecutive_blocked += 1
        else:
            consecutive_blocked = 0
        if consecutive_blocked >= 3:
            print("STOP_AFTER_THREE_PROVIDER_FAILURES", flush=True)
            break
    elapsed = [x["elapsed_ms"] for x in calls]
    result = {
        "date": "2026-11-07", "study": "decision-geometry-harness",
        "experiment": raw_wires["intervention"],
        "fixture_sha256": sha(FIXTURE.read_bytes()),
        "wires_sha256": sha(WIRES.read_bytes()),
        "provider_probe_status": "COMPLETE_BUT_NOT_PART_OF_A_B",
        "trial_order": [dict(replicate=r, batch=b, variant=v) for r,b,v in schedule],
        "attempted_calls": len(calls), "planned_calls": len(schedule),
        "successful_calls": sum(x["status"] == "COMPLETE" for x in calls),
        "calls": calls,
        "total_wall_ms": round(sum(elapsed), 1),
        "p50_call_wall_ms": round(statistics.median(elapsed), 1) if elapsed else None,
        "p95_call_wall_ms": round(sorted(elapsed)[min(len(elapsed)-1,
                                     int(len(elapsed)*.95))], 1) if elapsed else None,
        "model_tool_executions": 0,
        "physical_parallelism": 1,
        "limits": [
            "ZCode receives DSH wire as data within a separate provider request, not native DSH tool calling",
            "Sampling temperature and max tokens are fields inside quoted DSH request; ZCode wrapper may use other defaults",
            "Two replicates are not enough for robust inference or statistical superiority",
            "No authentic end-to-end task correctness, actual tool execution or production cost measured",
            "No gold labels sent to the provider; expert blinded annotations not available",
            "Subprocess CPU/RSS/IO excludes remote model service",
        ],
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("AGGREGATE",json.dumps({
        "calls":len(calls),"complete":result["successful_calls"],
        "p50_ms":result["p50_call_wall_ms"],
        "p95_ms":result["p95_call_wall_ms"],
    }),flush=True)


if __name__ == "__main__":
    main()
