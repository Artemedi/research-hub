# Agent Error Dataset — соответствие проектам (08.11.2026)

- HEAD приватного реестра: b3af154278a8724230185cba6b1898a106a4f25a; прочитано и хешировано карточек PROJECT.md: **45/45**.
- Источник: [Agent Error Dataset arXiv v2](https://arxiv.org/html/2609.40111v2); SHA-256 полного HTML: 31af8d0a1d4da3a4c4184def8fed7e6f76a6483005804f0868133b682d7aab14.
- Область: только профильный triage. Тексты приватных карточек и приватный код не копировались. Внедрение и production approval не подразумеваются.
- [Предметная проверка и synthetic A/B](../../reviews/agent-error-dataset/2026-11-08-checkpoint-replay-ab.md) · [машинная матрица](../../data/project-fit/agent-error-dataset/2026-11-08-project-fit.json)

## Shortlist

| Project ID | Основание по профилю | Граница доказательств |
|---|---|---|
| sequential-rca | Профиль sequential RCA и replay-oriented workflow ближе всего к trace-grounded failure diagnosis. | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE; точный adapter и чистая source seam не подтверждены. |
| dsh-runtime | Agent runtime владеет session checkpoint и tool-result recovery. | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE; unknown external outcome нельзя превращать в automatic side-effect retry. |
| akuz-issue | Цепочка incident evidence → root cause → remediation → control подходит для хранения diagnosis и validation evidence. | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE; проект не исполняет agent actions. |

## Сводка профильных решений

| Решение | Количество |
|---|---:|
| SHORTLIST | 3 |
| CONDITIONAL_NEEDS_EVIDENCE | 9 |
| NO_CURRENT_FIT | 17 |
| REFERENCE_NO_TARGET | 14 |
| CONTROL_PLANE_REFERENCE | 1 |
| NOT_EVALUATED | 1 |

## Все 45 профилей

| Project ID | Решение | Основание по профилю |
|---|---|---|
| AKUZ | NO_CURRENT_FIT | DBA/application operations; профиль не определяет владельца agent trace/replay. |
| Wiki_PG | CONDITIONAL_NEEDS_EVIDENCE | PostgreSQL DBA-автоматизация и диагностический retrieval смежны, но профиль не задаёт agent-owned checkpoint/replay contract. |
| akuz-issue | SHORTLIST | Цепочка evidence → root cause → remediation → control подходит для хранения trace-cited diagnosis и replay evidence; проект не исполняет agent actions. |
| akuz-optimizer-twin | NO_CURRENT_FIT | Fidelity optimizer/statistics не относится к диагностике agent actions и checkpoint replay. |
| akuz-schema-inventory | NO_CURRENT_FIT | Инвентаризация схем и зависимостей не содержит пути коррекции agent actions. |
| akuzlogparser | NO_CURRENT_FIT | Парсинг логов и отчётность не владеют коррекцией или replay agent actions. |
| psqlqa | REFERENCE_NO_TARGET | Сторонний анализатор планов; нет собственного agent replay target. |
| sequential-rca | SHORTLIST | Профиль sequential RCA и replay-oriented workflow напрямую соответствуют trace-grounded diagnosis; точный AED adapter не подтверждён. |
| 9router | NO_CURRENT_FIT | Маршрутизация provider/model не диагностирует ошибки действий и не владеет task checkpoints. |
| Harness | CONDITIONAL_NEEDS_EVIDENCE | Integration probes и recovery смежны, но immutable trace и независимый replay oracle не подтверждены. |
| HermesAgent | CONDITIONAL_NEEDS_EVIDENCE | Agent/tool execution смежны; профиль не подтверждает checkpoint-grounded diagnosis/correction contract. |
| TencentDB-Agent-Memory | REFERENCE_NO_TARGET | Сторонний memory reference; не собственный agent replay или incident evidence target. |
| agent-config | NO_CURRENT_FIT | Конфигурация и hooks не владеют trace-grounded diagnosis/replay. |
| agent-skills | CONDITIONAL_NEEDS_EVIDENCE | Skill может описывать процедуру review, но не может независимо подтвердить provenance trace или итоговое состояние. |
| bitvec-dsh | NO_CURRENT_FIT | Представление latent state не является workflow восстановления по action trace. |
| claude-code-docs | REFERENCE_NO_TARGET | Документационный reference, не владелец исполнения или evidence. |
| deepseek-harness | REFERENCE_NO_TARGET | Upstream reference; собственный runtime учитывается отдельно. |
| dsh-claude-primary-agent | CONDITIONAL_NEEDS_EVIDENCE | Интеграция agent SDK может предоставлять traces, но checkpoint-replay contract не подтверждён. |
| dsh-runtime | SHORTLIST | Agent runtime владеет session checkpoint и tool-result recovery; follow-up обязан сохранять unknown external outcome и запрещать automatic side-effect retry. |
| dsh-team-context | CONDITIONAL_NEEDS_EVIDENCE | Управляемый context/evidence смежен, но это не action executor и не replay authority. |
| dsh | CONTROL_PLANE_REFERENCE | Decision/governance control plane; не владелец agent execution/replay. |
| free-router | REFERENCE_NO_TARGET | Legacy routing reference; нет agent trace recovery target. |
| hermes-akuz-agents | CONDITIONAL_NEEDS_EVIDENCE | Multi-agent DBA automation смежна, если владеет failed-action traces и изолированным replay; этот контракт пока не установлен. |
| teamai-cli | REFERENCE_NO_TARGET | Reference для распространения skills/governance, не agent replay executor. |
| TelegramBot | NO_CURRENT_FIT | Scheduled automation/video workflow не соответствует scope agent failure replay. |
| TrinMedicalBot | NO_CURRENT_FIT | Профиль medical assistant не определяет владельца general tool-failure replay; медицинские данные и клинические claims не использовались. |
| confluence-wiki-backups | NO_CURRENT_FIT | Backup/restore не относится к диагностике и replay agent actions. |
| wiki-tasks | CONDITIONAL_NEEDS_EVIDENCE | Persistent task state/recovery смежны, но trace-grounded diagnosis и independent replay не подтверждены. |
| MyPartyIsGrinding | NO_CURRENT_FIT | Game-mod workflow не имеет соответствующего agent failure-replay target. |
| MyWiki | NO_CURRENT_FIT | Knowledge/wiki scope не подтверждает agent execution или checkpoint replay. |
| WarOfGenesisIdleLoot | NO_CURRENT_FIT | Game-mod workflow не имеет соответствующего agent failure-replay target. |
| anastasia-wiki-bot | DEFERRED (profile NOT_EVALUATED) | В текущем профиле недостаточно подтверждённых сведений, чтобы классифицировать agent trace/replay workflow. |
| concept-loom-desktop | NO_CURRENT_FIT | Learning/coach application не определяет agent action replay. |
| game-localization-guide | NO_CURRENT_FIT | Localization guidance не относится к agent failure diagnosis/replay. |
| MS-SQL | REFERENCE_NO_TARGET | Сторонний SQL reference, не собственный agent recovery target. |
| Postgres14book | REFERENCE_NO_TARGET | Книга/reference fork, не agent execution target. |
| SQL-Server-First-Responder-Kit | REFERENCE_NO_TARGET | Сторонний diagnostic toolkit; нет собственного agent trace-replay workflow. |
| SQLServerTools | REFERENCE_NO_TARGET | Сторонний maintenance toolkit, не agent replay target. |
| gitignore | REFERENCE_NO_TARGET | Reference templates не имеют agent execution/replay surface. |
| sqlserver-kit | REFERENCE_NO_TARGET | Сторонний SQL reference toolkit, не agent replay target. |
| tigertoolbox | REFERENCE_NO_TARGET | Сторонний DBA toolbox, не владелец agent action replay. |
| uuid-vs-auto-increment | REFERENCE_NO_TARGET | Сторонний index benchmark, не относится к trace-grounded agent recovery. |
| dsh-paper2agent | CONDITIONAL_NEEDS_EVIDENCE | Source/citation analysis может сохранять provenance diagnosis, но проект не владеет runtime action replay. |
| paper2agent-index | NO_CURRENT_FIT | Derived research index, не agent execution/replay target. |
| developer-safe-dotnet-core | NO_CURRENT_FIT | Domain/persistence API safety не относится к agent trace diagnosis/replay. |

## Интерпретация

- Все 45 PROJECT.md прочитаны на текущем registry HEAD и хешированы. Публичная матрица содержит только IDs, SHA карточек и обобщённые основания; тела приватных карточек и приватный код не публикуются.
- Три shortlist — соответствие по профилю, не проверенные integration seams. Проектная польза и end-to-end integration не измерялись.
- В разрешённом разделе связанных исследований трёх приватных карточек backlinks на Agent Error Dataset уже есть. Нового соответствия не возникло; project-registry не менялся.
- Ни исходники проектов, ни production database, ни пользовательские данные, ни deployment не изменялись. Авторские результаты остаются AUTHOR_REPORTED; synthetic lab не является научной репликацией.
