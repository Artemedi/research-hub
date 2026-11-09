#!/usr/bin/env python3
"""Evidence-gated 83-study closure inventory. Does not infer verdicts from PASS."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

# Each entry: tested proposition, reviewed source, independent machine result, limit.
BOUNDED = {
    "benchshield": (
        "Independent synthetic reward-lifecycle monitor on 100 constructed cases: 30 VIOLATION, 30 CLEAR, 40 ABSTAIN and tampered-log controls.",
        "reviews/benchshield/2026-11-04.md",
        "data/results/benchshield/2026-11-04.json",
        "Original BenchShield instrumentation not run; constructed labels, no security or DSH production effectiveness proof."),
    "decision-geometry-harness": (
        "Pinned DSH serializer schema-order paired provider tool-choice proxy: independent wire oracle 48/48 paired outcomes, mutation controls; native tool-use has a malformed/failed variant.",
        "reviews/decision-geometry-harness/2026-11-07-native-tool-ab.md",
        "data/results/decision-geometry-harness/2026-11-07-schema-ab-oracle.json",
        "Not original decision geometry paper replication or native DSH runtime/tool execution. Factorial effects, real workflow outcomes and provider equality not established."),
    "dsh-superagent-prototype": (
        "Pinned original in-memory core passed 15/15 isolated Ticket/Mandate/lifecycle contract cases and one independently introduced revoked-mandate mutant failed.",
        "reviews/dsh-superagent-prototype/2026-11-05.md",
        "data/results/dsh-superagent-prototype/2026-11-05.json",
        "Core only, fake Policy/Executor/Outbox; settingsPolicy, account adapters, full test suite and full-access permissions not safety validated."),
    "experienceindex": (
        "Independent Git SHA/href/source-pointer audit: 33/33 explicit related-review navigation cases, corrupt hash rejected; hit@5 baseline 32/33 vs link-augmented 33/33.",
        "reviews/experienceindex/2026-11-07.md",
        "data/results/experienceindex/2026-11-07-link-oracle.json",
        "Only literal link provenance and membership checked; no original ExperienceIndex method, BM25 ranking oracle or semantic relevance benchmark reproduced."),
    "goal-aware-dynamic-collaboration": (
        "35 pinned DSH task-graph validator cases and 35 external guarded synthetic cases matched separately encoded oracle, 70/70; mutant refused.",
        "reviews/goal-aware-dynamic-collaboration/2026-11-07.md",
        "data/results/goal-aware-dynamic-collaboration/2026-11-07-dag-oracle.json",
        "This is a DSH structural DAG guard, not the authors' GAD multi-agent planner or claimed task success; LLM workers not run."),
    "ipfire-fireperf": (
        "Original compiled fireperf 0.3.0 inside offline rootless Podman completed 12 isolated loopback runs, 240/240 connections; refused-port control detected.",
        "reviews/ipfire-fireperf/2026-11-04.md",
        "data/results/ipfire-fireperf/2026-11-04.json",
        "make check stopped after 23 PASS/1 SKIP; auto selected epoll, not io_uring. No WAN/firewall throughput, CPU-efficiency or DBA/SAN measurements."),
    "novafabric": (
        "Pinned original NovaFabric forensic tool mock replay 20/20 with 40 captured calls, isolated byte-identical outputs, 48 independently checked artifacts and tampering controls.",
        "reviews/novafabric/2026-11-04.md",
        "data/results/novafabric/2026-11-04.json",
        "Only explicit @record.tool interception; uninstrumented side effects remain live; untrusted signer identity and unsigned extra files not globally prevented."),
    "zero-code": (
        "Pinned original 0-CODE JSONC helper passed independent synthetic fixture validation: 120 valid, 24 invalid cases, strict duplicate-key path and two rejected mutants.",
        "reviews/zero-code/2026-11-07-jsonc-countercheck.md",
        "data/results/zero-code/2026-11-07-jsonc-oracle.json",
        "20 generated base objects with six syntactic variants; not supervisor permissions, full JSONC grammar or production config integration."),
    "agent-mosaic": (
        "Independent synthetic oracle validated 270 composite-disclosure gate cases; output-bound gate released 90/90 allowed outputs without false disclosure release.",
        "reviews/agent-mosaic/2026-11-07-composite-gate.md",
        "data/results/agent-mosaic/2026-11-07-composite-gate-oracle.json",
        "No original author benchmark or LLM experiment; strict renderer may abstain on valid free-form text and depends on claim provenance."),
    "alphaxiv-openresearch": (
        "25 synthetic Git source-snapshot comparisons: original paper2project tree_hash vs source-derived git-archive proxy, checksum/dirty/metadata/corruption controls.",
        "reviews/alphaxiv-openresearch/2026-11-06-provenance-ab.md",
        "data/results/alphaxiv-openresearch/2026-11-06-provenance-ab.json",
        "Proxy is NOT original OpenResearch SourceSnapshot::create; nonfeature-equivalent branches and no real orx run/daemon."),
    "cursor-token-efficiency": (
        "Local deterministic 260-task context-character proxy reduces size by ~50% with oracle routing, but keyword routing misses 40/260; author 7% is unreplicated.",
        "reviews/cursor-token-efficiency/2026-11-07-council-vs-single.md",
        "data/results/cursor-token-efficiency/2026-11-07-council-vs-single.json",
        "52 unique synthetic templates across 5 permutations, not 260 independent tasks; characters are not provider tokens."),
    "drag": (
        "Synthetic RAG evidence guard passes sealed in-distribution fixtures yet fails under format shift and forged-evidence OOD stress.",
        "reviews/drag/2026-11-06-evidence-gate-ab.md",
        "data/results/drag/2026-11-06-evidence-ood-stress.json",
        "OOD is posthoc diagnostic, not blind holdout; no real retrieval, provenance trust boundary, LLM, SQL data or production utility."),
    "dsh-creator-mode": (
        "Generated code client was verified in offline mock Cordis/React harness: 9/9 authored contract tests; 210 host/client suite tests passed separately.",
        "reviews/dsh-creator-mode/2026-11-06-external-generator-probe.md",
        "data/results/dsh-creator/2026-11-06-offline-poster-probe.json",
        "No real Creator Mode end-to-end execution, browser, original assets, pinned effective model or production install."),
    "gpt6-astra-skills-prompts": (
        "Five paired disposable coding tasks with real requested Astra model: both treatments 5/5 functional; reduced-context arm used 46.72% fewer input tokens and 13% less wall time.",
        "reviews/gpt6-astra-skills-prompts/2026-11-06-live-astra-ab.md",
        "data/results/gpt6-astra-skills-prompts/2026-11-06-scored-ab.json",
        "Very small paired sample; not official study replication, may differ on larger tasks; strict clean-workspace only 4/5 both arms."),
    "harness2": (
        "Pinned Harness2 selection-pool sanity check and shared 525-case synthetic selector-validation fixture: external guard picks locality candidate on 5/5 seeds.",
        "reviews/rrsi/2026-11-06-validation-ab.md",
        "data/results/rrsi/2026-11-06-validation-harness2-ab.json",
        "Primary mechanism tested is RRSI selector with Harness2 pool negative-control, NOT end-to-end Harness2 agent performance."),
    "karpathy-autoresearch": (
        "Actual pinned Wiki_PG autoloop script on six toy Git worktrees: 3/3 domain-only runs missed heldout UI and 3/3 complete runs passed.",
        "reviews/karpathy-autoresearch/2026-11-06-loop-audit.md",
        "data/results/karpathy-autoresearch/2026-11-06-wikipg-autoloop-oracle.json",
        "Scripted deterministic agent; not original video author or live LLM, 3 runs/arm, toy source trees only."),
    "rrsi": (
        "Real pinned RRSI selector on 5 seeded synthetic train/validation/holdout sets: train-only chose memorizer 5/5; guarded selection locality 5/5.",
        "reviews/rrsi/2026-11-06-validation-ab.md",
        "data/results/rrsi/2026-11-06-validation-harness2-ab.json",
        "Synthetic generated code gate; no original author benchmark, live LLM, real task holdout or actual cost gate."),
    "toolgrad": (
        "Pinned source chain updater/API validator with 500/500 synthetic chain completions, 100 unreachable rejections and 10/10 zero-error-count false negatives.",
        "reviews/toolgrad/2026-11-06-chain-validation-ab.md",
        "data/results/toolgrad/2026-11-06-chain-validation-ab.json",
        "Deterministic API proxy rather than Gemini/model, high source-validator false-negative class, not real project integration."),
    "veriharness": (
        "Separate agent-config citation-locality mechanism on 1000 synthetic cases: false accept baseline 400 versus 200 with ±1-line locality check.",
        "reviews/veriharness/2026-11-06-citation-locality-ab.md",
        "data/results/veriharness/2026-11-06-citation-locality-ab.json",
        "This executes agent-config, NOT original VeriHarness model or published benchmark; synthetic oracle not blindly human-labelled."),
    "exactly-once-limbo": (
        "Pinned TelegramBot main() under synthetic transport: 900 fault cases/arm expose retry and at-most-once loss/duplicate tradeoff.",
        "reviews/exactly-once-limbo/2026-11-06-policy-ab.md",
        "data/results/exactly-once-limbo/2026-11-06-telegrambot-policy-ab.json",
        "No real Telegram delivery, durable outbox, or actual fault frequencies; hypothetical idempotent server is not offered by Telegram."),
    "understand-anything": (
        "Original pinned viewer leaks synthetic outside-root sentinel through graph-listed symlink with valid token.",
        "reviews/understand-anything/2026-11-08-mcp-head-security.md",
        "data/results/understand-anything/2026-11-08-mcp-head-security.json",
        "Negative source security finding only; requires graph path plus token; not whole-app vulnerability assessment or production authorization."),
    "vercel-agent-desktop": (
        "Original Linux CLI, 12/12 isolated GTK toy UI positive and stale-ref negative cases; pinned core suite 1683 pass.",
        "reviews/vercel-agent-desktop/2026-11-05-wayland.md",
        "data/results/vercel-agent-desktop/2026-11-05.json",
        "Linux suite not fully green, 233 tests ignored; no broad toolkits, wrong-target safety or real project benefit."),
    "inspektor-gadget": (
        "Pinned Inspektor Gadget trace_exec --filter.exec captured 200/200 positive and 0/25 negative synthetic rootless Podman events.",
        "reviews/inspektor-gadget/2026-11-06-privileged-podman-trace.md",
        "data/results/inspektor-gadget/2026-11-06-podman-trace.json",
        "--comm variant captured 0/40; no kernel drop-rate or overhead proof, no actual PostgreSQL/AKUZ integration."),
    "tencent-teamai-cli": (
        "Locally ported TeamAI CLI passed 40/40 offline synthetic distribution contract ops and a negative oracle mutant; minimal-home write-scope failed.",
        "reviews/tencent-teamai-cli/2026-11-06-distribution-ab.md",
        "data/results/tencent-teamai-cli/2026-11-06-distribution-ab.json",
        "35 files outside intended minimal-home paths and unequal-feature A/B; not approved for deployment."),
    "agent-error-dataset": (
        "Checkpoint-bound correction: 90 synthetic paired trials; 270 negative controls.",
        "reviews/agent-error-dataset/2026-11-08-checkpoint-replay-ab.md",
        "data/results/agent-error-dataset/2026-11-08-independent-oracle.json",
        "No live agents, source dataset, causal RCA or real project recovery rate."),
    "agent-risk": (
        "Targeted replay versus live oracle on 200 synthetic finite episodes and assumption-breaking controls.",
        "reviews/agent-risk/2026-11-09-replay-assumptions.md",
        "data/results/agent-risk/2026-11-09-replay-boundary.json",
        "No original authors' model runs or real production gate approval."),
    "cera-moa": (
        "Independent synthetic oracle of cumulative-threshold routing rule over 10,000 scenarios.",
        "reviews/cera-moa/2026-11-08-routing-contract.md",
        "data/results/cera-moa/2026-11-08-independent-oracle.json",
        "No learned router, GPU quality/latency replication; one confidential project profile remains unassessed."),
    "chartli": (
        "Independent XML and finite SVG geometry oracles on 16 original-source fixtures with bad-input controls.",
        "reviews/chartli/2026-11-07-svg-validation.md",
        "data/results/chartli/2026-11-07-svg-oracle.json",
        "Five intentionally invalid fixtures fail; not browser rendering, numeric semantics or target benefit."),
    "htn-orchestrate": (
        "43 pinned upstream targeted tests plus 30 synthetic static DAG checks and 20 surrogate resumes.",
        "reviews/htn-orchestrate/2026-11-08-paired-audit-followup.md",
        "data/results/htn-orchestrate/2026-11-07-paired-audit.json",
        "No end-to-end HTN superiority proof; no held-out target project A/B."),
    "rea": (
        "48 independent synthetic PE32/PE32+ header/layout and rejection cases.",
        "reviews/reverse-engineer-anything/2026-11-05-pe-layout.md",
        "data/results/reverse-engineer-anything/2026-11-05.json",
        "No CLR-loadability, CIL reconstruction, arbitrary binary safety or target benefit."),
    "simurg": (
        "Cross-process source hash/sketch/SimHash stability with 4 process seeds and independent numeric oracles.",
        "reviews/simurg/2026-11-07-hash-stability.md",
        "data/results/simurg/2026-11-07-hash-stability.json",
        "Known AUROC ties and calibration/false-alarm issues remain unresolved for deployment."),
    "youtube-skills": (
        "Pinned Markdown package, external transcript provider boundary and secret bootstrap verified by independent source oracle.",
        "reviews/youtube-skills/2026-11-07-provider-boundary.md",
        "data/results/youtube-skills/2026-11-07-provider-boundary-oracle.json",
        "Provider API, cost, privacy and quality not tested; no keys or network calls."),
}
SPECIAL = {
    "unreal-agent": "Verify primary transcript or full original engineering source; video landing alone is insufficient.",
    "hyra-2": "Check available engineering article versus unavailable backend/model internals; record the precise source boundary.",
    "warp-skill-doctor": "Recover inspectable original implementation or document actual failed attempts and a concrete unblock condition.",
    "sequential-diagnosis-language-models": "Recheck pinned full paper and retained full-text evidence after source-fetch access failure.",
}
TERMINAL = {"ACCEPT_BOUNDED", "ACCEPT_RESEARCH_ONLY", "NO_FIT", "BLOCKED"}

# Current-portfolio verdict only: neither paper's original physical KV policy
# has a documented controlled serving target in any of the 45 project profiles.
NO_FIT = {
    "kvtether": (
        "A message-lifecycle-aware KV eviction manager requires serving backend hooks, original KV pool and worker lifecycle signals; no registered current project documents both a compatible serving runtime and control seam.",
        "reviews/kvtether/2026-11-05-full-text.md",
        "data/results/research-portfolio/2026-11-09-kv-backend-profile-gate.json",
        "New authorized project with source-verified KV lifecycle/eviction hooks, compatible model/runtime and an owner-approved measured lab, not generic mention of LLM, embeddings or context compression.",
    ),
    "random-attention": (
        "Prompt-preserving random reasoning-token KV eviction requires physical serving cache access and an instrumentable vLLM-like backend; none is documented among current 45 projects.",
        "studies/random-attention.md",
        "data/results/research-portfolio/2026-11-09-kv-backend-profile-gate.json",
        "New authorized project or backend code path exposing physical KV eviction controls; compare accuracy and serving throughput at fixed prompt, model, seeds and memory budget.",
    ),
}


# Separate evidence tier: six pinned original-source fixture replays, two historical
# read-only PostgreSQL/MCP labs with no preserved raw output receipts.
EVIDENCED_CODE = {
    "julia-1": (
        "Original Julia-1 display_probabilities on three authored positive/negative vectors, including .95 saturation and pruning.",
        "reviews/julia-1/2026-11-04.md",
        "experiments/bk026-julia/display_fixture.py",
        "Model weights, tensor routing and probability calibration not evaluated; no model inference."),
    "yahont-ce": (
        "Pinned original Yahont string_filtering maps a/b and ab to identical sanitized ID, but rejects empty and preserves doc_1.",
        "reviews/yahont-ce/2026-11-04.md",
        "experiments/bk053-yahont/id-fixture.py",
        "Not proof of actual index collision, tenant disclosure or ACL exploit; helper function only."),
    "open-steps": (
        "Pinned original start/stop hooks miss content-only edit of untracked file (stop 0) but detect edited tracked file (stop 2).",
        "reviews/open-steps/2026-11-04.md",
        "experiments/bk006-open-steps/fingerprint-fixture.sh",
        "One synthetic Git repo and hook pair; no real agents, multi-session race or baseline quality comparison."),
    "warp-skill-doctor": (
        "Pinned collector session_matches_repo incorrectly accepts unrelated same-name path while rejecting unrelated other-name path.",
        "reviews/warp-skill-doctor/2026-11-04.md",
        "experiments/bk019-skill-doctor/attribution-fixture.py",
        "No real private sessions or leak; 37 earlier upstream tests do not protect this attribution counterexample."),
    "local-knowledge-graph": (
        "Original strongest_path in synthetic directed graph selects reverse traversal 3→2; max-product path differs from highest geometric-mean path.",
        "reviews/local-knowledge-graph/2026-11-04.md",
        "experiments/bk024-local-knowledge-graph/paths-fixture.py",
        "No full model reasoning, real embedding corpus or graph retrieval; 21 upstream tests from earlier review not rerun."),
    "microsoft-skill-recorder": (
        "Pinned original scanStructuredPii detects synthetic email but not semantic Russian medical text; neutral case remains clean.",
        "reviews/microsoft-skill-recorder/2026-11-04.md",
        "experiments/bk022-skill-recorder/pii-fixture.mjs",
        "This only tests structured-PII detector, not OCR, full pre-send scan or Copilot egress; unrelated fail-open source branch remains a privacy concern."),
    "mcp-toolbox-postgres": (
        "Previously recorded original MCP Toolbox 1.15.0 versus Wiki_PG stdio lab: 80/80 GUC calls for each, four independent pg_settings SQL values, stale/live divergence, bind-param negative control.",
        "reviews/mcp-toolbox-postgres/2026-11-04.md",
        "experiments/2026-11-04-mcp-toolbox-wikipg-compare.py",
        "Original test report and reproducible script only: ephemeral PostgreSQL JSON receipts not retained, experiment NOT rerun this pass; no live target SQL integration."),
    "pgbot": (
        "Previously recorded original pgbot 0.9.0 disposable PG 18.3 test: 15k dead tuples, one blocked transaction, recovered vacuum and no-monitor partial-stat marker; 4 schema states validated.",
        "reviews/pgbot/2026-11-04.md",
        "experiments/2026-11-04-pgbot-verify.py",
        "Original lab report and verifier only: four generated JSON snapshots not retained, NOT rerun here. No PostgreSQL 15, production DBA accuracy or p95 claims."),
}

# Individually adjudicated primary-source methodological references only.
RESEARCH_ONLY = {
    'agent-transfer-protocol': ('Signed, durable cross-domain agent address/envelope and delayed-verification queue as a transport design to test.', 'Small 5/5 synthetic travel prototype, in-memory same-host +2.7 ms latency only; no deployed cross-org keys, revoke or retention proof.'),
    'agentic-self-awareness': ('Paired feasible versus blocked-task oracle must score correct action, refusal and changed-evidence re-evaluation separately.', '93.8% reported search-set strict SA is NOT held-out; feasible Retail solves fell to 9/32 under SA-only optimization, not proof of model introspection.'),
    'anthropic-agent-automations': ('Per-source bookmarks, overlap, durable result-ledger and ambiguous-post state form a practical scheduled-agent design reference.', 'Example policy/text is not atomic Slack+bookmark exactly-once; no live managed agent, distributed lock or user content policy tested.'),
    'behavior-beyond-text': ('Tool-attempt and realized side-effect oracles are separate from harmless-looking refusal text.', '2304 matched synthetic prompts and five open-weight models; unsafe attempted tool call is not verified side effect or a defect in our permission boundary.'),
    'bird-rl': ('Trajectory-scoped database state and final-state isolation should be part of SQL-agent evaluation and training.', 'Author 7B/14B gains measured against SQLite BIRD-CRITIC; state cloning, WAL/locking/IO differ radically for PostgreSQL and MSSQL.'),
    'concordat': ('Typestate/session protocol prevents out-of-state tool operations in a finite workflow before side effects.', "Approval was itself keyword 'yes' based; zero author-recorded violations cannot establish genuine owner consent or open-ended task safety."),
    'covert-assistance': ('Separate planner/developer/monitor permissions and validate actual effects rather than prompt-only warnings for covert delegation.', '6000 sandbox episodes and a separate matched 300-episode experiment are author-reported; models/secrets artificial, no current-agent failure established.'),
    'cve-2026-82533-technical-disclosure': ('Host/loopback headers must not substitute authenticated control-plane authority; use only as defensive regression threat model.', "OX-authored original security disclosure, not independent exploit reproduction or proof any current user's deployed version is vulnerable."),
    'daedalus': ('Procedural memory earned from resettable exercises and frozen before inference is a testable learning design.', 'Self-defined exercise success judged by LLM, not external oracle; the 3-success acceptance rule and API cost assume particular caching.'),
    'geoagent': ('Artifact-named stage contracts and deterministic output-geometry invariants provide a workflow-evidence design reference.', 'Single seismic 2-D data pipeline with niche Madagascar tooling; 6–11 min is not comparative agent/SWE/SQL success.'),
    'harnesssecurity-bench': ('Dual oracles for legitimate task utility and prohibited effect are a useful test-design instrument for agent harnesses.', 'Author 23 custom tasks/six harnesses, Docker/tool mock and model reviewer; listed DSH in 40-harness inventory is NOT proof current vulnerability.'),
    'hyra-2': ('Observation versus independently verified finding versus human-approved convention should be separate promotion states.', 'Full official 34k-character engineering article and results repo read, but no scheduler/model source, exact enforcement, replay or comparable A/B available.'),
    'jevagentharness': ('Calibrated task-state decision routing must be judged on whole agent task outcomes, not isolated multiple-choice accuracy.', 'Author English-agent/Gemini-biased tasks and threshold tuning; small-model GPU serving, non-inferiority margin and total cost not remeasured.'),
    'kvset': ('Mattson stack-distance and Fenwick LRU working-set estimation are a research reference for physical KV capacity planning.', '9-page primary PDF and author 10k/24k private serving traces, no target token-ID trace or original runtime calibration reproduced.'),
    'lago': ('Compare agent subtask reuse using an identical matched set of tasks and a frozen model budget, not an absolute single-method score.', '500-task absolute SWE score and 150 matched comparison have different denominators; model judge and runtime reuse not reproduced.'),
    'maadbench': ('Separate first-fault localization, propagation and final task outcome when evaluating agent anomaly detectors.', 'Author 5200 labeled traces and supervised AUROC are from constructed agent workflows; no transfer/false-alarm claim for current runtime.'),
    'matoi': ('Consequence prediction, current grant/authority and durable occurrence must remain distinct at each tool boundary.', "Preprint's 144 synthetic authored inputs/1440 cells and small cost gains have uncertain intervals; no arbitrary remote side effects or full mediation."),
    'memcomposer': ('Memory retrieval composition and ordering should be evaluated on complete task success under frozen memory banks.', 'Author GRPO and specific τ²-bench setups; shared static banks and retriever, costs of training/indexing and target utility unreplicated.'),
    'memory-centric-continual-learning': ('Outcome-based tests should distinguish memory retention, changed-fact adaptation and transfer, not retrieval recall alone.', 'Conceptual taxonomy/survey rather than a new controlled production benchmark; no demonstrated universal memory-policy advantage.'),
    'memscope': ('Use raw tool traces, current memory state and provider code to localize a memory repair in a reproducible isolated trial.', 'Author paired xBench/GAIA/ALFWorld with LLM judge and only 14 archived transitions; live self-modifying production memory unsafe.'),
    'package-hallucination-rule-files': ('Treat repository rule files as untrusted for dependency approval; compare package/lockfile diffs to owner policy.', 'Five selected packages and autonomous no-human-approval benchmark; attack-substitution frequencies not a universal compromise rate.'),
    'paper2agent': ('Source-to-tool research pipeline requires executable reference-code fixtures, exact reproduction checks and separate licensing.', 'Nature HTML Methods/Discussion read, supplementary PDF not separately analyzed; 74/100 paper agentification and 593/599 validated tools remain author-reported.'),
    'poisoned-skills': ('Markdown skills/config are injection-capable low-trust inputs; verify provenance and effects rather than relying on instruction text.', 'One LangChain prompt assembly, 270 forbidden QA prompts and seven open-weight models; ASR is text output, not tool privilege escalation.'),
    'polar': ('Compensatable/reversible action taxonomy is a cautionary advisory input, not proof of rollback or permission.', 'Only 8/18 model-domain comparisons improved in author report; reverse-search plan is not guaranteed to undo actual remote effects.'),
    'realm': ('Query-triggered memory graph reconsolidation should be anchored to immutable source evidence to resist stale/poisoned facts.', 'Author LoCoMo and LongMemEval small ablation gains, no long-running protected cross-session or real DBA correctness evidence.'),
    'recap': ('Context-dependency graphs and source-preserving compaction can be studied without deleting authoritative historic events.', 'Requires model attention or proxy; reported 94.5–95.6% cold-recovery latency reduction is derived in specific H100 model setup, not task speed.'),
    'red-teaming-auto-mode': ('Monitor transcripts, role boundaries, context compaction and delegated tasks are distinct surfaces for safe negative tests.', 'Full v1 PDF appendices reviewed, but simulation/LLM Dungeon Master and September snapshots do not show a current local vulnerability.'),
    'remory': ('Soft-token residual memory requires actor-state/gradient coupling and is research-only for a controlled own-weight inference stack.', 'Needs >1.5B trainable memory parameters and embeddings access; reported context compression not a drop-in closed API feature.'),
    'reva': ('History-indexed evidence views are only a research reference when attention traces from the exact generator are available.', 'Closed APIs generally do not expose necessary attention; offline score-store generation, index storage and model drift not measured.'),
    'self-replicating-prompt-injections': ('Original public simulated-propagation disclosure is a threat model for isolating untrusted connector/file/compaction text from instructions.', 'Full original disclosure described simulated tool calls only, NOT a reproduced self-propagating incident or arbitrary real-system impact.'),
    'sequential-diagnosis-language-models': ('Sequential clinical differential/alternative-testing protocol is a clinical-evaluation reference requiring independent specialist safety review.', 'Author Science/SDBench results not reproduced; 144 Wello synthetic operational calls prove HTTP delivery, NOT clinical correctness, and TrinMedicalBot deployment remains clinically unapproved.'),
    'silent-cue-loss': ('Structured DOCX styling/color/highlight can carry task-significant requirements that plain-text extraction may omit.', 'Author 76 policy DOCX plus 79 confirmatory docs and OOXML-derived labels; no validated benefit on our documents/OCR or every model.'),
    'squidagent': ('Use a critical-path and overhead-aware DAG scheduler only when tasks have independently testable interfaces.', 'Author nine tasks with one base model and LLM quality judge; projected 2.6x wall advantage cannot be extrapolated to IO-bound work.'),
    'statecomp': ('Decide when to compress active history while retaining immutable evidence; token savings alone are not safety or accuracy.', 'Requires hidden-state annotations/trained predictor; WorkBuddyBench reward +0.0039, Security reward declines; no cloud API equivalence.'),
    'swrouter': ('Multi-turn route evaluation should test actual context windows and model-eligibility boundaries, not last-turn similarity alone.', 'Author similarity threshold sensitivity extreme, model pool/caching and evaluation judge differ; cost and task win not locally replicated.'),
    'transferable-tool-selection': ('Plan→retrieve→select is an evaluation reference, but exact full gold tool-set match is not end-to-end task success.', 'Author ToolBench G3 2124 instructions and SFT/RL training; G2/TaskBench transfer not uniformly better; no current model routing validation.'),
    'trust-region-injection': ('Untrusted document surfaces/placement should be explicit dimensions of defensive prompt-injection test coverage.', 'Author 36 surfaces, 24 risk classes and testbeds; different placement affects observed model attempts, not proof current files are compromised.'),
    'unreal-agent': ('The official long-form engineering article offers a bounded benchmark/price accounting checklist for autonomous task agents.', 'Full ARTICLE was reviewed; video transcript was not verified and author dollars/pass rates, unreleased agent runtime and cost are NOT reproduced.'),
    'unsloth-decision-model': ('Decision model LoRA recipe and calibration/evaluation API differences are a useful comparative implementation reference.', 'Pinned public docs/notebook show inconsistent hyperparameters across recipes; no weights, GPU training, original score or licence-compliant target integration tested.'),
}

# Explicit terminal obstacle, independently demonstrated, with a concrete unblock gate.
BLOCKED = {
    "claude-swarm": (
        "Unsafe worker retry/completion decision in pinned original upstream WorktreeManager/WorkerManager.",
        "portfolio/2026-11-07/claude-swarm-failure-injection.md",
        "data/results/research-portfolio/2026-11-07-claude-swarm-failure-e2e.json",
        "WORKTREE_DATA_LOSS_AND_FALSE_COMPLETION: original built managers reproduced destructive same-feature retry, trusting unverified .done and bypassPermissions as default.",
        "A separate test-only repaired copy passed 19/19 simulated cases (portfolio/2026-11-07/claude-swarm-repair-ab.md); not a merged upstream security fix or safe production permission boundary.",
        "Pinned upstream must refuse dirty/active worktree destructive retry; gate completion on verified exit + source artifacts; remove bypassPermissions as implicit default; independently rerun negative controls and race/restart tests before scoped user approval."
    ),
    "hyperresearch": (
        "Automatic semantic citation acceptance via any six-word substring, pinned v0.13.0.",
        "reviews/hyperresearch/2026-11-09-citation-adjudication.md",
        "data/results/hyperresearch/2026-11-09-temporal-scope-oracle.json",
        "CITATION_AUTO_PASS_FALSE_SUPPORT: original source auto-accepted 48/60 authored unsupported temporal/scope/authorization/conjunction claims; negative source safety finding, not a real-world prevalence estimate.",
        "Tested exact-only comparator: 0/60 unsupported auto-pass, but only 12/24 supported auto-pass, requiring external/manual verification of paraphrases. Full downstream LLM verification not exercised.",
        "A new pinned upstream implementation must eliminate false auto-support on frozen hostile + independent natural held-out full-text claims and document exhaustive downstream coverage, positive paraphrase behavior, cost and target owner gate."
    ),
}

def read(root, p):
    return json.loads((root / p).read_text(encoding="utf-8"))

def sha(root, p):
    return hashlib.sha256((root / p).read_bytes()).hexdigest()

def validate_bounded(sid, x):
    if sid == "benchshield":
        assert x["cases"] == 100 and x["status"] == "PASS"
        assert x["not_original_BenchShield_implementation"] is True
        assert x["summary"]["verdict_VIOLATION"] == 30 and x["summary"]["verdict_ABSTAIN"] == 40
        assert x["summary"]["verdict_CLEAR"] == 30
        assert x["summary"]["permitted_false_accusations"] == 0
    elif sid == "decision-geometry-harness":
        assert x["scenario_count"] == 24 and x["replicates"] == 2
        assert x["status"] == "MODEL_ROUTING_SURROGATE_MEASURED"
        assert x["independent_wire_semantic_equivalence"] is True
        assert x["negative_tampered_schema_detected"] and x["negative_tampered_label_detected"]
        assert x["paired_comparison"]["both_correct"] == 48
        assert x["paired_comparison"]["eligible_paired_decisions"] == 48
    elif sid == "dsh-superagent-prototype":
        assert x["passed"] == len(x["checks"]) == 15
        assert x["scope"].startswith("original in-memory core")
    elif sid == "experienceindex":
        assert x["status"] == "PASS_BOUNDED_NAVIGATION_PROVENANCE"
        assert x["cases_validated"] == 33 and x["unexpected_cases"] == 0
        assert x["injected_wrong_source_hash_rejected"] is True
        assert x["navigation_hit_at5"] == {"baseline":32, "augmented":33}
    elif sid == "goal-aware-dynamic-collaboration":
        assert x["status"] == "PASS_SEPARATE_DECLARATIVE_ORACLE"
        assert x["graph_checked"] == x["workflow_checked"] == 35
        assert x["oracle_checks_passed"] == 70 and x["mutation_rejected"] is True
    elif sid == "ipfire-fireperf":
        assert x["status"] == "PASS" and x["asserted_total_connections"] == 240
        assert x["cases"] == len(x["runs"]) == 12
        assert x["refused_port_negative_control"]["failed"] == 1
        assert x["isolation_guard"]["no_default_ipv4_route"] is True
    elif sid == "novafabric":
        lab=x["lab"]; independent=x["independent_bundle_verification"]
        assert lab["status"] == independent["status"] == "PASS"
        assert lab["cases"] == lab["byte_identical_outputs"] == 20
        assert lab["captured_tool_calls"] == lab["mocked_tool_calls"] == 40
        assert lab["tool_body_executions_on_replay"] == 0
        assert independent["artifacts_verified"] == 48
        assert independent["pin_matched"] is False
        assert all(z.startswith("REJECTED") for z in independent["negative_controls"].values())
    elif sid == "zero-code":
        assert x["status"] == "PASS_BOUNDED_JSONC_BEHAVIOR"
        assert x["valid_cases_verified"] == 120 and x["invalid_cases_verified"] == 24
        assert x["mutations_rejected"] == 2
        assert x["strict_duplicate_key_route_verified"] is True
    elif sid == "agent-mosaic":
        assert x["independent_verification"] == "PASS" and x["rows_checked"] == 270
        assert x["oracle_counts"] == {"ALLOW":90, "DENY":120, "INCONCLUSIVE":60}
        gate=x["arms"]["output_bound_gate"]
        assert gate["actual_allow"] == 90 and gate["actual_inconclusive"] == 120
        assert gate.get("false_disclosure_release",0) == 0
    elif sid == "alphaxiv-openresearch":
        assert x["samples_per_arm"] == 25 and x["status"] == "SOURCE_DERIVED_GIT_ARCHIVE_AB_BASELINE_SOURCE_EXECUTED"
        assert all(x["controls_summary"][k] == 5 for k in (
            "archive_corruption_detected_B", "snapshot_available_without_source_B",
            "dirty_mutation_omitted_B", "metadata_stable_B", "missing_fulltext_rejected_external_gate"))
    elif sid == "cursor-token-efficiency":
        q=x["independent_gpt6"]["summary"]
        assert q["static"]["tasks"] == q["oracle"]["tasks"] == q["keyword"]["tasks"] == 260
        assert q["oracle"]["misses"] == 0 and q["keyword"]["misses"] == 40
        assert x["independent_gpt6"]["assertions"]["mutant_aggregate_rejected"]
        assert x["independent_gpt6"]["assertions"]["mutant_missing_set_rejected"]
    elif sid == "drag":
        assert x["status"] == "POSTHOC_STRESS_NOT_BLIND_HOLDOUT" and len(x["seeds"]) == 5
        base=x["mean_by_mutation_arm"]
        assert base["original"]["gate_follow"]["correct_abstention_rate_negative"] == 1.0
        assert base["format_shift"]["gate_follow"]["positive_answer_coverage"] == 0.0
        assert base["forged_observation"]["gate_follow"]["citation_precision"] == 0.0
    elif sid == "dsh-creator-mode":
        assert x["creator_mode_real_e2e"] is False
        lab=x["offline_container"]["result"]
        assert lab["verdict"] == "PASS" and lab["passes"] == 9 and all(lab["checks"].values())
        assert x["existing_native_tests"]["cordis_host_6_suites_pass"] == 102
        assert x["existing_native_tests"]["cordis_client_5_suites_pass"] == 108
    elif sid == "gpt6-astra-skills-prompts":
        assert x["summary"]["A"]["tasks"] == x["summary"]["B"]["tasks"] == 5
        assert x["summary"]["A"]["functional_pass"] == x["summary"]["B"]["functional_pass"] == 5
        assert x["comparisons"]["functional_pass_both"] is True
        assert x["comparisons"]["token_input_reduction_pct"] == 46.72
        assert x["is_an_official_study_replication"] is False
    elif sid in ("harness2","rrsi"):
        assert x["run_count"] == 5 and x["samples_per_run"] == {
            "training":40, "validation":25, "sealed_holdout":40}
        assert x["all_negative_controls_pass"] is True
        assert x["scores_mean_sealed_holdout"]["locality"] == 0.705
        assert x["scores_mean_sealed_holdout"]["memorizer"] == 0.455
        assert all(y["naive_selected"] == "memorizer" and
                   y["validation_guard_selected"] == "locality" for y in x["runs"])
    elif sid == "karpathy-autoresearch":
        assert x["runs"] == 6
        assert x["summary"]["domain-only"]["heldout_ui_passes"] == 0
        assert x["summary"]["complete"]["heldout_ui_passes"] == 3
        assert x["summary"]["complete"]["locked_oracle_tamper_survived"] == 0
    elif sid == "toolgrad":
        assert x["samples"] == 500 and x["status"] == "SOURCE_COMPONENTS_EXECUTED_WITH_PROXY_A_B"
        assert x["chain_first"]["verified"] == 500
        assert x["unreachable_test"]["query_first_rejected"] == 100
        assert x["negative_controls"]["false_negative_zero_error_count"] == 10
    elif sid == "veriharness":
        assert x["total_cases"] == 1000 and len(x["seeds"]) == 5
        assert x["mean_false_accept_rate"]["baseline"] == 0.666667
        assert x["mean_false_accept_rate"]["locality"] == 0.333333
    elif sid == "exactly-once-limbo":
        assert x["real_target_main_send_telegram_used"] is True and x["seed_count"] == 5
        a=x["totals"]["real_auto_retry"]
        b=x["totals"]["sidecar_pending_no_retry"]
        assert a["cases"] == b["cases"] == 900
        assert a["duplicate_cases"] == 600 and b["duplicate_cases"] == 100
        assert b["missing_cases"] == 200 and x["no_real_network_calls"] is True
    elif sid == "understand-anything":
        probe=x["synthetic_security_probe"]
        assert x["upstream_tests"]["passed"] == 32 and x["upstream_tests"]["failed"] == 0
        assert probe["result"] == "OBSERVED_SYMLINK_ESCAPE"
        assert probe["observed_http_status"] == 200 and probe["outside_file_exposed"] is True
        assert probe["bound_interface"] == "127.0.0.1" and x["production_approval"] is False
    elif sid == "vercel-agent-desktop":
        assert x["gui_cases_passed"] == 12 and x["all_gui_runs_passed"] is True
        assert len(x["gui_runs"]) == 3 and x["core_suite"] == "1683 passed; 0 failed"
    elif sid == "inspektor-gadget":
        assert len(x["trials"]) == 6 and x["trials"][0]["observed_events"] == 0
        runs=x["trials"][1:]
        assert all(y["expected_exec"] == y["observed_events"] == y["matched_comm"] == 40
                   and y["unexpected_negative"] == 0 and y["ig_exit"] == 0 for y in runs)
    elif sid == "tencent-teamai-cli":
        assert x["status"] == "FUNCTIONAL_PASS_SCOPE_GATE_FAIL" and x["cases_per_arm"] == 40
        check=x["validation"]
        assert check["B_correct_all"] and check["schema_fail_closed"] and check["local_guard_mutation_detected"]
        assert check["no_unexpected_home_file"] is False
        assert len(check["out_of_scope_files_in_minimal_claude_profile"]) == 35
    elif sid == "agent-error-dataset":
        assert x["independent_verification"] == "PASS" and x["trials_checked"] == 90
        assert x["negative_controls_blocked"] == 270 and x["false_accepts"] == 0
    elif sid == "agent-risk":
        assert x["status"] == "PASS" and x["scenario_count"] == 200
        assert x["counts"]["targeted_vs_live_harm_mismatches"] == 0
    elif sid == "cera-moa":
        assert x["status"] == "PASS" and x["verified_cases"] == 10000
        assert x["matches_experiment_digest"] is True
    elif sid == "chartli":
        assert x["total"] == 16 and x["well_formed_xml"] == 14
        assert x["finite_numeric_svg"] == 11 and all(x["mutation_checks"].values())
    elif sid == "htn-orchestrate":
        assert x["study_id"] == sid and x["upstream_source"]["sha"]
        assert x["synthetic_dag"]["passes"] == x["synthetic_dag"]["cases"] == 30
        assert x["synthetic_dag"]["resume_idempotence_pass"] == 20
    elif sid == "rea":
        assert x["passed"] == 48 and x["repetitions"] == 3
    elif sid == "simurg":
        assert x["status"] == "PASS_BOUNDED_CROSS_PROCESS_STABILITY"
        assert x["cross_process_checks_passed"] == 4 and len(x["pythonhashseed_cases"]) == 4
        assert x["unkeyed_external_b2sum_checks"] == 10
        assert all(x["negative_controls"].values())
    elif sid == "youtube-skills":
        assert x["independently_pinned_skills"] == 24
        assert x["auth_guide_sha_verified"] == 24 and x["synthetic_mutations_rejected"] == 2
        assert x["network_actions_run"] == 0

def next_gate(sid, full, experiments, missing):
    if sid in SPECIAL:
        return SPECIAL[sid]
    if experiments:
        return "Independently adjudicate recorded experiment scope, oracle, controls and author-vs-local distinction before terminal decision."
    if not full:
        return "Inspect complete pinned original article/code, methodological limitations and alternatives before a justified disposition."
    if missing:
        return "Use full review to adjudicate research-only value or bounded test; assess remaining project profiles without treating missing assessments as NO_FIT."
    return "Manually adjudicate review methods, limits and independent checks; choose supported research-only, bounded, or evidenced blocker."

def generate(root):
    x = read(root, "catalog/entities.json")
    old = read(root, "data/results/research-portfolio/2026-11-07-evidence-coverage-83.json")
    assert len(x["studies"]) == old["card_count"] == 83 and len(x["projects"]) == 45
    assert old["documentary_review_provenance_found"] == 83
    studies = {s["id"]: s for s in x["studies"]}
    reviews = {r["id"]: r for r in x["reviews"]}
    by_exp = defaultdict(list)
    for e in x["experiments"]:
        for sid in e["study_ids"]:
            by_exp[sid].append(e)
    assessments = {a["id"]: a for a in x["assessments"]}
    cur = defaultdict(dict)
    for a in x["current_assessments"]:
        assert a["project_id"] not in cur[a["study_id"]]
        cur[a["study_id"]][a["project_id"]] = assessments[a["assessment_id"]]
    provenance = {p["card"]: p for p in old["items"]}
    projects = {p["id"] for p in x["projects"]}
    output = []
    assert set(BOUNDED).issubset(studies)
    assert set(BLOCKED).issubset(studies) and not set(BLOCKED).intersection(BOUNDED)
    assert set(NO_FIT).issubset(studies) and not (set(NO_FIT) & (set(BOUNDED) | set(BLOCKED)))
    assert set(RESEARCH_ONLY).issubset(studies)
    assert not (set(RESEARCH_ONLY) & (set(BOUNDED) | set(BLOCKED) | set(NO_FIT)))
    assert set(EVIDENCED_CODE).issubset(studies)
    assert not (set(EVIDENCED_CODE) & (set(BOUNDED) | set(BLOCKED) | set(NO_FIT) | set(RESEARCH_ONLY)))
    for sid, study in sorted(studies.items()):
        p = study["card"]
        assert p in provenance
        document = provenance[p]["review_provenance"]
        current = reviews[study["current_review_id"]]
        assert sid in current["study_ids"]
        previous = [r for r in x["reviews"] if sid in r["study_ids"]]
        full = sorted({r["document"] for r in previous if r["source_coverage"] in (
            "FULL_TEXT_REVIEWED", "FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED",
            "FULL_PRIMARY_TECHNICAL_DISCLOSURE_READ")})
        explicit = cur[sid]
        missing = sorted(projects.difference(explicit))
        row = {
            "study_id": sid, "card": p, "card_sha256": sha(root, p),
            "kind": study["kind"], "primary_url": study["primary_url"],
            "review_document": document, "review_sha256": sha(root, document),
            "current_catalog_review": current["document"],
            "current_catalog_review_sha256": sha(root, current["document"]),
            "current_source_coverage_claim": current["source_coverage"],
            "previous_full_primary_review_documents": full,
            "existing_registered_experiments": [
                {"id": e["id"], "result": e["result"], "scope": e["scope"],
                 "artifacts": e["artifacts"]} for e in by_exp[sid]],
            "explicit_project_assessments": len(explicit),
            "project_assessment_decisions": dict(sorted(Counter(
                a["decision"] for a in explicit.values()).items())),
            "unassessed_project_count": len(missing),
            "unassessed_project_ids": missing,
            "author_results_independently_replicated_by_this_ledger": False,
            "production_approved": False,
        }
        if sid in BOUNDED:
            scope, reviewpath, evidencepath, limit = BOUNDED[sid]
            validate_bounded(sid, read(root, evidencepath))
            row.update({
                "closure_status": "ACCEPT_BOUNDED", "verified_scope": scope,
                "limits": limit, "evidence": [
                    {"path": f, "sha256": sha(root, f)}
                    for f in (reviewpath, evidencepath)],
                "deployment_gate": "Separate target-source seam, owned A/B, oracle, latency/cost/safety and explicit human approval.",
            })
        elif sid in EVIDENCED_CODE:
            scope, reviewpath, fixturepath, limits = EVIDENCED_CODE[sid]
            assert (root / reviewpath).is_file() and (root / fixturepath).is_file()
            repeatable = sid not in ("pgbot", "mcp-toolbox-postgres")
            documents = [reviewpath, fixturepath]
            if repeatable:
                evidencepath = "data/results/research-portfolio/2026-11-09-residual-engineering-oracle.json"
                oracle = read(root, evidencepath)
                assert oracle["status"] == "PASS_BOUNDED"
                recs = [rec for rec in oracle["records"] if rec["study"] == sid]
                assert len(recs) == 1 and recs[0]["passed"] is True
                assert recs[0]["fixture_sha256"] == sha(root, fixturepath)
                assert len(recs[0]["repetitions"]) == 2
                assert all(run["exit"] == 0 for run in recs[0]["repetitions"])
                assert recs[0]["repetitions"][0]["stdout_sha256"] == recs[0]["repetitions"][1]["stdout_sha256"]
                documents.append(evidencepath)
            else:
                reviewtext = (root / reviewpath).read_text(encoding="utf-8")
                if sid == "pgbot":
                    assert "pg_blocking_pids()" in reviewtext and "n_dead_tup=15000" in reviewtext
                    assert "Сами snapshots не включены" in reviewtext
                else:
                    assert "80/80" in reviewtext and "pg_catalog.pg_settings" in reviewtext
                    assert "BOTH_MCP_EXECUTED" in reviewtext
            row.update({
                "closure_status": "ACCEPT_BOUNDED", "verified_scope": scope,
                "limits": limits,
                "evidence_tier": (
                    "TWO_PINNED_PUBLIC_SOURCE_REPLAYS_WITH_INDEPENDENT_ORIGINAL_FIXTURE_SHA"
                    if repeatable else "HISTORIC_ORIGINAL_LAB_DOCUMENTED_ONLY_WITHOUT_RETAINED_RAW_RECEIPTS"),
                "independently_reexecuted_this_pass": repeatable,
                "production_approved": False,
                "deployment_gate": "Target owner-approved fresh held-out experiment and privilege/data-handling review; no auto promotion.",
                "evidence": [{"path": f, "sha256": sha(root, f)} for f in documents],
            })
        elif sid in RESEARCH_ONLY:
            methodological_reference, limits = RESEARCH_ONLY[sid]
            # A paper's full primary source was reviewed at an earlier pinned
            # date. This pass does not replay model experiments or claim that
            # all author-reported empirical gains are independently validated.
            if not full and sid not in ("self-replicating-prompt-injections", "unsloth-decision-model"):
                raise AssertionError(f"No adequate primary source evidence: {sid}")
            if sid in ("self-replicating-prompt-injections", "unsloth-decision-model"):
                assert study["kind"] in ("technical_disclosure", "engineering")
            assert len(methodological_reference) >= 50 and len(limits) >= 50
            doc_paths = list(dict.fromkeys([p, current["document"]] + full))
            assert all((root / doc).is_file() for doc in doc_paths)
            row.update({
                "closure_status": "ACCEPT_RESEARCH_ONLY",
                "verified_scope": "CRITICALLY_REVIEWED_PRIMARY_SOURCE_METHOD_AS_REFERENCE; NOT_AUTHOR_EMPIRICAL_REPLICATION",
                "methodological_reference": methodological_reference,
                "limits": limits,
                "author_results": "AUTHOR_REPORTED / NOT_REPRODUCED",
                "primary_source_full_text_prior_review": bool(full),
                "rechecked_source_bytes_in_this_pass": False,
                "deployment_gate": "No integration approval. Reopen only on new source claim, newly proven project seam or approved held-out experiment.",
                "evidence": [{"path": f, "sha256": sha(root, f)} for f in doc_paths],
            })
        elif sid in NO_FIT:
            decision, reviewpath, evidencepath, reopen = NO_FIT[sid]
            fit = read(root, evidencepath)
            assert fit["profiles_read"] == 45
            assert fit["documented_controllable_kv_backend_candidates"] == 0
            assert fit["decision"] == "NO_CURRENT_VERIFIED_FIT_FOR_PHYSICAL_KV_CACHE_CONTROL"
            assert sid in fit["evaluated_studies"]
            row.update({
                "closure_status": "NO_FIT", "verified_scope": "CURRENT_REGISTERED_PROJECT_PORTFOLIO_ONLY",
                "decision": decision, "reopen_condition": reopen,
                "limits": "Absence of a documented current capability, not proof of no possible future/self-hosted implementation or disproof of the paper's measured claims.",
                "evidence": [
                    {"path": f, "sha256": sha(root, f)} for f in (reviewpath, evidencepath)],
            })
        elif sid in BLOCKED:
            scope, reviewpath, oraclepath, obstacle, alternatives, unblock = BLOCKED[sid]
            oracle = read(root, oraclepath)
            if sid == "hyperresearch":
                assert oracle["input_sha256"] == sha(root, "data/results/hyperresearch/2026-11-09-temporal-scope-ab.json")
                assert oracle["status"] == "PASS" and oracle["validated_cases"] == 84
                assert oracle["counts"]["source_unsupported_auto_pass"] == 48
                assert oracle["counts"]["exact_only_unsupported_auto_pass"] == 0
                assert oracle["mutated_gold_rejected"] and oracle["mutated_verdict_rejected"]
                assert oracle["mutated_fixture_rejected"]
            elif sid == "claude-swarm":
                assert oracle["tests_total"] == oracle["matched_oracle"] == 15
                assert not oracle["unexpected_results"]
                assert oracle["upstream_pin"] == "31f19199bf3557cda4860231186a06b72c8edb94"
                assert any("Retry" in z for z in oracle["risks"])
                assert any(".done" in z for z in oracle["risks"])
            row.update({
                "closure_status": "BLOCKED", "verified_scope": scope,
                "blocker": obstacle, "attempted_alternative": alternatives,
                "unblock_condition": unblock,
                "limits": "Terminal rejection of the particular proved unsafe original-source behavior; other library components have not been globally rejected.",
                "evidence": [
                    {"path": f, "sha256": sha(root, f)}
                    for f in (reviewpath, oraclepath)],
                "production_approved": False,
            })
        else:
            row.update({
                "closure_status": "OPEN_EVIDENCE_ADJUDICATION", "verified_scope": None,
                "limits": "Document provenance does not prove scientific replication or current project fit.",
                "evidence": [],
                "next_evidence_gate": next_gate(sid, bool(full), by_exp[sid], missing),
            })
        output.append(row)
    c = Counter(row["closure_status"] for row in output)
    summary = {"total": 83, "terminal": sum(c[k] for k in TERMINAL),
               "open": c["OPEN_EVIDENCE_ADJUDICATION"],
               "by_status": dict(sorted(c.items())),
               "explicit_project_pairs": sum(v["explicit_project_assessments"] for v in output),
               "unassessed_project_pairs": sum(v["unassessed_project_count"] for v in output)}
    assert summary["terminal"] + summary["open"] == 83
    assert summary["explicit_project_pairs"] + summary["unassessed_project_pairs"] == 3735
    return {
        "date": "2026-11-09", "basis_repo": "Artemedi/research-hub",
        "basis_entities_sha256": sha(root, "catalog/entities.json"),
        "prior_provenance_sha256": sha(root, "data/results/research-portfolio/2026-11-07-evidence-coverage-83.json"),
        "study_status_note": "Terminal acceptance is manually bounded, never inferred from upstream PASS or the existence of a document.",
        "project_status_note": "Unassessed is not NO_FIT; assessments refer to recorded project snapshots, not automatically current HEAD.",
        "summary": summary, "studies": output}

def report(v):
    """Publish exact dispositions with the evidence and limits, not an ACCEPT tally."""
    summ = v["summary"]
    c = summ["by_status"]
    lines = [
        "# Research portfolio: evidence-qualified terminal dispositions for 83 cards",
        "",
        "**Date:** 2026-11-09. **Result:** {}/83 terminal research dispositions, {} open.".format(
            summ["terminal"], summ["open"]),
        "",
        "| Disposition | Cards | What is actually closed |",
        "| --- | ---: | --- |",
        "| ACCEPT_BOUNDED | {} | Only the explicitly tested engineering or synthetic proposition; not original whole-paper replication |".format(c.get("ACCEPT_BOUNDED", 0)),
        "| ACCEPT_RESEARCH_ONLY | {} | 37 prior full-primary method reviews plus 2 narrower official engineering/disclosure references; no author gains reproduced |".format(c.get("ACCEPT_RESEARCH_ONLY", 0)),
        "| BLOCKED | {} | Pinpointed original-source unsafe adoption path, actual counterexample, tested alternative and unblock rule |".format(c.get("BLOCKED", 0)),
        "| NO_FIT | {} | Concrete method needs a capability absent from currently documented 45-project portfolio; reopen on source/capability change |".format(c.get("NO_FIT", 0)),
        "",
        "The [83-card machine ledger](../../data/results/research-portfolio/2026-11-09-closure-ledger.json) "
        "contains original card and review SHA-256, primary URL, previous full-source provenance, "
        "per-study method/obstacle, negative evidence, limits and reopening conditions. "
        "The [reproduction script](../../experiments/research-portfolio/2026-11-09-closure-ledger.py) "
        "deliberately does not infer acceptance from a generic PASS, document count or project-name overlap.",
        "",
        "**Critical distinction:** terminal portfolio research disposition is NOT scientific "
        "replication and is NOT project implementation approval. The authors' experimental "
        "scores remain AUTHOR_REPORTED/NOT_REPRODUCED unless independently scoped evidence "
        "says exactly otherwise. Production approval is false for all 83.",
        "",
        "## ACCEPT_BOUNDED: measured narrow properties",
        "",
        "| Study | Accepted measurable property or negative finding | Evidence |",
        "| --- | --- | --- |",
    ]
    for r in v["studies"]:
        if r["closure_status"] != "ACCEPT_BOUNDED":
            continue
        rev = r["evidence"][0]["path"]
        caveat = ""
        if r.get("evidence_tier", "") == "HISTORIC_ORIGINAL_LAB_DOCUMENTED_ONLY_WITHOUT_RETAINED_RAW_RECEIPTS":
            caveat = " **[historical lab review; raw receipts not retained]**"
        lines.append("| {} | {}{} | [review](../../{}) |".format(
            r["study_id"], r["verified_scope"], caveat, rev))
    lines += [
        "",
        "**Evidence hierarchy:** six original public helper contracts were re-executed "
        "twice inside network-denied bubblewrap, exact source and fixture SHA pinned "
        "([machine receipts](../../data/results/research-portfolio/2026-11-09-residual-engineering-oracle.json)). "
        "Existing machine results for other bounded cases were independently read and "
        "validated against study-specific counts/negative controls, without unnecessary "
        "repeat model or GPU calls. For MCP Toolbox and pgbot only the detailed original "
        "dated lab reports and executable verifier survive; old disposable database JSON "
        "snapshots were not archived, so this pass does NOT claim a fresh independent rerun.",
        "",
        "## ACCEPT_RESEARCH_ONLY: critical full-source references",
        "",
        "These decisions concern specific methodology and limitations in previous legally "
        "accessed complete original papers or official technical write-ups. A credible "
        "evaluation protocol or threat-model reference is useful even when the claimed "
        "empirical improvement has not been reproduced. In this batch source downloads "
        "were not repeated merely to duplicate a pinned earlier PDF/HTML reading.",
        "",
        "| Study | What remains useful as research only | Primary reviewed source |",
        "| --- | --- | --- |",
    ]
    for r in v["studies"]:
        if r["closure_status"] == "ACCEPT_RESEARCH_ONLY":
            f = r["evidence"][0]["path"]
            lines.append("| {} | {} | [source record](../../{}) |".format(
                r["study_id"], r["methodological_reference"], f))
    lines += [
        "",
        "Every individual research-only record also stores its critical confounder, "
        "author-only results status and separate project implementation gate. "
        "For original disclosures and official software write-ups the disposition "
        "covers the public source's threat-model or interface method, not an absent "
        "peer-reviewed empirical benchmark.",
        "",
        "## BLOCKED: proved blockers, not paper rejection by guess",
        "",
        "| Study | Observed source-level blocker | Evidence |",
        "| --- | --- | --- |",
    ]
    for r in v["studies"]:
        if r["closure_status"] == "BLOCKED":
            f = r["evidence"][0]["path"]
            lines.append("| {} | {} | [review](../../{}) |".format(
                r["study_id"], r["blocker"], f))
    lines += [
        "",
        "**Unblock only by evidence**, not by repeated STATUS_PENDING: a new pinned "
        "source must eliminate the reproduced failure and pass independently guarded "
        "counterexamples and a separate owner-approved target test. Previously positive "
        "functions in the same projects are not automatically rejected.",
        "",
        "## NO_FIT: this registered portfolio, not all future machines",
        "",
        "| Study | Why the current portfolio has no verified implementation target |",
        "| --- | --- |",
    ]
    for r in v["studies"]:
        if r["closure_status"] == "NO_FIT":
            lines.append("| {} | {} |".format(r["study_id"], r["decision"]))
    lines += [
        "",
        "[Independent current-profile gate](../../data/results/research-portfolio/2026-11-09-kv-backend-profile-gate.json) "
        "read all 45 current private PROJECT.md at a pinned project-registry HEAD, "
        "emitting only an aggregate hash and absence of a documented controllable "
        "physical KV serving backend. It is not a full inspection of every project's "
        "implementation and does not exclude future unregistered hardware/backend.",
        "",
        "## Scope boundaries and project-fit honesty",
        "",
        "- Previous 83/83 review provenance covered **documents**, not verified science. "
        "The ledger resolves that distinction with per-card terminal scope.",
        "- Current project-assessment model explicitly records {}/3735 source–project "
        "pairs; {} pairs have no explicit decision. They are **NOT** inferred to "
        "be NO_FIT, nor does a project-profile match imply adoption.".format(
            summ["explicit_project_pairs"], summ["unassessed_project_pairs"]),
        "- Full original scientific benchmark results were not automatically accepted; "
        "there was no fresh production/SQL/clinical data processing in this closeout.",
        "- Clinical sequential diagnosis: the documented Wello experiment was an "
        "operational synthetic check, **not** a specialist-reviewed clinical validation "
        "or approval of deployed medical functionality.",
        "- Special sources: Hyra article does not reveal its actual scheduler enforcement; "
        "Unreal Agent official article does not certify the video transcript or runtime; "
        "NovaFabric recorded tool interception does not sandbox all external effects.",
        "- No confidential project-registry text/hashes, user tokens, models, source "
        "weights, or live production workloads were introduced in public research-hub.",
        "",
        "**Reopening rule:** new source SHA, independently detected error, an actual "
        "project capability/target seam, or an explicitly authorized bounded held-out "
        "test. Do not rebuild an endless general REWORK queue on a settled study. "
        "The separate weekly discovery of NEW research is outside this 83-card closure.",
        "",
    ]
    return "\n".join(lines)

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = a.parse_args()
    root = args.root.resolve()
    res = generate(root)
    out = root / "data/results/research-portfolio/2026-11-09-closure-ledger.json"
    md = root / "portfolio/2026-11-09/closure-ledger.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    md.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md.write_text(report(res), encoding="utf-8")
    print(json.dumps(res["summary"], indent=2))

if __name__ == "__main__":
    main()
