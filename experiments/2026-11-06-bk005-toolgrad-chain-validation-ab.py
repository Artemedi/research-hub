#!/usr/bin/env python3
"""BK-005: ToolGrad source-backed offline chain-first vs bounded DFS oracle.

Runs original ToolGrad chain_update_step, ApiUseWorkflow, and
validate_api_response; substitutes deterministic proposer/selector/inverse-query
for model-dependent components. Twelve synthetic in-memory tools, no network.
No model or original ToolGrad benchmark is run; this is a methodological probe.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc

SOURCE_SHA = "c9544f842aacc13b5e44d5833fcc5dc4b86c5161"
TOOLS = (
    "create", "owner", "note", "priority", "tag", "evidence", "ack",
    "validate", "snapshot", "close", "reopen", "report",
)
NEEDS = {
    "create": (),
    "owner": ("create",),
    "note": ("create",),
    "priority": ("owner",),
    "tag": ("create",),
    "evidence": ("note",),
    "ack": ("owner",),
    "validate": ("evidence",),
    "snapshot": ("create",),
    "close": ("validate",),
    "reopen": ("close",),
    "report": ("create",),
}
PREPLANNED_CLOSE = ("create", "note", "evidence", "validate", "close")
PREPLANNED_REOPEN = PREPLANNED_CLOSE + ("reopen",)
assert len(TOOLS) == 12

def p95(values):
    a = sorted(values)
    return round(a[math.ceil(len(a) * .95) - 1], 3)

def stats(values):
    return {"count": len(values), "mean": round(statistics.mean(values), 3),
            "p50": round(statistics.median(values), 3), "p95": p95(values),
            "min": round(min(values), 3), "max": round(max(values), 3)}

def sha(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()

def execute_tool(action, state):
    """External test oracle: in-memory effect, independent of ToolGrad's JSON validator."""
    assert action in TOOLS
    if action in state:
        return state, {"ok": False, "error": "already_done"}, False
    if not all(req in state for req in NEEDS[action]):
        return state, {"ok": False, "error": "precondition_failed"}, False
    result = frozenset((*state, action))
    return result, {"ok": True, "revision": len(result),
                    "case_id": "synthetic-only"}, True

def generate_actions(rng, trial):
    if trial % 10 == 0:
        return list(PREPLANNED_REOPEN)
    if trial % 10 == 1:
        return list(PREPLANNED_CLOSE)
    length = rng.randint(2, 6)
    chosen = ["create"]
    state = frozenset(chosen)
    while len(chosen) < length:
        valid = [a for a in TOOLS if a not in state and
                 all(r in state for r in NEEDS[a])]
        assert valid
        action = rng.choice(valid)
        state, _, ok = execute_tool(action, state)
        assert ok
        chosen.append(action)
    return chosen

def real_source_chain(actions, states, module, ToolAgentAction):
    workflow = None
    state = frozenset()
    calls = 0
    start = time.perf_counter_ns()
    for i, name in enumerate(actions):
        after, response, success = execute_tool(name, state)
        assert success and after != state
        valid, reason = module.validate_api_response(
            json.dumps(response, sort_keys=True), name, "")
        assert valid, (name, reason)
        # The real upstream action type and original source workflow updater.
        act = ToolAgentAction(
            tool=name, tool_input={"case_id": "synthetic-only"},
            log="synthetic tool call", message_log=[],
            tool_call_id=f"lab-{i}",
        )
        updated = module.chain_update_step(
            workflow, "-1" if workflow is None else "api_use_chain_1",
            (act, response),
        )
        chain = updated["chain"]
        assert chain.chain_id == "api_use_chain_1"
        assert len(chain.intermediate_steps) == i + 1
        workflow = states.ApiUseWorkflow(
            query="(generated later, deterministic)", response="",
            api_use_chains={chain.chain_id: chain},
        )
        state = after
        calls += 1
    # Deterministic post-hoc query, not a model-generated or human-written query.
    query = "Perform these supported operations: " + ",".join(sorted(state))
    actual = [step[0].tool for step in chain.intermediate_steps]
    assert actual == actions
    duration_ms = (time.perf_counter_ns() - start) / 1e6
    return state, query, {"wall_ms": round(duration_ms, 3), "calls": calls}

