# GeoAgent — Contract-Constrained Agents

**Primary source:** https://arxiv.org/abs/2610.31096 ; [full PDF v2](https://arxiv.org/pdf/2610.31096v2).
**Original PDF SHA-256:** f40b351366e3edea41252e1808ee75d823d170b0816f7767ca2c3f300df0aa94. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../reports/2026-11-03-full-text-review-2026-10-20-to-26.md). **Project applicability:** [explicit matrix](../reports/2026-11-03-project-mapping-2026-10-20-to-26.md).
**Editorial valuation / effort:** 8/10 ; 5/10. **Proposed disposition:** P1_ARTIFACT_CONTRACTS; no implementation approval.

## Methodology

Предметный pipeline обработки сейсмики Madagascar: около 1965 CLI-инструментов, индекс 1937 операторов и 54 agent wrappers (51 декларативно сгенерированный). Девять этапов принудительно отслеживают named artifacts, input resolution, parameters и output validation. Детерминированный geometry checker сверяет восемь инвариантов SPS/RPS/XPS/SEG-Y. Контейнерное выполнение изолировано на уровне task/session.

## Authors results

Один 2-D land dataset завершил все девять стадий примерно за 6–11 минут с проверенным артефактом каждого шага. Retrieval сокращал представление tool descriptions приблизительно с 12 тысяч до 2 тысяч токенов за ход. Это не сравнительный end-to-end benchmark независимых систем.

## Limitations

Демонстрация на одном типе данных; domain-specific contracts, отсутствует полноценная контрольная группа и статистика переноса на coding/SQL, поэтому нет утверждения о выигрыше DSH. Контракт workflow имеет собственную стоимость и может сужать допустимые сценарии.

## Minimal offline experiment

30–50 disposable шаговых задач: prompt-only против schema-only против named-artifact contract. Проверить фактический input и checksum final artifact независимым oracle, ошибочные transitions, tokens, latency, cost.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
