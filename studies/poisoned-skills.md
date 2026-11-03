# Poisoned Skills — Agent Markdown Config Injection

**Primary source:** https://arxiv.org/abs/2610.37738 ; [full PDF v1](https://arxiv.org/pdf/2610.37738v1).
**Original PDF SHA-256:** c4c01de2f64be7228fee6864c6143fc36e12a68bb90ab3ad2b490bf79ac981f0. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../reports/2026-11-03-full-text-review-2026-10-27-to-11-02.md). **Project applicability:** [explicit matrix](../reports/2026-11-03-project-mapping-2026-10-27-to-11-02.md).
**Editorial valuation / effort:** 8/10 ; 4/10. **Proposed disposition:** P1_RULE_FILE_PROVENANCE; no implementation approval.

## Methodology

Один LangChain QA agent собирает system prompt из загружаемого Markdown skill/config. Seven open-weight models, 270 forbidden questions по девяти категориям; сравнение benign vs tampered Markdown, а также обфускация zero-width и phonetic.

## Authors results

Средний ASR текстовых запрещённых ответов ~0,5% при benign prompt и 45% при tampered Markdown, до 68,9% для отдельных моделей; phonetic obfuscation снижала средний ASR до 30%. Это текстовый QA/JB outcome, не доказанный tool/privilege escalation.

## Limitations

Один framework и задачник, искусственная подмена trust artifact; подпись/hashing проверяет происхождение/целостность, но не содержательную безопасность. Работа не проверяет наших runtime guards и production mitigations.

## Minimal offline experiment

20 benign fixture prompts/skills без вредного payload; version-controlled trusted allowlist, diff/review provenance checks, compare permitted behavior и unauthorized policy drift. No third-party package install.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
