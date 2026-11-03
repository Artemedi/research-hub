# Закрытие исторических пробелов: 3–15 сентября 2026

**Выполнено:** 2026-11-03. **Источники:** [15 сентября Research Watch](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md), [решения владельца от 30 октября](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md), [хронологический индекс DSH](../archive/dsh/knowledge/research/README.md), [математическая инженерная оценка от 7 октября](../archive/dsh/knowledge/research/2026-10-07-math-models-assessment.md).
**Разграничение дат:** ToolGrad full paper опубликован на ACL в июле 2026, тогда как блог Google и наш Research Watch появились в сентябре. Random Attention v1 — 3 сентября; первичный полный дайджест 03–09 сентября не сохранился.
**Проверка:** 6/6 доступных полных первичных научных PDF (5 arXiv v1 + 1 ACL proceedings PDF) прочитаны по методу, результатам и ограничениям и проверены SHA-256; без независимой репликации. CVE отдельно оценён по полному публичному техническому раскрытию, **не** как научная статья. Математический отчёт классифицирован как уже проведённая оригинальная инженерная работа, не новый paper.
**Evidence statuses:** FULL_TEXT_REVIEWED_2026-11-03 (6); PRIMARY_TECHNICAL_DISCLOSURE (1); EXISTING_INTERNAL_ENGINEERING_RECORD (1); ORIGINAL_DIGEST_NOT_ARCHIVED (03–09 Sep).
**Проектное соответствие:** [явная двусторонняя матрица](2026-11-03-project-mapping-september-gaps.md), pinned project-registry@b5c7c8647b59e248c720d8a04b2ebc9e5eaafc2d. Все выводы PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE; **никакой source-code production аудит не проводился**.

## По каждой ранее непроверенной работе

| Источник | Что установлено по полной методике | Главная оговорка | Решение |
| --- | --- | --- | --- |
| [BenchShield — reward-integrity instrumentation](../studies/benchshield.md) | Авторы сообщили full-chain recall 77–100% против 23–94% для agentic scanner baseline; runtime accuracy 96% только среди покрытых verdict cells, coverage 87,5% (Table 4; 144 runnable cells). | Нужна instrumentation в контролируемой benchmark infrastructure; текущая schema fixed, semantics некоторых действий требует аудитора. | P1_EVAL_INTEGRITY_DESIGN |
| [SWRouter — multi-turn context-aware model routing](../studies/swrouter.md) | Авторы сообщают улучшение на 16,26% против лучшей индивидуальной модели и на 8,22% относительно Conv-ID Context (в авторской формулировке). | Порог, dataset, модельный pool и cost функций не универсальны; LLM-based scoring и контекстная конструкция могут переоценивать маршрут. | P2_SHADOW_ROUTER_TEST |
| [ToolGrad — verified chain-first tool-use dataset generation](../studies/toolgrad.md) | Generation pass 99,8% против 63,8% DFS, средняя длина gold chain 3,4 против 2,1; 500 сгенерированных примеров использованы для SFT. | Обучение SFT и single-turn tool use; авторы явно исключают multi-turn agents (BFCL v3/v4), оставляют RL как future work. | P1_BOUNDED_TEST_GENERATOR |
| [REVA — Reusable Evidence View Aggregation](../studies/reva.md) | Авторы сообщают +1,0…5,8 quality points и снижение request-time compression overhead в 5,3–15,6 раза против конкретных compressor baselines; materialization занимает менее 40 ms. | Нужны исторические attention traces **целевого генератора**, недоступные через многие closed APIs; исторический proxy по tool usage — уже другая гипотеза. | P2_ONLY_WHERE_ATTENTION_SIGNAL_EXISTS |
| [NovaFabric — tamper-evident agent run evidence](../studies/novafabric.md) | Mocked replay не делал новых model calls в 10/10 scenarios, но **полностью завершились только 2/10 tool-using workloads**: tool responses не подменялись, внешние вызовы оставались live. | Author-led preprint, прототипное состояние и несогласованные paths provenance: в полном v1 отозван ранее заявленный запрос parent-child «20/20» из-за отсутствующих данных в capsule. | P2_MINIMAL_REPLAY_BUNDLE_ONLY |
| [Random Attention — KV eviction for reasoning](../studies/random-attention.md) | При сопоставимой точности reasoning tasks authors report vLLM throughput на 32–43% выше TriAttention при matched budget, и 1,6–2,7× относительно uncompressed full attention в выбранных settings. | Требуется доступ к physical KV cache и интеграция в vLLM/другой controlled serving engine; архитектура обычных cloud API маршрутизаторов этого не предоставляет. | DEFER_NO_VERIFIED_KV_SERVING_TARGET |

