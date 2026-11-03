# Red-Teaming Auto Mode

**Primary source:** https://arxiv.org/abs/2609.19587

**Topic:** `SECURITY`. **Previously recorded evidence:** `PUBLIC_METHODS_REVIEW_RECORDED_APPENDICES_NOT_INSPECTED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-21-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-21-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
[arXiv:2609.19587](https://arxiv.org/abs/2609.19587) and [authors' detailed public article](https://alignment.anthropic.com/2026/red-teaming-auto-mode/) (methods, results, limitations; PDF appendices not independently inspected)

### Reported results and limitations
Tested blocking monitors against deliberate adversarial agent strategies; reported high bypass rates, with failures across forged transcript, compaction, multi-agent boundaries and unreviewed working-directory changes. September system snapshot, security observer assumed trustworthy, sandbox itself not evaluated.

### DSH-specific research disposition
**KEEP / high-priority isolated security regression inventory**, not a DSH agentic-monitor replacement; ensure action-authority validation, role framing, coverage across delegation/compaction, and monitor performance.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [dsh-runtime](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-runtime/PROJECT.md), [agent-config](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/agent-config/PROJECT.md), [HermesAgent](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/HermesAgent/PROJECT.md). Причина: Границы approval, tool effects, компакции и делегирования. [Cross-project matrix](../reports/2026-11-03-project-mapping-historical-16.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
