# DSH Research Knowledge — Chronological Index

Updated: 2026-10-27  
Status: **ARCHIVAL INDEX / NON-NORMATIVE KNOWLEDGE**  
Scope: papers, technical reports and engineering observations potentially relevant to DSH; source publication dates and digest coverage are distinct.

**Authority warning:** This directory is not a decision register, acceptance gate or implementation queue. The current DSH checkpoint is `docs/iq-f1-orchestration/STATE.md`; approvals and decisions live in `EVENTS.jsonl`. Start at [AGENTS.md](../../AGENTS.md). No research watch may override Class A/B procedures, IQ-F1 HOLD, or AF-003 constraints.

## Archive by digest date range

| Coverage | Archive file | Source status | Primary subjects |
| --- | --- | --- | --- |
| 03–09 Sep 2026 | *No full dated digest archived*; see early-item note below | Partial metadata only | Random Attention / KV inference |
| Initial September watch (dated 15 Sep; exact coverage interval not recorded) | [15 Sep watch](2026-09-15-deepseek-harness-research-watch.md); [operator-accepted research dispositions](2026-09-15-research-review-decisions.md) | Original report + non-normative decision note | BenchShield, SWRouter, ToolGrad, REVA, NovaFabric, CVE-2026-82533 |
| 15–21 Sep 2026 | [21 Sep reconstructed watch](2026-09-21-deepseek-harness-research-watch-reconstructed.md); [accepted review](2026-09-21-research-review-proposal.md); [P2A-001 isolated pilot](pilots/P2A-001-paper2agent-research-pipeline.md) | **Reconstructed index + operator-accepted research dispositions + design-only pilot** | Auto Mode, REALM, DRAG, Paper2Agent, CERA-MoA |
| 22–28 Sep 2026 | [28 Sep reconstructed watch](2026-09-28-deepseek-harness-research-watch-reconstructed.md); [operator-accepted review](2026-09-28-research-review-proposal.md) | **Reconstructed index + operator-accepted research dispositions (non-normative)** | Exactly-once, Cursor dynamic tools, StateComp, self-replicating injection, KVSET |
| 29 Sep–05 Oct 2026 | [05 Oct reconstructed watch](2026-10-05-deepseek-harness-research-watch-reconstructed.md); [operator-accepted review](2026-10-05-research-review-decisions.md) | **Reconstructed index + operator-accepted source-reviewed dispositions (non-normative)** | KVTether, ReCAP, VeriHarness, Agent Error Dataset, MAADBench, Covert Assistance |
| 06–12 Oct 2026 | [12 Oct reconstructed watch](2026-10-12-deepseek-harness-research-watch-reconstructed.md) | **Reconstructed index** | HarnessSecurity-Bench, SquidAgent, ExperienceIndex, DAEDALUS, package attack, POLAR, REMORY |
| 13–19 Oct 2026 | [19 Oct reconstructed watch](2026-10-19-deepseek-harness-research-watch-reconstructed.md) | **Reconstructed index** | HTN-Orchestrate, agent-risk, JevAgentHarness, MemComposer, LAGO, Agentic Self-Awareness; additional MemScope/Matoi |
| 20–26 Oct 2026 | [26 Oct edited watch](2026-10-26-deepseek-harness-research-watch.md) + [full original RU source](sources/2026-10-26-deepseek-harness-research-watch-original-ru.md) | Full operator-supplied report preserved as extracted text; English edition separately maintained | METR/OpenAI monitoring, GeoAgent, tool selection, refusal/tool actions, Agent Mosaic, cue loss, continual memory, BIRD-RL |
| 07 Oct 2026 (cross-cutting special) | [Mathematical methods](2026-10-07-math-models-assessment.md) | Original DSH evaluation | Formal specification, deterministic oracle, bounds and sample sizing |

