# Научные первоисточники — закрытие пробелов доказательного покрытия

**Дата:** 2026-11-05. **Research-hub baseline:** `822835c8a5a5ade05d9a7a17d2d78b41a99716fe`. **Project-registry baseline:** `838b86a28fcaa3440eeddbe147b6188e0d177963` (45 `PROJECT.md`). Сверка исходников — read-only. Это продолжение [первой партии аудита](evidence-coverage.md); она фиксировала состояние до данной партии.

## Метод и результат

Для двенадцати ранее не подтверждённых полнотекстовой меткой научных работ получены **полные официальные версии** — 11 HTML-статей и 9-страничный PDF KVSET. Для arXiv прочитаны §§ с методикой, setup, таблицами результатов, ограничениями и приложениями; дата и версия сверены с `/abs` и submission history. Для Nature прочитаны доступная полная статья, Methods, Discussion и Results (дополнительный Supplementary PDF отдельно **не** анализировался). У каждого нового обзора указаны canonical URL, версия, SHA-256 полученного представления, авторские выводы, ограничения, прежний статус и матрица предметного project-fit.

| Источник | Подтверждённая редакция | Новый обзор | Принципиальный предел |
| --- | --- | --- | --- |
| Agent Error Dataset | arXiv v2 | [полный текст](../../reviews/agent-error-dataset/2026-11-05-full-text.md) | frozen-cohort, grader contamination, independent repair not run |
| Covert Assistance | arXiv v1 | [полный текст](../../reviews/covert-assistance/2026-11-05-full-text.md) | synthetic security scenarios; no production privilege test |
| DRAG | arXiv v1 | [полный текст](../../reviews/drag/2026-11-05-full-text.md) | RAG-QA не равно generic agent workflow |
| LIMBO / Exactly-Once | arXiv v1 | [полный текст](../../reviews/exactly-once-limbo/2026-11-05-full-text.md) | mock service effect ledger, not real Telegram |
| KVSET | arXiv PDF v1 | [полный текст](../../reviews/kvset/2026-11-05-full-text.md) | page-granular LRU/full-attention only |
| KVTether | arXiv v1 | [полный текст](../../reviews/kvtether/2026-11-05-full-text.md) | controlled serving backend absent; `NO_CURRENT_TARGET` |
| MaadBench | arXiv v1 | [полный текст](../../reviews/maadbench/2026-11-05-full-text.md) | benchmark traces ≠ реальный мониторинг |
| Paper2Agent | Nature DOI version of record (16.09.2026) | [полный текст](../../reviews/paper2agent/2026-11-05-full-text.md) | supplementary unexamined; reference code not run |
| REALM | arXiv v1 | [полный текст](../../reviews/realm/2026-11-05-full-text.md) | derived memory, poisoned feedback risk |
| ReCAP | arXiv v1 | [полный текст](../../reviews/recap/2026-11-05-full-text.md) | attention/proxy and modeled compaction latency |
| StateComp | arXiv v1 | [полный текст](../../reviews/statecomp/2026-11-05-full-text.md) | hidden-state predictor; summary is lossy |
| VeriHarness | arXiv v1 | [полный текст](../../reviews/veriharness/2026-11-05-full-text.md) | 10-rollout cost; independent oracle not run |

Ранее в этой же серии отдельно полнотекстово проверены [RRSI](../../reviews/rrsi/2026-11-05-full-text.md), [Harness²](../../reviews/harness2/2026-11-05-full-text.md), [CERA-MoA](../../reviews/cera-moa/2026-11-05-full-text.md).

**Документальное покрытие научных статей после данной партии: 51/51 с `FULL_TEXT_REVIEWED` хотя бы в одной Review.** Для 15 работ это новый акт чтения от 05.11; остальные 36 имеют документированные ранее обзоры, которые **не перечитывались заново** в рамках этой серии. Наличие `FULL_TEXT_REVIEWED` не означает `LAB_VERIFIED` или подтверждённую пользу в проекте. Все авторские цифры помечены `AUTHOR_REPORTED`. Существующие bounded engineering/code experiments и historical DSH records не удалены.

## Версии и неизменность истории

Каждая новая научная проверка получила **отдельную** запись Version. У исторических Version с `ref: null` сохранены original URL и `unknown_reason`; публикация точного v1/v2 сейчас не превращает незадокументированное знание прошлого в известный факт. Нынешний pinned review использует собственный Version ID и SHA-256 в тексте. Для Nature версия — DOI version of record плюс snapshot HTML; для KVSET — официальный PDF v1.

## Портфель и отложенные материалы

Все 45 существующих `PROJECT.md` рассмотрены на уровне реестра. Новые positive fit-кандидаты или checked `repo@SHA/path:line` в этом проходе не создавались. Для каждого source сохранён уже документированный shortlist (не больше трёх проектов) или `NO_CURRENT_TARGET` с объяснением; изменять PROJECT.md для повтора source evidence без нового подтверждённого fit не требуется. Внешний проект коллеги остаётся `AUTHOR_STATED / NEEDS_SOURCE_CODE`.

**Дальнейшие gate, а не ошибки каталога:** `FULL_TEXT_UNAVAILABLE` для оригинального видео Unreal Agent, четыре ожидающих Telegram cases, ограниченные engineering reviews, неизмеренная project benefit, отсутствие acceptance для новых costly/sudo/eBPF/production/LLM A/B. Источники без подтверждаемой редакции помечаются `UNKNOWN`, не выдумываются.

## Контроль публикации

После регистрации source Versions/Reviews и навигации выполнить `node scripts/build-catalog.mjs`, `node scripts/check.mjs`, `node --test scripts/check.test.mjs scripts/entity-model.test.mjs scripts/document-assessment.test.mjs`, `git diff --check` и проверить CI на опубликованном SHA. Новых исполняемых экспериментов, агентных запусков и production-изменений не было.
