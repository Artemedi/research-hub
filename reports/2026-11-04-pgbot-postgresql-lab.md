# PostgreSQL / pgbot v0.9.0 — controlled diagnostic lab

**Дата эксперимента:** 2026-11-04 (Europe/Riga; фактические UTC timestamps в JSON за 2026-11-03).
**Статус:** `LAB_VERIFIED` для перечисленных сценариев; `HEAD_TO_HEAD_NOT_DONE` для Wiki_PG; `NO_PRODUCTION_APPROVAL`.
**Цель:** закрыть прежний статус `PGBOT_NOT_RUN` из [первого обзора](2026-11-03-bookmark-hypotheses-offline-experiments.md), не заменяя испытание инструмента авторскими заявлениями.

## Первичные материалы, версии, полномочия

- [pgbot upstream](https://github.com/pgrundev/pgbot/tree/826531fefd7d13b4381327acd4cce5be98bd71eb) — исходный код и тесты; лицензия Apache-2.0; [release v0.9.0](https://github.com/pgrundev/pgbot/releases/tag/v0.9.0).
- Исполняемый файл: `pgbot_0.9.0_linux_amd64.tar.gz`, SHA-256 `adf0f08fbdd212a8c6b1e0462f872916866968c25e6e35ba1b5bba22a39841bc`; скачан через `gh release download`, проверен `sha256sum -c`. Бинарник статически слинкован.
- Схема: `pgbot-context-1.5.0.json`, SHA-256 `2219364363668b57cba2c90eb03e7299e9c6b6b315605ba60aac61dc1f5c233b`.
- Лаборатория: Bazzite + Podman; локальный `postgres:18.3` (Debian); без сети (`--network none`), 512 MiB memory, 1 CPU, pids-limit=120. PostgreSQL доступен pgbot только через Unix socket *изнутри контейнера*. Production-подключений, внешних API и облачных LLM нет.
- Роль `pgbot_ro LOGIN`: `GRANT CONNECT ON DATABASE lab`, `GRANT pg_monitor`, **нет** grants на пользовательские таблицы. На уровне роли `default_transaction_read_only=on` и `statement_timeout=15000`. Session GUC не является write-protection boundary — таковой остаются grants.
- Параметры pgbot для управляемого опыта: `inspect --json --no-store --interval 500ms --window 1s --ash-hz 0 --fail-on none`. ASH sampler здесь выключен; вывод `--no-store` исключает сохранение baseline в локальную SQLite. `--fail-on none` используется, чтобы получить JSON и явно проверить finding IDs, а не принимать exit status за доказательство здоровья.

## Проверенные переходы и независимый oracle

| Состояние / вмешательство | Independent DB oracle | Реальный pgbot output | Итог |
| --- | --- | --- | --- |
| S0: 30 000 тестовых строк, 15 000 удалений в `vacuum_lab`, `autovacuum_enabled=false` | `pg_stat_user_tables.n_dead_tup=15000`, reloptions содержит отключение | `autovacuum_disabled_on_table` = **critical**, `table_bloat` = warn, blocked_count=0; 8 findings всего | PASS |
| S1: транзакция удерживает row lock; вторая UPDATE ожидает | `pg_blocking_pids()`: **1** блокируемая транзакция | `locks.blocked_count=1`, finding `blocking_chains` = **critical**; `activity --json` показал `Lock:transactionid` и `Timeout:PgSleep`; всего 9 findings | PASS |
| S2: оба сеанса завершились, `ALTER TABLE ... RESET (autovacuum_enabled)` и `VACUUM (ANALYZE)` | `n_dead_tup=0`, vacuum_count=1, blocked_count=0 | `blocking_chains`, `autovacuum_disabled_on_table`, `table_bloat` отсутствуют, 3 прочих findings остаются | PASS |
| S3: роль без `pg_monitor` | `no_monitor` имеет только CONNECT | `inspect` **не прерывается**; текстовый вывод предупреждает о неполных stats, а JSON содержит `server.has_pg_monitor=false`; при `--fail-on none` exit 0 | WARN: consumer must reject partial read |
| Контракт JSON | Официальная JSON Schema v1.5.0, библиотека `jsonschema` Draft 2020-12 | Все **4** JSON-состояния прошли валидацию | PASS |

Небезопасно считать `exit=0` достаточным условием подключения к агенту: для каждого JSON-ответа нужно требовать `server.has_pg_monitor === true` и проверять `schema_version`, а при `false` делать `ABSTAIN/PARTIAL_STATS`. Отсутствие `pg_monitor` не оформляется в данном JSON как обычная finding ID, поэтому проверять только массив `findings` недостаточно. Это поведение воспроизведено, **не объявлено дефектом upstream**: терминальный режим честно показывает предупреждение.

## Накладные расходы: ограниченный замер

Пять последовательных `inspect` в чистом S2, без других пользовательских запросов, на том же контейнере. Запуск включал `podman exec` (поэтому это **wall clock**, не чистое CPU-время PostgreSQL и не p95). Интервал сравнения счётчиков 500 мс; `--ash-hz 0`.

- Wall time: **620,2 / 617,9 / 620,9 / 618,8 / 621,4 мс**.
- **Медиана 620,2 мс**, n=5 (не производительный бенчмарк).
- `pg_stat_user_tables`, суммарные `n_tup_ins|n_tup_upd|n_tup_del`: `60000|2|15000` до и после серии, без роста.
- `fixture`: одинаковый `COUNT(*)` и MD5 агрегированных упорядоченных `id:value` до и после; проверка не утверждает отсутствие любого возможного IO/CPU overhead и не охватывает системные счётчики транзакций.
- Пять дополнительных JSON-ответов валидны по схеме, `server.has_pg_monitor=true`.

## Воспроизведение

Использовать только одноразовую локальную базу. Ниже — основные шаги, **без** обращения к AKUZ:

```bash
gh release download v0.9.0 -R pgrundev/pgbot \
  --pattern pgbot_0.9.0_linux_amd64.tar.gz
echo 'adf0f08fbdd212a8c6b1e0462f872916866968c25e6e35ba1b5bba22a39841bc  pgbot_0.9.0_linux_amd64.tar.gz' | sha256sum -c
tar xf pgbot_0.9.0_linux_amd64.tar.gz pgbot
chmod +x pgbot

podman run -d --name pgbot-isolated-lab --pull=never \
  --network none --memory 512m --cpus 1 --pids-limit 120 \
  -v "$PWD/pgbot:/usr/local/bin/pgbot:ro,Z" \
  -e POSTGRES_HOST_AUTH_METHOD=trust docker.io/library/postgres:18.3
# Дождаться pg_isready -U postgres (инициализация занимает несколько секунд).
podman exec pgbot-isolated-lab psql -U postgres -c 'CREATE DATABASE lab'
```

Подключившись к `lab` через `podman exec ... psql -U postgres -d lab`, применить:

```sql
CREATE ROLE pgbot_ro LOGIN;
GRANT CONNECT ON DATABASE lab TO pgbot_ro;
GRANT pg_monitor TO pgbot_ro;
ALTER ROLE pgbot_ro SET default_transaction_read_only=on;
ALTER ROLE pgbot_ro SET statement_timeout=15000;

CREATE TABLE public.fixture (id integer PRIMARY KEY, value text);
INSERT INTO public.fixture SELECT g, md5(g::text) FROM generate_series(1,30000) g;
CREATE TABLE public.vacuum_lab AS SELECT * FROM public.fixture;
ALTER TABLE public.vacuum_lab SET (autovacuum_enabled=false);
DELETE FROM public.vacuum_lab WHERE id <= 15000;
ANALYZE public.vacuum_lab;
```

Внутри контейнера вызвать `pgbot inspect 'host=/var/run/postgresql dbname=lab user=pgbot_ro' --json --no-store --interval 500ms --window 1s --ash-hz 0 --fail-on none`. Сохранить как `baseline.json`. Для блокировки использовать две отдельные psql-сессии, инициируя в первой `BEGIN; UPDATE public.fixture SET value=value WHERE id=1; SELECT pg_sleep(20); ROLLBACK;`, во второй — `UPDATE public.fixture SET value=value WHERE id=1;`. Во время ожидания получить `blocked.json`, затем дождаться завершения обоих сеансов. Далее `ALTER TABLE public.vacuum_lab RESET (autovacuum_enabled)`, отдельной командой `VACUUM (ANALYZE) public.vacuum_lab`; сохранить `fixed.json`. Для теста минимальных прав создать отдельную роль `no_monitor LOGIN`, выдать только CONNECT и получить `no-monitor.json` теми же опциями. Роль с trust-auth без сетевых интерфейсов подходит **только** для disposable lab. По окончании `podman rm -f pgbot-isolated-lab`.

Проверка ожидаемых переходов автоматизирована в [experiments/2026-11-04-pgbot-verify.py](../experiments/2026-11-04-pgbot-verify.py) (зависимость `jsonschema`; требует четыре JSON snapshot, официальную schema и `overhead.json` из пяти повторов). Сами snapshots не включены в архив, поскольку эксперименты должны независимо воспроизводиться; численные результаты выше фиксируют текущий запуск.

## Сопоставление с проектами и ограничения

- **Wiki_PG** ([source snapshot](https://github.com/Artemedi/Wiki_PG/tree/d55721bb99bff25fae352341cfd630c048693d6b)): только `PROJECT_PROFILE_MATCH`; комплексный Wiki_PG/Hermes MCP-агент **не запускался против этой же lab БД**. Исторические Wiki_PG benchmarks на других корпусах не являются head-to-head сравнениями. Рассматривать pgbot как независимый детерминированный evidence producer, если после исходниковых контрактных проверок нет дублирования уже существующих SQL probes.
- **sequential-rca**, **hermes-akuz-agents**: кандидаты по профилю, `NEEDS_SOURCE_CODE` для конкретного места интеграции; нельзя отправлять реальные логи/тексты запросов в LLM без контроля доступа.
- PostgreSQL 15.8, реплика, приоритеты PG role/pg_monitor, `pg_stat_statements`, `--ash-hz>0`, производительность на большом каталоге, race conditions, удалённый TLS, multi-DB и backup/restore **не проверены**. В лабе `archiving_disabled` остаётся warn по ожидаемой конфигурации, а `pg_stat_statements_missing` — info; не ошибочно трактовать как production findings.
- Отсутствует независимый DBA oracle для ложноположительных результатов на >30 разных инцидентах. Нет p95 и измерения реального overhead CPU/IO на production-подобной нагрузке.
- **Решение:** `KEEP_AS_CANDIDATE / LAB_VERIFIED / INTEGRATION_BLOCKED`. Дальнейшее испытание: отдельная PostgreSQL 15/18 test-площадка с минимум 30 размеченными сценариями, direct SQL/Wiki_PG/pgbot на **одинаковых** снимках; precision, recall, false positives, recovery, p95, max connections, IO, secrets exposure, version drift. Любая автоматическая коррекция отклоняется до отдельного human gate.

## Границы изменений

Тестовый контейнер удалён. Опубликованы только документы и верификатор; SQL-объекты, роли и DDL существующих баз, код Wiki_PG, downstream skills, deployment и Issues не менялись. Новые документы связаны с project-registry без перезаписи предыдущего отчёта.
