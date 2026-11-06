#!/usr/bin/env python3
"""Run pinned GPT-6 Astra A/B on disposable fixtures, preserve telemetry."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path("/var/tmp/bk009-astra-prompt-lab-20261106")
MANIFEST=json.loads((ROOT/"fixture-manifest.json").read_text())
ORDER=[
    ("unit","B"),("unit","A"),
    ("migration","A"),("migration","B"),
    ("config","B"),("config","A"),
    ("query","A"),("query","B"),
]

def oracle(task,path):
    tracked=subprocess.run(["git","diff","--name-only"],cwd=path,capture_output=True,text=True,check=True).stdout.splitlines()
    untracked=subprocess.run(["git","ls-files","--others","--exclude-standard"],cwd=path,capture_output=True,text=True,check=True).stdout.splitlines()
    changed=sorted(set(tracked+untracked))
    expected={
        "typo":"docs/quickstart.md","unit":"src/status_formatter.py",
        "migration":"migrations/0002_observations_created_at_idx.sql",
        "config":"config/service.yaml","query":"queries/find_event.sql",
    }[task]
    correct = changed == [expected]
    reasons=[]
    if not correct: reasons.append("wrong_changed_paths")
    if task=="typo":
        value=(path/expected).read_text()
        correct &= "returns status: ready." in value and "statuz" not in value
    elif task=="unit":
        p=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-v"],
            cwd=path,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"),
            capture_output=True,text=True,timeout=12)
        correct &= p.returncode==0
        if p.returncode:reasons.append("target_unit_failed")
    elif task=="migration":
        f=path/expected
        if not f.is_file():
            correct=False;reasons.append("missing_migration")
        else:
            sql=re.sub(r"\s+"," ",f.read_text().upper())
            correct &= "CREATE INDEX CONCURRENTLY IF NOT EXISTS" in sql
            correct &= "ON PUBLIC.OBSERVATIONS" in sql
            correct &= "CREATED_AT" in sql
            correct &= not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b",sql)
    elif task=="config":
        import yaml
        f=yaml.safe_load((path/expected).read_text())
        correct &= f.get("telemetry",{}).get("enabled") is False
        correct &= f.get("telemetry",{}).get("endpoint") == "http://127.0.0.1:4317"
        correct &= f.get("security",{}).get("require_auth") is True
    elif task=="query":
        sql=(path/expected).read_text()
        norm=sql.lower()
        correct &= "id::" not in norm and bool(re.search(r"\bid\s*=\s*'00000000-0000-0000-0000-000000000042'",norm))
        correct &= "from public.events" in norm
    return {"passed":bool(correct),"changed_paths":changed,"expected_path":expected,"reasons":reasons}

def parse_trace(file):
    events=[];commands=[];usage=None;agent=[]
    for line in file.read_text().splitlines():
        try:e=json.loads(line)
        except json.JSONDecodeError:continue
        if e.get("type")=="turn.completed":usage=e.get("usage")
        if e.get("type")=="item.completed":
            item=e.get("item",{})
            if item.get("type")=="command_execution":
                commands.append(str(item.get("command","")))
            if item.get("type")=="agent_message":
                agent.append(str(item.get("text",""))[:1200])
            if item.get("type")=="file_change":
                events.append(item.get("type"))
    invoked=" ".join(commands)
    return {
        "usage":usage,
        "cmd_count":len(commands),
        "test_command_count":sum("unittest" in x or "pytest" in x for x in commands),
        "docs_mentions_in_tool_commands":{
            name:sum(f"docs/{name}.md" in x for x in commands)
            for name in ("architecture","database","deployment")},
        "skill_tool_mentions":sum("SKILL.md" in x for x in commands),
        "file_change_events":len(events),
        "reported_completion":bool(agent),
        "agent_message_tail":agent[-1][:420] if agent else None
    }

def run(task,variant):
    ident=f"{variant}-{task}"
    work=ROOT/"work"/ident
    assert work.is_dir()
    trace=ROOT/"results"/f"{ident}.jsonl"
    stderr=ROOT/"results"/f"{ident}.stderr"
    assert not trace.exists(),ident
    cmd=[
        "timeout","145s","codex","exec",
        "--ignore-user-config","--ignore-rules","--ephemeral",
        "--skip-git-repo-check","--json","--sandbox","workspace-write",
        "-m","gpt-6-astra","-c","model_reasoning_effort=medium",
        MANIFEST["tasks"][task],
    ]
    started=time.monotonic()
    with trace.open("wb") as out,stderr.open("wb") as err:
        p=subprocess.run(cmd,cwd=work,stdin=subprocess.DEVNULL,
            stdout=out,stderr=err,timeout=160)
    wall=time.monotonic()-started
    parse=parse_trace(trace)
    correctness=oracle(task,work)
    rec={
        "id":ident,"task":task,"variant":variant,
        "rc":p.returncode,"wall_seconds":round(wall,3),
        "oracle":correctness,
        **parse
    }
    if parse["usage"]:
        u=parse["usage"]
        # Illustrative OpenAI API list-price equivalent, not real Codex charge.
        inp=u.get("input_tokens",0);cache=u.get("cached_input_tokens",0);output=u.get("output_tokens",0)
        rec["api_list_equivalent_usd_estimate"]=round((inp-cache)*10/1e6+cache*1/1e6+output*50/1e6,5)
    return rec

def main():
    report=ROOT/"results"/"ab-progress.json"
    raw={}
    for task in ("typo",):
        for variant in ("A","B"):
            p=ROOT/"results"/f"{variant}-{task}.jsonl"
            assert p.exists()
            tr=parse_trace(p)
            import re
            content=(ROOT/"results"/f"{variant}-{task}.time").read_text()
            match=re.search(r"WALL_SECONDS=([\d.]+)",content)
            assert match
            item={"id":f"{variant}-{task}","task":task,"variant":variant,"rc":0,
                  "wall_seconds":float(match.group(1)),
                  "oracle":oracle(task,ROOT/"work"/f"{variant}-{task}"),**tr}
            u=tr["usage"]
            item["api_list_equivalent_usd_estimate"]=round(
                (u["input_tokens"]-u["cached_input_tokens"])*10/1e6+
                u["cached_input_tokens"]*1/1e6+u["output_tokens"]*50/1e6,5)
            raw[item["id"]]=item
    report.write_text(json.dumps({"completed":list(raw.values()),"pending":ORDER},indent=2))
    for i,(task,variant) in enumerate(ORDER):
        try:
            result=run(task,variant)
        except Exception as e:
            result={"id":f"{variant}-{task}","task":task,"variant":variant,
                    "exception":str(e),"rc":None,"oracle":{"passed":False}}
        raw[result["id"]]=result
        report.write_text(json.dumps({"completed":list(raw.values()),"pending":ORDER[i+1:]},indent=2))
        print("FINISHED",result["id"],"RC",result.get("rc"),
            "PASS",result["oracle"].get("passed"),
            "SECONDS",result.get("wall_seconds"),
            "TOKENS",(result.get("usage") or {}).get("input_tokens"),flush=True)
    full={"study":"BK-009 GPT-6 Astra guidance","model":"gpt-6-astra",
          "cli":"Codex CLI 0.164.0","reasoning_effort":"medium",
          "samples":len(raw),"pairs":len(MANIFEST["tasks"]),
          "design":"Paired tasks, fixed model; A broad mandatory context+long skills vs B contextual guidance+short router skills. Each case independent local fixture. Task order alternated for four later pairs.",
          "manifest":MANIFEST,"results":list(raw.values()),
          "source":"https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra",
          "limitations":[
            "Official blog provides engineering advice, not a controlled study or expected effect size.",
            "Non-blinded combined treatment: AGENTS.md and skill metadata/body changed together.",
            "Only five task pairs, one run per variant, low statistical power; possible ordering/caching and server-load confounding.",
            "Usage includes provider prompt and tool-round context; cached tokens and list-price estimate are not billed Codex charges.",
            "No actual user project, no agent model generalization, no production approval.",
            "Before-start .agents skill content is different across arms; not a fixed-context-token fairness comparison.",
        ]}
    (ROOT/"results"/"ab.json").write_text(json.dumps(full,indent=2,ensure_ascii=False)+"\n")
    print("LAB_COMPLETE",len(raw),flush=True)
if __name__=="__main__":
    main()