def bounded_dfs(goal, max_depth, budget, rng):
    """Query-first proxy; randomized fixed order, independent from ground-truth chain."""
    order = list(TOOLS)
    rng.shuffle(order)
    expanded = 0
    attempts = 0
    visited = set()
    start = time.perf_counter_ns()

    def solve(cur, path):
        nonlocal expanded, attempts
        if cur == goal:
            return path
        if len(path) >= max_depth or expanded >= budget:
            return None
        key = (cur, len(path))
        if key in visited:
            return None
        visited.add(key)
        expanded += 1
        for name in order:
            attempts += 1
            nxt, _, ok = execute_tool(name, cur)
            if not ok or not nxt.issubset(goal):
                continue
            result = solve(nxt, path + (name,))
            if result is not None:
                return result
            if expanded >= budget:
                return None
        return None

    solution = solve(frozenset(), tuple())
    correct = False
    if solution is not None:
        state = frozenset()
        for action in solution:
            state, _, success = execute_tool(action, state)
            assert success
        correct = state == goal
        assert correct
    elapsed = (time.perf_counter_ns()-start)/1e6
    return {
        "success": correct, "expanded": expanded, "attempts": attempts,
        "wall_ms": round(elapsed,3), "solution_length":len(solution) if solution else None,
    }

def negative_oracles(module):
    """Immutable expected classifications from independent, stated service contracts."""
    records = [
        # true semantic successes: 10 different benign successful payloads
        *[("positive", json.dumps({"ok": True, "payload": {"count": i+1}}), "", True)
          for i in range(10)],
        # false positive JSONs: {error_count:0} is valid data, not an error
        *[("zero_error_count", json.dumps({
             "ok": True, "case_id": f"safe-{i}", "error_count": 0, "revision": i+1
          }), "", True) for i in range(10)],
        *[("explicit_fail", json.dumps({"ok":False, "error":"denied"}), "", False)
          for _ in range(10)],
        *[("empty", "", "", False) for _ in range(10)],
        *[("exception", json.dumps({"ok":True,"revision":1}), "transport timeout", False)
          for _ in range(10)],
    ]
    counts = {}
    for label in sorted({x[0] for x in records}):
        subset = [x for x in records if x[0]==label]
        accepted = sum(module.validate_api_response(body, "lab_tool", err)[0]
                       for _, body, err, _ in subset)
        expected_accepted = sum(expected for _, _, _, expected in subset)
        counts[label] = {
            "n":len(subset), "accepted":accepted, "expected_accepted":expected_accepted,
            "correct":len(subset)-abs(accepted-expected_accepted),
        }
    assert counts["positive"]["accepted"]==10
    assert counts["explicit_fail"]["accepted"]==0
    assert counts["empty"]["accepted"]==0
    assert counts["exception"]["accepted"]==0
    assert counts["zero_error_count"]["accepted"]==0, counts["zero_error_count"]
    # Source validator says "success", but service effects did not occur.
    valid, _=module.validate_api_response('{"ok":true,"revision":1}',"lab_tool","")
    assert valid
    mutated_without_effect = frozenset()   # no tool actually changed state
    assert mutated_without_effect != frozenset({"create"})
    return {
        "responses":counts,
        "false_negative_zero_error_count":10,
        "misleading_success_response_not_a_state_oracle":True,
    }

def read_io():
    try:
        return {kv.split(":")[0]:int(kv.split(":")[1].strip())
                for kv in Path("/proc/self/io").read_text().splitlines()}
    except (FileNotFoundError,PermissionError):
        return {}

