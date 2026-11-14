# Where LLM Agents Get Stuck Debugging Databases — Access More Than Reasoning

[Структурированная запись и связи](../catalog/studies/database-agent-observability.md)

**Тип:** полное авторское исследование-наблюдение; [arXiv 2611.17304v1](https://arxiv.org/pdf/2611.17304v1), 12.11.2026, 12 страниц; SHA-256 54a9e5744bcb6e801e60b0a647c3dee77fb28db40a48a15ed0603d32a8923dda.

**Маршрут:** Добавлен в карточки, P1 для sequential-rca и Wiki_PG на уровне evidence/observability evaluation, PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE.

Ретроспектива восьми database incidents, 27 сессий coding agent, около 3000 tool calls; все пять concurrency-dependent случаев имели первый неверный диагноз/исправление. Авторы связывают это с недостатком своевременных lock/deadlock/runtime наблюдений и частично с reasoning. Это качественная гипотеза из одной команды, **не контролируемое доказательство**, что расширение доступа предотвращает ошибки.

**Граница безопасности:** только offline replay записанных/синтетических evidence, никакого прямого grant к production, SQL-интерактивного доступа агента или несанкционированной регистрации. [Обзор](../reviews/database-agent-observability/2026-11-14.md) · [матрица](../portfolio/2026-11-14/review.md).
