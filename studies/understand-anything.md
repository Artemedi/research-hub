# Understand Anything — графы исходников и wiki

[Структурированная запись и связи](../catalog/studies/understand-anything.md)

- **Источник:** [Egonex-AI/Understand-Anything @4e6d3299017a7432da15957874992837a315c5b4](https://github.com/Egonex-AI/Understand-Anything/tree/4e6d3299017a7432da15957874992837a315c5b4), MIT; BK-048 / 16.10.
- **Подход:** статический разбор и LLM-анализ исходников/knowledge base строят граф, который показывает зависимости, семантические связи и impact; вычисленные LLM связи требуют отдельной проверки.
- **Уточнение к предварительной матрице:** исходники содержат SQL language config и отдельный `SQLParser`; ограниченная поддержка есть. На четырёх synthetic SQL inputs parser ошибочно дал `dbo` вместо `dbo.users`, пропустил `[dbo].[users]` и включил закомментированную таблицу; на простой таблице отработал. Это проверка одного parser API, не всех LLM/graph pipelines. 9 upstream wiki-parser tests прошли offline.
- **Проекты:** `dsh-team-context`, `MyWiki`, `akuz-schema-inventory` — сравнение с независимым oracle, `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`; SQL parser не замена проверенному MSSQL inventory. Реальный граф и LLM `NOT_RUN`; `NO_PRODUCTION_APPROVAL`.
- [Обзор и воспроизводимый fixture](../reviews/understand-anything/2026-11-04.md).
