#!/usr/bin/env python3
"""BK-041 disposable synthetic Podman eBPF probe. Never run on production.
WARNING: IG --output json includes process arguments/paths even with --fields.
The raw trace files are sensitive; NEVER publish them; only publish aggregates.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

D=Path("/tmp/bk041-ig-20261106")
BIN=str(D/"ig")
OCI="ghcr.io/inspektor-gadget/gadget/trace_exec@sha256:9182278eb6a11b6e2d59a748674b646a8512b715d3563ec3afdf340a2f55d435"
IMAGE="docker.io/library/node:22"
NAME="bk041-ig-synthetic-20261106"
SOCKET="/run/user/1000/podman/podman.sock"
OUT=D/"container-probe-results.json"
STATUS=D/"container-probe-status.json"
assert os.getuid()==1000 and os.geteuid()==1000
assert Path(SOCKET).is_socket() if hasattr(Path(SOCKET),"is_socket") else os.path.exists(SOCKET)
assert subprocess.run(["podman","image","exists",IMAGE]).returncode==0
assert subprocess.run(["podman","container","exists",NAME]).returncode!=0,"test container name is already in use; refuse to touch it"
expected_hash="f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1"
assert hashlib.sha256((D/"ig-linux-amd64-v0.57.0.tar.gz").read_bytes()).hexdigest()==expected_hash

def publish(path,data):
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    tmp.replace(path)

def container_started():
    cmd=["podman","run","-d","--rm","--pull=never",
         "--name",NAME,"--network=none","--read-only",
         "--cap-drop=all","--security-opt=no-new-privileges",
         "--pids-limit=64","--memory=256m","--cpus=1",
         "--tmpfs","/tmp:rw,exec,nosuid,size=16m",
         IMAGE,"sh","-c","sleep 180"]
    result=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=25)
    assert result.returncode==0,"container start failed: "+result.stderr[-1100:]

def cleanup_container():
    # The name was asserted unused before this test, so only our own container is affected.
    subprocess.run(["podman","rm","-f",NAME],stdin=subprocess.DEVNULL,capture_output=True,timeout=15)

def controlled_execs():
    sh="""
set -eu
cp /usr/bin/true /tmp/bk041exec
cp /usr/bin/true /tmp/bk041neg
i=0
while [ "$i" -lt 40 ]; do
    /tmp/bk041exec
    printf 'EXPECTED\\n'
    i=$((i+1))
done
i=0
while [ "$i" -lt 5 ]; do
    /tmp/bk041neg
    printf 'NEGATIVE\\n'
    i=$((i+1))
