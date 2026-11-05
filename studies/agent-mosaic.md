# Agent Mosaic — Composite Disclosure Risk

**Primary source:** https://arxiv.org/abs/2610.30418 ; [full PDF v1](https://arxiv.org/pdf/2610.30418v1).
**Original PDF SHA-256:** 3effb1c2251223ecbdd7e3f201681fdd33f07b99ddf314dabdd1577ce7822061. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../portfolio/2026-10-20--2026-10-26/review.md). **Project applicability:** [explicit matrix](../portfolio/2026-10-20--2026-10-26/project-fit.md).
**Editorial valuation / effort:** 8/10 ; 6/10. **Proposed disposition:** P1_SYNTHETIC_DISCLOSURE; no implementation approval.

## Methodology

30 вымышленных случаев из разных чувствительных областей, в которых каждый документ доступен отдельно, а их композиция даёт запрещённый вывод. 10800 simulated final answers (три модели), 1440 live-harness answers; варьируются намерения пользователя, classification headers, aggregation safeguards и distractors.

## Authors results

В симуляции pooled mosaic disclosure 52,68% для равной смеси трёх генераторов. Две меры защиты снижали pooled disclosure в конкретных factorial cells приблизительно с 68,63% до 32,37%, но риск оставался. Отказ текстом может сосуществовать с раскрытием составного факта.

## Limitations

Только 30 synthetic examples, одна adversarial suffix family и ограниченные distractors; правила секретности искусственные, результаты не измеряют утечку наших частных данных. Запрещено публиковать реальную внутреннюю информацию ради бенчмарка.

## Minimal offline experiment

30 synthetic двухдокументных pairs, заранее запрещённая composite relation, сравнить per-document ACL-only и outbound composite filter. False disclosures, false refusals, cost.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
