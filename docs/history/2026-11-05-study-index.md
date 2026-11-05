# Individually indexed studies — previously reviewed in DSH

- [Telegram follow-up 05.11: результаты и сохранённые gates](../../portfolio/2026-11-05/review.md).
- **[BK-062 — REA: новый follow-up](../../reviews/reverse-engineer-anything/2026-11-05-pe-layout.md)** — проверен экспериментально; предел проверки указан в отчёте.
- **[BK-065 — Vercel Agent Desktop: новый follow-up](../../reviews/vercel-agent-desktop/2026-11-05-wayland.md)** — проверен экспериментально; предел проверки указан в отчёте.
- **[BK-063 — Hyra 2.0: новый follow-up](../../reviews/hyra-2/2026-11-05.md)** — разобран; предел проверки указан в отчёте.


**BK-062 — REA:** [карточка](../../studies/reverse-engineer-anything.md), [промежуточный source gate](../../reviews/reverse-engineer-anything/2026-11-05-source-boundaries.md); исторический промежуточный gate; актуальный bounded follow-up указан выше.

**BK-065 — Vercel Agent Desktop:** [карточка](../../studies/vercel-agent-desktop.md), [промежуточный source gate](../../reviews/vercel-agent-desktop/2026-11-05-source-boundaries.md); полный review и runtime gate не завершены.


**Telegram BK-060 — DSH Superagent Prototype:** [карточка](../../studies/dsh-superagent-prototype.md), [source review и 15 ограниченных core checks](../../reviews/dsh-superagent-prototype/2026-11-05.md); полный security/runtime NOT_RUN, PROTOTYPE_NOT_PRODUCTION.


## New research intake — 2026-11-05

- [Sequential diagnosis with language models / MAI-DxO](../../studies/sequential-diagnosis-language-models.md) — [первоначальный полнотекстовый обзор](../../reviews/sequential-diagnosis-language-models/2026-11-05-project-fit.md) → [144 Wello A/B и внедрение в TrinMedicalBot 05.11.2026](../../reviews/sequential-diagnosis-language-models/2026-11-05-challenger.md). TrinMedicalBot: `PRODUCTION_DEPLOYED / CLINICAL_REVIEW_PENDING`; sequential-rca: `FIT_CANDIDATE / NEEDS_EVIDENCE`; оригинальный SDBench не воспроизводился.

**Telegram BK-053 — Yahont CE:** [карточка](../../studies/yahont-ce.md), [source review и synthetic ID helper test](../../reviews/yahont-ce/2026-11-04.md); retrieval не запускался.

**Telegram BK-050 — Chartli:** [карточка](../../studies/chartli.md), [source review и synthetic input tests](../../reviews/chartli/2026-11-04.md); CLI не запускался.

**Telegram BK-048 — Understand Anything:** [карточка](../../studies/understand-anything.md), [source review и synthetic SQL tests](../../reviews/understand-anything/2026-11-04.md); SQL parser имеет ограничения, реальный граф не запускался.

**Telegram BK-047 — agent automations:** [карточка](../../studies/anthropic-agent-automations.md), [source review](../../reviews/anthropic-agent-automations/2026-11-04.md); managed workflow не запускался.

**Telegram BK-043 — Unsloth decision model:** [карточка](../../studies/unsloth-decision-model.md), [source review](../../reviews/unsloth-decision-model/2026-11-04.md); обучение не запускалось.

**Telegram BK-037 — youtube-skills:** [карточка](../../studies/youtube-skills.md), [source review](../../reviews/youtube-skills/2026-11-04.md); внешний сервис не проверялся.

**Telegram BK-034 — autoresearch:** [карточка репозитория](../../studies/karpathy-autoresearch.md), [source review](../../reviews/karpathy-autoresearch/2026-11-04.md); видео недоступно, обучение не запускалось.