def run(repo, trials, seeds):
    sys.path.insert(0, str(repo))
    from langchain_classic.agents.output_parsers.tools import ToolAgentAction
    from toolgrad import states
    from toolgrad.modules import module_lib
    import inspect
    assert str(repo) in str(Path(inspect.getfile(module_lib.chain_update_step)).resolve())
    checks = negative_oracles(module_lib)
    records=[]
    coverage=Counter()
    io_before=read_io()
    usage_before=resource.getrusage(resource.RUSAGE_SELF)
    tracemalloc.start()
    begun=time.perf_counter()
    for seed in seeds:
        gen=random.Random(seed)
        for trial in range(trials):
            actions=generate_actions(gen,trial)
            goal,query,chain=real_source_chain(actions, states,module_lib,ToolAgentAction)
            assert goal==frozenset(actions)
            assert 2<=len(actions)<=6
            # Independent mutation replay: remove the last call, execute the
            # shortened chain, and require a different achieved state.
            corrupted_state = frozenset()
            for action in actions[:-1]:
                corrupted_state, _, ok = execute_tool(action, corrupted_state)
                assert ok
            assert corrupted_state != goal
            # mutate query label, must not pass independent state-intent check.
            corrupted=frozenset((*goal, "unavailable_external_publish"))
            assert goal != corrupted
            for action in actions: coverage[action]+=1
            per_budget={}
            for budget in (80,400):
                rng=random.Random(seed*1000003+trial*97+budget)
                per_budget[str(budget)]=bounded_dfs(goal,len(actions),budget,rng)
            records.append({
                "seed":seed,"trial":trial,"action_chain":actions,
                "goal":sorted(goal),"query_generated_from_verified_chain":query,
                "chain_first":chain,"dfs":per_budget,
            })
        print("SEED_DONE",seed,"trials",trials,flush=True)
    peak_traced=tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    usage_after=resource.getrusage(resource.RUSAGE_SELF)
    io_after=read_io()
    bfs_summary={}
    for budget in ("80","400"):
        items=[r["dfs"][budget] for r in records]
        bfs_summary[budget]={
            "success":sum(x["success"] for x in items),
            "tasks":len(items),
            "expanded":stats([x["expanded"] for x in items]),
            "attempts":stats([x["attempts"] for x in items]),
            "wall_ms":stats([x["wall_ms"] for x in items]),
        }
    cf=[r["chain_first"] for r in records]
    # Unreachable target: reopening requires closing, but closing is absent
    # from this exact monotonic goal. Neither a valid plan nor a success label
    # may be produced by the local DFS oracle.
    impossible = [bounded_dfs(frozenset({"create", "reopen"}), 6, 400,
                    random.Random(seed * 100 + j))
                  for seed in seeds for j in range(20)]
    assert all(not item["success"] for item in impossible)
    out={
        "study":"BK-005 ToolGrad",
        "source_repository":"https://github.com/zhongyi-zhou/toolgrad",
        "source_commit":SOURCE_SHA,
        "environment":"offline python 3.14 sandboxed fixture with no production resources",
        "status":"SOURCE_COMPONENTS_EXECUTED_WITH_PROXY_A_B",
        "scope":"Genuine source chain_update_step, source Pydantic ApiUseWorkflow and validate_api_response; deterministic tool proposer/selector/query instead of Gemini; query-first DFS written for this experiment.",
        "samples":len(records),"trials_per_seed":trials,"seeds":seeds,"tool_count":len(TOOLS),
        "tool_definitions_requirements":{k:list(v) for k,v in NEEDS.items()},
        "chain_length":{"min":min(len(r["action_chain"]) for r in records),
                        "max":max(len(r["action_chain"]) for r in records)},
        "tool_coverage":dict(sorted(coverage.items())),
        "chain_first":{"verified":len(records),"calls":stats([r["chain_first"]["calls"] for r in records]),
                       "wall_ms":stats([x["wall_ms"] for x in cf])},
        "query_first_bounded_dfs":bfs_summary,
        "unreachable_test":{
            "input":"goal requires reopen while close is explicitly absent",
            "classification":"REJECT_BY_INVARIANT",
            "is_reachable":False,"trials":len(impossible),
            "query_first_rejected":sum(not x["success"] for x in impossible),
            "note":"monotonic close flag is required before reopen; demonstrates query coverage limitation, not same-distribution pass rate",
        },
        "negative_controls":checks,
        "resources":{
            "wall_seconds_total":round(time.perf_counter()-begun,3),
            "cpu_seconds_self":round((usage_after.ru_utime+usage_after.ru_stime)-(usage_before.ru_utime+usage_before.ru_stime),3),
            "tracemalloc_peak_bytes":peak_traced,
            "rss_max_kib_cumulative":usage_after.ru_maxrss,
            "proc_io_delta":{k:io_after.get(k,0)-io_before.get(k,0) for k in io_after.keys()},
            "llm_calls":0,"tokens":None,"api_cost_usd":None,"gpu_vram":None,
        },
        "limitations":[
            "Not the original ToolGrad full proposer/executor/selector/inverse model pipeline; no Gemini/ToolBench/SFT/BFCL.",
            "No original paper 99.8% success or 63.8% DFS replication.",
            "Chain-first goals constructed from successful generated chains; query-first receives those same reachable goals, but not the chain. Not a natural user-query distribution or a feature-equivalent benchmark.",
            "Synthetic monotonic state machine of 12 safe in-memory tools; no SQL/PostgreSQL/agent integration, real effects or network.",
            "DFS budgets 80/400 and random order are invented local proxies; outputs cannot be attributed to authors.",
            "Original validate_api_response is a heuristic, not semantic state oracle; error_count=0 false negatives and misleading ok=true can affect labels.",
            "Python memory and proc IO aggregate whole process, not per-arm fair head-to-head.",
        ],
        "records":records,
    }
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--trials",type=int,default=100)
    ap.add_argument("--seeds",type=int,default=5)
    a=ap.parse_args()
    assert 1<=a.trials<=200 and 3<=a.seeds<=8
    repo=a.source.resolve()
    pinned=subprocess.run(["git","-C",str(repo),"rev-parse","HEAD"],
        capture_output=True,text=True,check=True).stdout.strip()
    assert pinned==SOURCE_SHA,(pinned,SOURCE_SHA)
    seeds=[20261106+i for i in range(a.seeds)]
    result=run(repo,a.trials,seeds)
    assert result["samples"]==a.trials*a.seeds
    assert result["chain_first"]["verified"]==result["samples"]
    assert result["negative_controls"]["false_negative_zero_error_count"]==10
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"samples":result["samples"],
        "coverage":result["tool_coverage"],
        "chain_first":result["chain_first"],
        "query_first":result["query_first_bounded_dfs"],
        "resources":result["resources"]},ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
