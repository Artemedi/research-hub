#!/usr/bin/env bash
# Reproduce bounded P0 source-function A/B without any outbound network.
set -euo pipefail
root="$(cd "$(dirname "$0")/../../.." && pwd)"
projects="$(dirname "$root")"
command -v bwrap >/dev/null || { echo 'BLOCKED: bwrap is required; will not fall back to host networking' >&2; exit 10; }
snap="$(mktemp -d /tmp/p0-snapshot.XXXXXXXX)"
cleanup() {
    case "$snap" in /tmp/p0-snapshot.*) rm -rf -- "$snap";; esac
}
trap cleanup EXIT
cd "$root"
python3 - "$snap" "$projects" <<'PY'
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

dest=Path(sys.argv[1])
projects=Path(sys.argv[2])
matrix=json.loads(Path("data/project-fit/portfolio/2026-11-09-targeted-fit.json").read_text())
for name,file in (
    ("TelegramBot","main.py"),
    ("agent-config","tools/review.py"),
    ("Wiki_PG","Wiki_PG/ingestion/retrieval_service.py"),
):
    matching=[row["source_anchor"] for row in matrix["pairs"]
              if row["source_anchor"] is not None
              and row["source_anchor"]["repo"]==name
              and row["source_anchor"]["path"]==file]
    if not matching:
        raise SystemExit(f"BLOCKED: missing source pin for {name}")
    pin=matching[0]
    assert all(r["commit"]==pin["commit"] and r["file_sha256"]==pin["file_sha256"] for r in matching)
    archive=subprocess.check_output([
        "git","-C",str(projects/name),"archive","--format=tar",pin["commit"],file,
    ])
    directory=dest/name
    directory.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        assert [m.name for m in tar.getmembers() if m.isfile()]==[file]
        tar.extractall(directory,filter="data")
    actual=hashlib.sha256((directory/file).read_bytes()).hexdigest()
    assert actual==pin["file_sha256"],f"PIN MISMATCH: {name}:{file}"
    print(f"VERIFIED_PIN {name}@{pin['commit']} {file} sha256:{actual}")
PY
bwrap --unshare-net --die-with-parent \
  --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib64 /lib64 \
  --dev /dev --proc /proc --tmpfs /tmp \
  --dir /source --dir /out \
  --ro-bind "$snap" /source \
  --ro-bind "$root/experiments/research-portfolio/p0-20261110/isolated_ab.py" /runner.py \
  --bind "$root/data/results/research-portfolio" /out \
  --setenv HOME /tmp --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 /runner.py --source /source --out /out/2026-11-10-p0-boundary-ab.json
