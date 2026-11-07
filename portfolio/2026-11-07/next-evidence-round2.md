# Следующий пакет проверок: источники и независимые лабораторные оракулы

**Дата:** 07.11.2026. **Объём:** `Hyperresearch`, `pgbot`, `Claude Swarm` и `MCP Toolbox` после [массового разбора 31 карточки](mass-swarm-review.md). Все проверки выполнены вне production, на закреплённых источниках. [Итоговая экспертиза предыдущего этапа](senior-review.md).

Задача нового этапа — не повторить логические задания ZCode, а закрыть конкретные пробелы воспроизводимыми проверками. Семь `BLOCKED` прошлой очереди имеют самостоятельные исторические обзоры; их отказы модели не являются основанием удалять ранее подтверждённые результаты.

## Проверенные результаты

| Объект и исходник | Эксперимент и независимый oracle | Измерено | Диспозиция |
| --- | --- | --- | --- |
| [Hyperresearch @aece65f](https://github.com/jordan-gibbs/hyperresearch/blob/aece65f9307197119629beacf8aeaf8cc80e999a/src/hyperresearch/core/citecheck.py#L257-L328) | Реальный `triage_pairs` из pinned code + 125 синтетических пар цитата/утверждение, помеченных независимым oracle | 25/25 exact positive приняты; **75/100** заведомо неподтверждённых примеров ошибочно получили `supported-mechanical`; консервативный exact-only gate — **0/100** ложных auto-pass на этом корпусе | **`REWORK_MECHANICAL_CITATION_GATE`**, не публиковать неподтверждённые цитаты по шести словам overlap |
| [pgbot @826531f — `plan/fetch.go`](https://github.com/pgrundev/pgbot/blob/826531fefd7d13b4381327acd4cce5be98bd71eb/internal/plan/fetch.go) | SQL, эквивалентный EXPLAIN-only plan fetch, в disposable PostgreSQL 18.6 `BEGIN READ ONLY`; функция `IMMUTABLE` против `VOLATILE` и `pg_sleep` | `IMMUTABLE` вызвал `RAISE NOTICE` во время планирования; оба контроля не вызвались | **`PLAN_ONLY_IS_NOT_ZERO_FUNCTION_EXECUTION`**; семантика безопасности зависит от доверенного SQL и роли |
| [Claude Swarm @31f1919](https://github.com/cj-vana/claude-swarm/tree/31f19199bf3557cda4860231186a06b72c8edb94) | Оригинальная сборка TypeScript + upstream Vitest в rootless Node 22 без сети во время тестов | **107/107 PASS**, три файла тестов; `manager.ts` по умолчанию задаёт `bypassPermissions` | **`UTILITY_TESTS_PASS / LIVE_WORKERS_NOT_TESTED`**; no production adoption |
| [MCP Toolbox v1.15.0](https://storage.googleapis.com/mcp-toolbox-for-databases/v1.15.0/linux/amd64/toolbox) | Реальный MCP `stdio` и фиксированный bind SQL `SELECT ... FROM pg_settings WHERE name = $1` против независимого PostgreSQL 18 SQL oracle | **30/30** GUC совпали; 3 негативных имени не выполнили DDL; `observer` не смог записать фикстуру, строк осталось 1 | **`NARROW_PARAMETERIZED_TOOL_PASS`**; только тест одного read-only инструмента |

Числа false auto-pass для Hyperresearch относятся **только к специально составленному стресс-корпусу**: 25 базовых высказываний × 5 версий (точная, противоречащая, другой объект, явное отрицание, нерелевантная). Это не prevalence на реальных научных статьях и не оценка последующего LLM cite checker. Консервативная альтернатива уменьшает риск молчаливого принятия, но отправляет больше перефразированных положительных высказываний на дорогой и медленный LLM review.

`pgbot` проверен на уровне **семантики PostgreSQL**, а не запуском его бинарника в этом конкретном тесте. Код `plan/fetch.go` вызывает `ReadOnlyTx` и `SimpleQuery` для `EXPLAIN (FORMAT JSON)`, а пользовательская `IMMUTABLE` функция с `RAISE NOTICE` исполнилась при constant folding. Это не доказательство исполнения всей SELECT, записи данных либо привилегий superuser. Но слова «никакой пользовательский код не выполняется» неверны как абсолютная граница. Требуется database least privilege и явная политика допустимых функций. Планирование — не security sandbox.

`Claude Swarm` прошёл реальный upstream `tsc` и Vitest: `prompt-templates.test.ts` (46), `confidence.test.ts` (40), `git-verification.test.ts` (21). Эти тесты **не** испытывают worker manager, два одновременных worktree, tmux, потерю lock или отказ во время replay. В [manager.ts](https://github.com/cj-vana/claude-swarm/blob/31f19199bf3557cda4860231186a06b72c8edb94/src/workers/manager.ts) исходное значение `CLAUDE_SWARM_PERMISSION_MODE` — `bypassPermissions`, а worker tools включают `Bash,Read,Write,Edit,Glob,Grep`. Успешная сборка не отменяет этот риск; для `dsh-runtime` и `dsh-claude-primary-agent` следующий gate — изолированный E2E с отказами, реальными правами и rollback.

`MCP Toolbox` испытан официальным бинарником с зафиксированным SHA-256: `f6fac005c39898a379523700727a2a3d0a2828f579bec22cc0efe74e0652062d`. Role `observer` имела только CONNECT/чтение каталога; после `BEGIN READ WRITE` попытка INSERT в `fixture` отклонена из-за недостаточных grants, а не только `default_transaction_read_only`. Медиана 30 последовательных MCP вызовов — **0,826 мс**: это локальный stdio micro-observation без warmup, конкуренции и production SLA. В startup логе имеются предупреждения о wildcard allowed-hosts/origins, но HTTP listener в эксперименте не публиковался. При расширении до HTTP нужно явно ограничить адреса и аутентификацию.

## Соответствие портфелю и трейдоффы

| Направление | Проекты для предметной проверки | Выгода / цена / блокер |
| --- | --- | --- |
| Citations из Hyperresearch | `agent-skills`, `dsh-paper2agent` | Можно убрать автоматический false positive, но дополнительные LLM-проверки увеличат задержку, токены и непредсказуемость без независимого oracle |
| PostgreSQL plan-only через pgbot | `Wiki_PG`, `sequential-rca`, `hermes-akuz-agents` | Планирование обычно дешевле исполнения, но остаются CPU planner, каталожный IO и возможные вычисления IMMUTABLE; нужны ограниченные GRANT и negative controls |
| Claude Swarm workers | `dsh-claude-primary-agent`, `dsh-runtime`, `wiki-tasks` | Параллельность требует дополнительных процессов, RAM, worktree IO и координации; политика bypassPermissions несовместима с прямым production rollout |
| MCP Toolbox live GUC | `Wiki_PG` | Дополняет исторические snapshots актуальным read-only источником; отдельный процесс/MCP и соединение повышают сложность и эксплуатационные издержки |

**Новые `FIT_APPROVED` / production approvals: 0.** Эти исследования относятся к прошлому `documented_candidate`, новой проверке механики и лабораторным ограничениям. Никакой код целевых проектов не изменён.

## Воспроизведение и доказательные файлы

| Эксперимент | Воспроизводимый скрипт | Сохранённый результат |
| --- | --- | --- |
| Hyperresearch | [fixture](../../experiments/research-portfolio/2026-11-07-hyperresearch-citation-ab.py) | [125 кейсов](../../data/results/research-portfolio/2026-11-07-hyperresearch-citation-ab.json) |
| pgbot | [Podman/SQL](../../experiments/research-portfolio/2026-11-07-pgbot-explain-plan-probe.py) | [три контроля](../../data/results/research-portfolio/2026-11-07-pgbot-explain-plan-probe.json) |
| Claude Swarm | оригинальные `npm run build` / `npm test` | [build/test provenance](../../data/results/research-portfolio/2026-11-07-claude-swarm-upstream-tests.json) |
| MCP Toolbox | [MCP/SQL](../../experiments/research-portfolio/2026-11-07-toolbox-30-settings.py) | [30 GUC + 3 negative](../../data/results/research-portfolio/2026-11-07-toolbox-30-settings.json) |

Исходный код и репозитории закреплены commit IDs, реальные результаты содержат SHA документа/исполняемого файла и ограничения. Публичные отчёты не содержат сырой исходный код сторонних проектов, секреты и полные научные статьи. Во всех контейнерах экспериментальная PostgreSQL была изолирована через `--network none` и удалена после завершения.

**Решение:** `ACCEPT_BOUNDED_EVIDENCE` для четырёх лабораторных пакетов, `REWORK` по конкретным найденным рискам, `NO_NEW_PROJECT_FIT`, `NO_PRODUCTION_APPROVAL`.
