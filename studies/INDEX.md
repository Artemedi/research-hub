# Individually indexed studies — previously reviewed in DSH

**Telegram BK-034 — autoresearch:** [карточка репозитория](karpathy-autoresearch.md), [source review](../reports/2026-11-04-bk034-autoresearch-review.md); видео недоступно, обучение не запускалось.

**Telegram BK-029 — 0-CODE:** [карточка](zero-code.md), [source review и synthetic guard tests](../reports/2026-11-04-bk029-zero-code-review.md); полноценный цикл не запускался.

**Telegram BK-028 — Hyperresearch:** [карточка](hyperresearch.md), [source review и synthetic citation fixture](../reports/2026-11-04-bk028-hyperresearch-review.md); полноценный pipeline не запускался.

**Telegram BK-026 — Julia 1:** [карточка](julia-1.md), [source review и synthetic probability fixture](../reports/2026-11-04-bk026-julia-1-review.md); inference не запускался.

**Telegram BK-025 — Unreal Agent video:** [карточка](unreal-agent-bk025.md), [provenance и отсрочка](../reports/2026-11-04-bk025-unreal-video-provenance.md); `FULL_TEXT_UNAVAILABLE`, метод не оценён.

**Telegram BK-024 — Local Knowledge Graph:** [карточка](local-knowledge-graph.md), [обзор и synthetic graph tests](../reports/2026-11-04-bk024-local-knowledge-graph-review.md); модель и реальный корпус не запускались.

**Telegram BK-022 — Microsoft Skill Recorder:** [карточка](microsoft-skill-recorder.md), [обзор и узкий synthetic privacy test](../reports/2026-11-04-bk022-skill-recorder-review.md); Copilot и реальная запись не запускались.

**Telegram BK-019 — Warp Skill Doctor:** [карточка](warp-skill-doctor.md), [обзор и изолированный тест атрибуции](../reports/2026-11-04-bk019-warp-skill-doctor-review.md); качество рекомендаций не проверялось.

**Telegram BK-016 — Claude Swarm:** [карточка](claude-swarm.md), [обзор исходных контрактов и project fit](../reports/2026-11-04-bk016-claude-swarm-review.md); найдено неподключение enforcement в штатной инициализации, динамический запуск не проводился.

**Telegram BK-011 — SIMURG:** [карточка](simurg.md), [обзор и изолированные проверки](../reports/2026-11-04-bk011-simurg-review.md): найдены ошибки AUROC и ограничения калибровки; польза проектам не измерена.

**Telegram BK-006 — Open Steps:** [инженерная карточка](open-steps.md), [обзор и ограниченная проверка хуков](../reports/2026-11-04-bk006-open-steps-review.md). Найден пропуск изменения untracked-файла; качество ответов не измерено.

**Telegram BK-014 — alphaXiv OpenResearch:** [source-reviewed engineering card](alphaxiv-openresearch.md), [Git-snapshot/full-text/security and project-fit report](../reports/2026-11-04-bk014-openresearch-review.md). Full-text metadata trap confirmed in original Rust source; only dsh-paper2agent profile matched; LAB_NOT_RUN and no adoption approval.

**Telegram BK-002 — Tencent TeamAI CLI:** [инженерная карточка](tencent-teamai-cli.md) и [полная сверка upstream↔fork и применимости к трём проектам](../reports/2026-11-04-bk002-tencent-teamai-cli-review.md). Source review, 6 merge conflicts; никакого исполнения TeamAI/лаборатории.

**Telegram BK-041 / BK-059 — независимые инженерные проверки вне DSH:** [Inspektor Gadget v0.57.0](inspektor-gadget.md) — [permission gate на Bazzite, eBPF tracing BLOCKED](../reports/2026-11-04-bk041-inspektor-gadget-gate.md); [IPFire fireperf 0.3.0](ipfire-fireperf.md) — [изолированный реальный loopback lab, 12×20 TCP](../reports/2026-11-04-bk059-fireperf-loopback.md). Первое остаётся `AWAITING_REAL_TRACE`, второе `ORIGINAL_BINARY_LOOPBACK_VERIFIED`; ни одно не получает production approval.

**Инженерные инструменты с лабораторной MCP-проверкой:** [Google MCP Toolbox / PostgreSQL](mcp-toolbox-postgres.md) — [проверенный live SQL и снимки Wiki_PG](../reports/2026-11-04-mcp-toolbox-vs-wikipg-postgres-lab.md), `LIMITED_FIXTURE_PASS / NO_PRODUCTION_APPROVAL`.

