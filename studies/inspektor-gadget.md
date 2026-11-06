# Inspektor Gadget

[Структурированная запись и связи](../catalog/studies/inspektor-gadget.md)

**Telegram source:** BK-041 / 08.10.2026; [official repository](https://github.com/inspektor-gadget/inspektor-gadget).
**Evidence type:** full first-party docs and verified official binary; **not** a peer-reviewed research paper. Not a source-level security audit of the entire project.
**Source pin:** [v0.57.0](https://github.com/inspektor-gadget/inspektor-gadget/tree/v0.57.0), tag SHA `29d60de9f7924607784915533dd5f3cc0052ee1a`; official release tar SHA-256 `f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1`.
**Full report:** [2026-11-04 Bazzite eBPF permission gate](../reviews/inspektor-gadget/2026-11-04.md) · [reproducible script](../experiments/2026-11-04-bk041-inspektor-gadget-permission-gate.py) · [results JSON](../data/results/inspektor-gadget/2026-11-04.json).

**Original tool execution:** `ig version` → v0.57.0; `ig run --help` confirmed `--verify-image`, `--allowed-gadgets`, `--disallow-pulling`, and timeout control. Bazzite 44 `6.18.56` had BTF, `CapEff=0`, `kernel.unprivileged_bpf_disabled=2`, and a minimal unprivileged `BPF_MAP_CREATE` returned `EPERM`. No gadget image pulled or eBPF program loaded.

**Decision (updated 2026-11-06):** `BOUNDED_SYNTHETIC_EBPF_VERIFIED / NOT_PRODUCTION_READY`. The original 2026-11-04 permission-gate results remain historical; a subsequent approved privileged rootless Podman test demonstrated 5 × 40/40 synthetic exec detections with 0/25 negative controls, provided `--filter.exec proc.comm==bk041exec` was used. `--comm` unexpectedly yielded 0/40 on the same container. See [full privileged Podman audit](../reviews/inspektor-gadget/2026-11-06-privileged-podman-trace.md), [aggregate JSON](../data/results/inspektor-gadget/2026-11-06-podman-trace.json), and [reproduction script](../experiments/2026-11-06-bk041-podman-trace.py). Production overhead and project integration remain unverified. `--output json` contains command arguments and paths even with `--fields`; never publish raw traces. AKUZ Linux/PostgreSQL and `sequential-rca` are conditional candidates only; Windows MSSQL is out of scope. No production approval.

**Дополнительные сохранённые доказательства:** [host diagnostic 0/40](../data/results/inspektor-gadget/2026-11-06-host-diagnostics.json), [initial host pilot 0/40](../data/results/inspektor-gadget/2026-11-06-host-pilot.json), [host diagnostic reproduction](../experiments/2026-11-06-bk041-host-diagnostic.py). Raw JSONL и stderr с чувствительными полями не публикуются.