done
"""
    start=time.monotonic()
    proc=subprocess.run(["podman","exec",NAME,"sh","-c",sh],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=25)
    duration=round(time.monotonic()-start,5)
    if proc.returncode!=0:
        raise RuntimeError("Synthetic workload failed: "+proc.stderr[-1000:])
    positive=proc.stdout.splitlines().count("EXPECTED")
    negative=proc.stdout.splitlines().count("NEGATIVE")
    assert positive==40 and negative==5,(positive,negative)
    return duration,positive,negative

def run_once(phase,filters,baseline_seconds):
    trace=D/f"container-{phase}-events.jsonl"
    error=D/f"container-{phase}-stderr.txt"
    cmd=["sudo","-n",BIN,"-v","run",OCI,"--timeout","20",
         "--allowed-gadgets",OCI,"--pull","never",
         "--runtimes","podman","--podman-socketpath",SOCKET,
         "--fields","proc.comm,proc.pid,proc.parent.pid,proc.creds.uid,timestamp",
         "--output","json",*filters]
    p=None
    started=time.monotonic()
    attach_ts=None
    try:
        # Rootless Podman API discovers existing containers but does not notify ig of new ones.
        container_started()
        with trace.open("wb") as out, error.open("wb") as err:
            p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
            for _ in range(250):
                if p.poll() is not None:
                    raise RuntimeError("IG exited early "+str(p.returncode)+": "+error.read_text(errors="replace")[-1500:])
                try: content=error.read_text(errors="replace")
                except OSError: content=""
                if "msg=running..." in content:
                    attach_ts=time.monotonic()
                    break
                time.sleep(.1)
            if attach_ts is None:
                raise RuntimeError("IG did not report ready within 25 sec")
            time.sleep(.5)
            workload_s,pos,neg=controlled_execs()
            try: rc=p.wait(timeout=35)
            except subprocess.TimeoutExpired:
                p.terminate()
                try:p.wait(timeout=4)
                except subprocess.TimeoutExpired:p.kill();p.wait()
                raise RuntimeError("IG failed to terminate at configured timeout")
        if rc!=0:
            raise RuntimeError("IG exited "+str(rc)+": "+error.read_text(errors="replace")[-1600:])
        events=[];bad=0
        for line in trace.read_text(errors="replace").splitlines():
            try:v=json.loads(line)
            except json.JSONDecodeError:bad+=1;continue
            if isinstance(v,dict):events.append(v)
        def get_comm(event):
            p=event.get("proc")
            if isinstance(p,dict):return p.get("comm")
            return event.get("proc.comm",event.get("comm"))
        def get_pid(event):
            p=event.get("proc")
            if isinstance(p,dict):return p.get("pid")
            return event.get("proc.pid",event.get("pid"))
        comms=[get_comm(e) for e in events]
        pids=[get_pid(e) for e in events]
        matched=sum(c=="bk041exec" for c in comms)
        wrong=sum(c=="bk041neg" for c in comms)
        return {
            "phase":phase,"filter":filters,"expected_exec":pos,"negative_exec":neg,
            "observed_events":len(events),"matched_comm":matched,
            "unexpected_negative":wrong,
            "distinct_event_pids":len(set(str(p) for p in pids if p is not None)),
            "unparsed_json_lines":bad,
            "baseline_workload_seconds":baseline_seconds,
            "traced_workload_seconds":workload_s,
            "relative_workload_delta_pct":round((workload_s/baseline_seconds-1)*100,2) if baseline_seconds else None,
            "ig_wall_seconds":round(time.monotonic()-started,3),
            "ig_ready_lag_seconds":round(attach_ts-started,3),
            "ig_exit":rc,
            "trace_sha256":hashlib.sha256(trace.read_bytes()).hexdigest(),
            "raw_trace_only_synthetic_filtered":True,
        }
    finally:
        cleanup_container()
        if p and p.poll() is None:
            p.terminate()
            try:p.wait(timeout=4)
            except subprocess.TimeoutExpired:p.kill();p.wait()

def main():
    publish(STATUS,{"state":"baseline"})
    container_started()
    try:base_s,positive,negative=controlled_execs()
    finally:cleanup_container()
    attempts=[]
    filters_list=[("comm",["--comm","bk041exec"]),
                  ("expr",["--filter.exec","proc.comm==bk041exec"])]
    for phase,flt in filters_list:
        publish(STATUS,{"state":"running","phase":phase,"completed":len(attempts)})
        row=run_once(phase,flt,base_s)
        attempts.append(row)
        print(json.dumps(row,ensure_ascii=False),flush=True)
        publish(OUT,{"study":"BK-041","version":"v0.57.0",
            "ig_archive_sha256":expected_hash,
            "oci_digest":"9182278eb6a11b6e2d59a748674b646a8512b715d3563ec3afdf340a2f55d435",
            "scope":"Rootless Podman demo, network=none, 40 synthetic exec and 5 negative, root IG with OCI pinned, no argv",
            "trials":attempts,
            "limits":["One baseline, nonrandomized latency; no causal overhead estimate",
                      "No kernel dropped-event counter, BPF map audit, systemwide CPU/IO",
                      "Not a database/production test",
                      "Host processes outside containers were not traced"]})
        if row["matched_comm"]>0:
            # Repeat with the successful filter; total 5 runs, stop if first succeeded but degraded badly.
            for index in range(2,6):
                name=f"repeat-{index}"
                publish(STATUS,{"state":"running","phase":name,"completed":len(attempts)})
                r=run_once(name,flt,base_s)
                attempts.append(r)
                publish(OUT,{**json.loads(OUT.read_text()),"trials":attempts})
                print(json.dumps(r,ensure_ascii=False),flush=True)
            break
    publish(STATUS,{"state":"finished","attempts":len(attempts),"any_events":any(x["observed_events"]>0 for x in attempts)})
    print("BK041_CONTAINER_LAB_DONE",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        publish(STATUS,{"state":"failed","error":str(e)})
        print("BK041_CONTAINER_LAB_FAILED:",str(e),file=sys.stderr,flush=True)
        raise
