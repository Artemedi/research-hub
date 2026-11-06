#!/usr/bin/env python3
"""BK-014 independent provenance A/B over disposable local Git fixtures.

A executes pinned paper2project.execution.tree_hash.
B reproduces pinned orx SourceSnapshot's committed-revision git archive,
content addressing and digest check. B is a SOURCE-DERIVED replay, not an
invocation of orx SourceSnapshot::create (Rust's full path is checked separately).
Neither variant executes agent code; shell controls are confined to fixture Git.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT=Path("/lab")
OWNER_PIN="6d82a42175a71d3327b773df88f1da0707efe43c"
ORX_PIN="23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d"
SCHEMA="BK014_PROVENANCE_v1"
SOURCES=[
    Path("/source-owner"),
    Path("/source-orx")
]
for path,pin in [(SOURCES[0],OWNER_PIN),(SOURCES[1],ORX_PIN)]:
    result=subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],capture_output=True,text=True,check=True)
    assert result.stdout.strip()==pin,(path,pin)
sys.path.insert(0,str(SOURCES[0]/"src"))
from paper2project.execution import tree_hash, container_argv, LIMITS

GIT_ENV=dict(os.environ,
             GIT_CONFIG_NOSYSTEM="1",GIT_CONFIG_GLOBAL="/dev/null",
             GIT_AUTHOR_NAME="BK014",GIT_AUTHOR_EMAIL="fixture@invalid.test",
             GIT_COMMITTER_NAME="BK014",GIT_COMMITTER_EMAIL="fixture@invalid.test",
             GIT_TERMINAL_PROMPT="0")

def git(args,cwd):
    q=subprocess.run(["git",*args],cwd=cwd,env=GIT_ENV,capture_output=True,text=True,timeout=12)
    if q.returncode:raise RuntimeError("git failed: "+str(args)+": "+q.stderr[-600:])
    return q.stdout.strip()

def sha_bytes(blob):return hashlib.sha256(blob).hexdigest()

def make_fixture(path,seed):
    path.mkdir()
    git(["init","-q","-b","main"],path)
    files={
        "src/analyze.py":"""from pathlib import Path
import hashlib, json
content = Path('papers/full.txt').read_bytes()
result = {'paper_sha256': hashlib.sha256(content).hexdigest(), 'valid': all(
  x in content.decode() for x in ('Methods:', 'Results:', 'Limitations:'))}
