# JetStream — verified SQL query accelerators with incremental maintenance

[Структурированная запись и связи](../catalog/studies/jetstream.md)

**Тип:** научная работа и авторская реализация. **Источник:** [arXiv 2610.20527v3](https://arxiv.org/pdf/2610.20527v3), пересмотр 04.11.2026; [закреплённый авторский artifact 5331cd8](https://github.com/akhileshvb/accelerator-codegen/tree/5331cd8bfa34ff5285b24a66b79eb8b53050fcd5). Полный PDF (14 страниц) доступен, SHA-256 d3355b67b62fb12358426517107239c47239f406fcdbff3d1af0592581def42d.

**Маршрут:** Добавлен в карточки, исследовательский кандидат для akuz-optimizer-twin, профильное совпадение / NEEDS_EVIDENCE; не внедрено.

JetStream генерирует специализированные ускорители известных SQL-запросов, обновляет состояние при записях и допускает доказательные Verus-контракты. Авторы сообщают 584× read-only TPC-H geomean к DuckDB для tested и 89× для verified; результаты привязаны к своему workload, аппаратуре и trusted host contracts. Это **не** ускорение произвольных SQL, не поддержка SQL Server и не качество существующего PG-двойника, который выполняет только EXPLAIN на пустой схеме.

**Ограничения:** консистентность зависит от trusted adapter/commit order; доказательство покрывает объявленную семантику и supported SQL, а не всё SQL. Нет тестов на наших БД; нагрузка записи, память и сборка могут съесть пользу. [Подробный обзор](../reviews/jetstream/2026-11-14.md) · [матрица проектов](../portfolio/2026-11-14/review.md).
