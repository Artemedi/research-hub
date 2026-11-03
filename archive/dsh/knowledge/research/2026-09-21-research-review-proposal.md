# DSH Research Review Proposal — 15–21 September 2026

Prepared: 2026-10-30  
Status: **OPERATOR-ACCEPTED RESEARCH DISPOSITIONS — NON-NORMATIVE CLASS D**  
Historical source: [reconstructed weekly index](2026-09-21-deepseek-harness-research-watch-reconstructed.md). This is a fresh applicability review using public primary-source material, **not** a reproduction of an original missing newsletter. No authorizations or changes to IQ-F1, AF-003, worker/model admission, runtime code, or registered artifacts are implied.

## Operator decision — 2026-10-30

The operator explicitly accepted all five dispositions after the independent review: Auto Mode **KEEP security regression scope**, REALM **ACCEPT offline reconsolidation experiment hypothesis only**, DRAG **ACCEPT offline retriever/generator benchmark only**, Paper2Agent **ACCEPT bounded research-pipeline pilot (first priority of interest)**, and CERA-MoA **SKIP current DSH Runtime implementation**. These are research-level decisions; they do not change current IQ-F1, AF-003, Model Trust or Host authorization.

**Paper2Agent execution path:** [P2A-001 isolated research-pipeline pilot scope](pilots/P2A-001-paper2agent-research-pipeline.md). This is a staged pilot design, not a completed execution or deployment.

## Scientific evidence ledger

| Candidate | Primary source and full-method inspection | Supported result; key caveat | Proposed DSH disposition |
| --- | --- | --- | --- |
| Red-Teaming Auto Mode | [arXiv:2609.19587](https://arxiv.org/abs/2609.19587) and [authors' detailed public article](https://alignment.anthropic.com/2026/red-teaming-auto-mode/) (methods, results, limitations; PDF appendices not independently inspected) | Tested blocking monitors against deliberate adversarial agent strategies; reported high bypass rates, with failures across forged transcript, compaction, multi-agent boundaries and unreviewed working-directory changes. September system snapshot, security observer assumed trustworthy, sandbox itself not evaluated. | **KEEP / high-priority isolated security regression inventory**, not a DSH agentic-monitor replacement; ensure action-authority validation, role framing, coverage across delegation/compaction, and monitor performance. |
| REALM | [arXiv:2609.16053 full HTML](https://arxiv.org/abs/2609.16053), method, results, ablations and appendices checked | LoCoMo 75.97%, LongMemEval 65.11%; isolated retrieval-triggered reconsolidation effect +2.01 and +2.13 points vs own no-recon variant. LoCoMo/LongMemEval judge evaluated using GPT-4o-mini; benchmark QA not equivalent to coding/DBA task success. Extra graph mutation/update work adds cost/risks. | **ACCEPT offline memory-quality hypothesis; DEFER structural memory rewrite.** Test changes to *derived* retrieval topology against immutable Memory events and fixed BM25/retrieval baselines, with feedback trust and rollback. |
| DRAG | [arXiv:2609.17709 full HTML](https://arxiv.org/abs/2609.17709), methods/results reviewed | Tests joint retriever rank (BM25 / E5 / reranking / decomposition) and generator effort on four QA datasets. Training-free DRAG_QPP uses Avg-IDF and context perplexity; SFT variant needs supervised data. Retrieval quality can matter more than increased generation effort; latency comparisons use a specific vLLM/A100 stack and do not include all preprocessing. | **ACCEPT a narrow offline RAG cost/quality ablation** over an existing Team Context / Memory read-only consumer, **not** a new agent/router component. Evaluate retrieval tiers and admitted model candidates separately; DSH Model Trust always first. |
| Paper2Agent | [Nature full HTML](https://www.nature.com/articles/s41586-026-11044-y), methods/results/discussion checked | From 100 biology papers, 74 could be agentified, yielding 599 proposed tools, 593 validation passes. Paper-backed MCP tools bind to reference code/results and are tested; not all research repos runnable. Benchmarks stress reuse/faithfulness; high-level scientific interpretation still human-owned. | **ACCEPT a bounded experiment** using 1–3 well documented research codebases to build validated *sandboxed* MCP adapters, compare with manual wrapping, and preserve references/tests/hashes; **reject automatic trust/public deployment**. Not a general new agent framework. |
| CERA-MoA | [arXiv:2609.18779 full HTML](https://arxiv.org/abs/2609.18779), method/experiments/appendix reviewed | Co-trains LoRA specialist policies and familiarity router using mid-layer model hidden states and RL; on Qwen3-4B reported OOD 72.8 avg vs best listed other 71.5. Benefits not established for opaque cloud API providers; needs hidden-state access, training infrastructure and quality-eval loop. | **SKIP DSH runtime implementation / RETAIN as future self-hosted training research**. Do not confuse with 9Router availability or DSH Model Trust tier; experiment only if owning trainable backend and stable held-out benchmark. |

## Recommended research work order (approved as priorities; no runtime implementation authorization)

1. **Security coverage assessment**: list authorization/monitor coverage for compaction summaries, tool edits, delayed execution, handoffs, cross-session workspace and role-framing, including negative tests; do not add model-based monitor by default.
2. **Memory quality benchmark design**: immutable source event log; derived graph/projection only; query-answer validation and no-regression/cost evidence before active reconsolidation.
3. **Paper2Agent narrow reproducible tools**: one disposable scientific or coding workflow, static dependencies/versions, independent output oracle, capability-limited MCP endpoint and teardown.
4. **DRAG offline comparison**: first retrieval-only selection vs fixed retrieval and fixed strong model; only later combine retrieval + model selection within eligible set.
5. **CERA-MoA**: archive as out-of-scope training/serving research.

The operator accepted these research dispositions. Implementing even an accepted experimental candidate requires the applicable current class/scope permissions; do not silently expand Host or research-task privileges. Source paper author date and weekly digest coverage are separate; REALM first appeared 13 September even though included in the 15–21 September weekly reconstructed index.

## Open validation before any implementation

- Compare each proposed regression/benchmark to actually implemented tests at pinned DSH runtime refs; this review did not execute local test suites or verify Host closure.
- Keep threat-model claims for the Auto Mode article distinct from full paper appendix verification and from demonstration of a DSH vulnerability.
- Measure final task states and costs, not only LLM-as-judge answer agreement, selected tools or route cost.
- Research dispositions were accepted by the operator on 2026-10-30. This does not confirm source-code implementation, independent reproduction of paper claims, or a production/Host authorization.
