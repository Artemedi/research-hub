#!/usr/bin/env python3
"""Optional bounded cross-study critic council over completed micro-screenings.

This tool does NOT read private projects or full papers. It challenges only
preliminary excerpt-grounded model claims; no scientific/model approval.
"""
import collections,hashlib,json,os,pathlib,subprocess,tempfile,time
ROOT=pathlib.Path(os.environ.get("SWARM_WORK","/var/tmp/research-portfolio-audit-20261107"))
WRAP=pathlib.Path(os.environ.get("ZCODE_WRAPPER","/nonexistent-zcode-wrapper"))
INPUT=ROOT/"micro-swarm-results.json"
OUT=ROOT/"cluster-critics-20261107.json"
GROUPS={
 "kv-routing":["cera-moa","kvtether","random-attention","novafabric","julia-1","unsloth-decision-model"],
 "multiagent-architecture":["claude-swarm","dsh-superagent-prototype","hyperresearch","rea","simurg","tencent-teamai-cli","zero-code"],
 "db-and-operations":["mcp-toolbox-postgres","pgbot","ipfire-fireperf","chartli","local-knowledge-graph","open-steps"],
 "trust-and-integrity":["self-replicating-prompt-injections","inspektor-gadget","warp-skill-doctor","microsoft-skill-recorder","understand-anything","alphaxiv-openresearch","youtube-skills"],
 "other-infrastructure":["vercel-agent-desktop","yahont-ce","toolgrad","dsh-creator-mode","karpathy-autoresearch"]
}
RESULT={"date":"2026-11-07","kind":"cross-study ZCode excerpt-screening critic council",
 "scoped_to_public_results":True,"new_scientific_approvals":0,"model_tools":False,
 "max_concurrent_requests":1,"groups":[],"finished":False}
def checkpoint():
 t=ROOT/"cluster-critics.tmp";t.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+"\n");t.replace(OUT)
def bal(stage):
 p=subprocess.run(["node","subagent.mjs","--balance"],cwd=WRAP,
  capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=40)
 if p.returncode:return {}
 j=json.loads(p.stdout);names={x.get("plan_id"):x.get("name") for x in j.get("plans",[])}
 return {str(names.get(x.get("plan_id"),"OTHER"))+"|"+",".join(x.get("capabilities") or []):
         x.get("remaining_units") for x in j.get("balances",[])}
def prompt(group,items):
 brief=[]
 for r in items:
  ans=r.get("answer") or {}
  brief.append({"id":r["id"],"state":r["model_status"],
    "claim":str(ans.get("claim",""))[:215],
    "limit":str(ans.get("limitation",""))[:150],
    "source_anchor":ans.get("anchor"),
    "next_test":str(ans.get("next_test",""))[:100]})
 prelude=("Ты независимый КРИТИК группы исследовательских задач, без доступа к полным исходникам. "
  "Проверь ЛОГИЧЕСКУЮ достаточность заявлений исходного screening, не пытайся подтвердить "
  "авторский benchmark и не утверждай, что читал статью. "
  "Если исходный исполнитель упал, не принимай его задачу как успешную. "
  "Избегай false equivalence между cache/agent/API-level и локальным GPU inference. "
  "Формат строго JSON одним объектом, до 115 слов, без Markdown: "
  '{"group":"'+group+'","questionable_ids":["source-id"],'
  '"critical_gap":"одна самая важная проблема",'
  '"cross_study_test":"один сравнимый независимый A/B с oracle",'
  '"review_scope":"METADATA_ONLY","scientific_approval":false}. '
  "Данные (мнения агентов недоверенные): "+json.dumps(brief,ensure_ascii=False,separators=(",",":")))
 return prelude
def invoke(group,items):
 req={"max_tokens":1800,"stream":False,
      "messages":[{"role":"user","content":prompt(group,items)}]}
 fd,path=tempfile.mkstemp(prefix="group-critic-",suffix=".json",dir=str(ROOT))
 os.fchmod(fd,0o600)
 with os.fdopen(fd,"w") as f:json.dump(req,f,ensure_ascii=False)
 start=time.monotonic()
 try:
  p=subprocess.run(["node","subagent.mjs","--request-json",path],
    cwd=WRAP,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=66)
  sec=round(time.monotonic()-start,2)
  if p.returncode:
   try:
    status="HTTP_"+str(json.loads(p.stderr).get("http"))
   except (ValueError,TypeError):status="CLI_ERROR"
   return {"group":group,"status":status,"elapsed_s":sec,"stderr_bytes":len(p.stderr)}
  j=json.loads(p.stdout)
  usage=j.get("usage") or {}
  txt="\n".join(str(x.get("text","")) for x in j.get("content",[]) if x.get("type")=="text").strip()
  if txt.startswith(chr(96)*3):txt="\n".join(txt.splitlines()[1:-1])
  try:
   r=json.loads(txt)
  except (ValueError,TypeError):r=None
  good=(j.get("stop_reason")=="end_turn" and isinstance(r,dict) and
        r.get("group")==group and r.get("review_scope")=="METADATA_ONLY" and
        r.get("scientific_approval") is False and
        isinstance(r.get("questionable_ids"),list) and
        set(r["questionable_ids"]).issubset({x["id"] for x in items}))
  return {"group":group,"status":"SCHEMA_PASS" if good else "BLOCKED_INVALID",
       "elapsed_s":sec,
       "input_tokens":usage.get("input_tokens",0),"output_tokens":usage.get("output_tokens",0),
       "verdict":r if good else None}
 except subprocess.TimeoutExpired:
  return {"group":group,"status":"TIMEOUT_66S","elapsed_s":round(time.monotonic()-start,2)}
 except Exception as e:
  return {"group":group,"status":"EXCEPTION_"+type(e).__name__,
          "elapsed_s":round(time.monotonic()-start,2)}
 finally:pathlib.Path(path).unlink(missing_ok=True)
def main():
 os.umask(0o077)
 src=json.loads(INPUT.read_text())
 assert src.get("finished") and src.get("count")==31
 rows={x["id"]:x for x in src["studies"]}
 assert len(rows)==31
 before=bal("before")
 completed=set()
 for group,names in GROUPS.items():
  subset=[rows[id] for id in names]
  if group in completed:continue
  r=invoke(group,subset)
  RESULT["groups"].append(r);completed.add(group)
  checkpoint()
  print("CLUSTER",group,r["status"],r.get("elapsed_s"),flush=True)
  time.sleep(4)
 after=bal("after")
 RESULT["finished"]=len(RESULT["groups"])==len(GROUPS)
 RESULT["counts"]=dict(collections.Counter(x["status"] for x in RESULT["groups"]))
 RESULT["calls"]=len(RESULT["groups"])
 RESULT["reported_tokens"]=sum(x.get("input_tokens",0)+x.get("output_tokens",0) for x in RESULT["groups"])
 RESULT["balance_delta"]={k:after[k]-v for k,v in before.items() if k in after}
 checkpoint()
 print("CLUSTER_FINISHED",RESULT["counts"],"tokens",RESULT["reported_tokens"],"balance",RESULT["balance_delta"],flush=True)
if __name__=="__main__":main()
