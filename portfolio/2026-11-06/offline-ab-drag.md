# Offline A/B: DRAG-inspired retrieval — 6 ноября 2026

**Предыдущие опыты:** [LIMBO / RRSI](offline-ab-followup.md). **Основной протокол:** [DRAG](../../reviews/drag/2026-11-06-retrieval-ab.md). [Код](../../experiments/2026-11-06-drag-retrieval-depth-ab.py) · [Машинные результаты](../../data/results/drag/2026-11-06-retrieval-depth-ab.json). Интеграционный приоритет по-прежнему относится только к устранению CVE-2026-82533 в DSH.

**Метод:** 5 seeds × 60 синтетических DBA-запросов, корпус по 84 документа, фиксированный K=3, независимая явно заданная разметка gold, негативные no-match/distractor/multi-hop, random route с тем же количеством deep decisions, пересчёт каждого из 1 200 retrieval outputs во втором прогоне. **Не оригинальный DRAG_QPP или DRAG_SFT**, без моделей, root или изменений production.

| Ветка | Mean Recall@3 | Полный evidence на положительных | Mean wall time / 60 запросов | No-match false citations |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 47,0% | 33,75% | 9,22 мс | 12/12 |
| Random matched-deep | 57,0% | 46,25% | 22,94 мс | 12/12 |
| Adaptive | **63,3%** | 54,17% | 26,01 мс | 12/12 |
| Always deep | **63,3%** | 54,17% | 31,55 мс | 12/12 |

**Негативный вывод:** adaptive проигрывает простому BM25 по multi-hop recall (50% против примерно 58,3%) и ни разу не возвращает полный двухдокументный ответ. No-match false citations **60/60 по пяти seeds**. По итогам research status = `SYNTHETIC_AB_OBSERVED / INTEGRATION_NOT_APPROVED`.

Измерены CPU, Python allocations/RSS (без разделения resident memory по arm), процессы чтения/записи IO и p50/p95. VRAM и LLM tokens = `N/A`, API spend = 0 USD. Проверены воспроизводимость, негативная мутация oracle, отсутствие gold в поисковом коде. Нельзя приписывать эффект продуктивным DBA pipeline или авторским DRAG benchmark.

**Следующий этап:** новый заранее зафиксированный, непересекающийся с этим корпусом holdout, проверка `abstain` для no-match и обязательности *всех* документов для multi-hop, далее 30–50 независимых обезличенных DBA запросов с реальным provenance. Ни один из исследовательских экспериментов не повышен до внедрения.
