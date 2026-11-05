# Cursor — Improved Token Efficiency

[Структурированная запись и связи](../catalog/studies/cursor-token-efficiency.md)

**Primary source:** https://cursor.com/blog/improved-token-efficiency

**Topic:** `INFERENCE_EFFICIENCY`. **Previously recorded evidence:** `FULL_ENGINEERING_ARTICLE_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-28-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-28-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
Complete first-party engineering article, not a peer-reviewed paper, 23 Sep 2026

### Reported results and limitations
Cursor reports 7% total token-cost reduction on its traffic; reduced static tool definitions, dynamic MCP tool loading, cache-stable prefixes and sparse file numbering. 46.9% reduction refers to tokens in **sessions calling an MCP tool**, not all traffic; 20% cold-cache miss reduction is another distinct metric. Proprietary A/B data are not independently reproducible.

### DSH-specific research disposition
**NEEDS_EVIDENCE / P2 PERFORMANCE BASELINE**. First measure DSH prompt/tool definition tokens, prompt cache hit/miss, tool selection failures, downstream task success and total cost, including extra dynamic discovery calls. Only then test safe on-demand presentation; tool visibility must never alter tool **authorization**. Avoid speculative framework.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [dsh-runtime](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-runtime/PROJECT.md), [HermesAgent](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/HermesAgent/PROJECT.md). Причина: Издержки tool schemas, MCP discovery и prompt-prefix cache stability. [Cross-project matrix](../portfolio/historical/project-fit.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
