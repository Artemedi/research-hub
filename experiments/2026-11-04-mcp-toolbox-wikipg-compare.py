#!/usr/bin/env python3
"""Compare live Toolbox and snapshot Wiki_PG MCP stdio contracts on a disposable PG lab.

Requires the lab setup detailed in the companion research report. No LLMs or public DB.
"""
import argparse
import asyncio
import json
import os
import statistics
import subprocess
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True,
                   help="Lab folder containing fake-wiki, Wiki_PG, venv and oracle-settings.json")
    p.add_argument("--container", default="trin-toolbox-lab-20261104")
    p.add_argument("--repetitions", type=int, default=20)
    p.add_argument("--staleness-check", action="store_true",
                   help="Change only disposable lab global work_mem and restore it")
    return p.parse_args()


def payload(result):
    if result.structuredContent is not None:
        return result.structuredContent
    if not result.content:
        return None
    return json.loads(result.content[0].text)


def oracle_from_pg(container):
    query = """
        SELECT name, setting, COALESCE(unit, '')
        FROM pg_catalog.pg_settings
        WHERE name IN ('max_connections', 'random_page_cost', 'wal_level', 'work_mem')
        ORDER BY name
    """
    command = ["podman", "exec", container, "psql", "-U", "postgres", "-d", "lab",
               "-X", "-At", "-F", "|", "-c", query]
    p = subprocess.run(command, capture_output=True, text=True, check=True)
    return {a: {"name": a, "setting": b, "unit": c}
            for a, b, c in (line.split("|") for line in p.stdout.strip().splitlines())}


def fixture_integrity(container):
    query = "SELECT count(*), min(id), max(id) FROM public.fixture"
    p = subprocess.run(["podman", "exec", container, "psql", "-U", "postgres",
                        "-d", "lab", "-X", "-At", "-c", query],
                       capture_output=True, text=True, check=True)
    return p.stdout.strip()


def summarize(ms):
    return {
        "n": len(ms),
        "median_ms": round(statistics.median(ms), 3),
        "min_ms": round(min(ms), 3),
        "max_ms": round(max(ms), 3),
        "p95_observed_ms": round(sorted(ms)[int(0.95*(len(ms)-1))], 3),
    }


async def staleness_probe(container, descriptors, old_value):
    """Modify only the disposable lab's global work_mem, then restore it."""
    if container != "trin-toolbox-lab-20261104":
        raise AssertionError("Refusing ALTER SYSTEM on a non-lab container")

    def execute(sql):
        p = subprocess.run(
            ["podman", "exec", container, "psql", "-U", "postgres", "-d", "lab",
             "-X", "-v", "ON_ERROR_STOP=1", "-c", sql],
            capture_output=True, text=True, check=True,
        )
        return p.stdout.strip()

    observed = {}
    try:
        execute("ALTER SYSTEM SET work_mem TO '8MB'")
        execute("SELECT pg_reload_conf()")
        for _ in range(40):
            if oracle_from_pg(container)["work_mem"]["setting"] == "8192":
                break
            await asyncio.sleep(0.1)
        assert oracle_from_pg(container)["work_mem"]["setting"] == "8192"
        for label, (params, tool) in descriptors.items():
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    kwargs = ({"setting":"work_mem"} if label == "toolbox"
                              else {"host":"LAB_001", "parameter":"work_mem"})
                    data = payload(await client.call_tool(tool, kwargs))
                    observed[label] = data["setting"]
        assert observed == {"toolbox":"8192", "wikipg":old_value}, observed
        return {"status":"PASS", "updated_live_pg_setting":observed["toolbox"],
                "unchanged_latest_wiki_snapshot":observed["wikipg"],
                "snapshot_stale_as_expected":True}
    finally:
        execute("ALTER SYSTEM RESET work_mem")
        execute("SELECT pg_reload_conf()")
        for _ in range(40):
            if oracle_from_pg(container)["work_mem"]["setting"] == old_value:
                break
            await asyncio.sleep(0.1)
        assert oracle_from_pg(container)["work_mem"]["setting"] == old_value


