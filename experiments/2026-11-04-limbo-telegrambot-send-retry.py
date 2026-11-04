#!/usr/bin/env python3
"""Actual TelegramBot main() under simulated ambiguous Telegram transport faults.

LIMBO upstream World/ToolRuntime supplies an independent service-contract control.
No external network or real Telegram credentials/production files are used.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import urllib.error

MODES = (
    "success", "timeout_pre", "timeout_post", "http500_pre", "http500_post",
    "timeout_late", "duplicate_delivery", "crash_after_ack", "state_lost_after_ack",
)
EXPECTED = {m: (1 if m in ("success", "timeout_pre", "http500_pre") else 2) for m in MODES}


def load_real_module(path):
    spec = importlib.util.spec_from_file_location("telegrambot_actual_main_lab", path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, {
        "TELEGRAM_BOT_TOKEN": "OFFLINE_TEST_NOT_A_TOKEN",
        "TELEGRAM_CHAT_ID": "-999999",
        "GEMINI_API_KEY": "OFFLINE_TEST_NOT_A_KEY",
        "YOUTUBE_CHANNEL_IDS": "lab-channel",
        "FORCE_TEST_POST": "false",
    }):
        spec.loader.exec_module(mod)
    return mod


class Reply:
    def __init__(self, msg_id):
        self.content = json.dumps({"ok": True, "result": {"message_id": msg_id}}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.content


class Transport:
    def __init__(self, mode, video_id):
        self.mode, self.video_id = mode, video_id
        self.calls, self.effects, self.deferred = 0, [], []

    def commit(self, payload):
        self.effects.append({
            "message_id": 1000 + len(self.effects),
            "video_id": self.video_id, "text": payload["text"],
        })

    def settle(self):
        for p in self.deferred:
            self.commit(p)
        self.deferred.clear()

    def urlopen(self, req, *args, **kwargs):
        if not req.full_url.startswith(
            "https://api.telegram.org/botOFFLINE_TEST_NOT_A_TOKEN/sendMessage"
        ):
            raise AssertionError("No other network endpoint is allowed")
        assert req.data
        payload = json.loads(req.data)
        assert payload["chat_id"] == "-999999" and payload["parse_mode"] == "HTML"
        assert self.video_id in payload["text"]
        self.calls += 1
        if self.calls == 1:
            if self.mode in ("timeout_pre", "http500_pre"):
                self.fail(req.full_url)
            if self.mode in ("timeout_post", "http500_post"):
                self.commit(payload)
                self.fail(req.full_url)
            if self.mode == "timeout_late":
                self.deferred.append(payload)
                raise TimeoutError("ambiguous timeout")
            if self.mode == "duplicate_delivery":
                self.commit(payload)
                self.commit(payload)
                return Reply(self.effects[-1]["message_id"])
        self.commit(payload)
        return Reply(self.effects[-1]["message_id"])

    def fail(self, url):
        if self.mode.startswith("timeout"):
            raise TimeoutError("ambiguous timeout")
        raise urllib.error.HTTPError(url, 500, "simulated HTTP 500", {}, None)


def actual_target_case(mod, mode, index, root):
    directory = root / f"{mode}-{index:02d}"
    directory.mkdir()
    seen_file = directory / "seen_videos.txt"
    state_file = directory / "post_state.json"
    mod.STATE_FILE = str(seen_file)
    mod.POST_STATE_FILE = str(state_file)
    mod.CHANNEL_IDS = ["lab-channel"]
    mod.FORCE_TEST_POST = False
    mod.TG_THREAD_ID = None
    video = f"vid-{index:02d}-{mode}"
    stamp = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)
    video_url = f"https://www.youtube.com/watch?v={video}"
    transport = Transport(mode, video)

    def candidate(channel, seen):
        assert channel == "lab-channel"
        return None if video in seen else (stamp, video, video_url)

    def invocation(crash=False):
        with patch.object(mod, "get_next_video", candidate), \
             patch.object(mod, "generate_science_post",
                          lambda url: f"<b>Offline video</b> {url}"), \
             patch.object(mod.urllib.request, "urlopen", transport.urlopen):
            try:
                if crash:
                    with patch.object(mod, "save_post_state",
                                      side_effect=SystemExit("simulated process crash")):
                        with redirect_stdout(io.StringIO()):
                            mod.main()
                else:
                    with redirect_stdout(io.StringIO()):
                        mod.main()
            except (RuntimeError, SystemExit) as exc:
                return type(exc).__name__
            return None

    first_error = invocation(crash=mode == "crash_after_ack")
    seen_after_first = seen_file.read_bytes() if seen_file.exists() else None
    state_after_first = state_file.read_bytes() if state_file.exists() else None
    first_count = len(transport.effects)
    if mode == "state_lost_after_ack":
        # Equivalent to losing local checkout state before separate git push.
        seen_file.unlink(missing_ok=True)
        state_file.unlink(missing_ok=True)
    second_error = invocation()
    transport.settle()
    count = len(transport.effects)
    assert count == EXPECTED[mode], (mode, count)
    assert transport.calls == (1 if mode in ("success", "duplicate_delivery") else 2)
    if mode == "crash_after_ack":
        assert first_error == "SystemExit"
    if mode in ("timeout_pre", "timeout_post", "http500_pre",
                "http500_post", "timeout_late"):
        assert first_error == "RuntimeError"
    assert all(e["video_id"] == video for e in transport.effects)
    return {
        "mode": mode, "first_error": first_error, "second_error": second_error,
        "first_count": first_count, "effect_count": count,
        "duplicate": count > 1, "calls": transport.calls,
        "first_state_hashable": [
            seen_after_first.decode() if seen_after_first else None,
            state_after_first.decode() if state_after_first else None,
        ],
    }


def upstream_limbo_original(root, n):
    sys.path.insert(0, str(root))
    from limbo.runtime import FaultSpec, ToolRuntime
    from limbo.services import build_tools
    from limbo.world import World
    result = {}
    for platform in ("x", "mastodon"):
        for mode in ("timeout_post", "timeout_late", "duplicate_delivery"):
            effects = []
            for i in range(n):
                world = World(seed=1000 + i)
                runtime = ToolRuntime(
                    world, build_tools(),
                    [FaultSpec(mode, "social_publish", {"platform": platform})],
                )
                args = {"platform": platform, "text": f"test announcement {i:02d}"}
                if platform == "mastodon":
                    args["idempotency_key"] = f"stable-post-{i:02d}"
                obs = runtime.execute("social_publish", args)
                if not obs.get("ok"):
                    retry = runtime.execute("social_publish", args)
                    assert retry["ok"]
                runtime.flush()
                count = sum(e.tool == "social_publish" for e in world.ledger)
                assert count == (2 if platform == "x" else 1)
                effects.append(count)
            result[f"{platform}/{mode}"] = {
                "cases": n, "effects_per_case": effects[0],
                "duplicates": sum(x > 1 for x in effects),
                "supports_idempotency_key": platform == "mastodon",
            }
    return result


def reservation_only_model(n):
    # Manual PENDING before send. On timeout, stop and ask for reconciliation.
    # Demonstrates at-most-once by abandoning pre-commit requests: NOT exactly-once.
    return {
        mode: {
            "cases": n, "duplicates": 0,
            "missing": n if mode == "timeout_pre" else 0,
            "uncertain_escalations": n,
        }
        for mode in ("timeout_pre", "timeout_post", "timeout_late")
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--telegram-root", type=Path, required=True)
    p.add_argument("--limbo-root", type=Path, required=True)
    p.add_argument("--telegram-commit", required=True)
    p.add_argument("--limbo-commit", required=True)
    p.add_argument("--cases-per-mode", type=int, default=20)
    a = p.parse_args()
    if not 1 <= a.cases_per_mode <= 200:
        p.error("cases-per-mode must be between 1 and 200")
    for repo, expected in ((a.telegram_root, a.telegram_commit),
                           (a.limbo_root, a.limbo_commit)):
        actual = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if actual != expected:
            p.error(f"Source revision mismatch: expected {expected}, got {actual}")
    module = load_real_module(a.telegram_root / "main.py")
    with tempfile.TemporaryDirectory(prefix="limbo-telegrambot-offline-") as t:
        records = [
            actual_target_case(module, mode, i, Path(t))
            for mode in MODES for i in range(a.cases_per_mode)
        ]
    counts = {
        m: {"cases": a.cases_per_mode,
            "duplicate_cases": sum(r["duplicate"] for r in records if r["mode"] == m),
            "committed_effects": sum(r["effect_count"] for r in records if r["mode"] == m)}
        for m in MODES
    }
    # The local evidence after first call is identical for pre-/post-commit
    # timeout, while the ground-truth service effects differ 0 vs 1.
    for i in range(a.cases_per_mode):
        pre = records[MODES.index("timeout_pre") * a.cases_per_mode + i]
        post = records[MODES.index("timeout_post") * a.cases_per_mode + i]
        assert pre["first_error"] == post["first_error"] == "RuntimeError"
        assert pre["first_state_hashable"] == post["first_state_hashable"]
        assert pre["first_count"] == 0 and post["first_count"] == 1
    upstream = upstream_limbo_original(a.limbo_root, a.cases_per_mode)
    reservations = reservation_only_model(a.cases_per_mode)
    assert len(records) == a.cases_per_mode * len(MODES)
    report = {
        "status": "PASS", "real_network_calls": 0,
        "actual_telegrambot_main_and_send_telegram_invoked": True,
        "telegrambot_commit": a.telegram_commit,
        "limbo_upstream_commit": a.limbo_commit,
        "cases_per_mode": a.cases_per_mode,
        "telegrambot_cases": len(records),
        "telegrambot_results": counts,
        "telegrambot_duplicate_cases": sum(r["duplicate"] for r in records),
        "first_observation_indistinguishable_between_pre_and_post": True,
        "original_limbo_world_results": upstream,
        "manual_pending_no_retry_tradeoff_model": reservations,
        "example_by_mode": {m: next(
            {"first_error": r["first_error"],
             "first_effects": r["first_count"],
             "final_effects": r["effect_count"],
             "attempts": r["calls"],
             "post_state_written_after_first": r["first_state_hashable"][1] is not None}
            for r in records if r["mode"] == m) for m in MODES},
        "limitations": [
            "Only real main.py control flow + urllib transport mock; no Telegram/Gemini/YouTube/Actions network.",
            "No actual Telegram idempotency key support; Mastodon in LIMBO is illustrative only.",
            "Provider ledger is a simulated independent oracle; no real sent message IDs or platform acknowledgement.",
            "Test runs are sequential and synthetic; network/IO/process latency not benchmarked.",
            "A local PENDING marker avoids automatic duplicate retries but cannot ensure delivery under timeout_pre.",
            "No deployment/production changes were made.",
        ],
    }
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
