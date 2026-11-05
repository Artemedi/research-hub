# Offline A/B: старт этапа экспериментальной валидации

**Дата:** 2026-11-06. **Область:** только offline synthetic, без платных LLM, root, GPU-моделей и production. **Наивысший интеграционный приоритет отдельно закреплён только за CVE-2026-82533 в DSH** — см. [исправленный backlog](integration-priority.md). Настоящий документ описывает **экспериментальную очередь**, а не список разрешённых внедрений.

## Выполненный первый пилот

[VeriHarness/agent-config citation guard — A/B](../../reviews/veriharness/2026-11-06-citation-locality-ab.md) • [скрипт](../../experiments/2026-11-06-agent-config-citation-locality-ab.py) • [машинные результаты](../../data/results/veriharness/2026-11-06-citation-locality-ab.json).

Проверены 1000 synthetic claims, 5 seeds, две равноправные ветки на одном наборе. Baseline `check_findings` нашёл citation где угодно в файле и ошибочно принял **400/600** отрицательных; добавленный guard `line ±1` ошибочно принял **200/600**. Положительные остались принятыми **400/400**. Наблюдаемое сокращение false accept на таких fixtures составляет 50% относительно baseline, при росте mean CPU/wall ~50% на evaluation. Все 200 оставшихся ложных принятия — класс `false_behavior`: необходим независимый исполняемый или статический семантический oracle, а не просто более строгая цитата. Это не A/B на LLM-агентных траекториях.

**Учет ресурсов:** wall/p50/p95, `process_time`, `tracemalloc`, process `/proc/self/io`, RSS snapshot; GPU/VRAM и tokens `N/A`, платных API calls `0`. Read/write bytes нулевые только в фазе проверки по заранее прочитанным строкам. Все данные, seeds, исходные версии и пределы валидности сохранены в raw JSON.

## Следующие дешёвые эксперименты — не интеграционные приоритеты

| Очередь | Научный источник | Независимый baseline и oracle | Отрицательные контроли | Gate |
| --- | --- | --- | --- | --- |
| После текущего пилота | [LIMBO](../../reviews/exactly-once-limbo/2026-11-05-full-text.md) | Реальный код TelegramBot + fake transport effect ledger; compare retry/reservation/idempotency where service supports keys | lost ack, late commit, redelivery, persisted state loss, no-key | Уже существует [bounded replay](../../reviews/exactly-once-limbo/2026-11-04.md); новый опыт должен добавить баланс дублей/пропусков и overhead, не выдавая fake contract за Telegram |
| После LIMBO | [RRSI / Harness²](../../reviews/rrsi/2026-11-05-full-text.md) | Held-out selector vs naive training-score ranking на pinned source functions | overfit memorizer, distribution shift, fake improvement / missing token-cost | Уже существует [smoke](../../reviews/rrsi-harness2/2026-11-04.md); нужны разные seeds, бюджет и честная агрегация |
| Отдельный без дорогой модели | [DRAG](../../reviews/drag/2026-11-05-full-text.md) | BM25 baseline vs constrained retrieval routing на synthetic document corpus | distractors, missing relevant document, citation drift | Отсутствует доказательство наличия уже внедрённого маршрутизатора; не утверждать улучшение RAG до опыта |

Для всех: неизменяемый oracle, заранее определённая метрика точности/надежности, отрицательные мутации, минимум 3 повторения, CPU/RAM/VRAM/IO, p50/p95, tokens и cost с явным `N/A`, если инструмент не использует модель, и критерий rollback. **Никакой** эффект на боевых нагрузках не наследуется от synthetic A/B.

**Критерий перевода в интеграционную задачу:** подтверждённый `repository@SHA/path:line`, исправление под тестами на целевом языке/файлах, воспроизводимая польза на реалистичных обезличенных данных, измеренная стоимость и отдельный owner gate. Пока всё перечисленное — `OFFLINE_RESEARCH`, без P1 и без deployment.
