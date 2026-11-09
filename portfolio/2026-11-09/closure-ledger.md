# Research portfolio: evidence-qualified terminal dispositions for 83 cards

**Date:** 2026-11-09. **Result:** 83/83 terminal research dispositions, 0 open.

| Disposition | Cards | What is actually closed |
| --- | ---: | --- |
| ACCEPT_BOUNDED | 40 | Only the explicitly tested engineering or synthetic proposition; not original whole-paper replication |
| ACCEPT_RESEARCH_ONLY | 39 | 37 prior full-primary method reviews plus 2 narrower official engineering/disclosure references; no author gains reproduced |
| BLOCKED | 2 | Pinpointed original-source unsafe adoption path, actual counterexample, tested alternative and unblock rule |
| NO_FIT | 2 | Concrete method needs a capability absent from currently documented 45-project portfolio; reopen on source/capability change |

The [83-card machine ledger](../../data/results/research-portfolio/2026-11-09-closure-ledger.json) contains original card and review SHA-256, primary URL, previous full-source provenance, per-study method/obstacle, negative evidence, limits and reopening conditions. The [reproduction script](../../experiments/research-portfolio/2026-11-09-closure-ledger.py) deliberately does not infer acceptance from a generic PASS, document count or project-name overlap.

**Critical distinction:** terminal portfolio research disposition is NOT scientific replication and is NOT project implementation approval. The authors' experimental scores remain AUTHOR_REPORTED/NOT_REPRODUCED unless independently scoped evidence says exactly otherwise. Production approval is false for all 83.

## ACCEPT_BOUNDED: measured narrow properties

