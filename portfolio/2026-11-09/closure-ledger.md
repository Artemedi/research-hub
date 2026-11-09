# Evidence-based closure ledger — first adjudication pass (83 cards)

Date: 2026-11-09. This is a finite evidence register, not 83 new reports.
This reconciliation reuses previous checks and includes the independent new Hyperresearch synthetic citation holdout; no model service, production action or source-card rewrite occurred.

Terminal: 25/83. Open: 58/83.

[Machine-readable 83-card ledger](../../data/results/research-portfolio/2026-11-09-closure-ledger.json) contains per-card SHA, review, full-source pointers, experiment records, project assessment coverage and precise unresolved gates. [Reproduction script](../../experiments/research-portfolio/2026-11-09-closure-ledger.py).

## Terminal bounded results

| Study | Verified property (not paper replication) | Existing dated evidence |
| --- | --- | --- |
| agent-error-dataset | Checkpoint-bound correction: 90 synthetic paired trials; 270 negative controls. | [review](../../reviews/agent-error-dataset/2026-11-08-checkpoint-replay-ab.md) |
| agent-mosaic | Independent synthetic oracle validated 270 composite-disclosure gate cases; output-bound gate released 90/90 allowed outputs without false disclosure release. | [review](../../reviews/agent-mosaic/2026-11-07-composite-gate.md) |
| agent-risk | Targeted replay versus live oracle on 200 synthetic finite episodes and assumption-breaking controls. | [review](../../reviews/agent-risk/2026-11-09-replay-assumptions.md) |
| alphaxiv-openresearch | 25 synthetic Git source-snapshot comparisons: original paper2project tree_hash vs source-derived git-archive proxy, checksum/dirty/metadata/corruption controls. | [review](../../reviews/alphaxiv-openresearch/2026-11-06-provenance-ab.md) |
| cera-moa | Independent synthetic oracle of cumulative-threshold routing rule over 10,000 scenarios. | [review](../../reviews/cera-moa/2026-11-08-routing-contract.md) |
| chartli | Independent XML and finite SVG geometry oracles on 16 original-source fixtures with bad-input controls. | [review](../../reviews/chartli/2026-11-07-svg-validation.md) |
| cursor-token-efficiency | Local deterministic 260-task context-character proxy reduces size by ~50% with oracle routing, but keyword routing misses 40/260; author 7% is unreplicated. | [review](../../reviews/cursor-token-efficiency/2026-11-07-council-vs-single.md) |
| drag | Synthetic RAG evidence guard passes sealed in-distribution fixtures yet fails under format shift and forged-evidence OOD stress. | [review](../../reviews/drag/2026-11-06-evidence-gate-ab.md) |
| dsh-creator-mode | Generated code client was verified in offline mock Cordis/React harness: 9/9 authored contract tests; 210 host/client suite tests passed separately. | [review](../../reviews/dsh-creator-mode/2026-11-06-external-generator-probe.md) |
| exactly-once-limbo | Pinned TelegramBot main() under synthetic transport: 900 fault cases/arm expose retry and at-most-once loss/duplicate tradeoff. | [review](../../reviews/exactly-once-limbo/2026-11-06-policy-ab.md) |
| gpt6-astra-skills-prompts | Five paired disposable coding tasks with real requested Astra model: both treatments 5/5 functional; reduced-context arm used 46.72% fewer input tokens and 13% less wall time. | [review](../../reviews/gpt6-astra-skills-prompts/2026-11-06-live-astra-ab.md) |
| harness2 | Pinned Harness2 selection-pool sanity check and shared 525-case synthetic selector-validation fixture: external guard picks locality candidate on 5/5 seeds. | [review](../../reviews/rrsi/2026-11-06-validation-ab.md) |
| htn-orchestrate | 43 pinned upstream targeted tests plus 30 synthetic static DAG checks and 20 surrogate resumes. | [review](../../reviews/htn-orchestrate/2026-11-08-paired-audit-followup.md) |
| inspektor-gadget | Pinned Inspektor Gadget trace_exec --filter.exec captured 200/200 positive and 0/25 negative synthetic rootless Podman events. | [review](../../reviews/inspektor-gadget/2026-11-06-privileged-podman-trace.md) |
| karpathy-autoresearch | Actual pinned Wiki_PG autoloop script on six toy Git worktrees: 3/3 domain-only runs missed heldout UI and 3/3 complete runs passed. | [review](../../reviews/karpathy-autoresearch/2026-11-06-loop-audit.md) |
| rea | 48 independent synthetic PE32/PE32+ header/layout and rejection cases. | [review](../../reviews/reverse-engineer-anything/2026-11-05-pe-layout.md) |
| rrsi | Real pinned RRSI selector on 5 seeded synthetic train/validation/holdout sets: train-only chose memorizer 5/5; guarded selection locality 5/5. | [review](../../reviews/rrsi/2026-11-06-validation-ab.md) |
| simurg | Cross-process source hash/sketch/SimHash stability with 4 process seeds and independent numeric oracles. | [review](../../reviews/simurg/2026-11-07-hash-stability.md) |
| tencent-teamai-cli | Locally ported TeamAI CLI passed 40/40 offline synthetic distribution contract ops and a negative oracle mutant; minimal-home write-scope failed. | [review](../../reviews/tencent-teamai-cli/2026-11-06-distribution-ab.md) |
| toolgrad | Pinned source chain updater/API validator with 500/500 synthetic chain completions, 100 unreachable rejections and 10/10 zero-error-count false negatives. | [review](../../reviews/toolgrad/2026-11-06-chain-validation-ab.md) |
| understand-anything | Original pinned viewer leaks synthetic outside-root sentinel through graph-listed symlink with valid token. | [review](../../reviews/understand-anything/2026-11-08-mcp-head-security.md) |
| vercel-agent-desktop | Original Linux CLI, 12/12 isolated GTK toy UI positive and stale-ref negative cases; pinned core suite 1683 pass. | [review](../../reviews/vercel-agent-desktop/2026-11-05-wayland.md) |
| veriharness | Separate agent-config citation-locality mechanism on 1000 synthetic cases: false accept baseline 400 versus 200 with ±1-line locality check. | [review](../../reviews/veriharness/2026-11-06-citation-locality-ab.md) |
| youtube-skills | Pinned Markdown package, external transcript provider boundary and secret bootstrap verified by independent source oracle. | [review](../../reviews/youtube-skills/2026-11-07-provider-boundary.md) |

