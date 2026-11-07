#!/usr/bin/env python3
"""Real pinned MCP Toolbox stdio + disposable PostgreSQL: SQL security controls.

No external database, no published ports, no host mounts, fixed SQL only.
Uses observer with minimal PostgreSQL GRANTs, independent direct SQL oracle,
false catalog shadow and planner-time IMMUTABLE timeout/EXECUTE negative controls.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

IMAGE = "docker.io/library/postgres:18"
NAME = "research-toolbox-security-20261107"
PASSWORD = "lab-synthetic-not-real"
BINARY = Path(os.environ["TOOLBOX_BIN"]).resolve()
EXPECTED_HASH = "f6fac005c39898a379523700727a2a3d0a2828f579bec22cc0efe74e0652062d"
OUT = Path(os.environ.get("OUTPUT", "toolbox-mcp-security-ab.json"))

def command(args, timeout=28):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)

def sql(query, role="postgres", db="lab", allow_fail=False):
    args = ["podman", "exec", "-i"]
    if role == "observer":
        args += ["-e", "PGPASSWORD=" + PASSWORD]
    args += [NAME, "psql", "-U", role, "-d", db, "-X", "-At", "-v", "ON_ERROR_STOP=1"]
    if role == "observer":
        args += ["-h", "127.0.0.1"]
    out = subprocess.run(args, input=query, text=True, capture_output=True, timeout=15)
    if out.returncode and not allow_fail:
        raise RuntimeError("SQL failure: " + out.stderr[-400:])
    return out

def unpack(result):
    if result.structured_content is not None:
        return result.structured_content
    if not result.content:
        return None
    payload = result.content[0].text
    try:
        return json.loads(payload)
    except (ValueError, TypeError):
        return payload

async def exercise():
    assert hashlib.sha256(BINARY.read_bytes()).hexdigest() == EXPECTED_HASH
    assert command(["podman", "container", "exists", NAME]).returncode != 0
    image = command(["podman", "image", "inspect", IMAGE, "--format", "{{.Id}}"])
    assert image.returncode == 0 and image.stdout.strip()
    result = {
        "date": "2026-11-07",
        "study": "MCP Toolbox PostgreSQL and pgbot planner-boundary follow-up",
        "toolbox_sha256": EXPECTED_HASH,
        "image": IMAGE, "image_id": image.stdout.strip(),
        "network": "none", "published_ports": 0, "host_mounts": 0,
        "credential_scope": "ephemeral synthetic only",
        "production_database_touched": False,
        "tool_allowlist": ["explain_planner", "explain_volatile", "get_safe_setting"],
    }
    with tempfile.TemporaryDirectory(prefix="research-toolbox-security-") as root:
        config = Path(root) / "tools.yaml"
        config.write_text(
            "kind: source\nname: lab-postgres\ntype: postgres\n"
            "host: 127.0.0.1\nport: \"5432\"\ndatabase: lab\n"
            "user: observer\npassword: " + PASSWORD + "\n"
            "---\nkind: tool\nname: get_safe_setting\n"
            "type: postgres-sql\nsource: lab-postgres\n"
            "description: Bind-only read of pg_catalog.pg_settings\n"
            "parameters:\n  - name: setting\n    type: string\n"
            "    description: Name of GUC\n"
            "statement: \"SELECT name, setting, unit FROM pg_catalog.pg_settings WHERE name = $1\"\n"
            "---\nkind: tool\nname: explain_planner\n"
            "type: postgres-sql\nsource: lab-postgres\n"
            "description: Planner-time IMMUTABLE test with role statement_timeout\n"
            "statement: \"EXPLAIN (FORMAT JSON) SELECT public.planner_delay()\"\n"
            "---\nkind: tool\nname: explain_volatile\n"
            "type: postgres-sql\nsource: lab-postgres\n"
            "description: VOLATILE function must not execute during EXPLAIN-only\n"
            "statement: \"EXPLAIN (FORMAT JSON) SELECT public.planner_volatile()\"\n",
            encoding="utf-8")
        config.chmod(0o600)
        started = command(["podman", "run", "--pull=never", "--rm", "-d",
                           "--name", NAME, "--network", "none", "--cpus", "2",
                           "--memory", "1g", "--pids-limit", "200",
                           "-e", "POSTGRES_PASSWORD=" + PASSWORD, IMAGE])
        if started.returncode != 0:
            raise RuntimeError("Cannot start isolated PG: " + started.stderr[-300:])
        try:
            for n in range(50):
                ready = command(["podman", "exec", NAME, "pg_isready", "-U", "postgres"])
                if ready.returncode == 0:
                    q = sql("SELECT 1;", db="postgres", allow_fail=True)
                    if q.returncode == 0:
                        break
                await asyncio.sleep(0.25)
            else:
                raise RuntimeError("PostgreSQL SQL readiness failed")
            assert sql("CREATE DATABASE lab;", db="postgres").returncode == 0
            setup = """
