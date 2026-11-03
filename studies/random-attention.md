# Random Attention — KV eviction for reasoning

**Original paper:** https://arxiv.org/abs/2609.03430; [complete PDF](https://arxiv.org/pdf/2609.03430v1).
**Primary version:** arXiv v1; 22 pages. **SHA-256:** `7126afd49f82a499e70bb201d32d3c11c8f75012323213c444982736926be14b` (checked 2026-11-03; PDF binary not redistributed).
**Source type:** `ARXIV_PREPRINT`. **Evidence:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_INDEPENDENTLY_REPRODUCED`.
**Historical first watch:** [15 Sep 2026](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md); [non-normative operator dispositions](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md). For Random Attention the earlier source is the [chronological archive index](../archive/dsh/knowledge/research/README.md).
**Historical closure:** [scientific review](../reports/2026-11-03-historical-gap-closure-2026-09-03-to-15.md); [research-to-project matrix](../reports/2026-11-03-project-mapping-september-gaps.md).
**Editorial value / disposition:** 7/10; `DEFER_NO_VERIFIED_KV_SERVING_TARGET` (research only, no production authorization).

## Methodology and sample

Нулевой baseline для KV eviction: полностью сохраняет prompt KV, а среди reasoning tokens независимо по attention heads выбирает случайные позиции вместо дорогих content-based scores. Четыре модели (Qwen3-4B/14B/32B, Phi-4-reasoning), шесть reasoning benchmarks (math/GPQA/code), multi-seed repetitions и vLLM serving comparison.

## Authors results (not local measurements)

При сопоставимой точности reasoning tasks authors report vLLM throughput на 32–43% выше TriAttention при matched budget, и 1,6–2,7× относительно uncompressed full attention в выбранных settings. Сравнение уже включает условие сохранения prompt: случайное удаление prompt не является проверенным методом.

## Limitations / transfer confounders

Требуется доступ к physical KV cache и интеграция в vLLM/другой controlled serving engine; архитектура обычных cloud API маршрутизаторов этого не предоставляет. Некоторые портированные baselines дают performance gaps из-за нефьюзенных scorers; точность при иных workloads и context budgets отдельно не проверена.

## Smallest discriminating experiment

Только если появится source-verified self-hosted vLLM serving stack: compare prompt-preserving random vs recency vs current KV policy на фиксированных model/seeds и задачах; accuracy with CI, throughput, memory, TTFT и p95. До подтверждения backend = NO_CURRENT_TARGET.

## Project-fit decision

Ни один PROJECT.md не подтверждает наличие управляемого physical KV eviction backend. bitvec-dsh занимается смежной латентной памятью, но не становится ложной целью.

**Gate:** `NO_CURRENT_TARGET / DEFER_MODEL_BACKEND_ONLY`. Owner gate and independent outcome oracle required before any code changes.
