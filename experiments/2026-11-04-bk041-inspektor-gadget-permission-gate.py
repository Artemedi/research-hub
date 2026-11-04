#!/usr/bin/env python3
"""Inspektor Gadget v0.57.0: nonprivileged BPF readiness and CLI guard check.

No sudo, no rootless privileged container, no gadget execution, no kernel mount.
This is an ENVIRONMENT GATE, not a tracer performance/effectiveness lab.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess


def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def bpf_map_create_unprivileged():
    # x86_64: BPF syscall 321, cmd=0 (BPF_MAP_CREATE), Array map 1,
    # fixed 4-byte key/value and one map element.
    # Guard below prevents test when running with effective capabilities.
    libc = ctypes.CDLL(None, use_errno=True)
    attrs = (ctypes.c_uint32 * 16)()
    attrs[0], attrs[1], attrs[2], attrs[3] = 1, 4, 4, 1
    fd = libc.syscall(321, 0, ctypes.byref(attrs), ctypes.sizeof(attrs))
    err = ctypes.get_errno()
    if fd >= 0:
        os.close(fd)
    return {"result_fd_sign": "negative" if fd < 0 else "nonnegative",
            "errno": err, "errno_name": os.strerror(err)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--release-tar", type=Path, required=True)
    p.add_argument("--expected-sha256", required=True)
    args = p.parse_args()
    actual_sha = hashlib.file_digest(args.release_tar.open("rb"), "sha256").hexdigest()
    if actual_sha != args.expected_sha256:
        p.error(f"release SHA256 mismatch: got {actual_sha}")
    output = subprocess.run(
        [str(args.binary), "version"], capture_output=True,
        text=True, timeout=6, check=True,
    )
    version = output.stdout.strip()
    assert version == "v0.57.0", version
    help_out = subprocess.run(
        [str(args.binary), "run", "--help"], capture_output=True,
        text=True, timeout=6, check=True,
    ).stdout
    flags = ["--disallow-pulling", "--verify-image",
             "--allowed-gadgets", "--timeout"]
    assert all(flag in help_out for flag in flags)
    cap_hex = read("/proc/self/status")
    lines = dict(
        ln.split(":", 1) for ln in cap_hex.splitlines() if ":" in ln
    )
    capeff = int(lines["CapEff"].strip(), 16)
    kernel_btf = Path("/sys/kernel/btf/vmlinux").is_file()
    unpriv = read("/proc/sys/kernel/unprivileged_bpf_disabled")
    probe = {
        "skipped": "unsafe: privileged user or unsupported architecture"
    }
    if platform.machine() == "x86_64" and capeff == 0 and unpriv in ("1", "2"):
        probe = bpf_map_create_unprivileged()
        assert probe["errno"] == 1, probe
    elif capeff == 0 and unpriv == "0":
        probe = {"skipped": "unprivileged BPF allowed; no kernel test without approval"}
    result = {
        "source": "Official github.com/inspektor-gadget/inspektor-gadget release",
        "release": version,
        "release_tar_sha256": actual_sha,
        "kernel": platform.release(),
        "btf_vmlinux_present": kernel_btf,
        "unprivileged_bpf_disabled": unpriv,
        "effective_caps_hex": lines["CapEff"].strip(),
        "bpf_map_create_probe": probe,
        "original_cli_run_flags_present": flags,
        "tracing_performed": False,
        "gadget_downloads": 0,
        "root_or_host_mount_changes": 0,
        "status": (
            "RUNTIME_BLOCKED_UNPRIVILEGED"
            if capeff == 0 and probe.get("errno") == 1
            else "RUNTIME_NOT_VERIFIED"
        ),
        "limitations": [
            "BPF_MAP_CREATE permission gate is a syscall test, NOT a live Inspektor Gadget trace.",
            "No eBPF program loaded; cannot measure syscall/TCP evidence completeness or overhead.",
            "Host eBPF tracing requires explicit privilege and security authorization in nonprod.",
            "No production claims for PostgreSQL/MSSQL RCA or kernel support per gadget.",
        ],
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()