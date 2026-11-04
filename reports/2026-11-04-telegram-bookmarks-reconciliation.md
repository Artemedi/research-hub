# Telegram-подборка → research-hub: полная сверка 65 пунктов

**Дата:** 2026-11-04. **Назначение:** восстановить последовательность исходных Telegram-закладок, не смешивая их с другими исследовательскими потоками.

**Происхождение:** сохранённые `bookmark_research_inventory_2026-11-03.json` и `bookmark_research_audit_2026-11-03.md` от 3 ноября. Это **производный аудит пересланных сообщений**, а не дословный экспорт Telegram. Даты, заголовки, URL и порядок перенесены из сохранённого аудита; сверка с исходным текстом Telegram построчно невозможна без его прямой копии.

## Итоги

- **65** записей, **63** уникальных URL/темы, **2** точных дубликата: BK-004 → BK-002 и BK-044 → BK-043.
- По текущему состоянию: проверен экспериментально: **9** / разобран: **16** / ожидает проверки: **21** / исключён: **19**.
- **13** пунктов имеют прямую карточку в `studies/` research-hub; **10** имеют ссылку на отдельный тестовый/permission-gate отчёт (не все эти работы считаются экспериментально верифицированными). BK-001 имеет только лабораторный отчёт без научной карточки.
- Все **65** исходных ссылок и основания решения доступны также в машиночитаемом [JSON](2026-11-04-telegram-bookmarks-reconciliation.json).

## Правила присвоения статуса

| Статус | Критерий |
| --- | --- |
| **Проверен экспериментально** | Реально выполнен ограниченный локальный опыт на авторском коде/целевой реализации; перечисленные метрики не переносятся автоматически на production. |
| **Разобран** | Полный первичный текст научной работы либо полная официальная инженерная статья уже оценены; независимый лабораторный эксперимент не подтверждён. |
| **Ожидает проверки** | Обзор/README/ссылка были первично проверены, но отсутствует полный научный текст (если нужен) или воспроизводимая проверка работы в конкретном проекте. |
| **Исключён** | Приоритет **C** в исходном аудите: исключён **из активной очереди** из-за низкой текущей применимости; не удалён из истории. Приоритет **D**: точный дубль. Если статья была полнотекстово прочитана, это сохраняется отдельно в `Evidence`. |

## Полная матрица в исходном Telegram-порядке

