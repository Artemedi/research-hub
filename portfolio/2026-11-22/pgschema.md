# Research intake — pgschema и evidence-gated PostgreSQL schema migrations

**Дата:** 2026-11-22. **Источник:** [`pgplex/pgschema@1b7eaf2827c84bb3e20679c6bab0c1116bf4e962`](https://github.com/pgplex/pgschema/tree/1b7eaf2827c84bb3e20679c6bab0c1116bf4e962), Apache-2.0; engineering source, **не peer-reviewed paper**. Дубликат URL в `research-hub@b809d00376a6001f4e49bb345ec0f7a09c30c908` не найден.

**Обобщённый предмет:** декларативное описание desired SQL schema с генерацией plan, отдельным DBA safety review, проверкой drift и **запрещённым автоматическим apply** до доказательной лаборатории. Не подменять программу миграции кнопкой Terraform-style. [Canonical study](../../studies/pgschema.md) · [pinned source audit + A/B/C](../../reviews/pgschema/2026-11-22.md).

**Реестр:** [`Artemedi/project-registry@7a976c353579f8da64789daf18fe1088e5ab8dbb`](https://github.com/Artemedi/project-registry/tree/7a976c353579f8da64789daf18fe1088e5ab8dbb), screening 45 project cards по описанию и стекам. Два подтверждённых источниками **документальных**, а не внедренческих, кандидата; остальные 43 = DEFERRED_SCREENING, не blanket NO_FIT.

| Исследование | Целевой проект | Связь с источником проекта | Риски/ограничения | Минимальный тест | Доказательный статус |
| --- | --- | --- | --- | --- | --- |
| [pgschema](../../studies/pgschema.md) | **AKUZ** | [`PG/AlterColumnIndex_pg.sql`](https://github.com/Artemedi/AKUZ/blob/c2ba29f6f9745a0a5e6e6a4bf6adc930595cf4cb/PG/AlterColumnIndex_pg.sql) имеет ручные PostgreSQL DDL для изменения индексов/колонок; подходит как дизайн синтетического data-loss/lock fixture | Реальное deployed состояние неизвестно; hot standby, WAL, table rewrite/ACCESS EXCLUSIVE, DROP, replay lag; отсутствует реальная oracle/DO NOT CONNECT | На выдуманной PG15/18 схеме сравнить A manually reviewed SQL vs B pgschema plan (без apply); независимый destructive DDL oracle и lock class | `DOCUMENTED_CANDIDATE / NEEDS_EVIDENCE` |
| [pgschema](../../studies/pgschema.md) | **Wiki_PG** | [`docs/universal-system-mcp.md`](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/docs/universal-system-mcp.md) документирует read-only evidence/state/coverage, возможно создать DBA-review checklist | Не DDL executor; нельзя выдать агенту права миграции/PG socket; отсутствуют исходники интеграции плагина | Документальный checklist для планов: lock, SQLSTATE, WAL, replica, owner/extension unsupported, schema drift; проверить на синтетическом плане | `DOCUMENTED_CANDIDATE / NEEDS_EVIDENCE` |

**Неприменимость без дополнительных данных:** `psqlqa` (EXPLAIN/GUI), `akuz-schema-inventory` (MSSQL/SQLite), `Postgres14book` (внешний материал) — не объявлять готовыми targets. Нет независимой source-backed точки внедрения `pgschema apply` в существующую систему.

## Предварительное решение и cost/risk

- **Engineering benefit hypothesis:** versioned desired state и читаемый JSON/SQL plan могут уменьшить ручную стоимость *планирования*; ускорение/безопасность `apply` на производственной PG не проверены.
- **Препятствия:** нет контроля `RENAME`/ownership/extensions, fingerprint не охватывает данные и реплики, операции split по группам, `--lock-timeout` не лимитирует DDL runtime, `CREATE INDEX CONCURRENTLY` тоже может оставить invalid index, небезопасные `DROP` и table rewrite.
- **Сравнение с ручным SQL:** A = DBA-reviewed SQL; B = generated plan + independent review, **без apply**; C = apply только на disposable synthetic PG15/18 после отдельного human/security gate. Metрики: плановая точность, unauthorized DROP, lock level/elapsed, WAL volume, lag/conflicts, output semantic/data oracle, review effort и rollback/recovery cost.
- **Итог:** **`ANALYSIS_ONLY / BENEFIT_UNPROVEN / NOT_PRODUCTION_APPROVED`**. Никаких реальных ALTER/CREATE/DROP, миграций на primary/standby или изменений рабочих проектов.

## Paper2Project — документальный анализ выполнен

Проверка проведена локально через `Paper2Project 1.0.2`, `job-b067e77b484a4dfa`; frozen research snapshot `1b74465aff661a3e3d20e2d11ea22804a3b9b95d9bfa9ce26c2ab30bf4b931e3`. Source-bound project snapshots: `AKUZ → 3ed7e5838ab24845d6184f9292aeef91bd7d177ba402c8c6d71616be6a2a8654`; `Wiki_PG → 5ae4aea3cea581dbddfadb469f036b2eebc744b8a005dc28808f246acaad89d4`. Analysis hash `1dd74e5c7340dd109eb810ec62629b53fd95f1dc15d4219974d7019d69d54440`.

- Оба проекта получили **`NEEDS_PROJECT_EVIDENCE`**, не `BENEFIT_DEMONSTRATED`. Исследование импортировано как `PROVIDED_TEXT_COMPLETENESS_UNATTESTED`, а не утверждение о полном аудите upstream.
- Подтверждены snapshot и точные source quotations, но автоматический evaluator оставил advisory `NEGATION_MISMATCH`, `CHECK_QUALIFIER_NEAR_QUOTE`, `POSSIBLE_CONDITION_OMISSION`. Это **не решённая** семантическая проверка: независимый reviewer обязан оценить, поддерживают ли цитаты сделанные выводы.
- Локальный Paper2Project selftest — **PASS**. Никаких сторонних бинарников, миграций, network-based models, реальной PostgreSQL-базы или production credentials не использовалось. A/B/C: **NOT_RUN**.
- Следующий stage: независимое DBA-рецензирование плана A/B/C, synthetic PostgreSQL 15/18 fixture, отдельное owner approval на выполнение в изолированном Podman; никаких схемных изменений на primary/standby.
