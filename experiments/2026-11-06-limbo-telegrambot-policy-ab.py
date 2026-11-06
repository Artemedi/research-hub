#!/usr/bin/env python3
"""Offline LIMBO x TelegramBot A/B: actual pinned main, fake outbound effect ledger.

Compare original automatic retry with a *counterfactual* sidecar PENDING fence,
and an *unavailable-to-Telegram* server idempotency oracle. No real outbound IO.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import tempfile
import time
import tracemalloc
from unittest.mock import patch

# Import ONLY known offline test helpers; their old __main__ is not executed.
BASELINE_REPLAY = Path(__file__).with_name(
    "2026-11-04-limbo-telegrambot-send-retry.py")
spec = importlib.util.spec_from_file_location("limbo_previous_lab", BASELINE_REPLAY)
previous = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(previous)

MODES = previous.MODES
ARMS = ("real_auto_retry", "sidecar_pending_no_retry",
        "hypothetical_server_idempotency")
AMBIGUOUS = {"timeout_pre", "timeout_post", "http500_pre", "http500_post",
             "timeout_late", "crash_after_ack", "state_lost_after_ack"}


class HypotheticalIdempotentTransport(previous.Transport):
    """Imaginary provider deduplicates by logical key; Telegram does NOT."""
    def commit(self, payload):
        if any(e["video_id"] == self.video_id for e in self.effects):
            return
        super().commit(payload)


def proc_io():
    p = Path("/proc/self/io")
    if not p.exists():
        return None
    result = {}
    for line in p.read_text().splitlines():
        k, sep, val = line.partition(":")
        if sep and k in ("rchar", "wchar", "read_bytes", "write_bytes"):
            result[k] = int(val.strip())
    return result


def check_revision(path, expected):
    sha = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                         check=True, capture_output=True, text=True).stdout.strip()
    if sha != expected:
        raise ValueError(f"Revision mismatch: {path} {sha} != {expected}")


def scenario(target, arm, mode, index, root):
    temp_state = root / f"{arm}-{mode}-{index:04d}"
    temp_state.mkdir()
    target.STATE_FILE = str(temp_state / "seen_videos.txt")
    target.POST_STATE_FILE = str(temp_state / "post_state.json")
    target.CHANNEL_IDS = ["synthetic-channel"]
    target.FORCE_TEST_POST = False
    target.TG_THREAD_ID = None
    video = f"synthetic-{index:04d}-{mode}"
    stamp = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)
    url = f"https://www.youtube.com/watch?v={video}"
    tr = (HypotheticalIdempotentTransport(mode, video)
          if arm == "hypothetical_server_idempotency"
          else previous.Transport(mode, video))

    def candidate(cid, seen):
        assert cid == "synthetic-channel"
        return None if video in seen else (stamp, video, url)

    def call(crash=False):
        with patch.object(target, "get_next_video", candidate), \
             patch.object(target, "generate_science_post",
                          lambda x: f"<b>Synthetic post</b> {x}"), \
             patch.object(target.urllib.request, "urlopen", tr.urlopen):
            try:
                if crash:
                    with patch.object(target, "save_post_state",
                                      side_effect=SystemExit("synthetic-crash")):
                        with redirect_stdout(io.StringIO()):
                            target.main()
                else:
                    with redirect_stdout(io.StringIO()):
                        target.main()
            except (RuntimeError, SystemExit) as e:
                return type(e).__name__
        return None

    # Counterfactual durable marker must be established BEFORE first external send.
    # Its persistence is modeled outside the checkout's local state files.
    pending = temp_state / "durable-outside-checkout-PENDING"
    if arm == "sidecar_pending_no_retry":
        pending.write_text(video + "\n")
    first_error = call(crash=(mode == "crash_after_ack"))
    effects_after_first = len(tr.effects)
    files_after_first = [
        (temp_state / f).read_bytes() if (temp_state / f).exists() else None
        for f in ("seen_videos.txt", "post_state.json")
    ]
    if mode == "state_lost_after_ack":
        (temp_state / "seen_videos.txt").unlink(missing_ok=True)
        (temp_state / "post_state.json").unlink(missing_ok=True)

    # Baseline and imaginary provider always retry; sidecar refuses auto replay
    # even following unconfirmed outcomes. This is a wrapper policy, NOT a patch.
    second_error = (None if arm == "sidecar_pending_no_retry" and pending.is_file()
                    and pending.read_text().strip() == video else call())
    tr.settle()
    effects = len(tr.effects)
    assert all(e["video_id"] == video for e in tr.effects)
    assert effects in (0, 1, 2), (mode, arm, effects)
    expected_effects = (
        (1 if mode in ("success", "timeout_pre", "http500_pre") else 2)
        if arm == "real_auto_retry" else
        (0 if mode in ("timeout_pre", "http500_pre") else
         2 if mode == "duplicate_delivery" else 1)
        if arm == "sidecar_pending_no_retry" else 1
    )
    assert effects == expected_effects, (arm, mode, effects, expected_effects)
    if mode in ("timeout_pre", "timeout_post"):
        assert first_error == "RuntimeError"
        assert files_after_first == [None, None] or (
            files_after_first[0] is None and
            files_after_first[1] is None
        ), (mode, files_after_first)
    if mode == "crash_after_ack":
        assert first_error == "SystemExit"
    return {
        "mode": mode, "count": effects, "calls": tr.calls,
        "first_effects": effects_after_first,
        "first_error": first_error, "second_error": second_error,
        "duplicate": effects > 1, "missing": effects == 0,
        "manual_review": arm == "sidecar_pending_no_retry" and mode in AMBIGUOUS,
        "pending_marker_preserved": pending.is_file()
        if arm == "sidecar_pending_no_retry" else None,
        "first_state": [x.decode() if x is not None else None
                        for x in files_after_first],
    }


def run_arm(target, arm, cases, root):
    start_io = proc_io()
    start_cpu = time.process_time_ns()
    start_wall = time.perf_counter_ns()
    tracemalloc.start()
    times, results = [], []
    for i, mode in enumerate(cases):
        tic = time.perf_counter_ns()
        results.append(scenario(target, arm, mode, i, root))
        times.append((time.perf_counter_ns() - tic) / 1e6)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    cpu_ms = (time.process_time_ns() - start_cpu) / 1e6
    wall_ms = (time.perf_counter_ns() - start_wall) / 1e6
    end_io = proc_io()
    io_delta = ({k: end_io[k] - start_io[k] for k in start_io}
                if start_io is not None and end_io is not None else None)
    latencies = sorted(times)
    by_fault = {
        mode: {
            "cases": sum(x["mode"] == mode for x in results),
            "duplicate_cases": sum(x["mode"] == mode and x["duplicate"]
                                   for x in results),
            "missing_cases": sum(x["mode"] == mode and x["missing"]
                                 for x in results),
        } for mode in MODES
    }
    return {
        "cases": len(results),
        "exactly_one": sum(x["count"] == 1 for x in results),
        "duplicate_cases": sum(x["duplicate"] for x in results),
        "missing_cases": sum(x["missing"] for x in results),
        "manual_review_cases": sum(x["manual_review"] for x in results),
        "actual_target_http_calls": sum(x["calls"] for x in results),
        "by_fault": by_fault,
        "latency_ms_p50": round(statistics.median(times), 4),
        "latency_ms_p95": round(latencies[int(.95 * len(times) + .999999)-1], 4),
        "wall_ms": round(wall_ms, 3),
        "cpu_ms": round(cpu_ms, 3),
        "python_peak_alloc_bytes": peak,
        "process_rss_highwater_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "proc_io_delta": io_delta,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--telegram-root", type=Path, required=True)
    parser.add_argument("--telegram-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--cases-per-mode", type=int, default=20)
    args = parser.parse_args()
    assert 3 <= args.seeds <= 10 and 5 <= args.cases_per_mode <= 100
    check_revision(args.telegram_root, args.telegram_commit)
    target = previous.load_real_module(args.telegram_root / "main.py")
    samples = []
    for n in range(args.seeds):
        seed = 20261106 + n
        modes = list(MODES) * args.cases_per_mode
        random.Random(seed).shuffle(modes)
        order = list(ARMS if n % 2 == 0 else reversed(ARMS))
        with tempfile.TemporaryDirectory(prefix="limbo-telegram-ab-") as td:
            scores = {arm: run_arm(target, arm, modes, Path(td))
                      for arm in order}
        assert scores["real_auto_retry"]["duplicate_cases"] == 6 * args.cases_per_mode
        assert scores["real_auto_retry"]["missing_cases"] == 0
        assert scores["sidecar_pending_no_retry"]["duplicate_cases"] == args.cases_per_mode
        assert scores["sidecar_pending_no_retry"]["missing_cases"] == 2 * args.cases_per_mode
        assert scores["hypothetical_server_idempotency"]["duplicate_cases"] == 0
        assert scores["hypothetical_server_idempotency"]["missing_cases"] == 0
        samples.append({
            "seed": seed,
            "case_order_sha256": hashlib.sha256("\n".join(modes).encode()).hexdigest(),
            "arm_order": order, "arms": scores,
        })
    totals = {
        arm: {
            key: sum(r["arms"][arm][key] for r in samples)
            for key in ("cases", "exactly_one", "duplicate_cases", "missing_cases",
                        "manual_review_cases", "actual_target_http_calls")
        } for arm in ARMS
    }
    out = {
        "experiment": "LIMBO/TelegramBot paired synthetic A/B tradeoff",
        "telegrambot_sha": args.telegram_commit,
        "real_target_main_send_telegram_used": True,
        "source_module_sha256": hashlib.sha256(
            (args.telegram_root / "main.py").read_bytes()).hexdigest(),
        "seed_count": args.seeds,
        "cases_per_mode_per_seed": args.cases_per_mode,
        "fault_modes": list(MODES),
        "arm_definitions": {
            "real_auto_retry": "Pinned TelegramBot main() twice; existing state only.",
            "sidecar_pending_no_retry": "COUNTERFACTUAL wrapper pre-writes an external PENDING marker, blocks ALL auto retry; DOES NOT modify TelegramBot source.",
            "hypothetical_server_idempotency": "COUNTERFACTUAL fake service deduplicates by simulated logical video key; Telegram Bot API does NOT provide that contract.",
        },
        "totals": totals, "runs": samples,
        "no_real_network_calls": True,
        "llm_calls": 0,
        "tokens": "N/A", "api_cost_usd": 0,
        "vram": "N/A, CPU-only",
        "host": {"python": os.sys.version.split()[0], "kernel": os.uname().release},
        "limitations": [
            "All faults and their equal class frequencies are synthetic, not Telegram incident frequencies.",
            "Policy wrapper is not deployed. It uses an imagined persistent sidecar marker; durability/fencing/reconciliation are not implemented.",
            "Hypothetical server-side idempotency is NOT offered by Telegram sendMessage.",
            "Duplicate delivery is an injected service fault; sidecar cannot suppress it.",
            "Transport latency, real network IO, message deletion/editing, real user payloads, bot rate limits, and multi-host concurrency NOT tested.",
            "Timing includes fake transport, Python mocks, temporary local files and tracemalloc instrumentation; not network p95.",
            "Shared process peak RSS is not per-arm cost; token/GPU results are N/A, not zero savings.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "totals": totals, "output": str(args.output),
        "sha256": out["source_module_sha256"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
