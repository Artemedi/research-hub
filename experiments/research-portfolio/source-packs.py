#!/usr/bin/env python3
"""Prepare source-grounded public evidence packs for 31 currently incomplete studies.

Only canonical public paper HTML, official disclosures, and pinned public GitHub
README/source/tests; no private PROJECT.md, repository secrets or credentials.
Packs are local only (0600), and provenance paths/sha256 can be published.
"""
import concurrent.futures, hashlib, json, os, pathlib, re, subprocess, time, urllib.parse
from collections import Counter
import requests
from bs4 import BeautifulSoup

ROOT=pathlib.Path(os.environ.get("SWARM_WORK","/var/tmp/research-portfolio-audit-20261107"))
H=pathlib.Path(os.environ.get("RESEARCH_HUB_ROOT",str(ROOT/"research-hub")))
PACK_DIR=ROOT/"swarm-packs"
PACK_DIR.mkdir(mode=0o700,exist_ok=True,parents=True)
os.chmod(PACK_DIR,0o700)
SOURCES={x["study_id"]:x for x in json.loads((ROOT/"source-audit.json").read_text())["entries"]}
COVERAGE=json.loads((ROOT/"coverage.json").read_text())["studies"]
HEADS={x["study_id"]:x for x in json.loads((ROOT/"source-heads.json").read_text())["entries"]}
ENTITY={x["id"]:x for x in json.loads((H/"catalog/entities.json").read_text())["studies"]}
TARGETS=sorted(
  [x for x in COVERAGE if x["current_review_access_claim"] in
   ("PARTIAL_SOURCE_REVIEW","BOUNDED_CODE_REVIEW","HISTORICAL_REVIEW_RECORDED")
   or x["documented_current_project_assessments"]==0],
  key=lambda x:(0 if x["documented_current_project_assessments"]==0 else
                1 if x["current_review_access_claim"]=="PARTIAL_SOURCE_REVIEW" else 2,x["study_id"])
)
assert len(TARGETS)==31

def sh(body):return hashlib.sha256(body).hexdigest()
def short(s,n=6000):return re.sub(r"\s+"," ",str(s or "")).strip()[:n]
def get(url,timeout=28,limit=10_000_000):
    # Do not follow private/internal redirects; only trusted public domains from catalog.
    response=requests.get(url,headers={"User-Agent":"ResearchHubEvidenceAudit/2026-11-07"},
                          timeout=(8,timeout),stream=True,allow_redirects=True)
    if response.status_code!=200:
        response.close();return {"http":response.status_code,"url":response.url},None
    pieces=[];count=0
    for chunk in response.iter_content(chunk_size=65536):
        count+=len(chunk)
        if count>limit:
            response.close();return {"http":200,"too_large":True,"url":response.url},None
        pieces.append(chunk)
    response.close()
    return {"http":200,"url":response.url},b"".join(pieces)

def plain_html(body):
    soup=BeautifulSoup(body,"lxml")
    for unwanted in soup.select("script,style,noscript,nav,footer,aside,header"):
        unwanted.decompose()
    root=soup.select_one("article") or soup.select_one("main") or soup.body or soup
    heads=[re.sub(r"\s+"," ",e.get_text(" ",strip=True)) for e in root.select("h2,h3,h4")]
    content=re.sub(r"\s+"," ",root.get_text(" ",strip=True)).strip()
    return heads,content

def snippets(text,headings):
    """"Local bounded excerpts with provenance anchors; never declare full scholarly review."""
    parts=[]
    titlepatterns=[
      ("method",r"\b(methodology|methods|method|proposed approach|implementation)\b"),
      ("result",r"\b(results|result|experiments|evaluation|benchmarks)\b"),
      ("limit",r"\b(limitations|threats to validity|limitations and discussion|discussion)\b")
    ]
    for label,pattern in titlepatterns:
        head=next((x for x in headings if re.search(pattern,x,re.I)),None)
        if not head:
            parts.append({"section":label,"heading":None,"excerpt":"","anchor_sha256":None})
            continue
        start=text.find(head)
        excerpt=text[start:start+(1350 if label!="limit" else 1100)] if start>=0 else ""
        parts.append({"section":label,"heading":head[:135],"excerpt":excerpt,
                      "anchor_sha256":sh(excerpt.encode()) if excerpt else None})
    if not any(x["excerpt"] for x in parts):
        excerpt=text[:3900]
        parts.append({"section":"opening","heading":None,"excerpt":excerpt,
                      "anchor_sha256":sh(excerpt.encode())})
    return parts

