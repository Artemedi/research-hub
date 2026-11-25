"""Compare live and snapshot PostgreSQL settings on isolated disposable databases."""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

WIKI_REV = "d55721bb99bff25fae352341cfd630c048693d6b"
BINARY_SHA = "f6fac005c39898a379523700727a2a3d0a2828f579bec22cc0efe74e0652062d"
IMAGES = {
    "15.20": "sha256:91b9edc40277faf94bc1e3d7ae621b185fa70f3099b94309c4731a8296114870",
    "18.3": "sha256:7e32e9833a6fb1c92c32552794cb6ed569d51b445a54907d35fc112ef39684db",
}
DATE_VALUES = {"2026-11-23": "4096", "2026-11-25": "8192"}
MISSING = "2026-11-24"
HOST = "FixtureHost"
CONFIG = Path(__file__).resolve().parents[1] / "2026-11-04-mcp-toolbox-wikipg-tools.yaml"
SNAPSHOTS = Path(f"raw/sysconfig-report/fixture/{HOST}/2026/11")


def command(*args):
    return subprocess.check_output(args, text=True, timeout=60).strip()


def psql(container, role, sql):
    return command("docker", "exec", container, "psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1",
                   "-U", role, "-d", "lab", "-c", sql)


def snapshot_path(date):
    return SNAPSHOTS / f"{HOST}_sysconfig_report_{date}_22-00-00.json"


def snapshot_root(root):
    registry = root / "operations/clusters/registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text(f"clusters:\n  {HOST}: fixture\n", encoding="utf-8")
    (root / SNAPSHOTS).mkdir(parents=True)
    for date, value in DATE_VALUES.items():
        (root / snapshot_path(date)).write_text(json.dumps({"postgres_settings": {"instances": [{
            "port": "5432", "settings": [{"name": "work_mem", "setting": value, "unit": "kB", "boot_val": "4096"}],
        }]}}), encoding="utf-8")


async def ask(session, tool, arguments):
    response = await asyncio.wait_for(session.call_tool(tool, arguments), timeout=25)
    if response.isError:
        raise AssertionError(f"{tool} returned an MCP error")
    if response.structuredContent is not None:
        return response.structuredContent
    return json.loads(response.content[0].text)


async def compare(container, wiki):
    live = StdioServerParameters(command="docker", args=[
        "exec", "-i", container, "/tmp/toolbox", "--config", "/tmp/tools.yaml", "--stdio",
    ])
    records = []
    async with stdio_client(wiki) as (wiki_read, wiki_write):
        async with ClientSession(wiki_read, wiki_write) as snapshots:
            await asyncio.wait_for(snapshots.initialize(), timeout=25)
            for value in ("4096", "8192", "16384"):
                psql(container, "postgres", f"ALTER ROLE observer SET work_mem TO '{value}kB'")
                oracle = psql(container, "observer", "SELECT setting || '|' || unit FROM pg_catalog.pg_settings "
                              "WHERE name = 'work_mem' AND current_setting('transaction_read_only') = 'on'")
                async with stdio_client(live) as (live_read, live_write):
                    async with ClientSession(live_read, live_write) as toolbox:
                        await asyncio.wait_for(toolbox.initialize(), timeout=25)
                        manifest = await asyncio.wait_for(toolbox.list_tools(), timeout=25)
                        names = {tool.name for tool in manifest.tools}
                        if names != {"get_live_pg_setting"}:
                            raise AssertionError(f"Unexpected toolbox tools: {names}")
                        reading = await ask(toolbox, "get_live_pg_setting", {"setting": "work_mem"})
                if (oracle, reading.get("name"), reading.get("setting"), reading.get("unit")) != (
                        value + "|kB", "work_mem", value, "kB"):
                    raise AssertionError((oracle, reading))
                snapshots_read = {}
                for date, expected in (*DATE_VALUES.items(), (None, "8192"), (MISSING, None)):
                    args = {"host": HOST, "parameter": "work_mem", "pg_port": "5432"}
                    if date:
                        args["snapshot_date"] = date
                    row = await ask(snapshots, "get_postgres_setting", args)
                    key = date or "latest"
                    if expected is None:
                        if row["status"] != "no_snapshot":
                            raise AssertionError("Missing date did not remain missing")
                        snapshots_read[key] = {"status": row["status"]}
                        continue
                    capture = date or "2026-11-25"
                    if (row["status"], row["setting"], row["unit"], row["captured_at"], row["source_file"]) != (
                            "ok", expected, "kB", capture + "T22:00:00", snapshot_path(capture).as_posix()):
                        raise AssertionError((key, row))
                    snapshots_read[key] = {field: row[field] for field in ("status", "setting", "unit", "captured_at", "source_file")}
                records.append({"live_oracle_kB": value, "toolbox_kB": reading["setting"], "snapshots": snapshots_read})
    return records


def trial(version, image, binary, wiki):
    label = "research-hub-toolbox-" + uuid4().hex[:12]
    container = command("docker", "run", "--detach", "--rm", "--name", label, "--pull", "never",
                        "--network", "none", "--memory", "768m", "--cpus", "1", "--pids-limit", "120",
                        "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-e", "POSTGRES_DB=lab", image)
    try:
        for _ in range(100):
            # TCP readiness excludes the entrypoint's socket-only initialization server.
            ready = subprocess.run(["docker", "exec", container, "pg_isready", "-h", "127.0.0.1",
                                    "-U", "postgres", "-d", "lab"], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=5)
            if ready.returncode == 0:
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("Disposable PostgreSQL did not start")
        major, minor = map(int, version.split("."))
        if psql(container, "postgres", "SHOW server_version_num") != str(major * 10000 + minor):
            raise RuntimeError("Unexpected PostgreSQL version")
        psql(container, "postgres", "CREATE ROLE observer LOGIN; ALTER ROLE observer SET default_transaction_read_only TO on")
        command("docker", "cp", str(binary), container + ":/tmp/toolbox")
        command("docker", "cp", str(CONFIG), container + ":/tmp/tools.yaml")
        command("docker", "exec", container, "chmod", "700", "/tmp/toolbox")
        return asyncio.run(compare(container, wiki))
    finally:
        command("docker", "stop", "--timeout", "4", container)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_checkout", type=Path)
    parser.add_argument("toolbox_binary", type=Path)
    args = parser.parse_args()
    source, binary = args.wiki_checkout.resolve(), args.toolbox_binary.resolve()
    if command("git", "-C", str(source), "rev-parse", "HEAD") != WIKI_REV or command(
            "git", "-C", str(source), "status", "--porcelain"):
        parser.error(f"Expected clean Wiki_PG checkout at {WIKI_REV}")
    with binary.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != BINARY_SHA:
            parser.error("Toolbox binary does not match the historical SHA-256")
    with TemporaryDirectory() as temp:
        root = Path(temp)
        snapshot_root(root)
        wiki = StdioServerParameters(command=sys.executable, args=[
            str(source / "Wiki_PG/ingestion/mcp_wiki_server.py"),
        ], env={**os.environ, "WIKIPG_WIKI_ROOT": str(root), "PYTHONDONTWRITEBYTECODE": "1"})
        rows = {version: trial(version, image, binary, wiki) for version, image in IMAGES.items()}
        if rows != {version: trial(version, image, binary, wiki) for version, image in IMAGES.items()}:
            raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_pg_revision": WIKI_REV, "toolbox_sha256": BINARY_SHA,
                      "postgres_images": IMAGES, "repeat_count": 2, "status": "PASS", "versions": rows}, indent=2))


if __name__ == "__main__":
    main()
