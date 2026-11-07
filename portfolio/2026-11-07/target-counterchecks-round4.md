# Контрпроверки IV: совет ZCode по цитированию и реальный MCP SQL security path

**Дата:** 07.11.2026. Продолжение [предыдущей ограниченной лабораторной проверки](target-counterchecks-round3.md), исходный хаб `55d6cd5`. Проверяются только инженерные интерфейсы на синтетических данных. Нет новых первоисточников, полнотекстовых научных обзоров, разрешений на внедрение или изменения project-fit.

## 1. dsh-paper2agent — чистый исходник + совет против независимого oracle

**Источник:** `Artemedi/dsh-paper2agent@6d82a42175a71d3327b773df88f1da0707efe43c` (`origin/main`, сверено с удалённым ref); точный SHA-256 `src/paper2project/core.py`: `95ea03c7fabbc586ac29e073f16ab5a6e1b5c10b8388f619afec4d3125e6ee79`. Воспроизводимый скрипт выгружает эту ревизию через `git archive` в временный каталог, **не читает** незакоммиченные изменения из рабочей копии.

**Сквозной ограниченный вызов:** реальный `App.import_projects` → `App.import_research` → `App.create_job` → `App.submit_analysis` в отдельном `TemporaryDirectory`; созданный исследователем oracle содержит шесть синтетических исходных предложений и 36 производных утверждений. Категории: exact, корректная переформулировка, противоречие, ошибочное число, ошибочный субъект, нерелевантное утверждение. Все цитаты ссылаются на настоящую допустимую строку и проектную строку; **истинность rationale не следует из структурной валидности цитаты**.

| Стратегия | Структурно принято | Автоматически принято из 12 поддержанных | Ложно принято из 24 неподтверждённых |
| --- | ---: | ---: | ---: |
| A: текущий `submit_analysis` | **36/36** | не семантический классификатор | не семантический классификатор |
| B: внешний exact-only auto-pass | н/п | **6/12**; ещё 6 парафраз отложены | **0/24** |
| C: ZCode GLM-5.3-Flash, одна роль | н/п | **12/12** | **0/24** |
| D: совет из двух независимых ролей той же модели, единогласный auto-pass | н/п | **12/12** | **0/24** |

**Фактически исполненный рой:** шесть пакетов × два последовательных model calls = **12/12 COMPLETE, 0 BLOCKED**, физическая конкуренция 1; checkpoint после каждого вызова. Роли `grounded_reviewer` и `adversarial_falsifier` были слепы к авторским меткам и друг другу, однако использовали **одну модельную семью** — это не статистически независимые oracle. Все 36 результатов ролей совпали, несогласий не было. Ответы проверены на полный набор ID и enum; при ошибке модельный пакет не получает PASS. Инструменты и приватные сведения в модель не передавались.

**Ресурсные наблюдения:** совокупное время вызовов 139,52 с, медиана 11,04 с на один шестикейсовый batch-role call; 4 874 reported input tokens, 5 034 output tokens, 11 520 cache-read input tokens. Это не стоимость в деньгах, не SLA и не head-to-head latency benchmark: внешнему exact-only сравнению модельные вызовы не требовались. Модельная достоверность **не экстраполируется** с специально составленных 36 простых утверждений на реальные scientific claims, косвенные доказательства, многодокументные цитаты, медицинские статьи, защищённые данные или длинные контексты.

**Решение:** `ACCEPT_BOUNDED_SYNTHETIC_COUNCIL_AB`; `REWORK_REAL_HELDOUT_SEMANTIC_GATE`; `NO_PROJECT_MODIFICATION`. Следующий oracle: легальные полные тексты с независимой разметкой claim ↔ цитата, реальные неоднозначные парафразы и отрицательные контролы, recall/precision/abstention и сравнение токенов/времени с одинаковым бюджето́м. До этого semantic auto-approval закрыт.

## 2. MCP Toolbox v1.15.0 — настоящий stdio, SQL/роль/namespace/timeout

**Источник:** официальный бинарник `MCP Toolbox v1.15.0`, SHA-256 `f6fac005c39898a379523700727a2a3d0a2828f579bec22cc0efe74e0652062d`; проверен после полной загрузки, извлечён и запущен внутри disposable rootless `postgres:18` (image ID `79061104669bb30919d015b549c764e2d8021a18ee39cb175581a2588fe90dbe`). `--network none`, 0 опубликованных портов, 0 host mounts, 2 CPU / 1 GiB, синтетические учётные данные, только `observer` с ограниченными grants. Через **реальный MCP stdio** и `ClientSession` вызваны ровно 3 фиксированных инструмента, нет общего `execute_sql`.

