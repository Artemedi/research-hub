#!/usr/bin/env python3
"""Independent gold+JSON Schema subset oracle for native ZCode tool_use A/B.

No imported helper from model runner; verifies pinned DSH serializer source,
the transferred DSH wire definition equivalence and actual Anthropic tool-use.
Never treats model text or model consensus as scientific acceptance.
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
RESULT = Path(os.environ["RESULT"])
OUTPUT = Path(os.environ["OUTPUT"])
DSH_ROOT = Path(os.environ["DSH_RUNTIME_ROOT"])
PIN = "3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc"
SERIALIZER_SHA = "36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(x):
    if isinstance(x, dict):
        return {key: canonical(value) for key, value in sorted(x.items())}
    if isinstance(x, list):
        return [canonical(value) for value in x]
    return x


def schema_valid(name, args, definitions):
    if name in ("NONE", "TEXT"):
        return args == {}
    if name not in definitions or not isinstance(args, dict):
        return False
    schema = definitions[name]["function"]["parameters"]
    props = schema["properties"]
    if not set(schema.get("required", [])).issubset(args):
        return False
    if schema.get("additionalProperties") is False and set(args) - set(props):
        return False
    for key, value in args.items():
        if key not in props:
            return False
        expected = props[key]
        typ = expected.get("type")
        if typ == "string" and not isinstance(value, str):
            return False
        if typ == "integer" and type(value) is not int:
            return False
        if typ == "array" and not (isinstance(value, list) and all(
                type(entry) is int for entry in value)):
            return False
        if "enum" in expected and value not in expected["enum"]:
            return False
    return True


def wire_checks(fixture_bytes, wire_bytes, records):
    assert records["source_pin"] == PIN
    assert records["source_sha256"] == SERIALIZER_SHA
    assert records["original_fixtures_sha256"] == sha(fixture_bytes)
    assert records["original_dsh_wires_sha256"] == sha(wire_bytes)
    wire = json.loads(wire_bytes)
    assert wire["dsh_runtime_pin"] == PIN
    assert wire["serializer_source_sha256"] == SERIALIZER_SHA
    assert wire["fixture_sha256"] == sha(fixture_bytes)
    a = next(x for x in wire["wires"] if x["batch"]==0 and x["variant"]=="A")
    b = next(x for x in wire["wires"] if x["batch"]==0 and x["variant"]=="B")
    def specs(item):
        return item["wire"]["tools"]
    assert [x["function"]["name"] for x in specs(a)] == [
        x["function"]["name"] for x in reversed(specs(b))]
    assert sorted([canonical(x) for x in specs(a)],key=lambda x:x["function"]["name"]) == sorted(
        [canonical(x) for x in specs(b)],key=lambda x:x["function"]["name"])
    for x,y in zip(specs(a), reversed(specs(b))):
        assert list(x["function"]["parameters"]["properties"]) == list(reversed(
            list(y["function"]["parameters"]["properties"])))
    changed = json.loads(json.dumps(specs(b)))
    changed[0]["function"]["description"] += " malicious injection"
    assert sorted([canonical(x) for x in specs(a)],key=lambda x:x["function"]["name"]) != sorted(
        [canonical(x) for x in changed],key=lambda x:x["function"]["name"])
    return {variant: {x["function"]["name"]:x for x in specs(item)}
            for variant, item in (("A",a),("B",b))}


def pct(values, quantile):
    if not values:
        return None
    return sorted(values)[min(len(values)-1,math.ceil(quantile*len(values))-1)]


def main():
    assert subprocess.check_output(
        ["git","-C",str(DSH_ROOT),"rev-parse","HEAD"],
        text=True).strip() == PIN
    source = DSH_ROOT / "packages/llm/llm-deepseek/src/serialize.ts"
    assert sha(source.read_bytes()) == SERIALIZER_SHA
    fixture_bytes, wire_bytes, result_bytes = (
        FIXTURE.read_bytes(), WIRES.read_bytes(), RESULT.read_bytes())
    fixtures, raw = json.loads(fixture_bytes), json.loads(result_bytes)
    lookup = wire_checks(fixture_bytes, wire_bytes, raw)
    gold={item["id"]:item for item in fixtures["cases"]}
    selected=raw["task_ids"]
    assert len(selected)==len(set(selected))==20
    assert set(selected).issubset(gold)
    assert sum(gold[id_]["expected_tool"]=="NONE" for id_ in selected)==3
    for tool in lookup["A"]:
        assert sum(gold[id_]["expected_tool"]==tool for id_ in selected)>=2
    assert raw["plan_calls"]==40 and 0<=raw["attempted_calls"]<=40
    assert raw["attempted_calls"]==len(raw["calls"])
    assert raw["variant_tool_definition_equivalence"] is True
    evaluated=[]
    seen=set()
    for row in raw["calls"]:
        key=(row["id"],row["variant"])
        assert key not in seen
        seen.add(key)
        assert row["id"] in selected and row["variant"] in ("A","B")
        if row["status"]!="COMPLETE":
            assert row.get("error")
            continue
        assert row["model"]=="glm-5.3-flash"
        expected=gold[row["id"]]
        actual=row["selected_tool"]
        arguments=row["selected_arguments"]
        name_correct=actual==expected["expected_tool"]
        args_correct=arguments==expected["expected_arguments"]
        schema_ok=schema_valid(actual,arguments,lookup[row["variant"]])
        native=(row["response_kind"]=="native_tool_use")
        if native:
            assert row["stop_reason"]=="tool_use"
            assert row["provider_tool_use_id_present"] is True
            assert actual in lookup[row["variant"]]
        else:
            assert row["stop_reason"]=="end_turn"
            assert actual in ("NONE","TEXT")
        evaluated.append({
            "id":row["id"],"variant":row["variant"],
            "name_correct":name_correct,"args_correct":args_correct,
            "schema_valid":schema_ok,"exact":name_correct and args_correct and schema_ok,
            "native_tool_use":native,
            "expected_none":expected["expected_tool"]=="NONE",
            "chosen_name":actual,"chosen_args":arguments,
            "model_txt":row.get("model_visible_text") if not native else None
        })
    # Independent mutation: a valid tool call with one deliberately deleted
    # required argument must be rejected by the constraint oracle.
    valid_positive = next((x for x in evaluated if x["native_tool_use"] and
                          x["schema_valid"] and not x["expected_none"]),None)
    assert valid_positive is not None, "No native valid tool call observed"
    definition=lookup[valid_positive["variant"]][valid_positive["chosen_name"]]
    required=definition["function"]["parameters"]["required"]
    altered=dict(valid_positive["chosen_args"])
    altered.pop(required[0],None)
    assert not schema_valid(valid_positive["chosen_name"], altered,
                            lookup[valid_positive["variant"]])
    by_variant={}
    for variant in ("A","B"):
        rows=[x for x in evaluated if x["variant"]==variant]
        calls=[x for x in raw["calls"] if x["variant"]==variant]
        completed=[x for x in calls if x["status"]=="COMPLETE"]
        by_variant[variant]={
            "calls_attempted":len(calls),"calls_complete":len(completed),
            "calls_blocked":len(calls)-len(completed),
            "decisions":len(rows),
            "native_tool_use":sum(x["native_tool_use"] for x in rows),
            "name_correct":sum(x["name_correct"] for x in rows),
            "arguments_correct":sum(x["args_correct"] for x in rows),
            "schema_valid":sum(x["schema_valid"] for x in rows),
            "exact_correct":sum(x["exact"] for x in rows),
            "no_tool_total":sum(x["expected_none"] for x in rows),
            "spurious_tool_calls_on_none":sum(x["expected_none"] and
                                              x["native_tool_use"] for x in rows),
            "p50_elapsed_ms":statistics.median(x["elapsed_ms"] for x in completed)
                if completed else None,
            "p95_elapsed_ms":pct([x["elapsed_ms"] for x in completed],.95),
            "provider_usage":{field:sum((x.get("usage")or{}).get(field,0)
                                       for x in completed)
                              for field in ("input_tokens","output_tokens",
                                            "cache_read_input_tokens")},
            "local_child_cpu_s":round(sum(x["cpu_user_s"]+x["cpu_sys_s"]
                                           for x in calls),3),
            "local_child_io_blocks":sum(x["local_inblocks"]+x["local_oublocks"]
                                         for x in calls),
        }
    positions={(x["id"],x["variant"]):x for x in evaluated}
    pairs=[]
    for id_ in selected:
        a,b=positions.get((id_,"A")),positions.get((id_,"B"))
        if not a or not b:
            continue
        pairs.append({
            "id":id_, "A_exact":a["exact"],"B_exact":b["exact"],
            "tool_changed":a["chosen_name"]!=b["chosen_name"],
            "args_changed":a["chosen_args"]!=b["chosen_args"],
            "A_native":a["native_tool_use"],"B_native":b["native_tool_use"],
        })
    pair_summary={
        "paired_tasks":len(pairs),
        "both_exact":sum(x["A_exact"] and x["B_exact"] for x in pairs),
        "only_A":sum(x["A_exact"] and not x["B_exact"] for x in pairs),
        "only_B":sum(x["B_exact"] and not x["A_exact"] for x in pairs),
        "both_wrong":sum(not x["A_exact"] and not x["B_exact"] for x in pairs),
        "different_tool":sum(x["tool_changed"] for x in pairs),
        "different_arguments":sum(x["args_changed"] for x in pairs),
    }
    assert pair_summary["paired_tasks"] == sum(
        pair_summary[k] for k in ("both_exact","only_A","only_B","both_wrong"))
    verdict="ACCEPT_BOUNDED_PROVIDER_NATIVE_TOOL_USE_AB" if len(pairs)==20 else         "PARTIAL_NATIVE_TOOL_USE_AB"
    record={
        "date":"2026-11-07","study":"decision-geometry-harness",
        "source_pin":PIN,"serializer_sha256":SERIALIZER_SHA,
        "fixture_sha256":sha(fixture_bytes),"wire_sha256":sha(wire_bytes),
        "native_result_sha256":sha(result_bytes),
        "schema_mutation_rejected":True,
        "required_argument_mutation_rejected":True,
        "variant":by_variant,"paired":pair_summary,
        "scored":evaluated,"pairs":pairs,
        "status":verdict,
        "limitations":[
            "Real ZCode native tool_use via Anthropic Messages, NOT DSH native DeepSeek transport",
            "Exact DSH schema converted into Anthropic input_schema, without real tool execution",
            "One provider sample per case/variant, no fixed decoding seeds or independent human gold",
            "Twenty authored cases and three NONE controls, not a representative production workload",
            "A/B swaps both function order and property order",
            "No real provider GPU metrics, no actual end-to-end agent task correctness"
        ]
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":verdict,"variant":by_variant,
                      "paired":pair_summary},ensure_ascii=False))


if __name__=="__main__":
    main()
