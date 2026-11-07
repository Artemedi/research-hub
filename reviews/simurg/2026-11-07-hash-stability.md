# SIMURG — независимая проверка межпроцессной воспроизводимости sketch/SimHash

**Дата:** 07.11.2026. **Дополнение к уже завершённому [полнотекстовому обзору SIMURG от 04.11](2026-11-04.md)**. Исторические проверки AUROC, калибровки и ложных срабатываний **не повторялись**. Проверяли ровно оставшийся source-based пробел из [массового аудита](../../portfolio/2026-11-07/mass-swarm-review.md): оценка функции `stable_hash()` и двух потребителей в независимых процессах с различным `PYTHONHASHSEED`.

**Первоисточник:** оригинальный полный 13-страничный технический отчёт [`paper/simurg_paper.pdf`](https://github.com/doofzoff/SIMURG/blob/2831a92359cdaf1b38cc14f55e74251e09a91e0b/paper/simurg_paper.pdf) и [авторский SIMURG v1.0.4 @ 2831a92359cdaf1b38cc14f55e74251e09a91e0b](https://github.com/doofzoff/SIMURG/tree/2831a92359cdaf1b38cc14f55e74251e09a91e0b). Публикация 24.08.2026, исходный код 21.09.2026; peer review не подтверждён, лицензия Apache-2.0. Метод, авторские измерения и ограничения полного PDF рассмотрены в предыдущем обзоре. Извлечённый источник на этой волне — **реальный код**, а не abstract.

## Метод и точное проверяемое утверждение

В [`core.py:28–35`](https://github.com/doofzoff/SIMURG/blob/2831a92359cdaf1b38cc14f55e74251e09a91e0b/src/simurg/core.py#L28-L35) автор реализует `stable_hash(string, seed)`: BLAKE2b digest size 8, ключ из числа seed в little endian (когда seed ненулевой), результат как 64-битное unsigned целое little endian. Преобразование строки: UTF-8 с `errors="ignore"`. Две реализации используют именно эту функцию:

- [`signals/sketch.py:20–40`](https://github.com/doofzoff/SIMURG/blob/2831a92359cdaf1b38cc14f55e74251e09a91e0b/src/simurg/signals/sketch.py#L20-L40) — Count-Min Sketch, четыре строки и отдельные deterministic seeds для bucket columns.
- [`signals/simhash.py:29–62`](https://github.com/doofzoff/SIMURG/blob/2831a92359cdaf1b38cc14f55e74251e09a91e0b/src/simurg/signals/simhash.py#L29-L62) — оконный 64-битный SimHash, majority bits, baseline после заполнения восьми токенов и относительный Hamming drift.

**Зафиксированные исходники:** `core.py` SHA-256 `8d0f7509146e62cbf0a1f485eb6e08935d014659e97f2157879178baf2dfa8cd`; `sketch.py` — `453a24545e0ae0150d05526a5c8e5d32eb761d97e7b5b6b1b9e7d11f76c4a841`; `simhash.py` — `419bf411f7fb18bfe89bd16ef271ce7f5be16b3344ef6724fa19ce4d0be94e3a`. До запуска независимый код проверяет commit и все три SHA; сторонний checkout остался неизменённым.

## Эксперимент и отдельные оракулы

[Исполняемый worker исходных функций](../../experiments/simurg/2026-11-07-hash-worker.py) / [управляющий процесс и отдельный oracle](../../experiments/simurg/2026-11-07-hash-stability.py) / [проверяемые исходы и хеши](../../data/results/simurg/2026-11-07-hash-stability.json).

Запущены **четыре независимых Python-процесса** с `PYTHONHASHSEED=0, 1, 42, 1337`, каждый импортирует оригинальные `stable_hash`, `CountMinSketch`, `RollingSimHash`, а не переписанные версии. Использованы 10 уникальных токенов, включая кириллицу, emoji, SQL/PG слова и повторения; 12 операций Sketch и 12 снимков оконного SimHash. Внешний oracle в отдельном управляющем процессе самостоятельно рассчитывает seeded hashes через стандартную `hashlib.blake2b`, sketch bucket matrices с инкрементами и rolling majority fingerprints через прямое суммирование 64 битов. Для **каждого unkeyed hash** задействована внешняя утилита `b2sum -l 64` — отдельный независимый исполняемый процесс. Это проверка двух независимых способов вычисления; алгоритм BLAKE2b при этом общий, и верификатор не является криптографическим аудитом реализации хеша.

| Контроль | Подтверждённый исход |
| --- | ---: |
| Совпадение source-output между разными PYTHONHASHSEED | **4/4** процесса, один и тот же SHA без встроенного `hash()` |
| External GNU `b2sum` vs `stable_hash()` без key | **10/10** уникальных строк |
| Seeded `blake2b` vs source и bucket reconstruction | **12/12** последовательных sketch-добавлений |
| Независимый bit-majority oracle vs RollingSimHash | **12/12** снимков, включая baseline/drift |
| Контроль Python builtin `hash("postgresql")` | **4 разных значения**; окружения действительно различаются |
| Подмена числа в stable-hash / одного SimHash snapshot | **2/2** отклонены |

**Расход:** 4 локальных коротких подпроцесса, фиксированные 256 колонок × 4 строки sketch; CPU/RAM/IO production не трогались, модельные вызовы и GPU отсутствуют. Метрики скорости/стоимости **не измерялись**; по ним делать выводов нельзя.

## Независимая контрпроверка и смысл результата

Числовой oracle проверял значения, полученные *реальным* авторским кодом, а не ответы модели. Внутренний Python `hash()` менялся с seed, тогда как независимый BLAKE2b и sketch/SimHash source сохраняли результат. Это строго подтверждает **process-stable reproducibility выбранных входов**, полезную для воспроизводимости детекторных feature-сигналов.

Ограничения: это **не** тест точности классификации corrupt/clean, не AUROC и не conformal false-alarm rate; 12 токенов не дают репрезентативной оценки русскоязычного/SQL production traffic. BLAKE2b одинакового размера может иметь коллизии; обработка UTF-8 `errors="ignore"` выбрасывает неправильные code points; ни одна детерминированная hash-функция не доказывает семантическую валидность LLM-ответов. Ранее [обнаруженные ошибки AUROC на ties и false alarms при calibration](2026-11-04.md) остаются **открытыми**, и локальный успех стабильности их не исправляет.

## Исследование → проекты

Сверена существующая матрица [прошлого обзора](2026-11-04.md) с актуальным registry `Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`; новые backlinks не создавались. Источники двух целевых проектов не правились.

| Исследование | Проект | Основание | Ограничения и следующий минимальный эксперимент | Статус |
| --- | --- | --- | --- | --- |
| SIMURG | `dsh-runtime` | Ранее подтверждена text/tool delta граница [streaming types @b6a1635](https://github.com/Artemedi/dsh-runtime/blob/b6a1635b1200071754e2871b9d9453368e6daf23/packages/llm/llm/src/types.ts#L390-L392); актуальный HEAD `3feed5d`, но новый end-to-end source seam/bench **не проверен этим тестом**. | Изолированный text-only replay по текущему @SHA, A/B guard on/off, byte-exact tool delta preserved, смешанный RU/SQL/JSON corpus, false abort/retry/latency/IO/cost. Прежде исправить AUROC/calibration и сформировать holdout. | `PROFILE_MATCH / HASH_STABILITY_VERIFIED / FIT_UNCHANGED` |
| SIMURG | `9router` | Исторический pinned SSE handler [@d15f5bf](https://github.com/Artemedi/9router/blob/d15f5bf3289e50bddda8263cddd239d7078e4ef0/open-sse/handlers/chatCore/streamingHandler.js#L1-L30); локальная актуальная рабочая копия в ходе этого эксперимента **не доступна**. | Не переносить Python guard на JS SSE без нового source@SHA и строгого test harness. Внешние источники и user events не исполнялись. | `HISTORICAL_SOURCE / NEEDS_CURRENT_CHECKOUT / FIT_UNCHANGED` |

Для остальных проектов текущего реестра новых конкретных implementation seams не подтверждено. Наличие streaming-ответа само по себе не оправдывает добавление ещё одного guard. Нет новых FIT approvals.

**Вердикт:** `ACCEPT_BOUNDED_CROSS_PROCESS_HASH_STABILITY` с **нулём новых модельных утверждений**; `REWORK_STREAMING_QUALITY_AND_CALIBRATION`; `NO_NEW_PROJECT_FIT`; `NO_PRODUCTION_APPROVAL`. Следующий полноценный критерий внедрения — независимое измерение false positives/false negatives на held-out корпусе, сохранность выходных delta и корректность rollback. Повторять стабильность hash без нового источника не нужно.
