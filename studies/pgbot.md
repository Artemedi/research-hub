# pgbot — deterministic PostgreSQL diagnostics for AI agents

**Класс:** ENGINEERING_IMPLEMENTATION (не научная статья).
**Первичный источник:** [pgrundev/pgbot](https://github.com/pgrundev/pgbot/tree/826531fefd7d13b4381327acd4cce5be98bd71eb), [release v0.9.0](https://github.com/pgrundev/pgbot/releases/tag/v0.9.0), Apache-2.0.
**Проверка:** [лабораторный протокол 2026-11-04](../reviews/pgbot/2026-11-04.md), [независимый JSON oracle](../experiments/2026-11-04-pgbot-verify.py).
**Статус:** `LAB_VERIFIED` / `HEAD_TO_HEAD_NOT_DONE` / `NO_PRODUCTION_APPROVAL`.

## Что проверено непосредственно

Статический бинарник pgbot v0.9.0 проверен по SHA-256, запущен против локального PostgreSQL 18.3 без сети под ролью `pgbot_ro` с `pg_monitor`. Статус не основан только на README или Telegram.

- На 15 000 dead tuples с `autovacuum_enabled=false` обнаружены `autovacuum_disabled_on_table` (critical) и `table_bloat` (warn).
- На одной созданной блокировке `pg_stat_activity/pg_blocking_pids` показал один blocked backend, а pgbot вернул `blocking_chains` (critical) и `locks.blocked_count=1`; `activity --json` сохранил wait type и скрыл SQL literals.
- После прекращения блокировки и `VACUUM (ANALYZE)` критичные/вакуумные findings исчезли.
- Роль без `pg_monitor` получила `server.has_pg_monitor=false`, но команда с `--fail-on none` завершилась успешно и выдала частичный отчет. Агент обязан проверять признак самостоятельно, не только наличие `findings`.
- Все четыре JSON-состояния соответствуют официальной JSON Schema `1.5.0`; пять дополнительных `inspect` прошли валидацию. Медиана пяти запусков — 620,2 мс с учётом `podman exec`; DML-счётчики и checksum пользовательской таблицы не изменились.

## Переносимость результатов и ограничения

Это маленький controlled smoke-test, не benchmark производительности под высокой нагрузкой и не валидация на PostgreSQL 15/репликации/многих базах. Отдельный `pgbot` не является заменой Wiki_PG, потому что Wiki_PG включает документацию, индекс, источники доказательств и собственные MCP-инструменты; против того же live lab instance Wiki_PG не запускался. Заключение о сравнительном превосходстве отсутствует.

## Применимость

- [Wiki_PG](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/Wiki_PG/PROJECT.md) — независимый evidence producer, если source-verified контракт и измерения показывают уникальные проверки. `PROFILE_MATCH` до интеграционного теста.
- [sequential-rca](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/sequential-rca/PROJECT.md) — возможная диагностическая телеметрия для RCA без автоматического исправления, `NEEDS_EVIDENCE`.
- [hermes-akuz-agents](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/hermes-akuz-agents/PROJECT.md) — read-only MCP-сигнал, `NEEDS_EVIDENCE`.

**Ближайший критерий:** 30+ независимо размеченных PG15/18 инцидентов с общим oracle, профилем затрат и воспроизведением в Wiki_PG и pgbot. Не подключать к production и не разрешать автокоррекцию без отдельного решения владельца.