def gh_tree(repo,rev):
    try:
        p=subprocess.run(["gh","api",f"repos/{repo}/git/trees/{rev}?recursive=1"],
                         text=True,capture_output=True,timeout=22)
        if p.returncode:return [],"TREE_UNAVAILABLE"
        data=json.loads(p.stdout)
        return [x.get("path","") for x in data.get("tree",[]) if x.get("type")=="blob"],None
    except (ValueError,subprocess.TimeoutExpired,OSError):
        return [],"TREE_UNAVAILABLE"
def picks(paths):
    names={p.lower():p for p in paths}
    readme=next((names[x] for x in ("readme.md","readme.rst","readme.txt") if x in names),None)
    files=[]
    if readme:files.append(("README",readme))
    source=[p for p in paths if p.endswith((".py",".ts",".js",".mjs",".go",".rs",".cs",".java"))
             and not any(y in p.lower() for y in ("node_modules/","vendor/","examples/","example/","dist/","build/","__pycache__/","lock","generated","fixture/","test","spec","/test/","/tests/"))
             and not pathlib.PurePosixPath(p).name.startswith(".")]
    tests=[p for p in paths if any(y in p.lower() for y in
           ("test_","/test/","/tests/",".test.",".spec.","_test.")) and
           p.endswith((".py",".ts",".js",".mjs",".go",".rs",".cs"))]
    def quality(p):
        score=0
        if p.startswith(("src/","app/","lib/","internal/","server/","packages/")):score+=5
        if p.lower().endswith(("main.py","main.ts","index.ts","server.py","cli.py")):score+=4
        if p.count("/")<4:score+=2
        if p.count("/")>5:score-=3
        return (-score,len(p),p)
    source.sort(key=quality);tests.sort(key=quality)
    for ty,items in (("SOURCE",source),("TEST",tests)):
        if items:files.append((ty,items[0]))
    return files[:3]

def code_bundle(src,head):
    repo=src.get("repository_id") or head.get("repo")
    if not repo:return {"status":"SOURCE_REPO_IDENTIFIER_MISSING","files":[]}
    # Pin to explicit primary URL revision when given; historical study retains exact version.
    rev=head.get("declared_primary_url_pin") or head.get("observed_public_HEAD")
    if not rev or not re.fullmatch("[0-9a-f]{40}",rev):
        return {"status":"PINNED_REVISION_UNAVAILABLE","repo":repo,"files":[]}
    paths,error=gh_tree(repo,rev)
    docs=[];selected=picks(paths)
    for label,path in selected:
        safe=urllib.parse.quote(path,safe="/")
        url=f"https://raw.githubusercontent.com/{repo}/{rev}/{safe}"
        try:
            meta,body=get(url,timeout=17,limit=300_000)
            if not body:continue
            raw=body.decode("utf-8",errors="replace")
            if not raw.strip() or "\x00" in raw:continue
            excerpts=raw[:2600 if label=="README" else 1800]
            docs.append({
                "type":label,"path":path,"url":url,"full_file_sha256":sh(body),
                "line_count":len(raw.splitlines()),"preview":excerpts,
                "excerpt_sha256":sh(excerpts.encode()),"preview_is_not_full_file":len(excerpts)<len(raw)
            })
        except (requests.RequestException,ValueError,UnicodeError,OSError):pass
    return {"status":"PINNED_CODE_EXCERPTS_AVAILABLE" if any(x["type"]=="SOURCE" for x in docs)
                       else "READABLE_REPO_WITHOUT_VERIFIED_IMPLEMENTATION_EXCERPT",
            "repo":repo,"revision":rev,"current_head":head.get("observed_public_HEAD"),
            "upstream_head_changed_since_explicit_pin":bool(head.get("head_differs_from_explicit_url_pin")),
            "tree_files_count":len(paths),"tree_error":error,
            "files":docs}