| Study | Accepted measurable property or negative finding | Evidence |
| --- | --- | --- |
| agent-error-dataset | Checkpoint-bound correction: 90 synthetic paired trials; 270 negative controls. | [review](../../reviews/agent-error-dataset/2026-11-08-checkpoint-replay-ab.md) |
| agent-mosaic | Independent synthetic oracle validated 270 composite-disclosure gate cases; output-bound gate released 90/90 allowed outputs without false disclosure release. | [review](../../reviews/agent-mosaic/2026-11-07-composite-gate.md) |
| agent-risk | Targeted replay versus live oracle on 200 synthetic finite episodes and assumption-breaking controls. | [review](../../reviews/agent-risk/2026-11-09-replay-assumptions.md) |
| alphaxiv-openresearch | 25 synthetic Git source-snapshot comparisons: original paper2project tree_hash vs source-derived git-archive proxy, checksum/dirty/metadata/corruption controls. | [review](../../reviews/alphaxiv-openresearch/2026-11-06-provenance-ab.md) |
| benchshield | Independent synthetic reward-lifecycle monitor on 100 constructed cases: 30 VIOLATION, 30 CLEAR, 40 ABSTAIN and tampered-log controls. | [review](../../reviews/benchshield/2026-11-04.md) |
| cera-moa | Independent synthetic oracle of cumulative-threshold routing rule over 10,000 scenarios. | [review](../../reviews/cera-moa/2026-11-08-routing-contract.md) |
| chartli | Independent XML and finite SVG geometry oracles on 16 original-source fixtures with bad-input controls. | [review](../../reviews/chartli/2026-11-07-svg-validation.md) |
| cursor-token-efficiency | Local deterministic 260-task context-character proxy reduces size by ~50% with oracle routing, but keyword routing misses 40/260; author 7% is unreplicated. | [review](../../reviews/cursor-token-efficiency/2026-11-07-council-vs-single.md) |
| decision-geometry-harness | Pinned DSH serializer schema-order paired provider tool-choice proxy: independent wire oracle 48/48 paired outcomes, mutation controls; native tool-use has a malformed/failed variant. | [review](../../reviews/decision-geometry-harness/2026-11-07-native-tool-ab.md) |
| drag | Synthetic RAG evidence guard passes sealed in-distribution fixtures yet fails under format shift and forged-evidence OOD stress. | [review](../../reviews/drag/2026-11-06-evidence-gate-ab.md) |
| dsh-creator-mode | Generated code client was verified in offline mock Cordis/React harness: 9/9 authored contract tests; 210 host/client suite tests passed separately. | [review](../../reviews/dsh-creator-mode/2026-11-06-external-generator-probe.md) |
| dsh-superagent-prototype | Pinned original in-memory core passed 15/15 isolated Ticket/Mandate/lifecycle contract cases and one independently introduced revoked-mandate mutant failed. | [review](../../reviews/dsh-superagent-prototype/2026-11-05.md) |
| exactly-once-limbo | Pinned TelegramBot main() under synthetic transport: 900 fault cases/arm expose retry and at-most-once loss/duplicate tradeoff. | [review](../../reviews/exactly-once-limbo/2026-11-06-policy-ab.md) |
| experienceindex | Independent Git SHA/href/source-pointer audit: 33/33 explicit related-review navigation cases, corrupt hash rejected; hit@5 baseline 32/33 vs link-augmented 33/33. | [review](../../reviews/experienceindex/2026-11-07.md) |
| goal-aware-dynamic-collaboration | 35 pinned DSH task-graph validator cases and 35 external guarded synthetic cases matched separately encoded oracle, 70/70; mutant refused. | [review](../../reviews/goal-aware-dynamic-collaboration/2026-11-07.md) |
| gpt6-astra-skills-prompts | Five paired disposable coding tasks with real requested Astra model: both treatments 5/5 functional; reduced-context arm used 46.72% fewer input tokens and 13% less wall time. | [review](../../reviews/gpt6-astra-skills-prompts/2026-11-06-live-astra-ab.md) |
| harness2 | Pinned Harness2 selection-pool sanity check and shared 525-case synthetic selector-validation fixture: external guard picks locality candidate on 5/5 seeds. | [review](../../reviews/rrsi/2026-11-06-validation-ab.md) |
| htn-orchestrate | 43 pinned upstream targeted tests plus 30 synthetic static DAG checks and 20 surrogate resumes. | [review](../../reviews/htn-orchestrate/2026-11-08-paired-audit-followup.md) |
| inspektor-gadget | Pinned Inspektor Gadget trace_exec --filter.exec captured 200/200 positive and 0/25 negative synthetic rootless Podman events. | [review](../../reviews/inspektor-gadget/2026-11-06-privileged-podman-trace.md) |
| ipfire-fireperf | Original compiled fireperf 0.3.0 inside offline rootless Podman completed 12 isolated loopback runs, 240/240 connections; refused-port control detected. | [review](../../reviews/ipfire-fireperf/2026-11-04.md) |
| julia-1 | Original Julia-1 display_probabilities on three authored positive/negative vectors, including .95 saturation and pruning. | [review](../../reviews/julia-1/2026-11-04.md) |
| karpathy-autoresearch | Actual pinned Wiki_PG autoloop script on six toy Git worktrees: 3/3 domain-only runs missed heldout UI and 3/3 complete runs passed. | [review](../../reviews/karpathy-autoresearch/2026-11-06-loop-audit.md) |
| local-knowledge-graph | Original strongest_path in synthetic directed graph selects reverse traversal 3→2; max-product path differs from highest geometric-mean path. | [review](../../reviews/local-knowledge-graph/2026-11-04.md) |
| mcp-toolbox-postgres | Previously recorded original MCP Toolbox 1.15.0 versus Wiki_PG stdio lab: 80/80 GUC calls for each, four independent pg_settings SQL values, stale/live divergence, bind-param negative control. **[historical lab review; raw receipts not retained]** | [review](../../reviews/mcp-toolbox-postgres/2026-11-04.md) |
| microsoft-skill-recorder | Pinned original scanStructuredPii detects synthetic email but not semantic Russian medical text; neutral case remains clean. | [review](../../reviews/microsoft-skill-recorder/2026-11-04.md) |
| novafabric | Pinned original NovaFabric forensic tool mock replay 20/20 with 40 captured calls, isolated byte-identical outputs, 48 independently checked artifacts and tampering controls. | [review](../../reviews/novafabric/2026-11-04.md) |
| open-steps | Pinned original start/stop hooks miss content-only edit of untracked file (stop 0) but detect edited tracked file (stop 2). | [review](../../reviews/open-steps/2026-11-04.md) |
| pgbot | Previously recorded original pgbot 0.9.0 disposable PG 18.3 test: 15k dead tuples, one blocked transaction, recovered vacuum and no-monitor partial-stat marker; 4 schema states validated. **[historical lab review; raw receipts not retained]** | [review](../../reviews/pgbot/2026-11-04.md) |
| rea | 48 independent synthetic PE32/PE32+ header/layout and rejection cases. | [review](../../reviews/reverse-engineer-anything/2026-11-05-pe-layout.md) |
| rrsi | Real pinned RRSI selector on 5 seeded synthetic train/validation/holdout sets: train-only chose memorizer 5/5; guarded selection locality 5/5. | [review](../../reviews/rrsi/2026-11-06-validation-ab.md) |
| simurg | Cross-process source hash/sketch/SimHash stability with 4 process seeds and independent numeric oracles. | [review](../../reviews/simurg/2026-11-07-hash-stability.md) |
| tencent-teamai-cli | Locally ported TeamAI CLI passed 40/40 offline synthetic distribution contract ops and a negative oracle mutant; minimal-home write-scope failed. | [review](../../reviews/tencent-teamai-cli/2026-11-06-distribution-ab.md) |
| toolgrad | Pinned source chain updater/API validator with 500/500 synthetic chain completions, 100 unreachable rejections and 10/10 zero-error-count false negatives. | [review](../../reviews/toolgrad/2026-11-06-chain-validation-ab.md) |
| understand-anything | Original pinned viewer leaks synthetic outside-root sentinel through graph-listed symlink with valid token. | [review](../../reviews/understand-anything/2026-11-08-mcp-head-security.md) |
| vercel-agent-desktop | Original Linux CLI, 12/12 isolated GTK toy UI positive and stale-ref negative cases; pinned core suite 1683 pass. | [review](../../reviews/vercel-agent-desktop/2026-11-05-wayland.md) |
| veriharness | Separate agent-config citation-locality mechanism on 1000 synthetic cases: false accept baseline 400 versus 200 with ±1-line locality check. | [review](../../reviews/veriharness/2026-11-06-citation-locality-ab.md) |
| warp-skill-doctor | Pinned collector session_matches_repo incorrectly accepts unrelated same-name path while rejecting unrelated other-name path. | [review](../../reviews/warp-skill-doctor/2026-11-04.md) |
| yahont-ce | Pinned original Yahont string_filtering maps a/b and ab to identical sanitized ID, but rejects empty and preserves doc_1. | [review](../../reviews/yahont-ce/2026-11-04.md) |
| youtube-skills | Pinned Markdown package, external transcript provider boundary and secret bootstrap verified by independent source oracle. | [review](../../reviews/youtube-skills/2026-11-07-provider-boundary.md) |
| zero-code | Pinned original 0-CODE JSONC helper passed independent synthetic fixture validation: 120 valid, 24 invalid cases, strict duplicate-key path and two rejected mutants. | [review](../../reviews/zero-code/2026-11-07-jsonc-countercheck.md) |

