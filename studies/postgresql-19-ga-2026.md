# PostgreSQL 19 GA — 2026-11-19

**Тип:** официальный engineering release; **FULL_TEXT_VERIFIED**: https://www.postgresql.org/docs/19/release-19.html

**Дата новой версии:** 2026-11-19. **Предыдущее рассмотрение:** [PostgreSQL minor 2026-11-12](postgresql-2026-11-minor-releases.md) — отдельная maintenance ветка, не дубликат GA.

Новые REPACK CONCURRENTLY, pg_plan_advice, autovacuum scoring/parallel index vacuum, pg_stat_recovery/pg_stat_autovacuum_scores, WAIT LSN, ON CONFLICT DO SELECT, optimizer transformations. Полный метод/результаты и migration caveats — в официальном changelog. Независимых AKUZ benchmarks нет; нельзя переносить performance claims на production. Риски major upgrade, compatibility, WAL/IO, REINDEX и replication.

**Применимость и минимальный A/B:** [отчёт и матрица 2026-11-23](../reports/2026-11-23-portfolio-research.md). Wiki_PG — PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE; developer-safe-dotnet-core — AUTHOR_STATED / NEEDS_SOURCE_CODE. Не является разрешением на внедрение.
