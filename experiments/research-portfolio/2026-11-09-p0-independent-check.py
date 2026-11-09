#!/usr/bin/env python3
"""Independent, deterministic numeric oracle for five P0 receipts + 16 gates.

Unlike p0-adjudicate.py this checker does not import the generator and
derives each case label by its own rule, including negative mutation tests.
It cannot independently rerun a user's Git source from GitHub CI and does
not constitute a separate model/clinical evaluation.
"""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"data/results/research-portfolio"
MANIFEST=ROOT/"data/project-fit/portfolio/2026-11-09-targeted-fit.json"
LEDGER=DATA/"2026-11-09-p0-experiment-ledger.json"
RESULT=DATA/"2026-11-09-p0-independent-check.json"

RAW={
 "quote":"2026-11-09-p0-agent-risk-agent-config.json",
 "delivery":"2026-11-09-p0-exactly-once-limbo-telegram.json",
 "retrieval":"2026-11-09-p0-agent-mosaic-team-context.json",
 "sql":"2026-11-09-p0-mcp-toolbox-pg.json",
 "source_pin":"2026-11-09-p0-paper2project-symlink.json",
}

def read(path):return json.loads(path.read_text())
def hash_file(path):return sha256(path.read_bytes()).hexdigest()

def verify_quote(d):
    assert d["pair"]=="agent-risk/agent-config"
    rows=d["records"]
    assert len(rows)==80 and len({r["id"] for r in rows})==80
    categories=Counter(r["category"] for r in rows)
    assert categories=={"valid":30,"wrong_line":18,"missing_quote":12,
                        "missing_source":10,"bad_line":7,"injected_quote":3}
    def independently_ground(row):
        if row["claimed_file"]!="good.py":return False
        lines=row["text"].splitlines()
        n=row["claimed_line"]
        if type(n)is not int or not 1<=n<=len(lines):return False
        quote=" ".join(row["quote"].split())
        return bool(quote) and quote in " ".join(lines[n-1].split())
    for r in rows:assert r["gold_valid"]==independently_ground(r)
    def confusion(name):
        predict=name+"_accept"
        return {
          "true_positive":sum(r["gold_valid"] and r[predict] for r in rows),
          "false_positive":sum(not r["gold_valid"] and r[predict] for r in rows),
          "false_negative":sum(r["gold_valid"] and not r[predict] for r in rows),
          "true_negative":sum(not r["gold_valid"] and not r[predict] for r in rows),
        }
    assert confusion("baseline")==d["baseline"]
    assert confusion("candidate")==d["candidate"]
    assert d["baseline"]=={"true_positive":30,"false_positive":18,"false_negative":0,"true_negative":32}
    assert d["candidate"]=={"true_positive":30,"false_positive":0,"false_negative":0,"true_negative":50}
    assert d["timing"]["samples_per_arm"]==1600
    assert d["timing"]["p95_candidate_ns"]<=d["timing"]["p95_baseline_ns"]*1.25
    return {"count":len(rows),"fp_original":18,"fp_candidate":0,
            "true_accepted_each_arm":30}

def verify_delivery(d):
    assert d["pair"]=="exactly-once-limbo/TelegramBot"
    rows=d["records"]
    assert len(rows)==120 and len({r["id"] for r in rows})==120
    ct=Counter(r["case"] for r in rows)
    assert ct=={z:30 for z in ("ack_normal","ack_lost_after_effect",
                             "error_before_effect","crash_after_ack_before_state")}
    expected={
      "ack_normal":(1,1,True,True,False),
      "ack_lost_after_effect":(2,1,True,False,True),
      "error_before_effect":(1,0,True,False,True),
      "crash_after_ack_before_state":(2,1,True,False,True),
    }
    for r in rows:
        baseline_remote,candidate_remote,baseline_success,candidate_success,pending=expected[r["case"]]
        assert r["baseline"]["remote_commits"]==baseline_remote
        assert r["candidate"]["remote_commits"]==candidate_remote
        assert r["baseline"]["recorded_success"] is baseline_success
        assert r["candidate"]["recorded_success"] is candidate_success
        assert r["candidate"]["unknown_pending"] is pending
        assert r["baseline"]["duplicate_remote_effect"] is (baseline_remote>1)
        assert r["candidate"]["duplicate_remote_effect"] is False
    def agg(arm):
        return {
            "total":len(rows),
            "duplicate_remote_effects":sum(r[arm]["duplicate_remote_effect"] for r in rows),
            "remote_commits":sum(r[arm]["remote_commits"] for r in rows),
            "recorded_success":sum(r[arm]["recorded_success"] for r in rows),
            "unknown_pending":sum(r[arm]["unknown_pending"] for r in rows),
            "false_recorded_success":sum(r[arm]["recorded_success"] and r[arm]["remote_commits"]==0 for r in rows),
        }
    assert agg("baseline")==d["baseline"]
    assert agg("candidate")==d["candidate"]
    assert d["baseline"]["duplicate_remote_effects"]==60
    assert d["candidate"]["duplicate_remote_effects"]==0
    assert d["candidate"]["unknown_pending"]==90
    assert d["candidate"]["recorded_success"]==30
    return {"count":len(rows),"duplicate_baseline":60,"duplicate_candidate":0,
            "candidate_undetermined":90}