## Правила для исторических решений

1. Принятые ранее **исследовательские приоритеты** 15 сентября сохраняются: BenchShield — контролировать eval integrity; SWRouter — не внедрять до offline; ToolGrad — только sandbox generator; REVA — пропустить текущую реализацию; NovaFabric — принять минимальный replay/evidence принцип, не полный framework. Данный новый scientific review **не перезаписывает решения владельца**.
2. В NovaFabric v1 полнота replay — лишь 2/10 tool-using workloads, и средняя capture completeness после исправлений 0,652 ± 0,064; эти ограничения запрещают формулировку «готовый детерминированный replay».
3. В ToolGrad полный peer-reviewed ACL текст исследует SFT и BFCL single-turn; он не подтверждает multi-agent task success и не готов к небезопасным tool executions.
4. Random Attention относится к управляемому KV serving; нельзя считать SWRouter или API-инференс эквивалентом backend. NO_CURRENT_TARGET — положительный итог отбора, не ошибка.

## Дополнительное устранение исторического пробела: Auto Mode appendices

У [Red-Teaming Auto Mode](../studies/red-teaming-auto-mode.md) ранее оставался статус `APPENDICES_NOT_INSPECTED`. На 2026-11-03 проверен **полный** [arXiv 2609.19587v1 PDF](https://arxiv.org/pdf/2609.19587v1), 23 страницы, SHA-256 `a17983591a1b420087ef918adf4d4995c97049c030f67b59049ab0d7caea058f`, включая приложения A–F. Проверены детали serialized transcript/role boundaries, attacker affordances, monitor model, replay/arena/simulation и limitations. В приложении F авторы сами отмечают риск overelicitation в упрощённой compaction simulation и экспериментальность LLM Dungeon Master. Никакой текущий DSH дефект не воспроизводился. Историческое решение KEEP сохраняется; `PDF_APPENDICES_REVIEWED_2026-11-03`, не VERIFIED_FIT.

## Отдельный технический источник: CVE-2026-82533

- [Полный разбор OX Research](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/), 8 сентября 2026; [отдельная карточка с ограничениями](../studies/cve-2026-82533-technical-disclosure.md). Публикация описывает проверяемый anti-pattern «доверие к клиентскому Host как аутентификации», control-plane authority escalation и исправленную версию 0.1.2-alpha.1.
- **Не** исследование новых агентных метрик, не evidence уязвимости наших актуальных репозиториев, не независимое воспроизведение. Предложены только fake local-control authorization regressions.

## Отдельная оригинальная инженерная оценка: 7 октября

- [Математические модели DSH](../archive/dsh/knowledge/research/2026-10-07-math-models-assessment.md) уже включают собственные расчёты/локальные тесты: byte caps, Wilson/sample sizing, TypeScript AST oracle и гонки таймеров. Это **не отдельная статья** и не непрочитанный источник; оставлена в исходном неизменяемом архиве без создания ложного paper ID.

## Оставшаяся неопределённость по полноте архива

Исторический Research Watch за 03–09 сентября **не был сохранён полностью**. Из его источников архив явно называет только Random Attention, теперь получивший полную научную карточку. Таким образом **KNOWN_NAMED_CANDIDATES_REVIEWED**, но нельзя утверждать, что не существовало других неизвестных записей или публикаций. Статус недоступного исторического текста: ORIGINAL_DIGEST_NOT_ARCHIVED, не FULL_TEXT_UNAVAILABLE у прочитанной Random Attention.

## Итог и контроль качества

Шесть PDF документов с первичными методами, результатами, ограничениями и SHA-256; полный инженерный security disclosure отдельно; исходные архивные документы не менялись. Проектные соответствия являются гипотезами по PROJECT.md, поэтому не санкционируют код, CI, GitHub Issues и production эксперименты.
