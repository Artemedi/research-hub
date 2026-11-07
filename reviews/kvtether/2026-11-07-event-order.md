# KVTether — порядок экспорта lifecycle events, но не физическая KV-политика

**Дата:** 07.11.2026. Продолжение уже завершённой [полнотекстовой проверки от 05.11](2026-11-05-full-text.md). Исторический [source card](../../studies/kvtether.md) не редактировался; полная авторская работа **повторно не рецензировалась с нуля**, только перепроверен узкий §4–8 контракт событий и ограничения для backend.

**Full legal original HTML:** [arXiv:2609.39819v1](https://arxiv.org/html/2609.39819v1), SHA-256 `d0c211ef0bc8cf6583ba7acb1b92b9609e0f44537062e7402a750d5e8a270bfb`, совпадает с ранее зафиксированным источником. Доступны Sections 2–9 с методом, экспериментами, ablation и overhead. **Registry pin:** `Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`. Рассмотрены профили всех текущих проектов, новое прямое право управлять физическим KV residency не установлено.

## Методология, результаты и ограничения источника

- **§4.1:** восемь lifecycle primitives: `append`, `replace`, `remove`, `fork`, `spawn`, `one_off`, `pin`, `unpin`. Это описания семантики context manager, **не** токенизация и не непосредственное размещение KV pages.
- **§4.2 и §5:** операции изменяют context ownership, shared prefix и жизненный цикл сообщений. `replace/remove` могут инвалидировать весь последующий KV suffix в контексте, даже если более поздний текст не изменился. Сервер преобразует message offsets в токены по **тому же formatter/tokenizer**, что и inference engine, и на границах LLM-вызовов различает Active/Suspended/Expired/Pinned/Temporary.
- **§7:** in-harness framework записывает вызов примитива **синхронно**, а экспортирует их в **сохранённом порядке асинхронно**. Далее server-side lifecycle manager принимает события и управляет GPU/host/remote cache через backend. Без такого backend автора **нельзя** воспроизвести ни физическую eviction policy, ни выгоду.
- **§8:** авторы сообщили среднее снижение end-to-end latency на **16,5% относительно LMCache** и **12,4% относительно MORI** на особой трёхузловой GB200 конфигурации, максимум 26,3/17,4%; предполагаемые task pricing savings 40,0/33,2% основаны на тарифной оценке. Это **не** измерение времени/денег в нашем портфеле. Приведённые накладные расходы sync primitive (<100 μs), interposition (<50 ms) и token mapping (~350 ms на 256K tokens) также строго workload/backend-specific.

**Пределы авторских результатов:** разные устройства, сетевой KV-tier, formatter/tokenizer, prefill ratio и доля повторного использования могут изменить знак выгоды. С закрытым удалённым API управлять physical KV placement нельзя; новые hook-методы в agent harness сами по себе не ускоряют inference. Против модели «KV cache lifecycle = обычный текстовый summarization».

## Исполнимый локальный эксперимент, строго ограниченный транспортным контрактом

В [исходном JS-сценарии](../../experiments/kvtether/2026-11-07-event-order.mjs) на **25 синтетических контекстах** генерируется последовательность восьми названных примитивов с явным `seq` и неключевой SHA-256 цепочкой. Асинхронная доставка с искусственно разными задержками доставляет события не по порядку, затем bounded receiver упорядочивает события по sequence и валидирует цепочку.

| Оракул | Измерено |
| --- | ---: |
| Неупорядоченный транспортный поток не является корректным serial event stream | **25/25** отклонений |
| Реконструкция по seq восстанавливает исходную последовательность | **25/25** успешно |
| Дубликат, потеря, неверный prev-hash, чужой контекст, мутация payload | **5/5** отклонены |
| Независимый Python-verifier с отдельным hash-chain алгоритмом | **25/25** контекстов, **200/200** событий |
| Отдельная мутация payload без пересчёта хеша | **REJECTED** |

[JSON следов](../../data/results/kvtether/2026-11-07-event-order.json) / [независимый replay](../../experiments/kvtether/2026-11-07-event-oracle.py) / [его JSON](../../data/results/kvtether/2026-11-07-event-oracle.json). Все проверки работают offline, без LLM, инференса, сети, прав администратора, GPU или пользовательских данных. Предыдущие попытки советников ZCode на других карточках подряд завершались провайдерскими отказами; ради соблюдения политики не был создан ещё один бесцельный запрос, отдельный проверяющий алгоритм выполняется локально.

**Критическое ограничение:** сценарий **не исполняет авторскую KVTether библиотеку**, не воспроизводит сообщения/токены/KV pages, не проверяет реальный SGLang, LMCache/MoonCake или профилирование GPU. Он демонстрирует *необходимость* упорядоченного экспорта и обнаружения потери/подмены, но **не** утверждает, что авторский код нарушает порядок. Сортировка по seq сама по себе не делает поток безопасным: нужны gap detection, ownership, hash provenance, настоящая локальная изоляция и доставка с правильными boundaries. Неключевой SHA не защищает от злонамеренного процесса с тем же UID.

## Матрица применимости и существующая инфраструктура

| Проект | Соответствие профилю | Необходимое подтверждение / компромисс | Диспозиция |
| --- | --- | --- | --- |
| `dsh-runtime` | Управляет агентным контекстом, но **не подтверждён owner физического KV-cache удалённого inference** | Нужен конкретный serving backend API для page residency, согласованный tokenizer и pinned source seam; иначе менять agent-loop ради восьми hooks бессмысленно. Дополнительные CPU, event IO, mapping latency и риск нарушения suffix validity. | `PROFILE_MATCH_ONLY / BACKEND_GATE_BLOCKED` |
| `HermesAgent` | Существует context/harness orchestration, но source профиля не доказывает доступность KV paging | Только после установки контролируемого локального/публично разрешённого inference backend выполнить реальную трассу и измерить true cache hits/latency, без секретов и медицинских сведений. | `AUTHOR_STATED_PROFILE / NEEDS_CONTROLLED_SERVING` |
| Все остальные, включая `Wiki_PG` и `paper2agent-index` | По состоянию snapshot нет подтверждённой необходимости управлять физическим GPU KV cache внутри этих проектов | Индексация документов, embeddings и caching ответа **не эквивалентны** KVTether; никаких искусственных FIT ради роста числа карточек. | `NO_CURRENT_TARGET` |

**Вердикт:** `ACCEPT_BOUNDED_SYNTHETIC_EVENT_ORDER`, `DEFER_KV_BACKEND_SPECIFIC`, `NO_NEW_FIT`, `NO_PRODUCTION_APPROVAL`, `BLOCKED_REAL_KV_MEASUREMENT`. Минимальный следующий gate — подтвердить controllable inference backend и его точные source@SHA интерфейсы, затем отдельный изолированный cache workload с валидатором prefix/SHA + исходным LRU baseline, графиками hit rate, p50/p95, bytes of KV moved, GPU/CPU RAM, storage/IO, error/rollback. Пока этого нет, **не внедрять** KVTether в agent runtime.
