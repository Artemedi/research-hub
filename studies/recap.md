# ReCAP — Persistent Context Graphs for Memory Compaction

**Primary source:** https://arxiv.org/abs/2609.40118

**Topic:** `MEMORY`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-10-05-research-review-decisions.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-10-05-research-review-decisions.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source assessment

## 5. ReCAP — recoverable context selection versus summary-only compaction

**Source:** [ReCAP: Persistent Context Graphs for Efficient Memory Compaction in LLM Agents](https://arxiv.org/abs/2609.40118), complete 19-page original PDF.

**Method and reported evidence.** ReCAP records attention-derived importance and dependency links in a persistent context graph and chooses relevant blocks at each new turn. Previously omitted material can return because the full source archive is retained; this contrasts with one-way deletion of old context. Authors evaluated **106 SWE-Together tasks** and **100 Lost-in-Conversation code instances**, on two locally served open-weight models, with retrieval and summarization baselines. Their reported ≈**95% reduction in compaction/cold-restoration time** refers to specific prepared-graph/cold-restoration scenarios, **not** overall interactive-agent time or a claim that arbitrary DSH runs accelerate by 95%. Supporting attention/proxy extraction, graph update/storage and query selection also cost time. A Qwen3-0.6B attention proxy was studied, but applicability to cloud models and DSH engineering tasks remains unverified.

**DSH mapping.** Preserve immutable source events, current user instructions, last edits and protected authority/control data; select only a **derived working context**. Do **not** add a third Memory subsystem or assume cloud LLM attention weights are available. Compare as part of the **same** previously accepted memory-quality evaluation stream as REALM and StateComp, not another implementation workstream.

**First falsifiable test.** Offline replay on held-out long task traces: no compression, bounded/static summary, simple lexical/BM25 source retrieval, and only then provenance-preserving graph selection (proxy explicitly marked unvalidated). Measure task success, recovered facts, loss of safety constraints, prefix-cache retention, end-to-end latency and complete token/computation cost. Graph gain must beat simpler baselines at comparable budgets before implementation is proposed.

**Decision:** `RETAIN_RESEARCH_HYPOTHESIS_IMPLEMENTATION_DEFERRED`, P2. **Status: research reference; no runtime implementation.**

## Further cross-project evaluation

- Candidate applicability beyond DSH: `NOT_YET_ASSESSED`. Scan all projects in project-registry only when a concrete research comparison is requested.
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
