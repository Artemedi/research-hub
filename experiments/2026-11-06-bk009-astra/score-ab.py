#!/usr/bin/env python3
"""Independent post-hoc scoring, never change any A/B workspace or oracle outputs."""
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import hashlib

D=Path("/var/tmp/bk009-astra-prompt-lab-20261106")
model_results=json.loads((D/"results"/"ab.json").read_text())
rows=model_results["results"]
assert len(rows)==10, len(rows)
assert {(x["task"],x["variant"]) for x in rows}=={(k,v) for k in ["typo","unit","migration","config","query"] for v in "AB"}
report=[]
cache_effects={}
for row in rows:
    assert row["rc"]==0,(row["id"],row["rc"])
    p=D/"work"/row["id"]
    changed=row["oracle"]["changed_paths"]
    extra=[x for x in changed if x!=row["oracle"]["expected_path"]]
    cache_files=sorted(x for x in extra if "/__pycache__/" in x and x.endswith(".pyc"))
    other_extra=sorted(set(extra)-set(cache_files))
    functional=bool(row["oracle"]["passed"])
    if row["task"]=="unit":
        test=subprocess.run(["python3","-m","unittest","discover","-s","tests","-v"],cwd=p,
            capture_output=True,text=True,timeout=15,env={"PATH":"/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1"})
        functional=(test.returncode==0 and row["oracle"]["expected_path"] in changed)
        assert functional,(row["id"],test.stderr)
    else:
        assert functional,row["id"]
    assert not other_extra,(row["id"],other_extra)
    # No actual non-code unexpected writes except Python interpreter cache.
    clean_scope=not extra
    u=row["usage"]
    assert u and u["input_tokens"]>=u["cached_input_tokens"] and u["output_tokens"]>=0
    report.append({
        "id":row["id"],"task":row["task"],"variant":row["variant"],
        "functional_success":functional,"strict_workspace_scope_pass":clean_scope,
        "nonsemantic_pycache_files":cache_files,"other_unrelated_paths":other_extra,
        "changed_paths":changed,"wall_seconds":row["wall_seconds"],
        "input_tokens":u["input_tokens"],"cached_input_tokens":u["cached_input_tokens"],
        "uncached_input_tokens":u["input_tokens"]-u["cached_input_tokens"],
        "output_tokens":u["output_tokens"],"tool_commands":row["cmd_count"],
        "test_commands":row["test_command_count"],
        "docs_tool_mentions":row["docs_mentions_in_tool_commands"],
        "skills_tool_mentions":row["skill_tool_mentions"],
        "api_price_equivalent_usd":row["api_list_equivalent_usd_estimate"],
        "success_exit":row["rc"]==0,
    })
cases={}
for task in ("typo","unit","migration","config","query"):
    a=next(x for x in report if x["task"]==task and x["variant"]=="A")
    b=next(x for x in report if x["task"]==task and x["variant"]=="B")
    cases[task]={"A":{"functional":a["functional_success"],"scope":a["strict_workspace_scope_pass"],
                       "wall_s":a["wall_seconds"],"input_tokens":a["input_tokens"],
                       "cache_tokens":a["cached_input_tokens"],"command_count":a["tool_commands"]},
                 "B":{"functional":b["functional_success"],"scope":b["strict_workspace_scope_pass"],
                       "wall_s":b["wall_seconds"],"input_tokens":b["input_tokens"],
                       "cache_tokens":b["cached_input_tokens"],"command_count":b["tool_commands"]},
                 "B_less_time":b["wall_seconds"]<a["wall_seconds"],
                 "B_less_tokens":b["input_tokens"]<a["input_tokens"]}
