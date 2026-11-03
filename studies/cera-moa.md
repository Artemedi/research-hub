# CERA-MoA — Adaptive Multi-Agent Routing

**Primary source:** https://arxiv.org/abs/2609.18779

**Topic:** `MODEL_ROUTING`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-21-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-21-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
[arXiv:2609.18779 full HTML](https://arxiv.org/abs/2609.18779), method/experiments/appendix reviewed

### Reported results and limitations
Co-trains LoRA specialist policies and familiarity router using mid-layer model hidden states and RL; on Qwen3-4B reported OOD 72.8 avg vs best listed other 71.5. Benefits not established for opaque cloud API providers; needs hidden-state access, training infrastructure and quality-eval loop.

### DSH-specific research disposition
**SKIP DSH runtime implementation / RETAIN as future self-hosted training research**. Do not confuse with 9Router availability or DSH Model Trust tier; experiment only if owning trainable backend and stable held-out benchmark.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): `NO_CURRENT_TARGET`. Причина: Скрытые состояния и LoRA-обучение требуют controlled trainable backend; обычный API-router не подходит. [Cross-project matrix](../reports/2026-11-03-project-mapping-historical-16.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
