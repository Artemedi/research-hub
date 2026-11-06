# Tencent TeamAI CLI

[Структурированная запись и связи](../catalog/studies/tencent-teamai-cli.md)

**Source type:** full technical open-source implementation and documentation, **not** a peer-reviewed paper. [Official source](https://github.com/Tencent/teamai-cli) • [full technical guide](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/docs/guide/distribution.md) • MIT.
**Upstream pin:** `Tencent/teamai-cli@7ed698998da8e446d8116c79ae58a9d5ff6ca016` (2026-11-04).
**Private fork pin:** `Artemedi/teamai-cli@5a3c371f692675b6e080a6554af5a3da0752fe5c` (2026-09-14).
**Telegram:** BK-002 / 08.09.2026. BK-004 is a **duplicate** of the same source; do not treat as another independent study.

**Primary claim:** Git-backed central ownership/distribution of skills, rules, agents, governance instructions, hooks and MCP settings. Under current upstream, a team may configure automatic session sync, pinned team revisions and declarative team scripts. This is an engineering feature claim, **not** evidence that it improves task quality in the owner's portfolio.

**Code evidence:** Tencent `src/pull.ts:165-260`, `src/post-pull.ts:57-115` and `src/codex-team-hooks.ts:198-245` are active delivery and trust boundaries. The owner's fork includes its own read-only `src/team-context.ts:146-189,264-316,342-389` DSH Team Context adapter, schema gate, local-skill-overrides, and authoritative governance injection.

**Current divergence:** common base `a3f0b6f6c5d314e0ba0d0a02de4c6e984fede55e`; fork is 13 commits ahead, 732 behind upstream. A **read-only** three-way merge rehearsal found 6 conflicting files including `src/pull.ts`, `src/source.ts`, `src/types.ts`, `src/resources/skills.ts`, two docs. No integration execution or fork rebase performed.

**Owner project fit:** `dsh-team-context` (canonical skills/governance provider), `agent-skills` (currently portable Codex skills installed with symlinks), `teamai-cli` (reference fork with owner-maintained adapter). Status `SOURCE_REVIEWED / PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE / LAB_NOT_RUN / NO_PRODUCTION_APPROVAL`. Other 42 project cards screened at profile level, no backlinks without stronger evidence.

**Main risks:** unconditional trust in canonical provider's published skills/governance in fork; upstream team scripts may execute on member machines, and Codex hooks may be rewritten. Project review, pinning and isolated workspace validation must precede adoption. For an existing single-machine workflow, extra sync complexity may be YAGNI.

**Full evidence:** [source review and 45-card mapping](../reviews/tencent-teamai-cli/2026-11-04.md) • [Telegram 65-item status ledger](../collections/telegram/README.md). No reproducible performance benchmark executed; a minimal isolated A/B plan is in the report.

## 2026-11-06 — изолированный A/B на локальном owner port

[Эксперимент с real CLI, Git+symlink baseline и независимым oracle](../reviews/tencent-teamai-cli/2026-11-06-distribution-ab.md) · [Python runner](../experiments/2026-11-06-bk002-teamai-distribution-ab.py) · [машинный результат](../data/results/tencent-teamai-cli/2026-11-06-distribution-ab.json).

Source **локальный, не опубликованный SHA** `teamai-cli-port-upstream@e5a0bb5901f4b1c78d7b1e28a2ba43e1cbe86db4` — это не upstream и не доступный GitHub commit. На isolated build/unit/E2E/typecheck/lint: 38/38 unit, 7/7 E2E, build/typecheck/lint PASS. Пять seeds × восемь этапов для каждой ветки; functional file-hash oracle 40/40 в обеих, B schema/governance gate PASS.

При выбранном минимальном только-.claude профиле B создал **35 разных путей за пределами допустимых `.claude/` / `.teamai/`** (файлы shell profile, AGENTS, Codex/OpenClaw/pi hooks и skill copies). Это поведение в disposable HOME, а не доказательство уязвимости; требование нулевых неожиданных записей **FAIL**. Wall p50 A 16.05 ms против B 753.773 ms, p95 A 17.936 против B 824.895 — feature-unequal synthetic CLI comparison, не token/LLM productivity benchmark. **Решение: `FUNCTIONAL_PASS / SCOPE_GATE_FAIL / NO_PRODUCTION_APPROVAL`**; нет внедрения и release proposal.
