#!/usr/bin/env python3
"""BK-041 diagnostic: bounded, filtered root eBPF against synthetic exec only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from hashlib import sha256

D=Path("/tmp/bk041-ig-20261106")
OCI="ghcr.io/inspektor-gadget/gadget/trace_exec@sha256:9182278eb6a11b6e2d59a748674b646a8512b715d3563ec3afdf340a2f55d435"
TARGET=str(D/"bk041exec")
NEG=str(D/"bk041neg")
IG=str(D/"ig")
assert os.geteuid()!=0, "run the workload as user, privilege only tracer via sudo"
assert os.getuid()==1000
assert all(Path(f).is_file() for f in (TARGET,NEG,IG))
out=D/"diagnostic-results.json"
status=D/"diagnostic-status.json"
assert sha256((D/"ig-linux-amd64-v0.57.0.tar.gz").read_bytes()).hexdigest()=="f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1"

def save(p,v):
    tmp=p.with_suffix(".tmp")
    tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
    tmp.replace(p)

def workload(path,n):
    ids=[]
    begin=time.perf_counter()
    for _ in range(n):
        x=subprocess.Popen([path],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        assert x.wait(timeout=2)==0
        ids.append(x.pid)
    return ids, round(time.perf_counter()-begin,6)

def pid_of(evt):
    if isinstance(evt.get("proc"),dict):
        return evt["proc"].get("pid")
    return evt.get("proc.pid",evt.get("pid"))

def test(phase, filter_args):
    trace=D/f"diagnostic-{phase}-exec.jsonl"
    err=D/f"diagnostic-{phase}-ig-stderr.txt"
    baseline,baseline_s=workload(TARGET,40)
    cmd=["sudo","-n", IG,"-v","run",OCI,"--timeout","40",
         "--allowed-gadgets",OCI,
         "--uid","1000","--output","json",
         "--fields","proc.comm,proc.pid,proc.creds.uid,timestamp",
         *filter_args]
    started=time.monotonic()
    with trace.open("wb") as stdout, err.open("wb") as stderr:
        proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
        # We observed 11.4 s of cold initialization on first pilot.
        # Wait 23 s to avoid generating controls before attach.
        time.sleep(23)
        if proc.poll() is not None:
            raise RuntimeError(f"tracer exited before positive control, code {proc.returncode}. Log: {err.read_text(errors='replace')[-1200:]}")
        controls,control_s=workload(TARGET,40)
        negatives,negative_s=workload(NEG,5)
        try:
            exitcode=proc.wait(timeout=70)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
            raise RuntimeError("tracer failed to obey timeout; sent termination")
    if exitcode!=0:
        raise RuntimeError(f"tracer exited code {exitcode}. Log: {err.read_text(errors='replace')[-1400:]}")
    records=[];bad=0
    for line in trace.read_text(errors="replace").splitlines():
        try:
            e=json.loads(line)
        except json.JSONDecodeError:
            bad+=1; continue
        if isinstance(e,dict):
            records.append(e)
    pids=[pid_of(e) for e in records]
    passed=len(set(controls)&set(pids))
    falsepos=len(set(negatives)&set(pids))
    return {
        "phase":phase, "filter":filter_args, "ig_exit":exitcode,
        "expected":40,"seen_events":len(records),
        "matched_unique_pids":passed,"missing":40-passed,
        "negative_control_runs":5,"negative_control_seen":falsepos,
        "invalid_json_lines":bad,
        "baseline_seconds":baseline_s,"traced_seconds":control_s,
        "tracer_wall_seconds":round(time.monotonic()-started,3),
        "stderr_bytes":err.stat().st_size,
        "startup_wait_seconds":23,
        "trace_filename":trace.name,
        "evidence_limits":"Trace attach was not independently probed; missing events may reflect filter, readiness, or kernel loss."
    }

def main():
    save(status,{"phase":"started","started":time.time()})
    outcomes=[]
    for phase,filters in [
        ("comm",["--comm","bk041exec"]),
        ("expr",["--filter-expr.exec",'proc.comm == "bk041exec"'])
    ]:
        save(status,{"phase":phase,"observations":outcomes})
        row=test(phase,filters)
        outcomes.append(row)
        print(json.dumps(row,ensure_ascii=False),flush=True)
        save(out,{
            "study":"BK-041","date":"2026-11-06",
            "release_archive_sha256":"f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1",
            "gadget_oci_manifest_sha256":"9182278eb6a11b6e2d59a748674b646a8512b715d3563ec3afdf340a2f55d435",
            "unprivileged_workload_uid":1000,
            "scope":"Host root ig run; UID and comm/expr prefilter; synthetic C test executable only; no command arguments",
            "cases":outcomes,
            "caveats":[
                "No production process selected; filters are limited to test executable",
                "No independently measured BPF attach time; 23s readiness delay is heuristic",
                "No kernel event loss counters, RSS, kernel maps, or true p95 inference",
                "Baseline-vs-traced timings are sequential and not a randomized A/B",
                "No per-process real workload claims"
            ]
        })
        if row["matched_unique_pids"]==40 and row["negative_control_seen"]==0:
            break
    save(status,{"phase":"complete","cases":len(outcomes),"found_any":any(x["matched_unique_pids"]>0 for x in outcomes)})
    print("BK041_DIAGNOSTIC_DONE",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        save(status,{"phase":"error","error":str(exc)})
        print("BK041_DIAGNOSTIC_ERROR",str(exc),file=sys.stderr,flush=True)
        raise