CREATE ROLE observer LOGIN PASSWORD 'lab-synthetic-not-real';
ALTER ROLE observer SET default_transaction_read_only = on;
ALTER ROLE observer SET statement_timeout = '80ms';
CREATE TABLE public.fixture (id integer PRIMARY KEY);
INSERT INTO public.fixture VALUES (1);
REVOKE ALL ON TABLE public.fixture FROM PUBLIC;
CREATE SCHEMA shadow;
CREATE TABLE shadow.pg_settings (name text, setting text, unit text);
INSERT INTO shadow.pg_settings VALUES ('max_connections','999999','');
GRANT USAGE ON SCHEMA shadow TO observer;
GRANT SELECT ON shadow.pg_settings TO observer;
ALTER ROLE observer SET search_path = shadow, pg_catalog;
CREATE FUNCTION public.planner_delay() RETURNS integer
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
 PERFORM pg_sleep(0.30);
 RAISE NOTICE 'SYNTHETIC_PLANNER_DELAY';
 RETURN 17;
END $$;
CREATE FUNCTION public.planner_volatile() RETURNS integer
LANGUAGE plpgsql VOLATILE AS $$
BEGIN
 PERFORM pg_sleep(0.30);
 RAISE NOTICE 'SYNTHETIC_VOLATILE_DELAY';
 RETURN 17;
