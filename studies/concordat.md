# Concordat — Typed Sessions for LLM Agents

[Структурированная запись и связи](../catalog/studies/concordat.md)

**Primary source:** https://arxiv.org/abs/2610.37461 ; [full PDF v2](https://arxiv.org/pdf/2610.37461v2).
**Original PDF SHA-256:** 40cdfc4cc918414bbb50485494003f45721a34dc0f1b2b773a5cdcbb5de18a31. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../portfolio/2026-10-27--2026-11-02/review.md). **Project applicability:** [explicit matrix](../portfolio/2026-10-27--2026-11-02/project-fit.md).
**Editorial valuation / effort:** 9/10 ; 5/10. **Proposed disposition:** P1_PROTOCOL_GATE_OFFLINE; no implementation approval.

## Methodology

Python typestate/session-type API с конечным автоматом: агенту видны только действия в текущем state; illegal tool calls блокируются до side effects. Включает handoff budgets и проверку subclass protocol refinement. Проверено на τ-bench airline 50 задач и дополнительных run sets под simulated customer pressure.

## Authors results

У baseline GPT-4.1 изменения без требуемого yes в 13 из 50 задач, у Haiku 5.5 — в 29 из 128 task-runs; Concordat не пропустил таких нарушений при заданном критерии. Разница task success статистически значима не была.

## Limitations

Сам gate и метрика approval используют одинаковую keyword-based проверку yes: нулевое нарушение по определению gate не доказывает корректного человеческого согласия. Нужен structured approval; generic finite state для open-ended задач сложен; provenance/state persistence требует отдельной оценки.

## Minimal offline experiment

50 synthetic inspect→propose→explicit structured approve→mutate→verify tasks. Prompt-only vs current authorization vs finite-state tool gate, независимый oracle на actual effect и owner consent, cost/latency.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
