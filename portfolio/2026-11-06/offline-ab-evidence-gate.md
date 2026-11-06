# Offline A/B — достаточность доказательств и multi-hop в DRAG-inspired поиске

**Дата:** 2026-11-06. **Экспериментальный статус:** `SYNTHETIC_HOLDOUT_PASS / ADVERSARIAL_OOD_FAIL / INTEGRATION_NOT_APPROVED`. Продолжает [первый DRAG retrieval A/B](offline-ab-drag.md). **Полный протокол:** [DRAG evidence gate](../../reviews/drag/2026-11-06-evidence-gate-ab.md). Интеграционный приоритет остаётся только у исправления CVE-2026-82533 в DSH; эта работа не разрешает deployment.

**Протокол:** отдельная калибровка на 3 seeds, затем 5 неиспользованных holdout seeds: 96 синтетических документов, 84 запроса/seed, всего **420 запросов** (180 с ответом / 240 отрицательных). Одна и та же исходная BM25, одинаковый лимит 3 цитат, независимый от результата retrieval авторский manifest ground truth. Сравнены BM25, structural gate, follow-only, combined gate+follow и заведомо ошибочный runbook-link control. Threshold 1.0 зафиксирован на calibration до holdout.

| Основной результат | BM25 baseline | Gate+Follow |
| --- | ---: | ---: |
| Recall@3 | 75% | 100% |
| Полный правильный комплект evidence | 66,7% | 100% |
| Отказ от ответа среди 240 отрицательных | 0% | 100% |
| Citation precision на исходном структурированном holdout | 14,3% | 100% |
| Mean CPU / 84 запроса | 45,56 мс | 50,43 мс |

**Обязательный adversarial stress на 5 новых seeds:** при смене `kind=observation` на `kind:observation` BM25 продолжал видеть те же тексты, но guard перестал отвечать на **все положительные запросы**. При добавлении четырёх поддельных документов на инцидент точность выданных guard цитат стала **0%**. Это post-hoc стресс на намеренно жёстких искусственных мутациях, а не оценка частоты рисков в реальной базе документов.

**Воспроизводимость:** [основной исходник](../../experiments/2026-11-06-drag-abstention-multihop-ab.py), [основные JSON-данные](../../data/results/drag/2026-11-06-abstention-multihop-ab.json), [OOD-скрипт](../../experiments/2026-11-06-drag-evidence-ood-stress.py), [OOD JSON](../../data/results/drag/2026-11-06-evidence-ood-stress.json), [7 регрессионных тестов](../../experiments/tests/test_drag_evidence_gate.py). Первичный невалидный запуск с дефектом парсера ID исключён; новые holdout seeds назначены после исправления.

**Накладные расходы:** CPU/wall/p50/p95, Python allocations, process RSS highwater, `/proc/self/io` собраны. VRAM, стоимость LLM-токенов: `N/A`; API spend = 0 USD без обращений к модели. Retrieval на данных в памяти не равен производственному IO и latency.

**Следующее исследование:** проверить дополнительный guard на доверенность источника и поддержку разных форматов на ещё новом независимом корпусе; только затем переносить на 30–50 обезличенных DBA-запросов с внешней разметкой. Никакие исходники целевых проектов и production не изменены.
