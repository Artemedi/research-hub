# VeriHarness × agent-config — offline verification-gate experiment

**Дата:** 2026-11-04. **Статус:** `DETERMINISTIC_GATES_VERIFIED / FULL_LLM_VERIHARNESS_UNTESTED / NO_PRODUCTION_APPROVAL`.

**Цель:** проверить конкретные гипотезы из [полной исторической научной оценки VeriHarness](../studies/veriharness.md): снижает ли проверка источников и независимый исполняемый oracle ошибочное принятие результатов, и какую часть проверок действительно делает сам открытый VeriHarness.

## Версии и границы

- [VeriHarness upstream](https://github.com/google-research/veriharness/tree/0f10db9818920f8d79641b23d9311c4877f67702), commit `0f10db9818920f8d79641b23d9311c4877f67702`, Apache-2.0, `harness/driver.py:428` (`validate_delivery`) и `:485` (`complete_bundle`).
- [agent-config](https://github.com/Artemedi/agent-config/tree/489e074ab0daaadb732673c193047172a3744862), commit `489e074ab0daaadb732673c193047172a3744862`, `tools/review.py:103-113` (`check_findings`); `tests/test_review.py`, `tests/test_model_assist.py`.
- Host Bazzite: Python 3.14.8; `agent-config` tests: **33 passed, 0 failed** in 0.10 seconds, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; no real model calls.
- Model endpoint not found on checked local endpoints; no model-specific API key supplied to this isolated experiment. VeriHarness normally requires pi runtime + active provider and four agent turns (resolver, challenger, adjudication, delivery) over multiple rollouts. **Эти LLM-этапы не запускались.** Исследовательские числа из статьи не приписываются локальному тесту.
- No production, no real user project artifacts, no keys, no git commits to target source, no additional agent/skill service.

## Test A — agent-config citation guard (50 процедурно сгенерированных утверждений)

**Hypothesis A:** check `file:line` and quote not just in the bundle, but near cited line; verify claims about executable behavior against an independent run.

Прогон с фиксированным seed `20261104`; по 10 случаев каждого типа, отдельные искусственные `gate(n)`:

1. `valid_exact`: верный результат, буквальная цитата находится на указанной строке.
2. `valid_neighbor`: верный результат, цитата на соседней строке (разрешено исходным prompt).
3. `wrong_line`: верный результат, но указанная строка далеко от цитаты.
4. `fabricated_quote`: quote не существует в коде.
5. `false_behavior`: точная цитата существует, но утверждение о поведении опровергается исполнением `gate(n)`.

**Независимый oracle:** Python `runpy.run_path` выполняет только самостоятельно сгенерированные локальные функции с детерминированным входом; truth считается корректным **только если** указана допустимая строка, цитата реальна и заявленное поведение совпадает с результатом. Никаких внешних API, сетевых вызовов или пользовательского кода не выполняется.

| Процедура | TP (верное принято) | FP (ложное принято) | TN (ложное отклонено) | FN (верное отклонено) | Precision |
|---|---:|---:|---:|---:|---:|
| Текущий `review.check_findings`: `location_ok && evidence_found` | 20 | **20** | 10 | 0 | **0.50** |
| Дополнительная проверка цитаты в окне `line ±1` | 20 | **10** | 20 | 0 | **0.667** |
| Проверка цитаты + исполняемый oracle с известным expected result | 20 | **0** | 30 | 0 | **1.00** |

**Техническое объяснение:** в [исходной `check_findings`](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103-L113) `location_ok` проверяет существование строки, а `evidence_found` ищет цитату во **всём** содержимом файла. Следовательно, цитата с нерелевантной далёкой строки может получить оба признака `True`. Дополнительный locality gate устраняет 10/10 специально созданных далёких цитат, но не умеет доказывать семантические выводы — оставшиеся 10 false accepts требуют реального исполняемого oracle.

Это **не измеренная общая error rate** и не оценка LLM: случаи искусственные, классы равномерны, oracle заранее задан. Precision зависит от соотношения классов в наборе; результаты не позволяют оценить production false accept rate или эффект на unseen tasks. Условия `line ±1` отражают текущий prompt (строка или соседняя строка); для многострочных цитат потребуется отдельный контракт. Не менять `check_findings` вслепую.

## Test B — реальные deterministic gates VeriHarness (16 комплектов артефактов)

Вызваны **именно исходные функции** `validate_delivery(ws, "r01")` и `complete_bundle(ws, "r01")` из [Google VeriHarness driver](https://github.com/google-research/veriharness/blob/0f10db9818920f8d79641b23d9311c4877f67702/harness/driver.py#L428-L515). На 16 отдельных синтетических задачах у base лежат два файла, а out содержит:

- 4 структурно полных и семантически корректных комплекта;
- 4 с отсутствующим README;
- 4 с пустым README вместо непустого base;
- 4 структурно полных, но семантически неверных комплекта (`gate(5)` даёт `False` вместо `True`).

| Показатель | Измерено |
|---|---:|
| Структурно валидны до восстановления | 8/16 |
| Файлов восстановлено `complete_bundle` | 8 |
| Структурно валидны после восстановления | 16/16 |
| Некорректные по поведению программы, но прошли gate | **4/16** и до, и после восстановления |

Вывод: это **content-blind gate**, предназначенный для полноты и формы deliverable. Он не обязан проверять семантику; фаза анализа ошибок у реального VeriHarness находится в отдельных **LLM**-resolver/challenger/adjudicator. Не трактовать четыре неверных комплекта как дефект драйвера или доказательство недостатка полного VeriHarness.

## Повторяемость и код

Скрипт: [experiments/2026-11-04-veriharness-offline-replay.py](../experiments/2026-11-04-veriharness-offline-replay.py). Сам создаёт все 50 утверждений и 16 комплектов во временном каталоге, использует только source-проверку двух *pinned* репозиториев, самостоятельно проверяет итоговые TP/FP/TN/FN и тестирует реальные функции драйвера. При неожиданном результате assert падает.

```bash
git clone --depth=1 https://github.com/Artemedi/agent-config.git /tmp/verify-agent-config
git clone --depth=1 https://github.com/google-research/veriharness.git /tmp/verify-veriharness
# Зафиксировать SHA ревизий выше или использовать pinned checkout.
PYTHONDONTWRITEBYTECODE=1 python3 experiments/2026-11-04-veriharness-offline-replay.py \
  --agent-config /tmp/verify-agent-config \
  --veriharness /tmp/verify-veriharness

cd /tmp/verify-agent-config
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python3 -m pytest -q tests/test_model_assist.py tests/test_review.py
```

Стоимость сторонних inference-запросов: **0**; измерение LLM output tokens: **не проводилось**. Варианты со строгой проверкой цитаты и oracle представлены в replay-скрипте, **не в исходниках agent-config**.

## Что делать с результатом

1. **agent-config:** `CONFIRMED_CITATION_SCOPE_GAP` — перепроверить контракт определения `evidence_found`: должен отражать нахождение цитаты около указанной строки. Отдельным patch/PR + негативными регрессионными тестами, не в этом исследовательском запуске. Не вводить универсальный LLM verifier для однократной правки.
2. **DSH:** уже зафиксирован `@artemedi/dsh-verifier` (состояние из исторического обзора), **не заменять** его ещё одним движком без независимого A/B. Извлечь идеи resolver/challenger только после проверок сценариев общего неверного консенсуса и независимого oracle.
3. **Full VeriHarness:** `EFFECT_UNMEASURED`. Для настоящего научного сравнения нужны идентичный набор реальных agent rollouts, сессии с моделью, неизменяемый grader, набор shared-wrong и disputed claims, стоимость всех N генераций + 4 verifier turns. Без этого авторские +6.2/+6.4 балла не являются результатом пользователя.
4. **Security:** в исходном VeriHarness jail доступен на Bazzite по `jail_unavailable()`, но sandbox не испытывался на недоверенном коде. Не обещать безопасность isolation без такого теста. Генерируемые артефакты offline dataset исполнены только потому, что их код создан самим replay-скриптом.

## Изменения

Добавлены только протокол и автономный offline replay в `research-hub`, а также ссылки из уже существующей карточки VeriHarness, README и project-registry/agent-config. Никакого source patch, переключения моделей, установки hooks, API расходов и вмешательства в production нет.
