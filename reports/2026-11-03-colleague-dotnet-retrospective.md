# Повторный отбор ранее рассмотренных работ для проекта коллеги

**Дата оценки:** 2026-11-03.
**Тип:** `HISTORICAL_REASSESSMENT` — не новый поиск публикаций.
**Состояние:** `AUTHOR_STATED / NEEDS_SOURCE_CODE`, без разрешения на реализацию.
**Проект:** [карточка](https://github.com/Artemedi/project-registry/blob/main/projects/07-colleague-projects/developer-safe-dotnet-core/PROJECT.md) и [Research Brief](https://github.com/Artemedi/project-registry/blob/main/projects/07-colleague-projects/developer-safe-dotnet-core/SOURCE_BRIEF.md).

Проект коллеги описывает C# 14/.NET 10/PostgreSQL-ядро с Roslyn-анализаторами, source generator, identity map, typed query DSL без ORM и планируемым независимым агентным аудитом. Исходный код проекта, HEAD, CI и baseline не предоставлены. Описание — `AUTHOR_STATED`, все интеграционные точки — `NEEDS_SOURCE_CODE`.

**Источники отбора:** [исторический индекс DSH](../archive/dsh/knowledge/research/README.md) и обсуждённый ранее обзор от 2 ноября в истории планировщика. Это shortlist уже рассмотренных работ, не самостоятельное подтверждение научных выводов. Перед внедрением заново сверить полный текст статьи, точную версию, результаты и код.

## Самые подходящие гипотезы

| Исследование | Первичный источник | Предположительная связь | Ценность / сложность* | Минимальная проверка |
| --- | --- | --- | --- | --- |
| VeriHarness | https://arxiv.org/abs/2610.00972 | Независимая доказательная проверка agentic code review, в дополнение к планируемой схеме hunter/refuter | 9 / 6 | 30 заранее размеченных нарушений C#, сравнить false accepts/rejects, время и токены с текущим процессом |
| Concordat | https://arxiv.org/abs/2610.37461 | Идеи типизированных переходов для misuse-resistant API; исходная работа про LLM-agent sessions, **не** C# типовую систему | 9 / 6 | Изолированный типизированный API и набор positive/negative compilation fixtures |
| GeoAgent | https://arxiv.org/abs/2610.31096 | Контракты артефактов между refine → review → design → plan → implement | 8 / 4 | 20 coding tasks, baseline vs проверяемые артефактные контракты; missing requirements и false completion |

## Остальные кандидаты

| Исследование | Источник | Идея | Блокер |
| --- | --- | --- | --- |
| BenchShield | https://arxiv.org/abs/2609.11028 | Целостность eval/guard-witness тестов: отличать PASS от доказанного корректного результата | Нужен независимый oracle и реальные traces |
| Where Does Exactly-Once Live? | https://arxiv.org/abs/2609.29095 | Обнаружение дублированных external side effects при повторных операциях | Атомарный PostgreSQL save — не то же, что exactly-once внешний вызов |
| Goal-Aware Dynamic Multi-Agent Collaboration | https://arxiv.org/abs/2610.39193 | Явные acceptance conditions и передача доказательств между агентными подзадачами | Дополнительный verifier/token/latency overhead; не создавать второй orchestrator по умолчанию |
| Silent Cue Loss | https://arxiv.org/abs/2610.30026 | Сохранение смысловых признаков при извлечении требований | Только при реальной работе с форматированными PDF/Word |

* Оценки 1–10 перенесены из прошлой дискуссии как **экспертные гипотезы**, не measurements проекта коллеги.

## Недостаточно представленные темы старого архива

Исторический DSH watch был преимущественно агентным. В нём нет полноценного обзора Roslyn incremental generators, identity map, clone/merge, SQL DSL без ORM, PostgreSQL schema drift, soft-delete uniqueness и guard-reachability. Это будущие поисковые направления, а не основания объявлять любые прежние agent papers подходящими.

**Следующий gate:** получить от коллеги разрешённый read-only доступ к исходникам, зафиксировать `repo@SHA`, проверить действующие тесты и baseline, затем повторить scientific fit и подготовить маленький эксперимент. Не переносить код коллеги в исследовательский архив.
