# 0-CODE — конфигурационный JSONC: оригинальный парсер, независимый oracle и дубликаты ключей

**Дата проверки:** 2026-11-07. Это новое узкое дополнение к [предыдущему полному обзору исходников 0-CODE](2026-11-04.md), а не повтор его уже пройденных проверок команд, stop-hooks и supervisor. Первоначальные 49 upstream unit tests и границы safety-фильтра из предыдущего обзора не пересоздавались; это **новый source-level эксперимент** над конфигурационным контрактом.

**Первичный инженерный источник:** [0-SOFT/0-CODE@47f6a81724e87ff5e916f0eb146516d801a8fb28](https://github.com/0-SOFT/0-CODE/tree/47f6a81724e87ff5e916f0eb146516d801a8fb28), v2.1.1 (19.10.2026), MIT. Checkout сделан во временном каталоге и не изменён. Непосредственно открыты оригинальные реализации [`lib/jsonc.mjs:1–36`](https://github.com/0-SOFT/0-CODE/blob/47f6a81724e87ff5e916f0eb146516d801a8fb28/lib/jsonc.mjs#L1-L36) (SHA-256 `f61414badb9ec40589ebb26655a4b109466c86e20a6e5d8b96add15bf7deb954`), [`lib/native-json.mjs:9–42`](https://github.com/0-SOFT/0-CODE/blob/47f6a81724e87ff5e916f0eb146516d801a8fb28/lib/native-json.mjs#L9-L42) (SHA-256 `c22d121df69f0f4839827b933810c0b05cf6ce86e83cc1ce1c6980ac608e4d42`), два родных test files и вызывающий [`core/project-inventory.mjs:20–27`](https://github.com/0-SOFT/0-CODE/blob/47f6a81724e87ff5e916f0eb146516d801a8fb28/core/project-inventory.mjs#L20-L27).

## Контракт и границы до эксперимента

`parseJsonc` — простой двухпроходный parser: удаляет `//` и `/*…*/` вне двойных кавычек, не меняя содержимое quoted strings, затем убирает завершающие запятые вне строк и передаёт результат в обычный `JSON.parse`. Все операции — над строковым input, никакой code evaluation нет. Однако **этот слой не определяет политик безопасности, уникальности ключей и прав записи**; поведение потребителя проверяется отдельно.

`native-json.mjs` не использует результат без проверки: его `inspect` разбирает структуру, содержит отдельный `Set` имён на уровне объекта, а повторение имени отклоняет как неоднозначный вход; следовательно, свойство обычного `parseJsonc` нельзя автоматически распространять на native JSON edit path. Напротив, `project-inventory.mjs:24` использует именно `parseJsonc` при чтении `.jsonc`, без проверки уникальности ключей в этой узкой ветке; какой downstream эффект это имеет в реальном проекте, **не измерялось**.

## Реальный source-path тест + независимая разметка

**Fixtures:** [Python-генератор](../../experiments/zero-code/2026-11-07-jsonc-fixtures.py) из `20` известных объектов × `6` синтаксических представлений: `plain`, `block`, `line-lf`, `line-crlf`, `trailing`, `mixed`. Авторский parser не участвует в создании золотого ответа: он задан стандартным `Python json.dumps` для исходных значений. Внутри строк присутствуют URL/`//`, `/* */`, экранированные кавычки, слеши, обратные слеши, кириллица, emoji, запятые и скобки. Комментарии добавляются **между** токенами, а завершающие запятые — только в непустых контейнерах. Синтетический corpus с фиксированным seed `20261107`, без личных данных.

**Исполнение оригинала:** [Node.js runner](../../experiments/zero-code/2026-11-07-jsonc-runner.mjs) импортирует настоящие `parseJsonc` и `readNativeJson` из pinned checkout после проверки commit+SHA файлов. Он выполняет `120` valid и `24` специально некорректных JSONC-потока. Дополнительные unit tests upstream: `tests/unit/jsonc.test.mjs` (**2/2 PASS**) и `tests/unit/native-json.test.mjs` (**3/3 PASS**). Ни supervisor, ни hooks, ни команды изменения среды не запускались.

| Оракул | Фактический результат | Ограничение |
| --- | ---: | --- |
| Объекты из 20 base × 6 JSONC variants совпали с gold | **120/120 PASS** | Случаи коррелированы между собой, это не 120 независимых реальных конфигураций |
| Заранее перечисленные невалидные синтетические входы отклонены | **24/24 PASS** | Это не полная формальная спецификация JSONC |
| Дополнительные авторские unit tests parser + native edit | **5/5 PASS** | Узкие unit-тесты, не e2e безопасности |
| Обычный `parseJsonc` на `{"model":"safe","model":"override"}` | **ACCEPT**, значение `override` | Совпадает с last-key-wins семантикой JS `JSON.parse`; не объявлять всемирной уязвимостью |
| Более строгий `readNativeJson` на том же input | **REJECT**, без дубля **ACCEPT** | Защита подтверждена именно у этого source-path |
| Отдельный Python-verifier по исходному gold | **120/120 + 24/24 PASS** | Проверяет парсерные outputs, не работу всего автономного цикла |
| Две намеренные мутации машинных результатов | **2/2 REJECT** | Испытание чувствительности verifier, не реальная атака |

[Полный машинный результат](../../data/results/zero-code/2026-11-07-jsonc.json) включает исходные SHA-256 каждой синтетической конфигурации, фактически возвращённые объекты/ошибки, авторский pin и source SHA. [Независимый Python-verifier](../../experiments/zero-code/2026-11-07-jsonc-oracle.py) не импортирует JS-парсер и заново сравнивает *фактические* значения с исходными Python-gold, не доверяя флагу `matched` в отчёте; [его машинный протокол](../../data/results/zero-code/2026-11-07-jsonc-oracle.json) содержит mutation controls и hash JSON основного результата. Сторонние LLM для числового verdict не нужны.

**Отдельный источник неопределённости:** не проверено, какое именно действие `project-inventory` выполнит после получения JSONC с повторным ключом; на данном этапе установлен только source code path. Отдельных live ZCode критиков в этом пакете не запускали после двух последовательных блокировок провайдера в предыдущем Decision Geometry контрчеке. Независимая валидация здесь машинная (Python–Node, distinct implementations), **не** согласование роя моделей.

## Применимость к существующим проектам

**Актуальный catalog snapshot:** `Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`, 45 project cards. Как и в предшествующем обзоре, рассматривались профильные кандидаты; предварительные ссылки на 0-CODE для них **уже есть** в registry и не дублировались. Это проверка parser-contract, не повторный global research-to-project approve.

| Исследование | Project ID | Source-подтверждение и смысл | Риск и следующий тест | Доказательный статус |
| --- | --- | --- | --- | --- |
| 0-CODE / JSONC | `agent-config` | [@489e074](https://github.com/Artemedi/agent-config/tree/489e074ab0daaadb732673c193047172a3744862) / [`hooks/harness.hooks.json:1–24`](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/hooks/harness.hooks.json#L1-L24) — проверяемый JSON-конфигурационный контракт, запреты записи credential/audit paths. **Не** установлено использование 0-CODE JSONC в нём. | Отдельные fixture tests текущего локального loader на duplicate keys, malformed JSON, комментарии и replay, без записи рабочих hooks. Принимающий parser/format может отличаться — сначала контракт. | `VERIFIED_CONFIG_SURFACE / NO_DIRECT_PARSER_FIT` |
| 0-CODE / JSONC | `dsh-runtime` | [@3feed5d](https://github.com/Artemedi/dsh-runtime/tree/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc); оригинальный [`packages/core/tools/src/schema.ts:11–21`](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/core/tools/src/schema.ts#L11-L21) — JSON tool-value annotations. Это **не** эквивалент чтения JSONC и не место прямой интеграции. | Если требуется external JSONC config, только отдельный upstream consumer proof+test; переносить чужой parser ради существующих schema nodes сейчас YAGNI. | `VERIFIED_SCHEMA_SURFACE / NO_DIRECT_PARSER_FIT` |
| 0-CODE / JSONC | `wiki-tasks` | Профиль документирует JSONL state + recovery; данный JSONC-парсер не является parser-заменой append-only журнала. Актуальный исходный checkout не инспектировался этим тестом. | Нужна отдельная предметная crash/recovery проверка, не переносить выводы из строкового parser в durability semantics. | `PROFILE_ONLY / NO_CURRENT_JSONC_FIT` |

Оставшиеся профильные направления не имеют доказанного source-contract, который улучшался бы от добавления `parseJsonc`; для проекта коллеги .NET нет current source seam. Никаких новых project-fit approvals и обратных ссылок по результатам этого узкого A/B.

## Вердикт и trade-offs

**`ACCEPT_BOUNDED_JSONC_PARSER_CONFORMANCE`** для исходного `0-CODE@47f6a8/lib/jsonc.mjs` на 120 валидных / 24 невалидных синтетических случаях с отдельным Python-gold. **`VERIFIED_NATIVE_DUPLICATE_REJECTION`** только на выбранном `readNativeJson` пути. **`REWORK_CALLER_SIDE_CONFIG_DUPLICATES`** — требуется установить, есть ли значимый эффект последнего значения в каком-либо разрешённом consumer. **`NO_DIRECT_PROJECT_ADOPTION` / `NO_PRODUCTION_APPROVAL`**.

Инженерные компромиссы: сохранение комментариев и trailing comma повышает удобство конфигов, но permissive key behavior усложняет анализ неоднозначных файлов; stricter inspector добавляет отдельную грамматическую проверку и код сопровождения. Измерения полного CPU/RAM/IO, масштабирования на мегабайтах, CI variability или эксплуатируемости **не проводились**; это не заявлено в выводах. Внедрять скопированный parser или полную агентную систему **не рекомендуется** без конкретного потребителя и независимого regression test.

Дальше по портфелю приоритетнее независимые experiments по semantic tool schema из Decision Geometry или по fault recovery из LIMBO; этот узкий JSONC gap закрыт как ограниченный source-contract test.
