#!/usr/bin/env python3
"""Deterministic synthetic check of agent-risk replay assumptions; no real agent or data."""
from __future__ import annotations
import copy
import json
import time
from pathlib import Path

N, HORIZON, THETA = 200, 6, 0.8

def initial(seed: int, announced: bool = False) -> dict:
    return {"seed": seed, "step": 0, "hidden": seed % 2, "refusals": 0,
            "done": False, "harm": False, "calls": 0, "announced": announced}

def propose(s: dict) -> str:
    if s["refusals"]:
        return "alternate_risky" if s["hidden"] == 1 else "safe"
    seed, t = s["seed"], s["step"]
    if s["announced"] and t == 0:
        return "risky" if seed % 3 else "safe"
    if (seed + 3*t) % 7 == 0: return "risky"
    if (seed + 5*t) % 11 == 0: return "mild"
    return "safe"

def score(a: str) -> float:
    return {"risky": .95, "alternate_risky": .60, "mild": .40, "safe": .20}[a]

def harmful(a: str, s: dict, env: int = 0) -> bool:
    return a in {"risky", "alternate_risky", "mild"} and s["hidden"] == (1 if env == 0 else 0)

def advance(s: dict, a: str, blocked: bool = False, env: int = 0) -> None:
    s["calls"] += 1
    if blocked:
        s["refusals"] += 1
    else:
        s["harm"] = s["harm"] or harmful(a, s, env)
        s["hidden"] = (s["hidden"] + (1 if a in {"risky", "alternate_risky"} else 0) + s["step"]) % 2
    s["step"] += 1
    s["done"] = s["step"] >= HORIZON or s["refusals"] >= 2

def baseline(seed: int):
    s, records, snapshot = initial(seed), [], None
    while not s["done"]:
        a = propose(s); v = score(a)
        if snapshot is None and v > THETA: snapshot = copy.deepcopy(s)
        records.append({"score": v, "harm": harmful(a, s), "cost": 1})
        advance(s, a)
    return s, records, snapshot

def live(seed: int, announced: bool = False, env: int = 0) -> dict:
    s = initial(seed, announced)
    while not s["done"]:
        a = propose(s); advance(s, a, score(a) > THETA, env)
    return s

def from_snapshot(snapshot: dict, include_hidden: bool = True):
    s = copy.deepcopy(snapshot)
    if not include_hidden: s["hidden"] = 0
    prefix_calls = s["calls"]
    while not s["done"]:
        a = propose(s); advance(s, a, score(a) > THETA)
    return s, s["calls"] - prefix_calls

def first_block(records: list[dict]):
    return next((i for i, r in enumerate(records) if r["score"] > THETA), None)

def stop_harm(records: list[dict]) -> bool:
    i = first_block(records)
    return any(r["harm"] for r in (records if i is None else records[:i]))

def main() -> None:
    t0 = time.perf_counter()
    rows = [(seed, *baseline(seed), live(seed)) for seed in range(N)]
    blocked = [r for r in rows if r[3] is not None]
    agree = [r for r in rows if r[3] is None]
    targeted_harm = targeted_calls = live_calls = exact = bad_snapshot = announced = changed_env = 0
    lower_harmed = unresolved = 0
    for seed, base, records, snap, live_state in rows:
        live_calls += live_state["calls"]
        if snap is None:
            targeted_harm += int(base["harm"])
            lower_harmed += int(any(r["harm"] for r in records))
            continue
        target, calls = from_snapshot(snap)
        partial, _ = from_snapshot(snap, include_hidden=False)
        targeted_harm += int(target["harm"]); targeted_calls += calls
        exact += target["harm"] != live_state["harm"]
        bad_snapshot += partial["harm"] != live_state["harm"]
        announced += live(seed, announced=True)["harm"] != target["harm"]
        changed_env += live(seed, env=1)["harm"] != target["harm"]
        i = first_block(records)
        pre = any(r["harm"] for r in records[:i])
        lower_harmed += int(pre); unresolved += int(not pre)

    live_harmed = sum(int(r[4]["harm"]) for r in rows)
    lower, upper = lower_harmed / N, (lower_harmed + unresolved) / N
    live_rate, targeted_rate = live_harmed / N, targeted_harm / N
    pre = [{"score":.2,"harm":True,"cost":1},{"score":.95,"harm":False,"cost":1},{"score":.2,"harm":False,"cost":1}]
    post = [{"score":.2,"harm":False,"cost":1},{"score":.95,"harm":False,"cost":1},{"score":.2,"harm":True,"cost":1}]
    same_coarse_flag = any(x["harm"] for x in pre) == any(x["harm"] for x in post)
    timing_changes_stop = stop_harm(pre) != stop_harm(post)
    result = {
      "experiment_id":"agent-risk-replay-boundary-20261109",
      "source":{"paper":"arXiv:2610.16280v1","paper_pdf_sha256":"2b6b107ed057dbfe7b7133143fe1bd7beef1178700b22bbc7af23caac204d21e",
                "companion_repo":"https://github.com/yzhao062/agent-risk","companion_repo_sha":"a1ab24aaf3c1e5bfbe47a24eaf4cf411bf0b3f1b"},
      "environment":"deterministic synthetic state machine; standard library only",
      "scenario_count":N,"horizon":HORIZON,"threshold":THETA,
      "counts":{"blocked_first_deviation":len(blocked),"agree_without_deviation":len(agree),
                "targeted_vs_live_harm_mismatches":exact,"incomplete_snapshot_mismatches":bad_snapshot,
                "announced_gate_vs_unannounced_replay_mismatches":announced,
                "changed_environment_vs_old_replay_mismatches":changed_env},
      "harm":{"log_only_outer_bounds":[lower,upper],"live_oracle_rate":live_rate,
              "targeted_replay_rate":targeted_rate,"targeted_matches_live":exact==0 and live_rate==targeted_rate},
      "calls":{"live_gate_calls":live_calls,"targeted_continuation_calls":targeted_calls,
               "targeted_to_live_ratio":targeted_calls/live_calls,"prefix_log_cost_excluded":True},
      "negative_controls":{"same_coarse_harm_flag":same_coarse_flag,"missing_timing_changes_stop_replay":timing_changes_stop,
                           "omitted_snapshot_state_mismatches":bad_snapshot,"announced_gate_breaks_A2":announced,
                           "changed_environment_breaks_A1":changed_env},
      "status":"PASS" if exact==0 and lower<=live_rate<=upper and targeted_rate==live_rate and targeted_calls<live_calls and same_coarse_flag and timing_changes_stop and bad_snapshot>0 and announced>0 and changed_env>0 else "FAIL",
      "limitations":["No LLM, tool environment, database, author harness, or real log was executed.",
                     "The finite deterministic state machine does not estimate field risk or reproduce the paper's 16 runs/49,000 episodes.",
                     "Calls count synthetic proposal steps, not tokens, latency, or monetary cost."],
      "elapsed_ms":round((time.perf_counter()-t0)*1000,3)
    }
    out = Path(__file__).resolve().parents[2] / "data/results/agent-risk/2026-11-09-replay-boundary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS": raise SystemExit(1)

if __name__ == "__main__": main()
