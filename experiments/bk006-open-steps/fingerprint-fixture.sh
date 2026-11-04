#!/usr/bin/env bash
# Run only inside the documented disposable bubblewrap environment.
set -euo pipefail
pack=/source
fixture=/tmp/fixture
expected=4fa744ba8ea06ccf128a39853824c46ac391dd00
[ "$(git -C "$pack" rev-parse HEAD)" = "$expected" ] || { echo 'wrong source revision'; exit 1; }
mkdir -p "$fixture" "$HOME"
cd "$fixture"
git init -q
printf 'baseline\n' > tracked.txt
git add tracked.txt
git -c user.name=Fixture -c user.email=fixture@example.invalid commit -qm baseline
printf 'before\n' > new.txt
payload='{"session_id":"bk006-fixture"}'
printf '%s' "$payload" | bash "$pack/hooks/session-start.sh" >/dev/null
before=$(sha256sum new.txt | cut -d ' ' -f 1)
printf 'after\n' > new.txt
after=$(sha256sum new.txt | cut -d ' ' -f 1)
[ "$before" != "$after" ]
set +e
out=$(printf '%s' "$payload" | OPEN_STEPS_COOLDOWN=0 bash "$pack/hooks/stop-report.sh" 2>&1)
status=$?
set -e
printf 'untracked content changed: yes\nstop after untracked edit: %s\n' "$status"
[ "$status" -eq 0 ] && [ -z "$out" ] || exit 1
printf 'changed\n' > tracked.txt
set +e
out=$(printf '%s' "$payload" | OPEN_STEPS_COOLDOWN=0 bash "$pack/hooks/stop-report.sh" 2>&1)
status=$?
set -e
printf 'stop after tracked edit: %s\n' "$status"
[ "$status" -eq 2 ] && [[ "$out" == *'Work landed'* ]] || exit 1
printf 'fixture result: reproduced (limited scope)\n'
