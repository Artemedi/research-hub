#!/usr/bin/env bash
set -euo pipefail

image=${1:?Built Agent Desktop image required}
toolkit=${2:?qt or electron required}
fixture=$(dirname "$(realpath "$0")")
mounts=(--mount "type=bind,source=$fixture,target=/fixture,readonly")
case "$toolkit" in
  qt) ;;
  electron)
    electron=$(realpath "${3:?Verified, unpacked Electron directory required}")
    test -x "$electron/electron"
    mounts+=(--mount "type=bind,source=$electron,target=/electron,readonly")
    ;;
  *) echo 'Expected qt or electron.' >&2; exit 2 ;;
esac

for _ in 1 2 3; do
  timeout 70 docker run --rm --init --network none --read-only --user 65534:65534 \
    --cap-drop ALL --security-opt no-new-privileges --cpus 2 --memory 1536m --pids-limit 256 \
    --tmpfs /tmp:rw,exec,nosuid,nodev,mode=1777,size=384m \
    "${mounts[@]}" "$image" /bin/bash -euc '
      export HOME=$(mktemp -d)
      export XDG_RUNTIME_DIR="$HOME/runtime" AGENT_DESKTOP_HOME="$HOME/ad-state"
      export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 QT_ACCESSIBILITY=1
      mkdir -m 700 "$XDG_RUNTIME_DIR"
      exec xvfb-run -a -e /dev/stderr -s "-screen 0 1024x768x24" dbus-run-session -- \
        /bin/bash -euc '"'"'
          openbox >"$HOME/openbox.log" 2>&1 &
          exec python3 /fixture/observe-toolkit.py /build/target/debug/agent-desktop "$1"
        '"'"' -- "$1"
    ' -- "$toolkit"
done
