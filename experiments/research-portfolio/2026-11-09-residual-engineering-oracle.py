#!/usr/bin/env python3
"""Recheck four pinned public source helpers in no-network Bwrap; no model calls.

Acquisition is separate and must use the immutable refs listed in reviews.
The script refuses unrecognized bytes or non-deterministic fixture results.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

PINNED = {
    "julia-1": {
        "source": "julia/probabilities.py",
        "sha256": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206",
        "pin": "a85b127321d580d65176c89ced8273f305745d85",
        "fixture": "experiments/bk026-julia/display_fixture.py",
        "expected": ["3/3 presentation fixtures passed; model inference NOT_RUN"],
    },
    "yahont-ce": {
        "source": "yahont/string_filtering.py",
        "sha256": "511568e3cd0e6b45a81769699b40440b1f77276db26a919aff619977a8e6fea8",
        "pin": "367b48da9de2d296f905aca4bf0eb384043bf643",
        "fixture": "experiments/bk053-yahont/id-fixture.py",
        "expected": ["a/b -> ab", "ab -> ab", "doc_1 -> doc_1"],
    },
    "warp-skill-doctor": {
        "source": "warp/collect_sessions.py",
        "sha256": "c74dabd95dad57421177fa9ead27882a571e7fe24d26eafbbafad1974c019658",
        "aux_sha256": "afc99fe98306c1a0dd537ef63a23ec891ff7e9f7146410e6a5e4cda86f3fdf83",
        "pin": "8792394ff1b655e0af451b8fabb68ef0cfcbd208",
        "fixture": "experiments/bk019-skill-doctor/attribution-fixture.py",
        "expected": ["own_child: True", "unrelated_same_name: True", "unrelated_other_name: False"],
    },
    "microsoft-skill-recorder": {
        "source": "ms-recorder/common/sensitive.ts",
        "sha256": "318b34ad298e73f683a1f1b55b87d8d830158209826cb3eed8c38116156154d9",
        "pin": "505c97ae47be5642c0e1b44ebb8d1c1530c298fa",
        "fixture": "experiments/bk022-skill-recorder/pii-fixture.mjs",
        "expected": ["synthetic_email [\"email\"]", "synthetic_medical []", "clean []"],
    },
    "local-knowledge-graph": {
        "source": "local-knowledge/mpe_lkg/graph.py",
        "sha256": "a4faedce7752c4f192d7bc06d727e1fe272da90986fc6fc2e9055c865f6f8f75",
        "pin": "58fce402c7d15a3f5abcc8d0b1e920c1be5071b5",
        "fixture": "experiments/bk024-local-knowledge-graph/paths-fixture.py",
        "expected": ["directed_edges_only: False", "path: ['1', '3', '2', '4']",
                     "alternative product: 0.729 mean: 0.9"],
    },
    "open-steps": {
        "source": "open-steps/hooks/fingerprint.sh",
        "sha256": "0433d8ed704260668a3974c6c9eee85949fef3feb01b0b17a2813b62f4f8bb0b",
        "pin": "4fa744ba8ea06ccf128a39853824c46ac391dd00",
        "fixture": "experiments/bk006-open-steps/fingerprint-fixture.sh",
        "expected": ["untracked content changed: yes",
                     "stop after untracked edit: 0",
                     "stop after tracked edit: 2",
                     "fixture result: reproduced (limited scope)"],
    },
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(root, sources, numpy_site, node_bin):
    records = []
    for sid, cfg in PINNED.items():
        src = sources / cfg["source"]
        assert src.is_file() and sha(src) == cfg["sha256"], f"source pin mismatch {sid}"
        src_folder = src.parent
        if sid == "warp-skill-doctor":
            aux = src_folder / "warp_decoder.py"
            assert aux.is_file() and sha(aux) == cfg["aux_sha256"]
        if sid == "microsoft-skill-recorder":
            src_folder = sources / "ms-recorder"
            assert node_bin.is_file()
        if sid == "local-knowledge-graph":
            src_folder = sources / "local-knowledge"
            assert numpy_site.is_dir()
        if sid == "open-steps":
            pin = subprocess.check_output(
                ["git", "-C", str(sources / "open-steps"), "rev-parse", "HEAD"],
                text=True).strip()
            assert pin == cfg["pin"]
            src_folder = sources / "open-steps"
        fixture = root / cfg["fixture"]
        assert fixture.is_file()
        base = [
            "bwrap", "--unshare-net", "--die-with-parent",
            "--ro-bind", "/usr", "/usr",
            "--symlink", "usr/bin", "/bin",
            "--symlink", "usr/lib64", "/lib64",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
            "--ro-bind", str(src_folder.resolve()), "/source",
            "--ro-bind", str(fixture.resolve()), "/fixture",
            "--setenv", "HOME", "/tmp/home",
            "--setenv", "PATH", "/usr/bin:/bin",
            "--setenv", "PYTHONPATH", "/source",
            "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        ]
        if sid == "local-knowledge-graph":
            base.extend(["--ro-bind", str(numpy_site.resolve()), "/deps",
                         "--setenv", "PYTHONPATH", "/source:/deps"])
        if sid == "microsoft-skill-recorder":
            base.extend(["--ro-bind", str(node_bin.resolve()), "/node"])
            command = ["/node", "--experimental-transform-types", "/fixture"]
        elif sid == "open-steps":
            command = ["/usr/bin/bash", "/fixture"]
        else:
            command = ["/usr/bin/python3", "/fixture"]
            if sid in ("julia-1", "yahont-ce"):
                command += ["/source/" + src.name]
        outcomes = []
        for rep in range(2):
            proc = subprocess.run(
                base + command, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=30,
                env={"PATH": "/usr/bin:/bin"}, check=False)
            assert proc.returncode == 0, f"{sid} rep {rep}: {proc.stderr[:400]}"
            for text in cfg["expected"]:
                assert text in proc.stdout, f"{sid}: missing fixture outcome {text}"
            outcomes.append({
                "run": rep, "exit": proc.returncode,
                "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
                "stdout_excerpt": proc.stdout.strip(),
            })
        assert outcomes[0]["stdout_sha256"] == outcomes[1]["stdout_sha256"], f"{sid} repeat mismatch"
        records.append({
            "study": sid, "source_pin": cfg["pin"],
            "source_file_sha256": cfg["sha256"],
            "fixture_path": cfg["fixture"], "fixture_sha256": sha(fixture),
            "repetitions": outcomes, "passed": True,
            "original_complete_suite_reexecuted": False,
        })
    return {
        "date": "2026-11-09",
        "environment": "Bazzite Linux rootless bwrap read-only original public blobs, no network, no production, no personal/project inputs",
        "scope": "Six original pure helpers/hook contracts only, sourced from immutable public revision URLs; two identical replays per case.",
        "records": records, "status": "PASS_BOUNDED",
        "limitations": [
            "Pinned file SHA proves exact downloaded bytes used, but source retrieval itself was separate and not authenticated against a signed upstream release.",
            "No original full upstream test suite rerun, no consumer integration, no production service.",
            "All input paths, decisions and outputs are synthetic.",
            "No real privacy leak, unauthorized filesystem effect, model accuracy or search-system impact demonstrated."
        ]
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources-root", type=Path, required=True)
    parser.add_argument("--numpy-site", type=Path, required=True)
    parser.add_argument("--node-bin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    obj=run(Path(__file__).resolve().parents[2], args.sources_root.resolve(), args.numpy_site.resolve(), args.node_bin)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ISOLATED_ENGINEERING_ORACLE", obj["status"], len(obj["records"]),"source checks x2")

if __name__ == "__main__":
    main()
