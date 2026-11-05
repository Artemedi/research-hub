#!/usr/bin/env bash
# Portable packaging of the observed lab command. No host display/home/network mounts.
# Usage: bash this.sh /absolute/path/to/cargo-target /absolute/path/to/gui-probe.py
set -euo pipefail
target=$(realpath "${1:?cargo target directory required}")
probe=$(realpath "${2:?authored GTK probe required}")
test -x "$target/debug/agent-desktop"
test -f "$probe"
lab=$(mktemp -d /tmp/bk065-synthetic.XXXXXXXX)
printf '%s\n' "$lab"
printf 'root:x:0:0:root:/root:/bin/bash\nlab:x:1000:1000:lab:/home:/bin/bash\n' > "$lab/passwd"
printf 'root:x:0:\nlab:x:1000:\n' > "$lab/group"
printf '11111111111111111111111111111111\n' > "$lab/machine-id"
for run in 1 2 3; do
  mkdir -p "$lab/run$run/home"
  timeout 60 bwrap --unshare-all --die-with-parent \
    --ro-bind /usr /usr --symlink usr/bin /bin \
    --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
    --ro-bind "$lab/passwd" /etc/passwd --ro-bind "$lab/group" /etc/group \
    --ro-bind "$lab/machine-id" /etc/machine-id \
    --ro-bind "$target" /target --ro-bind "$probe" /probe.py \
    --bind "$lab/run$run/home" /home --bind "$lab/run$run" /evidence \
    --tmpfs /tmp --tmpfs /run --proc /proc --dev /dev --clearenv \
    --setenv PATH /usr/bin --setenv HOME /home --setenv GSETTINGS_BACKEND memory \
    --setenv WLR_BACKENDS headless --setenv WLR_RENDERER pixman \
    --setenv WLR_LIBINPUT_NO_DEVICES 1 --setenv XDG_RUNTIME_DIR /run/private \
    --setenv GTK_A11Y always --setenv AGENT_DESKTOP_HOME /home/ad-state \
    /usr/bin/bash -c 'mkdir -m700 /run/private; exec dbus-run-session -- cage -d -- python3 /probe.py' \
    > "$lab/run$run/launch.log" 2>&1
  python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r.get("passed") and len(r["cases"])==4' "$lab/run$run/gui-probe.json"
done
# Artifacts retained for inspection. Do not bind host UI sockets to bypass a refusal.
