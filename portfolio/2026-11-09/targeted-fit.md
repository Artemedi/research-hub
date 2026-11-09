# Targeted research-to-project applicability: executable test proposals

2026-11-09. Pinned private project-registry source commit: 421268e5c60fd1b5f37bd69a84b923ff28ce3e86. 45 profiles checked for existence; no private text published.

This is a candidate decision matrix, NOT measured improvement, code integration, author-paper replication or permission to deploy. A verified symbol only means the named function exists in the named pinned Git object.

Scope: 75 candidate pairs (63 source-symbol anchored, 12 profile-only); all 40 ACCEPT_BOUNDED reviewed (2 deferred), and 18 selected research-only works.

## Two source feasibility checks actually executed

- **TelegramBot / exactly-once-limbo:** [original source function mock replay](../../data/results/research-portfolio/2026-11-09-telegram-ack-fixture.json) observed 2 remote effects after commit+lost ACK+retry, versus 1 with normal ACK or failure before commit. This is a baseline defect boundary only; no outbox improvement or network request was executed.
- **agent-config / source citation:** [original check_findings function replay](../../data/results/research-portfolio/2026-11-09-agentconfig-quote-fixture.json) returned location_ok=true and evidence_found=true for a quote that exists elsewhere in the file but not at its declared line. This tests diagnostic fields; it does NOT establish downstream automatic acceptance or remote exploit.

## P0: first source-anchored experiments

