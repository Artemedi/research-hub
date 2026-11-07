#!/usr/bin/env python3
"""Independent BLAKE2b, sketch and SimHash oracle for pinned SIMURG.

Runs original upstream functions in fresh Python processes using four distinct
PYTHONHASHSEED values; external GNU b2sum verifies unkeyed BLAKE2b digest.
No model, web, production, target repo change, or private text.
"""
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SOURCE = Path(os.environ["SIMURG_SOURCE"])
WORKER = Path(__file__).with_name("2026-11-07-hash-worker.py")
OUTPUT = Path(os.environ["OUTPUT"])
REV = "2831a92359cdaf1b38cc14f55e74251e09a91e0b"
FILES = {
    "src/simurg/core.py": "8d0f7509146e62cbf0a1f485eb6e08935d014659e97f2157879178baf2dfa8cd",
    "src/simurg/signals/sketch.py": "453a24545e0ae0150d05526a5c8e5d32eb761d97e7b5b6b1b9e7d11f76c4a841",
    "src/simurg/signals/simhash.py": "419bf411f7fb18bfe89bd16ef271ce7f5be16b3344ef6724fa19ce4d0be94e3a",
}
SEEDS = (0, 1, 42, 1337)
TOKENS = ("postgresql", "SQL Server", "повторение", "audit", "alpha",
          "beta", "123456", "🙂", "schema", "schema", "schema", "cache")
SHINGLE = ("schema", "cache", "query", "schema", "cache", "schema",
           "query", "cache", "schema", "vacuum", "schema", "cache")


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def independent_hash(token, seed=0):
    raw = seed.to_bytes(8, "little") if seed else b""
    return int.from_bytes(hashlib.blake2b(
        token.encode("utf-8"), key=raw, digest_size=8).digest(), "little")


def independent_sketch():
    depth, width = 4, 256
    rows = [[0] * width for _ in range(depth)]
    additions = []
    expected_cols = {}
    for text in SHINGLE:
        seeds = [0x9E3779B1*(index+1) & 0xFFFFFFFF for index in range(depth)]
        col = [independent_hash(text, seed) % width for seed in seeds]
        expected_cols[text] = col
        for row, column in zip(rows, col):
            row[column] += 1
        additions.append(min(rows[row][column] for row, column in enumerate(col)))
    return expected_cols, additions, {
        text: min(rows[row][col] for row, col in enumerate(expected_cols[text]))
        for text in set(SHINGLE)
    }


def independent_simhash():
    window = deque(maxlen=8)
    output = []
    baseline = None
    for idx, token in enumerate(TOKENS):
        window.append(independent_hash(token))
        fingerprint = 0
        for bit in range(64):
            difference = sum(1 if (n >> bit) & 1 else -1 for n in window)
            if difference > 0:
                fingerprint |= 1 << bit
        if idx == 7:
            baseline = fingerprint
        drift = (fingerprint ^ baseline).bit_count()/64 if baseline is not None and (
            len(window) >= 8) else 0.0
        output.append({"value":fingerprint, "baseline":baseline, "drift":drift})
    return output


def verify_actual(actual, expected_hashes, cols, additions, estimates, snapshots):
    if actual["stable"] != expected_hashes:
        return False
    if actual["sketch_cols"] != cols or actual["sketch_additions"] != additions:
        return False
    if actual["sketch_estimates"] != estimates:
        return False
    if actual["simhash_snapshots"] != snapshots:
        return False
    return True


