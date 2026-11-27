#!/usr/bin/env bash
set -euo pipefail
export PATH=/opt/go/bin:$PATH GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOMODCACHE=/cache/mod GOCACHE=/out/gocache HOME=/tmp
mkdir -p /out/gocache /out/work
cp -a /src/. /out/work/
cd /out/work
go version
echo '=== build ==='
go build -trimpath -o /out/gshell .
go version -m /out/gshell
sha256sum /out/gshell
echo '=== vet ==='
go vet ./...
echo '=== format ==='
test -z "$(gofmt -l .)"
echo '=== upstream tests ==='
go test ./...
echo '=== CLI smoke ==='
export XDG_CONFIG_HOME=/tmp/gshell-test-config
/out/gshell --version
/out/gshell --help | head -15
/out/gshell config set project valid-project
/out/gshell config show
if /out/gshell config set project 'bad;project'; then exit 1; fi
if /out/gshell auth status; then exit 1; fi
if /out/gshell cp a b; then exit 1; fi
echo 'CLI_SMOKE_PASS'
echo '=== synthetic SFTP ==='
cp /fixture/audit_test.go internal/ssh/audit_test.go
go test -count=1 -v -timeout=60s ./internal/ssh -run TestAuditTransfer
echo 'AUDIT_PASS'