**Telegram BK-029 — 0-CODE:** [карточка](../../studies/zero-code.md), [source review и synthetic guard tests](../../reviews/zero-code/2026-11-04.md); полноценный цикл не запускался.

**Telegram BK-028 — Hyperresearch:** [карточка](../../studies/hyperresearch.md), [source review и synthetic citation fixture](../../reviews/hyperresearch/2026-11-04.md); полноценный pipeline не запускался.

**Telegram BK-026 — Julia 1:** [карточка](../../studies/julia-1.md), [source review и synthetic probability fixture](../../reviews/julia-1/2026-11-04.md); inference не запускался.

**Telegram BK-025 — Unreal Agent video:** [карточка](../../studies/unreal-agent-bk025.md), [provenance и отсрочка](../../reviews/unreal-agent/2026-11-04.md); `FULL_TEXT_UNAVAILABLE`, метод не оценён.

**Telegram BK-024 — Local Knowledge Graph:** [карточка](../../studies/local-knowledge-graph.md), [обзор и synthetic graph tests](../../reviews/local-knowledge-graph/2026-11-04.md); модель и реальный корпус не запускались.

**Telegram BK-022 — Microsoft Skill Recorder:** [карточка](../../studies/microsoft-skill-recorder.md), [обзор и узкий synthetic privacy test](../../reviews/microsoft-skill-recorder/2026-11-04.md); Copilot и реальная запись не запускались.

**Telegram BK-019 — Warp Skill Doctor:** [карточка](../../studies/warp-skill-doctor.md), [обзор и изолированный тест атрибуции](../../reviews/warp-skill-doctor/2026-11-04.md); качество рекомендаций не проверялось.

**Telegram BK-016 — Claude Swarm:** [карточка](../../studies/claude-swarm.md), [обзор исходных контрактов и project fit](../../reviews/claude-swarm/2026-11-04.md); найдено неподключение enforcement в штатной инициализации, динамический запуск не проводился.

**Telegram BK-011 — SIMURG:** [карточка](../../studies/simurg.md), [обзор и изолированные проверки](../../reviews/simurg/2026-11-04.md): найдены ошибки AUROC и ограничения калибровки; польза проектам не измерена.

**Telegram BK-006 — Open Steps:** [инженерная карточка](../../studies/open-steps.md), [обзор и ограниченная проверка хуков](../../reviews/open-steps/2026-11-04.md). Найден пропуск изменения untracked-файла; качество ответов не измерено.

**Telegram BK-014 — alphaXiv OpenResearch:** [source-reviewed engineering card](../../studies/alphaxiv-openresearch.md), [Git-snapshot/full-text/security and project-fit report](../../reviews/alphaxiv-openresearch/2026-11-04.md). Full-text metadata trap confirmed in original Rust source; only dsh-paper2agent profile matched; LAB_NOT_RUN and no adoption approval.

**Telegram BK-002 — Tencent TeamAI CLI:** [инженерная карточка](../../studies/tencent-teamai-cli.md) и [полная сверка upstream↔fork и применимости к трём проектам](../../reviews/tencent-teamai-cli/2026-11-04.md). Source review, 6 merge conflicts; никакого исполнения TeamAI/лаборатории.

**Telegram BK-041 / BK-059 — независимые инженерные проверки вне DSH:** [Inspektor Gadget v0.57.0](../../studies/inspektor-gadget.md) — [permission gate на Bazzite, eBPF tracing BLOCKED](../../reviews/inspektor-gadget/2026-11-04.md); [IPFire fireperf 0.3.0](../../studies/ipfire-fireperf.md) — [изолированный реальный loopback lab, 12×20 TCP](../../reviews/ipfire-fireperf/2026-11-04.md). Первое остаётся `AWAITING_REAL_TRACE`, второе `ORIGINAL_BINARY_LOOPBACK_VERIFIED`; ни одно не получает production approval.

