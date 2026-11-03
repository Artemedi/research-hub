# Your Policy Is Secretly a Harness — Decision Geometry

**Primary source:** https://arxiv.org/abs/2610.37255 ; [full PDF v2](https://arxiv.org/pdf/2610.37255v2).
**Original PDF SHA-256:** d678315eba5c30fd26966f6a33ea635b2889391b0d8eacc718f085063cea5319. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../reports/2026-11-03-full-text-review-2026-10-27-to-11-02.md). **Project applicability:** [explicit matrix](../reports/2026-11-03-project-mapping-2026-10-27-to-11-02.md).
**Editorial valuation / effort:** 10/10 ; 4/10. **Proposed disposition:** P1_INTERFACE_REGRESSION_AB; no implementation approval.

## Methodology

Разделение потенциального ceiling интерфейса agent harness и policy mismatch при KL-regularized control. MiniWoB++ эксперимент меняет порядок observation fields/representation при сохранении семантически допустимых действий. В Terminal-Bench Lite оптимальную policy приближают более сильным teacher model.

## Authors results

Для обученной Qwen3.5-2B одна перестановка полей опускала task success с 85,0% до 19,2% в контролируемой среде. Это специфический benchmark, не ожидаемый процент регрессии DSH; fixed-model comparison может недооценить потенциально лучший, но непривычный harness.

## Limitations

Идеальный ceiling обычно неизвестен, teacher proxy смещён; эффект зависит от обучающего harness, модели, способов сериализации и исходной policy. На практике нужен воспроизводимый A/B для любого prompt/tool schema изменения, но не новая теоретическая RL-рамка.

## Minimal offline experiment

100 fixed model/tool tasks: неизменная LLM и tools, переставлять schema order, observation fields, prompt sections; repeated runs, task success, tool-choice drift, cached tokens, latency/IO.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
