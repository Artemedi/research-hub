# Offline A/B: второй и третий пилоты — LIMBO и RRSI/Harness²

**Дата:** 2026-11-06. **Previous:** [первый VeriHarness/agent-config A/B](offline-ab-pilot.md). **Контроль приоритета:** [только CVE-2026-82533 в DSH является приоритетной интеграцией](integration-priority.md). Ни одна из проверок ниже не повышает статус источников до успешно внедрённых, не утверждает научную репликацию и не меняет исходники проектов.

## Выполненные исследования

| Офлайн A/B | Реальный проверенный код | Независимый test oracle | Результат | Трейдофф | Verdict |
| --- | --- | --- | --- | --- | --- |
| [LIMBO × TelegramBot](../../reviews/exactly-once-limbo/2026-11-06-policy-ab.md) | Pinned `TelegramBot.main()/send_telegram()`, fake network transport | Effect ledger мок-сервиса, 9 fault-классов × 20 × 5 seeds | Auto retry: **600 дублей, 0 пропусков** /900; sidecar no retry: **100 дублей, 200 пропусков** /900; `idempotency` fake-server control: **0/0** | Уменьшение повторов ценой потери сообщений; provider idempotency в Telegram не подтверждена; около 1 600 vs 900 synthetic HTTP calls | `SYNTHETIC_POLICY_TRADEOFF_OBSERVED / NO_DEPLOYMENT` |
| [RRSI/Harness² selection](../../reviews/rrsi/2026-11-06-validation-ab.md) | Real `rrsi.select_round()`, `rrsi.aggregate()`, `harness2.selection_pool()`, `agent-config.check_findings()` | Self-generated executable `gate()` + independent sealed holdout, 5 seeds × 105 tasks | Train-only selector выбирает overfit memorizer **5/5**; с external validation guard — locality **5/5**; holdout **45,5% vs 70,5%** | Внешний guard — **не дефолт** RRSI, а модельный oracle не исследован; runtime tokens/cost `N/A` | `BOUNDED_SELECTOR_AB_OBSERVED / NO_MODEL_RUN` |

**Ресурсы и воспроизводимость.** Оба эксперимента измерили wall/CPU, process highwater RSS, Python allocations, `/proc/self/io`, p50/p95 по подходящим участкам. Физические прочитанные/записанные байты в cached-тестах равны нулю; логическое IO не нулевое. GPU/VRAM = `N/A`; inference token count = `N/A`; API cost = 0 USD, без платных вызовов. По всем пяти seed результаты и хэши fixture/source-контролей воспроизведены во втором прогоне; микротайминги закономерно не совпадают побайтно.

**Сторонние исходные тесты:** LIMBO `65/65 PASS`, RRSI `8/8 PASS`; все соответствующие исходники остались неизменными. Raw data + runnable scripts: [LIMBO JSON](../../data/results/exactly-once-limbo/2026-11-06-telegrambot-policy-ab.json), [LIMBO replay](../../experiments/2026-11-06-limbo-telegrambot-policy-ab.py), [RRSI JSON](../../data/results/rrsi/2026-11-06-validation-harness2-ab.json), [RRSI selector](../../experiments/2026-11-06-rrsi-validation-harness2-ab.py).

## Следующая очередь без платных моделей и production

| Следующий кандидат | Baseline и измеримый oracle | Negative controls / критерий остановки | Статус |
| --- | --- | --- | --- |
| [DRAG](../../reviews/drag/2026-11-05-full-text.md) | BM25/search baseline против лёгкого router по синтетическому DBA-корпусу, одинаковый query budget | distractors, no-match, misleading retrieval; изменение recall@k, CPU/IO, latency и расходы без модели | `PROPOSED_OFFLINE_AB`, ещё не запущен |
| [RRSI transfer](../../reviews/rrsi/2026-11-06-validation-ab.md) | Применение к обезличенным реальным code-review примерам со слепой проверкой истины | Distribution shift, multi-line цитаты, семантически ложные claims | `NEEDS_REAL_TASK_ORACLE` |
| [TelegramBot durable outbox](../../reviews/exactly-once-limbo/2026-11-06-policy-ab.md) | Изолированный multi-process synthetic crash/restart, conditional no-retry | Simulated network partition, state lost, double worker; целевая политика дублей/пропусков | `NEEDS_OWNER_POLICY`; **не** patch production |

**Research → projects:** LIMBO → `TelegramBot`; RRSI/Harness² → `agent-config`, `dsh-runtime`; DRAG → кандидаты из ранее проверенной source→project матрицы, требует отдельного кода/строк интерфейса. Project integrations `NOT_APPROVED`; никаких новых автоматических git-правок этих проектов. `REGISTRY_BACKLINKS_PENDING`: новые протоколы пока не отражены отдельно в приватных project-registry карточках.

**Очередной gate:** попробовать DRAG с фиксированным synthetic corpus и независимым relevance oracle; не подменять этим полноценное обучение/routing LLM. По безопасности по-прежнему прежде всего закрывать CVE-2026-82533, без выполнения exploit на работающем DSH.
