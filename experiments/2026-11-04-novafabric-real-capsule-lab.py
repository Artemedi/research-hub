#!/usr/bin/env python3
"""Real NovaFabric v0.108.0 capture/seal/verify/mock replay lab.

Uses the ORIGINAL nova CLI on toy decorated Python tools, local fake data only.
All fixtures and local signing keys stay under --workspace. Never use production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import time

import yaml

AGENT = '''\
import json
import os
from pathlib import Path
from novafabric.capture import record

def marker(label):
    with Path(os.environ["NOVA_LAB_SIDE"]).open("a") as file:
        file.write(label + "\\n")

@record.tool(mutation_class="read-only")
def fetch_metric(name):
    marker("fetch-executed")
    return json.loads(Path(os.environ["NOVA_LAB_SOURCE"]).read_text())[name]

@record.tool(mutation_class="none")
def calculate_metric(value):
    marker("calculate-executed")
    return {"metric": value, "doubled": 2 * value, "status": "ok"}

answer = calculate_metric(fetch_metric("value"))
Path(os.environ["NOVA_LAB_RESULT"]).write_text(json.dumps(answer, sort_keys=True) + "\\n")
print(json.dumps(answer, sort_keys=True))
'''


def cli(args, env, *, timeout=60, allow_failure=False):
    start = time.perf_counter()
    p = subprocess.run(
        [str(x) for x in args],
        env=env, text=True, capture_output=True, timeout=timeout,
    )
    duration = time.perf_counter() - start
    if p.returncode != 0 and not allow_failure:
        raise RuntimeError(
            f"Command failed {p.returncode}: {' '.join(map(str, args[:4]))}\n"
            f"STDOUT: {p.stdout[-1500:]}\nSTDERR: {p.stderr[-1500:]}"
        )
    return p, duration


def disk_bytes(directory):
    return sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())


def median(values):
    return round(statistics.median(values) * 1000, 3)


def create_mutation(original, dst, mutation):
    shutil.copytree(original, dst)
    if mutation == "output_payload":
        with (dst / "outputs/stdout.txt").open("ab") as fd:
            fd.write(b"tampered\n")
    elif mutation == "tool_swap":
        path = dst / "tool-calls.jsonl"
        lines = path.read_bytes().splitlines(keepends=True)
        assert len(lines) == 2
        path.write_bytes(lines[1] + lines[0])
    elif mutation == "manifest_status":
        path = dst / "capsule.yaml"
        content = path.read_text()
        assert "status: success" in content
        path.write_text(content.replace("status: success", "status: failure", 1))
    elif mutation == "missing_trace":
        (dst / "trace.jsonl").unlink()
    elif mutation == "renamed_empty_stream":
        (dst / "model-calls.jsonl").rename(dst / "model-calls.moved")
    elif mutation == "extra_unsigned_file":
        (dst / "rogue-added-after-seal.txt").write_text("Unregistered post-seal data\n")
    elif mutation == "remove_seal":
        shutil.rmtree(dst / ".seal")
    else:
        raise AssertionError(mutation)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--nova", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--cases", type=int, default=20)
    args = parser.parse_args()
    if not (1 <= args.cases <= 50):
        parser.error("--cases must be from 1 through 50")
    workspace = args.workspace.resolve()
    if workspace.exists() and any(workspace.iterdir()):
        parser.error("--workspace must not exist or must be empty")
    workspace.mkdir(parents=True, exist_ok=True)
    home = workspace / "novafabric-home"
    capsules = workspace / "capsules"
    data = workspace / "inputs"
    home.mkdir()
    capsules.mkdir()
    data.mkdir()
    fixture_agent = workspace / "toy_agent.py"
    fixture_agent.write_text(AGENT)
    env = {
        **os.environ,
        "NOVAFABRIC_HOME": str(home),
        "NOVAFABRIC_CAPSULE_DIR": str(capsules),
        "NOVA_CAPTURE_LEVEL": "forensic",
        "NOVAFABRIC_SUGGEST": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    init, init_secs = cli([args.nova, "seal", "init"], env)
    assert (home / "novaseal.yaml").exists(), init.stdout

    observed = []
    times = {"direct": [], "capture": [], "validate": [], "verify": [],
             "verify_ca": [], "replay_mocked": [], "replay_forensic": []}
    bytes_per_capsule = []
    ids = []
    for index in range(args.cases):
        value = 700 + 13 * index
        task = data / f"task-{index:02d}"
        task.mkdir()
        source = task / "source.json"
        side = task / "side.log"
        result = task / "answer.json"
        source.write_text(json.dumps({"value": value}))
        task_env = {
            **env,
            "NOVA_LAB_SOURCE": str(source),
            "NOVA_LAB_SIDE": str(side),
            "NOVA_LAB_RESULT": str(result),
        }
        answer = {"metric": value, "doubled": value * 2, "status": "ok"}
        expected_bytes = (json.dumps(answer, sort_keys=True) + "\n").encode()
        direct, duration = cli([args.python, fixture_agent], task_env)
        assert result.read_bytes() == expected_bytes
        assert side.read_text().splitlines() == ["fetch-executed", "calculate-executed"]
        times["direct"].append(duration)
        side.unlink()

        before = {p.name for p in capsules.iterdir()}
        cap_cmd, duration = cli(
            [args.nova, "capture", "--output-dir", capsules, args.python, fixture_agent],
            task_env,
        )
        times["capture"].append(duration)
        names = {p.name for p in capsules.iterdir()} - before
        assert len(names) == 1, (index, names, cap_cmd.stdout)
        capsule = capsules / names.pop()
        ids.append(capsule.name)
        manifest = yaml.safe_load((capsule / "capsule.yaml").read_text())
        assert manifest["status"] == "success" and manifest["exit_code"] == 0
        assert manifest["tool_call_count"] == 2
        assert result.read_bytes() == expected_bytes
        assert side.read_text().splitlines() == ["fetch-executed", "calculate-executed"]
        assert (capsule / "outputs/stdout.txt").read_bytes() == expected_bytes
        assert len((capsule / "tool-calls.jsonl").read_text().splitlines()) == 2

        _, duration = cli([args.nova, "validate", capsule], task_env)
        times["validate"].append(duration)
        _, duration = cli([args.nova, "verify", capsule], task_env)
        times["verify"].append(duration)
        verified, duration = cli([
            args.nova, "verify",
            "--ca-bundle", home / "keys/novaseal/ca.crt.pem",
            capsule,
        ], task_env)
        times["verify_ca"].append(duration)
        assert "local-ca-pinned" in verified.stdout.lower(), verified.stdout[-1200:]
        bytes_per_capsule.append(disk_bytes(capsule))
        assert (capsule / ".seal/manifest.dsse").exists()

        # A successful mocked replay must serve the *recorded* tool responses:
        # the live source has changed and both tool body side effects are monitored.
        source.write_text(json.dumps({"value": value + 9000}))
        side.write_text("")
        before = {p.name for p in (home / "replays").iterdir()} if (
            home / "replays"
        ).exists() else set()
        replayed, duration = cli(
            [args.nova, "replay", capsule, "--mode", "mocked"], task_env
        )
        times["replay_mocked"].append(duration)
        assert result.read_bytes() == expected_bytes, replayed.stdout[-600:]
        assert side.read_bytes() == b"", "Tool body executed unexpectedly"
        paths = {p.name for p in (home / "replays").iterdir()} - before
        assert len(paths) == 1, paths
        replay_result = yaml.safe_load((
            home / "replays" / paths.pop() / "replay_result.yaml"
        ).read_text())
        assert replay_result["status"] == "success"
        assert replay_result["tool_calls_mocked"] == 2
        assert replay_result["tool_calls_live"] == 0
        assert replay_result["tool_calls_unmatched"] == 0
        assert replay_result["queues_fully_consumed"]
        assert replay_result["replay_contract"]["network_connections_live"] == 0
        assert replay_result["model_calls_mocked"] == 0
        assert replay_result["tool_calls_recorded"] == 2
        assert result.read_bytes() == expected_bytes

        if index == 0:
            side.write_text("")
            forensic, duration = cli(
                [args.nova, "replay", capsule, "--mode", "forensic"], task_env
            )
            times["replay_forensic"].append(duration)
            assert "mode=forensic" in forensic.stdout
            assert side.read_bytes() == b""
        observed.append({
            "index": index, "source_value": value,
            "capsule_id": capsule.name, "tools_captured": 2, "tools_mocked": 2,
            "external_tool_body_executions_on_mocked_replay": 0,
            "output_sha256": hashlib.sha256(expected_bytes).hexdigest(),
            "verify": "PASS", "verify_ca": "PASS",
        })

    # Strictness is confined to intercepted calls; uninstrumented file I/O
    # still executes live during mocked replay. Both behaviors are measured.
    fixture_source = fixture_agent.read_text()
    task0 = data / "task-00"
    side0 = task0 / "side.log"
    env0 = {
        **env, "NOVA_LAB_SOURCE": str(task0 / "source.json"),
        "NOVA_LAB_SIDE": str(side0),
        "NOVA_LAB_RESULT": str(task0 / "answer.json"),
    }
    try:
        fixture_agent.write_text(fixture_source + '\nfetch_metric("value")\n')
        side0.write_text("")
        unmatched, _ = cli(
            [args.nova, "replay", capsules / ids[0], "--mode", "mocked"],
            env0, allow_failure=True,
        )
        assert unmatched.returncode != 0
        assert "tool_call_unmatched" in unmatched.stdout
        assert side0.read_bytes() == b"", "Unmatched decorated tool executed"
        fixture_agent.write_text(
            fixture_source
            + '\nPath(os.environ["NOVA_LAB_SIDE"]).write_text("UNINSTRUMENTED_LIVE")\n'
        )
        side0.write_text("")
        uninstrumented, _ = cli(
            [args.nova, "replay", capsules / ids[0], "--mode", "mocked"], env0
        )
        assert uninstrumented.returncode == 0
        assert side0.read_text() == "UNINSTRUMENTED_LIVE"
    finally:
        fixture_agent.write_text(fixture_source)
        side0.write_text("")
    boundary_controls = {
        "extra_instrumented_tool_call": "REFUSED_BEFORE_BODY_EXECUTION",
        "unrecorded_python_file_write": "EXECUTED_LIVE_DESPITE_MOCKED_REPLAY",
    }

    original = capsules / ids[0]
    mutation_checks = {}
    for mutation in (
        "output_payload", "tool_swap", "manifest_status", "missing_trace",
        "renamed_empty_stream", "remove_seal", "extra_unsigned_file",
    ):
        dst = workspace / "mutations" / mutation / original.name
        dst.parent.mkdir(parents=True)
        create_mutation(original, dst, mutation)
        test, _ = cli([args.nova, "verify", dst], env, allow_failure=True)
        mutation_checks[mutation] = {
            "verification_exit_code": test.returncode,
            "tampering_detected": test.returncode != 0,
        }
        if mutation != "extra_unsigned_file":
            assert test.returncode != 0, (mutation, test.stdout, test.stderr)
        # Extra files can be outside the signed evidence digests; report behavior,
        # do not assume rejection in either direction.

    summary = {
        "status": "PASS",
        "original_code": "MSKazemi/novafabric v0.108.0",
        "python": str(args.python),
        "cases": args.cases,
        "captured_tool_calls": args.cases * 2,
        "mocked_tool_calls": args.cases * 2,
        "tool_body_executions_on_replay": 0,
        "byte_identical_outputs": args.cases,
        "capsule_validate_pass": args.cases,
        "capsule_seal_verify_pass": args.cases,
        "local_ca_pinned_verify_pass": args.cases,
        "forensic_replay_pass": 1,
        "real_model_calls": 0,
        "network_connections_live_during_mocked": 0,
        "replay_policy": "NOVA_CAPTURE_LEVEL=forensic; instrumented @record.tool only",
        "median_duration_ms": {k: median(v) for k, v in times.items() if v},
        "median_capsule_bytes": int(statistics.median(bytes_per_capsule)),
        "min_capsule_bytes": min(bytes_per_capsule),
        "max_capsule_bytes": max(bytes_per_capsule),
        "mutation_checks": mutation_checks,
        "mocked_replay_boundary_controls": boundary_controls,
        "first_capsule": observed[0],
        "last_capsule": observed[-1],
        "limitations": [
            "Two explicit @record.tool boundaries per synthetic run, not arbitrary filesystem/shell tools.",
            "Model SDK responses, MCP network tools, real DSH runtime and provider transport not tested.",
            "In-memory/offline fixture source changed; no network sandbox or OS syscall audit performed.",
            "No trusted external TSA; local self-asserted signer and pinned local CA only.",
            "Emitted file inventory is authoritative only for covered evidence files.",
            "Performance compares different operations on one machine and does not establish production overhead.",
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
