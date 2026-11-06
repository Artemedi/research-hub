# BK-025 — Unreal Agent: первоисточник, исходники и проверка стоимости

**Дата проверки:** 2026-11-06. **Класс:** полный инженерный source review, не peer-reviewed эксперимент и не собственный A/B. **Статус:** `SOURCE_REVIEWED / BENCHMARK_COST_NOT_INDEPENDENTLY_RECONCILED / RUNTIME_AB_NOT_RUN`.

## 1. Источники и точная атрибуция

- Исходная Telegram-закладка BK-025 от 26.09.2026: [YouTube eFBSlgXG3U0](https://www.youtube.com/watch?v=eFBSlgXG3U0). Пользователь предоставил транскрипт в `Вставленный текст(20261105-225605).txt` (SHA-256 `1fc3abc0e8bee55cada7ab468df2a254194ae2926489e822de253226a9c2e284`). **Тождество исходному видео самостоятельно не удостоверено**: доступ к YouTube ранее потребовал авторизации. Сведения ниже из независимых официальных материалов не означают верификацию содержания видео.
- Полный официальный первичный инженерный материал, предшествующий видео: [Unreal Agent, Unreal Labs, 22.09.2026](https://unreallabs.ai/blog/unreal-agent/). Он содержит механизм, сравнительные таблицы и прямые Harbor job IDs. Это **не** научная публикация и не самостоятельная репликация авторами обзора.
- [Исходный Go-код, README и benchmark adapter — unreallabsai/unreal-agent@a5f3fd13032737142916523ae4344c392292f9d5](https://github.com/unreallabsai/unreal-agent/tree/a5f3fd13032737142916523ae4344c392292f9d5), MIT. Снимок получен как read-only Git checkout на Bazzite в `/tmp/bk025-unreal-agent-20261106`; локальные проекты не изменялись. Указанный SHA относится к состоянию **06.11.2026**, а не автоматически к исполняемому benchmark-бинарнику сентября; Harbor bundle имеет свой revision.
- Более поздняя [статья об async-compaction от 06.10.2026](https://unreallabs.ai/blog/long-horizon-agents-at-half-the-cost/) описывает отдельное усовершенствование. Её данные SWE-Marathon **не переносим** на первоначальный BK-025 benchmark.

## 2. Проверяемое техническое устройство

| Факт, подтверждённый исходниками | Pin и область кода | Что ещё не установлено |
| --- | --- | --- |
| Coordinator обслуживает tool-call statuses, dispatch операций и completion events вне линейного цикла ожидания каждой команды | [`harness/coordinator/loop.go`](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/harness/coordinator/loop.go#L90-L150), [`#L796-L900`](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/harness/coordinator/loop.go#L796-L900) | Уменьшение числа **реальных** LLM turns на задачах пользователя |
| Context builder формирует промежуточный результат `Tool call is still running`, затем заменяет ожидающий элемент готовым результатом | [`harness/contextbuilder/builder.go:16, 122–145`](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/harness/contextbuilder/builder.go#L120-L146) | Совместимость двойного tool-result в каждом API provider; официальный блог описывает отказы некоторых провайдеров |
| Хранилище сессий и manager операций разделены; у scheduler есть тесты persistence, повторной доставки, steering, recovery | [`harness/sessionstore/localfile/`](https://github.com/unreallabsai/unreal-agent/tree/a5f3fd13032737142916523ae4344c392292f9d5/harness/sessionstore/localfile), [`harness/coordinator/recovery_sequences_test.go`](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/harness/coordinator/recovery_sequences_test.go), [`scheduling_test.go`](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/harness/coordinator/scheduling_test.go) | Эти тесты **прочитаны**, но `go test` на Bazzite **не запускался** (Go toolchain отсутствует) |
| Harbor интеграция фиксирует source revision, binary hash и token usage, но явно назначает `context.cost_usd = None` | [`benchmarks/harbor/src/harness_harbor/agent.py`](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/benchmarks/harbor/src/harness_harbor/agent.py), [Harbor README](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/benchmarks/harbor/README.md) | Нельзя считать, что авторские суммы внесены адаптером и подтверждены Harbor; Harbor может получать billing из других источников |
| [SWE-Marathon compaction](https://unreallabs.ai/blog/long-horizon-agents-at-half-the-cost/) сохраняет system/recent context, суммирует среднюю часть и не останавливает pending tools | [`harness/contextbuilder/compaction.go`](https://github.com/unreallabsai/unreal-agent/blob/a5f3fd13032737142916523ae4344c392292f9d5/harness/contextbuilder/compaction.go) | Затраты на summary requests, semantic drift, cache invalidations и tail risk при compaction отдельно не измерены |

**Техническая гипотеза:** event-driven tool orchestration позволяет избежать модельных запросов, цель которых — лишь спросить состояние длительного теста, и упаковать независимую работу между осмысленными decisions. Но async сама по себе не означает меньше токенов, не сокращает длительность обязательной последовательной операции и добавляет complexity: pending state, retries, out-of-order results, cancellation, provider semantics, memory and output persistence.

## 3. Benchmark и независимая сверка

[Первая официальная статья](https://unreallabs.ai/blog/unreal-agent/) приводит GPT-6 Astra `xhigh`; далее **все доллары и pass rates — авторские утверждения**, а не собственные результаты.

| Benchmark | Unreal Agent | Codex | Вычисленная экономия | Сравнимость и evidence |
| --- | --- | --- | --- | --- |
| Terminal-Bench 4.0 | 57.9%, **$1,428** | 57.9%, **$2,350** | **39.23%** | Codex — **leaderboard baseline**, не парный прогон, в таблице нет его token/turn деталей; Unreal [Harbor job](https://hub.harborframework.com/jobs/27133053-2015-46f3-8c72-6b6910859da6) |
| SWE-Atlas QnA | 65.8%, **$936** | 63.3%, **$1,303** | **28.17%** | [Unreal job](https://hub.harborframework.com/jobs/3d2fa057-e11c-4be0-a962-e8be81b87709), [Codex job](https://hub.harborframework.com/jobs/11a440fb-b1c4-473b-98a6-907500b3fdaf); разные success rates |
| DeepSWE 1.1 | 72.4%, **$1,367** | 69.0%, **$1,633** | **16.29%** | Авторские суммы и связанные Harbor runs; не 40% |
| ALE-CLI | 30% full pass, **$217** | 29% full pass, **$292** | **25.68%** | Автор сообщает, что эти runs не находятся в Harbor |

**Самостоятельная проверка публичного Harbor HTML 06.11.2026 (read-only HTTPS, без cookies):**

- **Terminal-Bench Unreal job:** 330 trials; средняя reward отображается как `0.58`, токены `608,400,409`, 96% cache hit. **Inference cost: «No per-trial cost available»**. Нельзя независимо доказать сумму $1,428 по этой публичной странице.
- **SWE-Atlas Unreal job:** 372 trials; avg reward `0.63`, токены `329,419,580`, 90% cache hit. **Inference cost: «No per-trial cost available»**. Нельзя независимо подтвердить $936 по этой странице.
- **SWE-Atlas Codex job:** 372 trials; avg reward `0.60`, токены `612,065,274`, 94% cache hit; **Harbor inference cost $1,356.18**. В официальной статье **$1,303** — разница **$53.18 / 4.08%** относительно указанной в статье суммы. Не доказано, вызвана ли разница учётом errors, фильтрацией, тарификацией либо другими правилами агрегации.
- В пользовательском транскрипте указан Codex «$133» для Atlas, тогда как на **текущей** официальной странице написано **$1,303**. Нельзя установить, было ли это исправленным издательским typo или ошибкой транскрипта без независимого архивного снапшота. Заявление «$133 против $1,356.18» **не подтверждается текущим первоисточником**.
- Отсутствие стоимости на Harbor — **отсутствие доступного свидетельства**, а не доказательство нулевой стоимости или ложности авторских сумм. Cache hit % нельзя превращать в долларовую экономию без cached/new/output breakdown, ценовых тарифов и revision.

**Вывод о доказательной силе:** есть **verified source mechanism + vendor benchmark tables + independently inspected public job counters**, но нет сопоставимого **исходного cost ledger** для Unreal и нет нашего A/B. Следовательно, нельзя заявлять «DSH станет на 40% дешевле» или что одинаковый pass rate гарантирует одинаковую надёжность отдельных задач.

## 4. Research → Project: адресная оценка по реестру

За основу взят профиль [Artemedi/project-registry@838b86a28fcaa3440eeddbe147b6188e0d177963](https://github.com/Artemedi/project-registry/tree/838b86a28fcaa3440eeddbe147b6188e0d177963). **Project fit — гипотеза, не одобрение внедрения.**

| Проект / fit | Проблема и предметное соответствие | Контракт и следующий gate |
| --- | --- | --- |
| **[dsh-runtime](https://github.com/Artemedi/dsh-runtime)** — главный `CANDIDATE` | Собственный Node/TS Cordis agent-loop: tool orchestration, context compression и long-session continuation непосредственно соответствуют источнику | Сначала сравнить с уже имеющимся `benchmarks/agent-continuation/` и event loop на **pinned HEAD**; исключить уже реализованный event-driven подход. **CVE-2026-82533 остаётся единственным P0 приоритетом безопасности; эксперимент без патча — только disposable/offline** |
| **[agent-config](https://github.com/Artemedi/agent-config)** — `MEASUREMENT_CANDIDATE` | Agent hooks, review и trace могут служить сборщиком метрик повторных poll-turns и token taxonomy | Конфигурируемые hooks не равны асинхронному runtime; **не** переносить сюда Go coordinator |
| **[HermesAgent](https://github.com/Artemedi/HermesAgent)** — `SECONDARY_TRIAGE` | Gateway scheduling и длительные tools потенциально создают лишние status turns | Это git-tracked live config, не SDK; без логов провайдера и symbol-level seam нельзя утверждать, что он сейчас делает model-based polling |
| **[sequential-rca](https://github.com/Artemedi/sequential-rca)** — `SECONDARY_TRIAGE` | Несвязанные read-only evidence requests при DBA расследованиях можно потенциально распараллелить | Но текущий offline evidence gateway и логические зависимости требуют более сильного проверенного seam; не вызывать SQL/production |
| **[dsh](https://github.com/Artemedi/dsh)** — `REFERENCE_ONLY` | Контрольный research/backlog и порядок решений | Control-plane — не целевой runtime, практическая интеграция в `dsh-runtime` |
| **[AKUZ](https://github.com/Artemedi/AKUZ)** и **[TelegramBot](https://github.com/Artemedi/TelegramBot)** — `NO_DIRECT_FIT` | Ни OLTP SQL план, ни публикация video digest не улучшаются сами по себе от замены agent-loop | Возможная польза только через другие агентные компоненты; не создавать прямых backlinks |

Не считать «совместимое название проекта» подтверждённым code seam. Все остальные профили реестра не имеют более убедительной прямой связи, чем перечисленные candidate/reference; автоматических backlink-изменений в приватных проектных карточках не делалось.

## 5. Измеримый минимальный A/B — ПОКА НЕ ВЫПОЛНЕН

После устранения P0-CVE либо в **полностью изолированном одноразовом runtime**:

1. **Контроль A:** существующий `dsh-runtime@PIN` как есть. **B:** узкий opt-in event-driven scheduler только для independent long-running read-only tools, либо Unreal runner как внешний изолированный comparator. Не менять одновременно модель, промпт, политику инструментов и hardware.
2. **Набор:** 30 обезличенных fixtures (long-running build/test, independent inspection, slow/fast completion, sequential dependency, process timeout, cancellation, duplicate/lost completion, late result, crash/resume), по 3 независимых seeds; immutable oracle на корректное окончание, filesystem effects и отсутствие пропущенных результатов.
3. **Метрики:** pass@1/errors и равенство oracle, LLM turns, total/cached/new input и generated tokens с явным tariff snapshot, actual model API cost, p50/p95 wall/TTFT, CPU, peak RSS, process IO, persisted state size, number of polling calls, event loss. Платных запросов, GPU и live-agent runs в настоящем обзоре **0**.
4. **Отрицательные контроли:** tools, которые **нельзя** выполнять параллельно, stale/duplicated operation events, провайдер, отвергающий running→final tool result, compaction while pending, abort mid-write, resume after kill. Нельзя компенсировать снижение стоимости потерей корректности, появлением небезопасного shell execution или ростом p95.
5. **Критерий выхода:** нет критических correctness/recovery regressions, воспроизводимое сокращение *оплаченных* токенов или turn overhead при сравнимой корректности и строго посчитанная дополнительная стоимость scheduler/IO. Rollback = вернуть baseline scheduler/config; никакого merge или live-deploy по результату одной синтетики.

**Трейдоффы:** возможно ниже tokens/cost при overlap независимых tools; за это платим более сложной причинностью событий, хранением pending state, расходом IO и риском неидемпотентных повторов. Простая замена всей архитектуры DSH на Go harness нарушает YAGNI — **не рекомендуется** без локального измерения bottleneck.

## 6. Итог и следующий переход

**BK-025 → «разобран»** в смысле официального полного инженерного материала и pinned source; **не «проверен экспериментально»**, **видео отдельно не удостоверено**, **авторский cost advantage не подтверждён собственным benchmark**. Адресная проектная гипотеза: `dsh-runtime` и измерительный слой `agent-config`; Hermes и sequential-rca — только вторичные triage, AKUZ SQL/TelegramBot — no direct fit.

**Рекомендация по затрате времени:** не запускать полный TerminalBench за сотни/тысячи долларов ради этого пункта. ROI есть у дешёвого bounded A/B **после** устранения P0 CVE и доказательства, что базовый DSH действительно тратит модельные turns на polling. Если такого bottleneck нет — `NO_ACTION / YAGNI`, переход к BK-034.

**Проверка настоящего обзора:** читались тексты/исходники и фактические публичные HTML-counter данные, проведена арифметическая сверка; локальные Go tests и agent runtime не запускались; `npm/pnpm`, paid LLM, root, GitHub production, AKUZ и работающий DSH не менялись.
