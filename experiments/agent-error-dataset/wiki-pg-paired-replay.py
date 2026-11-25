"""Replay a rejected Wiki_PG read with one evidence-bound selector."""

import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import selectors
import subprocess
import sys
from tempfile import TemporaryDirectory


TARGET = "d55721bb99bff25fae352341cfd630c048693d6b"
STAMP = "2026-11-25T00:00:00Z"
ERRORS = {"port": "port required for instance scope", "region": "ambiguous host: specify region"}
HOSTS = {("lab-ports", "zone-a"): (150020, 180007),
         ("lab-shared", "zone-a"): (150019, 180006),
         ("lab-shared", "zone-b"): (150021, 180008)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root):
    paths = {}
    for (host, region), versions in HOSTS.items():
        path = root / "raw/sysconfig-report" / region / host / "state.json"
        path.parent.mkdir(parents=True)
        instances = [{"port": port, "server_version_num": version}
                     for port, version in zip((5432, 5433), versions)]
        path.write_text(json.dumps({"report_meta": {"timestamp_utc": STAMP},
                                   "postgres_runtime": {"instances": instances}}), encoding="ascii")
        paths[host, region] = path
    return paths


def invoke(query_class, root, action):
    reader = query_class(root)
    try:
        return reader.state(**action), None
    except ValueError as error:
        return None, str(error)
    finally:
        reader.close()


@contextmanager
def mcp_transport(checkout, root):
    env = {"PATH": os.defpath, "HOME": str(root), "WIKIPG_WIKI_ROOT": str(root),
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    server = checkout / "Wiki_PG/ingestion/mcp_wiki_server.py"
    with (root / "mcp-stderr.log").open("w+", encoding="utf-8") as errors:
        process = subprocess.Popen([sys.executable, "-B", str(server)], cwd=root, env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
                                   text=True, encoding="utf-8")
        ids = iter(range(1, 1000))
        try:
            def send(method, params, respond=True):
                request = dict(jsonrpc="2.0", method=method, params=params)
                if respond:
                    request["id"] = next(ids)
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()
                if not respond:
                    return None
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    if not selector.select(20):
                        raise TimeoutError("Wiki_PG MCP response timed out")
                    line = process.stdout.readline()
                if not line:
                    errors.seek(0)
                    raise RuntimeError(f"Wiki_PG MCP exited: {errors.read()[-400:]}")
                reply = json.loads(line)
                if reply.get("id") != request["id"] or "result" not in reply:
                    raise RuntimeError("Unexpected MCP protocol response")
                return reply["result"]

            send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "wiki-pg-replay", "version": "1"}})
            send("notifications/initialized", {}, respond=False)

            def read(action):
                reply = send("tools/call", {"name": "query_system_state", "arguments": action})
                value = reply["structuredContent"]
                if reply.get("isError"):
                    error = value["error"]
                    if error["code"] != "invalid_request":
                        raise RuntimeError(f"Unexpected Wiki_PG MCP error: {error['code']}")
                    return None, error["message"]
                return value, None

            yield read
            process.stdin.close()
            if process.wait(timeout=10) != 0:
                raise RuntimeError("Wiki_PG MCP failed on shutdown")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            for stream in (process.stdin, process.stdout):
                stream.close()


def correction(trace, clues):
    field = next((key for key, error in ERRORS.items() if error == trace["error"]), None)
    if field is None or field in trace["action"]:
        return None
    values = {value for action_id, key, value in clues if action_id == trace["id"] and key == field}
    if len(values) != 1:
        return None
    return {**trace["action"], field: values.pop()}


def verified(answer, paths, expected):
    if not answer or answer["status"] != "ok" or len(answer["sources"]) != 1 or len(answer["data"]) != 1:
        return False
    host, region, port = expected
    path = paths[host, region]
    instances = json.loads(path.read_bytes())["postgres_runtime"]["instances"]
    expected_version, = [str(i["server_version_num"]) for i in instances if str(i["port"]) == port]
    source, = answer["sources"]
    fact, = answer["data"]
    return ((source["host"], source["region"], source["sha256"]) == (host, region, digest(path))
            and (fact["key"], fact["pg_port"], fact["value_text"], fact["observed_at"]) ==
            ("server_version_num", port, expected_version, STAMP)
            and fact["source_id"] == source["source_id"])