summary={}
for arm in ("A","B"):
    samples=[r for r in report if r["variant"]==arm]
    summary[arm]={
        "tasks":len(samples),
        "functional_pass":sum(x["functional_success"] for x in samples),
        "strict_scope_pass":sum(x["strict_workspace_scope_pass"] for x in samples),
        "pycache_artifacts":sum(len(x["nonsemantic_pycache_files"]) for x in samples),
        "input_tokens_total":sum(x["input_tokens"] for x in samples),
        "cached_input_tokens_total":sum(x["cached_input_tokens"] for x in samples),
        "uncached_input_tokens_total":sum(x["uncached_input_tokens"] for x in samples),
        "output_tokens_total":sum(x["output_tokens"] for x in samples),
        "wall_seconds_total":round(sum(x["wall_seconds"] for x in samples),3),
        "wall_seconds_p50":round(statistics.median(x["wall_seconds"] for x in samples),3),
        "tool_commands_total":sum(x["tool_commands"] for x in samples),
        "test_commands_total":sum(x["test_commands"] for x in samples),
        "api_list_equivalent_usd_total":round(sum(x["api_price_equivalent_usd"] for x in samples),5),
    }
A,B=summary["A"],summary["B"]
comparison={
    "functional_pass_both":A["functional_pass"]==B["functional_pass"]==5,
    "token_input_reduction_pct":round(100*(A["input_tokens_total"]-B["input_tokens_total"])/A["input_tokens_total"],2),
    "wall_reduction_pct":round(100*(A["wall_seconds_total"]-B["wall_seconds_total"])/A["wall_seconds_total"],2),
    "list_price_equivalent_reduction_pct":round(100*(A["api_list_equivalent_usd_total"]-B["api_list_equivalent_usd_total"])/A["api_list_equivalent_usd_total"],2),
    "b_faster_task_pairs":sum(v["B_less_time"] for v in cases.values()),
    "b_lower_input_token_pairs":sum(v["B_less_tokens"] for v in cases.values()),
}
data={
    "study":"BK-009 GPT-6 Astra official guidance",
    "date":"2026-11-06",
    "source_url":"https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra",
    "source_markdown_sha256":hashlib.sha256((D/"official-article.md").read_bytes()).hexdigest(),
    "experiment":"Paired Codex CLI 0.164.0 --model gpt-6-astra, 5 tasks x2 treatment arms; safe disposable Git workspaces. Original article did not report controlled experiment.",
    "model":"gpt-6-astra",
    "model_reasoning_effort":"medium",
    "is_an_official_study_replication":False,
    "requires_model_for_replay":True,
    "runs":report,"per_task":cases,"summary":summary,"comparisons":comparison,
    "treatment_sizes":model_results["manifest"]["sizes"],
    "limitations":[
        "The upstream OpenAI article is engineering guidance, not a measured A/B study.",
        "Synthetic A is deliberately verbose and requires unrelated reads/tests; no evidence that this reflects any user production AGENTS.md.",
        "Only 5 different paired tasks and one call per treatment, no multi-run confidence interval; ordering/caching/provider/load confounding.",
        "Combined intervention AGENTS.md plus skill description, skill content/progressive router: cannot attribute savings to one mechanism.",
        "Both model calls use same pinned GPT-6 Astra and model reasoning effort, but prompt context and cache history differ.",
        "Only trivial self-contained text/SQL/YAML/Python fixtures; no benchmark on real large repositories.",
        "Untracked .pyc appears in both unit tests and is a strict scope fail, though target tests pass.",
        "CLI raw provider token usage includes model/tool context; price uses API list equivalents, not actual billed Codex charges.",
        "No production skill, prompt, runtime or account settings updated."
    ],
    "pricing":{
        "price_basis":"OpenAI gpt-6-astra official API model page as of 2026-11-06",
        "input_usd_per_million":10,"cached_input_usd_per_million":1,
        "output_usd_per_million":50,
        "not_actual_billed_codex_charge":True,
    }
}
out=D/"results"/"scored-ab.json"
out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"summary":summary,"comparison":comparison,"source_sha256":data["source_markdown_sha256"]},indent=2,ensure_ascii=False))