def verify_retrieval(d):
    assert d["pair"]=="agent-mosaic/dsh-team-context"
    rows=d["records"]
    assert len(rows)==60 and {r["id"] for r in rows}==set(range(60))
    assert Counter(r["ood"] for r in rows)=={False:45,True:15}
    for r in rows:
        assert r["ood"] is (r["id"]>=45)
        assert r["gold_id"] is None if r["ood"] else isinstance(r["gold_id"],str)
        assert r["approved_count"]==(0 if r["ood"] else 3)
        assert r["baseline"]=={"invalid":5,"correct":0,"returned":5}
        assert r["candidate"]=={"invalid":0,"correct":1,"returned":0 if r["ood"] else 3}
    def agg(arm):
        return {"cases":len(rows),
                "correct_or_abstain":sum(r[arm]["correct"] for r in rows),
                "wrong_source_count":sum(r[arm]["invalid"] for r in rows),
                "ood_abstained":sum(r[arm]["correct"] for r in rows if r["ood"])}
    assert agg("baseline")==d["baseline"]
    assert agg("candidate")==d["candidate"]
    assert d["candidate"]["wrong_source_count"]==0
    assert d["timing"]["p95_candidate_ns"]>d["timing"]["p95_baseline_ns"]*1.25
    return {"count":len(rows),"wrong_source_original":300,
            "wrong_source_candidate":0,"candidate_failed_p95":True}

def verify_sql(d):
    assert d["pair"]=="mcp-toolbox-postgres/Wiki_PG"
    rows=d["records"]
    assert len(rows)==48 and {r["id"] for r in rows}==set(range(48))
    expected_status={
        "bad_parameter":"invalid_parameter",
        "bad_date":"invalid_snapshot_date",
        "missing_host":"no_snapshot",
        "wrong_port":"no_instance",
        "invalid_snapshot":"invalid_snapshot",
        "no_snapshot":"no_snapshot",
        "no_setting":"not_found",
        "ambiguous_snapshot":"ambiguous_snapshot",
    }
    assert Counter(r["category"] for r in rows)==({"valid":40}|{k:1 for k in expected_status})
    for r in rows:
        if r["category"]=="valid":
            assert r["gold_status"]=="ok"
            assert r["gold_setting"]==str(200+7*r["id"])
            assert r["wrapper_source_present"]
        else:
            assert r["gold_status"]==expected_status[r["category"]]
            assert r["gold_setting"] is None
        assert r["baseline_status"]==r["wrapper_status"]==r["gold_status"]
        assert r["baseline_value"]==r["wrapper_value"]==r["gold_setting"]
        assert r["same_value"] is True
    assert d["baseline"]==d["candidate"]=={"valid_correct":40,"invalid_non_ok":8}
    assert d["timing"]["p95_candidate_ns"]>d["timing"]["p95_baseline_ns"]
    return {"count":len(rows),"identical_values":48,"new_accuracy_gain":0}

