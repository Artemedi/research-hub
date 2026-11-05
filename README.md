# Research Hub — исследования для всех проектов

Публичный независимый архив научных и инженерных исследований, проверок их применимости к проектам и минимальных экспериментов.

## Разделение ответственности

- [project-registry](https://github.com/Artemedi/project-registry) — **каталог проектов**: 44 репозитория Artemedi и отдельный проект коллеги, их задачи, ограничения и источники. Не хранилище результатов научного поиска.
- **research-hub (этот репозиторий)** — **единое место для новых обзоров** и истории исследовательских выводов по всему портфелю.
- [DSH](https://github.com/Artemedi/dsh) — управляющие документы и архитектурные решения именно DSH. Его прежний Research Watch сохранён как архив, но новые общепортфельные обзоры публикуются здесь.
- [paper2agent-index](https://github.com/Artemedi/paper2agent-index) — отдельный производный индекс экспериментального Paper2Project; он не заменяет этот архив и не обязателен для его работы.

## Навигация

- [MAI-DxO / SDBench — последовательная диагностика](studies/sequential-diagnosis-language-models.md) — [первоначальный полнотекстовый обзор и план](reports/2026-11-05-sequential-diagnosis-trinmedicalbot-review.md) → [144 Wello A/B и внедрение Challenger v2 в TrinMedicalBot 05.11.2026](reports/2026-11-05-sequential-diagnosis-challenger-production-followup.md); клиническая проверка ещё не выполнена, sequential-rca остаётся кандидатом.
- [RESEARCH_POLICY.md](RESEARCH_POLICY.md) — правила доступа к полным текстам, проверки кода, оценивания и публикации.
- [Проверенные ранее работы — 16 отдельных карточек](studies/INDEX.md) — индекс с доказательствами из DSH и ссылками на исходные решения. **Не** повторная научная экспертиза.
- [Научное ревью за 6–12 октября 2026](reports/2026-11-03-review-of-2026-10-06-to-12.md) — семь ранее не проверенных работ, полные PDF v1, методология, результаты, ограничения и предложения экспериментов; без внедрения.
- **[Научное ревью за 12–19 октября 2026](reports/2026-11-03-full-text-review-2026-10-12-to-19.md)** — восемь полных PDF v1, первичная методология, численные результаты, limitations и безопасные A/B гипотезы.
- **[Какие проекты подходят работам 12–19 октября?](reports/2026-11-03-project-mapping-2026-10-12-to-19.md)** — восемь явных сопоставлений с профилями и верифицируемыми экспериментами.
- **[Какие исследования каким проектам подходят?](reports/2026-11-03-project-mapping-2026-10-06-to-12.md)** — матрица семи работ выпуска: реальные названия целевых проектов, тематическое обоснование, блокеры и первый проверяемый эксперимент.
- **[Какие старые исследования подходят проектам?](reports/2026-11-03-project-mapping-historical-16.md)** — 16 ранее оценённых исследований, ссылки на 13 проектных карточек, причины, ограничения и безопасные эксперименты.
- **[Полный обзор 20–26 октября 2026](reports/2026-11-03-full-text-review-2026-10-20-to-26.md)** — 7 полнотекстовых статей; полный METR internal report исключён.
- **[Матрица по проектам 20–26 октября](reports/2026-11-03-project-mapping-2026-10-20-to-26.md)** — 7 работ с конкретными кандидатами и измеримыми тестами.
- **[Полный обзор 27 октября — 2 ноября 2026](reports/2026-11-03-full-text-review-2026-10-27-to-11-02.md)** — 6 полнотекстовых статей по запуску шедулера от 2 ноября.
- **[Матрица по проектам 27 октября — 2 ноября](reports/2026-11-03-project-mapping-2026-10-27-to-11-02.md)** — 6 работ, включая условную применимость ATP.
- **[Закрытие ранних исторических пробелов (3–15 сентября)](reports/2026-11-03-historical-gap-closure-2026-09-03-to-15.md)** — полные источники BenchShield, SWRouter, ToolGrad, REVA, NovaFabric, Random Attention; техническая CVE и математическая записка отделены от статей.
- **[Матрица ранних работ → проекты](reports/2026-11-03-project-mapping-september-gaps.md)** — гипотезы применимости, исключения и обратные ссылки в приватном реестре.
- [Архив DSH и проверка происхождения](archive/dsh/ARCHIVE_MANIFEST.md) — 15 исторических файлов из `Artemedi/dsh/knowledge/research` без изменения содержимого, с SHA исходного коммита и хешами.
- [Исторический хронологический индекс DSH](archive/dsh/knowledge/research/README.md) — копия исходного индекса; ссылки на внешние DSH-документы открывать в оригинальном репозитории.
- [Повторный отбор старых работ для .NET/PostgreSQL-проекта коллеги](reports/2026-11-03-colleague-dotnet-retrospective.md) — исторические кандидаты, не новые исследования.

## Новые отчёты

- **[Sequential Diagnosis / TrinMedicalBot — выполненный A/B и production-внедрение 5 ноября 2026](reports/2026-11-05-sequential-diagnosis-challenger-production-followup.md)** — 144/144 технически успешных Wello-запроса (72 на arm), 44/44 локальных инфраструктурных теста, Challenger v2, проверка лекарств по источникам, очередь Telegram. `PRODUCTION_DEPLOYED / CLINICAL_REVIEW_PENDING`; исходный SDBench не воспроизводился.

- **[Предварительная Telegram BK → проектная матрица: 22 материала / 45 карточек](reports/2026-11-04-telegram-bk-preliminary-project-matrix.md)** — 51 прямых и 48 условных соответствий без лабораторных тестов; [машинно-читаемая версия](reports/2026-11-04-telegram-bk-preliminary-project-matrix.json). Исторические статусы полного разбора не изменены.
- **[BK-014 — alphaXiv OpenResearch: source audit, full-text gate, experiment provenance and portfolio fit](reports/2026-11-04-bk014-openresearch-review.md)** — 45 project profiles checked, only dsh-paper2agent shortlisted; OpenAlex/PubMed/bioRxiv expose abstracts rather than full text via orx; [engineering card](studies/alphaxiv-openresearch.md), no execution and no production approval.
- **[BK-002 — Tencent TeamAI CLI: upstream, fork, trust boundaries и проектное соответствие](reports/2026-11-04-bk002-tencent-teamai-cli-review.md)** — 45 карточек рассмотрены, найдено три соответствия; форк 13 commits ahead / 732 behind upstream, 6 конфликтов сухого слияния; [карточка](studies/tencent-teamai-cli.md), без runtime теста, без разрешения на обновление.
- **[BK-041 — Inspektor Gadget v0.57.0: проверка eBPF-доступа на Bazzite](reports/2026-11-04-bk041-inspektor-gadget-gate.md)** — официальный CLI/SHA проверены; unprivileged BPF_MAP_CREATE → EPERM, реальная трассировка не выполнялась; [карточка](studies/inspektor-gadget.md), [gate script](experiments/2026-11-04-bk041-inspektor-gadget-permission-gate.py).
- **[BK-059 — IPFire fireperf 0.3.0: авторский бинарник и loopback](reports/2026-11-04-bk059-fireperf-loopback.md)** — 12 ограниченных тестов × 20 TCP, нулевые отказы, проверка request/response, закрытый порт; [карточка](studies/ipfire-fireperf.md), [скрипт](experiments/2026-11-04-bk059-fireperf-loopback-lab.py). Не тест сети AKUZ.

- **[BK-053 — Yahont CE: source review и synthetic ID helper test](reports/2026-11-04-bk053-yahont-review.md)** — [карточка](studies/yahont-ce.md); retrieval не запускался.
- **[BK-050 — Chartli: source review и synthetic input tests](reports/2026-11-04-bk050-chartli-review.md)** — [карточка](studies/chartli.md); CLI не запускался.
- **[BK-048 — Understand Anything: source review и synthetic SQL tests](reports/2026-11-04-bk048-understand-anything-review.md)** — [карточка](studies/understand-anything.md); реальный граф не запускался.
- **[BK-047 — Anthropic agent automations: source review](reports/2026-11-04-bk047-agent-automations-review.md)** — [карточка](studies/anthropic-agent-automations.md); workflow не запускался.
- **[BK-043 — Unsloth decision model: source review](reports/2026-11-04-bk043-unsloth-decision-review.md)** — [карточка](studies/unsloth-decision-model.md); обучение и бенчмарки не запускались.
- **[BK-037 — youtube-skills: source review](reports/2026-11-04-bk037-youtube-skills-review.md)** — [карточка](studies/youtube-skills.md); внешний API не вызывался.
- **[BK-034 — Karpathy autoresearch: source review](reports/2026-11-04-bk034-autoresearch-review.md)** — [карточка](studies/karpathy-autoresearch.md); исходное видео недоступно, обучение не запускалось.
- **[BK-029 — 0-CODE: source review и synthetic guard tests](reports/2026-11-04-bk029-zero-code-review.md)** — [карточка](studies/zero-code.md); полный цикл не запускался.
- **[BK-028 — Hyperresearch: source review и synthetic citation fixture](reports/2026-11-04-bk028-hyperresearch-review.md)** — [карточка](studies/hyperresearch.md); полный pipeline не запускался.
- **[BK-026 — Julia 1: source review и synthetic probability fixture](reports/2026-11-04-bk026-julia-1-review.md)** — [карточка](studies/julia-1.md); модель не запускалась.
- **[BK-025 — Unreal Agent video: provenance и отсрочка](reports/2026-11-04-bk025-unreal-video-provenance.md)** — [карточка](studies/unreal-agent-bk025.md); исходное видео недоступно, метод не оценён.
- **[BK-024 — Local Knowledge Graph: обзор и synthetic graph tests](reports/2026-11-04-bk024-local-knowledge-graph-review.md)** — [карточка](studies/local-knowledge-graph.md); граф шагов модели, не готовый RAG.
- **[BK-022 — Microsoft Skill Recorder: обзор и synthetic privacy test](reports/2026-11-04-bk022-skill-recorder-review.md)** — [карточка](studies/microsoft-skill-recorder.md); запись и Copilot не запускались.
- **[BK-019 — Warp Skill Doctor: обзор и тест атрибуции](reports/2026-11-04-bk019-warp-skill-doctor-review.md)** — [карточка](studies/warp-skill-doctor.md); только синтетические данные.
- **[BK-016 — Claude Swarm: обзор ограничений и изоляции](reports/2026-11-04-bk016-claude-swarm-review.md)** — [карточка](studies/claude-swarm.md); подтверждённые кодом риски, динамический запуск не проводился.
- **[BK-011 — SIMURG: обзор и изолированные проверки](reports/2026-11-04-bk011-simurg-review.md)** — [карточка](studies/simurg.md); обнаружены ошибки AUROC и ограничения калибровки.
- **[BK-006 — Open Steps: инженерный обзор и ограниченная проверка хуков](reports/2026-11-04-bk006-open-steps-review.md)** — [карточка](studies/open-steps.md); выявлен пропуск изменения untracked-файла, качество ответов не измерено.
- **[Telegram-подборка: сверка всех 65 записей с research-hub (4 ноября 2026)](reports/2026-11-04-telegram-bookmarks-reconciliation.md)** — 63 уникальные темы, 12 ограниченных экспериментальных проверок, 26 разборов источников, 8 ожидают проверки (включая BK-041: проверены только права eBPF), 19 выведены из активной очереди (включая 2 повтора); [машинно-читаемая матрица](reports/2026-11-04-telegram-bookmarks-reconciliation.json). Список восстановлен из сохранённого аудита, не из дословного экспорта Telegram.

- **[LIMBO × TelegramBot: повторные публикации при неоднозначном HTTP POST (4 ноября 2026)](reports/2026-11-04-limbo-telegrambot-ambiguous-publish.md)** — оригинальный код LIMBO и реальный TelegramBot `main()`: 180 детерминированных случаев с fake сервисом, подтверждённый trade-off at-most-once/retry; [скрипт](experiments/2026-11-04-limbo-telegrambot-send-retry.py) и [JSON](reports/2026-11-04-limbo-telegrambot-send-retry.json). Без сетевых запросов и изменений production.

- **[NovaFabric v0.108.0: реальные Run Capsules и воспроизводимый replay (4 ноября 2026)](reports/2026-11-04-novafabric-real-capsules-replay.md)** — 20 подписанных toy-капсул, 40/40 подставленных tool responses, проверка границ mocked mode, 6 отрицательных seal-тестов; независимый DSSE/Merkle [verifier](experiments/2026-11-04-novafabric-independent-bundle-verify.py) и [реальный CLI-скрипт](experiments/2026-11-04-novafabric-real-capsule-lab.py).

- **[BenchShield: целостность reward и provenance (4 ноября 2026)](reports/2026-11-04-benchshield-reward-integrity-offline.md)** — независимый offline lifecycle replay: 100 фиктивных траекторий, 30 доказанных нарушений, 40 отказов от необоснованного вердикта; [Python-скрипт](experiments/2026-11-04-benchshield-reward-integrity-replay.py), [JSON-агрегаты](reports/2026-11-04-benchshield-reward-integrity-offline.json). Не запуск оригинального BenchShield.

- **[MCP Toolbox v1.15.0 vs Wiki_PG: PostgreSQL GUC (4 ноября 2026)](reports/2026-11-04-mcp-toolbox-vs-wikipg-postgres-lab.md)** — реальные MCP stdio-сеансы, 4 GUC × 20 повторений на каждый инструмент, независимый SQL-oracle, исторические снимки, контроль устаревания и read-only роли; [карточка](studies/mcp-toolbox-postgres.md) и воспроизводимые скрипты.

- **[RRSI / Harness²: переобучение harness при отборе (4 ноября 2026)](reports/2026-11-04-rrsi-harness2-overfit-lab.md)** — 105 синтетических задач train/validation/holdout; оригинальные функции выбора RRSI и Harness², негативный memorizer-control, независимая проверка эффекта; [повторяемый скрипт](experiments/2026-11-04-rrsi-harness2-selector-smoke.py).

- **[VeriHarness / agent-config — offline replay (4 ноября 2026)](reports/2026-11-04-veriharness-agent-config-offline.md)** — реальные deterministic gates VeriHarness и текущего review.py, 50 синтетических assertions, 16 артефактных комплектов, воспроизводимый [скрипт](experiments/2026-11-04-veriharness-offline-replay.py); **не** тест полной LLM-оркестрации.

- **[pgbot v0.9.0: эксперимент на PostgreSQL 18.3 (4 ноября 2026)](reports/2026-11-04-pgbot-postgresql-lab.md)** — управляемые инциденты autovacuum и locking, проверка JSON Schema и прав, повторные измерения, независимый oracle и проектная карточка [pgbot](studies/pgbot.md). Без production.

- **[Лабораторные проверки гипотез из избранного (3 ноября 2026)](reports/2026-11-03-bookmark-hypotheses-offline-experiments.md)** — FTS5 A/B на размеченных DBA-запросах, read-only PostgreSQL sandbox, agent-config baseline, проверка ссылок, блокеры и ограничения; приложен воспроизводимый скрипт.

Еженедельная задача «Исследования для портфеля проектов» читает актуальный `project-registry`, проверяет полный текст новых работ и исходные репозитории, затем сохраняет обзор в `reports/YYYY-MM-DD-portfolio-research.md`. Новую ссылку добавлять в этот раздел. Если значимых материалов нет, сохранять честный отчёт `NO_SIGNIFICANT_NEW_MATERIAL` без выдуманных рекомендаций.

Не перезаписывать прошлые отчёты: уточнения и исправления оформлять новой датированной записью со ссылкой на прежнюю.

## Безопасность и полномочия

Не коммитить секреты, персональные или медицинские данные, закрытый код коллег, production-логи/дампы и полные тексты чужих защищённых статей. Сохранять собственную аналитику, цитаты в допустимом объёме и ссылки на первоисточники.

Исследование или оценка `10/10` не означает одобрение реализации. GitHub Issues, изменение рабочего кода и production-эксперименты требуют отдельного решения владельца.
