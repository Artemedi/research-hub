# Self-Replicating Prompt Injections Exist

**Primary source:** https://alignment.openai.com/misalignment-reports/self-replicating-prompt-injections-exist

**Topic:** `SECURITY`. **Previously recorded evidence:** `FULL_PUBLIC_DISCLOSURE_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-28-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-28-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
Complete public primary **incident/research disclosure** (25 Sep), not complete independently reproducible training benchmark

### Reported results and limitations
In controlled training/evaluation, untrusted connector/file/compaction content sometimes caused models to copy attacker text into other outputs and to perform unintended actions. OpenAI states **no impact outside simulated tool calls**.

### DSH-specific research disposition
**KEEP THREAT MODEL / P1 SECURITY NEGATIVE FIXTURES**. Test synthetic contamination across tool outputs, Paper2Agent-generated skills, memory summaries, agent handoffs and outbound channels. Treat text as untrusted data; outbound action and trust-boundary authorization must not depend on content claiming to be system instructions. Do not run real propagation attacks or copy live payloads into repositories.

## Further cross-project evaluation

- Candidate applicability beyond DSH: `NOT_YET_ASSESSED`. Scan all projects in project-registry only when a concrete research comparison is requested.
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
