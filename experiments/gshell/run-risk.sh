#!/usr/bin/env bash
set -euo pipefail
export PATH=/opt/go/bin:$PATH GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOMODCACHE=/cache/mod GOCACHE=/out/gocache HOME=/tmp
mkdir -p /out/gocache /out/riskwork
cp -a /src/. /out/riskwork/
cd /out/riskwork
cp /fixture/risk_ssh_test.go internal/ssh/risk_audit_test.go
cp /fixture/risk_auth_test.go internal/auth/risk_audit_test.go
cp /fixture/risk_api_test.go internal/cloudshell/risk_audit_test.go
go test -count=1 -v -timeout=40s ./internal/ssh ./internal/auth ./internal/cloudshell -run 'TestAudit(DestinationLoss|HostIdentityAndExit|ExistingCredentialMode|PollingHTTPError)$'
