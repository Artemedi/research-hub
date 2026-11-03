# DeepSeek Harness — Research Watch (reconstructed 2026-10-05)

Coverage: **29 September – 05 October 2026**  
Status: **RECONSTRUCTED HISTORICAL INDEX — NOT A VERBATIM NEWSLETTER OR FULL-TEXT SCIENTIFIC REVIEW**  
Sources: prior DSH Research Watch conversation summaries, with the cited public source links supplied/recovered. Claims here are *historical editorial takeaways*, not a newly independently reproduced full-method assessment.

These weekly reports were not stored in `Artemedi/dsh/knowledge/research/` when originally issued. This backfill preserves the previously discussed candidates **without inventing missing newsletter prose**. Each candidate remains research knowledge only; read the complete primary paper (HTML/PDF/legitimate author version) before full scientific evaluation or promotion. If unavailable, mark `FULL_TEXT_UNAVAILABLE`. Current checkpoints come from `AGENTS.md` and `docs/iq-f1-orchestration/STATE.md`, not historical report wording.

## Historical findings and candidate experiments

### KVTether: Capture the lifecycle — KV Cache management in ReAct Agents

- Source: https://arxiv.org/abs/2609.39819
- Finding/idea reported in historical watch: Agent lifecycle informs backend which KV ranges are live, waiting on tools/subagents, or dead.
- DSH applicability / next falsifiable check: Instrument lifecycle-to-LLM telemetry; test only where DSH controls self-hosted inference/KV backend.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### ReCAP: Persistent Context Graphs for Efficient Memory Compaction in LLM Agents

- Source: https://arxiv.org/abs/2609.40118
- Finding/idea reported in historical watch: Persistent context graph/derived compaction can exploit structure beyond plain rolling summaries.
- DSH applicability / next falsifiable check: Offline replay against existing immutable session log, simple summary and retrieval baselines.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### VeriHarness

- Source: https://arxiv.org/abs/2610.00972
- Finding/idea reported in historical watch: Independent disagreement resolver and challenger pattern for verification.
- DSH applicability / next falsifiable check: Treat outputs as supporting probabilistic evidence, never as a correctness proof or Model Trust authority; separate scorer from agent.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### Agent Error Dataset

- Source: https://arxiv.org/abs/2609.40111
- Finding/idea reported in historical watch: Dataset of agent mistakes/correction patterns suggested for replayable learning.
- DSH applicability / next falsifiable check: Use as externally sourced benchmark candidate; require full-text/methods and leakage-aware held-out split.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### MAADBench

- Source: https://arxiv.org/abs/2609.36556
- Finding/idea reported in historical watch: Multi-agent anomaly/fault-injection benchmark candidate.
- DSH applicability / next falsifiable check: Fault-injection exercises for Agent Teams/worker coordination after supported runtime composition.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### Covert Assistance

- Source: https://arxiv.org/abs/2609.39050
- Finding/idea reported in historical watch: Potential hidden assistance/coordination between nominally constrained agents.
- DSH applicability / next falsifiable check: Review observable actual actions and permissions, not model declarations of role or autonomy.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

## Archive position

Previous archival baseline: [15 September Research Watch](2026-09-15-deepseek-harness-research-watch.md). Next items and consolidated follow-up: [Research index](README.md) and [Assimilation plan](../../docs/research-assimilation-plan.md).

**Do not** infer that a proposed DSH code path, test suite or provider exists today from these historical suggestions. Do not amend IQ-F1 authority, AF-003 status or owner-approved gates based on research.
