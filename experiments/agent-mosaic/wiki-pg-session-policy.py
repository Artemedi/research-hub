"""Measure protective release rules on synthetic Wiki_PG MCP comparisons."""

import argparse
import asyncio
from collections import Counter
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


TARGET = "d55721bb99bff25fae352341cfd630c048693d6b"
BEFORE, AFTER = "2026-11-24T00:00:00Z", "2026-11-25T00:00:00Z"
RAM = "memory.total_ram"
CPU = "cpu.cpu(s)"
UPTIME = "operating_system.uptime_seconds"
PROTECTED_PAIR = frozenset((RAM, CPU))
SCENARIOS = (
    ("ram", ((RAM,),)),
    ("cpu", ((CPU,),)),
    ("together", ((RAM, CPU),)),
    ("ram_then_cpu", ((RAM,), (CPU,))),
    ("cpu_then_ram", ((CPU,), (RAM,))),
    ("ram_and_uptime", ((RAM, UPTIME),)),
    ("missing_source", ((RAM,),)),
)


def fixtures(root):
    cases = {}
    for index in range(1, 5):
        host = f"lab-{index}"
        folder = root / "raw/sysconfig-report/lab-zone" / host
        folder.mkdir(parents=True)
        paths = {}
        for stamp, values in ((BEFORE, (100, 2, 200)),
                              (AFTER, (100 + index * 8, 2 + index, 200 + index * 10))):
            ram, cpu, uptime = values
            path = folder / (stamp[:10] + ".json")
            path.write_text(json.dumps({"report_meta": {"timestamp_utc": stamp},
                                        "memory": {"total_ram": ram}, "cpu": {"cpu(s)": cpu},
                                        "operating_system": {"uptime_seconds": uptime}}), encoding="ascii")
            paths[stamp] = path
        cases[host] = paths
    return cases


def project_observations(payload, requested, allowed_sources):
    if payload["status"] != "ok" or payload["warnings"] or len(payload["data"]) != len(requested):
        return None
    listed = {source["source_id"]: source for source in payload["sources"]}
    expected_sources = set(allowed_sources.items())
    seen_sources = {(source["observed_at"], source["sha256"]) for source in listed.values()}
    if len(payload["sources"]) != 2 or len(listed) != 2 or seen_sources != expected_sources:
        return None
    observed = {}
    for row in payload["data"]:
        if row["key"] not in requested or row["key"] in observed or row["status"] not in ("changed", "unchanged"):
            return None
        for side, stamp in (("left", BEFORE), ("right", AFTER)):
            fact = row.get(side)
            if (not fact or fact["key"] != row["key"] or fact["observed_at"] != stamp
                    or listed.get(fact["source_id"], {}).get("observed_at") != stamp):
                return None
        delta = row["absolute_delta"]
        if type(delta) not in (int, float) or not math.isfinite(delta):
            return None
        observed[row["key"]] = delta
    return observed


def release(mode, observed, previously_released):
    if observed is None:
        return {"status": "ABSTAIN", "observations": {}}
    current = set(observed)
    combined = current | previously_released if mode == "session" else current
    if mode != "source_only" and PROTECTED_PAIR <= combined:
        return {"status": "DENY", "observations": {}}
    return {"status": "ALLOW", "observations": observed}


def check_outbound(host_paths, packets):
    earlier = json.loads(host_paths[BEFORE].read_bytes())
    later = json.loads(host_paths[AFTER].read_bytes())
    totals = Counter()
    for current in packets:
        for field, delta in current.items():
            scope, name = field.split(".", 1)
            if delta != later[scope][name] - earlier[scope][name]:
                raise AssertionError("Outbound delta differs from the independently read fixture")
        totals.update(current.keys())
    return totals[RAM] > 0 and totals[CPU] > 0


async def compare(checkout, root, hosts):
    server = checkout / "Wiki_PG/ingestion/mcp_wiki_server.py"
    config = StdioServerParameters(command=sys.executable, args=["-B", str(server)], cwd=root,
                                   env={"HOME": str(root), "WIKIPG_WIKI_ROOT": str(root),
                                        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
    payloads = {}
    with (root / "mcp-stderr.log").open("w", encoding="utf-8") as errors:
        async with stdio_client(config, errlog=errors) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await asyncio.wait_for(session.initialize(), timeout=20)
                for host in hosts:
                    for fields in ((RAM,), (CPU,), (RAM, CPU), (RAM, UPTIME)):
                        reply = await asyncio.wait_for(session.call_tool("compare_system_states", {
                            "hosts": [host], "fields": list(fields), "before": BEFORE, "after": AFTER,
                        }), timeout=20)
                        if reply.isError or not reply.structuredContent:
                            raise AssertionError("Wiki_PG MCP comparison failed")
                        payloads[host, fields] = reply.structuredContent
    return payloads


def run(root, checkout, build):
    hosts = fixtures(root)
    manifest = {host: {stamp: hashlib.sha256(path.read_bytes()).hexdigest() for stamp, path in files.items()}
                for host, files in hosts.items()}
    build(root)
    database = root / "System_Database/system.sqlite3"
    frozen_hash = hashlib.sha256(database.read_bytes()).hexdigest()
    payloads = asyncio.run(compare(checkout, root, hosts))
    results = {}
    for mode in ("source_only", "per_response", "session"):
        counts = Counter()
        for host, files in hosts.items():
            for name, requests in SCENARIOS:
                published, prior = [], set()
                for fields in requests:
                    value = payloads[host, fields]
                    if name == "missing_source":
                        value = deepcopy(value)
                        value["sources"].pop()
                    projected = project_observations(value, fields, manifest[host])
                    decision = release(mode, projected, prior)
                    counts[decision["status"]] += 1
                    published.append(decision["observations"])
                    prior.update(decision["observations"])
                    if projected is not None and name not in ("together", "ram_then_cpu", "cpu_then_ram"):
                        if set(decision["observations"]) != set(fields):
                            raise AssertionError("Permitted release lost a requested observation")
                counts["sessions_with_protected_pair"] += check_outbound(files, published)
        results[mode] = counts
    expected = {
        "source_only": {"ALLOW": 32, "ABSTAIN": 4, "sessions_with_protected_pair": 12},
        "per_response": {"ALLOW": 28, "DENY": 4, "ABSTAIN": 4, "sessions_with_protected_pair": 8},
        "session": {"ALLOW": 20, "DENY": 12, "ABSTAIN": 4, "sessions_with_protected_pair": 0},
    }
    if results != expected or frozen_hash != hashlib.sha256(database.read_bytes()).hexdigest():
        raise AssertionError(f"Unexpected protective policy results: {results}")
    return dict(target_commit=TARGET, python=platform.python_version(), mcp=version("mcp"),
                native_comparisons=len(payloads), sessions_per_mode=28,
                attempts_per_mode=36, checkpoint_unchanged=True, modes=results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    checkout = parser.parse_args().checkout.resolve()
    git = ["git", "-C", str(checkout)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != TARGET
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        raise ValueError("Use the clean, pinned Wiki_PG checkout")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(checkout / "Wiki_PG/ingestion"))
    from build_system_store import build

    with TemporaryDirectory(prefix="wiki-pg-mosaic-") as folder:
        print(json.dumps(run(Path(folder), checkout, build), indent=2))
