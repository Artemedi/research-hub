#!/usr/bin/env python3
"""Reproducible adversarial citation-triage A/B against pinned Hyperresearch.

Only tests the mechanical AUTO-PASS tier. Synthetic negative labels are
deliberate contradictions/other-entity/explicit denial; not clinical claims.
"""
import hashlib, importlib.util, json, os, pathlib, re, sqlite3, sys, types, collections

SRC=pathlib.Path(os.environ["HYPER_PIN"])
OUT=pathlib.Path(os.environ.get("OUTPUT",str(pathlib.Path.cwd()/"hyperresearch-citation-ab.json")))
assert (SRC/".git").is_dir()
import subprocess
PIN=subprocess.check_output(["git","-C",str(SRC),"rev-parse","HEAD"],text=True).strip()
assert PIN=="aece65f9307197119629beacf8aeaf8cc80e999a"
F=SRC/"src/hyperresearch/core/citecheck.py"
SOURCE_SHA=hashlib.sha256(F.read_bytes()).hexdigest()
for n in ("hyperresearch","hyperresearch.core","hyperresearch.core.fetcher","hyperresearch.core.patterns","hyperresearch.core.scholar"):
    m=types.ModuleType(n);m.__path__=[];sys.modules[n]=m
sys.modules["hyperresearch.core.fetcher"].existing_live_note_for_url=lambda *a:None
sys.modules["hyperresearch.core.patterns"].WIKI_LINK_RE=re.compile(r"\[\[([^\]\[|]+)(?:\|[^\]\[]+)?\]\](?!\()")
sys.modules["hyperresearch.core.patterns"].mask_code=lambda x:x
sys.modules["hyperresearch.core.scholar"].DOI_RE=re.compile("nevermatching")
sys.modules["hyperresearch.core.scholar"].extract_doi=lambda x:None
spec=importlib.util.spec_from_file_location("hyperresearch.core.citecheck",str(F))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

conn=sqlite3.connect(":memory:")
conn.row_factory=sqlite3.Row
conn.execute("CREATE TABLE claims(note_id text,claim text,quoted_support text,numbers text)")
phrases=[
    "preserves all edits across simultaneous worker sessions",
    "keeps audit records across repeated recovery attempts",
    "rejects unsafe writes during isolated database inspections",
    "checks data provenance before generating public results",
    "restores last checkpoints after unexpected worker crashes"
]
agents=["Alpha","Beta","Gamma","Delta","Omega"]
samples=[]
for i,agent in enumerate(agents):
    for j,phrase in enumerate(phrases):
        note=f"source_{i}_{j}"
        truth=f"The {agent} service always {phrase}."
        other=agents[(i+1)%len(agents)]
        conn.execute("INSERT INTO claims VALUES(?,?,?,?)",(note,truth,"",""))
        examples=[
            ("supported_exact",truth,True),
            ("contradiction_never",f"The {agent} service never {phrase}.",False),
            ("wrong_entity",f"The {other} service always {phrase}.",False),
            ("explicit_denial",f"The report explicitly denies that the {agent} service always {phrase}.",False),
            ("unrelated",f"The unrelated test case makes no claim about the {agent} service at all.",False),
        ]
        for typ,s,expected in examples:
            samples.append({"id":f"{i}-{j}-{typ}","note_id":note,
                 "sentence":s+" [["+note+"]]","expected_supported":expected,
                 "category":typ})
def triage_one(item):
    pairs=[dict(note_id=item["note_id"],sentence=item["sentence"],
                marker=f'[[{item["note_id"]}]]',numbers=[],strong=False)]
    res=module.triage_pairs(pairs,conn)
    assert res["total"]==1
    return res["pairs"][0]["verdict"]
def conservative_gate(item):
    # Independent comparator: no automatic support for non-identical claims.
    normalized=lambda s:re.sub(r"\s+"," ",s.lower()).strip(" .,:;")
    original=conn.execute("select claim from claims where note_id=?",(item["note_id"],)).fetchone()[0]
    candidate=re.sub(r"\[\[[^\]]+\]\]","",item["sentence"])
    return "supported-mechanical" if normalized(candidate)==normalized(original) else "needs-llm"

counts=collections.defaultdict(lambda:collections.Counter())
details=[]
for item in samples:
    got=triage_one(item); strict=conservative_gate(item)
    assert got in ("supported-mechanical","needs-llm")
    counts[item["category"]][got]+=1
    details.append({"id":item["id"],"expected_supported":item["expected_supported"],
                    "original_verdict":got,"conservative_verdict":strict,
                    "unsupported_auto_pass":not item["expected_supported"] and got=="supported-mechanical"})
positives=[r for r in details if r["expected_supported"]]
negatives=[r for r in details if not r["expected_supported"]]
n_fp=sum(r["unsupported_auto_pass"] for r in negatives)
n_tp=sum(r["original_verdict"]=="supported-mechanical" for r in positives)
n_fp_conservative=sum(not r["expected_supported"] and r["conservative_verdict"]=="supported-mechanical" for r in details)
n_tp_conservative=sum(r["expected_supported"] and r["conservative_verdict"]=="supported-mechanical" for r in details)
assert len(samples)==125 and len(positives)==25 and len(negatives)==100
assert n_tp==25 and n_fp>0 and n_fp_conservative==0 and n_tp_conservative==25
summary={
    "date":"2026-11-07","study":"hyperresearch","source_repo":"jordan-gibbs/hyperresearch",
    "pinned_commit":PIN,"source_file":"src/hyperresearch/core/citecheck.py","source_sha256":SOURCE_SHA,
    "experiment":"125 synthetic citation/note pairs using actual upstream triage_pairs",
    "balanced_base_prompts":25,"cases":len(details),"supported_ground_truth":25,
    "unsupported_ground_truth":100,
    "original_mechanical_true_positive":n_tp,
    "original_unsupported_auto_pass":n_fp,
    "original_false_auto_pass_rate_of_synthetic_unsupported":round(n_fp/100,4),
    "conservative_exact_only_true_positive":n_tp_conservative,
    "conservative_exact_only_unsupported_auto_pass":n_fp_conservative,
    "per_class":{k:dict(v) for k,v in sorted(counts.items())},
    "test_construction":"5 actors x 5 clauses; exact, never, other-entity, explicit-denial, unrelated",
    "limits":["Synthetic deliberately adversarial input, not a natural-citation prevalence estimate",
       "Strict comparator only changes the mechanical auto-pass decision; it requires downstream LLM review of non-exact paraphrases",
       "Tested isolated triage_pairs() loaded from pinned source with stubbed external dependencies",
       "No production Hyperresearch or project integration used, no model calls, no score of downstream LLM classifier"],
    "fixtures":details
}
OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
print("HYPERRESEARCH_AB_PASS", "cases",len(details),"unsupported_auto_pass",n_fp,
      "true_positive",n_tp,"conservative_fp",n_fp_conservative,
      "source_sha256",SOURCE_SHA)
print("CLASS_COUNTS",json.dumps(summary["per_class"],ensure_ascii=False))
