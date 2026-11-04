#!/usr/bin/env python3
"""Bounded IPFire fireperf 0.3.0 loopback lab in a NO-NETWORK container.

Run using rootless Podman --network=none --cpus=2 --memory=512m.
Only listens in the container network namespace. Requires a previously
checksum-verified upstream fireperf binary and local shared libs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import socket
import subprocess
import time


def require_isolation():
    route = Path("/proc/net/route").read_text().splitlines()[1:]
    if any(
        cols[1] == "00000000"
        for line in route
        if len(cols := line.split()) >= 3
    ):
        raise RuntimeError("Default IPv4 route exists; refusing network benchmark")
    # No default route is a prerequisite, not a proof of full network isolation.
    return {"no_default_ipv4_route": True, "loopback": socket.gethostbyname("localhost")}


def run(args, mode, backend, trial, port):
    command = str(args.binary)
    base = [command, "--ipv4", f"--port={port}", "--workers=1",
            f"--backend={backend}", "--json"]
    server = subprocess.Popen(
        base + ["--server", "--timeout=7"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        time.sleep(0.5)
        client = base + [
            "--client=127.0.0.1", "--rate=10", "--connections=20",
            "--parallel=2", "--timeout=5",
            "--close" if mode == "close" else "--exchange=64:256",
        ]
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.monotonic()
        reply = subprocess.run(client, text=True, capture_output=True, timeout=10)
        wall = time.monotonic() - start
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        assert reply.returncode == 0, (reply.returncode, reply.stderr[-500:])
        lines = [json.loads(line) for line in reply.stdout.splitlines() if line.strip()]
        assert lines[0]["type"] == "start" and lines[-1]["type"] == "summary"
        summary = lines[-1]
        connections = summary["connections"]
        assert connections["total"] == connections["attempted"] == 20, connections
        assert connections["failed"] == 0 and connections["lost"] == 0, connections
        assert summary["failed"] == {
            "timeout": 0, "rejected": 0, "local": 0, "incomplete": 0
        }, summary["failed"]
        assert summary["schedule"]["due"] == 20
        assert summary["schedule"]["skipped"] == 0
        if mode == "exchange":
            assert summary["exchanges"] == 20
            assert summary["sent"]["total_bytes"] == 20 * 64
            assert summary["received"]["total_bytes"] == 20 * 256
            assert summary["exchange"]["count"] == 20
        else:
            assert summary["sent"]["total_bytes"] == 0
            assert summary["received"]["total_bytes"] == 0
        assert summary["handshake"]["count"] == 20
        return {
            "mode": mode, "backend_requested": backend, "trial": trial,
            "backend_used": lines[0]["backend"],
            "wall_seconds": round(wall, 4),
            "connections": connections,
            "handshake": summary["handshake"],
            "exchange": summary.get("exchange"),
            "exchanges": summary.get("exchanges"),
            "sent_bytes": summary["sent"]["total_bytes"],
            "received_bytes": summary["received"]["total_bytes"],
            "schedule": summary["schedule"],
            "cpu_client_process_seconds_approx": round(
                (after.ru_utime + after.ru_stime) -
                (before.ru_utime + before.ru_stime), 5
            ),
        }
    finally:
        server.terminate()
        try:
            _, err = server.communicate(timeout=2.5)
        except subprocess.TimeoutExpired:
            server.kill()
            _, err = server.communicate(timeout=2.5)
        if server.returncode not in (-15, 0):
            raise AssertionError(("server_exit", server.returncode, err[-500:]))


def refused_control(args, port):
    command = [
        str(args.binary), "--ipv4", f"--port={port}",
        "--client=127.0.0.1", "--workers=1", "--backend=epoll",
        "--rate=2", "--connections=3", "--parallel=1",
        "--close", "--timeout=4", "--json",
    ]
    reply = subprocess.run(command, text=True, capture_output=True, timeout=8)
    data = []
    for line in reply.stdout.splitlines():
        try:
            data.append(json.loads(line))
        except ValueError:
            pass
    summary = next((x for x in reversed(data) if x.get("type") == "summary"), None)
    # A refused endpoint must never claim 3 completed, successful connections.
    if summary is not None:
        assert summary["connections"]["total"] == 0
        assert summary["connections"]["failed"] >= 1
        assert summary["failed"]["rejected"] >= 1
    else:
        assert reply.returncode != 0
    return {
        "returncode": reply.returncode,
        "got_summary": summary is not None,
        "attempted": summary["connections"]["attempted"] if summary else None,
        "failed": summary["connections"]["failed"] if summary else None,
        "failure_reasons": summary.get("failed") if summary else None,
        "stderr_tail": reply.stderr[-300:],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--base-port", type=int, default=49590)
    args = p.parse_args()
    if args.trials not in range(1, 6):
        p.error("1..5 trials only")
    if not 49152 <= args.base_port <= 60000:
        p.error("high ephemeral base port required")
    env = require_isolation()
    assert args.binary.exists()
    version = subprocess.run(
        [str(args.binary), "--version"], text=True, capture_output=True,
        timeout=3, check=True,
    ).stdout.splitlines()[0]
    assert "fireperf 0.3.0" in version, version
    records = []
    for mode in ("close", "exchange"):
        for backend in ("epoll", "auto"):
            for trial in range(args.trials):
                records.append(run(
                    args, mode, backend, trial,
                    args.base_port + len(records)
                ))
    negative = refused_control(args, args.base_port + 100)
    assert len(records) == 4 * args.trials
    report = {
        "status": "PASS",
        "source": "Official IPFire fireperf 0.3.0",
        "version": version,
        "network": "rootless podman --network=none, 127.0.0.1 only",
        "isolation_guard": env,
        "cpu_limit": "2 CPUs supplied by outer container",
        "memory_limit": "512 MiB supplied by outer container",
        "rate_connections_per_s": 10,
        "connections_per_case": 20,
        "cases": len(records),
        "asserted_total_connections": 20 * len(records),
        "runs": records,
        "refused_port_negative_control": negative,
        "limitations": [
            "Loopback within a container, not routed traffic, firewall, SAN or production.",
            "Small bounded connection and byte counts, not throughput capacity.",
            "CPU is approximate client wait4 rusage; not normalized throughput.",
            "No independent packet capture; JSON effect/byte counters checked against deterministic input.",
            "io_uring backend is selected only when environment allows; no performance inference.",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()