def verify_source_pin(d):
    assert d["pair"]=="paper2agent/dsh-paper2agent"
    rows=d["records"]
    assert len(rows)==42 and len({r["id"] for r in rows})==42
    assert Counter(r["category"] for r in rows)=={
        "valid":30,"missing":3,"outside":3,"symlink":3,"tamper":3}
    for r in rows:
        assert r["gold_accept"] is (r["category"]=="valid")
        if r["category"]=="valid":
            assert r["baseline_accept"] and r["candidate_accept"]
        elif r["category"]=="symlink":
            assert r["baseline_accept"] is True and r["candidate_accept"] is False
        else:
            assert not r["baseline_accept"] and not r["candidate_accept"]
    def aggregate(arm):
        k=arm+"_accept"
        return {
          "valid_accepted":sum(r["category"]=="valid" and r[k] for r in rows),
          "invalid_rejected":sum(r["category"]!="valid" and not r[k] for r in rows),
          "invalid_accepted":sum(r["category"]!="valid" and r[k] for r in rows),
          "symlink_accepted":sum(r["category"]=="symlink" and r[k] for r in rows),
          "snapshots_stable_after_external_edit":30,
        }
    assert aggregate("baseline")==d["baseline"]
    assert aggregate("candidate")==d["candidate"]
    assert d["baseline"]["invalid_rejected"]==9
    assert d["candidate"]["invalid_rejected"]==12
    patch=ROOT/"experiments/research-portfolio/2026-11-09-p0-paper2project-symlink-candidate.patch"
    assert d["candidate_patch_sha256"]==hash_file(patch)
    assert "candidate.is_symlink()" in patch.read_text()
    return {"count":len(rows),"source_symlink_false_allows":3,
            "candidate_symlink_false_allows":0}

VALIDATORS={"quote":verify_quote,"delivery":verify_delivery,
            "retrieval":verify_retrieval,"sql":verify_sql,
            "source_pin":verify_source_pin}

def receipts_check(objects,anchors):
    results={}
    for key,filename in RAW.items():
        data=objects[key]
        row=anchors[data["pair"]]
        assert data["source_git_sha"]==row["commit"],("wrong pinned source",key)
        assert data["source_file"]==row["path"]
        assert data["source_file_sha256"]==row["file_sha256"]
        results[key]=VALIDATORS[key](data)
    return results

