# Anthropic — scheduled agent automations

[Структурированная запись и связи](../catalog/studies/anthropic-agent-automations.md)

- **Источник:** [Building effective agent automations](https://claude.dev/blog/building-effective-agent-automations/), Lance Martin, CJ Avilla, 08.10.2026; [daily-brief reference @8ef47d719eba5379ff8f38133f5defcc499e856f](https://github.com/anthropics/claude-quickstarts/tree/8ef47d719eba5379ff8f38133f5defcc499e856f/managed-agents/daily-brief), MIT. Telegram BK-047 / 13.10.
- **Метод:** per-source bookmarks и overlap, явное сообщение о недоступных источниках, независимые preferences/state, подтверждение ответа перед изменением ledger, ограничения сети/ключей/бюджета. Большая часть поведения задана инструкцией модели, а не атомарным программным протоколом.
- **Ограничение:** проверка заголовка и `maybe posted` уменьшают неоднозначность, но не доказывают exactly-once при гонках, задержке видимости и сбоях. [Отдельный ранее выполненный LIMBO × TelegramBot lab](../reviews/exactly-once-limbo/2026-11-04.md) иллюстрирует похожий класс проблем, не является тестом Anthropic reference.
- **Проекты:** `TelegramBot`, `wiki-tasks`, `HermesAgent`, `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. Reference и hosted workflow не запускались; Slack, GitHub credentials и production не использовались. [Обзор](../reviews/anthropic-agent-automations/2026-11-04.md).
