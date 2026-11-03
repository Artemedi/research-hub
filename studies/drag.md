# DRAG — Dynamic Retriever and Generator Selection

**Primary source:** https://arxiv.org/abs/2609.17709

**Topic:** `RETRIEVAL`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-21-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-21-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
[arXiv:2609.17709 full HTML](https://arxiv.org/abs/2609.17709), methods/results reviewed

### Reported results and limitations
Tests joint retriever rank (BM25 / E5 / reranking / decomposition) and generator effort on four QA datasets. Training-free DRAG_QPP uses Avg-IDF and context perplexity; SFT variant needs supervised data. Retrieval quality can matter more than increased generation effort; latency comparisons use a specific vLLM/A100 stack and do not include all preprocessing.

### DSH-specific research disposition
**ACCEPT a narrow offline RAG cost/quality ablation** over an existing Team Context / Memory read-only consumer, **not** a new agent/router component. Evaluate retrieval tiers and admitted model candidates separately; DSH Model Trust always first.

## Further cross-project evaluation

- Candidate applicability beyond DSH: `NOT_YET_ASSESSED`. Scan all projects in project-registry only when a concrete research comparison is requested.
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
