# DeepSeek Harness — Research Watch (reconstructed 2026-09-28)

Coverage: **22–28 September 2026**  
Status: **RECONSTRUCTED HISTORICAL INDEX — NOT A VERBATIM NEWSLETTER OR FULL-TEXT SCIENTIFIC REVIEW**  
Sources: prior DSH Research Watch conversation summaries, with the cited public source links supplied/recovered. Claims here are *historical editorial takeaways*, not a newly independently reproduced full-method assessment.

These weekly reports were not stored in `Artemedi/dsh/knowledge/research/` when originally issued. This backfill preserves the previously discussed candidates **without inventing missing newsletter prose**. Each candidate remains research knowledge only; read the complete primary paper (HTML/PDF/legitimate author version) before full scientific evaluation or promotion. If unavailable, mark `FULL_TEXT_UNAVAILABLE`. Current checkpoints come from `AGENTS.md` and `docs/iq-f1-orchestration/STATE.md`, not historical report wording.

## Historical findings and candidate experiments

### Where Does Exactly-Once Live? Model, Harness, and Tool-Contract Effects on Duplicate Side Effects in LLM Agents

- Source: https://arxiv.org/abs/2609.29095
- Finding/idea reported in historical watch: Retries after ambiguous failures can duplicate externally committed effects; tool-side idempotency and stable operation identity matter.
- DSH applicability / next falsifiable check: Audit DSH tool operationId, retry/restart boundaries and externally observable effect ledger. Never assume generic session append is exactly-once side-effect enforcement.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### Cursor: Improved token efficiency for longer agent runs

- Source: https://prod.cursor.com/blog/improved-token-efficiency
- Finding/idea reported in historical watch: Dynamic tool schemas and cache-stable prefix design may reduce token waste.
- DSH applicability / next falsifiable check: Benchmark dynamic tool presentation vs all-tools baseline before altering prompts or auth.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### StateComp: Learning When to Compress History in Long Horizon Agents

- Source: https://arxiv.org/abs/2609.27298
- Finding/idea reported in historical watch: State-conditioned compression timing aims to avoid premature loss of actionable history.
- DSH applicability / next falsifiable check: Test derived history/projection over immutable event log; measure long-task quality as well as tokens.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### Self-replicating prompt injections exist

- Source: https://alignment.openai.com/misalignment-reports/self-replicating-prompt-injections-exist
- Finding/idea reported in historical watch: A prompt-injection payload may be repeated through outbound messages/tools, spreading across agent interactions.
- DSH applicability / next falsifiable check: Test taint/provenance and connector outbound boundaries in synthetic mail/calendar/team fixtures; original report observed no real-world propagation.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

### The KV Cache Working Set: Online Capacity Planning for LLM Inference Systems (KVSET)

- Source: https://arxiv.org/abs/2609.27746
- Finding/idea reported in historical watch: KV cache reuse-distance/capacity planning can use serving traces.
- DSH applicability / next falsifiable check: Telemetry/backend experiment, not agent-loop change; compare with existing provider telemetry.
- Admission: **knowledge only; not a production authorization**. Full-text/method verification required for scientific acceptance.

## Archive position

Previous archival baseline: [15 September Research Watch](2026-09-15-deepseek-harness-research-watch.md). Next items and consolidated follow-up: [Research index](README.md) and [Assimilation plan](../../docs/research-assimilation-plan.md).

**Do not** infer that a proposed DSH code path, test suite or provider exists today from these historical suggestions. Do not amend IQ-F1 authority, AF-003 status or owner-approved gates based on research.