| Study | Project | Consumer symbol at repo@SHA | Hypothesis | A/B |
| --- | --- | --- | --- | --- |
| agent-mosaic | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Запретить публикацию вывода, если claim основан на неразрешённом источнике. | [citation](#citation) |
| agent-mosaic | dsh-team-context | [src/core/scoped-recall.ts:73](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/scoped-recall.ts#L73) | Сохранять source scope в retrieved evidence до итогового ответа. | [retrieval](#retrieval) |
| agent-risk | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Различать доказанное нарушение политики и голословное замечание ревьюера. | [citation](#citation) |
| agent-risk | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Повторно оценивать риск изменений runtime по воспроизводимой сцене до merge. | [replay](#replay) |
| drag | Wiki_PG | [Wiki_PG/ingestion/retrieval_service.py:402](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/retrieval_service.py#L402) | Не ускорять ответы ценой ложных ссылок при OOD изменениях формата и подложной информации. | [retrieval](#retrieval) |
| exactly-once-limbo | TelegramBot | [main.py:187](https://github.com/Artemedi/TelegramBot/blob/a838ca6671cada5307825d3b5c433ce7083e1e76/main.py#L187) | Сократить дубли отправок на неоднозначном Telegram ACK, признавая окно неустранимой неопределённости. | [delivery](#delivery) |
| htn-orchestrate | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Сравнить fixed DAG с HTN под одинаковым бюджетом и отказами worker. | [dag](#dag) |
| mcp-toolbox-postgres | Wiki_PG | [Wiki_PG/ingestion/mcp_wiki_server.py:391](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/mcp_wiki_server.py#L391) | Сверить MCP read с прямыми pg_settings на одинаковом фиксированном snapshot. | [sql](#sql) |
| novafabric | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Обеспечить точную сверку offline agent tool replay без утверждения о полной изоляции побочных эффектов. | [replay](#replay) |
| novafabric | sequential-rca | [src/sequential_rca/review.py:81](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/review.py#L81) | Сопоставить audit artifact с исходным report/trace в отдельном изолированном запуске. | [replay](#replay) |
| veriharness | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Отвергать proof snippet вне заявленного файла/строки, сохраняя корректные findings. | [citation](#citation) |
| veriharness | dsh-paper2agent | [src/paper2project/core.py:137](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L137) | Не считать цитату доказательством без проверки идентичности источника и контекста. | [citation](#citation) |
| harnesssecurity-bench | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Раздельно измерять корректность задачи и запрещённый side effect. | [security](#security) |
| paper2agent | dsh-paper2agent | [src/paper2project/core.py:39](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L39) | Отклонять paper→tool bundle без исходника, лицензии и воспроизводимого версии кода. | [source_pin](#source_pin) |
| poisoned-skills | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Не подчинять reviewer исполняемой инструкции внутри внешнего SKILL.md. | [security](#security) |
| sequential-diagnosis-language-models | TrinMedicalBot | [eval/clinical_review.py:151](https://github.com/Artemedi/TrinMedicalBot/blob/5c32b51e007cf6486482b2aa96c6bce39f5412ac/eval/clinical_review.py#L151) | Оценивать последовательный клинический дифференциал только экспертно и без PHI. | [medical](#medical) |

## Remaining bounded-research candidate interfaces

| Study | Project | Source seam | Effect hypothesis | A/B |
| --- | --- | --- | --- | --- |
| agent-error-dataset | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Восстанавливать безопасный ход по журналу действий и обнаруживать неполные tool outcomes. | [replay](#replay) |
| alphaxiv-openresearch | dsh-paper2agent | [src/paper2project/core.py:39](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L39) | Восстановить точную версию статьи и исходника после удаления исходной рабочей папки. | [source_pin](#source_pin) |
| benchshield | dsh-paper2agent | [src/paper2project/core.py:137](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L137) | Не принимать заявленное улучшение на неподтверждённом score/trace. | [citation](#citation) |
| cursor-token-efficiency | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Уменьшить input schema context при сохранении выбора обязательных инструментов. | [routing](#routing) |
| decision-geometry-harness | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Сравнить строгую схему review evidence с текущей на одинаковых synthetic policy decisions. | [security](#security) |
| decision-geometry-harness | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Проверить, меняет ли форма tool schema фактический выбор разрешённого инструмента. | [routing](#routing) |
| dsh-creator-mode | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Проверять формат создаваемого skill/tool bundle до публикации, без запуска произвольного кода. | [skills](#skills) |
| dsh-superagent-prototype | dsh-claude-primary-agent | [src/session-binding.ts:3](https://github.com/Artemedi/dsh-claude-primary-agent/blob/625355078dc99ad04f347e8096f7f702ba4cb965/src/session-binding.ts#L3) | Не считать новый task завершённым при потере session binding. | [dag](#dag) |
| dsh-superagent-prototype | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Сопоставить Ticket lifecycle и допустимые действия с реальными session permissions. | [dag](#dag) |
| experienceindex | Wiki_PG | [Wiki_PG/ingestion/retrieval_service.py:402](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/retrieval_service.py#L402) | Хранить проверяемое source id и путь документа при retrieval top-k. | [graph](#graph) |
| experienceindex | dsh-team-context | [src/core/scoped-recall.ts:73](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/scoped-recall.ts#L73) | Увеличить точность ссылок на первичные документы при сохранении scoped recall. | [graph](#graph) |
| goal-aware-dynamic-collaboration | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Снизить нарушения зависимостей при параллельной работе с инструментами. | [dag](#dag) |
| gpt6-astra-skills-prompts | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Сравнить загрузку минимального review contract с полным на одних offline задачах. | [skills](#skills) |
| gpt6-astra-skills-prompts | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Сократить нерелевантные skill tokens, не теряя обязательных проверок. | [skills](#skills) |
| harness2 | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Выбирать проверяющего только по отдельному holdout, не по первому удачному seed. | [experiment](#experiment) |
| inspektor-gadget | Wiki_PG | [Wiki_PG/scripts/health_report.py:201](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/scripts/health_report.py#L201) | Разделить наблюдаемый I/O/proc event и неподтверждённое утверждение о причине. | [diagnostics](#diagnostics) |
| inspektor-gadget | sequential-rca | [src/sequential_rca/evaluate.py:133](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/evaluate.py#L133) | Добавлять проверенный Linux eBPF event к причине RCA без корреляционной ошибки. | [diagnostics](#diagnostics) |
| ipfire-fireperf | sequential-rca | [src/sequential_rca/evaluate.py:133](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/evaluate.py#L133) | Потреблять только отдельно снятые latency/refusal данные без собственного нагрузочного трафика. | [diagnostics](#diagnostics) |
| karpathy-autoresearch | Wiki_PG | [Wiki_PG/ingestion/retrieval_service.py:402](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/retrieval_service.py#L402) | Разделить гиперпараметры retrieval benchmark и неизменяемый набор проверочных query. | [experiment](#experiment) |
| karpathy-autoresearch | dsh-paper2agent | [src/paper2project/core.py:151](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L151) | Проводить source-pinned эксперимент и отвергать gain только на train subset. | [experiment](#experiment) |
| local-knowledge-graph | sequential-rca | [src/sequential_rca/evaluate.py:133](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/evaluate.py#L133) | Не выдавать ориентированный causal edge за двунаправленную подтверждённую причинность. | [graph](#graph) |
| microsoft-skill-recorder | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Не превращать внешнюю запись с чувствительным текстом в skill без предварительной проверки. | [privacy](#privacy) |
| open-steps | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Не считать отсутствие Git tracked diff доказательством отсутствия изменений в untracked files. | [skills](#skills) |
| pgbot | sequential-rca | [src/sequential_rca/evaluate.py:133](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/evaluate.py#L133) | Передавать PG health snapshots с явным age/staleness и без прямого подключения к production. | [diagnostics](#diagnostics) |
| rrsi | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Не продвигать model prompt/guard по тренировочному oracle без separate holdout. | [experiment](#experiment) |
| simurg | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Проверять алерты на agent/tool traces с количественным false alarm контролем. | [diagnostics](#diagnostics) |
| tencent-teamai-cli | dsh-team-context | [src/core/scoped-recall.ts:73](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/scoped-recall.ts#L73) | Тестировать локальный import/handoff skills без произвольного сетевого доступа. | [skills](#skills) |
| toolgrad | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Сверять шаги навыка с внешним oracle, а не с self-reported success. | [skills](#skills) |
| toolgrad | dsh-paper2agent | [src/paper2project/core.py:151](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L151) | Не использовать нулевой count ошибок как доказательство фактической корректности цепочки tools. | [experiment](#experiment) |
| understand-anything | dsh-team-context | [src/core/scoped-recall.ts:73](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/scoped-recall.ts#L73) | Не смешивать path traversal/symlink source с разрешёнными документами проекта. | [graph](#graph) |
| vercel-agent-desktop | psqlqa | [pg_query_analyzer/app.py:41](https://github.com/Artemedi/psqlqa/blob/b2e09ff24b06f3b7a92f7cf353cd3473c2a94aea/pg_query_analyzer/app.py#L41) | Оценить доступность GUI для изолированного read-only audit, не активируя действия с реальной БД. | [visual](#visual) |
| warp-skill-doctor | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Не объединять skill invocation traces от одноимённых, но чужих проектов. | [skills](#skills) |
| yahont-ce | Wiki_PG | [Wiki_PG/ingestion/retrieval_service.py:402](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/retrieval_service.py#L402) | Не допускать неявного alias разных документов после нормализации search ID. | [identity](#identity) |
| youtube-skills | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Пропускать непроверенный transcript/provider output только как untrusted data. | [skills](#skills) |
| agent-error-dataset | akuz-issue | PROFILE ONLY — source seam not verified | Привязать причину и ремедиацию к неизменному incident evidence и различать fail от неизвестного состояния. | [replay](#replay) |
| chartli | akuz-schema-inventory | PROFILE ONLY — source seam not verified | Проверять машинную корректность SVG-графиков по снимкам схемы, не превращая оценку SQL cost во время выполнения. | [visual](#visual) |
| cursor-token-efficiency | HermesAgent | PROFILE ONLY — source seam not verified | Динамическая передача только нужных tool schemas без ложного исключения доступных функций. | [routing](#routing) |
| exactly-once-limbo | HermesAgent | PROFILE ONLY — source seam not verified | Не повторять необратимое tool действие без durable result reconciliation. | [delivery](#delivery) |
| goal-aware-dynamic-collaboration | hermes-akuz-agents | PROFILE ONLY — source seam not verified | Разграничить агентские handoff и обязательные DBA prerequisites. | [dag](#dag) |
| htn-orchestrate | hermes-akuz-agents | PROFILE ONLY — source seam not verified | Не запускать зависимые DBA шаги до завершения проверяемых prerequisite. | [dag](#dag) |
| julia-1 | dsh-runtime | PROFILE ONLY — source seam not verified | Показывать допустимые candidate-route вероятности без подмены их откалиброванным confidence. | [routing](#routing) |
| pgbot | Wiki_PG | PROFILE ONLY — source seam not verified | Не путать недоступный snapshot PostgreSQL statistics с доказательством отсутствия vacuum проблемы. | [pg_health](#pg_health) |
| simurg | 9router | PROFILE ONLY — source seam not verified | Не переводить аномальный provider response в автоматическое переключение модели без явного safety policy. | [diagnostics](#diagnostics) |
| zero-code | agent-config | PROFILE ONLY — source seam not verified | Парсить JSONC по строгим правилам дублированных ключей до policy admission. | [jsonc](#jsonc) |

## Selected method-only research candidates

| Study | Project | Source seam | Effect hypothesis | A/B |
| --- | --- | --- | --- | --- |
| harnesssecurity-bench | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Раздельно измерять корректность задачи и запрещённый side effect. | [security](#security) |
| paper2agent | dsh-paper2agent | [src/paper2project/core.py:39](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L39) | Отклонять paper→tool bundle без исходника, лицензии и воспроизводимого версии кода. | [source_pin](#source_pin) |
| poisoned-skills | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | Не подчинять reviewer исполняемой инструкции внутри внешнего SKILL.md. | [security](#security) |
| sequential-diagnosis-language-models | TrinMedicalBot | [eval/clinical_review.py:151](https://github.com/Artemedi/TrinMedicalBot/blob/5c32b51e007cf6486482b2aa96c6bce39f5412ac/eval/clinical_review.py#L151) | Оценивать последовательный клинический дифференциал только экспертно и без PHI. | [medical](#medical) |
| behavior-beyond-text | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Сравнить слова отказа с реально разрешёнными side effects инструмента. | [security](#security) |
| concordat | dsh-claude-primary-agent | [src/session-binding.ts:3](https://github.com/Artemedi/dsh-claude-primary-agent/blob/625355078dc99ad04f347e8096f7f702ba4cb965/src/session-binding.ts#L3) | Проверить typestate допустимости resume/cancel вне prompt-only соглашений. | [dag](#dag) |
| covert-assistance | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Обнаруживать попытки незадекларированного делегирования при source review. | [security](#security) |
| maadbench | sequential-rca | [src/sequential_rca/evaluate.py:133](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/evaluate.py#L133) | Отличать первичную ошибку RCA от downstream каскада неверных выводов. | [diagnostics](#diagnostics) |
| matoi | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Проверять предупреждения о последствиях без подмены authority на side effect. | [security](#security) |
| memory-centric-continual-learning | dsh-team-context | [src/core/knowledge-index.ts:327](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/knowledge-index.ts#L327) | Различать recall score и изменённую истину memory по датированным источникам. | [retrieval](#retrieval) |
| memscope | dsh-team-context | [src/core/scoped-recall.ts:73](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/scoped-recall.ts#L73) | Локализовать memory regression на frozen corpus и отделять repair от retrieval noise. | [retrieval](#retrieval) |
| package-hallucination-rule-files | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Не повышать рекомендацию пакета из untrusted repository rules до разрешённой установки. | [security](#security) |
| recap | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Сравнить сохранение критичного evidence после context compression с обычной длинной сессией. | [routing](#routing) |
| silent-cue-loss | dsh-paper2agent | [src/paper2project/core.py:39](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L39) | Отмечать потерянное оформление DOCX как missing-evidence, не выдавая plain text за полный источник. | [docx_styles](#docx_styles) |
| statecomp | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Не сокращать agent state без проверки сохранения важных source constraints. | [routing](#routing) |
| transferable-tool-selection | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | Проверить plan→retrieve→select против direct tool choice при frozen tool contracts. | [routing](#routing) |
| trust-region-injection | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | Разграничить неверифицированный текст источника и исполняемую system policy. | [security](#security) |
| concordat | developer-safe-dotnet-core | PROFILE ONLY — source seam not verified | Проверить проектные Door, Guard и Handed Port контракты через отрицательные compilation witnesses; без доступа к исходникам коллеги это пока только гипотеза. | [typestate_dotnet](#typestate_dotnet) |
| swrouter | 9router | PROFILE ONLY — source seam not verified | Сравнить multi-turn routing с последним turn-only выбором без живого изменения провайдеров. | [routing](#routing) |

## Deliberately deferred bounded studies

- **cera-moa**: No own trainable adapter/model candidate or held-out routing corpus verified; author LoRA/MoA results cannot be directly attached to API-only agents.
- **rea**: No justified binary/managed artifact reconstruction task with a documented owner-maintained consumer; psqlqa potential is a weak profile guess, not a validated integration seam.

## Proposed offline paired experiments (NOT executed)

### citation

**Baseline:** Current target quote/path checks. **Variant:** Typed claim→source-span and effect-authority guard.
**Dataset:** 80 synthetic claims, 30 supported / 50 forged, sealed 20-case holdout. **Independent oracle:** Independent file/line/authorization gold.
**Metrics:** False auto-allow, valid coverage, p95. **Acceptance criterion:** 0 false auto-allow; valid coverage >= baseline; p95 <=1.25x.
**Negative controls:** correct quote wrong line; real text fake source; injected untrusted instruction.

### retrieval

**Baseline:** Existing unmodified top-k retrieval. **Variant:** Provenance graph or strict evidence-aware candidate ranking.
**Dataset:** 60 frozen query-document cases incl. 15 OOD. **Independent oracle:** Independent source ID and exact range labels.
**Metrics:** Recall@5, wrong-source citations, p95. **Acceptance criterion:** Recall@5 >= baseline; 0 wrong-source evidence; p95 <=1.25x.
**Negative controls:** stale indexed source; forged link; wrong tenant same phrase.

### replay

**Baseline:** Existing trace or source-only log. **Variant:** Versioned input/output and state capsule with replay guard.
**Dataset:** 40 synthetic episodes + 12 crash/partial/tamper cases. **Independent oracle:** Independent state/output hash and effect ledger.
**Metrics:** Replay exactness, tamper detection, overhead. **Acceptance criterion:** 40/40 deterministic match; 12/12 mutants rejected; no unrecorded effects.
**Negative controls:** mutated source SHA; truncated trace; ack lost after effect.

### dag

**Baseline:** Existing sequential or fixed DAG controller. **Variant:** Dependency-validated adaptive task handoff.
**Dataset:** 48 frozen task DAG and 8 invalid graphs. **Independent oracle:** Independent topological and deterministic task oracle.
**Metrics:** Dependency violations, completions, p95. **Acceptance criterion:** 0 dependency violations; completions >= baseline; p95 <=1.20x.
**Negative controls:** cycle; completed task replay; worker crash after partial effect.

### routing

**Baseline:** Existing allowed-model/tool selector. **Variant:** Scoped routing and reduced-context selection with safe fallback.
**Dataset:** 100 synthetic labelled requests with 20 sealed holdout. **Independent oracle:** Predefined allowed target set and task scorer.
**Metrics:** Invalid routes, task coverage, context size. **Acceptance criterion:** 0 unauthorized routes; coverage >= baseline; context <=0.90x.
**Negative controls:** similar forbidden tool; missing schema; provider unavailable.

### experiment

**Baseline:** Current source review and manual reference tests. **Variant:** Isolated candidate evaluation with independent held-out promotion.
**Dataset:** 30 toy improvements, 6 score/source mutations. **Independent oracle:** Frozen independent code/output oracle.
**Metrics:** False promotion, validated gain, CPU and wall overhead. **Acceptance criterion:** 0 bad promotions; 6/6 mutations blocked; no train-only selection.
**Negative controls:** scorer mutation; train overfit; changed source commit.

### source_pin

**Baseline:** Plain working-directory source handoff. **Variant:** Git archive at fixed SHA plus immutable input manifest.
**Dataset:** 30 synthetic repositories and 12 corrupt/dirty/missing-source controls. **Independent oracle:** External git archive byte digest and independent manifest.
**Metrics:** Provenance false accept, artifact completeness. **Acceptance criterion:** 0 unpinned/corrupt accepted; 30/30 valid snapshots replayable.
**Negative controls:** dirty untracked file; wrong SHA; deleted source checkout.

### delivery

**Baseline:** Current sendMessage then local post_state. **Variant:** Durable outbox with UNKNOWN quarantine and explicit reconciliation.
**Dataset:** 120 mocked sends across ack/timeout/ambiguous/crash states. **Independent oracle:** Independent mock server committed-send ledger.
**Metrics:** Duplicate sends, lost messages, ambiguous states. **Acceptance criterion:** No UNKNOWN retry without reconciliation; fewer duplicates, no false success.
**Negative controls:** server commit then lost ACK; crash before local state; timeout before effect.

### sql

**Baseline:** Existing deterministic read-only PG state service. **Variant:** Versioned MCP read adapter over same exact GUC fields.
**Dataset:** 40 synthetic pg_settings snapshots and 8 corrupted fixtures. **Independent oracle:** Independent exact SQL values and unit parsing.
**Metrics:** Numerical equivalence, stale handling, p95. **Acceptance criterion:** 40/40 exact matching, 8/8 invalid rejected, no DB/network writes.
**Negative controls:** stale GUC; invalid unit; partial timeout.

### security

**Baseline:** Existing policy, prompt and skill-file checks. **Variant:** Deterministic effect gate separated from untrusted text.
**Dataset:** 80 synthetic task+attack cases, incl. 20 legitimate tasks and 8 mutants. **Independent oracle:** Independent allowed-operation labels, not model judgment.
**Metrics:** Unauthorized effects, legitimate completion. **Acceptance criterion:** 0 unauthorized effects; legitimate coverage >= baseline; 8/8 mutants blocked.
**Negative controls:** fake SYSTEM in markdown; tool reply role spoof; malicious dependency.

### skills

**Baseline:** Current skill and static contract tests. **Variant:** Source-aware scoped skill/review contract.
**Dataset:** 50 synthetic invocations incl. 15 missing evidence and 10 OOD. **Independent oracle:** Independent source and allowed-operation gold.
**Metrics:** Ungrounded PASS, valid coverage, time/tokens. **Acceptance criterion:** 0 ungrounded PASS; legitimate coverage >= baseline; no real secrets.
**Negative controls:** untrusted SKILL text; same basename different repo; missing citation.

### graph

**Baseline:** Current direct source/link lookup. **Variant:** Versioned provenance edges and typed graph traversal.
**Dataset:** 45 synthetic linked artifacts + 30 path queries + 10 corrupt links. **Independent oracle:** Independent directed-edge and source-hash membership.
**Metrics:** Correct links, wrong direction, false edges. **Acceptance criterion:** 0 false edges; valid-link recall >= baseline; 10/10 bad rejected.
**Negative controls:** reversed edge; stale source hash; cross-scope link.

### diagnostics

**Baseline:** Current offline incident/RCA evaluation without new telemetry. **Variant:** Read-only event provenance and evidence-aware abstention.
**Dataset:** 50 synthetic host/DB traces incl. 10 decoys; no live targets. **Independent oracle:** Independent event-to-causal-mechanism adjudication.
**Metrics:** False causal PASS, supported-case coverage, overhead. **Acceptance criterion:** 0 unsupported causal PASS; coverage >= baseline; no external effect.
**Negative controls:** PID reuse; reordered timestamps; irrelevant but correlated event.

### visual

**Baseline:** Existing text/table report or manual GUI behavior. **Variant:** Read-only SVG or accessibility rendering from frozen observations.
**Dataset:** 25 synthetic charts/desktop states incl. invalid and zero cases. **Independent oracle:** Exact values and accessibility element identifiers.
**Metrics:** Numeric correctness, invalid SVG, unsafe UI actions. **Acceptance criterion:** 25/25 correct; 0 invalid SVG/unsafe click; no production UI.
**Negative controls:** negative/zero value; missing aria label; truncated source.

### medical

**Baseline:** Current synthetic clinical-response protocol. **Variant:** Expert-adjudicated sequential differential and safe-abstention rubric.
**Dataset:** 60 fabricated no-PHI medical vignettes; specialist-sealed gold. **Independent oracle:** Independent qualified clinician evaluation and severity rubric.
**Metrics:** Unsafe certainty, red-flag referral, clinical correctness. **Acceptance criterion:** NO deployment from this pilot; 0 critical safety failures before further expert evaluation.
**Negative controls:** urgent red flags; ambiguous symptoms; contraindication unknown.

### identity

**Baseline:** Current source-ID sanitizer and index lookup. **Variant:** Collision-guarded canonical IDs without destructive migration.
**Dataset:** 60 synthetic IDs with Unicode/separator cases. **Independent oracle:** Exact injectivity and scope membership.
**Metrics:** Collision rate, lookup agreement, false source alias. **Acceptance criterion:** 0 distinct-ID collisions, 0 cross-scope lookups, existing valid IDs stable.
**Negative controls:** a/b vs ab; Unicode confusable; empty ID.

### typestate_dotnet

**Baseline:** Current documented type/API policy and negative-compilation witnesses. **Variant:** Roslyn incremental analyzer or typestate design forbidding bad transitions at compile time.
**Dataset:** 40 synthetic C# projects: 20 permitted, 20 forbidden states and generic wrapper cases. **Independent oracle:** Independent documented door/guard transitions and actual compiler diagnostics.
**Metrics:** Illegal states compiled, legitimate builds preserved, compiler overhead. **Acceptance criterion:** 0/20 forbidden compile; 20/20 valid compile; no unapproved diagnostic suppression.
**Negative controls:** generic wrapper bypass; delegate capturing forbidden state; dependency boundary escaped.

### docx_styles

**Baseline:** Plain-text extraction of official source document. **Variant:** OOXML-aware extraction preserving color/highlight/hidden-style requirements.
**Dataset:** 24 synthetic DOCX with paired styled and unstyled warnings, no protected documents. **Independent oracle:** Independent OOXML package semantics and clause-preservation labels.
**Metrics:** Lost critical cues, parser disagreement, completion coverage. **Acceptance criterion:** 0 omitted mandatory cues on 24 fixtures; no newly invented warning.
**Negative controls:** highlight-only warning; nested style inheritance; broken relationship.

### privacy

**Baseline:** Existing structured PII detector on synthetic text. **Variant:** Conservative content-sensitivity guard and explicit human confirmation.
**Dataset:** 60 synthetic emails, medical narratives and neutral strings. **Independent oracle:** Independent seeded content class and required disclosure scope.
**Metrics:** False negative PII, false positive quarantine, data egress. **Acceptance criterion:** 0 synthetic sensitive egress; seeded sensitive recall >= baseline; no automatic post.
**Negative controls:** Russian medical narrative; split email identifier; lookalike benign medical term.

### jsonc

**Baseline:** Current config policy and strict JSON parse. **Variant:** JSONC canonical parse rejecting duplicate keys and unsafe override.
**Dataset:** 60 synthetic valid/invalid JSONC trees, including comments and trailing commas. **Independent oracle:** Independent JSONC syntax and duplicate-key/permission gold.
**Metrics:** Bad configs accepted, valid configs preserved, parse time. **Acceptance criterion:** 0 duplicate privilege keys accepted; all valid semantics match baseline.
**Negative controls:** duplicate security key; comment-trailing comma; ambiguous Unicode escape.

### pg_health

**Baseline:** Existing dated PostgreSQL health snapshot or missing-state abstention. **Variant:** Read-only typed relation/XID/autovacuum evidence adapter.
**Dataset:** 40 synthetic pg_stat_relation/txid snapshots with corrupt/stale variants. **Independent oracle:** Independent freeze headroom, stale snapshot and alert thresholds.
**Metrics:** Wrong XID risk label, false OK on missing stats, p95. **Acceptance criterion:** 0 false OK on missing/stale data; exact fixture alert decisions; no database writes.
**Negative controls:** statistics reset; missing monitor; toast age exceeds heap age.

## Evidence boundary

Historical 506 explicit source-to-project assessments remain unchanged. Other study–project pairs have not been assessed; no inferred NO_FIT. Before running a P0, independently inspect the exact source and consumer contract, freeze the corpus, run two arms with an external oracle, preserve costs, negative results and source hashes, and request owner approval. Clinical work requires qualified independent specialist validation. This file contains no real clinical or employer data.
