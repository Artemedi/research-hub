# Where You Inject Matters — Trust Region Effect

[Структурированная запись и связи](../catalog/studies/trust-region-injection.md)

**Primary source:** https://arxiv.org/abs/2610.38867 ; [full PDF v1](https://arxiv.org/pdf/2610.38867v1).
**Original PDF SHA-256:** 82473243e510b0a7fa305a92c73c619e15d91b276d224e00ea39413d2212d4d5. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../portfolio/2026-10-27--2026-11-02/review.md). **Project applicability:** [explicit matrix](../portfolio/2026-10-27--2026-11-02/project-fit.md).
**Editorial valuation / effort:** 9/10 ; 5/10. **Proposed disposition:** P1_DEFENSIVE_PLACEMENT_CORPUS; no implementation approval.

## Methodology

Три sandbox agent testbeds для tool, coding, daily workflow; 36 разных untrusted surfaces и 24 категорий риска. Содержание synthetic injection фиксируется при смене размещения. Исследуются поведение агента, источник текста и позиция внутри документа; механизм поиска payload/placement не нужен для defensive adoption.

## Authors results

Авторы сообщают, что для GPT-5.4 coding tasks исполнение той же вредной инструкции из README/TODO приблизительно в 2,6 раза чаще, чем из code/data files. Успех зависит от поверхности; большинство неуспехов обусловлено игнорированием, а не явным защитным отказом.

## Limitations

Измерения на выбранных моделях, attacker objectives и containers; их результаты не доказывают реальную компрометацию AGENTS.md, source code или MCP output в наших текущих проектах. Placement-based heuristic не заменяет authority checks.

## Minimal offline experiment

20–30 synthetic requests с одинаковым безвредным canary instruction в README/TODO/source/tool output; independent forbidden-effect oracle, read exposure, false accepts, legitimate utility; никакого реального вредного payload.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
