# Контрпроверки III: цитирование целевого инструмента и ограничение SQL-планировщика

**Дата:** 07.11.2026. Продолжение [четырёх лабораторных проверок](next-evidence-round2.md) после коммита `812e9df`. Новых научных работ, project-fit, правок целевых репозиториев и разрешений на production нет. Здесь проверялись две отдельные инженерные гипотезы на синтетических данных.

## 1. dsh-paper2agent: настоящая точка приёма анализа против консервативного citation gate

**Источник:** локальный текущий `dsh-paper2agent`, базовый Git HEAD `890db42da86c307606195256ad898367b1e1a4f2`; реально импортирован `src/paper2project/core.py` с SHA-256 `5c6e468d045e3fd91f1503c6c69e818e80c416aee119f0b6c96a508b5a7daa87`. **Рабочая копия целевого проекта имеет незакоммиченные изменения**; эти SHA не фиксируют все локальные зависимости. Код целевого проекта не менялся и не копировался в публичный хаб.

**Шов:** `App.import_projects()` + `App.import_research()` + `App.create_job()` + `App.submit_analysis()` на отдельных временных синтетических документах, без вызова модели. `App.citation()` проверяет присутствие ID в snapshot, границы строк и *при наличии* буквальный `quote`. Он не сопоставляет смысл `rationale` с процитированными фразами — этот этап делегирован независимому review.

| Тест | A: текущий `submit_analysis()` | B: внешний exact-only auto-pass |
| --- | ---: | ---: |
| Случаи | 150 | 150 |
| Поддержаны по заранее заданному oracle | 50 | 50 |
| Заведомо неподтверждённых | 100 | 100 |
| Неподтверждённые: принятые структуры A / false auto-pass B | **100/100** структурно | **0/100** автоматически |
| Точно поддержанные буквальные утверждения | 25/25 структурно | 25/25 автоматически |
| Поддержанные перефразирования | 25/25 структурно | **25/25** отложены на review |

Корпус: 5 участников × 5 утверждений × 6 типов (точное, `never`, другой участник, явное отрицание, нерелевантное, правильное перефразирование). В A каждое `rationale` подавалось с настоящей цитатой к исходной строке и отдельной цитатой к синтетическому описанию проекта. Контроль `invalid_line_range`, `forged_quote`, `unscoped_document` отклонён; **`missing_quote` принят**, что согласуется с необязательностью поля `quote`.

**Не переинтерпретировать:** `submit_analysis()` принимает *структуру анализа*, а не выдаёт научный вердикт `SUPPORTED`. Результат — тест риска последующего неправильного использования структурной приёмки как semantic validation. Альтернатива B пока существует только во внешнем тестовом коде; она **не внедрена**. Отсутствует проверка нормальных многострочных цитат, медицинских статей, качества LLM review и downstream решений. Медиана A ~1,64 мс и B ~0,0035 мс на этой машине не характеризует сквозную задержку или стоимость модели. Синтетические 100/100 — **не prevalence** на реальных исследованиях.

**Диспозиция:** `STRUCTURE_VALIDATION_CONFIRMED / SEMANTIC_AUTO_APPROVAL_BLOCKED`. Для `dsh-paper2agent` и `agent-skills` требуется held-out пакет реальных допустимых цитат/парафраз, независимый annotator/oracle, измерение `precision/recall`, времени/токенов, затем сравнение двух реализаций на **копии** исходника после получения воспроизводимого clean source snapshot.

## 2. PostgreSQL: ограничение времени планирования и прав EXECUTE

**Среда:** `docker.io/library/postgres:18` (локальный image ID `79061104669bb30919d015b549c764e2d8021a18ee39cb175581a2588fe90dbe`), rootless Podman `--network none`, 0 опубликованных портов, 0 host mounts, лимиты 2 CPU / 1 GiB / 200 процессов. В контейнере создана отдельная роль `observer` и синтетическая PL/pgSQL-функция, намеренно ошибочно объявленная `IMMUTABLE`, вызывающая `pg_sleep(0.30)` и `RAISE NOTICE`. Клиент посылает `EXPLAIN (FORMAT JSON)` без `ANALYZE` внутри `BEGIN READ ONLY`.

| Контроль | Результат | Wall-clock, включая запуск psql |
| --- | --- | ---: |
| A: `IMMUTABLE`, без ограничения statement timeout | `SYNTHETIC_PLANNER_DELAY` обнаружен, exit 0 | 390,25 мс |
| B: тот же запрос, `statement_timeout=80ms` | `canceling statement due to statement timeout`, exit 3 | 167,40 мс |
| `VOLATILE` в `EXPLAIN` без `ANALYZE` | Функция не вызвана, exit 0 | 84,81 мс |
| `REVOKE EXECUTE` у `observer` | `permission denied for function planner_delay`, exit 3 | 87,76 мс |

Здесь измерено не «выполнение SELECT целиком», а **исполнение тела пользовательской функции на этапе constant folding**. `READ ONLY` не является CPU/time sandbox; ограничение `statement_timeout` и отзыв `EXECUTE` сработали в этом конкретном сценарии. Замеры не являются latency benchmark. Не проверены произвольные SQL-инъекции, файловый/сетевой доступ, расширения, реальный бинарник `pgbot` или полноценный агентный MCP. Роль с повышенными правами и иная конфигурация потребуют отдельной проверки.

**Диспозиция:** `PLANNER_RESOURCE_BOUND_CONFIRMED / TOOL_SECURITY_STILL_PENDING`. Следующий gate для `Wiki_PG`, `sequential-rca`, `hermes-akuz-agents`: действительно вызвать штатный SQL/MCP tool на disposable PostgreSQL, запретить небезопасные команды allowlist'ом, использовать least-privilege, timeout, `search_path` и негативные тесты; затем проверить журнал/отказ/восстановление с независимым SQL-оракулом.

## Воспроизведение и доказательства

- [Целевой A/B скрипт](../../experiments/research-portfolio/2026-11-07-paper2agent-target-citation-ab.py) / [агрегаты и контрольные случаи](../../data/results/research-portfolio/2026-11-07-paper2agent-target-citation-ab.json). Запуск с `P2P_SOURCE=/path/to/dsh-paper2agent`, `P2P_GIT_SHA=<git HEAD>`, `P2P_TREE_CLEAN=false`, `OUTPUT=/path/to/result.json`; источники создаются только в `TemporaryDirectory`.
- [Timeout/GRANT/EXPLAIN скрипт](../../experiments/research-portfolio/2026-11-07-pgplanner-timeout-ab.py) / [исходные машинные результаты](../../data/results/research-portfolio/2026-11-07-pgplanner-timeout-ab.json). Нужен локальный образ PostgreSQL 18 в Podman; контейнер очищается в `finally`.

**Независимая модельная критика:** один дополнительный запрос к локальному ZCode завершён по лимиту 75 секунд с пустым stdout (exit 124). Статус роли `BLOCKED_PROVIDER`; приёмка ниже основана на детерминированных контрольных случаях и SQL-ошибках, а не на согласии моделей. Дальнейшее независимое рецензирование необходимо.

**Приёмка текущего этапа:** `ACCEPT_BOUNDED_TARGET_EVIDENCE`, `REWORK` семантического citation gate и полного SQL tool E2E, `NO_NEW_PROJECT_FIT`, `NO_PRODUCTION_APPROVAL`. Это не замещает предыдущие полнотекстовые scientific reviews и не даёт разрешения изменять реальные проекты или базы данных.
