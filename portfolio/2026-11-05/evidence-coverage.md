# Доказательное покрытие Research Hub — повторная проверка первоисточников

**Дата:** 2026-11-05. **Исходный снимок:** `research-hub@ec08c7fc04db40fab4fff52ad3071e02847cb5d4`; `project-registry@838b86a28fcaa3440eeddbe147b6188e0d177963` (45 проектных карточек). Этот отчёт дополняет, но не заменяет [обзор 5 ноября](review.md) и [историческую миграцию](../../docs/migration-completion.md).

**Область аудита:** 81 Study, 51 paper, существующие версии, Review, Assessment и данные связей. Отдельно прочитаны полные авторские HTML трёх работ. Все остальные scientific/evidence statuses сохранены без повышения. Внешние научные эксперименты, платные модели, системные инструменты и production не запускались.

## Закрытые доказательные пробелы

| Источник | Новое подтверждение | Что осталось непроверенным |
| --- | --- | --- |
| [RRSI](../../reviews/rrsi/2026-11-05-full-text.md) | arXiv:2609.24972v3, полный метод, таблицы и приложения, HTML SHA-256 | Оригинальные модельные эксперименты, токены и проектная выгода; [предыдущий bounded lab](../../reviews/rrsi-harness2/2026-11-04.md) сохранён |
| [Harness²](../../reviews/harness2/2026-11-05-full-text.md) | arXiv:2610.14224v1, Propose–Probe–Compose, результаты, неудачи, ограничения | Полный end-to-end agent experiment и безопасность самоизменения |
| [CERA-MoA](../../reviews/cera-moa/2026-11-05-full-text.md) | arXiv:2609.18779v1, контрольная версия, метод co-training и аппаратные издержки | Воспроизведение авторского обучения; `NO_CURRENT_TARGET` сохранён |

Обзоры получают `FULL_TEXT_REVIEWED` только как факт самостоятельного чтения полнотекстовой версии; `AUTHOR_REPORTED` не означает `LAB_VERIFIED`. Предыдущие Review records не удалены и не объявлены заменёнными.

## Незакрытая очередь научных источников

**Осталось 12 papers без явного `FULL_TEXT_REVIEWED` в модели v2:**

- `agent-error-dataset`, `covert-assistance`, `drag`, `exactly-once-limbo`
- `kvset`, `kvtether`, `maadbench`, `paper2agent`
- `realm`, `recap`, `statecomp`, `veriharness`

Историческое `FULL_TEXT_REVIEW_RECORDED` не выдавать за повторное прочтение; bounded code-review не заменяет работу с полным научным текстом. Дополнительно `unreal-agent` остаётся `FULL_TEXT_UNAVAILABLE` до доступа к исходному видео/транскрипту.

**Version pins:** 18 исторических записей все ещё имеют неизвестную версию; CERA-MoA сохранил исходную historical unknown, новой проверке отдельно присвоен arxiv:v1. У остальных 17 источников ещё нет подтверждённой актуальной редакции. Не угадывать версии и не изменять historical provenance.

**Engineering:** 24 записи `PARTIAL_SOURCE_REVIEW` остаются ограниченными; это допустимая доказательная категория, не общая очередь на дорогой E2E. Три normalized Experiment envelopes не означают, что отсутствовали все остальные исторические сырые опыты.

## Project-fit и безопасный предел

Покрытие project-fit не переоценивается механически: `MIGRATED=4`, `PARTIAL=73`, `NO_DOCUMENTED_ASSESSMENT=4`; новые рекомендации не добавлялись. Профильное совпадение не равняется проверенному integration seam. Для CERA нужен trainable backend/hidden states и бюджет GPU, поэтому его прежнее `NO_CURRENT_TARGET` и отсутствие backlinks сохранены.

Для `TrinMedicalBot` отдельно оставить открытым вопрос отображения `assessment.decision=DEFERRED` при evidence `PRODUCTION_DEPLOYED / CLINICAL_REVIEW_PENDING`: это известный семантический конфликт проекции, а не разрешение присваивать клиническую валидацию. В этом документальном проходе никаких медицинских утверждений или статусов не меняли.

## Следующие доказательные gates

1. Проверить 12 оставшихся полных первоисточников с версией/хешем, методами, числами, приложениями и ограничениями; добавлять только датированные Review, не менять историю молча.
2. Сопоставить остальные 17 источников с неизвестной актуальной версией, отдельно сохраняя историческое UNKNOWN для CERA-MoA; не подменять исходную ревизию более поздней.
3. Для предметно выбранных project targets — актуальный `repo@SHA/path:line`, baseline, независимый oracle, mutation/negative controls, повторения и измерения CPU/GPU/RAM/IO/latency/cost; до этого `BLOCKED: MEASUREMENT_MISSING`.
4. Не выполнять без отдельного owner approval сетевые нагрузочные, платные LLM, sudo/eBPF, production SQL или deployment-эксперименты.

**Верификация публикации:** `node scripts/build-catalog.mjs`, `node scripts/check.mjs`, `node --test scripts/check.test.mjs scripts/entity-model.test.mjs scripts/document-assessment.test.mjs`, `git diff --check` (фактические результаты указаны в отчёте об исполнении).
