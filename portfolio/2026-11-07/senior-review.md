# Финальная независимая экспертиза GPT-6: массовый предварительный разбор

**Дата:** 07.11.2026. **Объект:** 31 действующая карточка с недостающими проверками в `research-hub`, сопоставленная с приватной картой проектов. [Все 31 source/digest/model results](../../data/results/research-portfolio/2026-11-07-mass-swarm.json), [основной отчёт](mass-swarm-review.md), [проверка SHA/anchors](../../data/results/research-portfolio/2026-11-07-mass-anchor-audit.json).

**Внешний арбитр:** GPT-6, отдельно от ZCode GLM-5.3-Flash. Это независимое **инженерное суждение по уже доступным отрывкам и прежним датированным обзорам**, а не повторное чтение всех полных работ или исполнение чужих экспериментов.

## Проверка требований исследования

| Gate | Вердикт | Обоснование |
| --- | --- | --- |
| Инвентаризация исследовательских задач | `ACCEPT` | 31/31 canonical ID учтены; 31 публичный source pack |
| Ссылки на источник / хеш отрывка | `ACCEPT_AS_PROVENANCE` | 31/31 локальных excerpt SHA consistent; это **не** proof semantic truth |
| Выполнение коротких ZCode ролей | `PARTIAL` | 24/31 valid schema; 6 unsuccessful model calls, 1 source-blocked |
| Независимая критика всех научных выводов | `BLOCKED / NOT_COMPLETED` | Исходные узкие snippets не заменяют полный HTML/PDF+Methods/Results/Limitations, а одна модельная семья не является независимым oracle |
| Переоценка соответствий 45 проектам | `NO_NEW_PROJECT_FIT` | Только условные гипотезы; не проверены source seams и target baseline |
| Практическое внедрение | `NO_PRODUCTION_APPROVAL` | Нет независимого held-out A/B, издержек и негативных контролей на конкретном проекте |

`SCHEMA_PASS` означает **валидный структурированный ответ**, а не `SCIENTIFIC_ACCEPT`. Вердикт не повышает статусы ранее датированных `reviews/` и `current_assessments`, не создаёт registry backlinks.

## Выводы по конкретным исследованиям

**CERA-MoA (полный arXiv 2609.18779, ранее полнотекстово reviewed 05.11):** представленный отрывок Methods подтверждает shared 4B+LoRA схему, но не переносимость на API-only router. Appendix F прямо ограничивает оценку familiarity исходным prompt. **REWORK_PROJECT_FIT:** показать контролируемый hidden state / trainable adapter и точную ревизию backend; без этого `9router`, `dsh-runtime` — лишь условные направления, не fit.

**KVTether (полный arXiv 2609.39819, ранее полнотекстово reviewed 05.11):** lifecycle/event order и cache manager описаны в Methods. Реальная интеграция требует KV-serving hooks, контролируемого кэша и измерений на собственном inference runtime; облачный ZCode API этих свойств не подтвердил. **REWORK_PROJECT_FIT**, не объявлять экономию latency или стоимости только из авторских опытов.

**Random Attention (полный arXiv по канонической source card):** наблюдение из Limitations ограничено decode eviction в длинных chains of thought и training-free baselines, а не любым LLM cache. Нужен fixed-cache A/B на одном обслуживаемом backend и отдельная проверка областей переноса. **REWORK_MEASUREMENT**, без новой проектной привязки.

**NovaFabric:** собственная авторская оценка говорит об интервале для overhead, пересекающем ноль; это **недостаток мощности оценки**, а не доказанный zero-cost trace capture. Демонстрация 100M lineage edges != эксплуатация 100M агентов. **ACCEPT_CAVEAT**, не объявлять mature distributed production.

**Claude Swarm:** модель сделала вывод об orchestration на основании **docstring в SOURCE:src/index.ts**, а не функции, теста или успешного tmux-run. **REWORK_CLAIM_SCOPE:** заменить на «репозиторий декларирует MCP + tmux worker orchestration»; подтвердить вызовы, source@SHA, test/test fixture и failure recovery.

**Hyperresearch:** mock/fake provider test подтверждает наличие тестового шва, но не автоматическую проверку всех внешних провайдеров, реальное качество CLI или совместимость текущего HEAD. **REWORK_CLAIM_SCOPE** до запуска тестов pinned revision и independent external negative cases.

