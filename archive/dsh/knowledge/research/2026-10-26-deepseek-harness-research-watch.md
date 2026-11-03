# DeepSeek Harness — Research Watch (20–26 October 2026)

Date of digest: 2026-10-26  
Coverage: **2026-10-20 through 2026-10-26**  
Status: **RESEARCH KNOWLEDGE ONLY — NO IMPLEMENTATION AUTHORIZATION**  
Source: [full original Russian report (extracted text)](sources/2026-10-26-deepseek-harness-research-watch-original-ru.md), supplied by the operator and dated 2026-10-26; this Markdown is an English repository edition, not a verbatim copy. Original chat-renderer citation tokens in the source are archival text and may not resolve outside the original chat. The source report's past description of `Artemedi/deepseek-harness:master` is historical, **not** the current DSH runtime checkpoint.

## Source and evidence rules

The eight items below preserve the supplied report's findings, limitations and suggested experiments; publication links were resolved where possible to stable first-party pages or arXiv identifiers. The METR publication is a public high-level summary of a **non-public internal report**: do not treat it as independently reproducible full-method evidence. Scores such as "priority" are **editorial judgments**, not study outcomes. This import is not a fresh reproduction of every paper's methodology and results. Before endorsing scientific claims or authorizing a PoC, require a legally accessible full-text article (or openly available full methods); otherwise mark `FULL_TEXT_UNAVAILABLE`.

## 1. Monitoring completeness: METR + OpenAI