def main():
    assert subprocess.check_output(
        ["git", "-C", str(SOURCE), "rev-parse", "HEAD"],
        text=True).strip() == REV
    for name, digest in FILES.items():
        assert sha((SOURCE / name).read_bytes()) == digest
    expected_hashes = {
        token: {key: independent_hash(token, seed) for key, seed in (
            ("unseeded",0),("seeded_1",1),("seeded_12345",12345))}
        for token in TOKENS
    }
    for token in set(TOKENS):
        result = subprocess.run(["b2sum", "-l", "64"], input=token.encode("utf-8"),
                                capture_output=True, check=True)
        b2sum_hex = result.stdout.decode().split()[0]
        assert b2sum_hex == independent_hash(token).to_bytes(8,"little").hex()
    cols, additions, estimates = independent_sketch()
    snapshots = independent_simhash()
    records = []
    builtin = set()
    for seed in SEEDS:
        env = dict(os.environ, PYTHONHASHSEED=str(seed),
                   PYTHONDONTWRITEBYTECODE="1")
        process = subprocess.run([sys.executable, "-B", str(WORKER), str(SOURCE)],
                                 capture_output=True, text=True, env=env,
                                 check=True, timeout=20)
        record = json.loads(process.stdout)
        assert verify_actual(record, expected_hashes, cols, additions,
                             estimates, snapshots)
        builtin.add(record["builtin_hash_control"])
        fixed = {key:value for key,value in record.items()
                 if key != "builtin_hash_control"}
        records.append({
            "pythonhashseed":seed,
            "source_result_sha256":sha(json.dumps(
                fixed,ensure_ascii=False,sort_keys=True).encode("utf-8")),
            "native_builtin_hash_control":record["builtin_hash_control"],
            "matches_external_oracle":True,
        })
    assert len(set(r["source_result_sha256"] for r in records)) == 1
    assert len(builtin) == len(SEEDS), "Builtin hash negative control unexpectedly stable"
    forged = dict(expected_hashes)
    forged["schema"] = dict(forged["schema"], unseeded=0)
    assert not verify_actual(dict(stable=forged, sketch_cols=cols,
                                  sketch_additions=additions,
                                  sketch_estimates=estimates,
                                  simhash_snapshots=snapshots),
                             expected_hashes, cols, additions, estimates, snapshots)
    corrupted = [dict(record) for record in snapshots]
    corrupted[-1]["value"] ^= 1
    assert corrupted != snapshots
    output = {
        "date":"2026-11-07","study":"simurg",
        "source_pin":REV,"file_sha256":FILES,
        "worker_source_sha256":sha(WORKER.read_bytes()),
        "pythonhashseed_cases":list(SEEDS),
        "cross_process_checks_passed":len(records),
        "unkeyed_external_b2sum_checks":len(set(TOKENS)),
        "seeded_hash_oracle":"Python standard hashlib.blake2b, independent of source function",
        "unkeyed_hash_oracle":"GNU b2sum -l 64, independent implementation/process",
        "sketch_oracle":"reconstructed independent count-min bucket arrays with keyed hashes",
        "simhash_oracle":"independent per-token window and 64-bit majority recomputation",
        "records":records,"expected_unkeyed":{k:v["unseeded"]
                                               for k,v in expected_hashes.items()},
        "expected_sketch_columns":cols,
        "expected_sketch_additions":additions,
        "expected_simhash_snapshots":snapshots,
        "negative_controls":{
            "builtin_hash_changes_with_seed":len(builtin)==len(SEEDS),
            "tampered_stable_hash_rejected":True,
            "tampered_simhash_result_rejected":True,
        },
        "status":"PASS_BOUNDED_CROSS_PROCESS_STABILITY",
        "limitations":[
            "4 distinct PYTHONHASHSEED processes and 12 tokens, not statistical detector accuracy",
            "No SIMURG streaming guard, false-alarm calibration, AUROC or LLM exercised here",
            "Hashlib based independent keyed oracle uses the same public BLAKE2b algorithm",
            "Cross-process determinism is required for reproducible sketch buckets but does not prove collision resistance or semantic similarity",
            "No actual dsh-runtime or 9router integration, security enforcement or production workload",
        ]
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "seed_variants":len(records),
        "unkeyed_b2sum_verified":len(set(TOKENS)),
        "sketch_additions":len(additions),
        "simhash_snapshots":len(snapshots),
        "builtin_negative_control":True,
    }))


if __name__=="__main__":
    main()
