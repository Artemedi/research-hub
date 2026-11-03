# DeepSeek Harness — research watch

За этот цикл нашлось **пять материалов, которые имеют реальную архитектурную точку приложения к DSH**, а не просто относятся к теме agents. Три из них я бы уже рассматривал как кандидатов на эксперимент.

Состояние базы: ваш `Artemedi/deepseek-harness:master` сейчас на `5dda764ed3aa…` от **8 сентября 2026**, релизный merge `dsh@0.1.5-alpha.1`; после 10 сентября коммитов в вашем `master` нет. Upstream уже дошёл как минимум до `c291e796…` от **10 сентября**, так что перед реальной реализацией этих идей стоит сначала синхронизировать fork.

Текущая архитектура DSH при этом очень удобна для таких экспериментов: routing можно вмешивать через `agent/request`, tool execution — через `tools/*`, история является durable session log, а стандартный agent loop остаётся отдельным заменяемым implementation. Experimental Agent Teams уже имеют durable roster/mailbox/task DAG поверх того же session log.

## 🥇 1. BenchShield — защита agent-evals от reward hacking

**Дата:** 10 сентября 2026  
**Источник:** [BenchShield — arXiv](https://arxiv.org/abs/2609.11028)

BenchShield предлагает не пытаться ловить cheating/reward hacking только постфактум, а описывать жизненный цикл benchmark как конечную модель событий и проверять фактическую траекторию агента относительно разрешённой модели. Есть две части: статический анализ возможных reward-hacking путей и runtime attribution по инфраструктурным событиям. На корпусе из более чем 31 тыс. agent runs runtime-анализ авторов достиг 96% accuracy, а full-chain recall заметно превысил agentic scanner baseline.

**Почему DSH подходит особенно хорошо.** Здесь почти идеальное совпадение архитектур. DSH уже утверждает принцип `model-visible means logged`; turn/step/tool lifecycle сохраняется как события, а tool execution проходит через отдельный guarded pipeline. То есть значительную часть instrumentation, которую BenchShield приходится добавлять поверх других harness, DSH уже генерирует естественным образом.

**Точка интеграции:** отдельный `dsh-eval-integrity` plugin, слушающий `session/event`, `tools/pre-execute`, `tools/post-execute`, `agent/request`, `step/start/end`. Reward/evaluator можно представить отдельным capability seam, которому запрещён доступ из agent realm.

**Ожидаемая польза:** гораздо более надёжные собственные benchmarks DSH и Skill Evolution. Особенно важно, если оптимизация skill/prompt начнёт автоматически искать способы повысить score: система сможет отличать улучшение поведения от эксплуатации evaluator.

**Риски:** BenchShield проверяет хорошо формализуемые evaluation boundaries. Для fuzzy LLM-judge evaluation доказательства будут заметно слабее.

**Практическая ценность: 9.5/10. Сложность: 5/10.**

**Минимальный эксперимент:** сделать 20–30 artificial eval runs с намеренно уязвимым scorer: workspace-файл с ожидаемым ответом, environment variable, writable result file и доступный evaluator endpoint. Проверить, можно ли только по DSH session/tool events автоматически классифицировать legitimate solve против reward tampering. Никакого изменения agent loop для этого не требуется.

---

## 🥈 2. SWRouter — routing модели с учётом многоходового контекста

**Дата:** 10 сентября 2026  
**Источник:** [SWRouter — arXiv](https://arxiv.org/abs/2609.11414)

Главная идея SWRouter: выбор модели в multi-turn диалоге нельзя рассматривать отдельно от того, **какую часть истории мы показываем router'у**. Авторы используют similarity-based segmentation истории и отдельно измеряют качество context construction и собственно model routing. Они сообщают +16.26% к evaluation accuracy относительно лучшей одиночной модели и +8.22% относительно их Conv-ID baseline.

Для DSH это почти готовый architectural fit. Сейчас `agent/request` может менять `provider/model` перед dispatch; `prepareCall()` после этого определяет реальный route и его capabilities, а выбранный provider/model сохраняется в `request/context`.

**Точка интеграции:** router-plugin вокруг `agent/request`. Он получает derived session history, строит короткое representation последних тематически связанных окон и выбирает `(provider, model, reasoningEffort)`.

Это лучше, чем встраивать routing внутрь `agent-loop`: механизм остаётся обычным Cordis middleware.

**Ожидаемая польза:** потенциально очень серьёзная экономия. Простые continuation/tool steps можно отправлять дешёвой модели, сложные planning/debugging steps — сильной, причём решение будет учитывать trajectory, а не только последний prompt.

Есть ещё интересный побочный эффект: DSH уже явно документирует влияние prompt/history изменений на prefix/KV caching. Поэтому router можно оптимизировать не только по `$ / quality`, но и по **стоимости разрыва cached prefix**.

**Риски:** неправильный model switch способен съесть выигрыш из-за потери provider-side KV/prefix cache. Кроме того, слабая модель может испортить trajectory, после чего дорогой модели придётся исправлять ошибку.

**Практическая ценность: 9/10. Сложность: 4/10.**

**Минимальный эксперимент:** взять 100 сохранённых многошаговых DSH sessions и replay'ить их тремя политиками:

`always strong`  
`last-message router`  
`similarity-window router`

Измерять success rate, input/output tokens, cost, latency, число repair/retry steps и число смен model route. Если SWRouter-подобная политика сохраняет ≥98% baseline success при ≥25–30% экономии — имеет смысл делать полноценный plugin.

---

## 🥉 3. ToolGrad — автоматически выращивать сложные tool-use тесты

**Дата публикации Google Research:** 10 сентября 2026  
**Источник:** [Google Research — ToolGrad](https://research.google/blog/toolgrad-efficient-tool-use-dataset-generation-with-textual-gradients/)

У ToolGrad интересная инверсия: вместо

`придумать вопрос → заставить агента искать правильную цепочку tools`

делается

`сначала построить гарантированно рабочую tool-chain → затем сгенерировать задачу, которая её требует`.

API Proposer выбирает потенциальное продолжение chain, параллельные executors реально проверяют вызовы, selector выбирает рабочий вариант, после чего LLM обновляет задачу и expected response.

Авторы сообщают **99.8% pass rate** генерации, а всего 500 синтетических примеров уже заметно улучшали tool calling при fine-tuning; 12B-модель достигла BFCL 83.1.

Но для DSH наиболее интересна не тренировка модели.

**Точка интеграции:** `ctx.tools` + существующий guarded tool pipeline. Из зарегистрированных tool schemas можно автоматически строить **verified multi-tool regression scenarios** для самого harness.

Например:

`search → fetch → patch → test → git`

или специально:

`parallel-safe tool A + B → exclusive tool C → failure → retry/fallback`.

Это очень хорошо проверяет `src/tool-calls.ts`, bounded parallelism, exclusive barriers и обработку результатов стандартным loop.

**Ожидаемая польза:** автоматически растущий набор сложных tool-use evals, основанный на реальных plugins DSH. Это потенциально ещё интереснее в связке с вашим Skill Evolution: успешные chains становятся training/evaluation material.

**Риски:** ToolGrad первоначально нацелен на dataset generation для обучения LLM, поэтому часть framework придётся переосмыслить. Нельзя позволять генератору выполнять destructive tools без disposable environment.

**Практическая ценность: 8.5/10. Сложность: 5/10.**

**Минимальный эксперимент:** взять только 8–12 безопасных DSH tools и автоматически построить 100 verified chains длиной 2–6 вызовов. Затем сгенерировать user tasks назад из chains и посмотреть, насколько разные модели воспроизводят исходный workflow. Интересный metric: не exact tool sequence, а successful final state + лишние tool calls.

---

## 4. REVA — использовать историю обращений для будущего сжатия контекста

**Дата:** 10 сентября 2026  
**Источник:** [REVA — arXiv](https://arxiv.org/abs/2609.11209)

REVA атакует важную проблему prompt compression: compressor сам может оказаться настолько дорогим, что съест выигрыш от сокращения context.

Вместо отдельного online compressor авторы накапливают attention traces исторических обращений к документу и строят reusable evidence view. При следующем использовании документа нужное представление уже почти готово. Авторы получили +1.0–5.8 quality points и сокращение compression overhead в **5.3–15.6×**, добавляя менее 40 ms latency.

**Применимость к DSH — частичная.** Это не замена session compaction вообще. Метод особенно хорош там, где одни и те же внешние документы/кодовые артефакты появляются во многих запросах.

**Точка интеграции:** plugin перед `agent/pre-step` либо источник model-facing injected context. Сам score-store должен жить вне основного session history; в историю отправляется только выбранный readable evidence view.

Особенно интересный вариант для coding agent: вместо `document-keyed evidence` использовать:

`file/blob hash → historically useful spans`.

То есть Harness постепенно учится, какие части `package.json`, README, giant source file или API docs реально используются моделью.

**Ожидаемая польза:** меньше повторно передаваемого retrieval/context текста и более дешёвые long-running agents.

**Риски:** нужен доступ к attention signal либо proxy importance metric. Для закрытых API это главный стоп-фактор. Поэтому буквально реализовать REVA для Claude/OpenAI/DeepSeek API часто невозможно.

**Практическая ценность: 7/10. Сложность: 7/10.**

**Минимальный эксперимент:** не начинать с attention. Использовать tool-use attribution как дешёвый proxy: если агент после чтения фрагмента файла реально ссылается на него при patch/test, повысить importance span. Сравнить такой reuse-cache с naive `head-N`, BM25 и обычным summarizer на 50 повторяющихся repo tasks.

---

## 5. NovaFabric — cryptographically replayable agent runs

**Дата:** 11 сентября 2026  
**Источник:** [NovaFabric — arXiv](https://arxiv.org/abs/2609.12582)

NovaFabric предлагает превращать agent run в переносимый **Run Capsule**: provenance graph, tamper-evident Merkle log, DSSE/in-toto signatures, timestamps, redaction attestation и режимы replay. Идея интересная именно потому, что обычная observability trace сама по себе редактируема.

У DSH уже есть сильная основа для этого: session log — source of truth, а agent lifecycle, tool calls/results и request context сохраняются как durable facts.

Поэтому я бы **не переносил NovaFabric целиком**, а украл архитектурную идею:

`DSH session → canonical export → content hashes → signed manifest → optional deterministic replay`.

**Точка интеграции:** новый `SessionPersistence` exporter или observer `session/event`; replay поверх существующего session derivation/invariant machinery.

**Ожидаемая польза:** воспроизводимые bug reports, trustworthy eval artifacts, forensic analysis и очень полезная база для будущей Skill Evolution: можно доказать, на какой именно trajectory была рассчитана optimization score.

Но здесь надо быть скептичным: собственные результаты NovaFabric пока не выглядят production-ready — только 2/10 tool-using workloads удалось полностью replay'ить из-за отсутствия substitution tool responses.

**Практическая ценность: 7.5/10. Сложность: 6/10.**

**Минимальный эксперимент:** реализовать **не crypto**, а deterministic `dsh session export --replay-bundle`: session events + request headers + tool inputs/results + model responses + SHA-256 manifest. Потом поднять mock LLM/tool providers и добиться byte-identical reconstruction `deriveMessages()` на 20 сохранённых sessions. Только после этого имеет смысл добавлять DSSE/Merkle.

---

## Отдельно: security-сигнал непосредственно про DeepSeek Harness

Это не новый algorithmic paper текущего окна, но поскольку это **первый обзор**, пропускать его было бы неправильно.

8 сентября OX Research раскрыла **CVE-2026-82533**, CVSS 9.4: sandboxed DSH agent мог обратиться к локальному control API, подделать доверенный `Host` header и переключить собственную session в `danger-full-access`. Причина особенно показательна: filesystem sandbox работал, но loopback network находился за его security boundary.

[OX Research — CVE-2026-82533 technical write-up](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/)

Ваш текущий `0.1.5-alpha.1` уже **новее исправленной линии 0.1.2**, так что речь не о необходимости срочно патчить этот конкретный CVE.

Но архитектурный урок я бы превратил в permanent regression suite: **никакой capability, способной повысить authority агента, не должна быть достижима из execution realm агента только потому, что endpoint считается “local”.**

Это хорошо сочетается с BenchShield: можно буквально описать privilege transitions как запрещённые lifecycle edges и проверять их в каждом security/eval run.

## Что из этого я бы реально делал

Мой приоритет на эту неделю такой:

**№1 — BenchShield-inspired eval integrity plugin.** Самое сильное совпадение с уже существующей event-sourced архитектурой DSH и одновременно полезно для будущего Skill Evolution.

**№2 — SWRouter PoC через `agent/request`.** Очень низкая цена эксперимента: архитектура уже позволяет dynamic routing, поэтому сначала можно доказать или опровергнуть экономический эффект вообще без изменения core.

**№3 — ToolGrad-inspired generator regression scenarios.** Это может превратить набор DSH tools/plugins в автоматически растущую систему evals вместо вручную написанных happy-path тестов.

Критичный момент: **REVA я пока не стал бы реализовывать**, несмотря на красивые цифры. Для API-моделей отсутствие attention traces ломает центральную идею метода. NovaFabric тоже пока лучше использовать как источник design patterns, а не зависимость или спецификацию.

Из пяти свежих направлений именно первые три имеют сочетание **высокой потенциальной отдачи + естественного Cordis seam + дешёвого falsifiable experiment**. Это хороший критерий, чтобы не превращать `deepseek-harness` в склад модных research-фич.
