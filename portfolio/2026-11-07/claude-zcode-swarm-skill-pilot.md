# Применение Claude Swarm к ZCode-рoю: безопасный пилот и skill

**Дата:** 07.11.2026. Исходное пользовательское действие: предметные контрпроверки научных исследований. Проверен не общий бот с инструментами, а **реальный worker-management путь** оригинального Claude Swarm с заменой исполнителя на no-tool ZCode. Предыдущие ограничения и инженерная основа: [архитектура исследовательского оркестратора](../../docs/research-orchestrator.md), [проверка дефектов worktree и worker outcome](claude-swarm-failure-injection.md), [изолированный патч](claude-swarm-repair-ab.md) и [четыре source-anchored научные статьи](source-anchored-extension.md).

## Что именно работает

**Реальный путь:** `WorkerManager.startWorker()` из `cj-vana/claude-swarm@31f19199bf3557cda4860231186a06b72c8edb94` после строго ограниченного [patch](../../experiments/research-portfolio/2026-11-07-claude-swarm-recovery.patch.gz) → уникальная временная Git worktree → изолированный tmux → временная команда `claude-code` с [безынструментальным CLI-адаптером](../../experiments/research-portfolio/2026-11-07-zcode-claude-cli-shim.mjs) → реальный локальный `subagent.mjs` ZCode GLM-5.3-Flash → проверка ответа и session-specific `.done` → `WorkerManager.checkWorker()` → **отдельная внешняя проверка утверждений по oracle**. Задания и источники передавались только в виде публичного текста, а не через приватный project-registry, production или DB.

Проверено две логические роли — `reviewer`, `falsifier` — на одинаковых восьми claim↔source парах из официальных HTML статей [Agent Error Dataset](https://arxiv.org/html/2609.40111) и [BenchShield](https://arxiv.org/html/2609.11028). В наборе **четыре подтверждённых и четыре неподтверждённых** утверждения, авторские метки заранее определены, модели не переданы.

## A/B, абсолютные показатели

| Параметр | A: ZCode напрямую | B: ZCode через исправленный Claude Swarm |
| --- | --- | --- |
| Рабочие роли | 2 | 2 |
| Фактические модельные вызовы | 2 | 2 |
| Завершение после исправления времени ожидания | **2/2 COMPLETE** | **2/2 COMPLETE** |
| Точность относительно заранее составленного oracle | **8/8 для каждой роли** | **8/8 для каждой роли** |
| Ошибочные SUPPORTED | 0 | 0 |
| SHA-256 переданного модельного промпта | **совпадает** | **совпадает** |
| Provider/tool calls из модели | 0 разрешённых инструментов | 0 разрешённых инструментов |
| Физическая параллельность ZCode | 1 | 1 |

Первый экспериментальный запуск показал **ошибку самого тестового драйвера**: 15 секунд ожидания одного worker недостаточно, хотя провайдер мог ещё исполнять запрос. В этой попытке завершились 2/2 прямых вызова и 1/2 управляемых, второй стал `BLOCKED_TIMEOUT` тестового координатора. Ожидание увеличено до 66 секунд, не изменяя модельный лимит и число конкурентных процессов. Второй отказ был обнаружен после ужесточения фильтра ответа: ZCode возвращает служебный блок `thinking` наряду с `text`; ошибочное правило «только text» пометило обе корректные передачи как `BLOCKED_PROVIDER`. Фильтр исправлен точечно: допускается неисполняемое `thinking`, но `tool_use` и прочие неизвестные блоки по-прежнему запрещены. Затем **финальный A/B завершён 4/4**, офлайн-негативные тесты пройдены. Невыполненное задание нельзя трактовать как `ACCEPT`.

Записываются полные per-role usage, model, elapsed и хеши промпта и ответа в [машинных результатах](../../data/results/research-portfolio/2026-11-07-claude-zcode-swarm-pilot.json). На таком коротком нерандомизированном тесте **не утверждается преимущество производительности**: порядок A→B и серверный кеш могут повлиять на время; это сравнение корректности маршрутизации, а не SLA/стоимости. Независимая от ZCode проверка — авторская разметка восьми public-source утверждений, а не слепая экспертная разметка.

## Безопасность и границы

- Claude Swarm **сам не поддерживает ZCode нативно**. Пилот использовал явный no-tool адаптер и временную подмену команды CLI `claude-code`. Это не полноценная интеграция с реальными файловыми инструментами Claude Code.
- У upstream по умолчанию обнаружен `bypassPermissions`. В лаборатории флаг явно переопределён, а адаптер **не передаёт Bash/Write/Edit/MCP** в ZCode, проверяет public-only JSON job, session-qualified путь, точные идентификаторы и структурно полный ответ. Непредусмотренный tool-use block отклоняется.
- [Шесть офлайн-тестов адаптера](../../experiments/research-portfolio/2026-11-07-zcode-claude-cli-shim.test.mjs): happy-path с mock provider, отклонение отсутствующего job marker, `file://` источника, выхода за sandbox path, повторного done marker и ответа модели с `tool_use`. Все должны пройти перед публикацией.
- **Не security boundary:** worker и координатор работают от одного Unix UID, `.done`/`.exit` могут быть подделаны, stale locks и агрессивные попытки replay не решены, нет доказанной защищённости от malicious local process. Патч и skill не включают sandbox для произвольного кода.
- `WorkerManager` проверен в сценарии bounded worker запуска, **не** как глобальный production scheduler 100+ задач. Нет проверки concurrent workers, auto-merge, реальных source checkout в контексте полного DAG, внешних ZCode quotas при нагрузке, long-running recovery и rate limits.
- Сравнение двух одинаковых модельных prompts и успешных ответов на 8 выбранных примерах не оправдывает production-внедрения, автоматической оценки научной истины или расширения до 20–100 физических агентов.

## Закреплённый навык

Создан **repo-local SKILL.md**: [`research-swarm-orchestrator`](../../.agents/skills/research-swarm-orchestrator/SKILL.md), с короткой ссылкой из [`AGENTS.md`](../../AGENTS.md). Агент, работающий с `research-hub` и поддерживающий discovery `.agents/skills`, сможет использовать общий протокол: source/fulltext gate → роли и checkpoint → независимый oracle → Review/Rework/Blocked → минимальная приёмка → тесты/commit/CI. **Не установлен глобально в ChatGPT или ZCode и не запущен как автономный daemon**.

Репликация на Bazzite: проверить источник SHA, наложить изолированный patch, выполнить `npm run build && npm test`, установить локальные переменные `CLAUDE_SWARM_SOURCE`, `ZCODE_WRAPPER`, `ZCODE_SHIM` и `OUTPUT` по инструкциям skill; `node experiments/research-portfolio/2026-11-07-claude-zcode-swarm-pilot.mjs`. Скрипт создаёт **только** временные Git/tmux/CLI-shim файлы и удаляет их в `finally`. Окончательный оракул и метрики считаются снаружи, а не внутри ZCode.

**Вердикт:** `ACCEPT_BOUNDED_BRIDGE_PILOT`; `SKILL_REPOSITORY_LOCAL_READY`; `REWORK_HARDENED_GENERAL_ORCHESTRATION`; `NO_PRODUCTION_APPROVAL`. До расширения нужен A/B на ≥20 **разных** реальных безвредных задач с независимой разметкой, обработкой crash/retry и ресурсными метриками — как требуется в `docs/research-orchestrator.md`.
