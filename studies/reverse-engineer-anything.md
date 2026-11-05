# REA — Reverse Engineer Anything (BK-062)

- First-party [morluto/rea@970969cb53f788976e64eae387076fcea104b603](https://github.com/morluto/rea/tree/970969cb53f788976e64eae387076fcea104b603), package 6.8.0, проверено 05.11.2026; MIT плюс отдельные third-party terms.
- **Рассмотрен и отложен**. [Промежуточная проверка static/runtime границы](../reports/2026-11-05-bk062-rea-source-gate.md), [45 профилей](../reports/2026-11-05-bk062-project-triage.json).
- Исходник доступен; полный source review, parser/provider suite, tests/lint/build и реальные targets не проверены. `PARTIAL_SOURCE_REVIEW / NOT_RUN`, исторический статус **ожидает проверки**. Не `FULL_TEXT_UNAVAILABLE`, не `LAB_VERIFIED`.
- Установлен отдельный static PE/CLI contract; bridges не являются OS sandbox. Model egress, malformed input robustness, весь managed pipeline и target fit требуют дополнительной проверки.
- Возможные проекты: `MyPartyIsGrinding`, `WarOfGenesisIdleLoot`, `game-localization-guide` — пока `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`; проектных эффектов не измеряли. Новые backlinks не добавлялись.
