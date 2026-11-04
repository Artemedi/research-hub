# Telegram BK → проекты: предварительная матрица соответствий

**Дата:** 2026-11-04. **Проектный реестр:** `Artemedi/project-registry@8966dc62c63b56e7d8da085705fc9079a6c0e758`.
**Глубина:** `PRELIMINARY_PROFILE_TRIAGE_ONLY` — источники и 45 проектных профилей, без полного scientific review, без source-level integration audit и без эксперимента.
**Покрытие:** 22 содержательных кандидата из исторической очереди. Другие входные материалы, не являющиеся исследованиями/инженерными находками, **не сохраняются** здесь.

Только конкретное соответствие профилю: `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. Это **не** `FIT_CANDIDATE`, `LAB_VERIFIED` или `PRODUCTION_APPROVED`. Условные совпадения не создают backlink. Исторический Telegram ledger и его 23 статуса ожидания **не менялись**: полные обзоры будут позже.

## Материал → все профильные кандидаты

| Telegram BK и первоисточник | Прямые профильные совпадения | Условные совпадения | Почему требуется продолжить проверку |
| --- | --- | --- | --- |
| [BK-006 — Open Steps](https://github.com/kharmanskyi/open-steps/blob/4fa744ba8ea06ccf128a39853824c46ac391dd00/README.md) | `agent-skills`, `agent-config` | `dsh-team-context` | Улучшение читаемости не доказывает качество кода; нужны тесты неизменности фактов и совместимости фронтматтера. |
| [BK-011 — SIMURG](https://github.com/doofzoff/SIMURG/blob/2831a92359cdaf1b38cc14f55e74251e09a91e0b/README.md) | `dsh-runtime`, `9router` | `HermesAgent`, `TrinMedicalBot` | Полный научный PDF пока не прочитан; риск false positive на русскоязычных SQL/JSON и медицинском тексте. |
| [BK-016 — claude-swarm](https://github.com/cj-vana/claude-swarm/blob/31f19199bf3557cda4860231186a06b72c8edb94/README.md) | `dsh-runtime`, `dsh-claude-primary-agent`, `wiki-tasks` | `HermesAgent`, `Harness`, `dsh` | Требует проверки реального права записи, остановки workers, API-расхода и восстановления после отказов. |
| [BK-019 — Warp Skill Doctor](https://www.warp.dev/skill-doctor) | `agent-skills`, `agent-config` | `dsh-team-context` | Метод оценки вендорский и не воспроизведён; риск утечки приватных транскриптов и ложной оптимизации метрики. |
| [BK-022 — Microsoft Skill Recorder](https://github.com/microsoft/skill-recorder/blob/505c97ae47be5642c0e1b44ebb8d1c1530c298fa/README.md) | `agent-skills`, `agent-config` | `wiki-tasks`, `dsh-team-context` | Скринкаст/голос/окна содержат приватные сведения; нужна проверка покрытия действий и платформенных прав. |
| [BK-024 — Local Knowledge Graph](https://github.com/punnerud/Local_Knowledge_Graph/blob/58fce402c7d15a3f5abcc8d0b1e920c1be5071b5/README.md) | `dsh-team-context`, `Wiki_PG`, `MyWiki` | `dsh-runtime`, `sequential-rca` | Лицензия не OSI-approved, проверить коммерческие ограничения; графовые рёбра и эффект retrieval пока не верифицированы. |
| [BK-025 — исходный видеопункт](https://www.youtube.com/watch?v=eFBSlgXG3U0) ([более поздний авторский технический пост, не подтверждён как тот же эксперимент](https://unreallabs.ai/blog/long-horizon-agents-at-half-the-cost/)) | **нет — отложен** | `dsh-runtime`, `Harness`, `dsh-claude-primary-agent` | Видеозапись от сентября не удалось получить без авторизации; официальный технический пост появился позднее, тождественность экспериментов НЕ подтверждена. Отложено без backlinks. |
| [BK-026 — Julia 1 (144M decision model)](https://supersoniclabs.ai/julia-1/) | `9router`, `dsh-runtime` | `sequential-rca`, `TelegramBot` | Задачи сравнения не совпадают с портфелем; известны ограничения длинных списков и 1024 токенов, проверить лицензии/веса. |
| [BK-028 — Hyperresearch](https://github.com/jordan-gibbs/hyperresearch/blob/aece65f9307197119629beacf8aeaf8cc80e999a/README.md) | `dsh-paper2agent`, `agent-skills` | `dsh`, `dsh-team-context` | Позиция в бенчмарке заявлена автором; стоимость вызовов, воспроизводимость и границы полнотекстового допуска неизвестны. |
| [BK-029 — 0-CODE](https://github.com/0-SOFT/0-CODE/blob/47f6a81724e87ff5e916f0eb146516d801a8fb28/README.md) | `dsh-runtime`, `wiki-tasks`, `agent-config` | `Harness`, `dsh`, `HermesAgent`, `agent-skills` | Большая область записей/хуков и риск конфликта с существующими DSH STATE/EVENTS; никогда не интегрировать автоматически. |
| [BK-034 — Karpathy AutoResearch loop](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md) | `dsh-paper2agent`, `dsh-team-context` | `bitvec-dsh`, `dsh-runtime` | Исходная инфраструктура заточена под обучение GPT на GPU; overfitting и перенос на agent eval требуют отдельного измерения. |
| [BK-037 — youtube-skills](https://github.com/ZeroPointRepo/youtube-skills/blob/4f7994b94e7d5e250c3b51102d609992e04d5d0d/README.md) | `TelegramBot`, `HermesAgent`, `agent-skills` | `dsh-runtime` | Сервис внешний: проверить условия, стоимость, хранение ключей и точность субтитров; без API теста нет. |
| [BK-041 — Inspektor Gadget eBPF](https://github.com/inspektor-gadget/inspektor-gadget/blob/fcc7786b21d41e176e2ad5b4d5c86bc0269974d4/README.md) | `AKUZ`, `Wiki_PG`, `sequential-rca` | `akuz-issue` | На Bazzite unprivileged BPF_MAP_CREATE=EPERM; ни один настоящий gadget trace не выполнялся, LAB_VERIFIED не назначен. |
| [BK-043 — Unsloth decision model tutorial](https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth) | `9router`, `dsh-runtime` | `sequential-rca`, `wiki-tasks` | Потребность в разметке и реальном benchmark, 8 GB VRAM не гарантируют безопасное обучение; заявленные цифры не перенесены. |
| [BK-047 — Anthropic agent automations guide](https://claude.dev/blog/building-effective-agent-automations/) | `TelegramBot`, `wiki-tasks`, `HermesAgent` | `dsh`, `confluence-wiki-backups` | Описан конкретный managed-agents стек, не проверена переносимость механики на текущие системы и Google/GitHub интеграции. |
| [BK-048 — Understand Anything](https://github.com/Egonex-AI/Understand-Anything/blob/4e6d3299017a7432da15957874992837a315c5b4/README.md) | `dsh-team-context`, `MyWiki` | `akuz-schema-inventory`, `Wiki_PG`, `psqlqa` | В README нет заявленной поддержки SQL/T-SQL: невозможно считать граф кода готовой альтернативой проверенному MSSQL dependency graph. Остальные рёбра/impact и издержки модели не измерены. |
| [BK-050 — Chartli](https://github.com/ahmadawais/chartli/blob/3b39b97aeb564646437b2b7501b60541994d7575/README.md) | `AKUZ`, `Wiki_PG`, `akuz-schema-inventory` | `sequential-rca`, `akuzlogparser` | Только представление метрик, без новых диагностических правил; нужен тест точности осей и ценности против таблиц. |
| [BK-053 — Yahont CE](https://github.com/pipedude/yahont-ce/blob/367b48da9de2d296f905aca4bf0eb384043bf643/README.md) | `Wiki_PG`, `dsh-team-context`, `MyWiki` | `hermes-akuz-agents`, `HermesAgent` | Форк Onyx, проверить лицензии всех компонентов, ACL/PII, индекс и производительность, не переносить рабочий корпус без допуска. |
| [BK-060 — DeepSeek dsh-superagent prototype](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md) | `dsh`, `dsh-runtime`, `wiki-tasks` | `dsh-claude-primary-agent`, `HermesAgent`, `Harness` | Сам README говорит «research prototype, not production»; интеграция с DSH и проверка отказоустойчивости отсутствуют. |
| [BK-062 — Reverse Engineer Anything (REA)](https://github.com/morluto/rea/blob/5a1f75461ac843f32423afd49c9e8b69a116b879/README.md) | `MyPartyIsGrinding`, `WarOfGenesisIdleLoot`, `game-localization-guide` | `psqlqa` | Только собственные или разрешённые бинарники; правовая и supply-chain проверка перед запуском внешних инструментов. |
| [BK-063 — Tencent Hyra 2.0](https://hy.tencent.com/research/hyra2) | **нет — отложен** | `dsh`, `dsh-team-context`, `dsh-paper2agent`, `wiki-tasks` | DEFER: нет подтверждённого полного технического описания и исходников именно Hyra 2.0; публикации результатов Hyra ≠ воспроизводимость новой системы. |
| [BK-065 — Vercel Agent Desktop](https://github.com/vercel-labs/agent-desktop/blob/6660fbac768dc7e7332837b90ed465684859afa3/README.md) | `HermesAgent`, `Harness`, `psqlqa` | `concept-loom-desktop`, `hermes-akuz-agents`, `dsh-claude-primary-agent` | Linux Wayland/AT-SPI и приватные снимки окна, permissions, stale refs требуют отдельного GUI-sandbox и E2E. |

## Обоснование каждой прямой связи

Проектные роли ниже взяты из действующего `PROJECT.md`. Это явные рабочие гипотезы, а не установленный кодовый integration seam.

**BK-006 (Open Steps).** Набор навыков оформления статуса и независимой проверки работы агента, ориентированный на понятную человеку отчётность.
- `agent-skills` — Собственные SKILL.md: проверка результатов и читаемость статуса. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `agent-config` — Шаблоны Claude/Codex: стандарт отчётности и проверки. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-011 (SIMURG).** Раннее обнаружение деградации LLM-стрима (повторы, дрейф языка, мусор); не детектор фактических галлюцинаций.
- `dsh-runtime` — Контроль деградации генерации в потоке runtime. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `9router` — Проверка чанков ответов на шлюзе моделей; seam не подтверждён. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- Научный PDF доступен по ссылке из репозитория, **полный текст ещё не прочитан**, поэтому методология и эффект не проверялись.

**BK-016 (claude-swarm).** MCP-оркестрация параллельных Claude workers, git worktrees, checkpointing и проверки протоколов.
- `dsh-runtime` — Изоляция workers, retry и recovery runtime. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `dsh-claude-primary-agent` — Рабочие сессии Claude Agent SDK. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `wiki-tasks` — Долговечные задачи, блокировки и восстановление. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-019 (Warp Skill Doctor).** Анализ транскриптов с последующей оценкой качества навыков и предложением правок.
- `agent-skills` — Оценка качества собственных навыков по истории. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `agent-config` — Общая политика prompts/hooks и её ревью. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-022 (Microsoft Skill Recorder).** Захват GUI/терминальной последовательности и превращение её в SKILL.md/автоматизацию.
- `agent-skills` — Производство SKILL.md из наблюдаемого workflow. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `agent-config` — Проверка и установка экспортированных инструкций. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-024 (Local Knowledge Graph).** Локальное построение используемого в рассуждении RDF-графа с Ollama и несколькими режимами проверки.
- `dsh-team-context` — Структурирование связей знаний для retrieval. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `Wiki_PG` — Связи документов PostgreSQL и графовый oracle. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `MyWiki` — Связи Obsidian-заметок и локальный граф. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-025 (Unreal Agent cost vs Codex (видео)).** Видеообзор сравнения стоимости Unreal Agent и Codex. Транскрипт недоступен; позже вышла авторская техническая статья о compaction, но не доказано, что это тот же эксперимент.
- **Рассмотрен и отложен:** сентябрьское видео не удалось прочитать (YouTube запросил авторизацию); авторская публикация Unreal Labs вышла позднее, тождественность экспериментов не подтверждена, поэтому backlinks отсутствуют.

**BK-026 (Julia 1 (144M decision model)).** Авторская модель выбора из 2–20 опций с CPU-инференсом и несколькими оценками, включая неудачу на Banking77.
- `9router` — Классификатор выбора провайдера. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `dsh-runtime` — Дешёвое принятие решений для агентов. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-028 (Hyperresearch).** Многоэтапный research harness с библиографическим хранилищем и проверкой цитат, включая skill для Codex.
- `dsh-paper2agent` — Провенанс источников и проверка цитат научного конвейера. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `agent-skills` — Внешний Codex skill — reference для собственных навыков. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-029 (0-CODE).** Автономные циклы разработки, журнал состояния, doctor и hooks для Claude/Codex/OpenCode.
- `dsh-runtime` — Runtime-циклы, возобновление и state machine. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `wiki-tasks` — Persistent task state и документальные workflow. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `agent-config` — Настройка hooks, prompts и doctor. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-034 (Karpathy AutoResearch loop).** Фиксированный независимый eval и цикл изменения только train.py с сохранением лучшего коммита, вместо вторичного видео.
- `dsh-paper2agent` — Stage 6 эксперименты с фиксированным независимым oracle. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `dsh-team-context` — Безопасные циклы эволюции навыков. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- Видео недоступно для полного прочтения, но исходный Karpathy AutoResearch и program.md независимо подтверждают сам инженерный метод.

**BK-037 (youtube-skills).** Набор agent skills для транскриптов, поиска и списка видео через коммерческий TranscriptAPI.
- `TelegramBot` — YouTube источник метаданных и субтитров видео. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `HermesAgent` — Агентный видео-анализ в Hermes. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `agent-skills` — Проверяемая skill-обёртка внешнего TranscriptAPI. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-041 (Inspektor Gadget eBPF).** Наблюдаемость Linux syscalls/eBPF для диагностики DBA и системных инцидентов; BK-041 ранее имеет отдельную карточку и permission gate.
- `AKUZ` — Kernel evidence для Linux PostgreSQL DBA. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `Wiki_PG` — Диагностика Linux/PostgreSQL в Wiki_PG. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `sequential-rca` — Read-only syscall/IO trace как источник offline RCA. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- [BK-041 уже имеет собственную карточку](../studies/inspektor-gadget.md) и [ограниченный permission-gate отчёт](2026-11-04-bk041-inspektor-gadget-gate.md): eBPF-программа не запускалась.

**BK-043 (Unsloth decision model tutorial).** Обучение классификатора/модели принятия решений на Qwen/LoRA с оценкой выбора и вероятностей.
- `9router` — Решение о маршрутизации модели с вероятностями. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `dsh-runtime` — Выбор действия в runtime при наличии меток. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-047 (Anthropic agent automations guide).** Инженерная методика scheduled agents: source bookmarks, failure-aware reads, scoped secrets, отдельный destination и budget caps.
- `TelegramBot` — Долговечный bookmark и подтверждение отправки видео. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `wiki-tasks` — Event state, retries и обнаружение пропуска. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `HermesAgent` — Scheduled gateway, scoped credentials и budgets. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-048 (Understand Anything).** Построение графов исходников, функций, зависимостей и знаний с интерактивной навигацией и impact-анализом.
- `dsh-team-context` — Knowledge/retrieval graph в Team Context. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `MyWiki` — Структурированные связи Obsidian-вики. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-050 (Chartli).** CLI-рендеринг численных рядов в ASCII/Braille/Unicode/SVG для терминала.
- `AKUZ` — Терминальные числовые отчёты DBA. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `Wiki_PG` — Ряды PostgreSQL метрик в CLI. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `akuz-schema-inventory` — Показатели риска инвентаризации схемы. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-053 (Yahont CE).** Локальная русскоязычная RAG/поисковая платформа с гибридным поиском, источниками, агентами и MCP.
- `Wiki_PG` — Гибридный retrieval для Wiki_PG. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `dsh-team-context` — Контекст команды и knowledge retrieval. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `MyWiki` — Поиск по локальному корпусу вики. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-060 (DeepSeek dsh-superagent prototype).** Экспериментальный агент на событиях GitHub, с work items, разрешениями, изолированными сессиями и human escalation.
- `dsh` — Управление работами и owner approvals в DSH. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `dsh-runtime` — Изоляция исполнения запросов в runtime. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `wiki-tasks` — Persistent task и event processing. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-062 (Reverse Engineer Anything (REA)).** MCP-интерфейс к анализу бинарников/.NET/JS/Electron и динамических систем для поиска контрактов.
- `MyPartyIsGrinding` — Разрешённый reverse engineering модифицируемой игры. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `WarOfGenesisIdleLoot` — Анализ разрешённых .NET/mono assemblies. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `game-localization-guide` — Извлечение форматов и статический анализ для локализации. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

**BK-063 (Tencent Hyra 2.0).** Анонс разделения Overall/Mission/Worker, повторного использования исследовательских инструментов и независимого review.
- `REVIEWED_DEFERRED / NEEDS_EVIDENCE`: полный метод/реализация именно Hyra 2.0 не подтверждены, поэтому backlinks пока отсутствуют.

**BK-065 (Vercel Agent Desktop).** CLI/MCP компьютерного управления через системное accessibility tree (AT-SPI/UIA/AX) с проверяемыми element refs.
- `HermesAgent` — GUI-инструменты через Hermes gateway. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `Harness` — Стенд адаптера accessibility и MCP. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.
- `psqlqa` — UI acceptance testing PostgreSQL desktop app. `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`.

## Обратная матрица: проект → все подходящие BK

Каждая строка содержит все прямые и условные соответствия проекта без произвольного ограничения общим числом материалов. Для самого исследования прямых соответствий не более трёх по правилам `RESEARCH_POLICY.md`.

| Проектная карточка | Прямые BK (со ссылками в карточке) | Условные BK (только матрица) |
| --- | --- | --- |
| [9router](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/9router/PROJECT.md) | BK-011, BK-026, BK-043 | — |
| [AKUZ](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/AKUZ/PROJECT.md) | BK-041, BK-050 | — |
| [Harness](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/Harness/PROJECT.md) | BK-065 | BK-016, BK-025, BK-029, BK-060 |
| [HermesAgent](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/HermesAgent/PROJECT.md) | BK-037, BK-047, BK-065 | BK-011, BK-016, BK-029, BK-053, BK-060 |
| [MyPartyIsGrinding](https://github.com/Artemedi/project-registry/blob/main/projects/04-personal-games/MyPartyIsGrinding/PROJECT.md) | BK-062 | — |
| [MyWiki](https://github.com/Artemedi/project-registry/blob/main/projects/04-personal-games/MyWiki/PROJECT.md) | BK-024, BK-048, BK-053 | — |
| [TelegramBot](https://github.com/Artemedi/project-registry/blob/main/projects/03-automations/TelegramBot/PROJECT.md) | BK-037, BK-047 | BK-026 |
| [TrinMedicalBot](https://github.com/Artemedi/project-registry/blob/main/projects/03-automations/TrinMedicalBot/PROJECT.md) | — | BK-011 |
| [WarOfGenesisIdleLoot](https://github.com/Artemedi/project-registry/blob/main/projects/04-personal-games/WarOfGenesisIdleLoot/PROJECT.md) | BK-062 | — |
| [Wiki_PG](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/Wiki_PG/PROJECT.md) | BK-024, BK-041, BK-050, BK-053 | BK-048 |
| [agent-config](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/agent-config/PROJECT.md) | BK-006, BK-019, BK-022, BK-029 | — |
| [agent-skills](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/agent-skills/PROJECT.md) | BK-006, BK-019, BK-022, BK-028, BK-037 | BK-029 |
| [akuz-issue](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/akuz-issue/PROJECT.md) | — | BK-041 |
| [akuz-schema-inventory](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/akuz-schema-inventory/PROJECT.md) | BK-050 | BK-048 |
| [akuzlogparser](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/akuzlogparser/PROJECT.md) | — | BK-050 |
| [bitvec-dsh](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/bitvec-dsh/PROJECT.md) | — | BK-034 |
| [concept-loom-desktop](https://github.com/Artemedi/project-registry/blob/main/projects/04-personal-games/concept-loom-desktop/PROJECT.md) | — | BK-065 |
| [confluence-wiki-backups](https://github.com/Artemedi/project-registry/blob/main/projects/03-automations/confluence-wiki-backups/PROJECT.md) | — | BK-047 |
| [dsh](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh/PROJECT.md) | BK-060 | BK-016, BK-028, BK-029, BK-047, BK-063 |
| [dsh-claude-primary-agent](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh-claude-primary-agent/PROJECT.md) | BK-016 | BK-025, BK-060, BK-065 |
| [dsh-paper2agent](https://github.com/Artemedi/project-registry/blob/main/projects/06-independent-research/dsh-paper2agent/PROJECT.md) | BK-028, BK-034 | BK-063 |
| [dsh-runtime](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh-runtime/PROJECT.md) | BK-011, BK-016, BK-026, BK-029, BK-043, BK-060 | BK-024, BK-025, BK-034, BK-037 |
| [dsh-team-context](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh-team-context/PROJECT.md) | BK-024, BK-034, BK-048, BK-053 | BK-006, BK-019, BK-022, BK-028, BK-063 |
| [game-localization-guide](https://github.com/Artemedi/project-registry/blob/main/projects/04-personal-games/game-localization-guide/PROJECT.md) | BK-062 | — |
| [hermes-akuz-agents](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/hermes-akuz-agents/PROJECT.md) | — | BK-053, BK-065 |
| [psqlqa](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/psqlqa/PROJECT.md) | BK-065 | BK-048, BK-062 |
| [sequential-rca](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/sequential-rca/PROJECT.md) | BK-041 | BK-024, BK-026, BK-043, BK-050 |
| [wiki-tasks](https://github.com/Artemedi/project-registry/blob/main/projects/03-automations/wiki-tasks/PROJECT.md) | BK-016, BK-029, BK-047, BK-060 | BK-022, BK-043, BK-063 |

## Остальные 17 проектов из 45

Скрининг не обнаружил даже профильного основания для этих карточек: `MS-SQL`, `Postgres14book`, `SQL-Server-First-Responder-Kit`, `SQLServerTools`, `TencentDB-Agent-Memory`, `akuz-optimizer-twin`, `anastasia-wiki-bot`, `claude-code-docs`, `deepseek-harness`, `developer-safe-dotnet-core`, `free-router`, `gitignore`, `paper2agent-index`, `sqlserver-kit`, `teamai-cli`, `tigertoolbox`, `uuid-vs-auto-increment`.
Это `NO_FIT_AT_PROFILE_SCREENING` для текущих материалов, не окончательное `NOT_APPLICABLE` по полному научному анализу.

## Границы доказательности

- Для GitHub источников просмотрены README/официальные описания и проверен текущий HEAD. Код/тесты каждого из них ещё не проходили полноценный аудит и не исполнялись.
- Авторские показатели и таблицы Julia 1, Unsloth, Unreal Labs, SIMURG, Hyperresearch не являются независимо воспроизведёнными.
- BK-025: видео не удалось получить без авторизации; поздняя публикация Unreal Labs содержит родственный benchmark, но не доказано, что это идентичный ролик/эксперимент. Поэтому только условные привязки без backlinks.
- BK-034: original Karpathy AutoResearch с полным исходным методом доступен; само видео недоступно для полного просмотра.
- Для BK-063 нет подтверждения полного технического текста реализации Hyra 2.0; его условные цели не получат backlinks до отдельного допуска.
- Для papers без полного PDF/HTML/author version: никаких выводов о методологии, результатах и ограничениях только на основе abstract. `FULL_TEXT_UNAVAILABLE` ставится лишь после попыток получить полную статью; если PDF существует, но ещё не прочитан, это `NOT_REVIEWED`, а не `FULL_TEXT_UNAVAILABLE`.
- Последующий Stage 3/4 требует актуальный `repo@SHA/path:line` проекта, точный benchmark/oracle, границы риска/IO/CPU/VRAM и owner gate. Пока нет проверки — `NEEDS_EVIDENCE`; нет benchmark — `BLOCKED: MEASUREMENT_MISSING`.
- Ни одна установка инструмента, запуск платного API, GUI/eBPF, изменение исходников или production-действие не выполнялись.

Историческая [Telegram-матрица из 65 записей](2026-11-04-telegram-bookmarks-reconciliation.md) сохраняет прежние статусы **по уровню технической проверки**. Данная карта отвечает лишь на вопрос, какие исследования потенциально полезны каким проектам.
