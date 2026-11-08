# CERA-MoA — актуальная матрица применимости к 45 проектам

**Дата:** 2026-11-08. **Registry HEAD:** `b3af154278a8724230185cba6b1898a106a4f25a`. Инвентаризировано **45/45** `PROJECT.md`; 44 решения опубликованы, один внешний профиль намеренно `NOT_EVALUATED`, чтобы не раскрывать частные сведения. Первоисточник: [CERA-MoA arXiv v1](https://arxiv.org/html/2609.18779v1), SHA-256 `13f6536287ff7ebec0a21663f4d21fc61ce05c82d14ab14448f4080bed18bf0f`.

## Итог

**`NO_FIT / NO_CURRENT_TARGET`** — shortlist пуст. Из 45 профилей 44 получили публичную оценку: `29` собственных/прикладных — `NO_CURRENT_FIT`, `15` внешних fork, legacy/reference и derived-index карточек — `REFERENCE_NO_TARGET`; один профиль оставлен `NOT_EVALUATED` по ограничению конфиденциальности.

Ближайшие технические смежности не стали fit:

- `bitvec-dsh` — hidden-state extraction и trainable reader→generator bridge, но нет population of LoRA specialist policies или CERA router.
- `9router` — provider/API routing; opaque providers не раскрывают hidden states и weights.
- `dsh-runtime` — agent/tool orchestration, не model-training/serving backend.

Их текущие source revisions и узкий scope просмотра перечислены в [machine-readable matrix](../../data/project-fit/cera-moa/2026-11-08-project-fit.json). Наличие кода/тестов в `bitvec-dsh` не доказывает совместимость метода; тесты проекта в этом проходе не запускались. Остальные проекты оценены по профилям, без утверждения о просмотре их исходников.

## Полная матрица

| Project ID | Decision | Evidence | Причина |
|---|---|---|---|
| `AKUZ` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | DBA, diagnostics или SQL knowledge workload; отсутствует multi-agent trainable LLM backend. |
| `Wiki_PG` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | DBA, diagnostics или SQL knowledge workload; отсутствует multi-agent trainable LLM backend. |
| `akuz-issue` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | DBA, diagnostics или SQL knowledge workload; отсутствует multi-agent trainable LLM backend. |
| `akuz-optimizer-twin` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | DBA, diagnostics или SQL knowledge workload; отсутствует multi-agent trainable LLM backend. |
| `akuz-schema-inventory` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | DBA, diagnostics или SQL knowledge workload; отсутствует multi-agent trainable LLM backend. |
| `akuzlogparser` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | DBA, diagnostics или SQL knowledge workload; отсутствует multi-agent trainable LLM backend. |
| `psqlqa` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `sequential-rca` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | DBA, diagnostics или SQL knowledge workload; отсутствует multi-agent trainable LLM backend. |
| `9router` | `NO_CURRENT_FIT` | `PROFILE_AND_SOURCE_REVIEW` | Маршрутизация запросов к внешним провайдерам не даёт доступа к hidden states, весам или обучению экспертов. |
| `Harness` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Test/evaluation harness может измерять систему, но не владеет hidden-state model backend и LoRA policies. |
| `HermesAgent` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Конфигурация/agent layer поверх провайдеров; нет контроля model weights, hidden states и совместного RL/LoRA training. |
| `TencentDB-Agent-Memory` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `agent-config` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Конфигурация/agent layer поверх провайдеров; нет контроля model weights, hidden states и совместного RL/LoRA training. |
| `agent-skills` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Конфигурация/agent layer поверх провайдеров; нет контроля model weights, hidden states и совместного RL/LoRA training. |
| `bitvec-dsh` | `NO_CURRENT_FIT` | `PROFILE_AND_SOURCE_REVIEW` | Есть hidden-state extraction и trainable bridge, но задача reader→generator transfer не соответствует multi-LoRA specialist routing. |
| `claude-code-docs` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `deepseek-harness` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `dsh` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Control/knowledge plane, не модельный training/serving backend. |
| `dsh-claude-primary-agent` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Primary-agent SDK delegation; модель и её внутренние состояния остаются внешним сервисом. |
| `dsh-runtime` | `NO_CURRENT_FIT` | `PROFILE_AND_SOURCE_REVIEW` | Runtime управляет agent/tool execution, но не владеет trainable model backend, LoRA adapters или hidden-state extraction. |
| `dsh-team-context` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Knowledge/context retrieval plane не является trainable inference backend и не владеет весами specialist policies. |
| `free-router` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `hermes-akuz-agents` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Конфигурация/agent layer поверх провайдеров; нет контроля model weights, hidden states и совместного RL/LoRA training. |
| `teamai-cli` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `TelegramBot` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Automation/application/configuration layer без контроля trainable model weights и hidden states. |
| `TrinMedicalBot` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Конфигурация/agent layer поверх провайдеров; нет контроля model weights, hidden states и совместного RL/LoRA training. |
| `confluence-wiki-backups` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Wiki/backup/knowledge storage не является trainable inference backend. |
| `wiki-tasks` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Automation/application/configuration layer без контроля trainable model weights и hidden states. |
| `MyPartyIsGrinding` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Игровой/localization проект не содержит задачи multi-agent model training или hidden-state routing. |
| `MyWiki` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Wiki/backup/knowledge storage не является trainable inference backend. |
| `WarOfGenesisIdleLoot` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Игровой/localization проект не содержит задачи multi-agent model training или hidden-state routing. |
| `anastasia-wiki-bot` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Automation/application/configuration layer без контроля trainable model weights и hidden states. |
| `concept-loom-desktop` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Automation/application/configuration layer без контроля trainable model weights и hidden states. |
| `game-localization-guide` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Игровой/localization проект не содержит задачи multi-agent model training или hidden-state routing. |
| `MS-SQL` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `Postgres14book` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `SQL-Server-First-Responder-Kit` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `SQLServerTools` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `gitignore` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `sqlserver-kit` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `tigertoolbox` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `uuid-vs-auto-increment` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `dsh-paper2agent` | `NO_CURRENT_FIT` | `PROFILE_TRIAGE_ONLY` | Исследовательский paper-to-agent инструмент; не исполняемый multi-agent model-training backend. |
| `paper2agent-index` | `REFERENCE_NO_TARGET` | `PROFILE_TRIAGE_ONLY` | Внешний fork, legacy/reference или derived index; не собственный trainable inference target. |
| `developer-safe-dotnet-core` | `NEEDS_EVIDENCE` | `NOT_EVALUATED` | Публичная оценка не выполнялась; частные сведения не воспроизводятся. |


## Граница решения

CERA-MoA требует контролируемый self-hosted backend: промежуточные hidden states, несколько trainable LoRA/adapters, RL training loop, held-out benchmark и существенный GPU budget. Наличие API-router, agent orchestration, memory/retrieval или bridge training само по себе не удовлетворяет этому контракту.

**Никаких backlinks в приватный `project-registry` не добавлялось:** при `NO_FIT` обратные ссылки запрещены. Ни один project source, production workload или private card не изменялся.
