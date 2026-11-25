# PostgreSQL 2026-11-12 minor maintenance releases

[Структурированная запись и связи](../catalog/studies/postgresql-2026-11-minor-releases.md)

- **Версии:** PostgreSQL 18.7 / 17.12 / 16.16 / 15.20 / 14.25; дата 2026-11-12.
- **Тип:** официальный engineering changelog, не peer-reviewed paper.
- **FULL_TEXT_VERIFIED:** https://www.postgresql.org/docs/release/18.7/ ; https://www.postgresql.org/docs/release/15.20/
- **Суть:** security, planner correctness, index corruption, backup/replication fixes; требования reindex/backup-base по затронутым случаям.
- **Результаты:** исправления подтверждены release notes разработчиков, независимых AKUZ benchmarks нет.
- **Ограничения:** не все пункты PG18 относятся к PG15; deployment versions и affected index inventory неизвестны.
- **Оценка:** ценность 9/10, сложность 6/10, NEEDS_EVIDENCE.
- **Применимость:** [матрица и минимальный A/B](../reports/2026-11-16-portfolio-research.md).
- **Лицензия:** PostgreSQL License; применение штатных обновлений без заимствования чужого кода.
