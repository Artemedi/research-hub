# RRSI — Regularized Recursive Self-Improvement of Agent Harnesses

**Источник исследования:** [полный HTML v3, arXiv 2609.24972](https://arxiv.org/html/2609.24972v3). **Проверенный код:** [google-research/rrsi@be50316e](https://github.com/google-research/rrsi/tree/be50316e1db05914068a973f322770ef08ed7ba1), Apache-2.0.
**Эксперимент:** [2026-11-04 — RRSI / Harness² overfitting lab](../reports/2026-11-04-rrsi-harness2-overfit-lab.md), [воспроизводимый offline-скрипт](../experiments/2026-11-04-rrsi-harness2-selector-smoke.py).
**Статус:** `SELECTOR_MECHANICS_VERIFIED / NO_REAL_AGENT_BENCHMARK / NO_PRODUCTION_APPROVAL`.

## Подтверждено собственными проверками

Чистый upstream checkout: **8/8 unit tests**. Запущены реальные `RRSIConfig`, `aggregate`, `select_round` и `budget_table`, а не переписанный selector.

На управляемых 105 синтетических claim-check задачах (train=40, validation=25, отложенные holdout=40 с намеренным сдвигом частот дефектов) RRSI без внешнего domain guard выбрал **запоминающую train-ярлыки конфигурацию** (100% train → 45% holdout). Встроенные методы regularization **не тестировались целиком**, т.к. proposer, critic и pruner как LLM-цикл не запускались.

После введения **нашего дополнительного** validation-gate (минимум +10 п.п. к baseline) и запрета oracle, недоступного для произвольных реальных задач, выбран `locality`: 80% train / 80% validation / 70% holdout против 60% / 60% / 45% baseline. Указанный прирост **+25 п.п.** — только на специально сконструированной небольшой holdout-выборке; нельзя считать его приростом LLM.

**Критическое условие:** `policy tokens C=None` для всех вариантов; cost gate не измерен. Не утверждать токеновую эффективность или наилучшую конфигурацию по стоимости.

## Применимость

[agent-config](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/agent-config/PROJECT.md) — подходящий узкий эксперимент: проверить фактическое наличие цитаты около заявленного номера строки. [dsh-runtime](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh-runtime/PROJECT.md) — только будущая методология офлайн-отбора harness на одинаковых trace и закрытом oracle.

**Решение:** `ADOPT_SELECTION_DISCIPLINE_NOT_AUTO_EVOLUTION`. Не включать recursive self-modification в рабочий runtime; отделить train/validation/holdout, требовать измеренные токены и эксплуатационные ограничения, фиксировать immutable SHA и регрессии. Авторские улучшения из статьи не воспроизведены.