- Primary report: [METR, Red-Teaming OpenAI's Internal Agent Monitoring Systems (22 Oct)](https://metr.org/blog/2026-10-22-red-teaming-openai-agent-monitoring/)
- Complementary account: [OpenAI, Securing our frontier model training environment (23 Oct)](https://openai.com/index/securing-our-frontier-model-training-environment/)
- Original report takeaway: even sandbox, approval and logging do not by themselves prove that **all execution paths are monitored**. The historical METR exercise found monitoring gaps involving compaction, delayed coverage, trajectory serialization differences and ostensibly read-only tools. METR reviewed historical July 2026 configurations; OpenAI reports fixes to production-relevant issues; those fixes were not re-audited by METR.
- DSH applicability: event and control coverage across SessionEvent, model-derived history, tools, retries, compaction, subagent work and Agent Teams. A monitor observer is **not** an authority-granting or preventive authorization mechanism.
- Falsifiable experiment: 100–200 synthetic trajectories including cancellation, compaction, nested tools, subagents, retries and monitor failure. Reconcile `action initiated → policy evaluated → execution settled → durable event → monitor observed`; inject missing records and require detection.
- Risks/limits: monitoring overhead and asynchronous blind spots; private full METR report is not public. **Policy**: add as security/evidence *evaluation hypothesis*, not a production monitor patch.
- Priority: **P0 evaluation design**, subject to current IQ-F1 scope/owner gates.

## 2. Deterministic artifact contracts: GeoAgent

- Full paper entry: [GeoAgent: Contract-Constrained LLM Agents for Seismic Data Processing](https://arxiv.org/abs/2610.31096).
- Original report: nine-stage seismic processing system using named artifacts, deterministic input resolution, parameter takeover and output validation. A demonstration on a single dataset is **not** a broad agent-harness benchmark.
- DSH applicability: protect transitions in `generate → compile → test → package` from incorrect input artifact selection and false completion, **without** modifying generic agent loop.
- Experiment: 50 multi-step coding tasks, comparing prompt-only, schema-only and schema + deterministic artifact contracts; measure true final artifact correctness, not tool-call syntax alone.
- Risks: workflow-specific contract maintenance and over-restricting valid creative paths.
- Priority: **P1 offline workflow PoC**, no generic contract framework.

## 3. Selective tool visibility

- Full paper entry: [Training Small Language Models for Transferable Tool Selection](https://arxiv.org/abs/2610.31483).
- Original report: `Plan → Retrieve → Select` with a trained small model; tool-set exact-match evaluation is **not equivalent to downstream task success**; training checkpoints/code were reported unavailable at digest time.
- DSH applicability: selection of model-visible schemas using existing tool registry/restrictions, without weakening runtime authorization; always retain a path to discover tools omitted by a selector.
- Experiment: 100–200 held-out tasks: all tools vs BM25 Top-K vs small/LLM selector; measure **required-tool recall, task success, token overhead, TTFT and cost**.
- Risk: excluded essential tools, wasted selector calls.
- Priority: **P1 offline benchmark**, BM25 before SFT/RL.

## 4. Text refusal is not tool safety

- Full paper entry: [Behavior Beyond Text: Evaluating Refusal Transfer Failure in LLM Agents](https://arxiv.org/abs/2610.28982).
- Original report: 2,304 matched prompts across four domains; some requests refused in text nonetheless produced unsafe tool actions (reported 10–52%, depending on model/configuration).
- DSH applicability: evaluate **attempted calls, actual effects and false positives**, rather than relying on benign/declining prose. Tool authorization must not inherit authority from model refusal.
- Experiment: paired text-only/tool-enabled scenarios with known forbidden actions and allowed controls.
- Priority: **P1 security-regression design**. No claim this paper proves a vulnerability in DSH.

## 5. Cross-document mosaic disclosure

- Full paper entry: [Agent Mosaic: Recognizing Confidentiality Leaks in Agentic LLM Systems](https://arxiv.org/abs/2610.30418).
- Original report: access to individual permitted documents does not imply permission to reveal a sensitive **composite inference**; studied synthetic cases and live agents.
- DSH applicability: Agent Teams, tool/MCP outputs and outbound messages. Evaluate recipient/scope-based information-flow guarantees; do not pretend per-document ACL is sufficient.
- Experiment: 30 synthetic document corpora with explicit composite forbidden facts, compare document-only gating vs outbound disclosure verification.
- Risks: false positives and policy ambiguity; no automatic universal semantic DLP in the recovery path.
- Priority: **P2 security benchmark**.

## 6. Document ingestion may discard meaning

- Full paper entry: [What the Author Wrote, What the Agent Reads: Silent Cue Loss in Enterprise Document Ingestion](https://arxiv.org/abs/2610.30026).
- Original report: extraction of PDF/DOCX as plain text loses formatting cues (especially highlight and color) that encode requirements; measured on 76 real policy documents. The report quotes micro-F1 0.690 with cues vs 0.150 / 0.075 for tested lossy pipelines.
- DSH applicability: **only if** a real ingestion/converter workflow drops these cues. Do not change `agent-loop` for a speculative document-converter failure.
- Experiment: 30 deterministic test documents with known style-marked constraints; evaluate plain text vs explicit formatting annotations, including token cost.
- Priority: **P2 conditional ingestion PoC**.

## 7. Does memory improve future work?

- Full paper entry: [Memory-Centric Continual Learning for AI Agents](https://arxiv.org/abs/2610.29357).
- Original report: evaluate memory by behavioral improvement across **retention under interference, adaptation, and transfer**, not just retrieval precision; the paper provides a framework, not a proven production MemoryCore replacement.
- DSH applicability: Milestone 7 recall/routing proof, Shared Memory vs baseline evaluation and later Skill Evolution, with fixed model/tools/environment.
- Experiment: no-memory vs retrieval-only vs evolving memory on three split families; report task-level quality, provenance and storage/cost.
- Priority: **P1 evaluation methodology only**.

## 8. Additional engineering paper: BIRD-RL

- Full paper entry: [BIRD-RL: Scaling Agentic Reinforcement Learning over Stateful Data-Centric Environments](https://arxiv.org/abs/2610.29426).
- Original report: trajectory-scoped persistent execution environments for SQL/data tasks to prevent contaminated state; authors report 12.8× infrastructure spatial efficiency and BIRD-CRITIC-SQLite results.
- DSH applicability: **offline test/eval infrastructure**, especially database-backed tool chains (PostgreSQL/MSSQL scenarios), not a change to production DSH execution or an RL training commitment.
- Experiment: isolated DB container per trajectory vs snapshot/replica reuse, measuring setup time, disk, state isolation and replay determinism.
- Priority: **P2 offline infrastructure evaluation**.

## Editorial priority and implementation separation

| Track | Work now (research/design only) | Experiment gate | Production gate |
|---|---|---|---|
| Monitoring completeness | Coverage matrix and missing-event fixtures | Security/telemetry harness and isolated scorer | Complete contract + owner-approved scope |
| Artifact contracts | Narrow workflow contract spec | Disposable coding benchmark | Proven improvement without breaking accepted tools |
| Tool selection | Required-tool oracle and baseline | Full vs BM25 vs selector | No quality regression; Model Trust unchanged |
| Refusal/tool safety | Paired unsafe-action fixtures | Isolated tool execution | Proven policy enforcement |
| Mosaic disclosure | Confidentiality threat model | Synthetic multi-agent fixtures | Authorized outbound-policy design |
| Ingestion cue loss | Converter capability inventory | Formatting-preserving extraction PoC | Only when real converter seam warrants it |
| Continual memory | Retention/adaptation/transfer protocol | Stable runtime/eval harness | Quality benefit vs no-memory/retrieval-only baseline |
| BIRD-RL | Stateful sandbox design hypothesis | Disposable database trajectories | Infrastructure approval, not agent-loop feature |

## Actual DSH checkpoint matters

The September research-assimilation plan describes an earlier recovery stage. At time of this archival addition, consult `AGENTS.md` then `docs/iq-f1-orchestration/STATE.md` and `EVENTS.jsonl`: **IQ-F1 remains independently gated; a research document cannot authorize Host implementation, change owner decisions, relax AF-003, or promote a model.** `ROADMAP.md`, `docs/recovery-action-map.md` and this note are not current-state authorities.

## Related historical reports

- [15 Sep — initial Research Watch](2026-09-15-deepseek-harness-research-watch.md)
- [21 Sep — reconstructed edition](2026-09-21-deepseek-harness-research-watch-reconstructed.md)
- [28 Sep — reconstructed edition](2026-09-28-deepseek-harness-research-watch-reconstructed.md)
- [05 Oct — reconstructed edition](2026-10-05-deepseek-harness-research-watch-reconstructed.md)
- [12 Oct — reconstructed edition](2026-10-12-deepseek-harness-research-watch-reconstructed.md)
- [19 Oct — reconstructed edition](2026-10-19-deepseek-harness-research-watch-reconstructed.md)
- [07 Oct — separate mathematics assessment](2026-10-07-math-models-assessment.md)
