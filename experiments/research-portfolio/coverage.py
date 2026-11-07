#!/usr/bin/env python3
"""Conservative coverage audit: 83 sources x 45 registry project IDs.

Entries absent from current_assessments are NOT_EVALUATED, never NO_FIT.
No private project-card body or sensitive data is emitted.
"""
import argparse,collections,hashlib,json,pathlib,re,subprocess,urllib.parse,os
H=pathlib.Path(os.environ.get("RESEARCH_HUB_ROOT",pathlib.Path(__file__).resolve().parents[2]))
R=pathlib.Path(os.environ.get("PROJECT_REGISTRY_ROOT","/var/tmp/project-registry-audit-20261107"))
A=pathlib.Path(os.environ.get("RESEARCH_SOURCE_AUDIT","/var/tmp/research-portfolio-audit-20261107/source-audit.json"))
OUT=pathlib.Path(os.environ.get("RESEARCH_COVERAGE_OUT","/var/tmp/research-portfolio-audit-20261107/coverage.json"))
POS={
 "DOCUMENTED_CANDIDATE","CONDITIONAL_NEEDS_EVIDENCE","RESEARCH_CANDIDATE_TARGET_NOT_MEASURED",
 "ARCHITECTURAL_REFERENCE_CANDIDATE","PROFILE_CANDIDATE_NOT_VALIDATED","SHORTLIST",
 "NEEDS_EVIDENCE","CONDITIONAL_NEEDS_SOURCE_CODE"
}
def split_url_card(url):
 p=urllib.parse.urlparse(url).path
 m=re.search(r"/blob/[^/]+/(projects/.+/PROJECT\.md)$",p)
 return m.group(1) if m else None
def self_test():
 status={"A":"NO_CURRENT_FIT"}
 pairs=[{"project_id":id,"decision":status.get(id,"NOT_EVALUATED")} for id in ["A","B"]]
 assert pairs==[{"project_id":"A","decision":"NO_CURRENT_FIT"},
                {"project_id":"B","decision":"NOT_EVALUATED"}]
 assert len([x for x in pairs if x["decision"]=="NOT_EVALUATED"])==1
 print("COVERAGE_SELF_TEST_PASS",flush=True)
def main():
 self_test()
 e=json.loads((H/"catalog/entities.json").read_text())
 s=json.loads(A.read_text())
 assert s["audited"]==len(e["studies"])==83
 src={x["study_id"]:x for x in s["entries"]}
 rev={x["id"]:x for x in e["reviews"]}
 ass={x["id"]:x for x in e["assessments"]}
 current=collections.defaultdict(dict)
 for pointer in e["current_assessments"]:
  row=ass[pointer["assessment_id"]]
  assert row["study_id"]==pointer["study_id"] and row["project_id"]==pointer["project_id"]
  key=row["project_id"]
  assert key not in current[row["study_id"]]
  current[row["study_id"]][key]=row
 projects=[x["id"] for x in e["projects"]]
 assert len(projects)==len(set(projects))==45
 cardpaths={}
 for x in e["projects"]:
  path=split_url_card(x["registry_card_url"])
  assert path and (R/path).is_file(),x["id"]
  cardpaths[x["id"]]=path
 real_cards=list(R.glob("projects/*/*/PROJECT.md"))
 assert len(real_cards)==45
 result=[]
 count_decisions=collections.Counter()
 positives=collections.Counter()
 missing_literal=[]
 for study in e["studies"]:
  sid=study["id"]
  pointed=rev.get(study["current_review_id"])
  assert pointed and sid in pointed["study_ids"],sid
  pairs=[];pos=[]
  for pid in projects:
   row=current[sid].get(pid)
   if row:
    decision=row["decision"]
    count_decisions[decision]+=1
    cell={"project_id":pid,"decision":decision,"assessment_id":row["id"],
          "evidence":row.get("evidence"),"source_revision":row.get("project_revision"),
          "review_id":row.get("review_id")}
    if decision in POS:
     pos.append({"project_id":pid,"decision":decision,"evidence":row.get("evidence")})
     positives[pid]+=1
     # Just diagnostic: a missing slug doesn't prove a backlink missing.
     text=(R/cardpaths[pid]).read_text().lower()
     if sid.lower() not in text:
      missing_literal.append({"study_id":sid,"project_id":pid})
   else:
    cell={"project_id":pid,"decision":"NOT_EVALUATED"}
    count_decisions["NOT_EVALUATED"]+=1
   pairs.append(cell)
  assert len(pairs)==45
  result.append({
    "study_id":sid,"kind":study["kind"],
    "current_review_id":study["current_review_id"],
    "current_review_access_claim":pointed.get("source_coverage"),
    "automated_source_access":src[sid]["access"],
    "documented_current_project_assessments":len(current[sid]),
    "documented_candidates_total":len(pos),
    "documented_candidate_shortlist_not_new_fits":pos[:3],
    "all_45_projects":pairs
  })
 assert len(result)==83
 assert sum(x["documented_current_project_assessments"] for x in result)==len(e["current_assessments"])==376
 assert count_decisions["NOT_EVALUATED"]==83*45-376
 stats={"studies":83,"projects":45,"pairs":83*45,
        "documented_current_assessments":376,
        "no_documented_decision_pairs":83*45-376,
        "source_access_types":s["summary"],
        "assessment_decisions":dict(count_decisions),
        "projects_with_documented_candidates":len(positives),
        "studies_with_zero_assessments":[x["study_id"] for x in result if x["documented_current_project_assessments"]==0],
        "study_current_review_coverage":dict(collections.Counter(x["current_review_access_claim"] for x in result)),
        "candidate_project_counts":dict(sorted(positives.items())),
        "project_registry_card_count":len(real_cards),
        "possible_missing_literal_backlink_count":len(missing_literal)}
 baseline={
    "review_method":"PRESERVE_EXPLICIT_EXISTING_ASSESSMENTS_ONLY",
    "study_count":83,"project_count":45,"pairs":83*45,
    "registry_sha":"838b86a28fcaa3440eeddbe147b6188e0d177963",
    "hub_sha":"3180d9c46914f2f54d2a21e642b7ec3efffa2b99",
    "counts":stats,
    "caveats":["NOT_EVALUATED is a gap in evidence, not NO_FIT",
               "Old project source revision is a documented historical pin, not automatically a current contract",
               "Shortlist is copied from existing explicit assessments, not newly independently proven fit",
               "Private PROJECT.md source text is never exported to public archive",
               "A literal backlink search cannot detect all semantically equivalent links",
               "Project source code and current integration seams require separate pinned source review",
               "No permissions to implement, deploy or modify source code are inferred from this inventory"],
    "possible_missing_literal_backlinks_preview":missing_literal[:40],
    "studies":result
 }
 OUT.write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+"\n")
 print("COVERAGE_DONE",stats,"output",OUT,"bytes",OUT.stat().st_size,flush=True)
if __name__=="__main__":main()
