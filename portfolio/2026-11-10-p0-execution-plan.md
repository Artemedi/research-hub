# P0 offline execution — read-only staged plan (2026-11-10)

## Objective and assumptions

Run the exact 16 P0 research–project pairs in data/project-fit/portfolio/2026-11-09-targeted-fit.json. A passing literature review (ACCEPT_BOUNDED or ACCEPT_RESEARCH_ONLY) is not proof of integration or benefit. No source code modification, target project deployment, networked model calls, SQL writes, private user data or real Telegram messages are authorized. Existing research status and all prior current_assessments are immutable for this pass.

Full per-pair acceptance requires source-pinned project copy, current baseline, treatment actually attached to the consumer, sealed dataset with independent oracle, comparative quality and cost measurements, and negative controls. A unit/subsystem simulation can pass an interface feasibility gate but cannot pass full product effect and is BLOCKED_FULL_AB until remaining proof is available. Some subexperiments may disprove a treatment (REJECT_TREATMENT) or identify no genuine feature delta. Do not change NO_FIT just because a runtime test is missing.

## Isolation and dependencies

Use temporary source snapshots from pinned git objects (git show/git archive) only, with source hash checks. Execute Python semantic probes in bubblewrap --unshare-net, read-only mounted inputs, writable temporary sandbox and fake credentials. TypeScript static/mocking probes may use the existing local offline toolchain in an isolated directory only. Never import target module top-level when it initializes network clients, secrets, services or writes. Do not run real PG/MSSQL, Gemini, Telegram, clinical data, eBPF on host, Podman image pulls, Playwright browser or public APIs as part of a forced experiment.

## Scope per P0

- A/B boundary probes (when runnable): exactly-once-limbo/TelegramBot (mocked remote commit/ack and local persisted state), agent-risk/agent-config (source-anchored exact-line evidence against independent oracle), agent-mosaic/dsh-team-context (source-scoped recall merge), drag/Wiki_PG (pure original RRF subroutine against frozen allowed-source oracle).
- Source and prerequisite audit: agent-mosaic/dsh-runtime, agent-risk/dsh-runtime, htn-orchestrate/dsh-runtime, novafabric/dsh-runtime, harnesssecurity-bench/dsh-runtime, mcp-toolbox-postgres/Wiki_PG, novafabric/sequential-rca, veriharness/agent-skills, veriharness/dsh-paper2agent, paper2agent/dsh-paper2agent, poisoned-skills/agent-skills, sequential-diagnosis-language-models/TrinMedicalBot. Run relevant existing offline unit suites where safe. If full A/B cannot be executed, label precisely BLOCKED and describe the missing runnable candidate, dataset or independent expert oracle.

## Artifact changes

Only change research-hub worktree experiment/p0-source-ab-20261110:

1. portfolio/2026-11-10-p0-execution-plan.md — this prework plan.
2. experiments/research-portfolio/p0-20261110/*.py (and optional .ts) — deterministic, reusable offline harness and independent tests.
3. data/results/research-portfolio/2026-11-10-p0-*.json — bounded quantitative receipts, hashes, reasons and any unavailable prerequisites.
4. portfolio/2026-11-10-p0-execution.md — 16-row outcome matrix, each source anchor, verdict and next action.
5. catalog/structure.json, generated README indexes, scripts/check.mjs, .github/workflows/integrity.yml, scripts/check.test.mjs only as needed to index and fail CI on stale/mutated report.

No target repo or private registry files. Prefer one self-contained script over speculative abstraction layers.

## Execution gates

Commit plan independently. For each completed experiment, archive frozen original source, verify source SHA, run baseline and variant over same input cases with independently constructed gold labels. Record pass/total, false positives, false negatives, duplicates, missing delivery, p50/p95 latencies and explicit scope. On any isolation failure, stop that experiment and mark BLOCKED, never silently fall back to host network. Mutation check: a forged ACCEPT with no source/baseline/variant/oracle must fail CI; receipt status must match result and report exactly.

Run node scripts/build-catalog.mjs, node scripts/check.mjs, existing node tests, Python AST/available lint, explicit new harness tests, git diff --check, then PR/CI. Merge only after green CI. Do not destroy the user's dirty local target worktrees; remove only our named clean temporary worktrees.

## Trade-offs

Synthetic offline measurements can establish a guard mechanism and its computational cost, but cannot establish live application impact. A lightweight source snippet and source hash is preferable to cloning several-gigabyte service repos for a pure deterministic function, but its scope is explicitly smaller. Rejecting a treatment with better duplicates but worse lost-delivery is a valid result, not a failed project.
