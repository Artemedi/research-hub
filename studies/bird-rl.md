# BIRD-RL — Stateful SQL Agent Evaluation

**Primary source:** https://arxiv.org/abs/2610.29426 ; [full PDF v1](https://arxiv.org/pdf/2610.29426v1).
**Original PDF SHA-256:** e8c9232482b6cce191f5bca6b7a92b945b93c44f8fa5871e95af34706c0f25dc. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../portfolio/2026-10-20--2026-10-26/review.md). **Project applicability:** [explicit matrix](../portfolio/2026-10-20--2026-10-26/project-fit.md).
**Editorial valuation / effort:** 9/10 ; 7/10. **Proposed disposition:** P1_DB_STATE_ISOLATION; no implementation approval.

## Methodology

Trajectory-scoped persistent execution environment for SQL debugging/reinforcement learning: reuse DB replicas while preventing cross-trajectory state contamination. Четырёхфазное RL curriculum и BIRD-CRITIC-SQLite evaluation; измерены раздельно accuracy и spatial efficiency.

## Authors results

Авторы сообщают 44,4% и 48,0% success для 7B и 14B BIRD-Talon против 26,2%/33,8% base models. Отдельно заявлено 12,8× улучшение spatial efficiency тестовой инфраструктуры. Результат относится к SQLite, а не к PostgreSQL или MSSQL.

## Limitations

Различие движков, WAL/MVCC/locking/recovery и stateful admin operations; нет evidence безопасного replay на production DB. Разделять скорость clone, IO cost, snapshot consistency и сам успех SQL agent.

## Minimal offline experiment

Одноразовая PostgreSQL test DB: per-trajectory container, clone/base snapshot и допустимый rollback baseline. Проверить final DB state, contamination, setup wall-time, WAL bytes, IOPS, RAM, storage; никакого live production access.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
