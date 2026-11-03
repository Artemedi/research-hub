# Silent Cue Loss — Formatting in Document Ingestion

**Primary source:** https://arxiv.org/abs/2610.30026 ; [full PDF v1](https://arxiv.org/pdf/2610.30026v1).
**Original PDF SHA-256:** a1634fad8737ed6ff5524ff7f943ba48ee962cf0633e40b6cf356fb5608cf06c. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../reports/2026-11-03-full-text-review-2026-10-20-to-26.md). **Project applicability:** [explicit matrix](../reports/2026-11-03-project-mapping-2026-10-20-to-26.md).
**Editorial valuation / effort:** 8/10 ; 5/10. **Proposed disposition:** P2_CONDITIONAL_INGESTION; no implementation approval.

## Methodology

76 настоящих policy DOCX с gold marked requirements из OOXML и deterministic matcher, шесть answering models и шесть representations; paired document analysis, confirmatory 79-document followup для typed/untyped cue labels.

## Authors results

Micro-F1 0,690 при сохранённых стилевых подсказках против 0,150 в docling и 0,075 в plain text для данной постановки. Highlight и цвет наиболее важны. Representation обходится примерно вдвое дороже plain text в токенах.

## Limitations

Смысловая стилизация присутствует не во всех документах; PDF без OCR должен иметь извлекаемый текст; не все модели реагируют на cues; ground truth генерируется программно с rendered spot checks, а не полноценной независимой human annotation. Нужен доказанный ingestion seam.

## Minimal offline experiment

30 synthetic/style-annotated DOCX/PDF, oracle по выделенным инструкциям; plain text vs style annotations vs typed cue markers. Precision, recall, F1, latency/tokens, false positives.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
