# Decision Geometry — native provider tool-use A/B и безопасный tool_result roundtrip

**Дата:** 2026-11-07. Контрактная контрпроверка существующей карточки [Decision Geometry](../../studies/decision-geometry-harness.md), после [математического A/B](2026-11-07-bandit-countercheck.md) и [text-only DSH-wire A/B](2026-11-07-interface-order-ab.md). **Предыдущие этапы не воспроизводились заново без причины**: применялись уже доказанные SHA, pre-registered synthetic gold и исходный код.

**Полный научный первоисточник:** [arXiv:2610.37255v2](https://arxiv.org/html/2610.37255v2), HTML SHA-256 `5e37b2455cbe94cf1abbf932d28c96e5ee9f9bff18a547c76f1541387a58e4ce`, методология, результаты и ограничения разобраны в [ранее опубликованном полнотекстовом обзоре](2026-11-07-bandit-countercheck.md). Авторы наблюдали резкое снижение MiniWoB++ task success при изменении представления наблюдений, но **это не доказательство похожей регрессии в DSH**.

**Собственный source seam:** [`Artemedi/dsh-runtime@3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc`](https://github.com/Artemedi/dsh-runtime/tree/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc), [`packages/llm/llm-deepseek/src/serialize.ts:342–390`](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/llm/llm-deepseek/src/serialize.ts#L342-L390), exact source SHA-256 `36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162`. Оригинальный `serializeRequest()` из него ранее построил запросы и схемы 7 функций. Штатные **54/54 tests** сериализатора и **29/29 tests** `research-hub` пройдены в [предыдущей волне](2026-11-07-interface-order-ab.md), исходники не менялись.

## Что нового по сравнению с предыдущим text-only A/B

Прошлый [A/B](2026-11-07-interface-order-ab.md) давал модели JSON с `tools` как **цитируемый текст**: это был перенос имён и аргументов в JSON-предсказание, без tool-call интерфейса.

**В новом эксперименте модельный API действительно вернул Anthropic `tool_use`**, c `stop_reason: tool_use`, `id`, точным именем инструмента и объектом `input`. Для этого авторский DSH `tools[].function.{name,description,parameters}` был **механически преобразован** в Anthropic Messages `tools[].{name,description,input_schema}` через короткий отдельный conversion. Семантическая эквивалентность A и B проверена независимо. Вызовы шли через уже существующий ограниченный wrapper ZCode, model `glm-5.3-flash`. Временная конфигурация провайдера и секреты **не публиковались**.

**Главный предел:** это native tool-use **у ZCode/Anthropic**, **НЕ** прямой вызов через `dsh-runtime` DeepSeek/OpenAI-compatible adapter. Настоящие функции, файлы, БД, команды и permission-gated agent runtime **не выполнялись**. Название `native` относится к настоящему API-типу `tool_use`, а не к запуску production-like DSH. Различия protocol/decoder могут менять результат.

## Method / independent oracle / negative controls

1. Зафиксированы 20 разных синтетических read-only задач из уже [размеченного набора 24](../../data/results/decision-geometry-harness/2026-11-07-schema-ab-fixtures.json): минимум 2 на каждую из 7 функций, **3 `NONE`**, включая ранее неоднозначную `artifact-3`. Подбор и порядок определены фиксированным seed `20261107`, эталонные `expected_tool/expected_arguments` никогда не передавались модели.
2. Для **каждой задачи** выполнен A/B с чередованием `AB/BA`: **40 provider attempts**, один физический запрос одновременно, не более 45 секунд на запрос, fail-closed на ошибках; неуспешный запрос не перезапускается ради красивой статистики. В A исходные tool descriptions и property order, в B оба порядка обращены. Свойства схем, имена, значения и система инструкций эквивалентны. Эффект порядка функций и порядка свойств **нельзя разделить** при таком composite intervention.
3. [Runner](../../experiments/decision-geometry-harness/2026-11-07-native-tool-ab.py) сохраняет только структурированный provider tool-call, имя/аргументы, stop reason, SHA stdout и запроса, usage, wall-clock, локальные CPU/FS blocks и checkpoint, без model private thinking. [Машинный результат](../../data/results/decision-geometry-harness/2026-11-07-native-tool-ab.json).
4. [Отдельный независимый Python oracle](../../experiments/decision-geometry-harness/2026-11-07-native-tool-oracle.py) повторно сверяет исходный DSH Git SHA + source SHA, канонически сравнивает две преобразованные схемы (независимо от runner), проверяет required/unknown-arg types/enum, точный tool и arguments по preauthored gold, вычисляет только **завершённые парные** сравнения. Мутация description ломает schema-equivalence; удаление обязательного аргумента у правильного `tool_use` ломает argument validator. [Машинные результаты](../../data/results/decision-geometry-harness/2026-11-07-native-tool-oracle.json).
5. Абстрактный `NONE` без model tool call — ожидаемая категория, а не вызов функции. Структурно неправильный `tool_use` отмечается `INVALID_RESPONSE`, **не** становится `NONE`, loss или корректным ответом.

| Измерение | A: исходный порядок | B: обратный порядок |
| --- | ---: | ---: |
| Provider attempts | **20/20** | **20/20** |
| Structurally complete | **20/20** | **19/20** |
| Настоящие `tool_use` среди COMPLETE | **17** | **16** |
| Строго точные tool name + args + schema | **19/20** | **19/19** |
| Ложные `tool_use` на трёх `NONE` | **0/3** | **0/3** |
| Median wall-clock | **6.62 s** | **6.08 s** |
| p95 wall-clock | **8.03 s** | **8.02 s** |
| Provider reported input tokens (без cache-read) | **2 508** | **2 357** |
| Provider reported cache-read input tokens | **35 136** | **33 408** |
| Provider reported output tokens | **1 424** | **1 168** |

**Парный oracle (только COMPLETE для A и B):** **19 задач**, `both_exact=18`, `only_A=0`, `only_B=1`, `both_wrong=0`, `tool_changed=1`, `argument_changes=0`. На `none-2` A вернула обычный текст вместо строго предписанного `NONE`, B вернула `NONE`. Это **format-adherence ошибка**, но **не** нежелательное выполнение инструмента. Для `artifact-3` B дала ошибку `NON_SINGLE_TOOL_USE` (ответ с недопустимым числом/формой вызовов); A корректно вызвала функцию. Она исключена из парного сравнения как incomplete invalid provider output, но **включена в attempted denominator**. Повторять или заменять выход без новой предрегистрации нельзя.

**Нельзя заключать:** B лучше A, потому что `19/19 > 19/20`. Для 19 сравнимых задач B имела ровно **один** случай лучше, а у B также есть отдельный malformed structured output. Даже расхождение в задержке при одном вызове на пару и неопределённой provider sampling конфигурации не показывает causal performance gain; output token/caching variance тоже велико. Эталонные задания были authored, не blind human gold.

## Два дополнительных end-to-end protocol smoke-test без реального выполнения инструмента

Сделан ограниченный **`tool_use → tool_result → final answer`** протокол в [самостоятельном драйвере](../../experiments/decision-geometry-harness/2026-11-07-native-tool-continuation.py). Система вызвала ZCode native tool API, получила по одному структурированному вызову, **не исполнила их** и передала заранее подготовленные синтетические результаты:
- `sum_numbers(numbers=[4,9,-2])` → `{"sum":11}`;
- `get_job_status(job_id=job-104)` → `{"job_id":"job-104","state":"complete"}`.

[Машинные receipts](../../data/results/decision-geometry-harness/2026-11-07-native-tool-continuation.json) / [независимый verifier](../../experiments/decision-geometry-harness/2026-11-07-native-tool-continuation-oracle.py) / [его JSON](../../data/results/decision-geometry-harness/2026-11-07-native-tool-continuation-oracle.json): **2/2** корректных tool names/args + provider `tool_use`/final `end_turn`; **2/2** финальных ответов содержат правильное значение; **1/2** строго совпадает с заранее указанной формой `{"result":scalar}`. Для `job` провайдер вернул вложенный объект с верным `state`, а не scalar `complete`. Вердикт не округляется до `2/2 exact`. Дополнительная контрольная мутация числа в аргументе отвергается.

**Пользовательские скрипты инструментов не исполнялись ни разу**; smoke-test проверяет provider conversation protocol и serialization, не permission isolation, file IO, production safety или истинность tool output.

## Применимость ко всем project-registry профилям

**Актуальный проверенный registry pin:** [`Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`](https://github.com/Artemedi/project-registry/tree/fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6), 45 карточек; shortlist из существующего [project-fit](../../portfolio/2026-10-27--2026-11-02/project-fit.md) и предыдущих 2026-11-07 reviews. Backlinks к Decision Geometry уже присутствуют; новых доказательных FIT, требующих изменения реестра, нет.

| Исследование | Проект | Сопоставление и исходник | Следующий независимый gate | Статус |
| --- | --- | --- | --- | --- |
| Decision Geometry | `dsh-runtime` | **Source verified** [`packages/llm/llm-deepseek/src/serialize.ts:348–355@3feed5d`](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/llm/llm-deepseek/src/serialize.ts#L348-L355). Source tool descriptions реально переходят в provider wire. В этом тесте тот же контракт преобразован в API другой модели, не заменяя DSH adapter. | Изолированный **настоящий DSH native DeepSeek/OpenAI tools endpoint** с mock execution и фиксированными 50+ unique tasks / ≥3 replicas, controller-owned tool_result, 0 cross-scope side effects, p50/p95/CPU/GPU/RAM/IO/token cost, non-trivial negative controls. Проверить per-tool order vs property order раздельно. | `VERIFIED_SERIALIZER_SEAM / PROVIDER_NATIVE_ZCODE_AB_ONLY / DSH_NATIVE_PENDING` |
| Decision Geometry | `agent-config` | [`claude_templates/harness.CLAUDE.md@489e074`](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/claude_templates/harness.CLAUDE.md), prompt-surface source, но не связана с 7 synthetic tools текущего A/B. | Сначала отдельные permission-negative-tests на prompt section order с фиксированным schema и on-host isolated approval, без запуска hooks в user profile. | `DOCUMENTED_PROMPT_SURFACE / NOT_MEASURED_HERE` |
| Decision Geometry | `HermesAgent` | Регистровый profile показывает агентный loop; model-facing serializer в актуальной кодовой копии этим тестом не исследован. | Выделить current `repo@SHA:path`, после чего отдельно построить строгую регрессию формата `tool_use` и refusal. | `PROFILE_MATCH / NEEDS_SOURCE_PIN` |

Остальные проекты, включая индексные, научные, DBA и коллегин `.NET` проект без новой исходной реализации, не получили новых прямых implementation seam и project-fit approvals. Процент на synthetic tool routing **не переносится** на медицинские, SQL production или другие живые workflows.

## Trade-offs / final disposition

Структурированный native call уменьшает риск неправильного *текстового извлечения* выбора инструмента; одновременно добавляет provider-specific schemas, особую stop-логику, обязательность id и `tool_result`, новые состояния `INVALID_RESPONSE`, дополнительные токены и цену RTT. Порядок полей в JSON может менять output даже при одинаковой семантике. На этом небольшом A/B нет доказанной причинной выгоды, а один malformed `tool_use` и один неправильный финальный формат являются реальными обнаруженными ограничениями.

**`ACCEPT_BOUNDED_ZCODE_NATIVE_TOOL_USE_AB`**, **`ACCEPT_BOUNDED_SYNTHETIC_TOOL_RESULT_ROUNDTRIP_WITH_FORMAT_FAILURE`**, **`DEFER_TRUE_DSH_PROVIDER_NATIVE_AB`**, **`NO_NEW_PROJECT_FIT`**, **`NO_PRODUCTION_APPROVAL`**. Не рефакторить/пересортировывать production `dsh-runtime` schemas на основании двух успешных лабораторных сравнений; публикация отчёта и machine evidence **не означает** разрешение менять код проекта.