def ledger_check(ledger,objects):
    matrix=read(MANIFEST)
    p0={(r["study_id"]+"/"+r["project_id"]):r for r in matrix["pairs"] if r["priority"]=="P0"}
    assert len(p0)==16
    anchors={key:row["source_anchor"] for key,row in p0.items()}
    measured=receipts_check(objects,anchors)
    rows=ledger["rows"]
    assert len(rows)==16 and {r["pair_id"] for r in rows}==set(p0)
    assert ledger["counts"]=={
      "total":16,"measured_synthetic_ab":5,"blocked_before_experiment":11,
      "conditionally_promising":2,"reject_current_prototype":2,
      "no_incremental_gain":1,"approved_for_production":0}
    assert ledger["candidate_matrix_sha256"]==hash_file(MANIFEST)
    assert ledger["source_suites_receipt_sha256"]==hash_file(DATA/"2026-11-09-p0-target-snapshot-tests.json")
    assert ledger["candidate_suites_receipt_sha256"]==hash_file(DATA/"2026-11-09-p0-candidate-unit-suites.json")
    expected_status={
      "agent-risk/agent-config":("PILOT_PASS_CONDITIONAL","RESEARCH_CANDIDATE_NOT_APPROVED","quote"),
      "paper2agent/dsh-paper2agent":("PILOT_PASS_CONDITIONAL","RESEARCH_CANDIDATE_NOT_APPROVED","source_pin"),
      "agent-mosaic/dsh-team-context":("PILOT_FAIL_COST","REJECT_CURRENT_PROTOTYPE","retrieval"),
      "exactly-once-limbo/TelegramBot":("PILOT_FAIL_LIVENESS","REJECT_CURRENT_PROTOTYPE","delivery"),
      "mcp-toolbox-postgres/Wiki_PG":("PILOT_NO_INCREMENTAL_GAIN","NO_CHANGE","sql"),
    }
    for row in rows:
        pair=row["pair_id"]
        assert not row["production_approval"] and not row["target_repo_changed"]
        assert row["source_anchor"]==anchors[pair]
        assert row["protocol_id"]==p0[pair]["test_protocol_id"]
        assert row["owner_gate"]=="SOURCE_REVIEW_AND_OWNER_SIGNOFF_REQUIRED"
        assert len(row["next_gate"])>=60
        if pair in expected_status:
            status,decision,raw=expected_status[pair]
            assert row["execution_status"]==status and row["adoption_decision"]==decision
            assert row["experiment_executed"] is True
            evidence={r["path"]:r["sha256"] for r in row["evidence"]}
            filename=RAW[raw]
            assert evidence["data/results/research-portfolio/"+filename]==hash_file(DATA/filename)
            assert row["baseline"]==objects[raw]["baseline"]
            assert row["candidate"]==objects[raw]["candidate"]
            ratio=round(objects[raw]["timing"]["p95_candidate_ns"]/objects[raw]["timing"]["p95_baseline_ns"],4)
            assert row["latency_ratio_p95"]==ratio
            assert row["independent_oracle_kind"]=="DETERMINISTIC_SYNTHETIC_LABELS_ONLY"
        else:
            assert row["adoption_decision"]=="BLOCKED"
            assert row["experiment_executed"] is False
            assert row["candidate"] is None and row["baseline"] is None
            assert row["evidence"]==[] and row["latency_ratio_p95"] is None
            assert row["independent_oracle_kind"]=="UNAVAILABLE"
            assert row["execution_status"].startswith("BLOCKED_")
            assert len(row["blocker"])>80
    original_suites=read(DATA/"2026-11-09-p0-target-snapshot-tests.json")
    candidate_suites=read(DATA/"2026-11-09-p0-candidate-unit-suites.json")
    assert len(original_suites["tests"])==6
    assert all(t["returncode"]==0 and t["network"]=="bubblewrap unshare-net" for t in original_suites["tests"])
    suites={r["id"]:r for r in candidate_suites["results"]}
    assert suites["agent-config-line-guard"]["tests_run"]==10
    assert suites["agent-config-line-guard"]["tests_passed"]==10
    assert suites["paper2project-symlink-guard"]["tests_run"]==80
    assert suites["paper2project-symlink-guard"]["tests_passed"]==65
    assert suites["paper2project-symlink-guard"]["tests_skipped"]==15
    assert all(r["returncode"]==0 for r in candidate_suites["results"])
    return {"source_receipts":measured,"measured_pair_count":5,
            "blocked_pair_count":11,"source_suite_count":6,
            "candidate_suite_count":2}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--generate",action="store_true")
    parser.add_argument("--check",action="store_true")
    a=parser.parse_args()
    assert a.generate != a.check
    objects={key:read(DATA/filename) for key,filename in RAW.items()}
    ledger=read(LEDGER)
    result=ledger_check(ledger,objects)
    # Negative mutation controls are validated on *copies* and must fail closed.
    probes=[
      lambda d,o: o["quote"]["records"][0].update(gold_valid=not o["quote"]["records"][0]["gold_valid"]),
      lambda d,o: o["delivery"]["records"][1]["candidate"].update(remote_commits=99),
      lambda d,o: o["retrieval"]["candidate"].update(wrong_source_count=9),
      lambda d,o: o["sql"]["records"][0].update(wrapper_value="999999"),
      lambda d,o: o["source_pin"]["records"][30].update(candidate_accept=True),
      lambda d,o: o["quote"].update(source_git_sha="0"*40),
      lambda d,o: d["rows"][0].update(production_approval=True),
      lambda d,o: d["rows"].pop(),
    ]
    caught=0
    for probe in probes:
        copy_ledger=deepcopy(ledger);copy_objects=deepcopy(objects)
        probe(copy_ledger,copy_objects)
        try:ledger_check(copy_ledger,copy_objects)
        except (AssertionError,KeyError):
            caught+=1
        else:
            raise AssertionError("Failed closed-loop corruption probe")
    assert caught==8
    summary={"status":"PASS_INDEPENDENT_SYNTHETIC_ORACLE",
             "result":result,
             "negative_mutations_rejected":caught,
             "negative_mutations_total":len(probes),
             "limits":"Static receipt verification on CI; original isolated source can only be rerun on authorized pinned Git snapshots, and is not a second full scientific/clinical review."}
    expected=json.dumps(summary,indent=2,ensure_ascii=False)+"\n"
    if a.generate:RESULT.write_text(expected)
    else:assert RESULT.read_text()==expected,"Stale independent oracle receipt"
    print("P0_INDEPENDENT_ORACLE",summary["status"],caught,"mutations rejected",
          len(ledger["rows"]),"P0 pairs")

if __name__=="__main__":main()