**Новое исследование с лабораторным тестом selection mechanics (не воспроизведение LLM-экспериментов):** [RRSI](rrsi.md) и [Harness²](harness2.md) — [протокол](../reports/2026-11-04-rrsi-harness2-overfit-lab.md).

**Новые инженерные проверки (отдельно от научных full-text reviews):** [pgbot — PostgreSQL diagnostic lab, v0.9.0](pgbot.md) — `LAB_VERIFIED / NO_PRODUCTION_APPROVAL`, [протокол](../reports/2026-11-04-pgbot-postgresql-lab.md).

This index promotes **16 historically source-reviewed items** from the original DSH
research decisions into separate traceable records. Their original reviews and
full methodological qualifications are preserved via pinned SHA and archive links.
This is a document migration and extraction, **not a new independent replication**.

[**Historical project-fit matrix (16 papers)**](../reports/2026-11-03-project-mapping-historical-16.md) — linked to project profiles, proposed offline tests, and explicit NO_CURRENT_TARGET cases. This is a profile-based retrospective, not new scientific review.

| Study | Area | Historical evidence status |
| --- | --- | --- |
| [Red-Teaming Auto Mode](red-teaming-auto-mode.md) | `SECURITY` | `HISTORICAL_METHODS_ONLY; PDF_APPENDICES_REVIEWED_2026-11-03` |
| [REALM — Retrieval-Driven Memory Reconsolidation](realm.md) | `MEMORY` | `FULL_TEXT_REVIEW_RECORDED` |
| [DRAG — Dynamic Retriever and Generator Selection](drag.md) | `RETRIEVAL` | `FULL_TEXT_REVIEW_RECORDED` |
| [Paper2Agent — Research Papers as Reliable AI Agents](paper2agent.md) | `RESEARCH_WORKFLOW` | `FULL_TEXT_REVIEW_RECORDED` |
| [CERA-MoA — Adaptive Multi-Agent Routing](cera-moa.md) | `MODEL_ROUTING` | `FULL_TEXT_REVIEW_RECORDED` |
| [Where Does Exactly-Once Live? / LIMBO](exactly-once-limbo.md) | `RELIABILITY` | `FULL_TEXT_REVIEW_RECORDED` |
| [Cursor — Improved Token Efficiency](cursor-token-efficiency.md) | `INFERENCE_EFFICIENCY` | `FULL_ENGINEERING_ARTICLE_REVIEW_RECORDED` |
| [StateComp — State-Conditioned Context Compression](statecomp.md) | `CONTEXT_MANAGEMENT` | `FULL_TEXT_REVIEW_RECORDED` |
| [Self-Replicating Prompt Injections Exist](self-replicating-prompt-injections.md) | `SECURITY` | `FULL_PUBLIC_DISCLOSURE_REVIEW_RECORDED` |
| [KVSET — The KV Cache Working Set](kvset.md) | `KV_CACHE` | `FULL_TEXT_REVIEW_AND_LOCAL_TOOL_TEST_RECORDED` |
| [VeriHarness — Evidence-Grounded Agentic Verification](veriharness.md) | `VERIFICATION` | `FULL_TEXT_REVIEW_RECORDED` |
| [Agent Error Dataset — Trace-Grounded Diagnosis and Replay](agent-error-dataset.md) | `ERROR_RECOVERY` | `FULL_TEXT_REVIEW_RECORDED` |
| [Covert Assistance — Helpful LLM Agents Evade Oversight](covert-assistance.md) | `SECURITY` | `FULL_TEXT_REVIEW_RECORDED` |
| [MAADBench — Multi-Agent Anomaly and Fault Benchmarks](maadbench.md) | `EVALUATION` | `FULL_TEXT_REVIEW_RECORDED` |
| [ReCAP — Persistent Context Graphs for Memory Compaction](recap.md) | `MEMORY` | `FULL_TEXT_REVIEW_RECORDED` |
| [KVTether — KV Cache Lifecycle Management in ReAct Agents](kvtether.md) | `KV_CACHE` | `FULL_TEXT_REVIEW_RECORDED` |

## New full-text checks: 6–12 October watch (reviewed 2026-11-03)

