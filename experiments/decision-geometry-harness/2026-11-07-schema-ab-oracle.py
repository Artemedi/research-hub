#!/usr/bin/env python3
"""Independent verifier of paired LLM schema-order choices + pinned DSH wires.

Does not import experiment runner or trust model's own success labels.
Gold was fixed before ZCode calls and never sent in model-facing payloads.
"""
import hashlib
import json
import math
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
SHA = "36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162"


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def canonical(obj):
    if isinstance(obj, dict):
        return {k: canonical(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [canonical(x) for x in obj]
    return obj


def tools_unchanged(a, b):
    def unorder(tools):
        return sorted((canonical(tool) for tool in tools),
                      key=lambda x: x["function"]["name"])
    return unorder(a) == unorder(b)


def compatible_type(value, schema):
    typ = schema.get("type")
    if typ == "string":
        return isinstance(value, str) and (
            "enum" not in schema or value in schema["enum"])
    if typ == "integer":
        return type(value) is int
    if typ == "number":
        return (type(value) is int or type(value) is float)
    if typ == "boolean":
        return type(value) is bool
    if typ == "array":
        return isinstance(value, list) and all(
            compatible_type(x, schema["items"]) for x in value)
    return False


def schema_valid(tool, args, definitions):
    if tool == "NONE":
        return args == {}
    if tool not in definitions or not isinstance(args, dict):
        return False
    s = definitions[tool]["function"]["parameters"]
    required = set(s.get("required", []))
    properties = s.get("properties", {})
    if not required.issubset(args):
        return False
    if s.get("additionalProperties") is False and (set(args) - set(properties)):
        return False
    return all(k in properties and compatible_type(v, properties[k])
               for k, v in args.items())


def verify_wires(wires, fixtures):
    assert wires["dsh_runtime_pin"] == fixtures["source_pin"] == PIN
    assert wires["serializer_source_sha256"] == SHA
    assert wires["fixture_sha256"] == digest(FIXTURE.read_bytes())
    assert len(wires["wires"]) == 6
    lookup = {}
    for item in wires["wires"]:
        wire = item["wire"]
        lookup[item["batch"], item["variant"]] = item
        serialized = json.dumps(wire, separators=(",", ":"), ensure_ascii=False)
        assert digest(serialized.encode()) == item["wire_sha256"]
        assert len(item["task_ids"]) == 8
        tasks = json.loads(wire["messages"][-1]["content"])["tasks"]
        assert [t["id"] for t in tasks] == item["task_ids"]
        gold = {x["id"]: x["instruction"] for x in fixtures["cases"]}
        assert all(t["instruction"] == gold[t["id"]] for t in tasks)
        assert wire["messages"][0]["content"] == wires["wires"][0]["wire"]["messages"][0]["content"]
        assert wire["model"] == "glm-5.3-flash"
        assert wire["temperature"] == 0 and wire["max_tokens"] == 2500
    assert len(lookup) == 6
    for batch in range(3):
        a = lookup[batch, "A"]["wire"]
        b = lookup[batch, "B"]["wire"]
        assert a["messages"] == b["messages"]
        assert {k: v for k, v in a.items() if k != "tools"} == {
            k: v for k, v in b.items() if k != "tools"}
        assert tools_unchanged(a["tools"], b["tools"])
        a_tools = [t["function"]["name"] for t in a["tools"]]
        b_tools = [t["function"]["name"] for t in b["tools"]]
        assert a_tools == list(reversed(b_tools))
        for at, bt in zip(a["tools"], reversed(b["tools"])):
            ak = list(at["function"]["parameters"]["properties"])
            bk = list(bt["function"]["parameters"]["properties"])
            assert ak == list(reversed(bk))
    manipulated = json.loads(json.dumps(lookup[0, "B"]["wire"]["tools"]))
    manipulated[0]["function"]["description"] += " ALTERED"
    assert not tools_unchanged(lookup[0, "A"]["wire"]["tools"], manipulated)
    return lookup


def percentile(values, p):
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered)-1, math.ceil(len(ordered)*p)-1)
    return ordered[index]


