#!/usr/bin/env python3
"""Minimal research-portfolio DAG dispatcher, offline, reproducible, no LLM calls.

83 studies x 3 local verification stages. 2 physical workers, no private data.
Each stage has exact input evidence and a fail-closed result. This is a scheduler
integration test and audit, NOT an independent scientific verification.
"""
import argparse,collections,concurrent.futures,hashlib,heapq,json,pathlib,threading,time
from typing import Any

PHASES=("access_check","project_matrix_check","review_gate")
def sha(o:Any)->str:return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def state_for_source(src,alternate):
    kind=src["kind"];status=src["access"]
    if status in ("FULL_HTML_MACHINE_ACCESSIBLE","FULL_PDF_TEXT_EXTRACTABLE"):
        return "SOURCE_STRUCTURALLY_READABLE_NOT_SCIENTIFIC_REVIEWED"
    if src["study_id"]=="sequential-diagnosis-language-models" and alternate.get(src["study_id"],{}).get("full_text_accessible"):
        return "LEGAL_AUTHOR_FULL_TEXT_ALTERNATE_AVAILABLE"
    if status=="GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW":
        return "PUBLIC_REPOSITORY_REACHABLE_CODE_REVIEW_PENDING"
    if status in ("PRIMARY_HTML_TEXT_AVAILABLE",):
        return "PUBLIC_ARTICLE_READABLE_STRUCTURE_UNVERIFIED"
    if kind=="video":return "TRANSCRIPT_NOT_VERIFIED"
    return "SOURCE_ACCESS_NEEDS_MANUAL_RESOLUTION"
def verify_matrix(row):
    ids=[x["project_id"] for x in row["all_45_projects"]]
    if len(ids)!=45 or len(set(ids))!=45:return "BLOCKED_MATRIX_BAD_SHAPE"
    known=sum(x["decision"]!="NOT_EVALUATED" for x in row["all_45_projects"])
    if known!=row["documented_current_project_assessments"]:return "BLOCKED_MATRIX_INCONSISTENT"
    return "MATRIX_CONSISTENCY_CONFIRMED_NOT_FIT_APPROVAL"
def final_gate(src,mat,state):
    access=state["access_check"];map_state=state["project_matrix_check"]
    if map_state.startswith("BLOCKED"):return "REWORK_MATRIX"
    if access in ("SOURCE_ACCESS_NEEDS_MANUAL_RESOLUTION","TRANSCRIPT_NOT_VERIFIED"):
        return "REWORK_LEGAL_FULL_SOURCE_OR_TRANSCRIPT"
    if access=="PUBLIC_REPOSITORY_REACHABLE_CODE_REVIEW_PENDING":
        return "REWORK_PIN_AND_TEST_SOURCE_CODE"
    if mat["documented_current_project_assessments"]==0:
        return "REWORK_45_PROJECT_TRIAGE_WITHOUT_INFERRED_FIT"
    if src["prior_source_coverage"] in ("PARTIAL_SOURCE_REVIEW","BOUNDED_CODE_REVIEW","HISTORICAL_REVIEW_RECORDED"):
        return "REWORK_INDEPENDENT_SOURCE_AND_TEST_COVERAGE"
    return "HOLD_PRIOR_REVIEW_UNCHANGED_NO_NEW_DEPLOYMENT"
def evaluate(task,src,mat,alt,finished):
    sid,phase=task
    if phase=="access_check":return state_for_source(src,alt)
    if phase=="project_matrix_check":return verify_matrix(mat)
    assert phase=="review_gate"
    assert "access_check" in finished and "project_matrix_check" in finished
    return final_gate(src,mat,finished)
