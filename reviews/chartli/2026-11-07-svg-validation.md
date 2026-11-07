# Chartli — проверка исходного SVG-renderer и независимого XML/geometry oracle

**Дата:** 07.11.2026. Продолжение [полного source-based инженерного обзора от 04.11](2026-11-04.md), в котором уже были выявлены случаи потери первого значения scientific notation, подстановки нуля и распространения NaN при нормализации. Эти случаи **не воспроизводились повторно ради повышения статуса**; новая отдельная цель из [массовой очереди](../../portfolio/2026-11-07/mass-swarm-review.md) — проверить фактическую корректность SVG-выхода, а не только substring assertions оригинальных unit-тестов.

**Источник:** [ahmadawais/chartli v1.0.0 @ 3b39b97aeb564646437b2b7501b60541994d7575](https://github.com/ahmadawais/chartli/tree/3b39b97aeb564646437b2b7501b60541994d7575). Инженерный оригинальный код (не научная рецензируемая статья). Реальные исходники [`src/utils/svg.ts`](https://github.com/ahmadawais/chartli/blob/3b39b97aeb564646437b2b7501b60541994d7575/src/utils/svg.ts) SHA-256 `81b05c1000e389b80e11a87f09e74e889a899462e14cd322e9f259acb431db7e` и [`src/utils/normalize.ts`](https://github.com/ahmadawais/chartli/blob/3b39b97aeb564646437b2b7501b60541994d7575/src/utils/normalize.ts) SHA-256 `98adfcf1ebb0aa7793c194b1eb5e8e484004c52288fad0a692bee6c21503a438`. Исходник проверен по Git commit SHA и хешам до запуска. В исходном `tests/svg.test.ts` используются проверки строк на `<svg`, `</svg>`, `<circle>`, `<polyline>`, а не внешний XML-парсер; эти проверки полезны, но сами по себе не доказывают well-formedness и валидность числовых координат.

## Механизм и ограничения оригинала

Оригинальный `renderSvg()` получает `NormalizeResult` и параметры режимов circles/lines, выводит XML с корневым SVG и координатами из масштабированных чисел. Содержимое `xLabels`, `xAxisLabel`, `yAxisLabel`, `seriesLabels` экранирует `escapeXml` для `& < > ' "`. Этот helper **не удаляет запрещённые XML 1.0 управляющие символы**. Числа в координатах сериализуются как строки без явной проверки `Number.isFinite`. Это прямые возможности code path, а не данные о частоте пользовательских ошибок.

Ключевой trade-off: корректный синтаксис XML **не равен** корректной графической семантике. XML-парсер может принять атрибут `cy='NaN'`, но конечным числовым значением координаты он не становится. Даже обычные конечные точки не доказывают соблюдение scale/axis semantics для реальных единиц измерения — проблемы ранее описаны отдельно.

## Эксперимент и независимые оракулы

[Генератор 16 SVG из авторского TS](../../experiments/chartli/2026-11-07-svg-fixtures.mts) / [машинный manifest с SHA-256 всех исходных SVG](../../data/results/chartli/2026-11-07-svg-fixtures.json). Original `normalizeData` и `renderSvg` импортированы через локальный `tsx` из pinned checkout **без копирования или модификации источника**. Исходные файлы SVG создавались только во временной тестовой директории; пользовательских данных, сетевых запросов и внешних моделей не было.

**Внешний oracle:** [отдельный Python скрипт](../../experiments/chartli/2026-11-07-svg-oracle.py) заново считывает сырые файлы, сверяет SHA и выполняет **два независимых XML-разбора**: GNU `xmllint --nonet --noout` и `xml.etree.ElementTree`. Кроме того, он явно проверяет конечность координат `svg`/`circle`/`polyline`/`line`/`text`, количество примитивов и отсутствие неожиданных `script`-элементов; для специально экранированного `<script>`-текста проверено, что он остался текстом после XML-разбора. [Машинные результаты](../../data/results/chartli/2026-11-07-svg-oracle.json).

| Контроль | Результат |
| --- | ---: |
| 16 исходных генераций SVG | **16/16** доступны по SHA |
| Согласие независимых XML-парсеров | **16/16** |
| XML well-formedness | **14/16** |
| XML с конечной числовой геометрией | **11/16** |
| Позитивные single circles/lines и multi-series c легендой | **4/4** совпали по числу SVG-примитивов |
| Экранированные `<script>`, `&`, кавычки в labels | **2/2** остаются текстом, без script-element |
| Контроль повреждённого XML / подменённого `cx='NaN'` | **2/2** обнаружены независимым verifier |

**Два отрицательных XML-контроля:** входы с `\u0001` в `seriesLabels` и `\u0002` в `xAxisLabel` приводят к запрещённым PCDATA символам; оба независимых парсера отклоняют их. Следовательно, недостаточно экранировать только пять XML meta-символов для произвольного текста.

**Три неверных геометрических контроля:** `NaN`, `+Infinity` и переполненный exponent дают `NaN` в координатах. XML syntax passes, но отдельный finite-coordinate oracle отклоняет. Эти проверки сознательно построены на недопустимых числовых входах: это свидетельство **отсутствия защитного контракта на этом source path**, а не доказательство сбоя на валидных рядах.

**Режимы обычных данных:** circles/lines, single/multiple, legend, escaped axis labels, single point, flat values, negative values, empty data и ragged rows прошли оба независимых XML-контроля и finite-geometry gate. Ragged rows уже вызывают отдельный известный риск **семантического zero-fill**, который не может быть обнаружен одной XML-проверкой.

**Не выполнялось:** upstream `vitest run` (зависимости Chartli в checkout не установлены), полный пользовательский CLI, Rust renderer, реальный браузер и pixel/screenshot oracle. XML well-formedness плюс конечные координаты — необходимый, **но не достаточный** контракт для визуализационной корректности. Не присваивать научный статус на основании совпадения двух парсеров.

## Исследование → проекты

Актуальный registry [`Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`](https://github.com/Artemedi/project-registry/tree/fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6). Сопоставление всех профилей уже выполнено в [первой матрице Chartli](2026-11-04.md), которая остаётся в силе. На этом этапе не появилось конкретных новых source seams и project FIT.

| Исследование | Проект | Основание | Ограничения / следующий минимальный тест | Статус |
| --- | --- | --- | --- | --- |
| Chartli | `akuzlogparser` | В исходном [README@d6061aa](https://github.com/Artemedi/akuzlogparser/blob/d6061aa83cdeadc22e30cfaee36aea94ac131bb2/README.md#L42) заданы числовые диагностические `elapsed_s`; гипотетическая визуализация была отмечена ранее. | До внедрения нужен source@SHA конкретного exporter, schema валидных finite numeric values и timestamps, gold chart vs table, no hidden zero-fill. Запретить XML control chars, проверять единицы, IO и CPU. | `PROFILE_MATCH / SVG_CONTRACT_PARTIAL / NO_FIT_UPGRADE` |
| Chartli | `akuz-schema-inventory` | Историческая [архитектура@8d8adcd](https://github.com/Artemedi/akuz-schema-inventory/blob/8d8adcdf99cea0bd4e9fde40cfac2fb3371d9487/ARCHITECTURE.md#L103) описывает snapshot analytics; возможность диаграмм — лишь гипотеза. | Независимый тест экспортируемой таблицы + графика для разных масштабов и missing/NaN/inf, с финансовой и диагностической точностью; не заменять таблицы на SVG без объяснимой шкалы. | `PROFILE_MATCH / NEEDS_NUMERIC_ORACLE / NO_FIT_UPGRADE` |

Реальное поведение этих двух проектов **не испытывалось**; классификацию `PROFILE_MATCH` до `VERIFIED_FIT` не повышать. Другие проекты не получили нового сопоставления. Издержки: дополнительная фильтрация/валидация XML и чисел увеличит CPU/сложность и немного память/IO на парсинг, но измерения отсутствуют; браузерный render и SVG injection/external reference security также не проверены.

**Вердикт:** `SOURCE_PINNED / ACCEPT_BOUNDED_SVG_XML_AND_NUMERIC_ORACLE`, `REWORK_INPUT_SANITIZATION_AND_FINITE_GEOMETRY`, `NO_NEW_FIT`, `NO_PRODUCTION_APPROVAL`. Реальные исходники целевых проектов и исторические source cards **не изменялись**. Следующий gate для Chartli — сначала валидный numeric/export contract, потом сравнение графика с таблицей и с независимыми координатными ожиданиями. Пока архивировать этот ограниченный результат, не развивать отдельный графический framework.