**Evidence hierarchy:** six original public helper contracts were re-executed twice inside network-denied bubblewrap, exact source and fixture SHA pinned ([machine receipts](../../data/results/research-portfolio/2026-11-09-residual-engineering-oracle.json)). Existing machine results for other bounded cases were independently read and validated against study-specific counts/negative controls, without unnecessary repeat model or GPU calls. For MCP Toolbox and pgbot only the detailed original dated lab reports and executable verifier survive; old disposable database JSON snapshots were not archived, so this pass does NOT claim a fresh independent rerun.

## ACCEPT_RESEARCH_ONLY: critical full-source references

These decisions concern specific methodology and limitations in previous legally accessed complete original papers or official technical write-ups. A credible evaluation protocol or threat-model reference is useful even when the claimed empirical improvement has not been reproduced. In this batch source downloads were not repeated merely to duplicate a pinned earlier PDF/HTML reading.

| Study | What remains useful as research only | Primary reviewed source |
| --- | --- | --- |
| agent-transfer-protocol | Signed, durable cross-domain agent address/envelope and delayed-verification queue as a transport design to test. | [source record](../../studies/agent-transfer-protocol.md) |
| agentic-self-awareness | Paired feasible versus blocked-task oracle must score correct action, refusal and changed-evidence re-evaluation separately. | [source record](../../studies/agentic-self-awareness.md) |
| anthropic-agent-automations | Per-source bookmarks, overlap, durable result-ledger and ambiguous-post state form a practical scheduled-agent design reference. | [source record](../../studies/anthropic-agent-automations.md) |
| behavior-beyond-text | Tool-attempt and realized side-effect oracles are separate from harmless-looking refusal text. | [source record](../../studies/behavior-beyond-text.md) |
| bird-rl | Trajectory-scoped database state and final-state isolation should be part of SQL-agent evaluation and training. | [source record](../../studies/bird-rl.md) |
| concordat | Typestate/session protocol prevents out-of-state tool operations in a finite workflow before side effects. | [source record](../../studies/concordat.md) |
| covert-assistance | Separate planner/developer/monitor permissions and validate actual effects rather than prompt-only warnings for covert delegation. | [source record](../../studies/covert-assistance.md) |
| cve-2026-82533-technical-disclosure | Host/loopback headers must not substitute authenticated control-plane authority; use only as defensive regression threat model. | [source record](../../studies/cve-2026-82533-technical-disclosure.md) |
| daedalus | Procedural memory earned from resettable exercises and frozen before inference is a testable learning design. | [source record](../../studies/daedalus.md) |
| geoagent | Artifact-named stage contracts and deterministic output-geometry invariants provide a workflow-evidence design reference. | [source record](../../studies/geoagent.md) |
| harnesssecurity-bench | Dual oracles for legitimate task utility and prohibited effect are a useful test-design instrument for agent harnesses. | [source record](../../studies/harnesssecurity-bench.md) |
| hyra-2 | Observation versus independently verified finding versus human-approved convention should be separate promotion states. | [source record](../../studies/hyra-2.md) |
| jevagentharness | Calibrated task-state decision routing must be judged on whole agent task outcomes, not isolated multiple-choice accuracy. | [source record](../../studies/jevagentharness.md) |
| kvset | Mattson stack-distance and Fenwick LRU working-set estimation are a research reference for physical KV capacity planning. | [source record](../../studies/kvset.md) |
| lago | Compare agent subtask reuse using an identical matched set of tasks and a frozen model budget, not an absolute single-method score. | [source record](../../studies/lago.md) |
| maadbench | Separate first-fault localization, propagation and final task outcome when evaluating agent anomaly detectors. | [source record](../../studies/maadbench.md) |
| matoi | Consequence prediction, current grant/authority and durable occurrence must remain distinct at each tool boundary. | [source record](../../studies/matoi.md) |
| memcomposer | Memory retrieval composition and ordering should be evaluated on complete task success under frozen memory banks. | [source record](../../studies/memcomposer.md) |
| memory-centric-continual-learning | Outcome-based tests should distinguish memory retention, changed-fact adaptation and transfer, not retrieval recall alone. | [source record](../../studies/memory-centric-continual-learning.md) |
| memscope | Use raw tool traces, current memory state and provider code to localize a memory repair in a reproducible isolated trial. | [source record](../../studies/memscope.md) |
| package-hallucination-rule-files | Treat repository rule files as untrusted for dependency approval; compare package/lockfile diffs to owner policy. | [source record](../../studies/package-hallucination-rule-files.md) |
| paper2agent | Source-to-tool research pipeline requires executable reference-code fixtures, exact reproduction checks and separate licensing. | [source record](../../studies/paper2agent.md) |
| poisoned-skills | Markdown skills/config are injection-capable low-trust inputs; verify provenance and effects rather than relying on instruction text. | [source record](../../studies/poisoned-skills.md) |
| polar | Compensatable/reversible action taxonomy is a cautionary advisory input, not proof of rollback or permission. | [source record](../../studies/polar.md) |
| realm | Query-triggered memory graph reconsolidation should be anchored to immutable source evidence to resist stale/poisoned facts. | [source record](../../studies/realm.md) |
| recap | Context-dependency graphs and source-preserving compaction can be studied without deleting authoritative historic events. | [source record](../../studies/recap.md) |
| red-teaming-auto-mode | Monitor transcripts, role boundaries, context compaction and delegated tasks are distinct surfaces for safe negative tests. | [source record](../../studies/red-teaming-auto-mode.md) |
| remory | Soft-token residual memory requires actor-state/gradient coupling and is research-only for a controlled own-weight inference stack. | [source record](../../studies/remory.md) |
| reva | History-indexed evidence views are only a research reference when attention traces from the exact generator are available. | [source record](../../studies/reva.md) |
| self-replicating-prompt-injections | Original public simulated-propagation disclosure is a threat model for isolating untrusted connector/file/compaction text from instructions. | [source record](../../studies/self-replicating-prompt-injections.md) |
| sequential-diagnosis-language-models | Sequential clinical differential/alternative-testing protocol is a clinical-evaluation reference requiring independent specialist safety review. | [source record](../../studies/sequential-diagnosis-language-models.md) |
| silent-cue-loss | Structured DOCX styling/color/highlight can carry task-significant requirements that plain-text extraction may omit. | [source record](../../studies/silent-cue-loss.md) |
| squidagent | Use a critical-path and overhead-aware DAG scheduler only when tasks have independently testable interfaces. | [source record](../../studies/squidagent.md) |
| statecomp | Decide when to compress active history while retaining immutable evidence; token savings alone are not safety or accuracy. | [source record](../../studies/statecomp.md) |
| swrouter | Multi-turn route evaluation should test actual context windows and model-eligibility boundaries, not last-turn similarity alone. | [source record](../../studies/swrouter.md) |
| transferable-tool-selection | Plan→retrieve→select is an evaluation reference, but exact full gold tool-set match is not end-to-end task success. | [source record](../../studies/transferable-tool-selection.md) |
| trust-region-injection | Untrusted document surfaces/placement should be explicit dimensions of defensive prompt-injection test coverage. | [source record](../../studies/trust-region-injection.md) |
| unreal-agent | The official long-form engineering article offers a bounded benchmark/price accounting checklist for autonomous task agents. | [source record](../../studies/unreal-agent-bk025.md) |
| unsloth-decision-model | Decision model LoRA recipe and calibration/evaluation API differences are a useful comparative implementation reference. | [source record](../../studies/unsloth-decision-model.md) |