| ID / дата | Исходный пункт | Итоговый статус | В research-hub | Подтверждение / причина |
| --- | --- | --- | --- | --- |
| BK-001 / 07.09 | [Vectorless RAG vs embeddings](https://clc.to/iSaRbg) | **проверен экспериментально** | [Опыт](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-03-bookmark-hypotheses-offline-experiments.md) | Ограниченный offline FTS5-тест: 6 DBA-запросов, не сопоставление всех RAG-подходов; сокращённая Telegram-ссылка не подтверждает тезис. |
| BK-002 / 08.09 | [Tencent TeamAI CLI](https://github.com/Tencent/teamai-cli) | **разобран** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/tencent-teamai-cli.md), [Разбор fork/upstream](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-bk002-tencent-teamai-cli-review.md) | Полные код/документация изучены: fork 13 ahead / 732 behind; сухой merge — 6 конфликтов. 3 обоснованных project matches; реального TeamAI E2E/синхронизации не было. |
| BK-003 / 11.09 | [pgbot](https://github.com/pgrundev/pgbot) | **проверен экспериментально** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/pgbot.md), [Опыт](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-pgbot-postgresql-lab.md) | Запущен исходный pgbot v0.9.0 на изолированном PostgreSQL; production-эффект не доказан. |
| BK-004 / 11.09 | [Tencent TeamAI CLI — repeat](https://github.com/Tencent/teamai-cli) | **исключён** | — | Точный повтор BK-002; не считать самостоятельным источником или второй проверкой. |
| BK-005 / 11.09 | [ToolGrad](https://aclanthology.org/2026.findings-acl.950/) | **разобран** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/toolgrad.md) | Полный опубликованный текст научной работы ранее рассмотрен; воспроизведения chain-first обучения нет. |
| BK-006 / 11.09 | [Open Steps agent skills](https://github.com/kharmanskyi/open-steps) | **проверен экспериментально** | [Карточка](../studies/open-steps.md), [Разбор и опыт](2026-11-04-bk006-open-steps-review.md) | Offline tests и узкий синтетический тест хуков v0.4.8; обнаружен пропуск изменения уже существующего untracked-файла. Качество ответов и польза проектам не измерены. |
| BK-007 / 12.09 | [OpenAI Agents API](https://openai.com/index/introducing-the-agents-api/) | **разобран** | — | Прочитана официальная полная статья; сервисный runtime на проектах не тестировался. |
| BK-008 / 13.09 | [Beautiful Mermaid](https://github.com/lukilabs/beautiful-mermaid) | **исключён** | — | Инструмент оформления схем; нет подтверждённого сейчас эффекта на корректность или надёжность проектов. |
| BK-009 / 13.09 | [GPT-6 Astra skills/prompt guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | **разобран** | — | Прочитано официальное руководство; влияние на стоимость/качество skills локально не измерено. |
| BK-010 / 13.09 | [Lieflat Charts](https://github.com/larashero3-dotcom/lieflat-charts) | **исключён** | — | Витрина графиков без установленного сценария, который требует нового charting stack. |
| BK-011 / 15.09 | [SIMURG streaming integrity monitor](https://github.com/doofzoff/SIMURG) | **проверен экспериментально** | [Карточка](../studies/simurg.md), [Разбор и опыт](2026-11-04-bk011-simurg-review.md) | Узкий offline тест метрики AUROC, калибровки и синтетических текстов; качество на реальных проектах не измерено. |
| BK-012 / 15.09 | [The Last AI Built by Humans — RSI levels](https://arxiv.org/html/2609.11873v1) | **разобран** | — | Полная обзорная работа разобрана; типология RSI не доказывает работоспособности L5. |
| BK-013 / 16.09 | [Retrieve-for-Train (R4T)](https://arxiv.org/html/2603.06397v1) | **исключён** | — | Работа о RL-поиске на наборах данных; нет подходящего trainable target и бюджета для переноса на текущие проекты. |
| BK-014 / 16.09 | [alphaXiv OpenResearch](https://github.com/alphaXiv/OpenResearch) | **разобран** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/alphaxiv-openresearch.md), [Разбор provenance / full-text](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-bk014-openresearch-review.md) | Проверен официальный Rust v0.2.24: Git commit archives/SQLite/run lineage. В orx paper нет автоматического полного текста OpenAlex/PubMed/bioRxiv; один project fit — dsh-paper2agent, без запусков и A/B. |
| BK-015 / 17.09 | [Anything2Explainer](https://github.com/Vincentwei1021/anything2explainer) | **исключён** | — | Генерация объясняющих видео не связана с обнаруженной задачей портфеля; авторское обещание скорости не проверено. |
| BK-016 / 17.09 | [Claude-swarm](https://github.com/cj-vana/claude-swarm) | **ожидает проверки** | — | Оркестратор не тестировался; семантика записи в общие файлы и стоимость API неизвестны. |
| BK-017 / 17.09 | [Google AI UI design guide](https://aistudio.google.com/learn/ai-ui-design-google-ai-studio) | **исключён** | — | Руководство по дизайну UI не является релевантным научным улучшением работающего backend. |
| BK-018 / 20.09 | [ScientistTwo](https://arxiv.org/html/2609.19644v1) | **разобран** | — | Полный текст учтён; заявленная авторская проверка scientific output не воспроизведена. |
| BK-019 / 20.09 | [Warp Skill Doctor](https://www.warp.dev/skill-doctor) | **ожидает проверки** | — | Официальный инструмент указан, но нет privacy-аудита и сравнения с локальными skills. |
| BK-020 / 22.09 | [Google AX](https://github.com/google/ax) | **исключён** | — | Google AX ещё не стабилизирован; нет подтверждённой потребности в новой глобальной системе оркестрации. |
| BK-021 / 24.09 | [Cursor improved token efficiency](https://cursor.com/blog/improved-token-efficiency) | **разобран** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/cursor-token-efficiency.md) | Инженерная статья Cursor ранее разобрана в research-hub; экономия токенов локально не воспроизводилась. |
| BK-022 / 25.09 | [Microsoft Skill Recorder](https://github.com/microsoft/skill-recorder) | **ожидает проверки** | — | Прочитано описание Microsoft Skill Recorder; запись и восстановление реального workflow не проверены. |
| BK-023 / 25.09 | [Claude Code Advisor](https://code.claude.com/docs/en/advisor) | **разобран** | — | Полная официальная документация изучена; отдельного A/B в проектах нет. |
| BK-024 / 25.09 | [Local Knowledge Graph](https://github.com/punnerud/Local_Knowledge_Graph) | **ожидает проверки** | — | Нужен oracle по корректности рёбер и стоимости обновлений графа. |
| BK-025 / 26.09 | [Unreal Agent cost vs Codex video](https://www.youtube.com/watch?v=eFBSlgXG3U0) | **ожидает проверки** | — | Есть пересказ видео, но нет независимых task traces, токенов и воспроизводимого сравнения стоимости. |
| BK-026 / 27.09 | [Julia 1 144M decision model](https://supersoniclabs.ia.br/julia-1/) | **ожидает проверки** | — | Публикация разработчика модели не заменяет локальный inference/quality benchmark. |
| BK-027 / 27.09 | [AlloyDB PostgreSQL for agents](https://cloud.google.com/blog/products/databases/announcing-postgresql-for-agents-in-alloydb) | **разобран** | — | Официальная статья AlloyDB разобрана; это cloud preview, не стандартная функция PostgreSQL. |
| BK-028 / 27.09 | [Hyperresearch](https://github.com/jordan-gibbs/hyperresearch) | **ожидает проверки** | — | Нет независимо проверенного benchmark и фиксированного сравнения research-cost. |
| BK-029 / 28.09 | [0-CODE autonomous loops](https://github.com/0-SOFT/0-CODE) | **ожидает проверки** | — | Показан отдельный демо-запуск, не проверена устойчивость длительных автоматических циклов. |
| BK-030 / 28.09 | [Dream-RSI](https://arxiv.org/html/2609.14858v1) | **разобран** | — | Прочитан полный научный текст и подтверждено наличие авторского кода; training experiments не выполнялись. |
| BK-031 / 01.10 | [RRSI regularized harness evolution](https://arxiv.org/html/2609.24972v3) | **проверен экспериментально** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/rrsi.md), [Опыт](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-rrsi-harness2-overfit-lab.md) | Реальные функции отбора RRSI и тесты на 105 синтетических случаях; end-to-end LLM evolution не воспроизведена. |
| BK-032 / 01.10 | [Context Language Models](https://arxiv.org/html/2609.37725v1) | **разобран** | — | Полный текст и код найдены; не проверена эффективность на собственных задачах; лицензия CC BY-NC ограничивает использование. |
| BK-033 / 02.10 | [Karpathy answer format and comprehension](https://x.com/karpathy/status/2105819303471976479) | **исключён** | — | Социальный пост про формат ответов; нет первичного сравнительного исследования для русских DBA-задач. |
| BK-034 / 04.10 | [Karpathy-loop / AutoResearch video](https://www.youtube.com/watch?v=qLfSDQ5NGh0) | **ожидает проверки** | — | Видеопересказ; результаты оптимизационных запусков и защита от overfit не воспроизведены. |
| BK-035 / 04.10 | [Google MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox) | **проверен экспериментально** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/mcp-toolbox-postgres.md), [Опыт](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-mcp-toolbox-vs-wikipg-postgres-lab.md) | Реальный MCP Toolbox v1.15.0 и PostgreSQL GUC fixture, 160 RPC; не production. |
| BK-036 / 05.10 | [Advent of Agents](https://adventofagents.com/) | **исключён** | — | Сборник учебных уроков; конкретная новая проверяемая методика из ссылки не выделена. |
| BK-037 / 05.10 | [youtube-skills](https://github.com/ZeroPointRepo/youtube-skills) | **ожидает проверки** | — | Не проверен внешний TranscriptAPI, тарифы и устойчивость извлечения видео. |
| BK-038 / 06.10 | [NoPayWall model credit aggregator](https://nopaywall.io/) | **исключён** | — | Сторонний агрегатор модельных кредитов без подтверждённых гарантий провайдера и обработки секретов. |
| BK-039 / 07.10 | [VeriHarness](https://arxiv.org/html/2610.00972v1) | **проверен экспериментально** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/veriharness.md), [Опыт](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-veriharness-agent-config-offline.md) | Реальные компоненты VeriHarness и agent-config проверены offline; нет полноценного LLM-оркестрационного цикла. |
| BK-040 / 08.10 | [DeLM decentralized agents](https://arxiv.org/html/2606.10662v3) | **разобран** | — | Научный полный текст изучен; децентрализованный агентный рантайм не воспроизводился. |
| BK-041 / 08.10 | [Inspektor Gadget eBPF](https://github.com/inspektor-gadget/inspektor-gadget) | **ожидает проверки** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/inspektor-gadget.md), [Проверка допуска](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-bk041-inspektor-gadget-gate.md) | Официальный CLI v0.57.0 проверен, но BPF_MAP_CREATE вернул EPERM; живые eBPF events и RCA-overhead не проверены. |
| BK-042 / 10.10 | [Claude Code comprehensive course](https://github.com/wesammustafa/Claude-Code-Everything-You-Need-to-Know) | **исключён** | — | Обучающий курс; не демонстрирует отдельное новое исследование или целевой runtime improvement. |
| BK-043 / 11.10 | [Unsloth Qwen3.5 4B decision model](https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth) | **ожидает проверки** | — | Описан training tutorial; реальная локальная модель и данные для 8 GB VRAM не проверялись. |
| BK-044 / 12.10 | [Unsloth Qwen3.5 decision model — repeat](https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth) | **исключён** | — | Точный повтор BK-043; второй независимой работы нет. |
| BK-045 / 12.10 | [Animator](https://github.com/ashishjamarkattel/Animator) | **исключён** | — | Видео-генератор не покрывает текущую измеримую инженерную задачу; время вывода зависит от внешних моделей. |
| BK-046 / 12.10 | [QwenGyre](https://arxiv.org/html/2609.33848v1) | **исключён** | — | Работа требует масштабного GPU RL-training; текущая инфраструктура/проекты такой контур не подтверждают. |
| BK-047 / 13.10 | [Anthropic agent automations guide](https://claude.dev/blog/building-effective-agent-automations/) | **ожидает проверки** | — | Официальные советы не проверены на конкретной автоматизации или reproducible workflow. |
| BK-048 / 16.10 | [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) | **ожидает проверки** | — | Не измерено качество графа вызовов на актуальных исходниках одного проекта. |
| BK-049 / 16.10 | [Prompt Motion library](https://prompt-motion.com/) | **исключён** | — | Сборник motion-подсказок — источник оформления, не метод повышения надёжности продуктов. |
| BK-050 / 16.10 | [Chartli](https://github.com/ahmadawais/chartli) | **ожидает проверки** | — | CLI-диаграммы проверялись только как репозиторий; нет контракта для графиков DBA/логов. |
| BK-051 / 18.10 | [Harness²](https://arxiv.org/html/2610.14224v1) | **проверен экспериментально** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/harness2.md), [Опыт](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-rrsi-harness2-overfit-lab.md) | Выполнены реальный selector Harness² и upstream tests; модельные Propose/Probe/Compose не воспроизводились. |
| BK-052 / 19.10 | [Anatomy educational visualizations](https://github.com/wheresryan22/anatomy) | **исключён** | — | Учебная анатомическая визуализация; отсутствует подтверждённый target и проверка научной корректности. |
| BK-053 / 22.10 | [Yahont CE](https://github.com/pipedude/yahont-ce) | **ожидает проверки** | — | Нужна проверка лицензий подпапок, read-only deploy и качества ответов на локальном корпусе. |
| BK-054 / 23.10 | [Anthropic + Theorem formal verification](https://www.anthropic.com/research/formal-verification) | **разобран** | — | Официальная инженерная статья разобрана; формальная гарантия зависит от полноты спецификации. |
| BK-055 / 23.10 | [Claudemy](https://github.com/assafkip/claudemy) | **исключён** | — | Генерация обучающего аудио без подтверждённой востребованности, проблематики и надёжного oracle. |
| BK-056 / 24.10 | [Microsoft sequential diagnosis with LMs](https://www.science.org/doi/10.1126/science.aeh7930) | **разобран** | — | Полная Science-статья по последовательной диагностике разобрана отдельно; clinical deployment не проверен. |
| BK-057 / 28.10 | [SLEEP continual learning](https://arxiv.org/pdf/2606.03979) | **исключён** | — | Полноценное continual-training исследование, а не агентная память; нет управляемого обучения модели. |
| BK-058 / 31.10 | [Google Project Chrysalis](https://developers.googleblog.com/architecting-governed-self-evolving-ai-agents-on-gemini-agent-platform/) | **разобран** | — | Официальный архитектурный материал разобран; vendor ROI не подтверждён независимыми результатами. |
| BK-059 / 01.11 | [IPFire fireperf](https://www.ipfire.org/fireperf) | **проверен экспериментально** | [Карточка](https://github.com/Artemedi/research-hub/blob/main/studies/ipfire-fireperf.md), [Опыт](https://github.com/Artemedi/research-hub/blob/main/reports/2026-11-04-bk059-fireperf-loopback.md) | Авторская сборка 0.3.0, 12 ограниченных изолированных loopback-прогонов, 240/240 TCP и отрицательный контроль; не производство, не iperf3 A/B. |
| BK-060 / 01.11 | [dsh-superagent prototype](https://github.com/deepseek-ai/dsh-superagent-prototype) | **ожидает проверки** | — | README прямо называет проект прототипом; отсутствует воспроизводимый security/runtime test. |
| BK-061 / 01.11 | [ASCII Sharks](https://github.com/stackedlol/ascii-sharks) | **исключён** | — | ASCII-визуализация не имеет установленного ROI для задач проектов. |
| BK-062 / 02.11 | [Reverse Engineer Anything (REA)](https://github.com/morluto/rea) | **ожидает проверки** | — | Не установлен безопасный sandbox и допустимость работы с бинарниками/лицензиями. |
| BK-063 / 02.11 | [Tencent Hyra 2.0](https://hy.tencent.com/research/hyra2) | **ожидает проверки** | — | Сохранился анонс; полный методологический текст не подтверждён. По одной странице scientific verdict невозможен. |
| BK-064 / 02.11 | [DeepSeek Harness Creator Mode examples](https://cdn.deepseek.com/harness/dsh-creator-mode-prompt-collection-en.html) | **ожидает проверки** | — | Есть официальные примеры, но не tested transferable skill/protocol. |
| BK-065 / 03.11 | [Vercel Agent Desktop](https://github.com/vercel-labs/agent-desktop) | **ожидает проверки** | — | Существование code/README подтверждено; требуется disposable GUI/Wayland тест и privacy gate. |

## Чего фактически не хватало в research-hub

1. `research-hub/studies/INDEX.md` изначально индексировал преимущественно **научные наблюдения DSH**, а Telegram-закладки от 3 ноября жили в отдельной инвентаризации. Поэтому **отсутствие карточки НЕ означает отсутствия исходного анализа**; это может быть пробел каталогизации.
2. Для BK-001, BK-003, BK-031, BK-035, BK-039, BK-051 существуют **ограниченные лабораторные результаты**, но их нельзя объявлять воспроизведением всего исследования или внедрением.
3. BK-025 и BK-034 опираются на пересказы видео, BK-063 — на анонс без проверенного полного метода. **Не считать** их полным научным обзором. Для научных работ после поиска законных полных текстов: если доступа так и нет — `FULL_TEXT_UNAVAILABLE` и исключение из подробного научного анализа.
4. Сюжеты, выбранные в промежуточных экспериментах (BenchShield, NovaFabric, LIMBO), **не являются** строками исходного Telegram-списка. BIRD-RL также добавлен как внешний кандидат и не проведён экспериментально. Их результаты учитываются в общей библиотеке, но **не засчитываются** как последовательное закрытие Telegram-подборки.

## Следующая проверка без искусственного приоритета DSH

- **BK-041 Inspektor Gadget (A):** изолированное eBPF-наблюдение Linux/PG при подтверждённых правах и безопасном уровне нагрузки. Исходный приоритет A, фактический тест ещё не выполнен.
- **BK-059 IPFire fireperf (разобран):** только disposable сетевой стенд, ограничения нагрузки на SAN/SMB и отдельные IO/latency oracles, без stress production.
- **BK-050 Chartli (B):** применимость к графикам диагностических отчётов `akuzlogparser` при наличии настоящего контракта входного формата.
- **BK-014 alphaXiv OpenResearch (A):** provenance research-hub по одному доступному полному тексту, с DOI/version/citation проверки; не модельные пересказы.
- **BK-048 Understand Anything (B):** тест графа вызовов на зафиксированном исходнике отдельного проекта с независимым oracle.

**Не внедрено:** никакие production-проекты, рабочие агенты, публикации TelegramBot или DB-сервисы этим аудитом не изменены. Сверка исследовательских карточек и статусов — документальная операция.

**Трассируемость:** [старый исторический индекс](../studies/INDEX.md), [отчёт по избранному Vectorless/DBA](2026-11-03-bookmark-hypotheses-offline-experiments.md), [pgbot](2026-11-04-pgbot-postgresql-lab.md), [RRSI/Harness²](2026-11-04-rrsi-harness2-overfit-lab.md), [MCP Toolbox](2026-11-04-mcp-toolbox-vs-wikipg-postgres-lab.md), [VeriHarness](2026-11-04-veriharness-agent-config-offline.md).
