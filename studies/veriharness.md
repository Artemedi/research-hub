# VeriHarness — Evidence-Grounded Agentic Verification

**Primary source:** https://arxiv.org/abs/2610.00972

**Topic:** `VERIFICATION`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-10-05-research-review-decisions.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-10-05-research-review-decisions.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source assessment

## 1. VeriHarness — verification against evidence, not voting

**Source:** [VeriHarness: Scaling Agentic Verification for Long-Horizon Tasks](https://arxiv.org/abs/2610.00972), complete 28-page original PDF.

**Method and reported evidence.** A pool of ten outputs per task is examined by two separate verification contexts: a *disagreement resolver* tests conflicting claims, and a *consensus challenger* probes claims on which all outputs agree. Both work against the actual workspace, artifacts and tools; a fresh adjudicator combines evidence, selects a base and proposes an evidence-backed revision. On APEX-Agents consensus claims, **34% of unanimous values were judged incorrect**, while **74% of disputed claims had at least one correct candidate**. Across five workspace benchmarks, and equal ten-rollout generation pools, selection versus a single rollout improved mean scores by **+4.4 points** for Gemini 3.5 Flash and **+4.1** for Claude Opus 4.8; selection plus a revision pass improved **+6.2** and **+6.4** points, respectively. Results are benchmark averages, not a universal percentage increase in task success.

**Limits.** Ten rollouts and multi-turn investigation add generation, verification latency and token cost. Verification uses the **same model** as the generator; claimed improvement does not demonstrate independence from model-family error correlation. Several graders are rubrics/judges rather than deterministic oracles. Even a verifier agreeing with a recomputation can miss a later downstream error: the paper reports a substantial consensus-challenger blind spot. Verified claims constitute supporting evidence, not mathematically established correctness or permission to act.

**DSH mapping.** DSH already has `@artemedi/dsh-verifier`, **qualified offline but not profile-admitted** at the recorded checkpoint. Do **not** introduce another verifier engine in DSH Runtime. Reuse the paper's *methodology* to test existing/offline verification: contradictory model findings, consensus-wrong fixtures, recomputation against reference files and last-step error checks. Challenger and resolver should not be conflated with an independent/non-authoring governance council, and must not authorize Model Trust or IQ-F1 actions.

**First falsifiable test.** Create a small fixed corpus of distinct, non-production tasks with preserved artifacts and independent oracle/checklist. Compare current verifier / single-result review against claim-level resolver + challenger using the **same candidate pool**, recording: correct/incorrect claims, missed downstream defects, false accusations, latency and full tokens/cost including ten-rollout generation. No implementation transfer until its current test seams and provider availability have been verified.

**Decision:** `ACCEPT_VERIFICATION_METHODOLOGY`, P1. **Status: analysis accepted; experiment not run by this review.**

## Further cross-project evaluation

- Candidate applicability beyond DSH: `NOT_YET_ASSESSED`. Scan all projects in project-registry only when a concrete research comparison is requested.
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