**Инженерные инструменты с лабораторной MCP-проверкой:** [Google MCP Toolbox / PostgreSQL](../../studies/mcp-toolbox-postgres.md) — [проверенный live SQL и снимки Wiki_PG](../../reviews/mcp-toolbox-postgres/2026-11-04.md), `LIMITED_FIXTURE_PASS / NO_PRODUCTION_APPROVAL`.

**Новое исследование с лабораторным тестом selection mechanics (не воспроизведение LLM-экспериментов):** [RRSI](../../studies/rrsi.md) и [Harness²](../../studies/harness2.md) — [протокол](../../reviews/rrsi-harness2/2026-11-04.md).

**Новые инженерные проверки (отдельно от научных full-text reviews):** [pgbot — PostgreSQL diagnostic lab, v0.9.0](../../studies/pgbot.md) — `LAB_VERIFIED / NO_PRODUCTION_APPROVAL`, [протокол](../../reviews/pgbot/2026-11-04.md).

This index promotes **16 historically source-reviewed items** from the original DSH
research decisions into separate traceable records. Their original reviews and
full methodological qualifications are preserved via pinned SHA and archive links.
This is a document migration and extraction, **not a new independent replication**.

[**Historical project-fit matrix (16 papers)**](../../portfolio/historical/project-fit.md) — linked to project profiles, proposed offline tests, and explicit NO_CURRENT_TARGET cases. This is a profile-based retrospective, not new scientific review.

| Study | Area | Historical evidence status |
| --- | --- | --- |
| [Red-Teaming Auto Mode](../../studies/red-teaming-auto-mode.md) | `SECURITY` | `HISTORICAL_METHODS_ONLY; PDF_APPENDICES_REVIEWED_2026-11-03` |
| [REALM — Retrieval-Driven Memory Reconsolidation](../../studies/realm.md) | `MEMORY` | `FULL_TEXT_REVIEW_RECORDED` |
| [DRAG — Dynamic Retriever and Generator Selection](../../studies/drag.md) | `RETRIEVAL` | `FULL_TEXT_REVIEW_RECORDED` |
| [Paper2Agent — Research Papers as Reliable AI Agents](../../studies/paper2agent.md) | `RESEARCH_WORKFLOW` | `FULL_TEXT_REVIEW_RECORDED` |
| [CERA-MoA — Adaptive Multi-Agent Routing](../../studies/cera-moa.md) | `MODEL_ROUTING` | `FULL_TEXT_REVIEW_RECORDED` |
| [Where Does Exactly-Once Live? / LIMBO](../../studies/exactly-once-limbo.md) | `RELIABILITY` | `FULL_TEXT_REVIEW_RECORDED` |
| [Cursor — Improved Token Efficiency](../../studies/cursor-token-efficiency.md) | `INFERENCE_EFFICIENCY` | `FULL_ENGINEERING_ARTICLE_REVIEW_RECORDED` |
| [StateComp — State-Conditioned Context Compression](../../studies/statecomp.md) | `CONTEXT_MANAGEMENT` | `FULL_TEXT_REVIEW_RECORDED` |
| [Self-Replicating Prompt Injections Exist](../../studies/self-replicating-prompt-injections.md) | `SECURITY` | `FULL_PUBLIC_DISCLOSURE_REVIEW_RECORDED` |
| [KVSET — The KV Cache Working Set](../../studies/kvset.md) | `KV_CACHE` | `FULL_TEXT_REVIEW_AND_LOCAL_TOOL_TEST_RECORDED` |
| [VeriHarness — Evidence-Grounded Agentic Verification](../../studies/veriharness.md) | `VERIFICATION` | `FULL_TEXT_REVIEW_RECORDED` |
| [Agent Error Dataset — Trace-Grounded Diagnosis and Replay](../../studies/agent-error-dataset.md) | `ERROR_RECOVERY` | `FULL_TEXT_REVIEW_RECORDED` |
| [Covert Assistance — Helpful LLM Agents Evade Oversight](../../studies/covert-assistance.md) | `SECURITY` | `FULL_TEXT_REVIEW_RECORDED` |
| [MAADBench — Multi-Agent Anomaly and Fault Benchmarks](../../studies/maadbench.md) | `EVALUATION` | `FULL_TEXT_REVIEW_RECORDED` |
| [ReCAP — Persistent Context Graphs for Memory Compaction](../../studies/recap.md) | `MEMORY` | `FULL_TEXT_REVIEW_RECORDED` |
| [KVTether — KV Cache Lifecycle Management in ReAct Agents](../../studies/kvtether.md) | `KV_CACHE` | `FULL_TEXT_REVIEW_RECORDED` |

