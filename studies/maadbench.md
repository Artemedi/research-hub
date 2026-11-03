# MAADBench — Multi-Agent Anomaly and Fault Benchmarks

**Primary source:** https://arxiv.org/abs/2609.36556

**Topic:** `EVALUATION`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-10-05-research-review-decisions.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-10-05-research-review-decisions.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source assessment

## 4. MAADBench — refreshing fault-labeled multi-agent benchmarks

**Source:** [MAADBench](https://arxiv.org/abs/2609.36556), complete 33-page original PDF.

**Method and reported evidence.** Bottom-up composed atomic tasks with known oracle outputs yield deterministic failure labels across action, puzzle and room dependency levels. The authors generated **5,200 traces** across five model backbones and evaluated **25 anomaly-detection methods**. The anomaly-detection evaluation subset contains **17,180 labeled actions**, with **19.68% anomalous actions**. Results vary by backbone, label availability and error propagation. More supervised detectors perform better in the authors' setup; these are not performance predictions for DSH. Synthetic, deliberately structured puzzles do not represent the full diversity of real agent communication, memory and task coordination.

**DSH mapping.** Borrow the **generative test-construction principle**, not a turnkey monitor, another framework or a classifier trained on the published mixture. Add deterministic oracle-bearing failure and propagation fixtures to existing, supported test infrastructure **after** the relevant agent team/worker interfaces have a stable, permitted test seam. Include first-fault attribution, downstream propagation, omitted events and observer coverage, as distinct metrics. MAADBench's detection AUROC is not a quality gate for DSH without a matching labeled DSH workload.

**First falsifiable test.** Build a small predeclared set of sandbox-only, dependency-connected multi-agent scenarios using current public interfaces (if eligible), inject a controlled wrong step, and compare exact first-fault labels and downstream effects against independent instrumentation. No new production anomaly service or Host intervention.

**Decision:** `ACCEPT_TEST_GENERATION_PRINCIPLE`, P2. **Status: hypothesis and test design only; experiment not run.**

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [hermes-akuz-agents](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/hermes-akuz-agents/PROJECT.md), [agent-skills](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/agent-skills/PROJECT.md), [dsh-runtime](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-runtime/PROJECT.md). Причина: Multi-agent trace fixtures с известным first-fault и downstream propagation. [Cross-project matrix](../reports/2026-11-03-project-mapping-historical-16.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