**Completeness:** the five reconstructed watches recover **31 named historical items** (5 + 5 + 6 + 7 + 8) from prior digest summaries; the 26 Oct edition covers **eight items** (seven main papers/topics plus BIRD-RL) and the METR/OpenAI engineering sources. The historical summaries are not full verbatim newsletter texts. Do not treat completeness of title coverage as proof every full source was evaluated or every previous minor item was recovered.

**Older candidate missing from Git archive:** [Random Attention: Rethinking KV Cache Eviction for Efficient Reasoning](https://arxiv.org/abs/2609.03430), discussed in early September; preserve as inference-backend research metadata, not as a DSH agent-loop requirement.

## Cross-cycle synthesis: what we previously overlooked

These are **research clusters**, not new runtime epics:

| Cluster | Previously scattered candidate work | Bounded testable question | Ownership / earliest rational disposition |
| --- | --- | --- | --- |
| Security/monitor integrity | CVE-2026-82533; Auto Mode; self-replicating injections; Covert Assistance; HarnessSecurity-Bench; POLAR; METR; refusal transfer; Agent Mosaic; package rule attacks | Does the control plane prevent unauthorized actions and account for each reachable execution path, including compaction and delegation? | Current authority invariants and **offline security regression design**; owner gate for any new preventive authority |
| Durable execution / reproducibility | Exactly-once, NovaFabric, agent-risk, GeoAgent, BIRD-RL, formal/mathematical oracle note | Can a real operation be correlated, safely retried/replayed and verified by final state? | Scoped QA, evaluation runners and explicit effect contracts, not speculative shared framework |
| Memory and quality | REALM, StateComp, ReCAP, REMORY, REVA, ExperienceIndex, DAEDALUS, MemComposer, MCCL | Does recall improve held-out **task outcomes, retention, adaptation and transfer** beyond simple retrieval/summaries? | Stable-memory evaluation methodology; no new Memory subsystem by default |
| Routing/delegation | DRAG, SWRouter, CERA-MoA, SquidAgent, HTN-Orchestrate, JevAgentHarness | Is delegation better under **Model Trust eligible-set** and AF-003 runtime enforcement than strong-model baseline? | Offline/shadow routing tests after policy/evidence quality; never expand eligibility |
| Tool economy | ToolGrad, Paper2Agent, Cursor dynamic tools, learned tool selection, GeoAgent | Does selection/validated execution lower tokens or errors **without masking required tools**? | Disposable tests: all-tools vs BM25 vs selector; workflow-specific artifact contract |
| Inference/KV economics | Random Attention, KVSET, KVTether | Can backend KV hints reduce cost without undermining execution or quality? | Inference provider/serving stack, not DSH Harness fork |
| Document fidelity | Silent Cue Loss | Does DSH's actual converter erase style-implied requirements? | First inventory a real ingestion seam, then deterministic fixture |

## Research-to-implementation discipline

1. **Candidate registration:** link exact paper/report, date, version, accessible complete source and limitations; distinguish author claim from our hypothesis.
2. **Scientific review:** read complete article (HTML/PDF or legal author manuscript), including methods, results and limitations. Abstracts/press releases are screening only. Mark `FULL_TEXT_UNAVAILABLE` if no legitimate complete source exists.
3. **Applicability:** identify existing DSH boundary, owner, threat/quality premise and cheaper baseline; record any missing seam as `NEEDS_EVIDENCE`.
4. **Offline or shadow experiment:** use immutable replay, clean fixtures, deterministic outcome oracle, controlled model/tools/cost; do not modify Host or frozen source.
5. **Governance:** accepted knowledge ≠ accepted architecture ≠ authorization. Only separately approved scope with the requisite class and gates can enter production.

See [Research Assimilation Plan](../../docs/research-assimilation-plan.md).

## Maintenance

New periodic reviews use `YYYY-MM-DD-deepseek-harness-research-watch.md`, record an explicit coverage interval and link only real primary sources. Reconstructed archives include `-reconstructed` and MUST NOT overwrite original reports. Keep original historical documents immutable where possible; append corrections via a separate note rather than silently rewriting past claims. Period membership reflects **digest coverage**, not necessarily submission date for an updated paper.
