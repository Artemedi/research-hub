# Agent Transfer Protocol (ATP) — Server-Mediated Communication

**Primary source:** https://arxiv.org/abs/2610.38398 ; [full PDF v1](https://arxiv.org/pdf/2610.38398v1).
**Original PDF SHA-256:** 072f3943a10d1dfa6fa93d5932d8da9b5533b4d11ece905ba343a2a09e4843d5. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../portfolio/2026-10-27--2026-11-02/review.md). **Project applicability:** [explicit matrix](../portfolio/2026-10-27--2026-11-02/project-fit.md).
**Editorial valuation / effort:** 7/10 ; 8/10. **Proposed disposition:** P2_CROSS_DOMAIN_ONLY; no implementation approval.

## Methodology

Кросс-организационные logical agent addresses и stable domain servers с durable receive queue; подписанный полный message envelope проверяется при получении и позднем чтении. Прототип проверял offline/restarted instance, delayed verification, message persistence и latency относительно direct HTTPS.

## Authors results

В travel coordination workflow offline/migration variants дали 5/5 успешных прогонов каждая. При keep-alive и in-memory filesystem на одном компьютере добавочная медианная latency двух domain servers около 2,7 мс относительно direct HTTPS. Это не WAN production SLA.

## Limitations

Синтетические domains и небольшое число сценариев; управление ключами, identity, revoke, queue retention, multi-host failure и cost/IO не проверены промышленным образом. Не путать этот академический prototype с отдельными draft ATP документов IETF; не внедрять transport без реального межорганизационного требования.

## Minimal offline experiment

При доказанном cross-org scenario: two disposable domain queues vs signed direct webhook, offline receiver restart, immutable envelope, revocation, latency/IO, duplicate/late delivery. Если межорганизационной потребности нет — NO_IMPLEMENTATION_NOW.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