**11/11 контролей прошли:**

- `get_safe_setting`: `SELECT ... FROM pg_catalog.pg_settings WHERE name = $1` вернул реальное `max_connections=100`, хотя `observer.search_path=shadow,pg_catalog` и неуточнённый `pg_settings` возвращал подложное `999999`. Это проверенный end-to-end отрицательный namespace-контроль, **не** только заявление по исходнику.
- Шесть разных неправильных/SQL-injection строк переданы именно как **bind-параметр**, не вызвали DDL или изменённого результата.
- `explain_planner`: пользовательская `IMMUTABLE`-функция с `pg_sleep(0.30)` при `EXPLAIN` прервана ролью `statement_timeout=80ms`; MCP вернул `is_error` с timeout (наблюдаемое время вызова **81,07 мс**).
- `explain_volatile`: `EXPLAIN` без `ANALYZE` успешен (~0,99 мс); позднее `REVOKE EXECUTE` запретил вызов `IMMUTABLE` через сам MCP.
- После ошибок MCP-сессия продолжила выдавать корректный GUC; `observer` не смог вставить запись в fixture, счётчик оставался `1/1`.

**Ограничения:** этот A/B подтверждает поведение только **явно фиксированного allowlist**; нельзя объявлять доказанную безопасность произвольных SQL от агента, неправильных raw tool configs, привилегированных расширений, SQL из чужих источников и сетевого HTTP MCP listener. Startup Toolbox выдаёт предупреждения о wildcard hosts/origins; в данном **stdio/без network** эксперименте HTTP endpoint не публиковался. Сам `pgbot` и целевые интеграции `Wiki_PG`, `sequential-rca`, `hermes-akuz-agents` не запускались.

**Модельная критика:** ZCode `security_falsifier` вернул `ACCEPT_BOUNDED`, но частично неверно описал реальный shadow `search_path` контроль; его предложение вызвать `EXPLAIN ANALYZE` через фиксированные безопасные инструменты несовместимо с их контрактом и могло бы выполнить запрос, поэтому **не принято**. `methodology_critic` истёк по лимиту 50 секунд: `BLOCKED_PROVIDER`, а не голос согласия. Совет не заменяет 11 фактических независимых SQL/MCP оракулов.

**Решение:** `ACCEPT_NARROW_MCP_BOUNDARY`, `NO_GENERAL_AGENT_SQL_APPROVAL`. Следующее: настоящее средство маршрутизации SQL из соответствующего целевого проекта на **изолированном** PostgreSQL, source-pinned allowlist, ролевое разграничение, негативные тесты SQL AST, неверные tool descriptions и обработка ошибок; затем отдельно тесты отказоустойчивости и наблюдаемости.

## Репликация и артефакты

| Проверка | Исполняемый сценарий | Машинные результаты |
| --- | --- | --- |
| Clean-source citation + ZCode council | [скрипт](../../experiments/research-portfolio/2026-11-07-zcode-citation-council-ab.py) | [36 cases, 12 roles, hashes и usage](../../data/results/research-portfolio/2026-11-07-zcode-citation-council-ab.json) |
| MCP Toolbox security + direct SQL oracle | [скрипт](../../experiments/research-portfolio/2026-11-07-toolbox-mcp-security-ab.py) | [11 end-to-end контролей](../../data/results/research-portfolio/2026-11-07-toolbox-mcp-security-ab.json) |
| ZCode advisory critics | [скрипт](../../experiments/research-portfolio/2026-11-07-toolbox-security-critics.py) | [одна завершённая роль, один timeout](../../data/results/research-portfolio/2026-11-07-toolbox-security-critics.json) |

Вход в ZCode: только public synthetic fixtures; никакие исходные private `PROJECT.md`, пациенты, production SQL, пароли или реальные документы не передавались. Временные данные и модельные checkpoints оставлены только на исследовательской машине; в хабе публикуются лишь безопасные агрегаты/verdicts и идентификаторы. Бинарник и контейнер не коммитятся. Задания model tools не создают. Для воспроизведения нужны штатная авторизованная локальная ZCode-обёртка, `P2P_SOURCE` с Git ref, rootless Podman, локально проверенный Toolbox binary и Python MCP SDK.

**Итог:** `ACCEPT_BOUNDED_EVIDENCE` для двух target/lab экспериментов, `REWORK` для научной семантики цитирования и произвольного агентного SQL, `NO_NEW_FIT`, `NO_PRODUCTION_APPROVAL`. Нельзя обобщать успешные synthetic проверки на production. Следующий независимый gate — эксплуатационные failure-injection у `Claude Swarm` и настоящий held-out corpus из полных легальных источников.
