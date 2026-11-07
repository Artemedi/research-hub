#!/usr/bin/env python3
"""Run exactly two offline-marked original Hyperresearch source/ranking suites.

This verifies executable tests at pinned source, not any author benchmark or
semantic support claimed by a citation. No model, network services or secrets.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import time

SOURCE=Path(os.environ["SOURCE"]).resolve()
PYTHON=Path(os.environ["PYTHON"]).absolute()
OUTPUT=Path(os.environ["OUTPUT"]).resolve()
PIN="aece65f9307197119629beacf8aeaf8cc80e999a"
FILES={
    "tests/test_core/test_claims_and_embed.py":
        "0d44ba20bc2ff1247135850aa0c2a294850838a979c7bfa57ab697d2d7a1a2ab",
    "tests/test_core/test_source_ranking.py":
        "1edd23c944867140cab025b0a3ff8cc8402ced4d65a297069b132bb2b38be77d",
    "src/hyperresearch/core/citecheck.py":
        "53405db780de66866e8b3131f7a99edc1341832095fcc7b0888eaae69684a465"
}


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def main():
    actual=subprocess.check_output(["git","-C",str(SOURCE),"rev-parse","HEAD"],
                                   text=True).strip()
    assert actual==PIN
    for key,digest in FILES.items():
        assert sha((SOURCE/key).read_bytes())==digest
    tests=list(FILES)[:2]
    env=dict(os.environ,PYTHONPATH=str(SOURCE/"src"),
             PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
             PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTEST_ADDOPTS",None)
    args=[str(PYTHON),"-B","-m","pytest","-q","-p","no:cacheprovider",
          *tests,"--disable-warnings","--maxfail=1"]
    started=time.monotonic()
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    proc=subprocess.run(args,cwd=SOURCE,env=env,capture_output=True,
                        text=True,timeout=55)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    result=proc.stdout+"\n"+proc.stderr
    print("TEST_EXIT",proc.returncode,"DOTS",proc.stdout.count("."),
          "OUTPUT_SHA",sha(result.encode()))
    assert proc.returncode==0,result[-3000:]
    # pytest quiet output reports dots and '[100%]'; count via its verbose
    # collection mode in a separate read-only process, with no test execution.
    count=subprocess.run([str(PYTHON),"-B","-m","pytest","--collect-only","-q",
                          "-p","no:cacheprovider",*tests],cwd=SOURCE,env=env,
                         capture_output=True,text=True,timeout=55)
    assert count.returncode==0,count.stdout[-1500:]
    matches=re.findall(r"^tests/test_core/[^:]+:\s*(\d+)\s*$", count.stdout, re.M)
    assert len(matches)==2,count.stdout[-1200:]
    collected=sum(int(x) for x in matches)
    assert collected==54,collected
    assert proc.stdout.count(".")==collected,(
        proc.stdout.count("."),collected)
    record={
        "date":"2026-11-07","study":"hyperresearch",
        "source_pin":PIN,"file_sha256":FILES,
        "original_test_paths":tests,"test_count":collected,
        "test_pass_count":collected,"pytest_exit_code":proc.returncode,
        "test_stdout_sha256":sha(result.encode()),
        "test_collected_stdout_sha256":sha(count.stdout.encode()),
        "pytest_plugin_autoload_disabled":True,
        "network_requests_made_by_test_controller":0,
        "package_install_performed":False,
        "elapsed_ms":round(1000*(time.monotonic()-started),1),
        "local_child_cpu_s":round(after.ru_utime-before.ru_utime+
                                  after.ru_stime-before.ru_stime,4),
        "source_tree_modified":False,
        "status":"PINNED_UPSTREAM_54_TESTS_PASS",
        "independent_semantic_citation_verification":False,
        "limitations":[
            "Two existing upstream suites, 54 tests, not complete project test suite",
            "Upstream test success is neither independent citation truth nor production safety",
            "Prior synthetic support false positives remain unresolved",
            "No installation of Hyperresearch or live model, network provider or target project integration",
            "CPU excludes remote workloads (none used), elapsed includes subprocess startup"
        ],
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
    print("SUMMARY",collected,collected,record["elapsed_ms"])


if __name__=="__main__":
    main()