def article_bundle(src):
    url=src.get("verified_url") or src["url"]
    if src["kind"]=="paper" and "arxiv.org/html/" in url:
        source_kind="FULL_HTML"
    else:
        source_kind="PUBLIC_TECHNICAL_PAGE"
    try:
        meta,body=get(url)
        if not body:return {"status":"SOURCE_NOT_READABLE","http":meta.get("http"),"full_text_confirmed":False}
        headings,full=plain_html(body)
        if len(full)<2800:return {"status":"SOURCE_TOO_SHORT_OR_LANDING","full_text_confirmed":False,
                                  "observed_chars":len(full)}
        sections=snippets(full,headings)
        return {"status":"SOURCE_TEXT_EXTRACTED","source_kind":source_kind,
                "url":url,"full_text_characters":len(full),"full_text_sha256":sh(full.encode()),
                "headings_count":len(headings),"heading_names":headings[:40],
                "sections":sections,
                "full_text_machine_accessible":True,
                "full_text_scholarly_review_completed":False}
    except (requests.RequestException,ValueError,UnicodeError,OSError) as ex:
        return {"status":"SOURCE_FETCH_EXCEPTION","type":type(ex).__name__,
                "full_text_confirmed":False}
def prepare(x):
    sid=x["study_id"]
    src=SOURCES[sid]
    head=HEADS.get(sid,{})
    study=ENTITY[sid]
    path=H/study["card"]
    # Source card public, limited to descriptive header; existing review is not a new source.
    source_card=short(path.read_text(),780) if path.is_file() else ""
    if src["kind"]=="engineering" and src["access"]=="GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW":
        details=code_bundle(src,head)
    else:
        details=article_bundle(src)
    out={"study_id":sid,"kind":src["kind"],"source_url":src["url"],
         "current_review_claim":x["current_review_access_claim"],
         "existing_assessments_count":x["documented_current_project_assessments"],
         "previous_shortlist":[{"project_id":y["project_id"],"prior_decision":y["decision"]} for y in
                               x["documented_candidate_shortlist_not_new_fits"]],
         "source_card_public_excerpt":source_card,
         "source_evidence":details,
         "created_at":"2026-11-07",
         "new_independent_full_review_completed":False,
         "privacy_note":"public source content only, no private registry content"}
    dest=PACK_DIR/(sid+".json")
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    os.chmod(dest,0o600)
    return {"id":sid,"status":details["status"],"support_count":len(details.get("files",details.get("sections",[]))),
            "source_kind":src["kind"]}

def main():
    os.umask(0o077)
    began=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        tasks={pool.submit(prepare,x):x for x in TARGETS}
        statuses=[]
        for idx,f in enumerate(concurrent.futures.as_completed(tasks),1):
            try:r=f.result()
            except Exception as ex:
                r={"id":tasks[f]["study_id"],"status":"INTERNAL_EXCEPTION","type":type(ex).__name__}
            statuses.append(r)
            print("PACK",idx,"/",len(tasks),r["id"],r["status"],"support",r.get("support_count"),flush=True)
    status={"date":"2026-11-07","count":len(statuses),
            "summary":dict(Counter(x["status"] for x in statuses)),
            "elapsed_s":round(time.monotonic()-began,2),
            "records":sorted(statuses,key=lambda x:x["id"])}
    (ROOT/"swarm-pack-index.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
    assert status["count"]==31
    print("PACKS_DONE",status["summary"],"duration",status["elapsed_s"],flush=True)
if __name__=="__main__":main()
