# gshell — remote execution, SFTP and Cloud Shell lifecycle

[Структурированная запись и связи](../catalog/studies/gshell.md)

**Pinned:** [Spectra010s/gshell@4b5ca398a37af94fd36993a59dad4b4e99f8ea7c](https://github.com/Spectra010s/gshell/tree/4b5ca398a37af94fd36993a59dad4b4e99f8ea7c), MIT, Go 1.27. Engineering source review; all 24 tracked Go files (2563 lines), command/install/release documentation and scripts examined; not an external dependency or CVE audit.

**Evidence:** isolated Linux amd64 build, vet, formatting, CLI smoke and SFTP roundtrip/dry-run passed. No upstream automated tests. Paired 5-mode SFTP test (3 repeats per mode) observed full remote reads on unchanged sync and two reads on changed download. Independent Paper2Project reproduction arms passed 8/8 checks with immutable source/input trees. Full read in both arms disproves network traffic benefit for unchanged-file fixture. Four additional offline risk probes reproduced untrusted SSH key acceptance, destructive destination truncation, unchanged 0644 credential permissions and HTTP error polling. Target project benefit not established; no independent reviewer or live Google account.

**Risks:** SSH host key verification disabled; non-atomic transfers, ignored traversal/close errors, flattened exit code, unbounded prepare, credential storage, command/path handling. Do not copy these defaults. Research reference only; direct adoption blocked pending current target source and independent acceptance.

**Materials:** [review](../reviews/gshell/2026-11-27.md) · [paired protocol](../experiments/gshell/protocol.md) · [formal protocol](../experiments/gshell/engine-protocol.md) · [fixture](../experiments/gshell/audit_test.go) · [build and lab log](../data/results/gshell/2026-11-27-build-and-lab.log) · [formal result](../data/results/gshell/2026-11-27-paper2project.json) · [summary](../data/results/gshell/2026-11-27.json).
