"""Reassemble the historical KVSET delivery ZIP without executing packaged code."""

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
from unittest.mock import patch
import zipfile
import zlib

PILOT = "6418c2397fd16a73cba58990fca2f6801e01148c"
CURRENT = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
UPSTREAM = "fab8ac99017e4ca6f22c811ee874b72a2e1a7296"
PILOT_DIR = "experiments/kvset/"
VENDOR_DIR = "vendor/kv_cache_capacity_estimator"
ZIP_ROOT = "kvset-mcp/"
EXPECTED_ZIP = "cef186cc5b9a6bd52f58f7172e26c723aaf3fadf8e113ff04a9e9e14e369f766"
GENERATED = {"admission.json", "SOURCE-PROVENANCE.json"}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def blob(repo, revision, path):
    return git(repo, "cat-file", "blob", f"{revision}:{path}")


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def document(value):
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def parts_sorted(paths):
    return sorted(paths, key=lambda path: PurePosixPath(path).parts)


def rebuild(pilot, upstream):
    inventory = json.loads(blob(pilot, PILOT, PILOT_DIR + "reports/package-inventory.json"))
    delivery = json.loads(blob(pilot, PILOT, PILOT_DIR + "reports/delivery-validation.json"))
    expected = inventory["files"]
    if (inventory["sha256"] != EXPECTED_ZIP or delivery["archive_sha256"] != EXPECTED_ZIP
            or delivery["packaged_files"] != expected or not delivery["success"]):
        raise ValueError("The pinned inventory and delivery record disagree")

    admission_bytes = blob(pilot, PILOT, PILOT_DIR + "admission.json")
    admission = json.loads(admission_bytes)
    if admission["commit"] != UPSTREAM:
        raise ValueError("Unexpected admitted upstream commit")
    paths = git(upstream, "ls-tree", "-r", "--name-only", "-z", UPSTREAM).decode().strip("\0").split("\0")
    selected = parts_sorted(path for path in paths if path.startswith("src/") or path in
                            {"LICENSE", "README.md", "README.zh-CN.md", "pyproject.toml"})
    vendor = {path: blob(upstream, UPSTREAM, path) for path in selected}
    vendor_hashes = {path: digest(payload) for path, payload in vendor.items()}
    if any(admission["files"].get(path) != sha for path, sha in vendor_hashes.items()):
        raise ValueError("Upstream bytes disagree with the pilot admission record")

    runtime_names = {path for path in expected if not path.startswith(VENDOR_DIR + "/")} - GENERATED
    entries = {path: blob(pilot, PILOT, PILOT_DIR + path) for path in runtime_names}
    entries.update({f"{VENDOR_DIR}/{path}": payload for path, payload in vendor.items()})
    entries["admission.json"] = document(dict(admission, source_path=VENDOR_DIR, files=vendor_hashes))
    entries["SOURCE-PROVENANCE.json"] = document({
        "repository": admission["url"], "commit": UPSTREAM, "paper": admission["paper"],
        "license": admission["license"], "original_admission_sha256": digest(admission_bytes),
        "scope": "Unchanged author source files needed by offline token-ID analysis; no paper assets or scientific replacements.",
        "files": vendor_hashes,
    })
    actual = {name: digest(payload) for name, payload in entries.items()}
    if actual != expected:
        different = sorted(path for path in actual.keys() | expected.keys() if actual.get(path) != expected.get(path))
        raise ValueError("Package inventory differs: " + ", ".join(different))
    return inventory, entries, runtime_names, len(vendor)


def zip_bytes(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in parts_sorted(entries):
            info = zipfile.ZipInfo(ZIP_ROOT + name, date_time=(2026, 10, 31, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entries[name])
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot_repo", type=Path)
    parser.add_argument("upstream_repo", type=Path)
    parser.add_argument("--output", type=Path, help="Write a new ZIP only if its historical digest matches.")
    parser.add_argument("--zlib-ng", action="store_true", help="Try the optional zlib-ng compressor.")
    args = parser.parse_args()
    compressor, backend = zlib, "zlib " + zlib.ZLIB_RUNTIME_VERSION
    if args.zlib_ng:
        from zlib_ng import zlib_ng
        compressor, backend = zlib_ng, "zlib-ng " + zlib_ng.ZLIBNG_RUNTIME_VERSION
    inventory, entries, runtime_names, vendor_count = rebuild(args.pilot_repo, args.upstream_repo)
    with patch.object(zipfile, "zlib", compressor):
        package = zip_bytes(entries)
        if zip_bytes(entries) != package:
            raise AssertionError("ZIP bytes changed on repeat")
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        expected_names = [ZIP_ROOT + name for name in parts_sorted(entries)]
        if archive.namelist() != expected_names or archive.testzip() is not None:
            raise AssertionError("Rebuilt ZIP contains an invalid entry")
        if any(digest(archive.read(ZIP_ROOT + name)) != sha for name, sha in inventory["files"].items()):
            raise AssertionError("Archived payload differs from the inventory")
    rebuilt_sha = digest(package)
    exact = rebuilt_sha == EXPECTED_ZIP and len(package) == inventory["bytes"]
    changed = [name for name in sorted(runtime_names)
               if digest(blob(args.pilot_repo, CURRENT, PILOT_DIR + name)) != inventory["files"][name]]
    if args.output:
        if not exact:
            parser.error("Rebuilt payload matches the inventory, but ZIP bytes differ")
        with args.output.open("xb") as stream:
            stream.write(package)
    print(json.dumps({
        "pilot_revision": PILOT, "upstream_revision": UPSTREAM, "current_paper2project_revision": CURRENT,
        "repeat_count": 2, "manifest_entries_verified": len(entries), "vendor_entries_verified": vendor_count,
        "current_runtime_files_differing": changed, "historical_zip_bytes": inventory["bytes"],
        "historical_zip_sha256": EXPECTED_ZIP, "rebuilt_zip_bytes": len(package), "rebuilt_zip_sha256": rebuilt_sha,
        "zip_exact_match": exact, "compressor": backend,
    }, indent=2))


if __name__ == "__main__":
    main()