async def main(args):
    if args.repetitions < 5:
        raise ValueError("at least five repetitions required")
    root = args.root.resolve()
    oracle = oracle_from_pg(args.container)
    generated = json.loads((root / "oracle-settings.json").read_text())
    assert generated == oracle, "live database differs from captured lab fixture"
    before = fixture_integrity(args.container)

    descriptors = {
        "toolbox": (
            StdioServerParameters(
                command="podman",
                args=["exec", "-i", args.container, "/usr/local/bin/toolbox",
                      "--config", "/tmp/tools.yaml", "--stdio"]
            ),
            "get_live_pg_setting",
        ),
        "wikipg": (
            StdioServerParameters(
                command=str(root / "venv/bin/python"),
                args=[str(root / "Wiki_PG/Wiki_PG/ingestion/mcp_wiki_server.py")],
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                     "WIKIPG_WIKI_ROOT": str(root / "fake-wiki/Wiki_PG")}
            ),
            "get_postgres_setting",
        ),
    }
    readings = {}
    for label, (params, tool) in descriptors.items():
        init_start = time.perf_counter_ns()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                init_ms = (time.perf_counter_ns() - init_start) / 1e6
                manifest = await client.list_tools()
                names = {x.name for x in manifest.tools}
                assert tool in names, (label, names)
                ann = next(x.annotations for x in manifest.tools if x.name == tool)
                metadata = ann.model_dump(exclude_none=True) if ann else {}

                results = {}
                for name, expected in oracle.items():
                    latencies, bytesizes = [], []
                    for iteration in range(args.repetitions+2):
                        kwargs = ({"setting": name} if label == "toolbox"
                                  else {"host": "LAB_001", "parameter": name})
                        st = time.perf_counter_ns()
                        result = await client.call_tool(tool, kwargs)
                        elapsed = (time.perf_counter_ns() - st) / 1e6
                        assert not result.isError, (label, name, str(result)[:1000])
                        obj = payload(result)
                        assert isinstance(obj, dict), (label, name, obj)
                        for key in ("name", "setting", "unit"):
                            actual = obj["parameter"] if key == "name" and label == "wikipg" else obj.get(key)
                            if key == "unit":
                                actual = actual or ""
                            assert actual == expected[key], (label, name, key, actual, expected[key])
                        if label == "wikipg":
                            assert obj["status"] == "ok"
                            assert obj["captured_at"] == "2026-11-04T07:00:00"
                            assert "sysconfig_report_2026-11-04_07-00-00" in obj["source_file"]
                            if name == "work_mem":
                                assert obj["memory_conversion"]["setting"]["MiB"] == "4"
                        if iteration >= 2:
                            latencies.append(elapsed)
                            bytesizes.append(len(result.model_dump_json().encode("utf-8")))
                    results[name] = {"passes": args.repetitions,
                                     "call_latency": summarize(latencies),
                                     "sdk_result_json_bytes_median": int(statistics.median(bytesizes))}
                # Missing / unsafe request protections are not equivalent across sources.
                bad = "work_mem'; DROP TABLE public.fixture; --"
                badargs = ({"setting": bad} if label == "toolbox"
                           else {"host": "LAB_001", "parameter": bad})
                invalid = await client.call_tool(tool, badargs)
                obj = payload(invalid)
                if label == "toolbox":
                    # Fixed SQL + bind parameters; not a syntactically executable injection.
                    assert not invalid.isError
                    assert obj == [] or obj in ({}, None), obj
                    invalid_status = "parameterized_no_rows"
                else:
                    assert invalid.isError
                    assert obj["status"] == "invalid_parameter"
                    invalid_status = "invalid_parameter_error"

                historical = None
                missing_snapshot = None
                if label == "wikipg":
                    old = await client.call_tool(
                        tool, {"host":"LAB_001", "parameter":"work_mem",
                               "snapshot_date":"2026-11-03"}
                    )
                    record = payload(old)
                    assert not old.isError
                    assert record["setting"] == "8192"
                    assert record["captured_at"] == "2026-11-03T07:00:00"
                    assert "2026-11-03" in record["source_file"]
                    historical = {"setting": record["setting"],
                                  "captured_at": record["captured_at"],
                                  "source_provenance": True}
                    missing = await client.call_tool(
                        tool, {"host":"LAB_001", "parameter":"work_mem",
                               "snapshot_date":"2026-11-01"}
                    )
                    missing_obj = payload(missing)
                    assert missing_obj.get("status") == "no_snapshot"
                    missing_snapshot = {"status":"no_snapshot",
                                        "isError":bool(missing.isError)}
                readings[label] = {
                    "version_or_code": (
                        "mcp-toolbox 1.15.0+binary.linux.amd64.8e8e569"
                        if label == "toolbox" else "Wiki_PG source d55721bb99bf"),
                    "initialization_ms_including_transport": round(init_ms,3),
                    "server_tool_count": len(names),
                    "target_tool_annotations": metadata,
                    "same_oracle_results": results,
                    "injection_like_input": invalid_status,
                    "historical_2026_11_03": historical,
                    "missing_2026_11_01": missing_snapshot,
                }
    staleness = (await staleness_probe(args.container, descriptors,
                                       oracle["work_mem"]["setting"])
                 if args.staleness_check else None)
    after = fixture_integrity(args.container)
    assert before == after, (before, after)
    print(json.dumps({
        "status":"PASS",
        "oracle":oracle,
        "repetitions_per_tool_and_setting":args.repetitions,
        "test_dimensions":["value_match","time_scope","bound_parameter","lab_data_integrity",
                           "stdio_initialization","warm_rpc_latency","response_size"],
        "fixture_rows_before_after": {"before":before,"after":after},
        "results":readings,
        "staleness_test":staleness,
        "constraints":[
            "Wiki snapshot for latest date was intentionally generated from the same live oracle.",
            "Not an end-to-end question answering or model accuracy benchmark.",
            "Not apples-to-apples throughput: Toolbox is Go in Podman, Wiki_PG is host Python.",
            "Only four GUC names; one synthetic older snapshot and missing-date case.",
            "No production systems, real backup inventory, concurrent queries or CPU/IO profiler.",
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main(arguments()))
