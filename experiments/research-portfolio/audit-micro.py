#!/usr/bin/env python3
"""Offline independent provenance/anchor audit of public ZCode excerpt screening.

This checks evidence integrity and response scope, not whether the study's
methodology/results are valid or whether the target project will improve.
"""
import argparse,collections,hashlib,json,pathlib

def sha(t):return hashlib.sha256(t.encode()).hexdigest()
def evidence(pack):
    result={}
    source=pack["source_evidence"]
    for x in source.get("files",[]):
        key=x["type"]+":"+x["path"]
        expected=x.get("excerpt_sha256")
        value=x.get("preview","")
        result[key]=(bool(expected) and sha(value)==expected)
    for x in source.get("sections",[]):
        if not x.get("excerpt"):continue
        key=x["section"]+":"+str(x.get("heading") or "OPENING")
        expected=x.get("anchor_sha256")
        result[key]=(bool(expected) and sha(x["excerpt"])==expected)
    return result
def check(pack,model):
    anchors=evidence(pack)
    declared=model.get("anchors",[])
    answer=model.get("answer") or {}
    active=model.get("model_status")=="SCHEMA_PASS"
    correct_id=answer.get("id")==pack["study_id"] if active else None
    anchor_ok=(answer.get("anchor") in anchors or
               (answer.get("anchor")=="" and answer.get("claim")=="NEEDS_MORE_SOURCE")) if active else None
    exact_scope=answer.get("validation")=="SCREENING_ONLY" if active else None
    # Source-pack collector may have more than the three fragments sent to the model.
    provided=set(declared)
    prompt_anchor_ok=answer.get("anchor") in provided or answer.get("anchor")=="" if active else None
    integrity_ok=all(anchors.values())
    return {"id":pack["study_id"],"source_gate":pack["source_evidence"]["status"],
            "model_status":model.get("model_status","NOT_ATTEMPTED"),
            "source_excerpt_digests_consistent":integrity_ok,
            "source_fragment_count":len(anchors),
            "model_report_matches_study_id":correct_id,
            "model_answer_cites_known_source_anchor":anchor_ok,
            "model_anchor_sent_in_prompt":prompt_anchor_ok,
            "model_scope_screening_only":exact_scope,
            "scientific_claim_semantically_verified":False,
            "independent_author_experiment_replication":False,
            "project_fit_approved":False}
def self_test():
    p={"study_id":"X","source_evidence":{"status":"SOURCE_TEXT_EXTRACTED",
       "sections":[{"section":"method","heading":"Methods","excerpt":"abc",
                    "anchor_sha256":sha("abc")}],"files":[]}}
    r={"anchors":["method:Methods"],"model_status":"SCHEMA_PASS",
       "answer":{"id":"X","anchor":"method:Methods","claim":"abc","validation":"SCREENING_ONLY"}}
    assert check(p,r)["source_excerpt_digests_consistent"]
    assert check(p,r)["model_anchor_sent_in_prompt"]
    p["source_evidence"]["sections"][0]["excerpt"]="corrupted"
    assert not check(p,r)["source_excerpt_digests_consistent"]
    r["answer"]["anchor"]="invented"
    assert not check(p,r)["model_answer_cites_known_source_anchor"]
    print("PROVENANCE_NEGATIVE_TESTS_PASS")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--work",type=pathlib.Path)
    ap.add_argument("--out",type=pathlib.Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    self_test()
    if args.self_test:return
    if not args.work or not args.out:ap.error("--work and --out required")
    packs={p.stem:json.loads(p.read_text()) for p in (args.work/"swarm-packs").glob("*.json")}
    assert len(packs)==31
    result=json.loads((args.work/"micro-swarm-results.json").read_text())
    micro={x["id"]:x for x in result["studies"]}
    rows=[check(pack,micro.get(sid,{})) for sid,pack in sorted(packs.items())]
    summary={
       "source_digest_matches":sum(x["source_excerpt_digests_consistent"] for x in rows),
       "model_schema_complete":sum(x["model_status"]=="SCHEMA_PASS" for x in rows),
       "model_anchor_valid":sum(x["model_answer_cites_known_source_anchor"] is True for x in rows),
       "provider_or_source_blocked":sum(x["model_status"]!="SCHEMA_PASS" for x in rows)
    }
    assert summary["source_digest_matches"]==31
    assert summary["model_anchor_valid"]==summary["model_schema_complete"]
    out={"date":"2026-11-07","scope":"offline SHA and schema audit, NOT semantic source validation",
         "sources":31,"summary":summary,
         "limitations":["Evidence excerpt SHA can be internally consistent yet source claims false",
           "A model citing one correct anchor is not a full-text review",
           "Pinned public code snippets not executed and no independent benchmark reproduced",
           "No production approval or new project FIT granted"],"studies":rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print("PROVENANCE_AUDIT_PASS",summary)
if __name__=="__main__":main()
