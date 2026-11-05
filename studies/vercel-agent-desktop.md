# Vercel Agent Desktop

[Структурированная запись и связи](../catalog/studies/vercel-agent-desktop.md)

- Current pinned source: b43ac4f6e892ef608f8851428613c4009f0e84c7; проверено 05.11.2026.
- **Рассмотрен и отложен** для внедрения. Исторический статус **проверен экспериментально**, только для описанных bounded fixtures.
- [Новый отчёт](../reviews/vercel-agent-desktop/2026-11-05-wayland.md), [все 45 решений](../data/project-fit/vercel-agent-desktop/2026-11-05.json). Предыдущий source-gate отчёт сохранён и связан из нового обзора.
- Original Linux CLI на private Wayland toy UI: 12/12 cases; core1683 PASS, fmt/clippy core/build PASS. Linux whole-suite retained failures (2173/1/233 ignored); failing source scanner отдельно PASS. Не all-platform security или project-benefit verification.
- Target benefit, полный repository security audit и production approval отсутствуют.
