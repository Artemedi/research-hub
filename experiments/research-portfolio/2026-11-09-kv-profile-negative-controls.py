#!/usr/bin/env python3
"""Adversarial audit of the retired lexical-only physical-KV fit exclusion.

The four synthetic project profiles below are NOT claims about the user's
private repositories. The pinned historical script remains unmodified.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = ROOT / "experiments/research-portfolio/2026-11-09-kv-backend-profile-gate.py"
PIN = "b797a1354239c28b8026f59f4b474b803c439e4a48f91fcb067e639677344e42"

def main():
    assert hashlib.sha256(HISTORICAL.read_bytes()).hexdigest() == PIN
    source = HISTORICAL.read_text(encoding="utf-8")
    # The exact legacy source predicates must be present: this audit does not
    # silently substitute a different classifier.
    assert 'vllm|sglang|lmcache|mooncake|inference server|serving backend' in source
    assert 'cache.{0,30}(evict|hook)' in source
    serving = re.compile(r"(?i)\b(vllm|sglang|lmcache|mooncake|inference server|serving backend)\b")
    control = re.compile(r"(?i)(KV.{0,12}(evict|cache|manag|hook)|evict.{0,30}(cache|KV)|cache.{0,30}(evict|hook)|pin.{0,10}unpin)")
    fixtures = [
        ("llama_cpp_owned_cache", "Own llama.cpp backend exposes controllable KV-cache eviction hooks and explicit sequence removal.", True),
        ("tensorrt_owned_cache", "Own TensorRT-LLM backend exposes controllable KV-cache eviction hooks and explicit sequence removal.", True),
        ("vllm_owned_cache", "Own vLLM backend exposes controllable KV-cache eviction hooks and explicit sequence removal.", True),
        ("vllm_log_analyzer", "Only analyzes vLLM KV-cache eviction logs; no serving runtime and no authority to modify the cache.", False),
    ]
    checks = []
    for name, text, actual in fixtures:
        legacy_candidate = bool(serving.search(text) and control.search(text))
        checks.append({
            "fixture": name,
            "documented_real_authority_fixture_gold": actual,
            "historical_gate_candidate": legacy_candidate,
            "historical_gate_correct": actual == legacy_candidate,
        })
    assert [r["historical_gate_candidate"] for r in checks] == [False, False, True, True]
    assert sum(not r["historical_gate_correct"] for r in checks) == 3
    result = {
        "status": "PASS_ADVERSARIAL_AUDIT_OF_INADEQUATE_NEGATIVE_GATE",
        "original_gate_sha256": PIN,
        "fixtures": checks,
        "incorrect_decisions": 3,
        "total_synthetic_fixtures": 4,
        "conclusion": "Lexical absence is not a valid exhaustive NO_FIT oracle; project-specific verified backend ownership and source-level hooks remain unassessed.",
        "privacy": "No private project contents used or published; authored synthetic text only.",
        "next_gate": "Review current candidate project source at pinned commit for actual controllable KV lifecycle/eviction hook and owner-approved held-out metrics; do not convert missing assessment to NO_FIT.",
    }
    output = ROOT / "data/results/research-portfolio/2026-11-09-kv-profile-negative-controls.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result["status"],result["incorrect_decisions"],"/",result["total_synthetic_fixtures"])

if __name__ == "__main__":
    main()
