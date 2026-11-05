# KVTether — KV Cache Lifecycle Management in ReAct Agents

**Primary source:** https://arxiv.org/abs/2609.39819

**Topic:** `KV_CACHE`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-10-05-research-review-decisions.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-10-05-research-review-decisions.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source assessment

## 6. KVTether — physical KV-cache retention from harness lifecycle

**Source:** [KVTether: Capture the Lifecycle — KV Cache Management in ReAct Agents](https://arxiv.org/abs/2609.39819), complete 14-page original PDF.

**Method and reported evidence.** A message/context-lifecycle adapter emits `append`, `replace`, `remove`, `fork`, `spawn`, `one_off`, `pin`, `unpin` events. A serving-side manager maps these into live/idle/discarded KV ranges and controls eviction/reclamation. The authors evaluated against LMCache and MORI; mean **end-to-end latency** fell **16.5%** and **12.4%**, respectively, with reported *maximum* reductions of **26.3%** and **17.4%** on studied workloads. Reported estimated task-pricing reductions are **40.0%** and **33.2%** on average using an assumed tariff, **not** observed DSH provider invoices. Adapter overhead includes per-call token/KV mapping; measured performance comes from a specific serving setup and workloads, not general API-hosted models.

**DSH mapping.** DSH controls context/agent orchestration but **does not control physical remote-provider KV cache residency**. This research belongs to a self-hosted inference backend or provider willing to expose and enforce KV storage hints. Existing KVSET is a complementary *capacity-planning* research tool, not a substitute for lifecycle-eviction control. Do not put KVTether hooks or a new KV cache manager into DSH Runtime absent a concrete backend owner and test case.

**First falsifiable test (only after prerequisites).** Controlled local inference with known tokenizer, attention layout, physical KV cache configuration and representative permitted traces; compare static LRU/KVSET-informed provisioning to lifecycle hints, including prefill, true cache hits, overhead, end-to-end latency and costs. Treat KVSET's prior local Paper2Agent reproduction as scientific-tool qualification, **not** demonstrated DSH savings.

**Decision:** `DEFER_BACKEND_SPECIFIC`. **Status: retain as reference only.**

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): `NO_CURRENT_TARGET`. Причина: Физическое удержание KV-cache требует полного контроля serving backend, который не подтверждён профилями. [Cross-project matrix](../portfolio/historical/project-fit.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
