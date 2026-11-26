"""Validate the saved Creator fixture receipt without executing plugin code."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

SKILLS_HEAD = "8170c5fd92de212132bca7374bb050ac635a2c01"
RECEIPT_SHA = "3fe59eae711914481a85c43c4bd1819b01bc24845328af22313ccb1376eac3e9"
MODE = "EXTERNAL_CODEX_GENERATION_PLUS_SYNTHETIC_CORDIS_RUN_CARD_VERIFIER"
CHECKS = {"default_title", "title_edit", "text_edit", "shader_colors_independent",
          "minimal_ui", "slot_scoped", "unload_cleanup", "missing_slot_safe", "invalid_source_rejected"}
ROOT = Path(__file__).resolve().parents[2]


def classify(code, manifest, record):
    if record["mode"] != MODE or record["creator_mode_real_e2e"] is not False:
        return "scope_mismatch"
    container = record["offline_container"]
    evidence = container["result"]
    if sha256(code).hexdigest() != record["plugin_code_sha256"]:
        return "code_digest_mismatch"
    if sha256(manifest).hexdigest() != record["plugin_manifest_sha256"]:
        return "manifest_digest_mismatch"
    if evidence["sha256"] != record["plugin_code_sha256"] or evidence["source_bytes"] != len(code):
        return "verifier_binding_mismatch"
    checks = evidence["checks"]
    if (set(checks) != CHECKS or not all(value is True for value in checks.values())
            or evidence["passes"] != len(CHECKS) or evidence["verdict"] != "PASS"):
        return "required_checks_missing_or_failed"
    if (container["rootless"] is not True or container["network"] != "none"
            or container["rootfs"] != "read-only"):
        return "offline_boundary_missing"
    return "offline_fixture_only"


def replay(code, manifest, receipt):
    missing, failed, relabeled, mismatched, boundary = (deepcopy(receipt) for _ in range(5))
    del missing["offline_container"]["result"]["checks"]["unload_cleanup"]
    failed["offline_container"]["result"]["checks"]["title_edit"] = False
    relabeled["creator_mode_real_e2e"] = True
    mismatched["offline_container"]["result"]["sha256"] = "0" * 64
    boundary["offline_container"]["rootless"] = False
    cases = {
        "historical_fixture": (code, manifest, receipt, "offline_fixture_only"),
        "changed_code": (code + b"\n", manifest, receipt, "code_digest_mismatch"),
        "changed_manifest": (code, manifest + b"\n", receipt, "manifest_digest_mismatch"),
        "cleanup_check_missing": (code, manifest, missing, "required_checks_missing_or_failed"),
        "title_check_failed": (code, manifest, failed, "required_checks_missing_or_failed"),
        "scope_relabeled": (code, manifest, relabeled, "scope_mismatch"),
        "verifier_hash_mismatch": (code, manifest, mismatched, "verifier_binding_mismatch"),
        "boundary_missing": (code, manifest, boundary, "offline_boundary_missing"),
    }
    results = {}
    for label, (code_bytes, manifest_bytes, record, expected) in cases.items():
        decision = classify(code_bytes, manifest_bytes, record)
        if decision != expected:
            raise AssertionError((label, decision, expected))
        results[label] = decision
    return results


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("agent_skills_checkout", type=Path)
    skills = cli.parse_args().agent_skills_checkout.resolve()
    git = ["git", "-C", str(skills)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != SKILLS_HEAD
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        cli.error(f"Expected clean agent-skills checkout at {SKILLS_HEAD}")
    suite = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"],
                           cwd=skills, capture_output=True, text=True, check=True, timeout=60)
    tests = int(re.search(r"Ran (\d+) tests", suite.stderr)[1])
    base = ROOT / "data/fixtures/dsh-creator/2026-11-06"
    report = (ROOT / "data/results/dsh-creator/2026-11-06-offline-poster-probe.json").read_bytes()
    if sha256(report).hexdigest() != RECEIPT_SHA:
        raise AssertionError("The historical receipt changed")
    inputs = ((base / "code.client.js").read_bytes(), (base / "manifest.json").read_bytes(), json.loads(report))
    results = replay(*inputs)
    if results != replay(*inputs):
        raise AssertionError("Repeat diverged")
    print(json.dumps({"agent_skills_revision": SKILLS_HEAD, "native_skills_tests_passed": tests,
                      "historical_report_sha256": RECEIPT_SHA, "recorded_fixture_checks": len(CHECKS),
                      "repeat_count": 2, "cases": results, "creator_runtime_executed": False}, indent=2))


if __name__ == "__main__":
    main()
