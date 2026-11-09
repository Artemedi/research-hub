#!/usr/bin/env python3
"""Existing tests from pinned, unmodified target git archives in bwrap --unshare-net.

Not an intervention A/B. Captures the availability of a trusted baseline,
preventing an unrun test suite from being treated as a passed experiment.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
TARGETS=ROOT.parent
MATRIX=json.loads((ROOT/"data/project-fit/portfolio/2026-11-09-targeted-fit.json").read_text())
OUT=ROOT/"data/results/research-portfolio/2026-11-10-p0-baseline-suites.json"
SPECS=[
    ("agent-config", "tests", "unittest", ""),
    ("agent-skills", "tests", "unittest", ""),
    ("dsh-paper2agent", "tests", "unittest", "/source/src:/source/tools"),
    ("sequential-rca", "tests/test_review.py", "pytest", "/source/src"),
]
USER_SITE=Path("/home/Trintos/.local/lib/python3.14/site-packages")

def pin_for(repo):
    found=[row["source_anchor"] for row in MATRIX["pairs"]
           if row["priority"]=="P0" and row["source_anchor"]
           and row["source_anchor"]["repo"]==repo]
    assert found,repo
    revisions={a["commit"] for a in found}
    assert len(revisions)==1,(repo,revisions)
    return revisions.pop()

def archive_repo(repo,sha,dest):
    blob=subprocess.check_output(["git","-C",str(TARGETS/repo),"archive","--format=tar",sha])
    if len(blob)>100_000_000:raise RuntimeError(f"Archive over 100MB for {repo}, skip")
    with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
        names=[m.name for m in archive.getmembers() if m.isfile()]
        assert not any(n.startswith("/") or ".." in Path(n).parts for n in names)
        archive.extractall(dest,filter="data")
    return hashlib.sha256(blob).hexdigest()

def run_one(repo,target,method,extra_path):
    sha=pin_for(repo)
    with tempfile.TemporaryDirectory(prefix="p0-baseline-") as folder:
        src=Path(folder)
        archive_hash=archive_repo(repo,sha,src)
        module=["/usr/bin/python3","-m",("unittest" if method=="unittest" else "pytest")]
        module+=(["discover","-s",target,"-q"] if method=="unittest" else [target,"-q","-p","no:cacheprovider","--disable-warnings"])
        bwrap=["bwrap","--unshare-net","--die-with-parent",
               "--ro-bind","/usr","/usr",
               "--symlink","usr/bin","/bin","--symlink","usr/lib64","/lib64",
               "--dev","/dev","--proc","/proc","--tmpfs","/tmp",
               "--dir","/source","--ro-bind",str(src),"/source",
               "--setenv","HOME","/tmp","--setenv","PYTHONDONTWRITEBYTECODE","1",
               "--setenv","PYTHONPATH",extra_path]
        if method=="pytest":
            # Site-packages only, never mount home credentials.
            assert USER_SITE.is_dir()
            bwrap+=["--dir","/home","--dir","/home/Trintos",
                    "--dir","/home/Trintos/.local","--dir","/home/Trintos/.local/lib",
                    "--dir","/home/Trintos/.local/lib/python3.14",
                    "--ro-bind",str(USER_SITE),str(USER_SITE),
                    "--setenv","PYTHONPATH",str(USER_SITE)+":"+extra_path]
        bwrap+=["--chdir","/source"]+module
        start=time.monotonic()
        try:
            result=subprocess.run(bwrap,capture_output=True,text=True,timeout=100)
            status="PASS_EXISTING_TESTS" if result.returncode==0 else "BLOCKED_OR_FAILED_EXISTING_TESTS"
            trace=result.stdout+"\n"+result.stderr
            unit=re.search(r"Ran (\d+) tests? in",trace)
            unit_count=int(unit.group(1)) if unit else None
            pytest_count=re.search(r"(\d+) passed",trace)
            skips=re.search(r"skipped=(\d+)",trace)
            skip_count=int(skips.group(1)) if skips else 0
            passed=int(pytest_count.group(1)) if pytest_count else (
                unit_count-skip_count if result.returncode==0 and unit_count is not None else None)
            errors=re.search(r"(\d+) errors?",trace)
            return {"project_id":repo,"source_git_sha":sha,"git_archive_sha256":archive_hash,
                    "archive_receipt_scope":"archive hash, not build output","network_denied":True,"exit_code":result.returncode,
                    "scope":method+" "+target,"test_count":unit_count,"passed":passed,
                    "skipped":skip_count,"status":status,
                    "runtime_s":round(time.monotonic()-start,3),
                    "output_tail":trace[-1600:]}
        except subprocess.TimeoutExpired:
            return {"project_id":repo,"source_git_sha":sha,"git_archive_sha256":archive_hash,
                    "network_denied":True,"status":"BLOCKED_TEST_TIMEOUT",
                    "runtime_s":round(time.monotonic()-start,3),"scope":method+" "+target}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    assert args.execute
    rows=[]
    for repo,target,method,extra in SPECS:
        record=run_one(repo,target,method,extra)
        rows.append(record)
        print("ISOLATED_EXISTING_BASELINE",repo,record["status"],record.get("passed"),record.get("exit_code"))
    OUT.write_text(json.dumps({"date":"2026-11-10","scope":"EXISTING_TARGET_TESTS_ONLY_NOT_INTERVENTION_AB",
                              "rows":rows},ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":
    main()
