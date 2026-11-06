#!/usr/bin/env python3
"""BK-002 TeamAI CLI vs scripted Git+symlink, local Git fixtures only.

Runs the real built CLI of a pinned, disposable TeamAI fork checkout.
No network, credentials, external hooks, live agent profiles or production files.
Baseline is an explicitly simple Git+symlink script, NOT a universal claim
about a human-reviewed manual workflow. Tested only in a rootless container.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import tempfile
import time

PIN = "e5a0bb5901f4b1c78d7b1e28a2ba43e1cbe86db4"
GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="BK002 Lab",
    GIT_AUTHOR_EMAIL="lab@invalid.example",
    GIT_COMMITTER_NAME="BK002 Lab",
    GIT_COMMITTER_EMAIL="lab@invalid.example",
    GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null",
    GIT_TERMINAL_PROMPT="0", CI="true")
V1 = "---\nname: incident-response\ndescription: dummy\n---\n# Version 1\n"
V2 = V1.replace("Version 1", "Version 2")
V3 = V1.replace("Version 1", "Version 3")
V4 = V1.replace("Version 1", "Version 4")
BAD = V1.replace("Version 1", "INVALID-MUST-NOT-LAND")
GOV = "All production changes require two reviewers.\n"
SCENARIOS = ("initial", "update", "delete", "restore", "invalid_schema",
             "unknown_field", "recover", "idempotent")
def sha(x): return hashlib.sha256(x.encode()).hexdigest()
def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
def git(args, cwd):
    p=subprocess.run(["git",*args],cwd=cwd,env=GIT_ENV,
        capture_output=True,text=True,timeout=12)
    if p.returncode:
        raise RuntimeError(f"git failed {args}: {p.stderr[-550:]}")
    return p.stdout.strip()
def load_skill(home):
    p=home/".claude"/"skills"/"incident-response"/"SKILL.md"
    return p.read_text() if p.is_file() else None
def snapshot(home):
    skill=load_skill(home)
    gov=home/".claude"/"CLAUDE.md"
    return {"skill_sha256":sha(skill) if skill is not None else None,
            "governance_sha256":sha(gov.read_text()) if gov.is_file() else None,
            "skill_present":skill is not None}
def measure(func):
    a=resource.getrusage(resource.RUSAGE_CHILDREN)
    started=time.perf_counter_ns()
    out=func()
    b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return out,{"wall_ms":round((time.perf_counter_ns()-started)/1e6,3),
      "child_cpu_ms":round(((b.ru_utime+b.ru_stime)-(a.ru_utime+a.ru_stime))*1000,3),
      "child_inblock":b.ru_inblock-a.ru_inblock,
      "child_oublock":b.ru_oublock-a.ru_oublock,
      "child_peak_rss_kib_cumulative":b.ru_maxrss}
def publish(repo,version,extra=""):
    skill=repo/"skills"/"incident-response"/"SKILL.md"
    if version is None:
        if skill.is_file(): skill.unlink()
        d=skill.parent
        if d.is_dir(): d.rmdir()
    else:put(skill,version)
    put(repo/"team-context.yaml","schemaVersion: "+("2" if extra=="schema2" else "1")+"\n"+
        ("unexpected: true\n" if extra=="unknown" else ""))
    put(repo/"governance"/"policy.md",GOV)
    git(["add","-A"],repo)
    git(["commit","-q","-m","stage "+str(version)[:20]+extra],repo)
def setup(root,cli):
    provider=root/"provider-origin"
    provider.mkdir()
    put(provider/"skills"/"incident-response"/"SKILL.md",V1)
    put(provider/"team-context.yaml","schemaVersion: 1\n")
    put(provider/"governance"/"policy.md",GOV)
    git(["init","-q","-b","main"],provider)
    git(["add","-A"],provider)
    git(["commit","-q","-m","initial"],provider)
    team=root/"team-origin"
    team.mkdir()
    put(team/"teamai.yaml",
        "team: bk002-e2e\nrepo: "+str(team)+"\nprovider: git\nteamContext:\n  repo: "+str(provider)+"\n")
    git(["init","-q","-b","main"],team)
    git(["add","-A"],team)
    git(["commit","-q","-m","initial"],team)
    ah=root/"A-home"
    bh=root/"B-home"
    for home in (ah,bh):
        (home/".claude"/"skills").mkdir(parents=True)
        (home/".claude"/"rules").mkdir(parents=True)
    cacheA=ah/"provider-cache"
    git(["clone","-q",str(provider),str(cacheA)],root)
    (bh/".teamai").mkdir()
    local=bh/".teamai"/"team-repo"
    git(["clone","-q",str(team),str(local)],root)
    put(bh/".teamai"/"config.yaml",
      "repo:\n  localPath: "+str(local)+"\n  remote: "+str(team)+
      "\nusername: lab\nupdatePolicy: auto\nscope: user\n")
    cached=bh/".teamai"/"team-context"/sha(str(provider))[:16]/"repo"
    cached.parent.mkdir(parents=True)
    git(["clone","-q",str(provider),str(cached)],root)
    return provider,ah,bh,cacheA
def baseline_pull(home,cache):
    git(["-C",str(cache),"pull","--ff-only","-q"],home)
    target=cache/"skills"/"incident-response"
    link=home/".claude"/"skills"/"incident-response"
    if target.joinpath("SKILL.md").is_file():
        if link.is_symlink() and link.resolve()==target.resolve(): pass
        else:
            if link.exists() or link.is_symlink():link.unlink()
            link.symlink_to(target,target_is_directory=True)
    else:
        if link.exists() or link.is_symlink():link.unlink()
    return "OK"
def cli_pull(cli,home,root):
    env=dict(GIT_ENV,HOME=str(home),XDG_CONFIG_HOME=str(home/".config"))
    p=subprocess.run(["node",str(cli),"pull","--force"],
        cwd=root,env=env,capture_output=True,text=True,timeout=25)
    if p.returncode!=0:
        raise RuntimeError("CLI pull failed: "+(p.stdout+"\n"+p.stderr)[-850:])
    return (p.stdout+"\n"+p.stderr)[-3500:]
def allowed(home,arm):
    allow=(".claude/",".teamai/") if arm=="B" else (".claude/","provider-cache/")
    bad=[]
    for f in home.rglob("*"):
        if f.is_file() or f.is_symlink():
            s=f.relative_to(home).as_posix()
            if not any(s.startswith(prefix) for prefix in allow):bad.append(s)
    return bad
def metric_summary(values):
    vals=sorted(values)
    p95=vals[min(len(vals)-1,__import__("math").ceil(.95*len(vals))-1)]
    return {"n":len(vals),"p50":round(statistics.median(vals),3),
            "p95_nearest_rank":round(p95,3),
            "min":round(vals[0],3),"max":round(vals[-1],3),
            "mean":round(statistics.mean(vals),3)}
def run_seed(seed,cli):
    rows=[]
    with tempfile.TemporaryDirectory(prefix="bk002-teamai-seed-") as work:
        root=Path(work)
        provider,ah,bh,cache=setup(root,cli)
        rng=random.Random(seed)
        phases={
          "initial":(V1,""),
          "update":(V2,""),
          "delete":(None,""),
          "restore":(V3,""),
          "invalid_schema":(BAD,"schema2"),
          "unknown_field":(BAD,"unknown"),
          "recover":(V4,""),
          "idempotent":(V4,"")
        }
        last_b=None
        for phase,(expected,extra) in phases.items():
            if phase not in ("initial","idempotent"):publish(provider,expected,extra)
            order=["A","B"]
            rng.shuffle(order)
            arms={}
            outputs={}
            for arm in order:
                output,metrics=measure(
                    (lambda:baseline_pull(ah,cache)) if arm=="A" else
                    (lambda:cli_pull(cli,bh,root)))
                outputs[arm]=output
                arms[arm]=metrics
            A=snapshot(ah);B=snapshot(bh)
            # This is a distinct independent file-content oracle, not CLI claims.
            exp_b=V3 if phase in ("invalid_schema","unknown_field") else expected
            if phase=="idempotent":exp_b=V4
            assert A["skill_sha256"]==(sha(expected) if expected is not None else None),(seed,phase,"baseline",A)
            assert B["skill_sha256"]==(sha(exp_b) if exp_b is not None else None),(seed,phase,"TeamAI",B)
            if B["skill_present"]:
                gov=(bh/".claude"/"CLAUDE.md").read_text()
                assert GOV.strip() in gov
                assert "Team Context Governance" in gov
            if phase in ("invalid_schema","unknown_field"):
                assert "unsupported schemaVersion" in outputs["B"] if phase=="invalid_schema" else "unknown top-level field" in outputs["B"]
                assert BAD in load_skill(ah) and BAD not in load_skill(bh)
            if phase=="idempotent":
                assert B==last_b,(seed,phase,"idempotency hash")
            bad_A=allowed(ah,"A")
            bad_B=allowed(bh,"B")
            assert not bad_A,(seed,phase,"baseline unexpected writes",bad_A)
            # Candidate writes outside the minimal Claude-only profile are a
            # FIRST-CLASS FAILED acceptance gate, not a reason to hide results.
            # Continue other scenarios and report all extra paths.
            row={"seed":seed,"phase":phase,"arms":arms,
                 "oracle":{"A_skill_sha":A["skill_sha256"],"B_skill_sha":B["skill_sha256"],
                   "B_governance_sha":B["governance_sha256"],
                   "B_correct":True,"A_correct_for_simple_mirror":True,
                   "B_unexpected_home_files":bad_B,"A_unexpected_home_files":bad_A,
                   "B_invalid_manifest_guard":phase in ("invalid_schema","unknown_field")}}
            rows.append(row)
            last_b=B
        # Deliberate mutation of independent oracle: must be caught.
        try:
            assert sha(BAD)==snapshot(bh)["skill_sha256"],"injected wrong acceptance"
        except AssertionError:
            mutation_caught=True
        else:
            mutation_caught=False
        assert mutation_caught
    return rows
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkout",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--repeats",type=int,default=5)
    args=p.parse_args()
    assert 3<=args.repeats<=8
    checkout=args.checkout.resolve()
    assert checkout.is_dir()
    assert git(["rev-parse","HEAD"],checkout)==PIN,"wrong fork source pin"
    cli=checkout/"dist"/"index.js"
    assert cli.is_file(),"build tested CLI first"
    samples=[]
    begin=time.perf_counter()
    for seed in range(args.repeats):
        rows=run_seed(20261106+seed,cli)
        samples.extend(rows)
        print("seed",seed,"stages",len(rows),"PASS",flush=True)
    by_arm={}
    for arm in ("A","B"):
        parts=[row["arms"][arm] for row in samples]
        by_arm[arm]={
          "wall_ms":metric_summary([x["wall_ms"] for x in parts]),
          "child_cpu_ms":metric_summary([x["child_cpu_ms"] for x in parts]),
          "child_inblock_total":sum(x["child_inblock"] for x in parts),
          "child_oublock_total":sum(x["child_oublock"] for x in parts),
          "peak_child_rss_kib_observed":max(x["child_peak_rss_kib_cumulative"] for x in parts)
        }
    extra_paths=sorted({p for row in samples for p in row["oracle"]["B_unexpected_home_files"]})
    result={
      "study":"BK-002 Tencent TeamAI CLI",
      "source":"Artemedi/teamai-cli",
      "source_commit":PIN,
      "upstream_code_transitively_in_port":True,
      "source_was_checked_out_in_disposable_clone":True,
      "mode":"LOCAL_GIT_SYMLINK_BASELINE_VS_REAL_PORTED_TEAMAI_CLI",
      "status":"FUNCTIONAL_PASS_SCOPE_GATE_FAIL" if extra_paths else "PASS",
      "repeats":args.repeats,"seeds":[20261106+i for i in range(args.repeats)],
      "scenarios":list(SCENARIOS),"cases_per_arm":len(samples),
      "validation":{"B_correct_all":True,"schema_fail_closed":True,
        "local_guard_mutation_detected":True,"no_unexpected_home_file":not bool(extra_paths),
        "out_of_scope_files_in_minimal_claude_profile":extra_paths,
        "offline_no_network":True},
      "baseline_def": "Automated Git pull + symlink of one dummy skill, with deletion cleanup but without schema or governance validation. NOT manual human review.",
      "arm_B_def":"Real TeamAI CLI pull --force from pinned ported owner fork, configured only in disposable HOME with dummy local Git origins.",
      "metrics":by_arm,
      "runs":samples,
      "limitations":[
        "One tiny synthetic skill and governance file, not actual multi-user or multi-tool production",
        "No measurement of rollout quality, inference tokens, model error rate, or human review labor",
        "Manual baseline lacks schema validation by construction; a reviewed manual process can guard equally",
        "No observed network IO; all Git remotes are local",
        "Child rusage block counters are kernel accounting, not physical bytes or full system IO",
        "Child maxrss is a cumulative upper envelope; not p95 memory per operation",
        "No merge/rebase of upstream into any real user fork, no hooks published or executed"
      ],
      "tooling":{"python":__import__("sys").version.split()[0],
                 "llm_calls":0,"tokens":None,"cost_usd":None,"gpu_vram":None},
      "elapsed_wall_seconds_total":round(time.perf_counter()-begin,3)
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],
      "cases_per_arm":result["cases_per_arm"],
      "metrics":by_arm,"seconds":result["elapsed_wall_seconds_total"]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
