# Open Steps — понятные статусы и навыки агентной разработки

- **Источник:** [kharmanskyi/open-steps](https://github.com/kharmanskyi/open-steps), Pavlo Kharmanskyi; открытая инженерная реализация, не рецензируемая научная статья.
- **Исходный Telegram ID:** BK-006 / 11.09.2026; при этом здесь рассмотрена более поздняя версия, не утверждается, что она существовала в исходной закладке.
- **Версия:** [v0.4.8 / 4fa744ba8ea06ccf128a39853824c46ac391dd00](https://github.com/kharmanskyi/open-steps/tree/4fa744ba8ea06ccf128a39853824c46ac391dd00), коммит 2026-10-05; проверка 2026-11-04; [MIT](https://github.com/kharmanskyi/open-steps/blob/4fa744ba8ea06ccf128a39853824c46ac391dd00/LICENSE).
- **Что предлагает:** восемь инструкций для статуса, упрощения, вопросов, пользовательских действий, независимой приёмки, выбора следующей задачи, premortem и карты продукта; отдельные hooks, doctor и измерительный стенд.
- **AUTHOR_REPORTED:** активация skill на 25 фразах × 3 повтора на каждой из трёх моделей Claude; это небольшой smoke test с другими активными инструкциями. Качество сохранения фактов не установлено. Автор различает вызов, отказ и фактическую загрузку skill.
- **INDEPENDENTLY_VERIFIED:** авторские offline тесты hooks 290/290 и eval fixtures 116/116; в отдельной синтетической Git-среде изменение содержимого уже существующего untracked-файла не вызвало stop-report, а tracked контроль вызвал. Это подтверждённый узкий дефект механизма наблюдения, не оценка качества LLM.
- **Проекты:** `agent-skills`, `agent-config`, `dsh-team-context` — `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`: правила понятной отчётности и безопасного жизненного цикла навыков; предметные детали и ограничения в [отчёте](../reports/2026-11-04-bk006-open-steps-review.md).
- **Статус:** `LAB_VERIFIED` только для указанной синтетической проверки и offline tests; `BLOCKED: MEASUREMENT_MISSING` для качества ответов и эффекта на проекты; `NO_PRODUCTION_APPROVAL`. Установка пакета, его хуков, автоматическое слияние и внешние модельные вызовы не выполнялись.

[Воспроизводимый эксперимент](../experiments/bk006-open-steps/fingerprint-fixture.sh) • [Полный инженерный обзор и матрица](../reports/2026-11-04-bk006-open-steps-review.md) • [Предварительная Telegram-матрица](../reports/2026-11-04-telegram-bk-preliminary-project-matrix.md)
