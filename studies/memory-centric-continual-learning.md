# Memory-Centric Continual Learning (MCCL)

**Primary source:** https://arxiv.org/abs/2610.29357 ; [full PDF v1](https://arxiv.org/pdf/2610.29357v1).
**Original PDF SHA-256:** f5d32f7b605cc18e033b1820e99aa23ac715671a7bf10b1608abfd5324bce268. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../reports/2026-11-03-full-text-review-2026-10-20-to-26.md). **Project applicability:** [explicit matrix](../reports/2026-11-03-project-mapping-2026-10-20-to-26.md).
**Editorial valuation / effort:** 8/10 ; 3/10. **Proposed disposition:** P1_EVALUATION_METHOD_ONLY; no implementation approval.

## Methodology

Концептуальная taxonomy по memory substrate/asset/policy, inner loop изменения памяти и outer loop изменения management policy, протокол измерения retention under interference, adaptation to changed facts и transfer. Ресурсные scaling hypotheses; опубликованные численные примеры других работ — это цитируемая литература, не собственный новый бенчмарк MCCL.

## Authors results

Методологический тезис: retrieval accuracy и recall сами по себе не доказывают улучшение будущих действий. Авторская работа предлагает постановку тестов с outcome-based оценкой, не сообщает measured production gain для DSH.

## Limitations

Не доказано превосходство конкретной памяти, оптимальный budget или универсальность scaling curves; нужны независимые temporal splits и зафиксированная среда, иначе contamination легко имитирует learning.

## Minimal offline experiment

Три temporal held-out cohorts: retention с interference, changed facts, transfer. Baselines no-memory / BM25 / existing memory при равном model/tools бюджете; task success, stale facts, citations, storage IO.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
