#!/usr/bin/env python3
"""Isolated PostgreSQL 18 EXPLAIN planner-time function evaluation probe.

Rootless Podman, no network/published ports, no host database or production
credentials. Creates and deletes only an ephemeral postgres:18 container.
"""
import hashlib,json,os,pathlib,subprocess,time
OUT=pathlib.Path(os.environ.get("OUTPUT",str(pathlib.Path.cwd()/"pgbot-explain-plan-probe.json")))
NAME="research-pgplanner-20261107"
IMAGE="docker.io/library/postgres:18"
def shell(args,stdin=None,timeout=30):
    p=subprocess.run(args,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    return p
def psql(sql):
    return shell(["podman","exec","-i",NAME,"psql","-U","postgres","-d","postgres",
                  "-X","-q","-v","ON_ERROR_STOP=1"],sql,timeout=25)
def notice(sql):
    start=time.monotonic()
    p=psql(sql)
    return {"exit_code":p.returncode,"elapsed_ms":round((time.monotonic()-start)*1000),
            "notice_detected":"PLANNER_IMMUTABLE_CALLED" in p.stderr or "PLANNER_VOLATILE_CALLED" in p.stderr,
            "stdout_sha256":hashlib.sha256(p.stdout.encode()).hexdigest(),
            "stderr_tail":p.stderr[-600:]}
def main():
    assert shell(["podman","container","exists",NAME],timeout=10).returncode!=0, "container-name collision"
    image=shell(["podman","image","inspect",IMAGE,"--format","{{.Id}}"],timeout=15)
    assert image.returncode==0 and image.stdout.strip()
    result={"date":"2026-11-07","study":"pgbot","experiment":"EXPLAIN-only read-only transaction planner-time execution",
      "source_repo":"pgrundev/pgbot",
      "source_pin":"826531fefd7d13b4381327acd4cce5be98bd71eb",
      "source_observation":"internal/plan/fetch.go calls ReadOnlyTx and SimpleQuery of EXPLAIN (FORMAT JSON) SELECT",
      "image":IMAGE,"image_id":image.stdout.strip(),"network":"none","published_ports":0,
      "credentials":"ephemeral synthetic only",
      "production_db_touched":False}
    launch=["podman","run","--pull=never","--rm","-d","--name",NAME,"--network","none",
      "--memory","1g","--cpus","2","--pids-limit","200",
      "-e","POSTGRES_PASSWORD=synthetic-local-fixture",
      IMAGE]
    start=shell(launch,timeout=35)
    if start.returncode:
        raise RuntimeError("Container startup blocked: "+start.stderr[-500:])
    try:
        ready=False
        for i in range(38):
            p=shell(["podman","exec",NAME,"pg_isready","-U","postgres"],timeout=8)
            if p.returncode==0:ready=True;break
            time.sleep(0.4)
        if not ready:raise RuntimeError("Postgres never became ready")
        version=psql("SELECT current_setting('server_version_num');")
        assert version.returncode==0
        result["server_version_num"]=next(x.strip() for x in version.stdout.splitlines() if x.strip().isdigit())
        setup=psql("""CREATE FUNCTION planner_immutable() RETURNS integer
            LANGUAGE plpgsql IMMUTABLE AS $$
            BEGIN
              RAISE NOTICE 'PLANNER_IMMUTABLE_CALLED';
              RETURN 42;
            END $$;
            CREATE FUNCTION planner_volatile() RETURNS integer
            LANGUAGE plpgsql VOLATILE AS $$
            BEGIN
              RAISE NOTICE 'PLANNER_VOLATILE_CALLED';
              RETURN 42;
            END $$;""")
        assert setup.returncode==0,setup.stderr[-300:]
        statements={
          "immutable_explain_read_only":
             "BEGIN READ ONLY; EXPLAIN (FORMAT JSON) SELECT planner_immutable(); ROLLBACK;",
          "volatile_explain_read_only":
             "BEGIN READ ONLY; EXPLAIN (FORMAT JSON) SELECT planner_volatile(); ROLLBACK;",
          "pg_sleep_explain_read_only":
             "BEGIN READ ONLY; EXPLAIN (FORMAT JSON) SELECT pg_sleep(2); ROLLBACK;",
        }
        result["cases"]={k:notice(q) for k,q in statements.items()}
        assert all(r["exit_code"]==0 for r in result["cases"].values())
        assert result["cases"]["immutable_explain_read_only"]["notice_detected"] is True
        assert result["cases"]["volatile_explain_read_only"]["notice_detected"] is False
        assert result["cases"]["pg_sleep_explain_read_only"]["notice_detected"] is False
        result["conclusion"]="Read-only plan-only EXPLAIN can invoke a user-defined IMMUTABLE function during constant folding. This does not mean the SELECT plan is executed wholesale; it invalidates an absolute assertion that no user function body can run while planning."
        result["limits"]=[
           "Only a synthetic user-defined IMMUTABLE function with RAISE NOTICE was tested in PostgreSQL 18",
           "No destructive side effect, no file access, network, or privilege escalation was attempted",
           "Real risk depends on EXECUTE rights, trusted language/procedure implementation and connection role",
           "pgbot code was reviewed at its pinned commit, but its binary was not used in this isolated SQL proof",
           "Planning itself may evaluate IMMUTABLE expressions, even inside a READ ONLY transaction"
        ]
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print("POSTGRES_PLANNER_PROOF_PASS",result["server_version_num"],result["image_id"][:20])
        for k,v in result["cases"].items():
            print("CASE",k,"notice_detected",v["notice_detected"],"elapsed_ms",v["elapsed_ms"])
    finally:
        stop=shell(["podman","stop","--time","2",NAME],timeout=20)
        if stop.returncode:
            shell(["podman","rm","-f",NAME],timeout=20)
        assert shell(["podman","container","exists",NAME],timeout=8).returncode!=0, "Ephemeral container survived cleanup"
if __name__=="__main__":main()
