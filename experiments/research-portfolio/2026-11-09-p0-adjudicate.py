#!/usr/bin/env python3
"""Derive a 16-P0 per-pair decision ledger from immutable synthetic receipts.

The independent checker (separate file) computes oracle metrics without
importing this generator; this generator never executes experiments.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"data/results/research-portfolio"
MATRIX=ROOT/"data/project-fit/portfolio/2026-11-09-targeted-fit.json"
OUTPUT=DATA/"2026-11-09-p0-experiment-ledger.json"
REPORT=ROOT/"portfolio/2026-11-09/p0-experiment-results.md"

RECEIPTS={
 "agent-risk/agent-config":"2026-11-09-p0-agent-risk-agent-config.json",
 "agent-mosaic/dsh-team-context":"2026-11-09-p0-agent-mosaic-team-context.json",
 "exactly-once-limbo/TelegramBot":"2026-11-09-p0-exactly-once-limbo-telegram.json",
 "mcp-toolbox-postgres/Wiki_PG":"2026-11-09-p0-mcp-toolbox-pg.json",
 "paper2agent/dsh-paper2agent":"2026-11-09-p0-paper2project-symlink.json",
}
BLOCKERS={
 "agent-mosaic/dsh-runtime":("BLOCKED_ADAPTER","No outbound claim-source authority guard wired at SessionCommandController.prompt; only source symbol exists.",
    "Build a read-only evidence admission seam, freeze 80 cited claims and an independent source/permission oracle."),
 "agent-risk/dsh-runtime":("BLOCKED_REPLAY_ORACLE","No immutable per-step tool-effect log with a restorable session and independent replay oracle was established in the pinned source.",
    "Provide 40 deterministic episodes +12 tamper/partial controls and recoverable state before A/B."),
 "drag/Wiki_PG":("BLOCKED_ENV_AND_ORACLE","Original retrieve() depends on missing isolated chromadb/embedding runtime; no frozen relevant/OOD 60-query quality gold.",
    "Freeze 60 source-labeled retrieval queries, approved embedding/index version and isolated no-network retrieval consumer."),
 "htn-orchestrate/dsh-runtime":("BLOCKED_ADAPTER","Session prompt is not an HTN planner, and no project-bound scheduler/dependency result adapter was identified.",
    "Implement narrow dependency-checked planner seam in isolated runner and replay 48 DAG +8 invalid graphs."),
 "novafabric/dsh-runtime":("BLOCKED_ADAPTER","No own tool-side-effect capsule emitter or restorable replay boundary verified; a prompt symbol is insufficient.",
    "Pin 40 episodes and 12 corrupted capsules, side-effect ledger and independent state-hash oracle."),
 "novafabric/sequential-rca":("BLOCKED_ADAPTER","score_review has 14 passing archived tests; no NovaFabric capsule intake, independently checked hash chain or 40 matched traces integrated.",
    "Add isolated receipt-consumer adapter and compare 40 real schema traces +12 tampered artifacts."),
 "veriharness/agent-skills":("BLOCKED_ADAPTER","Three static skill tests pass, but no dynamic reviewer/citation admission consumer exists in this repository.",
    "Define exact input/output contract and 80 independently labeled source-span claims; keep plugin execution disabled."),
 "veriharness/dsh-paper2agent":("BLOCKED_SEMANTIC_ORACLE","Original App.citation validates source-bound line range but not semantic sufficiency; no qualified independent claim-to-context oracle or candidate added.",
    "Supply sealed 80 supported/unsupported claims and an isolated App.review_analysis consumer with independent semantic labels."),
 "harnesssecurity-bench/dsh-runtime":("BLOCKED_EFFECT_ORACLE","No actual permission-enforced effect boundary and held-out 80 attack/legitimate trace pairs in the isolated session code.",
    "Pin exact allowed-operation oracle and run 80 malicious/legitimate trace pairs with negative controls."),
 "poisoned-skills/agent-skills":("BLOCKED_RUNTIME_SEAM","Static skill contract suite is not a runtime tool execution authorization boundary.",
    "Identify real skill-ingest/effect consumer and run 80 attacks without executing untrusted code or network."),
 "sequential-diagnosis-language-models/TrinMedicalBot":("BLOCKED_CLINICAL_ORACLE","17 offline tests cover blind-review plumbing, not an expert-adjudicated 60-vignette model comparison; qualified specialist and sealed clinical gold unavailable.",
    "Require independent qualified clinical adjudicators, synthetic no-PHI 60-case gold, critical-risk rule and explicit medical deployment review."),
}
DETERMINATIONS={
 "agent-risk/agent-config":("PILOT_PASS_CONDITIONAL","RESEARCH_CANDIDATE_NOT_APPROVED",
     "Current quote guard: 18/50 false positives; candidate: 0/50; both preserved 30/30 valid claims. Synthetic p95 meets declared 1.25x rule. 10 isolated patched unit tests pass.",
     "Review and test minimal 5-line patch on a separate, truly held-out project review corpus; owner-approved PR only after independent gate."),
 "agent-mosaic/dsh-team-context":("PILOT_FAIL_COST","REJECT_CURRENT_PROTOTYPE",
     "On 60 constructed source-manifest cases, incorrect retrieved source hits 300 -> 0, but 95th-percentile per-call time rose >1.25x; toy manifest not established in runtime.",
     "Optimize source manifest verification and run a real frozen retrieval corpus with independent relevance/authorization oracle and p95."),
 "exactly-once-limbo/TelegramBot":("PILOT_FAIL_LIVENESS","REJECT_CURRENT_PROTOTYPE",
     "On 120 mock sends, duplicate remote effects 60 -> 0, but 90/120 candidate outcomes quarantined as UNKNOWN; no server-side reconciliation. Candidate p95 increased.",
     "Do not deploy until server-side idempotency/reconciliation or human resolution protocol exists, with measured delivery completeness and bounded UNKNOWN recovery."),
 "mcp-toolbox-postgres/Wiki_PG":("PILOT_NO_INCREMENTAL_GAIN","NO_CHANGE",
     "Direct existing GUC reader and existing MCP wrapper both reproduce all 40 valid snapshot values and reject 8 malformed cases; duplicate wrapper showed no accuracy gain and higher p95.",
     "Retain the existing get_postgres_setting contract; revisit only if controlled real-use benchmark proves a missing field/contract."),
 "paper2agent/dsh-paper2agent":("PILOT_PASS_CONDITIONAL","RESEARCH_CANDIDATE_NOT_APPROVED",
     "Original source accepted 3/3 prohibited same-root symlink imports; isolated minimal pre-resolve guard rejected 3/3, preserving 30/30 legitimate source imports and 9 other negative checks. Patched suite 65 pass, 15 skip.",
     "Submit minimal symlink fix with regression test from clean origin/main worktree; independent source review and CI before merge; review ancestor symlink edge cases separately."),
}
SUITE_MAP={
 "agent-risk/agent-config":"agent-config-review",
 "agent-mosaic/dsh-team-context":None,
 "drag/Wiki_PG":"wiki-pg-guc",
 "exactly-once-limbo/TelegramBot":None,
 "mcp-toolbox-postgres/Wiki_PG":"wiki-pg-guc",
 "novafabric/sequential-rca":"sequential-rca-review",
 "veriharness/agent-skills":"agent-skills-static",
 "veriharness/dsh-paper2agent":"paper2project-core",
 "paper2agent/dsh-paper2agent":"paper2project-core",
 "poisoned-skills/agent-skills":"agent-skills-static",
 "sequential-diagnosis-language-models/TrinMedicalBot":"trinmedical-clinical-plumbing",
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((DATA/name).read_text())

def build():
 matrix=json.loads(MATRIX.read_text())
 p0=[r for r in matrix["pairs"] if r["priority"]=="P0"]
 assert len(p0)==16
 assert {r["study_id"]+"/"+r["project_id"] for r in p0}==set(RECEIPTS)|set(BLOCKERS)
 suite=read("2026-11-09-p0-target-snapshot-tests.json")
 candidate_suite=read("2026-11-09-p0-candidate-unit-suites.json")
 assert all(t["returncode"]==0 for t in suite["tests"])
 assert all(t["returncode"]==0 for t in candidate_suite["results"])
 suites={r["id"]:r for r in suite["tests"]}
 result=[]
 for row in p0:
  key=row["study_id"]+"/"+row["project_id"]
  anchor=row["source_anchor"]
  assert anchor and anchor["repo"]==row["project_id"]
  item={
   "study_id":row["study_id"],"project_id":row["project_id"],"pair_id":key,
   "study_decision_scope":row["phase"],
   "source_anchor":anchor,
   "protocol_id":row["test_protocol_id"],
   "baseline_suite_id":SUITE_MAP.get(key),
   "baseline_suite_status":suites[SUITE_MAP[key]]["returncode"] if SUITE_MAP.get(key) else None,
   "production_approval":False,"target_repo_changed":False,
   "independent_oracle_kind":"DETERMINISTIC_SYNTHETIC_LABELS_ONLY" if key in RECEIPTS else "UNAVAILABLE",
   "owner_gate":"SOURCE_REVIEW_AND_OWNER_SIGNOFF_REQUIRED",
  }
  if key in RECEIPTS:
   name=RECEIPTS[key];raw=read(name)
   assert raw["pair"]==key and raw["source_git_sha"]==anchor["commit"]
   assert raw["source_file_sha256"]==anchor["file_sha256"]
   status,decision,meaning,nextgate=DETERMINATIONS[key]
   t=raw["timing"]
   item.update({
    "execution_status":status,"adoption_decision":decision,
    "measured_scope":raw["scope"],"measurement_summary":meaning,
    "baseline":raw["baseline"],"candidate":raw["candidate"],
    "latency_ratio_p95":round(t["p95_candidate_ns"]/t["p95_baseline_ns"],4),
    "evidence":[{"path":"data/results/research-portfolio/"+name,"sha256":sha(DATA/name)}],
    "next_gate":nextgate,"experiment_executed":True,
   })
   if key=="agent-risk/agent-config":
    patch=ROOT/"experiments/research-portfolio/2026-11-09-p0-agentconfig-candidate.patch"
    item["evidence"].append({"path":patch.relative_to(ROOT).as_posix(),"sha256":sha(patch)})
   if key=="paper2agent/dsh-paper2agent":
    patch=ROOT/"experiments/research-portfolio/2026-11-09-p0-paper2project-symlink-candidate.patch"
    assert raw["candidate_patch_sha256"]==sha(patch)
    item["evidence"].append({"path":patch.relative_to(ROOT).as_posix(),"sha256":sha(patch)})
  else:
   why,nextgate=BLOCKERS[key][1:]
   item.update({
     "execution_status":BLOCKERS[key][0],"adoption_decision":"BLOCKED",
     "measured_scope":"NONE_FOR_PROPOSED_P0_AB",
     "measurement_summary":"No source-integrated matched A/B was run for this pair.",
     "baseline":None,"candidate":None,
     "latency_ratio_p95":None,
     "blocker":why,"next_gate":nextgate,"experiment_executed":False,"evidence":[],
   })
  result.append(item)
 result.sort(key=lambda r:(r["adoption_decision"]=="BLOCKED",r["study_id"],r["project_id"]))
 return {
   "date":"2026-11-09","scope":"ALL_16_P0_ISOLATED_PINNED_TARGET_SNAPSHOT_ATTEMPTS",
   "method":"All experiments in temporary pinned Git archives, network-unshared; no original source edited",
   "candidate_matrix_sha256":sha(MATRIX),
   "source_suites_receipt_sha256":sha(DATA/"2026-11-09-p0-target-snapshot-tests.json"),
   "candidate_suites_receipt_sha256":sha(DATA/"2026-11-09-p0-candidate-unit-suites.json"),
   "counts":{"total":len(result),"measured_synthetic_ab":len(RECEIPTS),
             "blocked_before_experiment":len(BLOCKERS),
             "conditionally_promising":2,"reject_current_prototype":2,
             "no_incremental_gain":1,"approved_for_production":0},
   "rows":result,
   "limitations":[
       "Independent numerical verifier is external to experiment runner, but tests use synthetic deterministic oracle, not a second human/scientific replication.",
       "Sample p95 numbers are small isolated timing measurements; comparative latency effects have not been reproduced on realistic held-out workloads.",
       "No full-source model/DB/retrieval/system E2E, clinical specialist evaluation, real Telegram messaging or medical PHI.",
       "Positive test means only bounded candidate for next gate, never permission to deploy.",
       "Previously recorded 81/83 scientific dispositions and 506 historical project assessments are unchanged.",
   ],
 }

def report(x):
 c=x["counts"];lines=[
 "# P0 research integration: isolated experiment execution and independent gates",
 "",
 "**Date:** 2026-11-09. **Source:** 16 P0 pairs in the [targeted matrix](../../data/project-fit/portfolio/2026-11-09-targeted-fit.json).",
 "",
 "**Result:** {} isolated source-level synthetic A/B; {} blocked by missing target adapter, runtime or oracle. "
 "{} candidates for further review, {} prototypes rejected, {} redundant/no measured incremental change. **0 production approvals.**".format(
 c["measured_synthetic_ab"],c["blocked_before_experiment"],
 c["conditionally_promising"],c["reject_current_prototype"],c["no_incremental_gain"]),
 "",
 "Source snapshots were Git-archived at pinned commits and original referenced blobs checked byte-for-byte. "
 "No private project descriptions, clinical patient data, messages, production databases or target project code changed.",
 "",
 "## Every P0 pair: observed effect and decision", "",
 "| Study | Target | Execution / deployment decision | Measured effect or blocker | Follow-up |",
 "| --- | --- | --- | --- | --- |",
 ]
 for r in x["rows"]:
  expl=r["measurement_summary"] if r["experiment_executed"] else r["blocker"]
  lines.append("| {} | {} | {} / **{}** | {} | {} |".format(
    r["study_id"],r["project_id"],r["execution_status"],r["adoption_decision"],
    expl,r["next_gate"]))
 lines.extend(["","## Exact bounded A/B numeric summary","",
               "| Pair | Original baseline | Candidate | p95 ratio | Decision |",
               "| --- | --- | --- | --- | --- |"])
 for r in x["rows"]:
  if not r["experiment_executed"]:continue
  lines.append("| {} | {} | {} | {}× | {} |".format(
    r["pair_id"],str(r["baseline"]).replace("|","/"),str(r["candidate"]).replace("|","/"),
    r["latency_ratio_p95"],r["adoption_decision"]))
 lines.extend(["","## Evidence receipts and source-level patch proposals",""])
 for r in x["rows"]:
  if not r["evidence"]:continue
  lines.append("### "+r["pair_id"])
  lines.append("")
  a=r["source_anchor"]
  lines.append("Pinned source: [{}:{}]({}), SHA256 of original code blob: {}.".format(
    a["path"],a["line"],a["url"],a["file_sha256"]))
  for e in r["evidence"]:
   lines.append("- [Evidence or minimal isolated patch](../../"+e["path"]+") · sha256 "+e["sha256"])
  lines.append("")
 lines.extend(["## Baseline unit suites and negative controls","",
               "Pinned archived target-suite receipts: [read-only network-disabled tests](../../data/results/research-portfolio/2026-11-09-p0-target-snapshot-tests.json). "
               "Candidate patch suites: [separate network-disabled execution](../../data/results/research-portfolio/2026-11-09-p0-candidate-unit-suites.json).",
               "",
               "Independent numerical check: p0-independent-check.py verifies all outcome classifications, direct fixture labels, source blob SHA, all 16 pairs, five measured receipts and deliberate mutation negatives. "
               "This is NOT human model benchmarking or production acceptance.",
               "",
               "## Integration and resource trade-offs","",
               "- Strict quote checks and pre-resolve symlink guarding have small code footprints and measurable synthetic false-allow reductions; full representative holdouts and target-repo CI are the next gate.",
               "- Source-manifest filtering can remove toy injected results but requires a trustworthy manifest, increases computation and in this run exceeded the originally declared 1.25x p95 budget.",
               "- Quarantining uncertain Telegram outcomes avoids blind duplicate retries but stalls completion; without remote dedupe/reconciliation it cannot promise exactly-once semantics.",
               "- The Wiki_PG GUC MCP tool already exists and is deterministic on synthetic snapshots. Adding another layer under YAGNI is unjustified without evidence of a missing capability.",
               "- The remaining P0 scenarios require project-bound adapters, a stable execution context, actual model outcomes or qualified clinical experts. They remain explicitly blocked.",
               "",
               "**Publication is not deployment:** all original target repositories remain unchanged. "
               "Existing historical research/project-fit decisions are preserved. No production authorization granted.",""])
 return "\n".join(lines)

def main():
 p=argparse.ArgumentParser();p.add_argument("--generate",action="store_true");p.add_argument("--check",action="store_true")
 a=p.parse_args();assert a.generate!=a.check
 result=build()
 if a.generate:
  OUTPUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
  REPORT.write_text(report(result))
 else:
  assert OUTPUT.read_text()==json.dumps(result,indent=2,ensure_ascii=False)+"\n","Stale machine ledger"
  assert REPORT.read_text()==report(result),"Stale human report"
 print("P0_ADJUDICATION",result["counts"])

if __name__=="__main__":main()
