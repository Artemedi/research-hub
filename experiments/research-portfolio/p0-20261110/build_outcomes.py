#!/usr/bin/env python3
"""Independent 16-pair P0 trial accounting, report and mutation validator.

No external app is invoked in --generate / --check; source-pinned offline
receipts produced previously under bwrap remain independently inspectable.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
MATRIX=ROOT/"data/project-fit/portfolio/2026-11-09-targeted-fit.json"
RECEIPT=ROOT/"data/results/research-portfolio/2026-11-10-p0-boundary-ab.json"
BASELINES=ROOT/"data/results/research-portfolio/2026-11-10-p0-baseline-suites.json"
NODE=ROOT/"data/results/research-portfolio/2026-11-10-p0-team-scope-baseline.json"
OUT=ROOT/"data/results/research-portfolio/2026-11-10-p0-outcomes.json"
REPORT=ROOT/"portfolio/2026-11-10-p0-execution.md"

# Full-suite project application gate and exact missing evidence. These are
# explicit decisions, not inferred from source-symbol presence.
BLOCKERS={
("agent-mosaic","dsh-runtime"):
 ("No output-admission or citation provenance consumer implemented at session-to-response boundary; frozen effect/citation trace and independent full-agent oracle absent.",
  "Build a read-only output-admission probe over pinned session outputs and test 80 bounded prompts with exact independent source spans."),
("agent-mosaic","dsh-team-context"):
 ("Original recallScoped already isolates project scope by default (3/3 network-denied baseline tests); no separate Agent Mosaic evidence-propagation treatment or full retrieval/output evaluation is implemented.",
  "Design source-span propagation beyond existing recall scope, then freeze project/user knowledge corpus and output-citation oracle."),
("agent-risk","agent-config"):
 ("Function-level citation oracle improved, but no integrated review-to-policy approval boundary or held-out actual policy-change dataset; line-bound checks alone do not replay risk.",
  "Patch only the pinned review adapter in isolated copy, run 80 blinded policy-change cases, track downstream allow/deny and nonzero false allow."),
("agent-risk","dsh-runtime"):
 ("Session prompt symbol does not provide a restorable full agent state, deterministic effect journal or pre-change risk replay; no candidate adapter.",
  "Pin a replayable event-state capsule and a held-out risk-policy oracle for 40 isolated agent trajectories."),
("drag","Wiki_PG"):
 ("Pure _rrf_fuse rank-source safety probe succeeded, but current retrieve()/select_retrieval_ids already apply host and curated-source policy; no DRAG implementation or frozen Chroma dense/BM25 retrieval corpus was run.",
  "Compare unchanged retrieval pipeline against a distinct DRAG-style adapter on a frozen authorized 60-query corpus, measure recall, wrong source and p95."),
("exactly-once-limbo","TelegramBot"):
 ("One proposed quarantine variant failed joint safety+delivery: zero duplicate messages but 40/120 lost deliveries; Telegram Bot API authoritative UNKNOWN-effect reconciliation/idempotency is not established.",
  "Reject blind-retry and naive quarantine as complete solutions; prove server-supported deduplication or an owner-approved reconciliation protocol before any new live delivery."),
("htn-orchestrate","dsh-runtime"):
 ("Session prompt entry exists but no integrated hierarchical planner, dependency-checked ticket executor, frozen task DAG or worker-failure oracle.",
  "Implement an isolated non-effecting HTN-vs-fixed-DAG harness for 48 held-out tasks with dependency and resource accounting."),
("mcp-toolbox-postgres","Wiki_PG"):
 ("Current code already exposes get_postgres_setting() with read-only snapshot semantics; no distinct Google MCP Toolbox adapter and no paired numeric fixture comparison against it.",
  "Compare 40 frozen GUC fixtures for the existing Wiki_PG MCP tool and a pinned Toolbox adapter without connecting to production PostgreSQL."),
("novafabric","dsh-runtime"):
 ("No NovaFabric capsule capture/restore integration, immutable side-effect journal or rebooted-session replay oracle is attached to session controller.",
  "Build isolated trace/capsule capture with 40 deterministic episodes and 12 tamper/crash controls."),
("novafabric","sequential-rca"):
 ("Existing 14/14 review tests verify report hashes/attribution but do not exercise a NovaFabric capsule importer or a distinct variant; independent DBA causal judgment is absent.",
  "Connect a read-only capsule input to score_review on synthetic traces; compare original report binding against mutated evidence."),
("veriharness","agent-skills"):
 ("11/11 static skill contract tests pass but they do not execute a reviewer, tool result or VeriHarness evidence verifier; no paired variant.",
  "Instrument an isolated skill-review consumer and evaluate forged quotes and independent line-level gold across 80 claims."),
("veriharness","dsh-paper2agent"):
 ("Published clean Paper2Project offline suite passed 99 tests with 16 explicit skips; core citation() already checks owner/document/range/quote, but no distinct VeriHarness treatment or author benefit A/B.",
  "Run a pinned source-hash and citation false-allow benchmark on a separate proposed verifier; ensure it adds value beyond existing citation()."),
("harnesssecurity-bench","dsh-runtime"):
 ("No bounded effect-authorization simulator or adversarial tool-execution oracle at the pinned session prompt; source-symbol pin is not proof of a security gate.",
  "Use an isolated effect ledger and 80 authorized/forbidden task pairs; measure actual unauthorized effects under treatment."),
("paper2agent","dsh-paper2agent"):
 ("Original Paper2Project already implements source import, exact citations and review, and 99 offline tests passed with 16 skips; no new paper-to-tool treatment, held-out benefit evaluation or distinct adapter.",
  "Compare original import/review workflow with an independently justified new method on pinned synthetic papers and code fixtures."),
("poisoned-skills","agent-skills"):
 ("Static 11/11 skills tests establish structure only, not behavior when a model interprets malicious SKILL.md; no contained tool consumer or attack oracle.",
  "Construct an isolated fake tool/effect runner and independently scored poisoned-versus-clean skill corpus before considering enforcement."),
("sequential-diagnosis-language-models","TrinMedicalBot"):
 ("No independent qualified clinical reviewers or sealed, approved vignette gold; existing score() is not an expert oracle. No real patient data or unsupervised medical model test authorized.",
  "Prepare consent-free synthetic vignettes with independent qualified specialist adjudication and clinical safety governance before supervised A/B."),
}
EXPECTED_PAIRED={
 ("exactly-once-limbo","TelegramBot"):"REJECT_TREATMENT_DELIVERY_REGRESSION",
 ("agent-risk","agent-config"):"PASS_OFFLINE_LINE_BINDING_GUARD",
 ("drag","Wiki_PG"):"PASS_OFFLINE_RANK_SOURCE_GUARD",
}

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def inputs():
    matrix=read(MATRIX)
    receipt=read(RECEIPT)
    baselines=read(BASELINES)
    node=read(NODE)
    return matrix,receipt,baselines,node

def validate_receipts(matrix,receipt,baselines,node):
    p0={(r["study_id"],r["project_id"]):r for r in matrix["pairs"] if r["priority"]=="P0"}
    assert len(p0)==16 and set(p0)==set(BLOCKERS)
    assert set(EXPECTED_PAIRED).issubset(set(p0))
    assert receipt["scope"]=="SUBSYSTEM_OFFLINE_SYNTHETIC_ONLY"
    assert len(receipt["results"])==3
    for rec in receipt["results"]:
        key=(rec["study_id"],rec["project_id"])
        assert EXPECTED_PAIRED[key]==rec["subsystem_verdict"]
        assert rec["full_product_verdict"]=="BLOCKED_FULL_AB"
        assert rec["network_access"]=="DENIED_BWRAP_NETWORK_NAMESPACE"
        assert rec["snapshot_scope"].startswith("pinned Git source file")
        assert rec["real_model_used"] is False and rec["human_expert_oracle"] is False
        a=p0[key]["source_anchor"]
        assert a["file_sha256"]==rec["source_file_sha256"]
        assert len(rec["negative_controls"])>=3
        if key==("exactly-once-limbo","TelegramBot"):
            b=rec["metrics"]["baseline_retry"]
            c=rec["metrics"]["candidate_quarantine"]
            assert b["cases"]==c["cases"]==120
            assert (b["duplicate_cases"],b["lost_delivery_cases"])==(40,0)
            assert (c["duplicate_cases"],c["lost_delivery_cases"])==(0,40)
            assert b["false_local_success"]==c["false_local_success"]==0
        elif key==("agent-risk","agent-config"):
            b=rec["metrics"]["baseline"]
            c=rec["metrics"]["candidate_same_line"]
            assert b["cases"]==c["cases"]==80
            assert (b["false_accepts"],c["false_accepts"])==(20,0)
            assert b["true_accepts"]==c["true_accepts"]==30
            assert c["synthetic_gate_satisfied"] is True
        else:
            b=rec["metrics"]["baseline_rrf"]
            c=rec["metrics"]["candidate_scoped_rrf"]
            assert b["cases"]==c["cases"]==60
            assert b["wrong_source_count"]==30 and c["wrong_source_count"]==0
            assert (b["recall_at_5_total"],c["recall_at_5_total"])==(270,300)
            assert c["synthetic_gate_satisfied"] is True
    assert len(baselines["rows"])==4
    expected={"agent-config":(33,33,0),"agent-skills":(11,11,0),
              "dsh-paper2agent":(115,99,16),"sequential-rca":(None,14,0)}
    for x in baselines["rows"]:
        assert x["network_denied"] is True and x["status"]=="PASS_EXISTING_TESTS"
        assert expected[x["project_id"]]==(x["test_count"],x["passed"],x["skipped"])
        assert x["source_git_sha"]==next(r["source_anchor"]["commit"] for r in p0.values() if r["source_anchor"] and r["project_id"]==x["project_id"])
    assert node["status"]=="PASS_PINNED_BASELINE_SCOPE_TESTS_ONLY"
    assert node["project_id"]=="dsh-team-context"
    assert node["tests_run"]==node["tests_pass"]==3 and node["tests_fail"]==0
    assert node["network_denied"] is True and node["no_measured_treatment"] is True
    assert node["source_anchor"]["commit"]==p0[("agent-mosaic","dsh-team-context")]["source_anchor"]["commit"]
    return p0

def construct():
    matrix,receipt,baselines,node=inputs()
    p0=validate_receipts(matrix,receipt,baselines,node)
    paired={(r["study_id"],r["project_id"]):r for r in receipt["results"]}
    source_baselines={r["project_id"]:r for r in baselines["rows"]}
    source_baselines["dsh-team-context"]=node
    rows=[]
    for key,source in sorted(p0.items()):
        reason,next_action=BLOCKERS[key]
        proof=paired.get(key)
        test=source_baselines.get(key[1])
        row={
            "study_id":key[0],
            "project_id":key[1],
            "priority":"P0",
            "source_pin":source["source_anchor"],
            "protocol_id":source["test_protocol_id"],
            "hypothesis":source["hypothesis"],
            "source_symbol_verified":source["source_anchor"] is not None,
            "subsystem_status":proof["subsystem_verdict"] if proof else "NOT_EXECUTED_NO_PAIRED_TREATMENT",
            "subsystem_trial_scope":proof["limits"] if proof else None,
            "subsystem_receipt":str(RECEIPT.relative_to(ROOT)) if proof else None,
            "source_baseline_test_status":test["status"] if test else "NOT_EXECUTED",
            "source_baseline_receipt":(
                str(NODE.relative_to(ROOT)) if key[1]=="dsh-team-context"
                else str(BASELINES.relative_to(ROOT)) if test else None),
            "full_p0_decision":"BLOCKED_FULL_AB",
            "production_approved":False,
            "target_repo_modified":False,
            "independent_full_task_oracle_available":False,
            "measured_production_gain":False,
            "blocker":reason,
            "next_gate":next_action,
        }
        rows.append(row)
    assert len(rows)==16
    return {
        "date":"2026-11-10",
        "scope":"PINNED_ISOLATED_SOURCE_P0_AB_AND_GATES",
        "status":"COMPLETE_ACCOUNTING_PARTIAL_EXECUTION",
        "source_matrix_sha256":digest(MATRIX),
        "boundary_ab_receipt_sha256":digest(RECEIPT),
        "baseline_test_receipt_sha256":digest(BASELINES),
        "team_scope_receipt_sha256":digest(NODE),
        "original_target_worktrees_modified":False,
        "production_accessed":False,
        "model_or_clinical_oracle_called":False,
        "total_p0":16,
        "paired_subsystem_trials":3,
        "subsystem_safety_passed":2,
        "subsystem_treatment_rejected":1,
        "full_p0_accepted":0,
        "full_p0_blocked":16,
        "existing_unit_baselines_passed_projects":5,
        "existing_unit_baseline_tests_passed":33+11+99+14+3,
        "existing_unit_baseline_tests_skipped":16,
        "rows":rows,
        "interpretation":"No full project-integrated independent held-out A/B completed. Outcomes are source-backed subsystem-only synthetic tests plus archived existing baseline suites and exact blockers. No adoption permission.",
    }

def check(x):
    matrix,receipt,baselines,node=inputs()
    p0=validate_receipts(matrix,receipt,baselines,node)
    assert x["source_matrix_sha256"]==digest(MATRIX)
    assert x["boundary_ab_receipt_sha256"]==digest(RECEIPT)
    assert x["baseline_test_receipt_sha256"]==digest(BASELINES)
    assert x["team_scope_receipt_sha256"]==digest(NODE)
    assert x["scope"]=="PINNED_ISOLATED_SOURCE_P0_AB_AND_GATES"
    assert x["status"]=="COMPLETE_ACCOUNTING_PARTIAL_EXECUTION"
    assert (x["total_p0"],x["paired_subsystem_trials"],x["full_p0_accepted"],x["full_p0_blocked"])==(16,3,0,16)
    assert x["subsystem_safety_passed"]==2 and x["subsystem_treatment_rejected"]==1
    assert x["existing_unit_baselines_passed_projects"]==5
    assert x["existing_unit_baseline_tests_passed"]==160 and x["existing_unit_baseline_tests_skipped"]==16
    assert len(x["rows"])==16 and x["original_target_worktrees_modified"] is False
    assert x["production_accessed"] is False and x["model_or_clinical_oracle_called"] is False
    seen=set()
    for row in x["rows"]:
        key=(row["study_id"],row["project_id"])
        assert key in p0 and key not in seen
        seen.add(key)
        assert row["source_pin"]==p0[key]["source_anchor"]
        assert row["protocol_id"]==p0[key]["test_protocol_id"]
        assert row["hypothesis"]==p0[key]["hypothesis"]
        assert row["full_p0_decision"]=="BLOCKED_FULL_AB"
        assert row["production_approved"] is False
        assert row["target_repo_modified"] is False
        assert row["measured_production_gain"] is False
        assert row["independent_full_task_oracle_available"] is False
        assert (row["blocker"],row["next_gate"])==BLOCKERS[key]
        assert len(row["blocker"])>=90 and len(row["next_gate"])>=70
        if key in EXPECTED_PAIRED:
            assert row["subsystem_status"]==EXPECTED_PAIRED[key]
            assert row["subsystem_receipt"]==str(RECEIPT.relative_to(ROOT))
        else:
            assert row["subsystem_status"]=="NOT_EXECUTED_NO_PAIRED_TREATMENT"
            assert row["subsystem_receipt"] is None
        assert row["source_symbol_verified"] is True
    assert seen==set(p0)

def render(x):
    check(x)
    baseline=read(BASELINES)
    ab=read(RECEIPT)
    by_paired={(v["study_id"],v["project_id"]):v for v in ab["results"]}
    rows=[
        "# P0: frozen-source independent offline trials and remaining evidence gates",
        "",
        "Date: **2026-11-10**. Prior [P0 shortlist](2026-11-09/targeted-fit.md): exact 16 pairs, "
        "all anchored to original project Git objects. No repo code, deployments, "
        "network services, actual databases or personal/clinical data were changed or accessed.",
        "",
        "**Decision:** 0 full-integrated A/B accepted; 16 remain BLOCKED_FULL_AB. "
        "Three source-function subsystem A/B experiments were actually executed: "
        "two passed their limited synthetic safety/recall gate and one treatment was rejected. "
        "The rest have a verified source symbol and an explicit missing full-experiment prerequisite, "
        "not a fictional PASS or NO_FIT.",
        "",
        "## Measured offline comparisons",
        "",
        "| Study / target | Frozen data | Baseline | Candidate | Bounded result / full decision |",
        "| --- | --- | --- | --- | --- |",
    ]
    t=by_paired[("exactly-once-limbo","TelegramBot")]
    b=t["metrics"]["baseline_retry"];c=t["metrics"]["candidate_quarantine"]
    rows.append("| exactly-once-limbo / TelegramBot | 120 mocked sends (40×3) | {} duplicates, {} missing | {} duplicates, {} missing | **REJECT** quarantine: missing delivery; BLOCKED_FULL_AB |".format(
        b["duplicate_cases"],b["lost_delivery_cases"],c["duplicate_cases"],c["lost_delivery_cases"]))
    t=by_paired[("agent-risk","agent-config")]
    b=t["metrics"]["baseline"];c=t["metrics"]["candidate_same_line"]
    rows.append("| agent-risk / agent-config | 80 exact-line synthetic claims | {}/{} false accept | {}/{} false accept; {} true positives | **PASS subsystem** citation quality and micro p95; BLOCKED_FULL_AB |".format(
        b["false_accepts"],b["cases"],c["false_accepts"],c["cases"],c["true_accepts"]))
    t=by_paired[("drag","Wiki_PG")]
    b=t["metrics"]["baseline_rrf"];c=t["metrics"]["candidate_scoped_rrf"]
    rows.append("| drag / Wiki_PG | 60 artificial fused ranking queries | Recall@5 {}/300, {} forbidden docs | Recall@5 {}/300, {} forbidden docs | **PASS subsystem** on pure RRF only; BLOCKED_FULL_AB |".format(
        b["recall_at_5_total"],b["wrong_source_count"],c["recall_at_5_total"],c["wrong_source_count"]))
    rows+=["", "Source excerpts were run by AST extraction from pinned Git archives under "
           "bubblewrap with the network namespace disabled. All numerics above are synthetic "
           "in-process counts, not study-author gains, complete target end-to-end results, "
           "observed production incidents or clinical efficacy. Existing Wiki_PG retrieval "
           "already has host/curated filtering; adversarial RRF lists do not imply those invalid "
           "documents could reach the current full pipeline.",
           "",
           "## Baseline target tests (no new treatment)",
           "",
           "| Repo | Source pin | Offline tests |",
           "| --- | --- | --- |"]
    for r in baseline["rows"]:
        rows.append("| {} | {} | {} passed, {} skipped; {} |".format(
            r["project_id"],r["source_git_sha"][:12],r["passed"],r["skipped"],r["status"]))
    node=read(NODE)
    rows.append("| dsh-team-context | {} | 3 passed, 0 skipped; source scope isolation already tested |".format(
        node["source_anchor"]["commit"][:12]))
    rows+=["","**Baseline total:** {} passed, {} skipped. "
            "These are not 160 comparative scientific successes and do not imply any P0 gain.".format(
                x["existing_unit_baseline_tests_passed"],x["existing_unit_baseline_tests_skipped"]),
            "", "## Decision per all 16 P0 pairs", "",
            "| Study | Target | Source-pinned symbol | Subsystem | Full A/B | Unmet prerequisite |",
            "| --- | --- | --- | --- | --- | --- |"]
    for r in x["rows"]:
        a=r["source_pin"]
        link="[{}:{}]({})".format(a["path"],a["line"],a["url"])
        rows.append("| {} | {} | {} | {} | {} | {} |".format(
            r["study_id"],r["project_id"],link,r["subsystem_status"],
            r["full_p0_decision"],r["blocker"]))
    rows+=["","## Exact next gates", ""]
    for r in x["rows"]:
        rows.append("- **{} / {}:** {}".format(r["study_id"],r["project_id"],r["next_gate"]))
    rows+=["","## Traceability, trade-offs and adoption decision", "",
            "- [Full 16-row JSON receipt](../data/results/research-portfolio/2026-11-10-p0-outcomes.json).",
            "- [Executed source-level A/B results](../data/results/research-portfolio/2026-11-10-p0-boundary-ab.json); "
            "[existing offline suites](../data/results/research-portfolio/2026-11-10-p0-baseline-suites.json); "
            "[team-context baseline](../data/results/research-portfolio/2026-11-10-p0-team-scope-baseline.json).",
            "- Repro: offline source archive + SHA → read-only bwrap sandbox → source function + isolated candidate "
            "→ frozen, prelabelled independent synthetic oracle → all negative controls → receipt. "
            "Use scripts in experiments/research-portfolio/p0-20261110/.",
            "- A strict evidence guard and rank filter add code and some latency but prevent local false accepts. "
            "This trade-off is not measured at deployment scale; p95 in microseconds from synthetic calls is not a service SLA.",
            "- Candidate quarantine reduces duplicate effects but increases losses. Real external exactly-once "
            "delivery requires a validated provider-side idempotency/reconciliation boundary, not a clever local retry loop.",
            "- Source symbol existence (including a prompt() method) is not an implemented adapter. "
            "The final verdict intentionally stays BLOCKED; no production or project change was approved.",""]
    timing_section=["## In-process timing (microseconds, synthetic only)","",
                    "| Study / target | Baseline p50/p95 | Candidate p50/p95 | p95 ratio |",
                    "| --- | --- | --- | --- |"]
    for key, bname, cname in (
        (("exactly-once-limbo","TelegramBot"),"baseline_retry","candidate_quarantine"),
        (("agent-risk","agent-config"),"baseline","candidate_same_line"),
        (("drag","Wiki_PG"),"baseline_rrf","candidate_scoped_rrf"),
    ):
        metrics=by_paired[key]["metrics"]
        b=metrics[bname]["timing"]
        c=metrics[cname]["timing"]
        timing_section.append("| {} / {} | {} / {} | {} / {} | {:.2f}x |".format(
            key[0],key[1],b["p50_us"],b["p95_us"],c["p50_us"],c["p95_us"],
            c["p95_us"]/b["p95_us"]))
    timing_section+=["","These are one-process synthetic microbenchmarks without model or network "
                     "latency, not a production SLA or confidence interval across hosts.",""]
    rows[rows.index("## Baseline target tests (no new treatment)"):rows.index("## Baseline target tests (no new treatment)")]=timing_section
    return "\n".join(rows)

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--generate",action="store_true")
    arg.add_argument("--check",action="store_true")
    args=arg.parse_args()
    assert args.generate != args.check
    if args.generate:
        output=construct()
        check(output)
        OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
        REPORT.write_text(render(output))
    else:
        output=read(OUT)
        check(output)
        assert REPORT.read_text()==render(output),"Stale P0 result report"
        tests=[
            lambda x:x["rows"][0].update(full_p0_decision="ACCEPT"),
            lambda x:x["rows"][0].update(production_approved=True),
            lambda x:x["rows"][0].update(subsystem_status="PASS_FULL_AB"),
            lambda x:x["rows"].pop(),
            lambda x:x.update(full_p0_accepted=1),
            lambda x:x.update(boundary_ab_receipt_sha256="0"*64),
        ]
        for mutate in tests:
            x=copy.deepcopy(output);mutate(x)
            try:check(x)
            except AssertionError:continue
            raise AssertionError("FAIL_OPEN: admitted corrupt P0 result")
    print("P0_OUTCOMES", "GENERATED" if args.generate else "PASS",
          "pairs",len(output["rows"]),
          "paired_offline",output["paired_subsystem_trials"],
          "accepted",output["full_p0_accepted"],
          "blocked",output["full_p0_blocked"],
          "negative_mutations",6)

if __name__=="__main__":
    main()
