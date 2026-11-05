# Vercel Agent Desktop — BK-065

- First-party [vercel-labs/agent-desktop@b43ac4f6e892ef608f8851428613c4009f0e84c7](https://github.com/vercel-labs/agent-desktop/tree/b43ac4f6e892ef608f8851428613c4009f0e84c7), workspace 1.2.0, Apache-2.0, проверено 05.11.2026.
- **Рассмотрен и отложен**. [Промежуточная проверка refs/permissions и GUI gate](../reports/2026-11-05-bk065-agent-desktop-source-gate.md), [45 профилей](../reports/2026-11-05-bk065-project-triage.json).
- `PARTIAL_SOURCE_REVIEW / GUI_NOT_RUN / BLOCKED_ENV`: полного source review, Rust tests/lint/build и изолированного Wayland/Windows GUI-теста нет. Исторический статус **ожидает проверки** сохранён.
- По коду: snapshot-qualified refs, strict identity matching, headless interaction policy и OS permission preflight. Их end-to-end действие, privacy и race resistance не доказаны локальным запуском.
- Кандидаты: `Harness`, `HermesAgent`, `psqlqa` — `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`, без проверенного текущего integration seam. Старые предварительные backlinks не повышены; новые не добавлялись. Не `LAB_VERIFIED` и не `PRODUCTION_APPROVED`.
