#!/usr/bin/env python3
"""Isolated PostgreSQL planner-time function delay versus timeout and EXECUTE grant.

Only synthetic functions inside a disposable rootless offline Postgres container.
No remote database connections, published ports, host mounts, or production roles.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

IMAGE = "docker.io/library/postgres:18"
NAME = "research-pgplanner-timeout-20261107"
OUT = Path(os.environ.get("OUTPUT", "pgplanner-timeout-ab.json"))

def call(args, input_text=None, timeout=35):
    return subprocess.run(args, input=input_text, text=True, capture_output=True, timeout=timeout)

def query(sql, timeout=15):
    start = time.monotonic()
    p = call(["podman", "exec", "-i", NAME, "psql", "-U", "postgres", "-d",
              "postgres", "-X", "-q", "-v", "ON_ERROR_STOP=1"], sql, timeout)
    return {
        "exit_code": p.returncode,
        "elapsed_ms": round((time.monotonic() - start) * 1000, 2),
        "planner_notice": "SYNTHETIC_PLANNER_DELAY" in p.stderr,
        "statement_timeout": "canceling statement due to statement timeout" in p.stderr,
        "permission_denied": "permission denied for function planner_delay" in p.stderr,
        "stdout_sha256": hashlib.sha256(p.stdout.encode()).hexdigest(),
        "stderr_tail": p.stderr[-400:]
    }

def main():
    assert call(["podman", "container", "exists", NAME]).returncode != 0, "name collision"
    inspected = call(["podman", "image", "inspect", IMAGE, "--format", "{{.Id}}"])
    assert inspected.returncode == 0 and inspected.stdout.strip(), "pinned image not local"
    result = {
        "date": "2026-11-07",
        "study": "pgbot / PostgreSQL agent SQL security",
        "experiment": "EXPLAIN (FORMAT JSON) read-only planner-time delay; timeout and GRANT/REVOKE",
        "image": IMAGE, "image_id": inspected.stdout.strip(),
        "network": "none", "published_ports": 0, "host_mounts": 0,
        "production_database_touched": False, "credentials": "disposable synthetic only"
    }
    launch = call(["podman", "run", "--pull=never", "--rm", "-d", "--name", NAME,
                   "--network", "none", "--cpus", "2", "--memory", "1g",
                   "--pids-limit", "200", "-e", "POSTGRES_PASSWORD=lab-synthetic-only", IMAGE])
    if launch.returncode:
        raise RuntimeError("Container startup: " + launch.stderr[-500:])
    try:
        for i in range(40):
            ready = call(["podman", "exec", NAME, "pg_isready", "-U", "postgres"], timeout=8)
            if ready.returncode == 0:
                version = query("SHOW server_version_num;")
                if version["exit_code"] == 0:
                    break
            time.sleep(0.3)
        else:
            raise RuntimeError("Postgres never accepted SQL queries")
        setup = query("""CREATE ROLE observer;
CREATE FUNCTION public.planner_delay() RETURNS integer
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
  PERFORM pg_sleep(0.30);
  RAISE NOTICE 'SYNTHETIC_PLANNER_DELAY';
  RETURN 17;
END $$;
CREATE FUNCTION public.planner_delay_volatile() RETURNS integer
LANGUAGE plpgsql VOLATILE AS $$
BEGIN
  PERFORM pg_sleep(0.30);
  RAISE NOTICE 'SYNTHETIC_VOLATILE_DELAY';
  RETURN 17;
END $$;
REVOKE ALL ON FUNCTION public.planner_delay() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.planner_delay() TO observer;
GRANT EXECUTE ON FUNCTION public.planner_delay_volatile() TO observer;
""")
        assert setup["exit_code"] == 0, setup["stderr_tail"]
        cases = {}
        cases["no_timeout"] = query("""SET ROLE observer;
BEGIN READ ONLY;
SET LOCAL statement_timeout = '0';
EXPLAIN (FORMAT JSON) SELECT public.planner_delay();
COMMIT;""")
        cases["strict_timeout"] = query("""SET ROLE observer;
BEGIN READ ONLY;
SET LOCAL statement_timeout = '80ms';
EXPLAIN (FORMAT JSON) SELECT public.planner_delay();
ROLLBACK;""")
        cases["volatile_explain_control"] = query("""SET ROLE observer;
BEGIN READ ONLY;
SET LOCAL statement_timeout = '80ms';
EXPLAIN (FORMAT JSON) SELECT public.planner_delay_volatile();
COMMIT;""")
        revoke = query("REVOKE EXECUTE ON FUNCTION public.planner_delay() FROM observer;")
        assert revoke["exit_code"] == 0
        cases["execute_revoked"] = query("""SET ROLE observer;
BEGIN READ ONLY;
EXPLAIN (FORMAT JSON) SELECT public.planner_delay();
ROLLBACK;""")
        assert cases["no_timeout"]["exit_code"] == 0
        assert cases["no_timeout"]["planner_notice"]
        assert cases["no_timeout"]["elapsed_ms"] >= 270
        assert cases["strict_timeout"]["exit_code"] != 0
        assert cases["strict_timeout"]["statement_timeout"]
        assert cases["strict_timeout"]["elapsed_ms"] < 290
        assert cases["volatile_explain_control"]["exit_code"] == 0
        assert not cases["volatile_explain_control"]["planner_notice"]
        assert cases["volatile_explain_control"]["elapsed_ms"] < 290
        assert cases["execute_revoked"]["exit_code"] != 0
        assert cases["execute_revoked"]["permission_denied"]
        assert not cases["execute_revoked"]["planner_notice"]
        result["cases"] = cases
        result["conclusion"] = (
            "A mislabeled IMMUTABLE function can impose execution latency during "
            "EXPLAIN READ ONLY; statement_timeout and role EXECUTE grants bound "
            "the tested case. EXPLAIN without ANALYZE is not an execution sandbox."
        )
        result["limits"] = [
            "Only synthetic PL/pgSQL RAISE NOTICE and pg_sleep; no destructive side effects",
            "The real pgbot binary, arbitrary SQL tool wrappers and MCP clients were not invoked",
            "Wall time includes psql/podman overhead; this is not a performance benchmark",
            "No network, file, privilege escalation or adversarial extension execution tested",
            "Statement timeout and EXECUTE revocation are complementary controls, not a universal policy"
        ]
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({k: {"exit": v["exit_code"], "ms": v["elapsed_ms"],
                              "notice": v["planner_notice"], "timeout": v["statement_timeout"],
                              "denied": v["permission_denied"]}
                          for k,v in cases.items()}))
    finally:
        stop = call(["podman", "stop", "--time", "2", NAME], timeout=25)
        if stop.returncode:
            call(["podman", "rm", "-f", NAME], timeout=25)
        assert call(["podman", "container", "exists", NAME]).returncode != 0

if __name__ == "__main__":
    main()
