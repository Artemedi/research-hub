# Decision Geometry — реальный DSH serializer и два контролируемых A/B представления

**Дата:** 2026-11-07. Узкий практический follow-up к [полному source-level анализу и математической контрпроверке](2026-11-07-bandit-countercheck.md). Полный HTML [arXiv:2610.37255v2](https://arxiv.org/html/2610.37255v2), проверенный на прошлом этапе SHA-256 `5e37b2455cbe94cf1abbf932d28c96e5ee9f9bff18a547c76f1541387a58e4ce`, уже содержит методы, результаты и ограничения. В этом этапе не воспроизводились MiniWoB++/Terminal-Bench, а проверялась доступная **модельная чувствительность к сериализации реального DSH wire**.

**Реальная граница проекта:** [`Artemedi/dsh-runtime@3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc`](https://github.com/Artemedi/dsh-runtime/tree/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc), [`packages/llm/llm-deepseek/src/serialize.ts:342–390`](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/llm/llm-deepseek/src/serialize.ts#L342-L390), file SHA-256 `36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162`. Запускался **оригинальный экспорт `serializeRequest`** через локальную версию `tsx`; код исходного проекта не менялся, модельно-исполняемые функции отсутствовали. Два A/B намеренно разделены, чтобы не смешивать перестановку инструментария и контекст.

## Принципиальное ограничение уровня эксперимента

**Это не native `dsh-runtime` model/tool run.** Экспорт `serializeRequest()` построил настоящие provider-wire JSON объекты, но модель `glm-5.3-flash` вызывалась через **отдельный ZCode text-only provider**: wire JSON передавался ей как *инертный текст*. Реальные `tools` и `tool_call` интерфейсы провайдера не включались, никакие пользовательские/производственные операции не выполнялись. Поэтому удалось измерить **выбор функции и формирование аргументов по описаниям**, а не корректность вызова в настоящем DSH agent loop, не безопасность реальных tool permissions и не end-to-end task success.

`temperature:0` и `max_tokens:2500` относятся **к цитируемому DSH wire** и не становятся гарантированными параметрами реального ZCode вызова. Зафиксированы фактические `model`, `stop_reason`, токены и время из ответов провайдера. Контроль физической конкуренции: **один ZCode вызов одновременно**, без модели-критика, model consensus и доступа к инструментам.

## A/B №1 — порядок определений tool schema и полей аргументов

**Метод:** [24 предварительно созданных synthetic tasks с независимым gold](../../experiments/decision-geometry-harness/2026-11-07-schema-ab-fixtures.py), [JSON golden fixture](../../data/results/decision-geometry-harness/2026-11-07-schema-ab-fixtures.json). 7 классов read-only функций, 21 позитивный запрос + 3 явных `NONE`, английский и русский. **Входы фиксированы до первого model call.** `A`: исходный порядок 7 функций и `properties`. `B`: обратный порядок 7 функций **и** ключей `properties`; названия, descriptions, constraints, `required`, значения, контекст и сами задачи неизменны. Это **составное вмешательство**: по результату нельзя определить, повлиял ли порядок функций или полей.

[Генератор настоящего DSH wire](../../experiments/decision-geometry-harness/2026-11-07-schema-ab-wire.mts) / [все шесть сериализованных wire requests](../../data/results/decision-geometry-harness/2026-11-07-schema-ab-wires.json). В каждой A/B паре запросы имеют одинаковый byte length, и независимый Python-verifier подтверждает глубинную эквивалентность значений, tool definitions, обязательности полей и `messages`; меняется только порядок JSON-представления.

**Протокол:** 3 batches × 8 задач × 2 variants × 2 replicates = **96 решений на 12 вызовов**. Порядок версий чередуется `AB/BA` между batch и replicate. Ответы парсятся без repair и без повторов неуспешного model call. [Исполняемый ограниченный ZCode-раннер](../../experiments/decision-geometry-harness/2026-11-07-schema-ab-run.py), [все 12 моделируемых receipts, хеши prompt и usage](../../data/results/decision-geometry-harness/2026-11-07-schema-ab-model.json). В raw provider не передавались значения gold `expected_tool` / `expected_arguments`.

| Наблюдение | A — исходная форма | B — перестановка |
| --- | ---: | ---: |
| Завершено provider calls | **6/6** | **6/6** |
| Совпадение tool name, аргументов и schema constraints | **48/48** | **48/48** |
| Ложный вызов на явном `NONE` | **0/6** | **0/6** |
| Медиана wall-clock на один batch-call | **15.7 с** | **21.1 с** |
| Reported input tokens (без cache-read) | **4 364** | **5 772** |
| Reported output tokens (включая внутренний вывод провайдера) | **5 038** | **6 932** |
| Reported cache-read input tokens | **7 808** | **6 400** |

**Парный независимый oracle:** [Python verifier](../../experiments/decision-geometry-harness/2026-11-07-schema-ab-oracle.py) / [машинный протокол](../../data/results/decision-geometry-harness/2026-11-07-schema-ab-oracle.json): **48 пар**, оба варианта верны в **48/48**, выбор функции изменился **0/48**, аргументы изменились **0/48**, `A-only/B-only` выигрышей **0/0**. Отдельная мутация tool description ломает semantic-equality oracle; подмена правильного названия функции ломает gold oracle.

**Интерпретация:** это *проверенное отсутствие наблюдаемого расхождения* на узком, намеренно простом наборе. При 100% baseline нет пространства для измеримого улучшения, и **нельзя** обобщать `0/48` на реальные prompt schema refactors, сложные многошаговые задачи, другие модели или большие языковые контексты. Отличие wall-clock, token/caching mix и задержка провайдера на **шести вызовах на вариант** не доказывают влияние порядка на скорость/стоимость. Это не воспроизведение опубликованных авторами 85%→19,2%; их обучение/политика и наши задания несопоставимы.

## A/B №2 — порядок полей observation, устаревший предыдущий шаг

**Новый независимый от первого A/B набор:** [16 предварительно созданных записей](../../experiments/decision-geometry-harness/2026-11-07-observation-fixtures.py) из двух задач на каждую из семи tool categories плюс двух `NONE`. [Golden fixture](../../data/results/decision-geometry-harness/2026-11-07-observation-fixtures.json) закреплён SHA и ссылается на исходную разметку из первого A/B. Каждая запись состоит из `current_request` (единственный авторитетный запрос), `previous_observation` (историческая, **намеренно отвлекающая** подсказка на *другую* функцию) и `context_metadata`. В prompt явно задано: предыдущая запись не является новым поручением. Это имитация конфликтующих сигналов, **не** восстановленная естественная DSH-сессия.

**Вмешательство:** `A` сохраняет исходный порядок JSON-полей состояния, `B` обращает порядок **только полей наблюдения**, включая ключи вложенных объектов. Все значения, messages semantics, список функций, ограничения tool schema и явная приоритетность `current_request` остаются одинаковыми. [Исходный генератор настоящего DSH wire](../../experiments/decision-geometry-harness/2026-11-07-observation-wire.mts) / [четыре wire-объекта с SHA](../../data/results/decision-geometry-harness/2026-11-07-observation-wires.json). Независимая программа проверила deep-sorted equality наблюдений, идентичность `tools`, prompt и SHA, а не только одинаковую длину входа.

**План до запуска:** 2 batches × 8 scenarios × 2 variants × 2 replicas = **64 модельных решения на восьми calls**; порядок `AB/BA` чередовался. **Фактически:** `7/8 COMPLETE`, `1/8 BLOCKED_PROVIDER` — последний `B, batch=1, replicate=1` превысил **52 секунды** и не вернул завершённого результата. Запрос не запускали заново и не заменяли данными A. [Receipt всех восьми попыток](../../data/results/decision-geometry-harness/2026-11-07-observation-model.json), включая ошибка/timeout, usage, SHA, elapsed и локальный CPU/FS IO; никаких инструментов, кроме неисполняемого выбора по тексту, модель не получила.

| Наблюдение | A — исходный порядок полей | B — обратный порядок полей |
| --- | ---: | ---: |
| Completed model calls | **4/4** | **3/4**, один `TIMEOUT` |
| Задач с валидным полным ответом / scored | **30/32** | **23/24** |
| Использован *устаревший* previous-tool как новое поручение | **0/32** | **0/24** |
| Ложный вызов инструмента на явном `NONE` | **0/4** | **0/4** |
| Ошибки именно имени функции | **0/32** | **1/24** |
| Ошибки схемы обязательных аргументов | **2/32** | **0/24** (один валидный `NONE` вместо нужной функции) |

**Строгая парная оценка:** [Python-verifier, независимый от model-runner](../../experiments/decision-geometry-harness/2026-11-07-observation-oracle.py) / [JSON-отчёт](../../data/results/decision-geometry-harness/2026-11-07-observation-oracle.json). Для трёх **полностью завершённых пар вызовов** получены **24 сопоставимых ответа**: `both_correct=23`, `both_wrong=1`, `A_only_correct=0`, `B_only_correct=0`, `tool_changes=1`, `argument_changes=1`. Единственный несовпадающий выбор — `obs-artifact-3`: A выбрала `list_experiment_artifacts`, но **опустила обязательный `kind`**, B выбрала `NONE` (аргументы пустые). Для того же входа повтор A вновь опустил `kind`, но соответствующая B-пара **НЕ подтверждена** из-за provider timeout.

**Существенная оговорка к gold:** фраза *«List experiment artifacts associated with study=kv-order»* имеет возможную лексическую неоднозначность: `experiment artifacts` может интерпретироваться и как тип `kind=experiment`, и как общее описание артефактов проекта. В исходном authored gold установлено `kind=experiment`, а schema требует `kind` независимо от такой интерпретации. Отсутствие `kind` — воспроизведённая формальная ошибка аргументов, но **не основание выводить массовую semantic regression**. Не меняли исходную разметку после наблюдения ошибки — это исказило бы A/B. Требуется более жёсткая preregistration и независимая человеческая разметка следующего корпуса.

**Важнейшая статистическая граница:** `30/32` и `23/24` **нельзя напрямую сравнивать как проценты успеха**, потому что у B отсутствует целый batch. На одинаковых 24 парах **точная доля успеха совпадает: 23/24 против 23/24**. Изменение структуры одного ответа демонстрирует чувствительность выбранного примера, **но не устойчивое превосходство B или ухудшение от перестановки**. Провайдерский timeout — отдельная категория, не переносить его в category `model incorrect`.

## Независимая контрпроверка и повторяемость

- **Контрактный oracle:** оба wire-генератора вызывают настоящий неизменённый DSH `serializeRequest()`; код источника/commit SHA, инструментальные объекты и семантическая эквивалентность JSON проверяются **отдельным Python-процессом**, до оценки ответов. Кроме наших тестов, исходный upstream `vitest run packages/llm/llm-deepseek/tests/serialize.spec.ts` на той же pinned рабочей копии выполнил **54/54 PASS** (1 test file), без правок исходников.
- **Ответный oracle:** заранее определённые synthetic labels, точное имя функции, аргументы, обязательные JSON types, `NONE` и отсутствие обращения к историческому tool. Эталон **не** включается в prompts, и модель не оценивает собственные результаты. Следующие отдельные проверки ловят подмену поля tool description, подмену одного правильного ответа и подмену current_request в observation.
- **Модельная независимость:** два повторения одного `glm-5.3-flash` — **не** экспертиза разных моделей и не blind human panel. Отдельный вызов ZCode совета ради согласованного голоса в этом A/B **не добавил бы независимого oracle**; поэтому не используется для повышения статуса.
- **Сбойные ответы:** все 20 вызовов по двум A/B (19 COMPLETE / 1 TIMEOUT) проходят bounded policy; сценарий последнего таймаута не воспроизводился новым платным запросом. Сохранённые checkpoint receipts позволяют восстановить отчёт без нового model call.
- **Расходы и производительность:** фактические wall-clock, reported provider input/output/cache-read tokens и `resource.getrusage(RUSAGE_CHILDREN)` CPU/FS blocks сохранены отдельно для всех вызовов. Локальные показатели **не** включают серверные GPU/RAM/IO провайдера. `p50/p95` 3–6 вызовов на вариант не являются performance benchmark, денежной выгоды/убытка без тарифов также **нет**. У ZCode temperature/seeds не установлены из цитируемого wire.

Сценарии не содержат чувствительных данных, SQL production, ключей или частных карточек; оригинальные исходники `dsh-runtime`, научный checkout, `agent-config` и `project-registry` не правились. Никакие настоящие API инструменты агента не выполнялись.

## Применимость к проектам и следующий тест

**Пин реестра:** `Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`, 45 profiles, с ранее установленными [research-to-project links](../../portfolio/2026-10-27--2026-11-02/project-fit.md). У всех трёх shortlisted projects уже существуют обратные ссылки на Decision Geometry, в registry нет нового статуса или дублирования.

| Исследование | Целевой project ID | Source seam / основание | Ограничения и минимальный следующий тест | Доказательная диспозиция |
| --- | --- | --- | --- | --- |
| Decision Geometry | `dsh-runtime` | **VERIFIED** [реальный tool serialization @3feed5d:348–355](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/llm/llm-deepseek/src/serialize.ts#L348-L355). Параметры `tools[].function.parameters` передаются в wire без канонической сортировки. Место для **регрессионного теста**, а не требование постоянной сортировки. | Изолированный **native-model tool-call A/B** с одним настоящим фиксированным model/provider, фактическими function-call outputs, no-op tool executor, строгими permission guards и golden schema semantics. 50+ независимых задач, хотя бы 3 прогона, слепая оценка; учитывать output validity, hallucinated calls, p50/p95, token cost, caching, CPU/RAM/IO. | `VERIFIED_SOURCE_SEAM / SURROGATE_MEASURED / NATIVE_AB_BLOCKED` |
| Decision Geometry | `agent-config` | [@489e074: `claude_templates/harness.CLAUDE.md:6–13`](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/claude_templates/harness.CLAUDE.md#L6-L13) — реальная поверхность model instructions и permissions, но ни один existing hook не менялся. | Отдельный held-out negative-case A/B по порядку *инструкций*, проверяя запреты команд/файлов. Текущие JSON tool prompts напрямую к этому файлу не привязаны. | `VERIFIED_PROMPT_SURFACE / NOT_MEASURED_IN_THIS_AB` |
| Decision Geometry | `HermesAgent` | Registry указывает agent orchestration; конкретный model-facing encoder@SHA в текущем этапе **не проверен**. | Предъявить исходник и зафиксировать путь наблюдения к модели, затем применить тот же oracle; нельзя смешивать API-контекст и локальную сериализацию. | `PROFILE_MATCH / NEEDS_CURRENT_SOURCE_SEAM` |

Остальные профили (включая DBA, документацию, cache indexes, игровые задачи и проект коллеги .NET без отдельной source-level трассы) не получили нового доказательного `FIT`; никакой абстрактный «всем агентам полезно» не оправдывает внедрение. Existing historical assessments и backlinks не повышались на основании согласия моделей.

**Итоговая диспозиция:** `ACCEPT_BOUNDED_DSH_WIRE_EQUIVALENCE`; `ACCEPT_BOUNDED_MODEL_SCHEMA_ORDER_AB`; `PARTIAL_OBSERVATION_ORDER_AB / BLOCKED_PROVIDER_1_CALL`; `REWORK_NATIVE_MODEL_TOOL_EXECUTION_AB`; `NO_NEW_FIT`; `NO_PRODUCTION_APPROVAL`. Сейчас нет экспериментального основания менять порядок property/инструментов в production, добавлять общий schema canonicalizer или переписывать agent prompt orchestration. Нужен целевой production-like test только после независимой корректной baseline метрики; иначе **YAGNI**.