All 24 ACCEPT_BOUNDED records refer only to explicitly measured narrow properties.
They do not endorse author-reported generalization, target-project benefit or deployment.

## Terminal source blocker (not a fictitious ACCEPT)

The [Hyperresearch source review](../../reviews/hyperresearch/2026-11-09-citation-adjudication.md) documents original triage_pairs granting 48/60 unsafe auto-support outcomes on new synthetic temporal/scope/authorization/conjunction claims. Source adoption is BLOCKED: CITATION_AUTO_PASS_FALSE_SUPPORT; the exact-only comparator prevents these auto-passes at the cost of paraphrase abstention. The source pin, alternatives and explicit unblock criterion are recorded per-card. Unrelated storage/retrieval behavior is not rejected.

## Unresolved evidence, not false closure

58 source cards remain OPEN_EVIDENCE_ADJUDICATION, not REWORK-by-default, BLOCKED-without-a-real-obstacle or speculative ACCEPT.
Existing canonical current assessments cover 506/3735 research–project pairs; 3229 pairs have no explicit decision. They are not inferred NO_FIT.
The previous 83/83 coverage report established review-document provenance, not scientific validity; this ledger explicitly preserves that boundary.

## Next finite gates

1. Source availability: warp-skill-doctor, hyra-2, unreal-agent, sequential-diagnosis-language-models. A BLOCKED result requires failed access attempts and an unblock criterion, not merely no local source.
2. Remaining full-primary cases: decide ACCEPT_RESEARCH_ONLY only after independent methodological review; otherwise use a bounded oracle or documented obstacle. The linked existing experiments must be adjudicated before any new execution.

No original study cards, generated source bodies, target project repositories, private registry files or production resources were modified.
