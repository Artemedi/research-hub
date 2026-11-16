# Портфельный обзор — 2026-11-16

**Период:** 2026-11-12 00:00 — 2026-11-16 08:05 Europe/Moscow. Предыдущий недельный обзор: 2026-11-11; дополнительно учтены карточки research-hub до 2026-11-14. **project-registry HEAD:** `fd706fd846b5a2d53a8b71d8df4d311f219e5da1`; **research-hub исходный HEAD:** `20f397beb1fb681afd508bbb8ea524d11b058ba9`. Каталог — discovery, не runtime evidence. README перечисляет 45 карточек, включая внешний developer-safe-dotnet-core. Все 45 PROJECT.md построчно повторно не прочитаны: ограничение полноты этого запуска.

## Принятый материал: PostgreSQL minor releases 18.7 / 17.12 / 16.16 / 15.20 / 14.25

**Новая версия:** 2026-11-12; не новая публикация PostgreSQL как продукта. **FULL_TEXT_VERIFIED**: [официальные подробные release notes 18.7](https://www.postgresql.org/docs/release/18.7/), [объявление и upgrade caveats](https://www.postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released-3442/), [15.20 notes](https://www.postgresql.org/docs/release/15.20/). Официальный changelog описывает исправления, но не содержит публичного performance benchmark на нагрузке AKUZ. Лицензия: PostgreSQL License, патч — штатное обслуживание, не сторонняя библиотека.

**Метод/факты:** maintenance fixes (не научный эксперимент). Объявлено 52 security fixes и более 140 bug fixes. Исправлены возможная порча GIN и pg_trgm GiST индексов, неверные результаты planner при LATERAL/outer joins, нарушения корректности partition pruning, проблемы incremental/base backup, ошибки logical replication. Изменён алгоритм join removal: переписывание parse tree вместо модификации derived planner structures. Известны post-upgrade меры: выборочный REINDEX при затронутых индексах, новая полная backup-base при использовании incremental backups. Отдельные исправления относятся только к конкретным версиям: применимость каждого пункта к PG15 проверять по 15.20 release notes, не переносить автоматически весь список 18.7.

**Потенциальная польза:** уменьшение риска silent wrong results и corruption; performance gain **UNKNOWN**, исправление планировщика может также менять планы в худшую сторону. **Практическая ценность 9/10** (correctness/security на крупных PG), **сложность 6/10** (тестирование, backup/reindex, extension ABI). Риски: downtime/replica lag, IO/CPU на REINDEX, место под перестройку, восстановление, несовместимость C extensions, смена планов, дополнительное окно обслуживания. GPU/VRAM не нужны; latency может измениться. Ни одно production изменение не разрешено.

**Минимальный A/B:** две изолированные копии одинакового synthetic или обезличенного PG snapshot на 15.19 и 15.20 (для PG18: 18.6 vs 18.7), одинаковая конфигурация, 20–30 заранее зафиксированных запросов с outer join/LATERAL/partition pruning и GIN; oracle — независимый SQL reference и сравнение полных результатов/хешей, плюс EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON), 5 прогонов после прогрева, median/p95, shared hit/read, temp IO, план, расхождения строк. Отдельно проверять restore test backup и index integrity. Успех: ноль расхождений с oracle и ноль новых ошибок; регрессии p95 >10% требуют triage, а не автоматического принятия. Ограничить тест 2 CPU, 8 GiB RAM, 10 GiB temp IO, 30 мин; тестовые datasets подбирать под бюджет. **BLOCKED: MEASUREMENT_MISSING**; baseline не запускался.

**Интеграционная граница:** обновление серверной СУБД — не точка вставки кода Wiki_PG. Исходник Wiki_PG `d55721bb99bff25fae352341cfd630c048693d6b`, [README.md:1](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/README.md#L1) подтверждает контур DBA-знаний, но не deployment PG. Реальная версия сервера и его backup/reindex процедуры **UNKNOWN/NEEDS_EVIDENCE**. Для внешнего .NET проекта сведения [SOURCE_BRIEF.md](https://github.com/Artemedi/project-registry/blob/fd706fd846b5a2d53a8b71d8df4d311f219e5da1/projects/07-colleague-projects/developer-safe-dotnet-core/SOURCE_BRIEF.md) — **AUTHOR_STATED**, code seam и baseline **NEEDS_SOURCE_CODE**.

## Матрица «исследование → конкретные проекты»

| Исследование | 1–3 проекта и PROJECT.md | Почему | Ограничения | Минимальный A/B | Статус |
| --- | --- | --- | --- | --- | --- |
| PostgreSQL 15.20 / 18.7 maintenance | [Wiki_PG](https://github.com/Artemedi/project-registry/blob/fd706fd846b5a2d53a8b71d8df4d311f219e5da1/projects/01-dba-akuz/Wiki_PG/PROJECT.md); [developer-safe-dotnet-core](https://github.com/Artemedi/project-registry/blob/fd706fd846b5a2d53a8b71d8df4d311f219e5da1/projects/07-colleague-projects/developer-safe-dotnet-core/PROJECT.md) | PG DBA diagnosis; PostgreSQL persistence without ORM | Неподтверждённые deployment версии; для коллеги AUTHOR_STATED / NEEDS_SOURCE_CODE; ни один repo не является самим PostgreSQL server | Изолированные 15.19/15.20 или 18.6/18.7, SQL oracle + plan/IO + backup restore | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |

## Отсев / дубликаты

- [.NET November 2026 servicing](https://devblogs.microsoft.com/dotnet/dotnet-and-dotnet-framework-november-2026-servicing-updates/): опубликовано **10 ноября**, до данного окна; важное security обновление, но не включено как новая работа.
- PostgreSQL 19 RC2 от 12 ноября: не считать production candidate; релиз-кандидат и новая ветка, не подходящая замена поддерживаемого PG15/18 без отдельного миграционного плана.
- [Datasentinel 2026.10](https://www.postgresql.org/about/newsarchive/): 15 ноября, marketing release notice, нет прочитанного полного технического метода/измерений: **FULL_TEXT_UNAVAILABLE** для научного включения.
- Ранее рассмотренные AvalancheBench и prompt-injection swarm — без подтверждённой новой версии в этом окне: **DUPLICATE_UNCHANGED**, не переизданы.

## Приоритет

**P1: PostgreSQL security/correctness minor upgrade readiness** — начать с инвентаризации версий/расширений, affected indexes и restore rehearsal, затем isolated A/B. Второго и третьего приоритета без новых full-text evidence нет.

## Пределы проверки

Это один подтверждённый engineering change, не измеренный benefit. Не выполнены exhaustive reread всех 94 studies, архивных обзоров и 45 PROJECT.md, локальная сборка, diff и CI; внешние репозитории не изменены. Любая формулировка VERIFIED_FIT была бы преждевременной. Публикация документа сама по себе не подтверждает тесты.