# REALM — Retrieval-Driven Memory Reconsolidation

**Primary source:** https://arxiv.org/abs/2609.16053

**Topic:** `MEMORY`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-21-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-21-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
[arXiv:2609.16053 full HTML](https://arxiv.org/abs/2609.16053), method, results, ablations and appendices checked

### Reported results and limitations
LoCoMo 75.97%, LongMemEval 65.11%; isolated retrieval-triggered reconsolidation effect +2.01 and +2.13 points vs own no-recon variant. LoCoMo/LongMemEval judge evaluated using GPT-4o-mini; benchmark QA not equivalent to coding/DBA task success. Extra graph mutation/update work adds cost/risks.

### DSH-specific research disposition
**ACCEPT offline memory-quality hypothesis; DEFER structural memory rewrite.** Test changes to *derived* retrieval topology against immutable Memory events and fixed BM25/retrieval baselines, with feedback trust and rollback.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [dsh-team-context](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-team-context/PROJECT.md), [Wiki_PG](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/01-dba-akuz/Wiki_PG/PROJECT.md). Причина: Переукладка связей в memory/retrieval при неизменном источнике. [Cross-project matrix](../reports/2026-11-03-project-mapping-historical-16.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
