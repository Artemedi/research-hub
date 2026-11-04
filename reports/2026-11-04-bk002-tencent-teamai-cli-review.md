# Telegram BK-002 — Tencent TeamAI CLI: исходный код, fork divergence и применимость к портфелю

**Проверка:** 2026-11-04. **Исходный Telegram-пункт:** BK-002 / 08.09.2026, приоритет A. **Пользовательский исход:** `Добавлен в карточки` (только после подтверждения backlinks в registry). **Состояние доказательности:** `SOURCE_REVIEWED / PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE / LAB_NOT_RUN / NO_PRODUCTION_APPROVAL`.

## 1. Что именно является источником

Это **инженерное ПО**, не рецензируемая научная статья. Обязательное full-text правило применено к [полной официальной документации](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/docs/product-overview.md), [руководству по распространению ресурсов](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/docs/guide/distribution.md), [исходному коду](https://github.com/Tencent/teamai-cli/tree/7ed698998da8e446d8116c79ae58a9d5ff6ca016/src) и тестовым файлам. Не заменено пресс-релизом или рекламным abstract.

- **Официальный upstream:** [Tencent/teamai-cli@7ed698998da8e446d8116c79ae58a9d5ff6ca016](https://github.com/Tencent/teamai-cli/tree/7ed698998da8e446d8116c79ae58a9d5ff6ca016), commit от 2026-11-04. Текущий `package.json` содержит `0.22.0`, но **SHA, не строка version**, определяет проверенный код. MIT.
- **Собственный fork:** [Artemedi/teamai-cli@5a3c371f692675b6e080a6554af5a3da0752fe5c](https://github.com/Artemedi/teamai-cli/tree/5a3c371f692675b6e080a6554af5a3da0752fe5c), commit от 2026-09-14. Не путать форк с актуальным upstream.
- **Общая база:** `a3f0b6f6c5d314e0ba0d0a02de4c6e984fede55e` по `git merge-base` после догрузки истории. Проверены реальные локальные Git objects, не API-оценка популярности.

## 2. Функциональность, подтверждённая исходным кодом

| Возможность | Фактический источник | Интерпретация |
| --- | --- | --- |
| Версионированный Git-набор skills/rules/hooks/MCP/agents и распределение в разные AI tools | [product overview](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/docs/product-overview.md) и [distribution mechanism](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/docs/guide/distribution.md) | Проверено как задокументированный архитектурный контракт; многопользовательское E2E не запускалось |
| Обновление team repo, версии и short-circuit при недавнем обновлении | [src/pull.ts:165–260](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/src/pull.ts#L165-L260) | Код допускает изменения локальной копии и доставку в инструмент; не read-only клиент |
| Декларируемый `scripts.postPull` исполняется при pull, path ограничен clone | [src/post-pull.ts:57–115](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/src/post-pull.ts#L57-L115) | **Доверенная execution boundary**: path containment не заменяет review самого скрипта; безопасность репозитория-поставщика критична |
| Управление Codex hooks | [src/codex-team-hooks.ts:198–245](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/src/codex-team-hooks.ts#L198-L245) | При управляемой установке может менять `~/.codex/hooks.json`; нельзя пробовать на действующем рабочем профиле |
| Pin team ref и автоматическая синхронизация ресурсов/хуков | [docs/guide/distribution.md](https://github.com/Tencent/teamai-cli/blob/7ed698998da8e446d8116c79ae58a9d5ff6ca016/docs/guide/distribution.md) | Pin к commit/tag ограничивает дрейф; `--team-ref` и границы совместимости надо проверить E2E |

**Возможная польза:** воспроизводимая доставка политик и skills между несколькими средами, централизованный review/PR, меньше ручных симлинков. **Не доказано:** снижение числа ошибок, уменьшение latency/tokens, безопасность реального деплоя, экономия сопровождения. Возникают накладные Git fetch, файловые записи, зависимости Node, дополнительные хуки и более широкая область доверия. Раздача hooks/MCP/скриптов автоматически может изменить поведение инструментов в нескольких проектах.

## 3. Что фактически добавлено в Artemedi fork

Сравнивались **не два HEAD простым file diff**, а ветви относительно общего предка.

- От `a3f0b6f6...` до fork: **13 уникальных коммитов**, **13 изменённых файлов**, `+1742/-94` строк. Основное — собственный read-only адаптер DSH Team Context, контракт и тесты.
- Upstream к моменту проверки ушёл вперёд на **732 коммита**, включая архитектурное развитие `src/pull.ts`, `src/resources/skills.ts`, `src/source.ts`, `src/types.ts`.
- **Сухой 3-way merge**, без изменения рабочих файлов, показал **6 content conflicts**: `docs/usage-guide.md`, `docs/usage-guide.zh-CN.md`, `src/pull.ts`, `src/resources/skills.ts`, `src/source.ts`, `src/types.ts`. Это реальный blocker для простого fast-forward/rebase; конфликты нужно разрешать и проверять, но это **не доказательство runtime defect**.
- [src/team-context.ts:146–189](https://github.com/Artemedi/teamai-cli/blob/5a3c371f692675b6e080a6554af5a3da0752fe5c/src/team-context.ts#L146-L189) валидирует `team-context.yaml`, schemaVersion и неизвестные поля **до** применения снапшота.
- [src/team-context.ts:264–316](https://github.com/Artemedi/teamai-cli/blob/5a3c371f692675b6e080a6554af5a3da0752fe5c/src/team-context.ts#L264-L316) содержит policy: при коллизии локальный skill побеждает; stale copy удаляется по manifest; governance заменяется авторитетным блоком.
- [src/team-context.ts:342–389](https://github.com/Artemedi/teamai-cli/blob/5a3c371f692675b6e080a6554af5a3da0752fe5c/src/team-context.ts#L342-L389) поддерживает cached best-effort fetch, `dryRun` и сохранение manifest после materialize. [src/pull.ts:1701–1711](https://github.com/Artemedi/teamai-cli/blob/5a3c371f692675b6e080a6554af5a3da0752fe5c/src/pull.ts#L1701-L1711) вызывает адаптер из общего pull. [Дизайн](https://github.com/Artemedi/teamai-cli/blob/5a3c371f692675b6e080a6554af5a3da0752fe5c/docs/designs/dsh-team-context-v1.md) ограничивает v1 read-only `skills/` и `governance/`, без публикации обратно в canonical provider.

**Trust trade-off:** в дизайне fork всё под `skills/` и `governance/` канонического provider доверено без дополнительного allowlist; это осознанное решение, **не автоматически уязвимость**, но требует контроля прав публикации и аудита supply chain. `governance` нельзя локально перекрыть; при недоступности provider оставляют предыдущее состояние. Отдельный threat model нужен для rollback и компрометации репозитория поставщика.

## 4. Project-fit: проверены все 45 существующих PROJECT.md

Три наиболее предметных соответствия:

| Конкретный проект | Подтверждённый контекст | Fit / доказательство | Ограничение и ближайшая проверка |
| --- | --- | --- | --- |
| **[dsh-team-context](https://github.com/Artemedi/dsh-team-context)** | [Architecture@373ba695:21–51](https://github.com/Artemedi/dsh-team-context/blob/373ba695512052753b1a9eb2183bac30ea795016/docs/architecture.md#L21-L51): владеет skills/governance, отделён от runtime; fork TeamAI уже читает этот контракт | `PROJECT_PROFILE_MATCH / VERIFIED_FORK_CONSUMER / NEEDS_EVIDENCE` | Из-за 732 upstream-коммитов и 6 merge conflicts **не** заявлять новую версию совместимой; нужна проверка контракта `schemaVersion`, fail-closed и local-wins |
| **[agent-skills](https://github.com/Artemedi/agent-skills)** | [README@163d928:8–34](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/README.md#L8-L34): ручная установка skills симлинками и отсутствие автоматической синхронизации | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` | TeamAI мог бы раздавать skills на несколько машин, но ценность относительно нынешнего symlink+Git не измерена; не менять локальную Codex-конфигурацию до изолированного A/B |
| **[teamai-cli](https://github.com/Artemedi/teamai-cli)** | Имеет **собственные** изменения `src/team-context.ts` и `src/pull.ts` относительно Tencent; не просто зеркало | `REFERENCE_FORK / SOURCE_DIFF_VERIFIED / REBASE_BLOCKED_BY_CONFLICTS` | Это reference и объект сопровождения, а не доказанный runtime target. Нужны 6 diff resolutions и проверка нового API, если владелец решит актуализировать fork |

**Остальные 42 карточки** изучены на уровне Research-to-Project профиля и не получили backlinks: не найдено столь же прямого контура или воспроизводимой необходимости. Перечень по доменам (не код-аудит каждой реализации):

- DBA/AKUZ (8): AKUZ, Wiki_PG, akuz-issue, akuz-optimizer-twin, akuz-schema-inventory, akuzlogparser, psqlqa, sequential-rca — TeamAI не является SQL/IO/RCA методом; опосредованная доставка skills не даёт конкретного измеренного DBA эффекта.
- Другие агентные (13): 9router, Harness, HermesAgent, TencentDB-Agent-Memory, agent-config, bitvec-dsh, claude-code-docs, deepseek-harness, dsh, dsh-claude-primary-agent, dsh-runtime, free-router, hermes-akuz-agents — потенциальные downstream потребители, но текущие данные не дают более сильного и уникального integration seam, чем выбранные три; `agent-config` остаётся дополнительным кандидатом на следующий triage.
- Автоматизации (4): TelegramBot, TrinMedicalBot, confluence-wiki-backups, wiki-tasks — предметные failure modes относятся к публикации, workflow и состоянию, а не к массовой раздаче TeamAI skills.
- Персональные/игровые (6): MyPartyIsGrinding, MyWiki, WarOfGenesisIdleLoot, anastasia-wiki-bot, concept-loom-desktop, game-localization-guide — нет достаточно подтверждённого управляемого многоагентного rollout.
- Внешние референсы (8): MS-SQL, Postgres14book, SQL-Server-First-Responder-Kit, SQLServerTools, gitignore, sqlserver-kit, tigertoolbox, uuid-vs-auto-increment — не управляемые downstream targets.
- Независимые исследования (2): dsh-paper2agent, paper2agent-index — другой исследовательский контракт, автоматическая раздача команд не доказывает improvement.
- Проект коллеги (1): developer-safe-dotnet-core — предоставлен brief без доступного кода, `NEEDS_SOURCE_CODE`; нет source-confirmed TeamAI seam.

## 5. Измеримый следующий эксперимент (НЕ выполнялся)

**Human gate обязателен.** Две одноразовые рабочие области в изолированной Linux/Node среде, без доступа к `~/.agents`, `~/.codex`, `~/.claude`, пользовательскому `~/.ssh` и реальным TeamAI/MCP токенам. Фиктивные репозитории и dummy skills; локальный git server или bare repo; без hooks/scripts с внешним действием.

- **Baseline A:** нынешние `agent-skills` + явный Git update и симлинк; **B:** оригинальный TeamAI на pinned commit и **отдельный** fork adapter с явным `team-context.yaml` v1. Сравнивать честно одинаковый набор команд и scope `project/user`.
- **Oracle:** manifest с ожидаемыми SHA256 каждого доставленного `SKILL.md`/rules/governance файла, точными путями, отсутствием неожиданной записи; детерминированные тесты idempotent pull, local override, rename/deletion, corruption/version mismatch, offline, concurrent fetch, conflicting policy, rollback. Малый mutation test для некорректного schemaVersion должен остановить обновление.
- **Метрики:** успешная доставка/конфликт/непреднамеренная перезапись по 5 повторениям, p50/p95 elapsed, network bytes, disk IO, peak RSS, число hooks/scripts/external tools, время ручного восстановления. Нужен заранее зафиксированный target acceptance (например, **0 незапрошенных записей** и **0 невыявленных конфликтов**) и верхний бюджет IO/CPU.
- **Отдельная ветка fork-upgrade:** разрешить конфликты в disposable worktree, сборка TypeScript, тесты fork contract, upstream targeted E2E + независимая проверка доставки. Не менять работающие агенты и не запускать publish. Точность merge и script trust важнее скорости доставки.
- **Trade-offs:** удобство многомашинной синхронизации против новых Node зависимостей, hook execution surface, merge debt, риска переписать локальные config, большего числа Git/sync I/O. Для одного пользователя на одной машине замена симлинков может оказаться **YAGNI**.

**Execution:** статическая проверка исходников, Git history и dry merge — `VERIFIED_STATIC`; `npm install`, `npm test`, `teamai init/pull`, hooks, runtime benchmark и production интеграция **NOT_RUN**. `LAB_VERIFIED` и `PRODUCTION_APPROVED` не назначены.

## 6. Решение

**Пригоден для исследовательской привязки**, поэтому `Добавлен в карточки` для трёх конкретных проектных профилей. Ветку `Artemedi/teamai-cli` нельзя автоматически объявить устаревшей функцией, но её **не следует обновлять вслепую**: 732 новых upstream-коммита и 6 конфликтов требуют отдельной адаптации и offline validation. Не подменять «source reviewed» доказанным multi-agent effect.

Полный исходный Telegram список и остальные статусы ведутся отдельно в [матрице BK-001…BK-065](2026-11-04-telegram-bookmarks-reconciliation.md). Новое исследование не добавляет Telegram ID и не меняет старые записи вне BK-002.
