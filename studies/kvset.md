# KVSET — The KV Cache Working Set

[Структурированная запись и связи](../catalog/studies/kvset.md)

**Primary source:** https://arxiv.org/abs/2609.27746

**Topic:** `KV_CACHE`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_AND_LOCAL_TOOL_TEST_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-28-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-28-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
Complete nine-page arXiv paper and **local Paper2Agent P2A-001-C executable reproduction** (2026-10-31)

### Reported results and limitations
Computes page-granular LRU prefix-cache working-set/capacity curves from token-ID traces. Author study used 10k/24k-request serving traces and GLM-5.2; 95%/99% coverage sizing on that workload is about 1 TiB/5 TiB, not applicable as DSH requirement. Limits: LRU, full-attention component and a known tokenizer/KV bytes-per-token; hidden cloud cache behavior unobservable. Local P2A-001-C direct original-code/wrapper checks and 45/45 original source tests passed on a pinned research revision; **no DSH latency/cost benefit was measured**.

### DSH-specific research disposition
**RETAIN ACCEPTED LOCAL RESEARCH TOOL / DEFER RUNTIME**. No new implementation is needed: use existing `kvset_analyze_token_trace` only with permissible sanitized traces for a backend-specific/offline prefix-stability experiment once a known serving stack or measurements exist.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [dsh-paper2agent](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/06-independent-research/dsh-paper2agent/PROJECT.md). Причина: Квалифицированный научный KV-capacity анализ, не production runtime optimization. [Cross-project matrix](../portfolio/historical/project-fit.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
