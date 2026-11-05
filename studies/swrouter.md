# SWRouter — multi-turn context-aware model routing

[Структурированная запись и связи](../catalog/studies/swrouter.md)

**Original paper:** https://arxiv.org/abs/2609.11414; [complete PDF](https://arxiv.org/pdf/2609.11414v1).
**Primary version:** arXiv v1; 26 pages. **SHA-256:** `e24cbce0ffdb95dd18a6e8620439e5c29d3eb5c1e2aa7c985f9cec18668bb825` (checked 2026-11-03; PDF binary not redistributed).
**Source type:** `ARXIV_PREPRINT`. **Evidence:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_INDEPENDENTLY_REPRODUCED`.
**Historical first watch:** [15 Sep 2026](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md); [non-normative operator dispositions](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md). For Random Attention the earlier source is the [chronological archive index](../archive/dsh/knowledge/research/README.md).
**Historical closure:** [scientific review](../portfolio/2026-09-03--2026-09-15/review.md); [research-to-project matrix](../portfolio/2026-09-03--2026-09-15/project-fit.md).
**Editorial value / disposition:** 8/10; `P2_SHADOW_ROUTER_TEST` (research only, no production authorization).

## Methodology and sample

Similarity-Contractive Window segmentation сохраняет связанные фрагменты диалога, contrastive route training использует model-level и sample-level objectives. Оценка декомпозирует end-to-end evaluation accuracy, mean construction accuracy и router performance. Используются MT-Bench/ShareGPT и настройки multi-turn model pools.

## Authors results (not local measurements)

Авторы сообщают улучшение на 16,26% против лучшей индивидуальной модели и на 8,22% относительно Conv-ID Context (в авторской формулировке). Сильная чувствительность similarity threshold: в отдельном опыте 40,89% accuracy при tau=0,91, но 25,6% при 0,85 и 18,3% при 0,95.

## Limitations / transfer confounders

Порог, dataset, модельный pool и cost функций не универсальны; LLM-based scoring и контекстная конструкция могут переоценивать маршрут. Переход модели может разрушать cached prompt prefix и менять trust eligibility. Авторы не доказали экономию наших multi-agent или SQL траекторий.

## Smallest discriminating experiment

На 100 frozen multi-turn tasks compare always strong, simple last-turn routing, BM25 history windows, similarity windows; oracle actual task success, allowed provider set, cost including prompt caching, p95 and repair turns.

## Project-fit decision

Распределение контекстных окон и выбор модели в существующих маршрутизаторах и gateway; Model Trust and current model eligibility не изменяются.

**Gate:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE`. Owner gate and independent outcome oracle required before any code changes.
