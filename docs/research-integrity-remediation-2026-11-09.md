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
5. **paper2agent-index.** Fix two missing dsh-paper2agent/docs/product references, mark stale source commit snapshots, avoid modifying unsupported measurements. Validate references and index consistency, commit and verify in separate repo.
6. **dsh-paper2agent.** Inspect published HEAD against local 22 dirty/untracked paths; preserve user work. Produce concrete evidence-based completion and reproducibility report. Commit only an independently verifiable, scoped finished slice if safe; otherwise explicitly mark remaining blocked and do not synthesize a clean release.

## Trade-offs and safeguards

Use a single canonical disposition JSON read when generating catalog views: trivial CPU/memory/IO overhead and one file dependency, versus avoiding drift from 83 duplicated manual statuses. A full 83 x 45 integration review is separate and cannot be inferred from lexical project descriptions. No status promotion without a scoped oracle. Each step gets its own diff, tests, commit/PR, CI and user-facing evidence or an explicit blocker.

## Verified execution log

- **Step 1 — completed:** [PR #4](https://github.com/Artemedi/research-hub/pull/4), merged at 0a9950f; GitHub check succeeded. The independent evidence receipt is now checked by CI and the normal integrity command.
- **Step 2 — completed:** [PR #5](https://github.com/Artemedi/research-hub/pull/5), merged at 50f70ad; 83 generated study pages display scoped decision/evidence from one canonical ledger and preserve scientific review history.
- **Step 3 — completed:** [PR #6](https://github.com/Artemedi/research-hub/pull/6), merged at 1d0d840; two unsupported KV-cache NO_FIT claims retracted after three negative-control failures. Current honest result: 81/83 terminal, 2 open, source-level project review still required.
- **Step 4 — documentation:** correct historical card counts and clarify distinct research, review, fit and implementation states.
- **Step 5 — corrected assumption:** two dsh-paper2agent product docs exist in upstream origin/main 6d82a42; the local checkout is behind 22 commits. Preserve valid references and audit index revisions for staleness instead of deleting links.
