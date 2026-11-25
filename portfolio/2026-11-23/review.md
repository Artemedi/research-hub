# Портфельный обзор — 2026-11-23

**Период поиска:** 2026-11-16 00:00 — 2026-11-23 08:55 Europe/Moscow. Предыдущий успешный недельный отчёт: [2026-11-16](../2026-11-16/review.md). **project-registry HEAD:** `7a976c353579f8da64789daf18fe1088e5ab8dbb`; **research-hub исходный HEAD:** `b809d00376a6001f4e49bb345ec0f7a09c30c908`. Источник discovery: [README](https://github.com/Artemedi/project-registry/blob/7a976c353579f8da64789daf18fe1088e5ab8dbb/README.md), [RESEARCH_GUIDE](https://github.com/Artemedi/project-registry/blob/7a976c353579f8da64789daf18fe1088e5ab8dbb/RESEARCH_GUIDE.md), 45 карточек (44 репозитория + внешний проект). Начальный тематический screening охватывал перечень всех 45; **не все 45 PROJECT.md повторно прочитаны построчно**. Приоритетная проверка проведена по Wiki_PG и developer-safe-dotnet-core. Это ограничение полноты, а не VERIFIED_FIT для остального портфеля.

## Принято: PostgreSQL 19 GA (19 ноября 2026)

**FULL_TEXT_VERIFIED** — [полные официальные release notes](https://www.postgresql.org/docs/19/release-19.html), разделы E.1.2–E.1.3; [официальное объявление](https://www.postgresql.org/about/newsarchive/pgsql/). Дата первоначального GA: **2026-11-19**; это новая major version, не переиздание 18.7 от 12 ноября. Лицензия PostgreSQL License. Источник — engineering release documentation, **не контролируемый benchmark на AKUZ**.

**Механизмы и факты.** В 19 добавлены `REPACK (CONCURRENTLY)` (не блокирует обычные чтения/записи, но требует проверки locking и дискового бюджета), `pg_plan_advice` и `pg_stash_advice` для экспериментов с планами, параллельный autovacuum индексов и scoring приоритета таблиц, `pg_stat_autovacuum_scores`, `pg_stat_recovery`, `pg_stat_lock`, дополнительные WAL full-page image и EXPLAIN IO метрики. Оптимизатор умеет в ряде случаев преобразовать NOT IN в anti join, делать раннюю агрегацию и улучшать FK checks. `WAIT` обеспечивает ожидание заданного LSN на standby (read-your-writes), **но не устраняет конфликты long-running hot-standby queries с WAL replay**. Отдельно введено `INSERT ... ON CONFLICT DO SELECT ... RETURNING` (полезно для get-or-create). Авторы не приводят универсального эффекта для данных пользователя.

**Совместимость:** major upgrade требует pg_upgrade/dump-restore/logical migration; изменены JIT default (off), `io_workers` заменён на четыре GUC, изменены wait-event names, поведение text-search/pg_trgm для некоторых локалей (может требовать REINDEX), ограничена совместимость некоторых btree_gist inet/cidr индексов. Риск CPU/IO/диска для REPACK, RAM/worker pressure для autovacuum, WAL/репликации, изменения планов и regression SQL. Нельзя использовать PG19 функции на текущем PG15/18 без upgrade.

**Практическая ценность: 9/10** (релевантность проблемам VACUUM/XID, репликам и диагностике). **Сложность внедрения: 8/10** (major migration, расширения, replica/backup, app compatibility). Это оценка *возможности*, не измеренного ускорения.

**Минимальный A/B (offline, без production):** на синтетической или разрешённой обезличенной копии фиксированного набора SQL и данных PG18.7 (A) против PG19.0 (B); 5 прогонов после прогрева, одинаковые CPU/RAM/IO limits и статистика. Отдельно: (1) 20 EXPLAIN ANALYZE BUFFERS WAL планов с oracle равенства result sets; (2) таблица с контролируемым bloat и REPACK с мониторингом disk peak, lock waits, p95 latency и WAL; (3) replica replay под read-only длинным запросом и WAIT с проверкой LSN, без обещания устранения конфликтов; (4) autovacuum backlog/XID age и workers. Успех: ноль расхождений SQL/backup/replication oracle; без ухудшения p95 более 5% и disk/WAL выше заранее выделенного бюджета; отдельные improvements только при воспроизводимом выигрыше >10% и отсутствии correctness regression. Ресурсный cap для первого теста: 4 vCPU, 16 GB RAM, 100 GB scratch, 2 часа; большие AKUZ-подобные данные — отдельный gate. Статус `BLOCKED: MEASUREMENT_MISSING`.

## Обязательная матрица соответствия

| Исследование | 1–3 конкретных проекта / PROJECT.md | Почему именно этот проект | Ограничения | Следующий минимальный A/B | Статус |
|---|---|---|---|---|---|
| PostgreSQL 19 GA | [Wiki_PG](https://github.com/Artemedi/project-registry/blob/7a976c353579f8da64789daf18fe1088e5ab8dbb/projects/01-dba-akuz/Wiki_PG/PROJECT.md) | PostgreSQL diagnostics, knowledge and MCP state evidence; новые GUC/DMV, WAL и vacuum требуют корректного version-gating | Источник [Wiki_PG README](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/README.md#L1) и [docs/universal-system-mcp.md](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/docs/universal-system-mcp.md#L11) подтверждают документационный контракт, **не конкретный code seam**; `UNKNOWN/NEEDS_EVIDENCE`, live baseline не проверен | Offline PG18/19 snapshots с GUC/DMV, oracle по version-aware outputs, 30 запросов и ноль ложных фактов | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| PostgreSQL 19 GA | [developer-safe-dotnet-core](https://github.com/Artemedi/project-registry/blob/7a976c353579f8da64789daf18fe1088e5ab8dbb/projects/07-colleague-projects/developer-safe-dotnet-core/PROJECT.md) | Авторский [SOURCE_BRIEF](https://github.com/Artemedi/project-registry/blob/7a976c353579f8da64789daf18fe1088e5ab8dbb/projects/07-colleague-projects/developer-safe-dotnet-core/SOURCE_BRIEF.md) описывает ручной PostgreSQL SQL, schema drift и HiLo; ON CONFLICT get-or-create может быть релевантен | `AUTHOR_STATED / NEEDS_SOURCE_CODE`: URL, repo@SHA, API, тесты, baseline не предоставлены; PG19 не заявлен поддерживаемым | Условно: PG18 vs PG19 на 50 параллельных get-or-create с SQL result/uniqueness oracle, p95 и lock waits, только после доступа к коду | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE / NEEDS_SOURCE_CODE` |

**Shortlist не означает implementation approval.** Отдельные `dsh` (control-plane), `dsh-runtime`, исторический `deepseek-harness` fork, `dsh-paper2agent` и вспомогательный `paper2agent-index` не были назначены целями: нет доказанной связи PG19 функций с их кодом. Для остальных карточек не заявлен fit без предметного подтверждения.

## Отклонено / не переиздавать

- PostgreSQL 18.7/17.12/15.20 от **12 ноября** — **DUPLICATE_UNCHANGED**; уже [отчёт 16 ноября](../2026-11-16/review.md).
- Microsoft Ignite SQL announcements от **16 ноября** — **SCREENED_OUT**: общий анонс/сводка, не выделено новой подтверждённой on-prem SQL Server 2022 интеграции с полной методологией и A/B.
- Другие найденные search snippets и abstracts — **FULL_TEXT_UNAVAILABLE / NOT_QUALIFIED** для включения: полный авторский метод/результаты в рамках данного прохода не проверены. Не объявляются новыми исследованиями.

## Приоритет и блокеры

1. **PG19 read-only diagnostics/knowledge version-gating для Wiki_PG** — самый дешёвый и безопасный offline oracle, прежде чем обсуждать major migration. Требуется проверить actual parser/API source seam и версии источников.
2. **PG19 VACUUM/REPACK/replica isolated benchmark** — потенциально большой выигрыш для AKUZ DBA, но высокий I/O/WAL риск и необходимость изолированной среды; не production.
3. **PG19 get-or-create concurrency для внешнего .NET ядра** — только AUTHOR_STATED; `NEEDS_SOURCE_CODE` и согласие владельца.

**Проверка новизны:** индекс [studies/INDEX.md](../../studies/INDEX.md) содержит ранее опубликованные материалы; PG19 GA в просмотренном индексе не найден. Архивные обзоры использованы для дедупликации по теме, но не выполнено полное построчное повторное чтение всех исторических файлов. Ни одно изменение source repos/production не разрешено.
