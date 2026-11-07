#!/usr/bin/env python3
"""Independent verifier for state-observation field order A/B with stale cues.

Checks exact DSH wire semantic invariance, author-gold selections, paired drift,
negative controls and errors. Never imports the model runner.
"""
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess

FIXTURE = Path(os.environ["FIXTURE"])
WIRES = Path(os.environ["WIRES"])
MODEL = Path(os.environ["MODEL"])
DSH = Path(os.environ["DSH_RUNTIME_ROOT"])
OUTPUT = Path(os.environ["OUTPUT"])
PIN = "3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc"
SOURCE_SHA = "36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162"


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def deep_sort(value):
    if isinstance(value, dict):
        return {name: deep_sort(x) for name, x in sorted(value.items())}
    if isinstance(value, list):
        return [deep_sort(x) for x in value]
    return value


def source_verified():
    assert subprocess.check_output(
        ["git", "-C", str(DSH), "rev-parse", "HEAD"],
        text=True).strip() == PIN
    source = DSH / "packages/llm/llm-deepseek/src/serialize.ts"
    assert sha(source.read_bytes()) == SOURCE_SHA


def valid_tool_args(tool, args, definitions):
    if not isinstance(args, dict):
        return False
    if tool == "NONE":
        return args == {}
    if tool not in definitions:
        return False
    schema = definitions[tool]["function"]["parameters"]
    props = schema["properties"]
    if not set(schema.get("required", [])).issubset(args):
        return False
    if schema.get("additionalProperties") is False and set(args)-set(props):
        return False
    for key, value in args.items():
        if key not in props:
            return False
        s = props[key]
        kind = s.get("type")
        if kind == "string" and not isinstance(value, str):
            return False
        if kind == "integer" and type(value) is not int:
            return False
        if kind == "array" and not (
            isinstance(value, list) and all(type(v) is int for v in value)
        ):
            return False
        if "enum" in s and value not in s["enum"]:
            return False
    return True


def verify_wire(fixtures, wires):
    assert fixtures["case_count"] == 16 and wires["batch_count"] == 2
    assert wires["dsh_runtime_pin"] == PIN
    assert wires["serializer_source_sha256"] == SOURCE_SHA
    assert wires["fixture_sha256"] == sha(FIXTURE.read_bytes())
    assert len(wires["wires"]) == 4
    lookup = {(w["batch"], w["variant"]): w for w in wires["wires"]}
    assert len(lookup) == 4
    gold = {row["id"]: row for row in fixtures["cases"]}
    for batch in range(2):
        a, b = lookup[batch, "A"], lookup[batch, "B"]
        aw, bw = a["wire"], b["wire"]
        assert aw["tools"] == bw["tools"]
        assert len(a["task_ids"]) == len(b["task_ids"]) == 8
        assert a["task_ids"] == b["task_ids"]
        assert len(aw["messages"]) == len(bw["messages"]) == 2
        assert aw["messages"][0] == bw["messages"][0]
        assert {key: val for key, val in aw.items() if key != "messages"} == {
            key: val for key, val in bw.items() if key != "messages"}
        observations = []
        for item in (a, b):
            wire = item["wire"]
            assert wire["model"] == "glm-5.3-flash"
            assert wire["temperature"] == 0
            serialized = json.dumps(wire, ensure_ascii=False, separators=(",", ":"))
            assert sha(serialized.encode()) == item["wire_sha256"]
            text = wire["messages"][-1]["content"]
            assert "expected_tool" not in text and "expected_arguments" not in text
            obj = json.loads(text)
            assert list(obj) == ["observations"]
            observations.append(obj)
            assert [x["id"] for x in obj["observations"]] == item["task_ids"]
            for row in obj["observations"]:
                assert row["current_request"] == gold[row["id"]]["current_request"]
                assert row["previous_observation"] == gold[row["id"]]["previous_observation"]
                assert row["context_metadata"] == gold[row["id"]]["context_metadata"]
                assert row["previous_observation"]["last_tool"] != gold[row["id"]]["expected_tool"]
        assert deep_sort(observations[0]) == deep_sort(observations[1])
        assert aw["messages"][-1]["content"] != bw["messages"][-1]["content"]
    tampered = json.loads(json.dumps(lookup[0, "B"]["wire"]["messages"][-1]["content"]))
    mutated = json.loads(tampered)
    mutated["observations"][0]["current_request"] += " ALTERED"
    assert deep_sort(mutated) != deep_sort(
        json.loads(lookup[0, "A"]["wire"]["messages"][-1]["content"]))
    return lookup