## New full-text checks: 6–12 October watch (reviewed 2026-11-03)

These **seven additional papers** had appeared only in a *reconstructed screening watch*,
not in the 16 older evidence-based DSH decisions above. Their **original PDF v1**
methods, results and caveats were examined on 2026-11-03; the studies themselves
were **not independently replicated**. Dispositions are *proposals pending owner review*.
Full results: [6–12 Oct retrospective scientific review](../../portfolio/2026-10-06--2026-10-12/review.md).
Concrete preliminary project links: [research-to-project mapping](../../portfolio/2026-10-06--2026-10-12/project-fit.md) (profile-based, **not** source-verified).

| Paper | arXiv / DOI | Status |
| --- | --- | --- |
| [HarnessSecurity-Bench](../../studies/harnesssecurity-bench.md) | [arXiv:2610.07639](https://arxiv.org/abs/2610.07639) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [SquidAgent](../../studies/squidagent.md) | [arXiv:2610.08647](https://arxiv.org/abs/2610.08647) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [ExperienceIndex](../../studies/experienceindex.md) | [arXiv:2610.10091](https://arxiv.org/abs/2610.10091) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [DAEDALUS](../../studies/daedalus.md) | [arXiv:2610.08048](https://arxiv.org/abs/2610.08048) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [PackHallu](../../studies/package-hallucination-rule-files.md) | [arXiv:2610.09264](https://arxiv.org/abs/2610.09264) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [POLAR](../../studies/polar.md) | [arXiv:2610.08082](https://arxiv.org/abs/2610.08082) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [REMORY](../../studies/remory.md) | [arXiv:2610.11287](https://arxiv.org/abs/2610.11287) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |

## Full-text checks: 12–19 October historical watch (reviewed 2026-11-03)

The [historical DSH watch](../../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md) was reconstructed screening-only, including **six primary picks and two extra mentions**. All eight original v1 PDFs were subsequently reviewed in full on 2026-11-03, with explicit methodology, result and limitation notes; no independent reproduction was performed.

[Full review](../../portfolio/2026-10-12--2026-10-19/review.md) | [research → project mapping](../../portfolio/2026-10-12--2026-10-19/project-fit.md)

| Study | Full source | Evidence |
| --- | --- | --- |
| [HTN-Orchestrate](../../studies/htn-orchestrate.md) | [arXiv:2610.22195](https://arxiv.org/abs/2610.22195) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [agent-risk](../../studies/agent-risk.md) | [arXiv:2610.16280](https://arxiv.org/abs/2610.16280) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [JevAgentHarness](../../studies/jevagentharness.md) | [arXiv:2610.21412](https://arxiv.org/abs/2610.21412) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [MemComposer](../../studies/memcomposer.md) | [arXiv:2610.21091](https://arxiv.org/abs/2610.21091) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [LAGO](../../studies/lago.md) | [arXiv:2610.19843](https://arxiv.org/abs/2610.19843) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [Agentic Self-Awareness](../../studies/agentic-self-awareness.md) | [arXiv:2610.19226](https://arxiv.org/abs/2610.19226) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [MemScope](../../studies/memscope.md) | [arXiv:2610.21170](https://arxiv.org/abs/2610.21170) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [Matoi](../../studies/matoi.md) | [arXiv:2610.21394](https://arxiv.org/abs/2610.21394) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |

## Full text checked: 20–26 October 2026 (reviewed 2026-11-03)

This window had a separate document-based review; author results were not independently replicated. See [scientific review](../../portfolio/2026-10-20--2026-10-26/review.md) and [explicit project-fit matrix](../../portfolio/2026-10-20--2026-10-26/project-fit.md).

| Study | Primary arXiv work | Evidence status |
| --- | --- | --- |
| [GeoAgent — Contract-Constrained Agents](../../studies/geoagent.md) | [arXiv:2610.31096](https://arxiv.org/abs/2610.31096) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Training Small LMs for Transferable Tool Selection](../../studies/transferable-tool-selection.md) | [arXiv:2610.31483](https://arxiv.org/abs/2610.31483) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Behavior Beyond Text — Refusal Transfer Failure](../../studies/behavior-beyond-text.md) | [arXiv:2610.28982](https://arxiv.org/abs/2610.28982) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Agent Mosaic — Composite Disclosure Risk](../../studies/agent-mosaic.md) | [arXiv:2610.30418](https://arxiv.org/abs/2610.30418) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Silent Cue Loss — Formatting in Document Ingestion](../../studies/silent-cue-loss.md) | [arXiv:2610.30026](https://arxiv.org/abs/2610.30026) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Memory-Centric Continual Learning (MCCL)](../../studies/memory-centric-continual-learning.md) | [arXiv:2610.29357](https://arxiv.org/abs/2610.29357) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [BIRD-RL — Stateful SQL Agent Evaluation](../../studies/bird-rl.md) | [arXiv:2610.29426](https://arxiv.org/abs/2610.29426) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |


METR internal monitoring report: FULL_TEXT_UNAVAILABLE, only public overview; not promoted to source-reviewed paper.


## Full text checked: 27 October–2 November 2026 (reviewed 2026-11-03)

This window had a separate document-based review; author results were not independently replicated. See [scientific review](../../portfolio/2026-10-27--2026-11-02/review.md) and [explicit project-fit matrix](../../portfolio/2026-10-27--2026-11-02/project-fit.md).

| Study | Primary arXiv work | Evidence status |
| --- | --- | --- |
| [Concordat — Typed Sessions for LLM Agents](../../studies/concordat.md) | [arXiv:2610.37461](https://arxiv.org/abs/2610.37461) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Goal-Aware Dynamic Multi-Agent Collaboration (GAD)](../../studies/goal-aware-dynamic-collaboration.md) | [arXiv:2610.39193](https://arxiv.org/abs/2610.39193) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Your Policy Is Secretly a Harness — Decision Geometry](../../studies/decision-geometry-harness.md) | [arXiv:2610.37255](https://arxiv.org/abs/2610.37255) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Where You Inject Matters — Trust Region Effect](../../studies/trust-region-injection.md) | [arXiv:2610.38867](https://arxiv.org/abs/2610.38867) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Poisoned Skills — Agent Markdown Config Injection](../../studies/poisoned-skills.md) | [arXiv:2610.37738](https://arxiv.org/abs/2610.37738) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Agent Transfer Protocol (ATP) — Server-Mediated Communication](../../studies/agent-transfer-protocol.md) | [arXiv:2610.38398](https://arxiv.org/abs/2610.38398) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |

## Original September gap closure (full text reviewed 2026-11-03)

[Scientific source review](../../portfolio/2026-09-03--2026-09-15/review.md) and [project-fit mapping](../../portfolio/2026-09-03--2026-09-15/project-fit.md). Six original full research PDFs checked; one original technical security disclosure separately classified. Earlier DSH owner decisions remain unchanged.

| Source | Original source and version | Evidence type |
| --- | --- | --- |
| [BenchShield — reward-integrity instrumentation](../../studies/benchshield.md) | [2609.11028](https://arxiv.org/abs/2609.11028) | ARXIV_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [SWRouter — multi-turn context-aware model routing](../../studies/swrouter.md) | [2609.11414](https://arxiv.org/abs/2609.11414) | ARXIV_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [ToolGrad — verified chain-first tool-use dataset generation](../../studies/toolgrad.md) | [ACL:2026.findings-acl.950](https://aclanthology.org/2026.findings-acl.950/) | PEER_REVIEWED_ACL_FINDINGS / FULL_TEXT_REVIEWED_2026-11-03 |
| [REVA — Reusable Evidence View Aggregation](../../studies/reva.md) | [2609.11209](https://arxiv.org/abs/2609.11209) | ARXIV_ICDM_ACCEPTED_MANUSCRIPT / FULL_TEXT_REVIEWED_2026-11-03 |
| [NovaFabric — tamper-evident agent run evidence](../../studies/novafabric.md) | [2609.12582](https://arxiv.org/abs/2609.12582) | AUTHOR_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [Random Attention — KV eviction for reasoning](../../studies/random-attention.md) | [2609.03430](https://arxiv.org/abs/2609.03430) | ARXIV_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [CVE-2026-82533 technical disclosure](../../studies/cve-2026-82533-technical-disclosure.md) | [OX Research](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/) | PRIMARY_TECHNICAL_DISCLOSURE, NOT A PAPER |

The [2026-10-07 mathematical DSH assessment](../../archive/dsh/knowledge/research/2026-10-07-math-models-assessment.md) is an existing internal engineering document, not a new paper. The complete original 03–09 Sep digest was not archived; only the named Random Attention candidate could be recovered. NO_CURRENT_TARGET for that KV-serving paper.

## Scope and exclusions

- 2026-09-21: five historical source assessments. Auto Mode public methods were reviewed then, while its PDF appendices were not. A separate full v1 PDF + appendices A–F source check was completed on 2026-11-03 and appended to its card; no local experiment was reproduced.
- 2026-09-28: five full-source / first-party technical reviews; KVSET has an
  additional **bounded local test** on pinned original code, which is not a production benefit claim.
- 2026-10-05: six complete scientific-paper assessments, with methodology,
  caveats and accepted research-only dispositions.
- The original 15 September digest and decision note did not verify the complete methods of all five early candidates. All five plus the separately named 03 Sep Random Attention were given a fresh, version-pinned complete-source review on 2026-11-03 above; prior owner research dispositions remain unchanged.
- The original 12 and 19 October digests remain **reconstructed screening-only summaries**. Seven original 12 October candidates and eight 19 October candidates each now have a separate 2026-11-03 full-text review above; historical originals are unchanged.
- The original 26 October DSH watch is an operator-supplied historical summary, not itself a fresh full-text review. Seven papers from it were separately checked in full on 2026-11-03 above; METR remains FULL_TEXT_UNAVAILABLE.
- The 7 October mathematical-models assessment is original internal engineering evidence, not a scientific paper; it remains in the immutable archive. The original 03–09 September digest was never archived in full (ORIGINAL_DIGEST_NOT_ARCHIVED).

**Evidence levels:** `FULL_TEXT_REVIEW_RECORDED` = an earlier review states
it inspected the complete work (not locally reproduced);
`FULL_ENGINEERING_ARTICLE_REVIEW_RECORDED` and
`FULL_PUBLIC_DISCLOSURE_REVIEW_RECORDED` are primary technical reports
rather than peer-reviewed papers; the other labels record their narrower
qualification. All scores and implementation proposals remain hypotheses
until repeated against a current target project and independent oracle.

**Future reviews:** check these titles, DOIs and URLs before adding a new report.
When reviewing a new source version or another project, create a dated
follow-up in `reports/` and link this prior evidence; do not overwrite history.
