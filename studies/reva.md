# REVA — Reusable Evidence View Aggregation

**Original paper:** https://arxiv.org/abs/2609.11209; [complete PDF](https://arxiv.org/pdf/2609.11209v1).
**Primary version:** arXiv v1; 11 pages. **SHA-256:** `a1779977061cc77485478e6567ec6d98c44852f5059a4cb0e77b6ba88244d601` (checked 2026-11-03; PDF binary not redistributed).
**Source type:** `ARXIV_ICDM_ACCEPTED_MANUSCRIPT`. **Evidence:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_INDEPENDENTLY_REPRODUCED`.
**Historical first watch:** [15 Sep 2026](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md); [non-normative operator dispositions](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md). For Random Attention the earlier source is the [chronological archive index](../archive/dsh/knowledge/research/README.md).
**Historical closure:** [scientific review](../portfolio/2026-09-03--2026-09-15/review.md); [research-to-project matrix](../portfolio/2026-09-03--2026-09-15/project-fit.md).
**Editorial value / disposition:** 7/10; `P2_ONLY_WHERE_ATTENTION_SIGNAL_EXISTS` (research only, no production authorization).

## Methodology and sample

Исторические query→document→generator attention traces агрегируются в document-keyed статистику важности на уровне читаемых слов; при следующем запросе из frozen offline score store составляется budget-specific plain-text evidence view. Четыре QA benchmarks NQ, TriviaQA, HotpotQA, 2Wiki, top-10 retrieval cache, strict held-out reuse с fallback для ранее неизвестных документов.

## Authors results (not local measurements)

Авторы сообщают +1,0…5,8 quality points и снижение request-time compression overhead в 5,3–15,6 раза против конкретных compressor baselines; materialization занимает менее 40 ms. Важная оговорка: online overhead не включает retrieval, сборку score store и generation; хранение 113 тыс. scored HotpotQA queries оценено около 1 GB.

## Limitations / transfer confounders

Нужны исторические attention traces **целевого генератора**, недоступные через многие closed APIs; исторический proxy по tool usage — уже другая гипотеза. Смена модели, корпуса или tokenizer нарушает совместимость score store. Стоимость offline подготовки и память нельзя считать нулевыми.

## Smallest discriminating experiment

50 repeat-document questions: prefix/head-N, BM25 rerank, summary, simple span provenance proxy; только при controlled attention signals добавить REVA. Считать held-out correctness, source-verified citations, online+indexing tokens, RAM and latency.

## Project-fit decision

Управляемые reusable evidence views при повторных запросах к документам/БД; это retrieval hypothesis, а не прямая реализация closed-API REVA.

**Gate:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE`. Owner gate and independent outcome oracle required before any code changes.
