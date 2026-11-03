# Where Does Exactly-Once Live? / LIMBO

**Primary source:** https://arxiv.org/abs/2609.29095

**Topic:** `RELIABILITY`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-28-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-28-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
Complete 23-page arXiv PDF, including setup, theorems, Tables 3–6 and limitations

### Reported results and limitations
25,930 **synthetic fault-injection** episodes with nine models/three harnesses. Client-side read-back cannot solve in-flight/late commit or redelivery with a key-less non-idempotent write. Keys-everywhere cut duplicate write rate 28% → 4% in studied conditions; a wrapper can help only when the actual service contract supports idempotency.

### DSH-specific research disposition
**ACCEPT REQUIREMENT / P1 COVERAGE AUDIT**. Inventory per-tool effect identity, logical operation correlation, key support and ambiguous-outcome retry. Confirm in actual pinned code and tests; propose a disposable service-level fault fixture before code changes. Durable session evidence is NOT exactly-once external execution. No generic new transaction framework.

## Further cross-project evaluation

- Candidate applicability beyond DSH: `NOT_YET_ASSESSED`. Scan all projects in project-registry only when a concrete research comparison is requested.
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
