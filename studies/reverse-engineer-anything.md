# REA — Reverse Engineer Anything

- Current pinned source: 92f332652d352e60b550567adf2399d83d8ebe78; проверено 05.11.2026.
- **Добавлен в карточки** как ограниченный static-analysis кандидат. Исторический статус **проверен экспериментально**, только для описанных bounded fixtures.
- [Новый отчёт](../reviews/reverse-engineer-anything/2026-11-05-pe-layout.md), [все 45 решений](../data/project-fit/reverse-engineer-anything/2026-11-05.json). Предыдущий source-gate отчёт сохранён и связан из нового обзора.
- 48/48 authored PE32/PE32+ layout cases на original reader и обнаруженный overlap-guard mutant. Только header/layout boundary; весь metadata/CIL/CLI/MCP pipeline, package tests/lint/build и project benefit не проверены.
- Target benefit, полный repository security audit и production approval отсутствуют.