def main():
    assert subprocess.check_output(
        ["git", "-C", str(DSH), "rev-parse", "HEAD"], text=True).strip() == PIN
    source = DSH / "packages/llm/llm-deepseek/src/serialize.ts"
    assert digest(source.read_bytes()) == SHA
    fixtures = json.loads(FIXTURE.read_text())
    wires = json.loads(WIRES.read_text())
    model = json.loads(MODEL.read_text())
    assert fixtures["case_count"] == 24
    lookup = verify_wires(wires, fixtures)
    assert model["fixture_sha256"] == digest(FIXTURE.read_bytes())
    assert model["wires_sha256"] == digest(WIRES.read_bytes())
    assert model["planned_calls"] == 12
    assert len(model["calls"]) == model["attempted_calls"] <= 12
    gold = {row["id"]: row for row in fixtures["cases"]}
    assert len(gold) == 24
    scored = []
    trial = {}
    for call in model["calls"]:
        assert (call["batch"], call["variant"]) in lookup
        assert call["replicate"] in (0, 1)
        assert call["wire_sha256"] == lookup[call["batch"], call["variant"]]["wire_sha256"]
        assert call["task_ids"] == lookup[call["batch"], call["variant"]]["task_ids"]
        key = (call["replicate"], call["batch"], call["variant"])
        assert key not in trial
        trial[key] = call
        if call["status"] != "COMPLETE":
            continue
        assert call["model"] == "glm-5.3-flash"
        definitions = {
            x["function"]["name"]: x for x in lookup[call["batch"],
                                                        call["variant"]]["wire"]["tools"]
        }
        answer = {x["id"]: x for x in call["results"]}
        assert set(answer) == set(call["task_ids"])
        for id_ in call["task_ids"]:
            expected = gold[id_]
            observed = answer[id_]
            name_correct = observed["tool"] == expected["expected_tool"]
            arguments_correct = observed["arguments"] == expected["expected_arguments"]
            valid = schema_valid(observed["tool"], observed["arguments"], definitions)
            scored.append({
                "id": id_, "batch": call["batch"],
                "replicate": call["replicate"], "variant": call["variant"],
                "language": "ru" if any("\u0400" <= c <= "\u04ff"
                                      for c in expected["instruction"]) else "en",
                "negative": expected["expected_tool"] == "NONE",
                "selected_tool": observed["tool"],
                "selected_arguments": observed["arguments"],
                "tool_correct": name_correct,
                "arguments_correct": arguments_correct,
                "schema_valid": valid,
                "exact": name_correct and arguments_correct and valid,
            })
    # Score mutations have to fail; no model output can override gold labels.
    if scored:
        first = next(row for row in scored if row["tool_correct"])
        label_mutation = dict(first)
        label_mutation["selected_tool"] = "NONE" if gold[first["id"]]["expected_tool"] != "NONE" else "invalid_tool"
        assert label_mutation["selected_tool"] != gold[first["id"]]["expected_tool"]
    counts = {}
    for variant in ("A", "B"):
        subset = [x for x in scored if x["variant"] == variant]
        calls = [x for x in model["calls"] if x["variant"] == variant]
        usage = {
            key: sum((c.get("usage") or {}).get(key, 0)
                     for c in calls if c["status"] == "COMPLETE")
            for key in ("input_tokens", "output_tokens", "cache_read_input_tokens")
        }
        durations = [c["elapsed_ms"] for c in calls if c["status"] == "COMPLETE"]
        counts[variant] = {
            "completed_calls": sum(x["status"] == "COMPLETE" for x in calls),
            "failed_calls": sum(x["status"] != "COMPLETE" for x in calls),
            "scored_decisions": len(subset),
            "tool_name_correct": sum(x["tool_correct"] for x in subset),
            "arguments_correct": sum(x["arguments_correct"] for x in subset),
            "schema_valid": sum(x["schema_valid"] for x in subset),
            "exact_correct": sum(x["exact"] for x in subset),
            "negative_cases": sum(x["negative"] for x in subset),
            "negative_false_tool": sum(x["negative"] and x["selected_tool"] != "NONE"
                                      for x in subset),
            "ru_exact": sum(x["exact"] and x["language"] == "ru" for x in subset),
            "en_exact": sum(x["exact"] and x["language"] == "en" for x in subset),
            "p50_completed_call_ms": statistics.median(durations) if durations else None,
            "p95_completed_call_ms": percentile(durations, .95),
            "reported_tokens": usage,
        }
    positions = {(x["replicate"],x["batch"],x["id"],x["variant"]): x for x in scored}
    pairs = []
    for replica in (0,1):
        for batch in range(3):
            a = trial.get((replica,batch,"A"))
            b = trial.get((replica,batch,"B"))
            if a is None or b is None or a["status"]!="COMPLETE" or b["status"]!="COMPLETE":
                continue
            for id_ in lookup[batch, "A"]["task_ids"]:
                left=positions[replica,batch,id_,"A"]
                right=positions[replica,batch,id_,"B"]
                pairs.append({
                    "replicate": replica, "batch": batch, "id": id_,
                    "a_exact": left["exact"], "b_exact": right["exact"],
                    "a_tool":left["selected_tool"],"b_tool":right["selected_tool"],
                    "a_arguments":left["selected_arguments"],
                    "b_arguments":right["selected_arguments"],
                    "different_selection":left["selected_tool"]!=right["selected_tool"],
                    "different_args":left["selected_arguments"]!=right["selected_arguments"],
                })
    comparison = {
        "eligible_paired_decisions": len(pairs),
        "a_only_correct": sum(x["a_exact"] and not x["b_exact"] for x in pairs),
        "b_only_correct": sum(x["b_exact"] and not x["a_exact"] for x in pairs),
        "both_correct": sum(x["a_exact"] and x["b_exact"] for x in pairs),
        "both_wrong": sum(not x["a_exact"] and not x["b_exact"] for x in pairs),
        "tool_selection_changes": sum(x["different_selection"] for x in pairs),
        "argument_changes": sum(x["different_args"] for x in pairs),
    }
    assert sum(comparison[k] for k in ("a_only_correct","b_only_correct","both_correct","both_wrong")) == len(pairs)
    output = {
        "date": "2026-11-07",
        "study": "decision-geometry-harness",
        "source_pin": PIN,
        "serializer_source_sha256": SHA,
        "fixtures_sha256": digest(FIXTURE.read_bytes()),
        "wires_sha256": digest(WIRES.read_bytes()),
        "model_calls_sha256": digest(MODEL.read_bytes()),
        "scenario_count": 24, "replicates": 2,
        "independent_wire_semantic_equivalence": True,
        "negative_tampered_schema_detected": True,
        "negative_tampered_label_detected": bool(scored),
        "results_by_variant": counts,
        "paired_comparison": comparison,
        "scored": scored,
        "pairs": pairs,
        "status": "MODEL_ROUTING_SURROGATE_MEASURED" if len(pairs)==48 else
                  "PARTIAL_MODEL_ROUTING_SURROGATE",
        "limitations": [
            "Two correlated repetitions per authored item, not blind human expert labels",
            "ZCode sees serialized DSH tool request as text, cannot call tools and does not execute agent loop",
            "Provider owns actual sampling defaults; temperature:0 in quoted wire is not enforced",
            "A/B changes BOTH tool order and field order, not independently factorial",
            "No actual DSH provider model invocation, no production inference or tool execute",
            "Only local subprocess CPU/IO and remote token usage reported; no backend GPU/IO cost",
            "Tool correctness is pre-authored independent gold for clear synthetic requests",
        ]
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "status":output["status"],"counts":counts,
        "paired":comparison,"model_calls":model["attempted_calls"]
    },ensure_ascii=False))


if __name__ == "__main__":
    main()