END $$;
REVOKE ALL ON FUNCTION public.planner_delay() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.planner_delay() TO observer;
GRANT EXECUTE ON FUNCTION public.planner_volatile() TO observer;
"""
            assert sql(setup).returncode == 0
            direct = sql("SELECT setting FROM pg_catalog.pg_settings WHERE name='max_connections';",
                         role="observer").stdout.strip()
            shadow = sql("SELECT setting FROM pg_settings WHERE name='max_connections';",
                         role="observer").stdout.strip()
            assert direct.isdigit() and shadow == "999999" and direct != shadow, (direct, shadow)
            assert sql("SHOW statement_timeout;", role="observer").stdout.strip() == "80ms"
            denied = sql("BEGIN READ WRITE; INSERT INTO public.fixture VALUES (2);",
                         role="observer", allow_fail=True)
            assert denied.returncode != 0
            assert sql("SELECT COUNT(*) FROM public.fixture;").stdout.strip() == "1"
            cp = command(["podman", "cp", str(BINARY), NAME + ":/tmp/toolbox"])
            assert cp.returncode == 0, cp.stderr[-250:]
            cp = command(["podman", "cp", str(config), NAME + ":/tmp/tools.yaml"])
            assert cp.returncode == 0, cp.stderr[-250:]
            p = StdioServerParameters(
                command="podman", args=["exec", "-i", NAME, "/tmp/toolbox",
                                       "--config", "/tmp/tools.yaml", "--stdio"])
            controls = []
            async with stdio_client(p) as (rd, wr):
                async with ClientSession(rd, wr) as client:
                    await asyncio.wait_for(client.initialize(), timeout=18)
                    manifest = await asyncio.wait_for(client.list_tools(), timeout=12)
                    names = sorted(x.name for x in manifest.tools)
                    assert names == sorted(result["tool_allowlist"]), names
                    # Catalog schema shadow is deliberately ahead of pg_catalog
                    setting = await asyncio.wait_for(client.call_tool(
                        "get_safe_setting", {"setting": "max_connections"}), timeout=12)
                    assert not setting.is_error
                    value = unpack(setting)
                    assert isinstance(value, dict) and value.get("setting") == direct, value
                    controls.append({"name": "qualified_catalog_ignores_shadow",
                                     "passed": True, "observed_equals_real": True,
                                     "shadow_value": shadow, "real_value": direct})
                    negatives = (
                        "max_connections'; DROP TABLE public.fixture; --",
                        "max_connections' OR '1'='1",
                        "max_connections; SELECT pg_sleep(3)",
                        "../pg_settings",
                        "MAX_CONNECTIONS",
                        "not_a_real_setting_20261107",
                    )
                    for bad in negatives:
                        r = await asyncio.wait_for(client.call_tool(
                            "get_safe_setting", {"setting": bad}), timeout=12)
                        if not r.is_error:
                            got = unpack(r)
                            assert got in (None, [], {}), (bad, got)
                        controls.append({
                            "name": "injection_or_invalid_name",
                            "input_sha256": hashlib.sha256(bad.encode()).hexdigest(),
                            "passed": True, "mcp_error": bool(r.is_error)
                        })
                    # A mislabelled IMMUTABLE function is evaluated in the planner.
                    start = time.perf_counter()
                    r = await asyncio.wait_for(client.call_tool("explain_planner", {}),
                                               timeout=12)
                    elapsed = round((time.perf_counter() - start)*1000, 2)
                    details = str(unpack(r))
                    assert r.is_error and "statement timeout" in details.lower(), details[:250]
                    controls.append({"name": "planner_timeout_via_real_mcp",
                                     "passed": True, "mcp_error": True,
                                     "contains_timeout": True,
                                     "elapsed_ms": elapsed})
                    start = time.perf_counter()
                    r = await asyncio.wait_for(client.call_tool("explain_volatile", {}),
                                               timeout=12)
                    elapsed = round((time.perf_counter() - start)*1000, 2)
                    assert not r.is_error, str(unpack(r))[:250]
                    controls.append({"name": "volatile_explain_no_function_exec",
                                     "passed": True, "elapsed_ms": elapsed})
                    assert sql("REVOKE EXECUTE ON FUNCTION public.planner_delay() FROM observer;").returncode == 0
                    r = await asyncio.wait_for(client.call_tool("explain_planner", {}),
                                               timeout=12)
                    denied_text = str(unpack(r))
                    assert r.is_error and "permission denied" in denied_text.lower(), denied_text[:250]
                    controls.append({"name": "revoke_execute_via_real_mcp",
                                     "passed": True, "mcp_error": True})
                    r = await asyncio.wait_for(client.call_tool(
                        "get_safe_setting", {"setting": "max_connections"}), timeout=12)
                    assert not r.is_error and unpack(r).get("setting") == direct
                    controls.append({"name": "mcp_connection_recovers_after_errors",
                                     "passed": True})
            after = sql("SELECT COUNT(*) FROM public.fixture;").stdout.strip()
            assert after == "1"
            result.update({
                "direct_catalog_value": direct,
                "shadow_catalog_value": shadow,
                "observer_insert_denied": True,
                "fixture_count_before_after": "1/1",
                "mcp_tool_count": len(names),
                "checks_total": len(controls),
                "checks_passed": sum(x["passed"] for x in controls),
                "checks": controls,
                "limits": [
                    "A single allowlisted synthetic tool config; not arbitrary agent-generated SQL",
                    "Planner function is artificial PL/pgSQL with pg_sleep and no destructive effects",
                    "Strict statement_timeout applies to this PostgreSQL role and simple test",
                    "Namespace shadow is an isolated fake catalog table, not a real attack on privileged code",
                    "No actual pgbot executable, Wiki_PG integration, network, privileged extensions or clinical data",
                    "Wall-clock timings contain subprocess/stdio overhead and are not production latency"
                ]
            })
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
            print("MCP_BOUNDARY_PASS", len(controls), "real_guc", direct, "shadow", shadow,
                  flush=True)
        finally:
            command(["podman", "stop", "--time", "2", NAME], timeout=25)
            if command(["podman", "container", "exists", NAME]).returncode == 0:
                command(["podman", "rm", "-f", NAME], timeout=20)
            assert command(["podman", "container", "exists", NAME]).returncode != 0

if __name__ == "__main__":
    asyncio.run(exercise())