def matrix():
    for index in range(4):
        port, other_port = (("5432", "5433") if index % 2 else ("5433", "5432"))
        region, other_region = (("zone-a", "zone-b") if index < 2 else ("zone-b", "zone-a"))
        action_id = f"read-{index}"
        port_action = dict(host="lab-ports", region="zone-a")
        region_action = dict(host="lab-shared", port=port)
        yield "explicit_port", action_id, "port", port_action, [(action_id, "port", port)], (
            ("lab-ports", "zone-a", port), other_port)
        yield "explicit_region", action_id, "region", region_action, [(action_id, "region", region)], (
            ("lab-shared", region, port), other_region)
        yield "no_port", action_id, "port", port_action, [], None
        yield "no_region", action_id, "region", region_action, [], None
        yield "conflicting_ports", action_id, "port", port_action, [
            (action_id, "port", port), (action_id, "port", other_port)], None
        yield "other_action_clue", action_id, "port", port_action, [("other-read", "port", port)], None


def exercise(read, paths):
    counts, families = Counter(), {}
    for name, action_id, field, selectors, clues, oracle in matrix():
        action = dict(**selectors, scope="pg_instance", fields=["server_version_num"], mode="at", at=STAMP)
        initial = read(action)
        if initial != (None, ERRORS[field]) or read(action) != initial:
            raise AssertionError(f"{name}: original error or retry changed")
        counts["original_retries_failed"] += 1
        repaired = correction({"id": action_id, "action": action, "error": initial[1]}, clues)
        if oracle is None:
            if repaired is not None:
                raise AssertionError(f"{name}: requested abstention")
            counts["abstained"] += 1
            families.setdefault(name, Counter())["abstained"] += 1
            continue
        if repaired is None or repaired.keys() != action.keys() | {field} or any(
                repaired[key] != value for key, value in action.items()):
            raise AssertionError(f"{name}: expected one selector change")
        expected, wrong_value = oracle
        answer, error = read(repaired)
        if error or not verified(answer, paths, expected):
            raise AssertionError(f"{name}: corrected result disagrees with frozen JSON")
        wrong, error = read({**repaired, field: wrong_value})
        if error or not wrong or wrong["status"] != "ok" or verified(wrong, paths, expected):
            raise AssertionError(f"{name}: the alternate valid selector did not exercise the oracle")
        counts["corrections_verified"] += 1
        counts["wrong_selectors_detected"] += 1
        families.setdefault(name, Counter())["corrected"] += 1
    if counts != {"original_retries_failed": 24, "abstained": 16,
                  "corrections_verified": 8, "wrong_selectors_detected": 8}:
        raise AssertionError("Unexpected replay counts")
    return dict(cases=24, **counts, families=families)


def run(root, checkout, query_class, build):
    paths = fixture(root)
    build(root)
    database = root / "System_Database/system.sqlite3"
    before = {path: digest(path) for path in [database, *paths.values()]}
    api = exercise(lambda action: invoke(query_class, root, action), paths)
    with mcp_transport(checkout, root) as read:
        stdio = exercise(read, paths)
    if before != {path: digest(path) for path in before}:
        raise AssertionError("The checkpoint changed during read-only replay")
    if api != stdio:
        raise AssertionError("Python and MCP comparisons disagree")
    return dict(target_commit=TARGET, python=platform.python_version(), mcp=version("mcp"),
                checkpoint_unchanged=True, python_api=api, mcp_stdio=stdio)


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
    from system_queries import SystemQueries

    with TemporaryDirectory(prefix="wiki-pg-read-replay-") as folder:
        print(json.dumps(run(Path(folder), checkout, SystemQueries, build), indent=2))
