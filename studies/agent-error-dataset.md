# Agent Error Dataset — Trace-Grounded Diagnosis and Replay

[Структурированная запись и связи](../catalog/studies/agent-error-dataset.md)

**Primary source:** https://arxiv.org/abs/2609.40111

**Topic:** `ERROR_RECOVERY`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-10-05-research-review-decisions.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-10-05-research-review-decisions.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source assessment

## 2. Agent Error Dataset — trace-grounded RCA and counterfactual replay

**Source:** [Agent Error Dataset](https://arxiv.org/abs/2609.40111), complete 73-page original PDF and appendices.

**Method and reported evidence.** Dataset includes **50,228 error–diagnosis pairs** but only **38,278 distinct source blobs** across **9,961 environment-scoped source tasks**, drawn from 33 environments, 19 harness families and 23 policy models. These counts are **not independent failure counts**; many failures admit multiple diagnoses. The central tested workflow isolates a failed step, cites a trace/source-backed diagnosis, proposes a correction and performs replay against a saved state/checkpoint. In **3,062 matched replay pairs**, first-proposal corrections increased verifier pass rates **18.4% → 51.1%** compared with replaying the original failing action. This measures correction under supplied failure location; it is **not** automatic error detection, general agent recovery or evidence of transfer to DBA production.

**Limits.** Several diagnoses rely on teacher models, and matching a quoted trace span proves occurrence, not causal explanation. Dataset populations, experiments and training subsets are not a single nested, uniformly qualified collection; historical evaluation subsets had incomplete source policy context. Training a Qwen3-8B diagnosis model improved agreement with **internal teacher labels**, not independently adjudicated ground truth. Shared environments/tasks create leakage risks; successful replays and failure-only samples cannot establish general deployment failure rates.

**DSH mapping.** Extend the *evaluation design*, not model training. Preserve provenance, exact failed tool/action, observation, policy/context snapshot, proposed replacement and a re-executable independent oracle. Combine with previously accepted NovaFabric/minimal replay principle and ToolGrad source-based tests where appropriate. A replay is not proof of identical external-world side effects. **Do not** make production SQL, Host or real connector operations replay targets.

**First falsifiable test.** Select **20–30 genuinely observed** non-production failures (only if such evidence is available; do not invent counts), stratified by tool error, planning, lost context and recovery. For each: original action, corrected alternative, matched disposable checkpoint, output artifacts, independent final-state oracle, and separate failure-location adjudication. Compare baseline retry versus one predeclared correction, prevent multiple candidates from being silently cherry-picked, log cost and mismatched replay environments.

**Decision:** `ACCEPT_OFFLINE_RCA_REPLAY_METHODOLOGY`, P1. **Status: analysis accepted; dataset import, training and replay experiment not performed by this review.**

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [sequential-rca](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/01-dba-akuz/sequential-rca/PROJECT.md), [akuz-issue](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/01-dba-akuz/akuz-issue/PROJECT.md), [dsh-runtime](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-runtime/PROJECT.md). Причина: Trace-grounded RCA и counterfactual replay по фактам, не по догадкам. [Cross-project matrix](../portfolio/historical/project-fit.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.
