# Research Portfolio Orchestrator — global research management

Дата: 2026-11-07. Статус: **архитектура и ограниченный offline-прототип**. Не автономный production daemon, не разрешение на внедрение.

## Роли репозиториев

- Приватный `Artemedi/project-registry@838b86a28fcaa3440eeddbe147b6188e0d177963` — глобальная карта **45** исходных карточек проектов, границы, research-вопросы, портфель и профиль внешнего .NET проекта. Не публиковать их закрытые содержимое и source.
- Публичный `Artemedi/research-hub@3180d9c46914f2f54d2a21e642b7ec3efffa2b99` — каноническая история источников, обзоров, экспериментов и project-fit. `catalog/entities.json` фиксирует доказательные связи; `catalog/structure.json` определяет пути. Генерируемые представления не редактируются вручную.
- `paper2agent-index` — отдельный производный shortlist, не authority по review, не источник новых фактов или production approval.
- Исходный `project-repository@SHA/path:line` — authority по действительному коду/API. PROJECT.md/brief описывает профиль, **не подтверждает** работающий контракт.

Исследовательские карточки `studies/`, датированные `reviews/`, машинные данные `data/results/`, матрицы `data/project-fit/`, сводки `portfolio/`. Telegram BK — provenance, а не главный study id. Historical reviews/архив DSH сохраняются.

## Обязательный исследовательский цикл

1. Дедупликация DOI/arXiv/URL/version и исходной даты, `source_id`, frozen план, первичные и негативные гипотезы.
2. **Полный текст** легального HTML/PDF/авторской полной версии, включая Methods, Results, Limitations, оценки выборки и переносимости. Abstract, PR и snippets — только screening; если после поиска альтернатив полного текста нет, `FULL_TEXT_UNAVAILABLE`. Для engineering — официальное полное описание, pinned source + тесты. HTTP 200, pdftotext и список заголовков сами по себе не являются методологическим review.
3. Разделить `AUTHOR_REPORTED`, `SOURCE_REVIEWED`, `LAB_VERIFIED`, `PROJECT_PROFILE_MATCH`, `PRODUCTION_APPROVED` как **разные независимые измерения**. Привязка к профилю не равна улучшению на реальных сценариях.
4. Проверить все 45 PROJECT.md и сделать **1–3 shortlist либо NO_FIT**, явно маркируя непроверенные пары `NOT_EVALUATED`. Для каждого shortlist нужен source seam `repo@SHA/path:line`, либо `AUTHOR_STATED / NEEDS_SOURCE_CODE` (внешний проект).
5. Независимая проверка источника и эксперимента: исходный baseline/target, held-out cases, noise/quality oracle, отрицательные тесты, CPU/IO/RAM, latency, cost, безопасность и ограничения. Нет независимого oracle — `BLOCKED: MEASUREMENT_MISSING`.
6. Итоговый совет проверяет расхождения; GPT-6 принимает `ACCEPT`, `REWORK`, `BLOCKED` или `REJECT` по *текущему этапу*. `ACCEPT` не позволяет менять production или исходники без отдельного owner gate. Адресный возврат сохраняет существующие доказательства и повторяет лишь нужный шаг.

## Глобальный диспетчер

**Логические агенты ≠ физические процессы.** 100+ ролей образуют отдельные DAG для разных исследований, с общим приоритетным планировщиком и ограниченной очередью вызовов (текущая интеграция ZCode: целевой cap 1, максимум 2). Каждый узел: `study_id`, `task_id`, `role`, `input_digest`, `depend_on`, `acceptance_checks`, `iteration`, `evidence_output`, `privacy_scope`, `tool_allowlist`.

Состояния:
- `PLANNED` — source ID, дедупликация и критерии зафиксированы.
- `READY` — все зависимости приняты.
- `RUNNING` — одиночный ограниченный tool/model запрос.
- `REVIEW` — доказательства переданы независимому reviewer.
- `ACCEPT` — criteria **данного узла** выполнены.
- `REWORK` — конкретное противоречие + приёмочный тест исправления.
- `BLOCKED` — нет полного текста, разрешения, источника, oracle или capacity/ provider.
- `REJECT` — гипотеза опровергнута либо NO_FIT с доказательствами.

Scheduler выбирает `READY` узлы *из разных исследований*; завершение R1 открывает его REVIEW, одновременно R2 получает первоисточник, R3 переходит к эксперименту, R4 получает отказ и `REWORK`. Порядок определяется риском, ценностью, близостью к разрешению и fairness; одни исследования не блокируют другие. Crash/retry — idempotency key, bounded retry, checkpoint, полный учёт token usage и фактической квоты; если вызов не вернул итог — `BLOCKED_PROVIDER`, не имитация PASS.

**Вход в ZCode:** только публичные сведения или отдельные безопасные synthetic fixtures, без приватных профилей, живых SQL, учётных данных, пациентов, облачных токенов и production-логов. Сырой вывод инструментов недоверенный. `tool_result` подтверждается для **каждого** `tool_use_id`. В отчётах нужны **полные агрегаты** и denominators, а не первые N примеров: в BK-021 сокращённый список 6 примеров был принят за все 20 отрицательных cases.

**Роли при необходимости**: full-text reader, methodologist, factchecker, project reviewer, code reviewer, experimenter, security/privacy, licenses, QA/oracle, adversarial critic, integrator. Простые задачи без лишних ролей. GPT-6 — внешний reviewer, а не ещё один голос той же модели.

## Структура evidence packet

`study_id / source URL / source version / observed_at / source hash`; проверенные полный текст и разделы; утверждения и denominators; ограниченная стратегия тестирования; artefact paths и окружение; project shortlist с pinned source seam; независимый oracle и negative controls; observed outcomes; риски и условность; `ACCEPT/REWORK/BLOCKED/REJECT`; следующая минимальная проверка.

## Подтверждённые границы прототипа

- 83 источника прошли **machine accessibility** screening, не повторную полнотекстовую научную экспертизу.
- 45 профилей, 3 735 пар study×project; 376 документированных оценок, остальные 3 359 `NOT_EVALUATED`, а не `NO_FIT`.
- Двухпоточный deterministic controller выполнил **249 этапов** по 83 исследованиям, **без LLM вызовов**. Это проверка очереди и зависимостей, не доказательство реального исследовательского превосходства.
- Ранее 14 ZCode логических ролей с одним исполнителем проверили синтетику 12 кейсов; долгий интегратор/арбитр испытывали timeout. Конкурентные 20 запросов к неофициальному wrapper дали высокий отказ; не повышать параллельность без воспроизводимого стабилизационного теста.
- В этом проходе новый ZCode-screening проходит отдельно и не устанавливает научных фактов на основе карточных сниппетов.

## Отдельный gate перед внедрением оркестратора

Испытать >=20 **разных новых** реальных безвредных задач с известным независимым oracle: A — single worker, B — фиксированный совет, C — адаптивный DAG, одинаковые source, budgets и tool schemas. Считать pass@task, recall/falsification, e2e p50/p95, latency до *проверенного* ACCEPT, total input/output/cache tokens, реальные квоты, CPU/RAM/IO и ошибки provider, включая потерю/duplication и timeout. Без положительного сравнительного результата не менять runtime.

Текущий чат **не** является постоянно работающим сервисом: после окончания ответа не гарантирует автономного выполнения. Постоянный диспетчер требует отдельного явно запущенного и контролируемого сервиса, которого здесь не разворачивали.