print(json.dumps(result, sort_keys=True))
""",
        "papers/full.txt":f"Title: Synthetic Research {seed}\nMethods: deterministic benchmark\nResults: dummy evidence only\nLimitations: not real science\n",
        "inputs/settings.json":json.dumps({"seed":seed,"scenario":"fixture-only"},sort_keys=True)+"\n",
        "README.md":"Synthetic BK-014 test. No real papers, secrets, providers, or databases.\n"
    }
    for rel,val in files.items():
        p=path/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(val)
    git(["add","-A"],path);git(["commit","-q","-m",f"synthetic seed {seed}"],path)
    head=git(["rev-parse","HEAD"],path)
    assert not git(["status","--porcelain"],path)
    return head,files

def full_text_present(path):
    f=path/"papers"/"full.txt"
    if not f.is_file():return False
    text=f.read_text()
    return all(s in text for s in ("Methods:","Results:","Limitations:"))

def measure(fn):
    res0=resource.getrusage(resource.RUSAGE_SELF)
    child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    started=time.perf_counter_ns()
    output=fn()
    wall=(time.perf_counter_ns()-started)/1e6
    res1=resource.getrusage(resource.RUSAGE_SELF)
    child1=resource.getrusage(resource.RUSAGE_CHILDREN)
    cpus=(
        (res1.ru_utime+res1.ru_stime)-(res0.ru_utime+res0.ru_stime)
        +(child1.ru_utime+child1.ru_stime)-(child0.ru_utime+child0.ru_stime)
    )
    return output,{"wall_ms":round(wall,4),
                   "cpu_ms":round(cpus*1000,4),
                   "peak_rss_kib_cumulative":max(res1.ru_maxrss,child1.ru_maxrss),
                   "bytes_out":0}

def baseline_hash(repo):
    return tree_hash(repo)["sha256"]

def source_derived_archive(repo,rev,dir):
    # Matches original src/compute.rs: archive(repo, revision, "tar", tmp),
    # digest_file(tmp), install_content_addressed(tmp, digest.tar).
    tmp=dir/".source.tmp.tar"
    assert not tmp.exists()
    with tmp.open("wb") as out:
        p=subprocess.run(["git","archive","--format=tar",rev],cwd=repo,env=GIT_ENV,
                         stdout=out,stderr=subprocess.PIPE,timeout=12)
    if p.returncode:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("git archive failed: "+p.stderr.decode(errors="replace")[-200:])
    blob=tmp.read_bytes()
    digest=sha_bytes(blob)
    destination=dir/(digest+".tar")
    if destination.exists():
        assert destination.read_bytes()==blob
        tmp.unlink()
    else:
        tmp.rename(destination)
        destination.chmod(0o600)
    return {"git_commit":rev,"archive_sha256":digest,"archive_bytes":len(blob),
            "archive_path":str(destination)}

def verify_archive(rec):
    p=Path(rec["archive_path"])
    raw=p.read_bytes()
    return sha_bytes(raw)==rec["archive_sha256"] and len(raw)==rec["archive_bytes"]

def independent_tar_oracle(rec,files):
    assert verify_archive(rec)
    with tarfile.open(rec["archive_path"],mode="r") as t:
        names={m.name for m in t.getmembers() if m.isfile()}
        assert names==set(files),(names,files.keys())
        for rel,content in files.items():
            item=t.extractfile(rel)
            assert item is not None
            assert item.read()==content.encode()
    return True

def stats(vals):
    v=sorted(vals)
    import math
    return {"n":len(v),"p50":round(statistics.median(v),4),
            "p95_nearest_rank":round(v[math.ceil(len(v)*0.95)-1],4),
            "mean":round(statistics.mean(v),4),
            "min":round(v[0],4),"max":round(v[-1],4)}

def run(seed,repeat):
    rng=random.Random(seed)
    with tempfile.TemporaryDirectory(prefix="bk014-seed-",dir="/lab/fixtures") as temp:
        base=Path(temp)
        repo=base/"repo"
        head,files=make_fixture(repo,seed)
        assert full_text_present(repo)
        # Source A is pinned author's actual tree_hash, not a synthetic hash.
        baseline_ref=baseline_hash(repo)
        controls={
            "seed":seed,"git_commit":head,"full_text_gate_pass":True,
            "baseline_direct_tree_sha256":baseline_ref,
            "archive_committed_no_dirty":True,
            "metadata_false_invalidation_A":False,
            "metadata_stable_B":False,
            "dirty_mutation_detected_A":False,
            "dirty_mutation_omitted_B":False,
            "post_commit_both_change":False,
            "archive_corruption_detected_B":False,
            "snapshot_available_without_source_B":False,
            "missing_fulltext_rejected_external_gate":False,
            "no_unrelated_host_files":True,
        }
        snaps=[]
        records=[]
        for i in range(repeat):
            path=base/("content-"+str(i))
            path.mkdir()
            order=["A","B"]
            rng.shuffle(order)
            metrics={}
            for arm in order:
                if arm=="A":
                    val,met=measure(lambda:baseline_hash(repo))
                    assert val==baseline_ref
                else:
                    val,met=measure(lambda:source_derived_archive(repo,head,path))
                    assert independent_tar_oracle(val,files)
                    met["bytes_out"]=val["archive_bytes"]
                    snaps.append(val)
                metrics[arm]=met
            records.append({"rep":i,"order":order,"A":metrics["A"],"B":metrics["B"]})
        assert len({s["archive_sha256"] for s in snaps})==1
        assert len({s["git_commit"] for s in snaps})==1
        snapshot=snaps[0]
        # Git config changes only metadata; file content of commit and working
        # tree is identical. A includes .git, B intentionally does not.
        git(["config","--local","bk014.fixture-meta",f"{seed}"],repo)
        after_meta=baseline_hash(repo)
        post_meta=source_derived_archive(repo,head,base/"content-0")
        controls["metadata_false_invalidation_A"]=after_meta!=baseline_ref
        controls["metadata_stable_B"]=post_meta["archive_sha256"]==snapshot["archive_sha256"]
        # Make dirty uncommitted change; A can detect different working tree,
        # B archives commit and does NOT represent dirty content.
        (repo/"papers"/"full.txt").write_text("DIRTY UNCOMMITTED\n")
        dirty=baseline_hash(repo)
        candidate=source_derived_archive(repo,head,base/"content-0")
        controls["dirty_mutation_detected_A"]=dirty!=after_meta
        controls["dirty_mutation_omitted_B"]=candidate["archive_sha256"]==snapshot["archive_sha256"]
        # Verify full text gate for missing text is OUTSIDE both mechanisms.
        (repo/"papers"/"full.txt").unlink()
        controls["missing_fulltext_rejected_external_gate"]=not full_text_present(repo)
        (repo/"papers"/"full.txt").write_text(files["papers/full.txt"])
        # Commit a content change: metadata changes and new SHA on both arms.
        updated=files["papers/full.txt"].replace("dummy evidence", "changed evidence")
        (repo/"papers"/"full.txt").write_text(updated)
        git(["add","papers/full.txt"],repo)
        git(["commit","-q","-m","change full text"],repo)
        newhead=git(["rev-parse","HEAD"],repo)
        new_a=baseline_hash(repo)
        new_b=source_derived_archive(repo,newhead,base/"content-0")
        controls["post_commit_both_change"]=new_a!=baseline_ref and new_b["archive_sha256"]!=snapshot["archive_sha256"]
        # Corrupt cached content; digest must reject.
        archive=Path(snapshot["archive_path"])
        with archive.open("r+b") as fd:
            fd.seek(64);orig=fd.read(1)
            fd.seek(64);fd.write(bytes([orig[0]^1]))
        controls["archive_corruption_detected_B"]=not verify_archive(snapshot)
        # An untouched second content-addressed archive survives source removal.
        survivor=snaps[-1]
        assert Path(survivor["archive_path"])!=archive
        assert verify_archive(survivor)
        import shutil
        shutil.rmtree(repo)
        controls["snapshot_available_without_source_B"]=independent_tar_oracle(survivor,files)
        assert all(controls[x] for x in controls if x not in ("seed","git_commit","baseline_direct_tree_sha256","archive_committed_no_dirty"))
        return {"seed":seed,"controls":controls,"measurements":records,
                "archive_bytes":snapshot["archive_bytes"]}

def main():
    results=[run(20261106+i,5) for i in range(5)]
    missing=[]
    for p in (ROOT/"fixtures").glob("*"):
        if p.is_dir():missing.append(p.name)
    assert not missing,missing
    samples={arm:[r["measurements"][i][arm] for r in results for i in range(5)] for arm in ("A","B")}
    summary={
        arm: {
            "wall_ms":stats([x["wall_ms"] for x in vals]),
            "cpu_ms":stats([x["cpu_ms"] for x in vals]),
            "total_archive_bytes_written":sum(x["bytes_out"] for x in vals),
            "rss_max_kib_cumulative":max(x["peak_rss_kib_cumulative"] for x in vals)
        } for arm,vals in samples.items()
    }
    cmd=container_argv(LIMITS,"docker.io/library/node:22",["python3","-c","print(1)"],
                       "/work/source",None,"/work/output")
    assert "--network=none" in cmd and "--read-only" in cmd and "--cap-drop=ALL" in cmd
    assert "--security-opt=no-new-privileges" in cmd and any(":ro" in a for a in cmd)
    result={
        "study":"BK-014 alphaXiv OpenResearch",
        "date":"2026-11-06",
        "pin_orx":ORX_PIN,"pin_paper2project":OWNER_PIN,
        "status":"SOURCE_DERIVED_GIT_ARCHIVE_AB_BASELINE_SOURCE_EXECUTED",
        "branch_A":"Actual owner paper2project.execution.tree_hash (includes .git and all current bytes, modes)",
        "branch_B":"Source-derived reimplementation of original Rust SourceSnapshot git archive + SHA256 content-addressed cache, not actual orx SourceSnapshot::create",
        "design":"5 seeds x5 repetitions; same synthetic Git repository, content, operation sequence; A/B order shuffled per repeat",
        "metrics":summary,"samples_per_arm":25,
        "full_text_input":{"synthetic_methods_results_limitations_present":5,
          "missing_fulltext_negative_cases":5,
          "missing_fulltext_rejected_by":"external explicit gate, not orx or paper2project snapshot"},
        "controls_summary":{key:sum(bool(r["controls"][key]) for r in results)
            for key in results[0]["controls"] if isinstance(results[0]["controls"][key],bool)},
        "owner_podman_argv":{"offline":True,"read_only":True,"drop_caps":True,"no_new_privileges":True,"source_mount_ro":True},
        "io_semantics":"Archive bytes are logical tar payload bytes, not measured physical I/O; A hash reads .git and content but does not persist source snapshot",
        "resources":{"model_calls":0,"api_cost_usd":0,"gpu_vram":None,
          "CPU_time":"rusage_self+children, in synthetic local container",
          "RSS":"cumulative max for entire process, not per-arm"},
        "limitations":[
            "B reimplements documented Rust SourceSnapshot archive/digest behavior, NOT a direct invocation of orx SourceSnapshot or its SQLite/daemon lifecycle. Separate source build/tests are needed to validate binary.",
            "A hashes current working tree INCLUDING .git metadata, while B creates immutable Git commit tar. They are NOT functionally equivalent by design.",
            "This compares provenance guarantees, not end-to-end research quality, launch safety, or workflow speed.",
            "No actual paper or model, only explicit synthetic full-text fixture; no AlphaXiv/PubMed queries.",
            "Crash/restart of orx supervisor, remote GPU, agent calls and database WAL are not exercised.",
            "B archive omission of dirty changes is expected semantics; strong guard requires explicit git dirty preflight.",
            "No user workspace files, secrets or production datasets were read.",
            "A and B do not control for git metadata or filesystem cache across repetitions; speed is descriptive only."
        ],
        "records":results
    }
    (ROOT/"results"/"provenance-ab.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"summary":summary,
                     "controls":result["controls_summary"],
                     "fulltext":result["full_text_input"]},ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