Every individual research-only record also stores its critical confounder, author-only results status and separate project implementation gate. For original disclosures and official software write-ups the disposition covers the public source's threat-model or interface method, not an absent peer-reviewed empirical benchmark.

## BLOCKED: proved blockers, not paper rejection by guess

| Study | Observed source-level blocker | Evidence |
| --- | --- | --- |
| claude-swarm | WORKTREE_DATA_LOSS_AND_FALSE_COMPLETION: original built managers reproduced destructive same-feature retry, trusting unverified .done and bypassPermissions as default. | [review](../../portfolio/2026-11-07/claude-swarm-failure-injection.md) |
| hyperresearch | CITATION_AUTO_PASS_FALSE_SUPPORT: original source auto-accepted 48/60 authored unsupported temporal/scope/authorization/conjunction claims; negative source safety finding, not a real-world prevalence estimate. | [review](../../reviews/hyperresearch/2026-11-09-citation-adjudication.md) |

**Unblock only by evidence**, not by repeated STATUS_PENDING: a new pinned source must eliminate the reproduced failure and pass independently guarded counterexamples and a separate owner-approved target test. Previously positive functions in the same projects are not automatically rejected.

## NO_FIT: this registered portfolio, not all future machines

| Study | Why the current portfolio has no verified implementation target |
| --- | --- |
| kvtether | A message-lifecycle-aware KV eviction manager requires serving backend hooks, original KV pool and worker lifecycle signals; no registered current project documents both a compatible serving runtime and control seam. |
| random-attention | Prompt-preserving random reasoning-token KV eviction requires physical serving cache access and an instrumentable vLLM-like backend; none is documented among current 45 projects. |

