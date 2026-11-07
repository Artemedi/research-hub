# Hyperresearch — реальный upstream test contract на закреплённом исходнике

**Дата:** 07.11.2026. Дополнение к [полному инженерному обзору 04.11](2026-11-04.md) и [предыдущему независимому 125-парному цитатному стресс-тесту](../../portfolio/2026-11-07/next-evidence-round2.md). Эти 125 сценариев и вопрос семантической корректности цитат **не повторяются**: прежний вывод `REWORK_MECHANICAL_CITATION_GATE` сохраняется.

**Первичный инженерный источник:** [`jordan-gibbs/hyperresearch@aece65f9307197119629beacf8aeaf8cc80e999a`](https://github.com/jordan-gibbs/hyperresearch/tree/aece65f9307197119629beacf8aeaf8cc80e999a), версия 0.13.0, MIT. Проверен оригинальный Git HEAD и source SHA: `src/hyperresearch/core/citecheck.py` = `53405db780de66866e8b3131f7a99edc1341832095fcc7b0888eaae69684a465`, `tests/test_core/test_claims_and_embed.py` = `0d44ba20bc2ff1247135850aa0c2a294850838a979c7bfa57ab697d2d7a1a2ab`, `tests/test_core/test_source_ranking.py` = `1edd23c944867140cab025b0a3ff8cc8402ced4d65a297069b132bb2b38be77d`.

## Метод и реально измеренный результат

[Воспроизводимый раннер](../../experiments/hyperresearch/2026-11-07-pinned-upstream-tests.py) исполняет *исходные авторские pytest* в двух выбранных ядровых наборах на Python без загрузки LLM, API или расширений: тесты хранения/поиска claims и embeddings плюс source ranking, schema v9, DOI/quality. До запуска проверяется commit SHA и три точных SHA-256. `PYTHONPATH` указывает на pinned `src`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `PYTHONDONTWRITEBYTECODE=1`, `pytest -p no:cacheprovider`, без `pip install` и модификации исходника. `--collect-only` независимо сверяет число тестов; в этой конфигурации два файла содержат **28 + 26 = 54** теста.

**Результат:** **54/54 PASS**; `pytest` exit 0, SHA stdout `92295b0fc8c365eeec63cb280b6f7d3e27385895ff2f0098073b8c696eb46d80`; [сохранённый протокол и локальные CPU/wall метрики](../../data/results/hyperresearch/2026-11-07-upstream-tests.json). Это реальные импорты и тесты из upstream; *не* подмена тестов JSON-описанием и не голос модели. При этом авторские тесты — **не независимые научные gold labels** и не доказательство отсутствия источниковых ошибок.

**Независимая контрпроверка:** уже опубликованный [стресс-тест triage пар](../../data/results/research-portfolio/2026-11-07-hyperresearch-citation-ab.json) ранее выявил **75/100 ложных `supported-mechanical`** на намеренно враждебных примерах и `0/100` ложных auto-pass у внешнего exact-only gate на том же составленном корпусе. Эта строка относится к author-created synthetic dataset, не реальному проценту ошибок в научных статьях. Текущие 54/54 upstream tests **не опровергают** контрпример: они проверяют другие функции. Это и есть независимая проверка области применимости двух несовместимых «процентов успеха».

## Исследование → проекты

Актуальный `Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`. Сопоставление всех 45 профилей выполнено ранее в [обзоре и матрице](2026-11-04.md); новых проверенных source seams в target нет.

| Исследование | Проект | Основание | Минимальный независимый следующий тест | Статус |
| --- | --- | --- | --- | --- |
| Hyperresearch | `agent-skills` | Использует проверки навыков/источников в workflow; источник подтверждает техническую реализуемость claims-store, но не защищённость итогового semantic review. | На чистой копии текущего target собрать held-out пары прямых, косвенных, смешанных цитат из легальных полных источников; сравнить exact-only/reviewer, false support, latency/token costs; user approval отдельно. | `PROFILE_MATCH / UPSTREAM_TESTS_PASS / NEEDS_SOURCE_GROUNDED_EVAL` |
| Hyperresearch | `dsh-paper2agent` | Есть собственный путь `submit_analysis`, уже отдельно проверенный в [target A/B](../../portfolio/2026-11-07/target-counterchecks-round4.md); это **структурная** приёмка, а не семантическая. | Тот же независимый adjudication corpus, oracle support и запрет присваивать научное `ACCEPT` результатам valid JSON. Не дублировать оркестратор. | `PROFILE_MATCH / CITATION_GATE_REWORK_UNCHANGED` |

**Компромиссы:** точный literal gate заметно уменьшает риск ложно положительного citation pass, но переводит перефразы на более дорогую модельную проверку; добавление полного внешнего citation engine повышает сложность, RAM/IO и latency без доказанного target выигрыша. Сейчас измерено только `pytest` на одном локальном runtime, не workload/SLA. Никаких рабочих профилей, секретов, медицинских данных или сетевого LLM не использовано.

**Вердикт:** `ACCEPT_PINNED_UPSTREAM_TEST_CONTRACT_54` и прежний `REWORK_MECHANICAL_CITATION_GATE` остаются совместимыми, потому что относятся к разным проверяемым свойствам. `NO_NEW_PROJECT_FIT / NO_PRODUCTION_APPROVAL`. Не повышать статус на основании 54 тестов и не повторять текущую проверку при неизменном SHA.
