# StateComp — State-Conditioned Context Compression

[Структурированная запись и связи](../catalog/studies/statecomp.md)

**Primary source:** https://arxiv.org/abs/2609.27298

**Topic:** `CONTEXT_MANAGEMENT`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-28-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-28-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
Complete 33-page arXiv PDF (method, 260-task WorkBuddyBench study, Appendices C–F)

### Reported results and limitations
State-conditioned KEEP/READY labels; candidate spans compressed only after grouping/threshold gates. In the authors' benchmark total tokens fell 698.17M → 333.24M (−52.27%) with mean reward 0.6987 → 0.7026, not a demonstrated general quality gain. Hidden-state-trained router and dependency labels; the 12.67× headline applies to **feature extraction on seven successful paired states**, not end-to-end task speed. Reported selective 72.22% precision occurs at 0.111% recall, not a high-coverage safety guarantee.

### DSH-specific research disposition
**ACCEPT EVALUATION HYPOTHESIS / DEFER TRAINED ROUTER**. Test conservative derived-history compaction under immutable event-source plus long-horizon replay and missing-fact regression checks; compare no compaction, fixed threshold/periodic and source-derived summary. Keep authority/ tool results protected; no learned deployment without coverage and quality evidence.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [dsh-runtime](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-runtime/PROJECT.md), [dsh-team-context](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-team-context/PROJECT.md). Причина: Консервативная compaction derived context с сохранением immutable events. [Cross-project matrix](../portfolio/historical/project-fit.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