def run(sources,matrix,alternates,max_workers=2):
    catalog={x["study_id"]:x for x in sources}
    coverage={x["study_id"]:x for x in matrix}
    assert len(catalog)==len(coverage)==83 and set(catalog)==set(coverage)
    alts={x["study_id"]:x for x in alternates}
    work={}   # study_id -> per-stage evidence
    events=[]
    heap=[];seq=0
    for sid in sorted(catalog):
        # Source access problems and absent project assessments get headroom.
        priority=(0 if coverage[sid]["documented_current_project_assessments"]==0 else
                  1 if catalog[sid]["access"] in ("SOURCE_UNREACHABLE_OR_TOO_LARGE",
                                                 "SHORT_LANDING_NOT_FULL_TEXT_CONFIRMED") else 2)
        heapq.heappush(heap,(priority,seq,sid,"access_check"));seq+=1
    active={}
    max_seen=0
    def submit_next(pool):
        nonlocal max_seen,seq
        while heap and len(active)<max_workers:
            priority,n,sid,stage=heapq.heappop(heap)
            # Each new stage's predecessors were completed in main event loop.
            future=pool.submit(evaluate,(sid,stage),catalog[sid],coverage[sid],
                              alts,dict(work.get(sid,{})))
            active[future]=(priority,sid,stage)
            max_seen=max(max_seen,len(active))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        submit_next(pool)
        while active:
            done,_=concurrent.futures.wait(active,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                priority,sid,phase=active.pop(future)
                code=future.result()
                work.setdefault(sid,{})[phase]=code
                events.append({"study_id":sid,"stage":phase,"result":code})
                if phase=="access_check":
                    heapq.heappush(heap,(priority,seq,sid,"project_matrix_check"));seq+=1
                elif phase=="project_matrix_check":
                    heapq.heappush(heap,(priority,seq,sid,"review_gate"));seq+=1
            submit_next(pool)
    assert len(events)==249 and len(work)==83
    assert all(set(x)==set(PHASES) for x in work.values())
    return {"model_calls":0,"network_calls":0,"source_count":len(work),
            "stages":list(PHASES),"task_executions":len(events),
            "physical_workers_limit":max_workers,"peak_physical_workers":max_seen,
            "decision_counts":dict(collections.Counter(x["review_gate"] for x in work.values())),
            "events":events,
            "study_state":[{"study_id":sid,**states} for sid,states in sorted(work.items())]}
def test():
    assert state_for_source({"kind":"paper","access":"SOURCE_UNREACHABLE_OR_TOO_LARGE","study_id":"example"}, {})=="SOURCE_ACCESS_NEEDS_MANUAL_RESOLUTION"
    assert state_for_source({"kind":"paper","access":"FULL_HTML_MACHINE_ACCESSIBLE","study_id":"example"}, {})=="SOURCE_STRUCTURALLY_READABLE_NOT_SCIENTIFIC_REVIEWED"
    test_row={"all_45_projects":[{"project_id":str(i),"decision":"NOT_EVALUATED"} for i in range(45)],
              "documented_current_project_assessments":0}
    assert verify_matrix(test_row)=="MATRIX_CONSISTENCY_CONFIRMED_NOT_FIT_APPROVAL"
    test_row["all_45_projects"][4]["project_id"]=test_row["all_45_projects"][3]["project_id"]
    assert verify_matrix(test_row)=="BLOCKED_MATRIX_BAD_SHAPE"
    assert final_gate({"prior_source_coverage":"FULL_TEXT_REVIEWED"},
                      {"documented_current_project_assessments":1},
                      {"access_check":"SOURCE_STRUCTURALLY_READABLE_NOT_SCIENTIFIC_REVIEWED",
                       "project_matrix_check":"BLOCKED_MATRIX_BAD_SHAPE"})=="REWORK_MATRIX"
    print("CONTROLLER_NEGATIVE_TESTS_PASS")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source")
    ap.add_argument("--coverage")
    ap.add_argument("--alternates")
    ap.add_argument("--out")
    ap.add_argument("--workers",type=int,choices=(1,2),default=2)
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    test()
    if a.self_test:return
    for arg in ("source","coverage","alternates","out"):
        if not getattr(a,arg):ap.error("--"+arg+" is required")
    sources=json.loads(pathlib.Path(a.source).read_text())
    coverage=json.loads(pathlib.Path(a.coverage).read_text())
    alternate=json.loads(pathlib.Path(a.alternates).read_text())
    result=run(sources["entries"],coverage["studies"],alternate["entries"],a.workers)
    result["scope"]="DETERMINISTIC_METADATA_REVIEW_CONTROLLER_NOT_SCIENTIFIC_REPRODUCTION"
    result["registry_sha"]=coverage["registry_sha"]
    result["source_scan_sha256"]=hashlib.sha256(pathlib.Path(a.source).read_bytes()).hexdigest()
    result["coverage_sha256"]=hashlib.sha256(pathlib.Path(a.coverage).read_bytes()).hexdigest()
    result["review_outcome"]="NO_NEW_PRODUCTION_APPROVAL"
    result["limitations"]=[
        "No ZCode model calls were performed in this particular scheduler audit",
        "Source accessibility is not independent full-text methodological reading",
        "Project matrix validates consistency of prior assessments, not every candidate's fit",
        "Deterministic stage scores are gate decisions, not author-reported experiment replications",
        "No changes to original research outcomes or private project source code"
    ]
    p=pathlib.Path(a.out);p.parent.mkdir(exist_ok=True,parents=True)
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("CONTROLLER_83_DONE",result["task_executions"],"stages",
          result["decision_counts"],"peak_workers",result["peak_physical_workers"],
          "file",p,flush=True)
if __name__=="__main__":main()
