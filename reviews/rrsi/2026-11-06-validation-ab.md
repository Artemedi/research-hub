# RRSI / Harness² — многократный offline A/B на sealed holdout

**Дата:** 2026-11-06. **Evidence:** `BOUNDED_SELECTOR_AB_OBSERVED / NO_MODEL_GENERATION / NO_DEPLOYMENT`. Продолжение [RRSI full text](2026-11-05-full-text.md), [Harness² full text](../harness2/2026-11-05-full-text.md) и [предыдущего однократного smoke](../rrsi-harness2/2026-11-04.md). **Не** репликация научных benchmark-чисел RRSI или полного multi-agent Harness².

**Фактические авторские code revisions:** `RRSI@be50316e1db05914068a973f322770ef08ed7ba1` (`rrsi/selection.py:select_round`, `rrsi/evaluate.py:aggregate`), `Harness²@6868817518876de8fd170c6a8354daca273b6191` (`harness2/core/selection.py:selection_pool, assign_ids`), целевой `agent-config@489e074ab0daaadb732673c193047172a3744862/tools/review.py:check_findings`.

[Протокол-скрипт](../../experiments/2026-11-06-rrsi-validation-harness2-ab.py) · [полный JSON результатов](../../data/results/rrsi/2026-11-06-validation-harness2-ab.json).

## Дизайн

Каждый из пяти независимых `seed=20261106..20261110` создаёт 40 train, 25 validation, 40 sealed holdout (итого 525 процедурно сгенерированных задач). Мутационные отрицательные классы: `wrong_line`, `fabricated_quote`, `false_behavior`; положительные: точные/соседние цитаты с верным исполняемым поведением. **Независимый oracle** запускает только созданные самим скриптом `gate(value)`; исходный `check_findings` не определяет truth. Holdout содержит распределительный сдвиг с пятью разными смесями классов и не используется ни одним selection guard.

Сравнение происходит на **том же исходном `RRSI.select_round`**:

- **A — без дополнительного validation guard:** выбирается максимально вознаграждённый по train вариант из синтетических candidates.
- **B — с явно добавленным внешним domain guard:** допускается только кандидат, улучшающий accuracy на *validation* хотя бы на 10 процентных пунктов; исходная функция поддерживает `guard_fn`, но **сама автоматически не создает** этот guard.
- Отрицательный control `memorizer` намеренно запоминает training IDs и при неизвестных ID возвращает baseline — 100% train и отсутствие прироста на validation/holdout.
- Кандидат `locality` лишь ищет quote в окне заявленной строки ±1 и **не** проверяет семантическое утверждение при точной цитате.
- Для Harness² отдельно фактически вызваны `selection_pool`, `assign_ids` из pinned source: режимы parallel/sequential исключили исходный baseline из собственного пула, детерминированные ID совпали. Ни `compose`, ни model calls/полный Harness² не выполнялись.
- Дополнительный **синтетический** negative-control `RRSI.cost_rule`: допустимая стоимость `ΔC=0` пропускается, а `ΔC=+900%` при `ΔS=+20pp` отвергается; это проверка математического правила, **не измерение расхода реальных токенов**.

## Наблюдения

| Показатель | Baseline | Train-only memorizer | Locality |
| --- | ---: | ---: | ---: |
| Train accuracy (каждый seed) | 60% | **100%** | 80% |
| Validation accuracy (каждый seed) | 60% | 60% | **80%** |
| Средний accuracy на sealed holdout, 5 seeds | **45,5%** | **45,5%** | **70,5%** |

**Решение исходного селектора без guard:** `memorizer` в 5/5 seeds. **С дополнительным guard:** `locality` в 5/5 seeds. Это разница в выборе `+25,0pp` на **искусственной** holdout-популяции, а не увеличение качества LLM-агента на 25pp. Отдельный memorizer — нарочно созданный overfitting control, **не** результат настоящего proposer RRSI. Семантические ложные утверждения всё ещё могут пройти locality.

**Ресурсные показатели:** среднее elapsed wall 45,5 мс и CPU 45,2 мс **на целый seed** (40+25+40), включая генерацию/исполнение synthetic кодовых fixtures, а не только selector. `selector_latency_us` сохраняет измерения двух собственно вызовов `select_round`, но сравнивать как скорость A/B недостоверно из-за микросекунд и кеша. Наибольший `tracemalloc` peak allocations в пяти seed около 423 KB, `/proc/self/io` зафиксирован с (physical read_bytes/write_bytes = 0/0) на cache, но логические rchar/wchar положительны. Shared RSS highwater не равен per-variant RAM. **VRAM:** `N/A`; **LLM tokens:** `N/A`; **API spend:** 0 USD.

**Воспроизводимость:** повтор пяти seeds дал совпадение контентных hash всех `gate` source fixtures, train/validation/holdout tables, решений selector, negative controls и выбора Harness². `RRSI` upstream `tests/test_core.py` — **8/8 PASS**. Нет реальных внешних LLM, платных моделей, privilege elevation, production или source patch.

## Вывод

**Подтверждённая механика:** максимизация train-only estimate в конкретном синтетическом сценарии допускает переобученного кандидата, дополнительная проверка validation способна блокировать его, пока оно общее для кандидатов. Нельзя по одному типу искусственно созданных задач заключать, что RRSI стандартно переобучается, или что самостоятельно созданная политика validation необходима во всех его приложениях. Для действительного агента сначала нужен blind real-task holdout и измерение inference-budget, потому что в этом опыте `EvalResult.C=None`, cost gates нельзя считать практически проверенными.

| Исследование | Проекты | Почему | Ограничения | Следующий минимальный опыт | Evidence |
| --- | --- | --- | --- | --- | --- |
| RRSI / Harness² selection | `agent-config`, `dsh-runtime` | Подтверждена исходная функция отбора и проверенный locality seam в `agent-config` | Нет proposer/LLM, только synthetic source claims и Harness² selection_pool | 3× blinded anonymized real-code findings, train/validation/holdout, 100% isolation, tokens + wall/CPU/IO, blocked default cost unknown | `SOURCE_SELECTOR_AB_OBSERVED / REAL_AGENT_VALUE_UNKNOWN` |
