# Agent Mosaic — project fit (2026-11-07)

- Registry HEAD: 838b86a28fcaa3440eeddbe147b6188e0d177963; PROJECT.md cards read: **45**.
- Source: [Agent Mosaic arXiv v1](https://arxiv.org/html/2610.30418v1); full HTML SHA-256: 80b01bba9c64a4bee86dec3badaccc39e8e801121c0610544affb5e67cfe190a.
- Scope: profile-level triage across all 45 cards. Private card bodies were not copied. No target implementation or production behavior is approved.
- The three shortlisted IDs are candidates only; all remain PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE until a pinned source seam and a project-specific synthetic workload are independently verified.
- Machine-readable companion: [45-card JSON matrix](../../data/project-fit/agent-mosaic/2026-11-07-composite-gate.json). Its `decision` is the canonical assessment state; `profile_decision` preserves the profile-level category, including explicit `NOT_EVALUATED`.

## Decision counts

| Decision | Count |
|---|---:|
| SHORTLIST | 3 |
| CONDITIONAL_NEEDS_EVIDENCE | 8 |
| NO_CURRENT_FIT | 17 |
| REFERENCE_NO_TARGET | 14 |
| CONTROL_PLANE_REFERENCE | 1 |
| NOT_EVALUATED | 2 |

## Full 45-project matrix

| Project ID | Decision | Evidence | Rationale |
|---|---|---|---|
| AKUZ | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Смешанная DBA/application база; в профиле нет agentic cross-document answer boundary. |
| Wiki_PG | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Hybrid retrieval и MCP смежны, но профиль не задаёт защищённые cross-source отношения или модель классификации; требуется конкретный workload и source audit. |
| akuz-issue | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Incident evidence и DBA playbooks; профиль не показывает agent runtime, выпускающий ответы из нескольких закрытых источников. |
| akuz-optimizer-twin | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Локальный optimizer twin решает fidelity статистик/планов, а не confidentiality в agent synthesis. |
| akuz-schema-inventory | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Read-only schema inventory и dependency graphs; нет agentic final-output boundary. |
| akuzlogparser | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Streaming log parsing/reporting; не multi-document LLM output path. |
| psqlqa | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний fork анализатора планов; нет собственного downstream agent output boundary. |
| sequential-rca | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Offline RCA workflow; в профиле нет агентного synthesis boundary. |
| 9router | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Provider/model routing не классифицирует содержание и не контролирует итоговый текст. |
| Harness | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Интеграционная probe-область подходит для будущего synthetic test, но не является владельцем final-answer enforcement. |
| HermesAgent | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Gateway/tool configuration смежна с исследованием, но конфигурация не равна runtime output gate; live результат авторов не переносится на текущую установку. |
| TencentDB-Agent-Memory | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний memory reference; не собственный runtime и не владелец выпуска ответа. |
| agent-config | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Prompt/hook rules могут быть одним слоем защиты, но авторские результаты показывают остаточное раскрытие при headers/rules; самостоятельный enforcement не доказан. |
| agent-skills | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Skills могут задавать правила, но не обеспечивают детерминированный контроль финального текста. |
| bitvec-dsh | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Latent-state bridge и обучение; не относится к cross-source disclosure enforcement. |
| claude-code-docs | REFERENCE_NO_TARGET | REFERENCE_ONLY | Архив документации, не исполняемый agent runtime. |
| deepseek-harness | REFERENCE_NO_TARGET | REFERENCE_ONLY | Upstream tracking reference; собственный runtime выделен отдельно. |
| dsh | CONTROL_PLANE_REFERENCE | PROFILE_TRIAGE_ONLY | Control-plane governance и owner approvals полезны для gate процесса, но не являются runtime enforcement point. |
| dsh-claude-primary-agent | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Agent SDK integration может оказаться runtime boundary, но профиль не подтверждает cross-document retrieval или provenance contract. |
| dsh-runtime | SHORTLIST | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE | Агентный runtime и tool orchestration — вероятная точка enforcement на выпуске ответа; конкретный output hook на текущем исходнике не закреплён. |
| dsh-team-context | SHORTLIST | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE | Контур governed knowledge/retrieval — возможный владелец source labels и provenance; финальный ответ выпускает runtime, а claim-level gate пока не подтверждён. |
| free-router | REFERENCE_NO_TARGET | REFERENCE_ONLY | Legacy routing reference; маршрутизация провайдера не контролирует композицию содержимого. |
| hermes-akuz-agents | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Multi-agent handoff создаёт потенциальный путь накопления фактов, но профиль не документирует source labels, clearance или output gate. |
| teamai-cli | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний fork синхронизации знаний/rules; не собственный output gate. |
| TelegramBot | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Scheduled video publication; нет конфиденциального agent retrieval/output workload. |
| TrinMedicalBot | SHORTLIST | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE | Медицинский assistant profile с внешним retrieval: риск композиционного раскрытия прямо релевантен, но это профиль, а не runtime; клинические данные и production не использовались. |
| confluence-wiki-backups | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Backup/restore repository; целостность резервных копий не является agent answer-release control. |
| wiki-tasks | CONDITIONAL_NEEDS_EVIDENCE | PROFILE_TRIAGE_ONLY | Persistent memory/task state смежны с накоплением фактов, но защищённый multi-source corpus и final-output owner не подтверждены. |
| MyPartyIsGrinding | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Game modification project; нет соответствующего agentic confidential corpus. |
| MyWiki | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Личная offline wiki; профиль не подтверждает agentic multi-source answer pipeline. |
| WarOfGenesisIdleLoot | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Game modification project; нет соответствующего agentic confidential corpus. |
| anastasia-wiki-bot | NOT_EVALUATED | NOT_EVALUATED | Назначение проекта в профиле не подтверждено; без source evidence fit не оценивается. |
| concept-loom-desktop | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Learning/coach application; профиль не задаёт защищённый multi-document knowledge boundary. |
| game-localization-guide | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Localization workflow; не agentic confidential synthesis. |
| MS-SQL | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний набор SQL-скриптов; нет agentic cross-document answer path. |
| Postgres14book | REFERENCE_NO_TARGET | REFERENCE_ONLY | Fork книги; справочный материал, не runtime. |
| SQL-Server-First-Responder-Kit | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний diagnostic kit; не agentic retrieval/output owner. |
| SQLServerTools | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний maintenance toolkit; нет multi-source agent boundary. |
| gitignore | REFERENCE_NO_TARGET | REFERENCE_ONLY | Справочные шаблоны ignore; не agent runtime. |
| sqlserver-kit | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний SQL reference toolkit; нет agentic output path. |
| tigertoolbox | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний Microsoft toolbox; не agent runtime. |
| uuid-vs-auto-increment | REFERENCE_NO_TARGET | REFERENCE_ONLY | Сторонний benchmark по индексам; предметно не связан с composite disclosure. |
| dsh-paper2agent | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Исследовательский paper-to-agent инструмент; не runtime, обрабатывающий защищённые пользовательские источники. |
| paper2agent-index | NO_CURRENT_FIT | PROFILE_TRIAGE_ONLY | Derived index; не самостоятельный agent runtime или output enforcement layer. |
| developer-safe-dotnet-core | NOT_EVALUATED | NOT_EVALUATED | В карточке нет Research-to-Project профиля и доступного source snapshot; оценка не выполнялась. |

## Shortlist interpretation

- TrinMedicalBot: domain-level confidentiality risk candidate only; no patient/clinical records were used and no clinical quality claim is made.
- dsh-team-context: candidate for source labels/provenance in the knowledge plane; it does not itself own final answer release.
- dsh-runtime: candidate for a deterministic output-release gate; no source-level integration hook was verified in this run.

Wiki_PG, HermesAgent, agent-config, agent-skills, Harness, dsh-claude-primary-agent, hermes-akuz-agents, and wiki-tasks remain conditional, not shortlisted. Their profiles describe adjacent retrieval/configuration/orchestration concerns, but not a verified claim-level confidentiality contract.

No project source code was changed. No private PROJECT.md body text, source code, credentials, or production data was copied into this public report.