These **seven additional papers** had appeared only in a *reconstructed screening watch*,
not in the 16 older evidence-based DSH decisions above. Their **original PDF v1**
methods, results and caveats were examined on 2026-11-03; the studies themselves
were **not independently replicated**. Dispositions are *proposals pending owner review*.
Full results: [6–12 Oct retrospective scientific review](../reports/2026-11-03-review-of-2026-10-06-to-12.md).
Concrete preliminary project links: [research-to-project mapping](../reports/2026-11-03-project-mapping-2026-10-06-to-12.md) (profile-based, **not** source-verified).

| Paper | arXiv / DOI | Status |
| --- | --- | --- |
| [HarnessSecurity-Bench](harnesssecurity-bench.md) | [arXiv:2610.07639](https://arxiv.org/abs/2610.07639) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [SquidAgent](squidagent.md) | [arXiv:2610.08647](https://arxiv.org/abs/2610.08647) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [ExperienceIndex](experienceindex.md) | [arXiv:2610.10091](https://arxiv.org/abs/2610.10091) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [DAEDALUS](daedalus.md) | [arXiv:2610.08048](https://arxiv.org/abs/2610.08048) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [PackHallu](package-hallucination-rule-files.md) | [arXiv:2610.09264](https://arxiv.org/abs/2610.09264) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [POLAR](polar.md) | [arXiv:2610.08082](https://arxiv.org/abs/2610.08082) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [REMORY](remory.md) | [arXiv:2610.11287](https://arxiv.org/abs/2610.11287) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |

## Full-text checks: 12–19 October historical watch (reviewed 2026-11-03)

The [historical DSH watch](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md) was reconstructed screening-only, including **six primary picks and two extra mentions**. All eight original v1 PDFs were subsequently reviewed in full on 2026-11-03, with explicit methodology, result and limitation notes; no independent reproduction was performed.

[Full review](../reports/2026-11-03-full-text-review-2026-10-12-to-19.md) | [research → project mapping](../reports/2026-11-03-project-mapping-2026-10-12-to-19.md)

| Study | Full source | Evidence |
| --- | --- | --- |
| [HTN-Orchestrate](htn-orchestrate.md) | [arXiv:2610.22195](https://arxiv.org/abs/2610.22195) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [agent-risk](agent-risk.md) | [arXiv:2610.16280](https://arxiv.org/abs/2610.16280) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [JevAgentHarness](jevagentharness.md) | [arXiv:2610.21412](https://arxiv.org/abs/2610.21412) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [MemComposer](memcomposer.md) | [arXiv:2610.21091](https://arxiv.org/abs/2610.21091) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [LAGO](lago.md) | [arXiv:2610.19843](https://arxiv.org/abs/2610.19843) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [Agentic Self-Awareness](agentic-self-awareness.md) | [arXiv:2610.19226](https://arxiv.org/abs/2610.19226) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [MemScope](memscope.md) | [arXiv:2610.21170](https://arxiv.org/abs/2610.21170) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |
| [Matoi](matoi.md) | [arXiv:2610.21394](https://arxiv.org/abs/2610.21394) | `FULL_TEXT_REVIEWED_2026-11-03 / PROPOSED_ONLY` |

## Full text checked: 20–26 October 2026 (reviewed 2026-11-03)

This window had a separate document-based review; author results were not independently replicated. See [scientific review](../reports/2026-11-03-full-text-review-2026-10-20-to-26.md) and [explicit project-fit matrix](../reports/2026-11-03-project-mapping-2026-10-20-to-26.md).

| Study | Primary arXiv work | Evidence status |
| --- | --- | --- |
| [GeoAgent — Contract-Constrained Agents](geoagent.md) | [arXiv:2610.31096](https://arxiv.org/abs/2610.31096) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Training Small LMs for Transferable Tool Selection](transferable-tool-selection.md) | [arXiv:2610.31483](https://arxiv.org/abs/2610.31483) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Behavior Beyond Text — Refusal Transfer Failure](behavior-beyond-text.md) | [arXiv:2610.28982](https://arxiv.org/abs/2610.28982) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Agent Mosaic — Composite Disclosure Risk](agent-mosaic.md) | [arXiv:2610.30418](https://arxiv.org/abs/2610.30418) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Silent Cue Loss — Formatting in Document Ingestion](silent-cue-loss.md) | [arXiv:2610.30026](https://arxiv.org/abs/2610.30026) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Memory-Centric Continual Learning (MCCL)](memory-centric-continual-learning.md) | [arXiv:2610.29357](https://arxiv.org/abs/2610.29357) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [BIRD-RL — Stateful SQL Agent Evaluation](bird-rl.md) | [arXiv:2610.29426](https://arxiv.org/abs/2610.29426) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |


METR internal monitoring report: FULL_TEXT_UNAVAILABLE, only public overview; not promoted to source-reviewed paper.


## Full text checked: 27 October–2 November 2026 (reviewed 2026-11-03)

This window had a separate document-based review; author results were not independently replicated. See [scientific review](../reports/2026-11-03-full-text-review-2026-10-27-to-11-02.md) and [explicit project-fit matrix](../reports/2026-11-03-project-mapping-2026-10-27-to-11-02.md).

| Study | Primary arXiv work | Evidence status |
| --- | --- | --- |
| [Concordat — Typed Sessions for LLM Agents](concordat.md) | [arXiv:2610.37461](https://arxiv.org/abs/2610.37461) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Goal-Aware Dynamic Multi-Agent Collaboration (GAD)](goal-aware-dynamic-collaboration.md) | [arXiv:2610.39193](https://arxiv.org/abs/2610.39193) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Your Policy Is Secretly a Harness — Decision Geometry](decision-geometry-harness.md) | [arXiv:2610.37255](https://arxiv.org/abs/2610.37255) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Where You Inject Matters — Trust Region Effect](trust-region-injection.md) | [arXiv:2610.38867](https://arxiv.org/abs/2610.38867) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Poisoned Skills — Agent Markdown Config Injection](poisoned-skills.md) | [arXiv:2610.37738](https://arxiv.org/abs/2610.37738) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |
| [Agent Transfer Protocol (ATP) — Server-Mediated Communication](agent-transfer-protocol.md) | [arXiv:2610.38398](https://arxiv.org/abs/2610.38398) | FULL_TEXT_REVIEWED_2026-11-03 / PROJECT_PROFILE_MATCH / PROPOSED_ONLY |

## Original September gap closure (full text reviewed 2026-11-03)

[Scientific source review](../reports/2026-11-03-historical-gap-closure-2026-09-03-to-15.md) and [project-fit mapping](../reports/2026-11-03-project-mapping-september-gaps.md). Six original full research PDFs checked; one original technical security disclosure separately classified. Earlier DSH owner decisions remain unchanged.

| Source | Original source and version | Evidence type |
| --- | --- | --- |
| [BenchShield — reward-integrity instrumentation](benchshield.md) | [2609.11028](https://arxiv.org/abs/2609.11028) | ARXIV_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [SWRouter — multi-turn context-aware model routing](swrouter.md) | [2609.11414](https://arxiv.org/abs/2609.11414) | ARXIV_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [ToolGrad — verified chain-first tool-use dataset generation](toolgrad.md) | [ACL:2026.findings-acl.950](https://aclanthology.org/2026.findings-acl.950/) | PEER_REVIEWED_ACL_FINDINGS / FULL_TEXT_REVIEWED_2026-11-03 |
| [REVA — Reusable Evidence View Aggregation](reva.md) | [2609.11209](https://arxiv.org/abs/2609.11209) | ARXIV_ICDM_ACCEPTED_MANUSCRIPT / FULL_TEXT_REVIEWED_2026-11-03 |
| [NovaFabric — tamper-evident agent run evidence](novafabric.md) | [2609.12582](https://arxiv.org/abs/2609.12582) | AUTHOR_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [Random Attention — KV eviction for reasoning](random-attention.md) | [2609.03430](https://arxiv.org/abs/2609.03430) | ARXIV_PREPRINT / FULL_TEXT_REVIEWED_2026-11-03 |
| [CVE-2026-82533 technical disclosure](cve-2026-82533-technical-disclosure.md) | [OX Research](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/) | PRIMARY_TECHNICAL_DISCLOSURE, NOT A PAPER |

The [2026-10-07 mathematical DSH assessment](../archive/dsh/knowledge/research/2026-10-07-math-models-assessment.md) is an existing internal engineering document, not a new paper. The complete original 03–09 Sep digest was not archived; only the named Random Attention candidate could be recovered. NO_CURRENT_TARGET for that KV-serving paper.

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
