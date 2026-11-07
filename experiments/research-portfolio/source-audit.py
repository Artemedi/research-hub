#!/usr/bin/env python3
"""Audit access to ALL public study source URLs, without changing past scientific verdicts.
HTML/PDF structural checks are screening only; not a reading or an independent review.
Never store paper full text, repository source or private project information in the public result.
"""
import argparse,hashlib,json,os,pathlib,re,subprocess,tempfile,time,urllib.parse
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
import requests
from bs4 import BeautifulSoup
H=pathlib.Path(os.environ.get("RESEARCH_HUB_ROOT",pathlib.Path(__file__).resolve().parents[2]))
ROOT=pathlib.Path(os.environ.get("RESEARCH_AUDIT_WORK","/var/tmp/research-portfolio-audit-20261107"))
ROOT.mkdir(mode=0o700,exist_ok=True,parents=True)
def norm(x):return re.sub(r"\s+"," ",x or "").strip()
def h(x):return hashlib.sha256(x).hexdigest()
def html(body):
 s=BeautifulSoup(body,"lxml")
 for bad in s.select("script,style,noscript,nav,footer,aside,header"):bad.decompose()
 doc=s.select_one("article") or s.select_one("main") or s.body or s
 meta=s.find("meta",attrs={"name":"citation_title"}) or s.find("meta",attrs={"property":"og:title"})
 title=(meta.get("content") if meta else None) or (s.find("h1").get_text(" ",strip=True) if s.find("h1") else "")
 headings=[norm(x.get_text(" ",strip=True))[:100] for x in doc.select("h2,h3,h4")][:100]
 txt=norm(doc.get_text(" ",strip=True))
 return {"observed_title":norm(title)[:200],"plain_text_chars":len(txt),"plain_text_sha256":h(txt.encode()),
         "headings_count":len(headings),"headings":headings}
def hint(headings):
 s=" ".join(headings).lower()
 return {"methods_hint":bool(re.search(r"\b(method|methodology|experiment|design|approach)\w*",s)),
         "results_hint":bool(re.search(r"\b(result|finding|evaluation|experiment)\w*",s)),
         "limitations_hint":bool(re.search(r"\b(limitations?|threats to validity|discussion)\b",s))}
def get(url):
 response=requests.get(url,headers={"User-Agent":"ResearchHubPublicSourceAudit/1.0",
                                    "Accept":"text/html,application/pdf;q=0.9,*/*;q=0.5"},
                       timeout=(8,19),stream=True)
 record={"http":response.status_code,"final_url":response.url,
         "mime":(response.headers.get("Content-Type") or "").split(";")[0]}
 if response.status_code!=200:
  response.close();return record,None
 arr=[];n=0
 for chunk in response.iter_content(chunk_size=131072):
  arr.append(chunk);n+=len(chunk)
  if n>12_000_000:
   response.close();return {**record,"error":"BYTE_BUDGET"},None
 response.close()
 return record,b"".join(arr)
def pdf(body):
 if not body.startswith(b"%PDF"):raise ValueError("not_pdf")
 with tempfile.TemporaryDirectory(prefix="research-pdf-",dir=str(ROOT)) as work:
  p=pathlib.Path(work)/"original.pdf";p.write_bytes(body)
  z=subprocess.run(["pdftotext","-layout",str(p),"-"],
                   capture_output=True,text=True,timeout=26)
  if z.returncode:raise ValueError("pdf_no_text")
  plain=norm(z.stdout)
 return {"observed_title":plain[:170],"plain_text_chars":len(plain),
         "plain_text_sha256":h(plain.encode()),"binary_sha256":h(body),
         "headings_count":None,"headings":[]}
