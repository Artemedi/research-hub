# Research intake — TufaZip, 21 ноября 2026

**Окно:** пользовательский источник от 21.11.2026, полный авторский технический текст от 14.10.2026; ревизия pinned `Tufalabs/tufazip@b9d678db3a0f726e117c8cab51927975830395ac`. Сопоставление с `Artemedi/project-registry@7a976c353579f8da64789daf18fe1088e5ab8dbb`, все 45 проектов. Каталог `Artemedi/research-hub@e1c3ea06c45d84b77814fafd938e27e031c78766` без ранее существующей карточки TufaZip. Новых Telegram-BK идентификаторов не создано.

## Результат

Одна техническая работа с полной методологией и кодом: [TufaZip — source review](../../reviews/tufazip/2026-11-21.md), [источник](../../studies/tufazip.md). `REVIEWED_DEFERRED / NO_FIT`, несмотря на подтверждённый официальный benchmark score — в текущем портфеле отсутствуют доказанные workload и hardware для недельного специализированного энтропийного кодирования текста. Обратных ссылок в проектные карточки нет.

| Исследование | Проект | Обоснование | Ограничения | Минимальный следующий тест | Статус |
| --- | --- | --- | --- | --- | --- |
| [TufaZip v2](../../studies/tufazip.md) | **NO_FIT** по всем 45 PROJECT.md; near misses: confluence-wiki-backups, dsh-team-context, Wiki_PG, dsh-runtime | Эти проекты требуют быстро читаемого архива/семантического извлечения, а статья оценивает только lossless compressed bytes фиксированного enwik9 | Fixed decoder, exact 2× B200+CUDA runtime, многодневные encode/decode, pretrain weights и нет end-to-end utility | Только после документированного cold archive workload: 1–10 MB synthetic corpus vs zstd по total compressed size, SHA-256 roundtrip, read latency, ресурсам, 3 повтора. Toy-copy метод не равен TufaZip reproduction | `DEFERRED / NO_FIT / BLOCKED: MEASUREMENT_MISSING` |

**Ценность методологии:** 6/10 для исследовательского понимания neural predictor + arithmetic coding; **применимость текущим проектам:** 1/10, **прямая сложность репликации:** 10/10 из-за жёстких GPU/временных ограничений. Оценки качественные, не model-run outputs. Авторская v2 декодирующая программа не запускалась; проверены только static code и хеши локальных публичных файлов, а не готовый энкодер или обратное восстановление enwik9. Никаких экспериментальных/production изменений.