[Independent current-profile gate](../../data/results/research-portfolio/2026-11-09-kv-backend-profile-gate.json) read all 45 current private PROJECT.md at a pinned project-registry HEAD, emitting only an aggregate hash and absence of a documented controllable physical KV serving backend. It is not a full inspection of every project's implementation and does not exclude future unregistered hardware/backend.

## Scope boundaries and project-fit honesty

- Previous 83/83 review provenance covered **documents**, not verified science. The ledger resolves that distinction with per-card terminal scope.
- Current project-assessment model explicitly records 506/3735 source–project pairs; 3229 pairs have no explicit decision. They are **NOT** inferred to be NO_FIT, nor does a project-profile match imply adoption.
- Full original scientific benchmark results were not automatically accepted; there was no fresh production/SQL/clinical data processing in this closeout.
- Clinical sequential diagnosis: the documented Wello experiment was an operational synthetic check, **not** a specialist-reviewed clinical validation or approval of deployed medical functionality.
- Special sources: Hyra article does not reveal its actual scheduler enforcement; Unreal Agent official article does not certify the video transcript or runtime; NovaFabric recorded tool interception does not sandbox all external effects.
- No confidential project-registry text/hashes, user tokens, models, source weights, or live production workloads were introduced in public research-hub.

**Reopening rule:** new source SHA, independently detected error, an actual project capability/target seam, or an explicitly authorized bounded held-out test. Do not rebuild an endless general REWORK queue on a settled study. The separate weekly discovery of NEW research is outside this 83-card closure.
