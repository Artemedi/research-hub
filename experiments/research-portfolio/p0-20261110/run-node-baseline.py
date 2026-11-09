#!/usr/bin/env python3
"""Re-run pinned dsh-team-context scope tests with source archive and no network.

Confirms baseline has project-vs-user scope control; not a new treatment A/B.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
ORIG=ROOT.parent/"dsh-team-context"
OUT=ROOT/"data/results/research-portfolio/2026-11-10-p0-team-scope-baseline.json"
M=json.loads((ROOT/"data/project-fit/portfolio/2026-11-09-targeted-fit.json").read_text())
ANCHOR=next(r["source_anchor"] for r in M["pairs"] if r["study_id"]=="agent-mosaic" and r["project_id"]=="dsh-team-context")
assert ANCHOR["path"]=="src/core/scoped-recall.ts"
NODE=shutil.which("node")
assert NODE is not None,"BLOCKED_NODE_UNAVAILABLE"
NODE_MODULES=ORIG/"node_modules"
assert (NODE_MODULES/"tsx/dist/cli.mjs").is_file(),"BLOCKED_OFFLINE_TSX_DEPS_UNAVAILABLE"

def main():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix="p0-team-scope-") as folder:
        work=Path(folder)
        blob=subprocess.check_output(["git","-C",str(ORIG),"archive","--format=tar",ANCHOR["commit"]])
        assert len(blob)<100_000_000,"BLOCKED_ARCHIVE_OVERSIZED"
        with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
            archive.extractall(work,filter="data")
        assert hashlib.sha256((work/ANCHOR["path"]).read_bytes()).hexdigest()==ANCHOR["file_sha256"]
        (work/"node_modules").symlink_to("/node_modules")
        shutil.copyfile(NODE,work/"node")
        (work/"node").chmod(0o755)
        command=["bwrap","--unshare-net","--die-with-parent",
                 "--ro-bind","/usr","/usr","--symlink","usr/bin","/bin",
                 "--symlink","usr/lib64","/lib64","--dev","/dev",
                 "--proc","/proc","--tmpfs","/tmp",
                 "--dir","/source","--dir","/node_modules",
                 "--ro-bind",str(work),"/source",
                 "--ro-bind",str(NODE_MODULES),"/node_modules",
                 "--ro-bind",str(work/"node"),"/node",
                 "--setenv","HOME","/tmp","--setenv","NODE_OPTIONS","--no-warnings",
                 "/node","/node_modules/tsx/dist/cli.mjs",
                 "--test","/source/test/scoped-recall.test.ts"]
        proc=subprocess.run(command,capture_output=True,text=True,timeout=70)
        output=proc.stdout+"\n"+proc.stderr
        count=re.search(r"# tests (\d+)",output)
        passed=re.search(r"# pass (\d+)",output)
        failed=re.search(r"# fail (\d+)",output)
        result={
            "status":"PASS_PINNED_BASELINE_SCOPE_TESTS_ONLY" if proc.returncode==0 else "BLOCKED_SOURCE_BASELINE",
            "study_id":"agent-mosaic","project_id":"dsh-team-context",
            "source_anchor":ANCHOR,
            "source_archive_sha256":hashlib.sha256(blob).hexdigest(),
            "network_denied":True,
            "baseline_command":"tsx --test test/scoped-recall.test.ts on original archive; no variants",
            "tests_run":int(count.group(1)) if count else None,
            "tests_pass":int(passed.group(1)) if passed else None,
            "tests_fail":int(failed.group(1)) if failed else None,
            "runtime_s":round(time.monotonic()-started,3),
            "output_tail":output[-1600:],
            "no_measured_treatment":True,
            "notes":"Original recallScoped defaults to project-only, explicit inheritUserScope adds user with scope label and duplicate project wins. No new Agent Mosaic consumer is implemented; no measured effect.",
        }
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print("PINNED_OFFLINE_TS_BASELINE",result["status"],result["tests_run"],result["tests_pass"],result["tests_fail"])
        if proc.returncode:raise SystemExit(1)
if __name__=="__main__":
    main()
