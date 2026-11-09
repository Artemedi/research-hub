# Research repositories: logic and structural integrity remediation (2026-11-09)

Scope: research-hub and paper2agent-index; read-only review of project-registry, deepseek-harness, and currently dirty dsh-paper2agent. Use dedicated branches, preserve unrelated state, commit and verify each step before the next. The 83-card closure ledger is not scientific replication or project deployment approval.

## Assumptions and source of truth

- Study/source/version/project fit: research-hub/catalog/entities.json. Historical study body files and archive/dsh/ remain immutable.
- Terminal research disposition: data/results/research-portfolio/2026-11-09-closure-ledger.json, a separate scoped adjudication. Do not infer this from current_review_id, source_coverage, generic PASS or experiment count. Generated pages should link/display this canonical status, without maintaining a second editable disposition.
- project-registry PROJECT.md is the project capability profile at pinned commit. Missing keywords cannot conclusively prove NO_FIT. Private profile content stays private.
- paper2agent-index is a derived, potentially stale cache, not proof of a current integration seam.
- dsh-paper2agent has pre-existing uncommitted/untracked experimental code. Do not stash, commit, delete, or rewrite it without careful reconciliation. No production/DB/model invocations for documentation maintenance.

## Ordered steps and acceptance

1. **CI failure gate.** Edit .github/workflows/integrity.yml, the existing independent ledger verifier and its targeted regression. Pull requests must fail when a terminal decision changes, evidence SHA changes, a study is removed or a generated catalogue view is stale. Run repository integrity, tests, diff check and CI; publish independent commit.
2. **Catalogue and evidence alignment.** Edit scripts/build-catalog.mjs, scripts/entity-model.mjs only if necessary, unit tests, generated catalog/studies pages. Show explicit terminal study disposition, source evidence and limitations. Preserve historical scientific current_review_id and project fit. Avoid manually duplicating 83 editable statuses. Regenerate and verify.
3. **KV NO_FIT correction.** Reassess kvtether and random-attention. The old kv-backend-profile-gate.py regex is not sufficient negative evidence. Add synthetic negative controls for llama.cpp, TensorRT-LLM and observational false-positive; clarify missing per-project evaluation. Change dispositions to evidenced unknown/nonterminal where warranted; correct totals without pretending closure.
4. **Documentation.** AGENTS.md and docs/data-model.md: 81 -> 83; clarify distinct source, reviewed evidence, terminal disposition, and project applicability. Avoid unrelated formatting changes.
5. **paper2agent-index.** Check alleged missing product docs against published origin/main before changing references; pin valid URLs and flag genuinely stale source snapshots, without altering historical measurements. Validate structure and links in its own repository.
6. **dsh-paper2agent.** Inspect published HEAD against local 22 dirty/untracked paths; preserve user work. Produce concrete evidence-based completion and reproducibility report. Commit only an independently verifiable, scoped finished slice if safe; otherwise explicitly mark remaining blocked and do not synthesize a clean release.

## Trade-offs and safeguards

Use a single canonical disposition JSON read when generating catalog views: trivial CPU/memory/IO overhead and one file dependency, versus avoiding drift from 83 duplicated manual statuses. A full 83 x 45 integration review is separate and cannot be inferred from lexical project descriptions. No status promotion without a scoped oracle. Each step gets its own diff, tests, commit/PR, CI and user-facing evidence or an explicit blocker.

## Verified execution log

- **Step 1 — completed:** [PR #4](https://github.com/Artemedi/research-hub/pull/4), merged at 0a9950f; GitHub check succeeded. The independent evidence receipt is now checked by CI and the normal integrity command.
- **Step 2 — completed:** [PR #5](https://github.com/Artemedi/research-hub/pull/5), merged at 50f70ad; 83 generated study pages display scoped decision/evidence from one canonical ledger and preserve scientific review history.
- **Step 3 — completed:** [PR #6](https://github.com/Artemedi/research-hub/pull/6), merged at 1d0d840; two unsupported KV-cache NO_FIT claims retracted after three negative-control failures. Current honest result: 81/83 terminal, 2 open, source-level project review still required.
- **Step 4 — completed:** [PR #7](https://github.com/Artemedi/research-hub/pull/7), merged at 28852911; counts 81 -> 83 and distinct evidence/review/fit/adoption contracts. [CI success](https://github.com/Artemedi/research-hub/actions/runs/42604240381).
- **Step 5 — completed:** [paper2agent-index PR #1](https://github.com/Artemedi/paper2agent-index/pull/1), merged at ac32f87; remote source commit 6d82a42 contains both product docs. Links pinned, three source snapshots marked stale, readiness unchanged. Schema, Markdown links and exact source revisions checked locally. That repository has no CI workflow.
- **Step 6 — published clean-checkout test repair:** [dsh-paper2agent PR #2](https://github.com/Artemedi/dsh-paper2agent/pull/2), merged at cbcb1c0; [main CI SUCCESS](https://github.com/Artemedi/dsh-paper2agent/actions/runs/42605618955). Original clean remote 6d82a42 initially had 105/113 tests pass with 8 fixture setup errors from missing ignored upstream LICENSE; the new isolated synthetic license fixture allows 115 tests with 0 failures and 2 explicit skips (real upstream checkout + rootless Podman E2E). Offline paper2project selftest PASS. Changes only in two test files and a new CI workflow, not production product code.

## Outstanding gates after this execution

1. **81/83 terminal research dispositions, two honest OPEN records.** KVTether and Random Attention still need explicit project-by-project, source-level verification of actual physical KV-cache control and an independently measured bounded experiment before any new NO_FIT or ACCEPT.
2. **The local dsh-paper2agent worktree is intentionally not rebased, stashed or reset.** It still has 22 user-owned modified/untracked paths and is behind current published main by 24 commits. Its working-tree content may conflict with remotely published source: reconcile files and tests explicitly before adopting remote main there. The published clean checkout is independently validated; this does not qualify the unmerged local experimental changes.
3. **deepseek-harness local dirty files and all project-registry private source bodies were untouched.** Research-hub archive history and original study card contents remain intact. 506 explicit research-to-project decisions are preserved; absence of an assessment is not NO_FIT.

The remediation changes are independently published and traceable, but these unresolved scientific/project-fit and local-worktree gates are not presented as completed implementations.