def main():
    source_verified()
    fixtures = json.loads(FIXTURE.read_text())
    wires = json.loads(WIRES.read_text())
    model = json.loads(MODEL.read_text())
    lookup = verify_wire(fixtures, wires)
    assert model["fixture_sha256"] == sha(FIXTURE.read_bytes())
    assert model["wires_sha256"] == sha(WIRES.read_bytes())
    assert model["planned_calls"] == 8
    assert 0 < model["attempted_calls"] <= 8
    gold = {item["id"]: item for item in fixtures["cases"]}
    all_rows = []
    call_map = {}
    for call in model["calls"]:
        key = (call["replicate"],call["batch"],call["variant"])
        assert key not in call_map
        call_map[key] = call
        assert call["wire_sha256"] == lookup[call["batch"],call["variant"]]["wire_sha256"]
        if call["status"] != "COMPLETE":
            continue
        assert call["model"] == "glm-5.3-flash"
        answers = {x["id"]:x for x in call["results"]}
        assert set(answers) == set(call["task_ids"])
        tool_specs = {x["function"]["name"]:x for x in lookup[
            call["batch"],call["variant"]]["wire"]["tools"]}
        for id_ in call["task_ids"]:
            expected = gold[id_]
            actual = answers[id_]
            valid = valid_tool_args(actual["tool"],actual["arguments"],tool_specs)
            exact = (valid and actual["tool"] == expected["expected_tool"] and
                     actual["arguments"] == expected["expected_arguments"])
            all_rows.append({
                "id":id_,"replicate":call["replicate"],
                "batch":call["batch"],"variant":call["variant"],
                "chosen_tool":actual["tool"],
                "arguments":actual["arguments"],
                "schema_valid":valid,
                "tool_correct":actual["tool"] == expected["expected_tool"],
                "args_correct":actual["arguments"] == expected["expected_arguments"],
                "historical_tool_leak":actual["tool"] ==
                   expected["previous_observation"]["last_tool"] and
                   actual["tool"] != expected["expected_tool"],
                "negative":expected["expected_tool"]=="NONE",
                "exact":exact
            })
    if all_rows:
        sample = next(x for x in all_rows if x["exact"])
        assert sample["chosen_tool"] == gold[sample["id"]]["expected_tool"]
        assert ("NONE" if sample["chosen_tool"] != "NONE" else "invalid_tool") != sample["chosen_tool"]
    by_variant={}
    for variant in ("A","B"):
        rows=[x for x in all_rows if x["variant"]==variant]
        calls=[x for x in model["calls"] if x["variant"]==variant]
        wall=[x["elapsed_ms"] for x in calls if x["status"]=="COMPLETE"]
        by_variant[variant]={
            "calls_complete":sum(x["status"]=="COMPLETE" for x in calls),
            "calls_failed":sum(x["status"]!="COMPLETE" for x in calls),
            "decisions":len(rows),
            "exact_correct":sum(x["exact"] for x in rows),
            "schema_valid":sum(x["schema_valid"] for x in rows),
            "wrong_tool":sum(not x["tool_correct"] for x in rows),
            "stale_tool_leaks":sum(x["historical_tool_leak"] for x in rows),
            "false_tool_on_none":sum(x["negative"] and x["chosen_tool"]!="NONE" for x in rows),
            "negative_cases":sum(x["negative"] for x in rows),
            "median_call_ms":statistics.median(wall) if wall else None,
            "input_tokens":sum((x.get("usage")or{}).get("input_tokens",0) for x in calls),
            "output_tokens":sum((x.get("usage")or{}).get("output_tokens",0) for x in calls),
            "cache_read_input_tokens":sum((x.get("usage")or{}).get("cache_read_input_tokens",0) for x in calls)
        }
    index={(x["replicate"],x["batch"],x["id"],x["variant"]):x for x in all_rows}
    pairs=[]
    for rep in (0,1):
        for batch in (0,1):
            a=call_map.get((rep,batch,"A"))
            b=call_map.get((rep,batch,"B"))
            if not a or not b or a["status"]!="COMPLETE" or b["status"]!="COMPLETE":
                continue
            for id_ in lookup[batch,"A"]["task_ids"]:
                left=index[rep,batch,id_,"A"]
                right=index[rep,batch,id_,"B"]
                pairs.append({
                    "id":id_,"replicate":rep,
                    "A_correct":left["exact"],"B_correct":right["exact"],
                    "tool_changed":left["chosen_tool"]!=right["chosen_tool"],
                    "args_changed":left["arguments"]!=right["arguments"],
                    "A_stale_tool":left["historical_tool_leak"],
                    "B_stale_tool":right["historical_tool_leak"],
                })
    comparison={
        "paired":len(pairs),
        "both_correct":sum(x["A_correct"] and x["B_correct"] for x in pairs),
        "A_only_correct":sum(x["A_correct"] and not x["B_correct"] for x in pairs),
        "B_only_correct":sum(x["B_correct"] and not x["A_correct"] for x in pairs),
        "both_wrong":sum(not x["A_correct"] and not x["B_correct"] for x in pairs),
        "tool_changes":sum(x["tool_changed"] for x in pairs),
        "argument_changes":sum(x["args_changed"] for x in pairs)
    }
    assert sum(comparison[k] for k in ("both_correct","A_only_correct","B_only_correct","both_wrong"))==len(pairs)
    record={
        "study":"decision-geometry-harness","date":"2026-11-07",
        "test":"observation-field-order text-only ZCode surrogate",
        "source_pin":PIN,"source_sha256":SOURCE_SHA,
        "fixture_sha256":sha(FIXTURE.read_bytes()),
        "wire_sha256":sha(WIRES.read_bytes()),
        "model_sha256":sha(MODEL.read_bytes()),
        "semantic_wire_invariant":True,
        "tampered_observation_detected":True,
        "tampered_answer_label_detected":bool(all_rows),
        "by_variant":by_variant,"comparison":comparison,
        "scored":all_rows,"paired_records":pairs,
        "status":"ACCEPT_BOUNDED_OBSERVATION_ORDER_LAB" if len(pairs)==32
             else "PARTIAL_OBSERVATION_ORDER_LAB",
        "limitations":[
            "Two model repetitions on 16 authored synthetic cases, no held-out human annotations",
            "Inert JSON observations included as user message text; no actual executing tool result or agent state",
            "No native DSH provider request, no remote model temperature control",
            "Only JSON key order changed; not natural-language observation format or full prompt topology",
            "No production tool execution or service state"
        ]
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":record["status"],"by_variant":by_variant,
                      "comparison":comparison},ensure_ascii=False))


if __name__=="__main__":
    main()