**mcp-toolbox-postgres:** `SOURCE:internal/log/log.go` показывает модуль логирования, но не механизм PostgreSQL query tool execution. **REWORK_SOURCE_SELECTION:** осмотреть core/adapter и security policy на pinned source, проверить с тестовыми read-only credentials в изолированной БД; присутствие `log/slog` не доказывает рабочий MCP tool.

**pgbot:** константа промпта с запретом выдумывать execution nodes не доказывает, что SQL рантайм гарантированно выполняет `EXPLAIN` без `ANALYZE` и не исполняет пользовательский запрос. **REWORK_CODE_AND_SECURITY:** проверить реальный путь SQL и permissions, негативный тест, transaction rollback.

**Open Steps:** docstring и `evals/score.py` без выполнения не подтверждают отсутствие model judge в scoring или однозначность артефактов. **REWORK_TEST**, held-out noisy judge vs deterministic scorer.

**inspektor-gadget:** один unit-test версии не устанавливает безопасность eBPF/privileged capture; нужны real kernel constraints, isolated tests, source and supply-chain audit. **REWORK_SCOPE**.

**IPFire fireperf:** число соединений и line-rate — исходное маркетинговое утверждение. Нужен независимый conntrack/network oracle на изолированном шлюзе. Нельзя переносить сравнение с iperf3 прямо на PostgreSQL workload. **AUTHOR_CLAIM_ONLY**.

**Julia 1 / Unsloth decision-model:** доступны анонсы/документация, но не подтверждены полные параметры эксперимента, held-out splits и лицензии. Результаты бенчмарков, если указаны, остаются **VENDOR_REPORTED**; требует воспроизводимого checkpoint и честного сравнительного baseline.

**Self-replicating Prompt Injections:** `opening:OPENING` содержит summary-level утверждение о simulated spread, не независимую оценку механизма и production incidents. **FULL_TEXT_REVIEW_GATE_NOT_MET_BY_THIS_MICRO_PASS**, если полного оригинального текста не было в фактическом input роли.

**YouTube Skills / Microsoft Skill Recorder:** существование публичного README или описания возможностей не доказывает работу стороннего API, качество transcript, user-action provenance, privacy guarantees или реальную replay безопасность. **REWORK_UPSTREAM_AND_PRIVACY_TEST**.

**Simurg / Yahont CE / Chartli / REA / understand-anything / dsh-superagent-prototype / zero-code:** короткие code paths/README фрагменты дают **точки для последующего pinned code review**, но не дают доказанных runtime property, тестов, производительности или проектной применимости. Нельзя по одному re-export, import, README или комментарию выводить корректность реализации. **SOURCE_FRAGMENT_ACCEPT, CLAIM_REVIEW_PENDING**.

**Ошибочные/незавершённые ZCode ответы:** `local-knowledge-graph`, `vercel-agent-desktop`, `dsh-creator-mode`, `karpathy-autoresearch`, `tencent-teamai-cli`, `toolgrad` — `BLOCKED_ROLE_INCOMPLETE`. `warp-skill-doctor` — `BLOCKED_SOURCE` по доступному brief; ранее pinned source review сохраняется. Не подменять отказ модели негативной оценкой технологии.

## Решение старшего ревьюера

**`ACCEPT` только по полноте реестра входных работ**, метаданным происхождения и результату ограниченного `source-excerpt screening`. `REWORK` по научной и инженерной доказательности, а не по структуре JSON. `REJECT` к производственному внедрению без подтверждённого target-specific A/B; ни одна научная гипотеза не объявляется опровергнутой только из-за неуспеха модели.**

Отдельные тематические роли-критики ZCode являются дополнительным сигналом, а не независимым scientific oracle. Для следующих итераций ожидается полный доступный легальный первоисточник (не snippets), чтение Methods+Results+Limitations, раздельный author vs replication verdict, source@SHA/path:line с тестами и сравнение на реальном target. Исторические `NO_CURRENT_TARGET` по CERA/KVTether не заменяются сомнительными «FIT_CANDIDATE» без изменившейся архитектуры исходных проектов.

**Реальная польза для Research Orchestrator:** очередь с одной физической сессией справилась с source screening лучше длинных 14-role prompts/20-way concurrency, но эффект качества на независимых научных задачах и стоимость verified completion **не оценены**. Запрашивать production-деплой пока нельзя.