def audit(study,review):
 url=study["primary_url"]
 row={"study_id":study["id"],"kind":study["kind"],"url":url,
      "prior_source_coverage":review.get("source_coverage"),
      "prior_review_id":study.get("current_review_id"),
      "screening_only":True}
 match=re.search(r"^https?://(?:www\.)?arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})",url)
 if match:
  paper=match.group(1)
  for part in ("html","pdf"):
   try:
    meta,body=get(f"https://arxiv.org/{part}/{paper}")
    row[part+"_http"]=meta["http"]
    if not body:continue
    if part=="html":
     d=html(body)
     if d["plain_text_chars"]<3500 or d["headings_count"]<2:continue
     row.update(access="FULL_HTML_MACHINE_ACCESSIBLE",verified_url=meta["final_url"],
                source=d,structural_hints=hint(d["headings"]))
     return row
    d=pdf(body)
    if d["plain_text_chars"]<3500:continue
    row.update(access="FULL_PDF_TEXT_EXTRACTABLE",verified_url=meta["final_url"],source=d)
    return row
   except (requests.RequestException,ValueError,subprocess.TimeoutExpired,OSError) as ex:
    row[part+"_error_type"]=type(ex).__name__
  row["access"]="FULL_TEXT_NOT_CONFIRMED_BY_AUTOMATED_PROBE"
  return row
 try:
  m,body=get(url)
  row.update(http=m["http"],verified_url=m["final_url"])
  if body is None:
   row["access"]="SOURCE_UNREACHABLE_OR_TOO_LARGE";return row
  kind=study["kind"]
  host=urllib.parse.urlparse(url).netloc
  if kind=="video":row["access"]="VIDEO_LANDING_ONLY_NO_TRANSCRIPT_VERIFIED"
  elif host=="github.com":
   segments=urllib.parse.urlparse(url).path.strip("/").split("/")
   row["repository_id"]="/".join(segments[:2]) if len(segments)>=2 else None
   row["access"]="GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW"
  elif body.startswith(b"%PDF"):
   d=pdf(body)
   row["source"]=d
   row["access"]="FULL_PDF_TEXT_EXTRACTABLE" if d["plain_text_chars"]>=3500 else "PDF_NOT_FULL_TEXT_CONFIRMED"
  else:
   d=html(body)
   row["source"]=d
   row["access"]="PRIMARY_HTML_TEXT_AVAILABLE" if d["plain_text_chars"]>=3000 else "SHORT_LANDING_NOT_FULL_TEXT_CONFIRMED"
   row["structural_hints"]=hint(d["headings"])
 except (requests.RequestException,ValueError,subprocess.TimeoutExpired,OSError) as ex:
  row["access"]="REQUEST_OR_PARSE_ERROR";row["error_type"]=type(ex).__name__
 return row
def selftest():
 d=html(b'<article><h1>A</h1><h2>Methods</h2><p>Experiment</p><h2>Results</h2><h2>Limitations</h2></article>')
 assert d["headings_count"]==3 and all(hint(d["headings"]).values())
 assert not all(hint(["Abstract","Introduction"]).values())
 print("SELF_TEST_PASS",flush=True)
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--workers",type=int,choices=(1,2,3),default=3)
 ap.add_argument("--out",default=str(ROOT/"source-audit.json"))
 args=ap.parse_args()
 selftest()
 if args.self_test:return
 e=json.loads((H/"catalog/entities.json").read_text())
 reviews={r["id"]:r for r in e["reviews"]}
 out=[];start=time.monotonic()
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  work={pool.submit(audit,s,reviews.get(s.get("current_review_id"),{})):s for s in e["studies"]}
  for i,f in enumerate(as_completed(work),1):
   try:entry=f.result()
   except Exception as ex:
    entry={"study_id":work[f]["id"],"access":"AUDIT_INTERNAL_EXCEPTION","error_type":type(ex).__name__}
   out.append(entry)
   if i%8==0 or i==len(work):print("PROGRESS",i,"/",len(work),entry["study_id"],entry["access"],flush=True)
 out.sort(key=lambda v:v["study_id"])
 result={
  "date":"2026-11-07","hub_baseline_sha":"3180d9c46914f2f54d2a21e642b7ec3efffa2b99",
  "project_registry_baseline_sha":"838b86a28fcaa3440eeddbe147b6188e0d177963",
  "scope":"machine access and structure screening for ALL existing study primary URLs",
  "study_count":len(e["studies"]),"audited":len(out),"elapsed_seconds":round(time.monotonic()-start,2),
  "summary":dict(Counter(v["access"] for v in out)),
  "caveats":["No claim of full scholarly review from machine availability checks",
             "No figures/tables/code or statistical methodology independently inspected by this scanner",
             "Headings indicate possible structure, not evidence quality",
             "Network failures do not invalidate prior full-text reviewed status",
             "No protected source contents, PDFs, repo code or private project descriptions included",
             "All historical reviews, project mapping and evidence statuses untouched"],
  "entries":out}
 p=pathlib.Path(args.out);p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 print("DONE",result["audited"],"TIME",result["elapsed_seconds"],"SUMMARY",result["summary"],flush=True)
if __name__=="__main__":main()
