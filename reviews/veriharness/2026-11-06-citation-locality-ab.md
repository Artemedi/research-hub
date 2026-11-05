# VeriHarness / agent-config — воспроизводимый offline A/B для citation locality

**Дата:** 2026-11-06. **Тип:** `BOUNDED_CODE_REVIEW / OFFLINE_AB_OBSERVED / NO_LLM`. Связан с [историческим исследованием](2026-11-04.md) и [полным текстом VeriHarness](2026-11-05-full-text.md), **но не воспроизводит эксперимент LLM-verifier**.

**Реальный тестируемый исходник:** `Artemedi/agent-config@489e074ab0daaadb732673c193047172a3744862`, `tools/review.py:103–113`, функция `check_findings`, SHA-256 файла `5aa8032a7c56fc6ff1fe050138343a54d8363d1211aa72e7733c153001cfe505`. Библиотека не патчилась и не коммитилась. Хост: Bazzite 44, Linux `6.18.56-ogc1.1.fc44.x86_64`, Python 3.14.8.

**Скрипт:** [2026-11-06-agent-config-citation-locality-ab.py](../../experiments/2026-11-06-agent-config-citation-locality-ab.py). **Raw данные:** [1000 случаев, пять seeds](../../data/results/veriharness/2026-11-06-citation-locality-ab.json).

## Протокол

Пять непересекающихся сгенерированных наборов (`seed=20261106..20261110`), по 200 случаев каждый: 40 `valid_exact`, 40 `valid_neighbor`, 40 `wrong_line`, 40 `fabricated_quote`, 40 `false_behavior`. Положительные примеры: исходная цитата на указанной или соседней строке плюс верное выполнение функции. Отрицательные: реальная цитата с *неверной* строкой; несуществующая цитата; корректная цитата, но ложное ожидаемое поведение. Уникальные threshold/gate fixtures создаются с фиксированным seed.

**Независимый относительно алгоритма проверки oracle** вычисляет допустимость location и текста из генератора, а поведение проверяет исполнением **только самостоятельно сгенерированного Python `gate(n)`** на конкретном входе; результат сверяется с выражением `n >= threshold`. Сам `check_findings` не участвует в создании ground truth. Разделение не слепое для автора fixtures: это ограничение протокола.

- **A / baseline:** реальная `review.check_findings`, принятие только когда `location_ok and evidence_found`. Текущее определение `evidence_found` ищет цитату во всём файле.
- **B / treatment:** тот же исходный `review.check_findings` плюс детерминированный локальный контроль: цитата должна встречаться в окне **строка ±1**.
- Оба варианта получают **одинаковые** данные; порядок A/B меняется через seed, чтобы ослабить грубый warm-cache bias. Учитываются TP/FP/TN/FN и вычислительные показатели. Каждая из пяти seed-пар является отдельным повтором; не пять одинаковых исполнений одной выборки.

## Наблюдения

| Показатель на 1000 специально сконструированных случаев | A: Baseline | B: Locality |
| --- | ---: | ---: |
| TP / FP / TN / FN | 400 / 400 / 200 / 0 | 400 / 200 / 400 / 0 |
| Precision (в этом искусственном балансе классов) | 0,500 | 0,667 |
| False accept rate среди 600 ложных утверждений | 66,7% | **33,3%** |
| Recall на 400 положительных fixtures | 100% | 100% |
| Среднее wall time на 200 случаев, 5 repeats | 8,973 мс | 13,465 мс |
| Диапазон p95 на один check across seeds | 46,7–52,6 мкс | 73,5–105,0 мкс |
| `tracemalloc` peak Python allocations, типичный run | ~141 KB | ~141 KB |
| `/proc/self/io` physical `read_bytes/write_bytes` при evaluation | 0/0 | 0/0 |

Относительная **накладная стоимость B**: примерно +50% wall/CPU в микробенчмарке. Замеры `/proc/self/io` не включают генерацию исходных файлов и запись итогового JSON, которые сделаны **вне** timed evaluation. `ru_maxrss` в JSON — пиковый RSS всего процесса, **не** память отдельного варианта. Python `tracemalloc` не измеряет kernel memory. Микросекундные тайминги зависят от накладных расходов instrumentation и cache.

**Токены:** `N/A` (LLM не запускалась). **Сетевая стоимость inference:** 0 USD, поскольку не выполнялись API-вызовы, но это не сравнительная оценка стоимости LLM. **VRAM:** `N/A` (нет GPU workload). **CPU:** `process_time` и wall time измерены в JSON. **IO:** указан именно процессный IO evaluation, не полный storage footprint стенда.

## Контроли и ограничения

Наличие `wrong_line` проверяет проблему local provenance; `fabricated_quote` проверяет отрицательный путь исходной функции; `false_behavior` демонстрирует **оставшиеся** ложные принятия — цитата сама по себе не доказывает выполнение заявленного поведения. Таким образом, результат нельзя интерпретировать как «точность анализа кода улучшилась на 33 п.п. в production». Соотношение классов искусственное, semantic oracle для реальных замечаний отсутствует. Не запускались полный VeriHarness, resolver/challenger/adjudicator, LLM, реальные проекты или внешние инструменты.

| Исследование | Проекты | Почему | Ограничения | Следующий минимальный опыт | Evidence |
| --- | --- | --- | --- | --- | --- |
| VeriHarness / citation locality | `agent-config`, `dsh-runtime` | Existing review gate принимает quote вне указанной строки; no new framework | Только artificial file:line fixtures; 50%+ overhead в микробенчмарке | Добавить разные source languages, multiline quotes, повторяемые строки, реальные обезличенные findings и blind human oracle, затем обсудить отдельный PR | `SYNTHETIC_AB_PASS / PROJECT_BENEFIT_NOT_MEASURED` |

**Решение:** метод готов к следующей офлайновой проверке на более реалистичных разнотипных файлах, **не** к немедленной интеграции. Production, исходники `agent-config`, DSH и их настройки не изменены.
