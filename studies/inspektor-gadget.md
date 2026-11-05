# Inspektor Gadget

[Структурированная запись и связи](../catalog/studies/inspektor-gadget.md)

**Telegram source:** BK-041 / 08.10.2026; [official repository](https://github.com/inspektor-gadget/inspektor-gadget).
**Evidence type:** full first-party docs and verified official binary; **not** a peer-reviewed research paper. Not a source-level security audit of the entire project.
**Source pin:** [v0.57.0](https://github.com/inspektor-gadget/inspektor-gadget/tree/v0.57.0), tag SHA `29d60de9f7924607784915533dd5f3cc0052ee1a`; official release tar SHA-256 `f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1`.
**Full report:** [2026-11-04 Bazzite eBPF permission gate](../reviews/inspektor-gadget/2026-11-04.md) · [reproducible script](../experiments/2026-11-04-bk041-inspektor-gadget-permission-gate.py) · [results JSON](../data/results/inspektor-gadget/2026-11-04.json).

**Original tool execution:** `ig version` → v0.57.0; `ig run --help` confirmed `--verify-image`, `--allowed-gadgets`, `--disallow-pulling`, and timeout control. Bazzite 44 `6.18.56` had BTF, `CapEff=0`, `kernel.unprivileged_bpf_disabled=2`, and a minimal unprivileged `BPF_MAP_CREATE` returned `EPERM`. No gadget image pulled or eBPF program loaded.

**Decision:** `AWAITING_REAL_NONPROD_GADGET_TRACE / PERMISSION_GATE_VERIFIED`, not a verified DBA RCA benefit. Target possibilities: Linux/PostgreSQL AKUZ process/file/network events and `sequential-rca` evidence ingestion *only if source-level seam and independent event oracle are confirmed*. Does not apply directly to Windows SQL Server. Requires owner-approved isolated elevated nonprod lab, event completeness/overhead metrics, pinned verified Gadget images. No production approval.
