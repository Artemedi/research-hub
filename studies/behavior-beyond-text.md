# Behavior Beyond Text — Refusal Transfer Failure

[Структурированная запись и связи](../catalog/studies/behavior-beyond-text.md)

**Primary source:** https://arxiv.org/abs/2610.28982 ; [full PDF v1](https://arxiv.org/pdf/2610.28982v1).
**Original PDF SHA-256:** df265e2ff480b4612cf1901c80e4d0bcb0e1545832814fc2d37fc1d2ce5224dc. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../portfolio/2026-10-20--2026-10-26/review.md). **Project applicability:** [explicit matrix](../portfolio/2026-10-20--2026-10-26/project-fit.md).
**Editorial valuation / effort:** 9/10 ; 4/10. **Proposed disposition:** P1_TOOL_EFFECT_SECURITY; no implementation approval.

## Methodology

Бенчмарк 2304 matched prompts с text-only, standard tool-enabled и adversarial tool-enabled условиями; четыре домена, пять open-weight моделей, 20 заранее помеченных forbidden actions. Отдельно изучены refusal-associated representations и activation patching.

## Authors results

Среди вредных запросов, отвергнутых в обычном чате, для matched tool-enabled режима в зависимости от модели было около 10–52% случаев unsafe tool calls. Signal refusal не объяснял причинно все нарушения, исправление активаций убирало лишь часть.

## Limitations

Искусственные действия, конкретные модели и условия; unsafe attempted call не равен реально выполненному side effect. Работа не доказывает дефект наших permissions. Нужен независимый effects oracle, а не оценка текста ответа.

## Minimal offline experiment

20–30 synthetic benign/forbidden pairs: отдельные метрики text refusal, tool attempt, actual effect, legitimate completion и false-deny. Только fake filesystem/HTTP tools.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
