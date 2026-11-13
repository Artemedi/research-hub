# NVIDIA Auto Ontology — семантический слой и text-to-SQL

[Структурированная запись и связи](../catalog/studies/auto-ontology.md)

- **Первоисточник:** [NVIDIA/auto-ontology @fc43a82600e18b19d159c52023f54f5572f537ac](https://github.com/NVIDIA/auto-ontology/tree/fc43a82600e18b19d159c52023f54f5572f537ac); [отдельный eval](https://github.com/NVIDIA/auto-ontology-eval).
- **Класс:** engineering project, не рецензируемая научная статья; лицензия Apache-2.0; Python package v1.2.0 в закреплённой ревизии.
- **Проверка:** просмотрены README, документация API/MCP/credentials, исходные файлы semantic compilation/SQL validation/connector, опубликованные issues. Статический аудит, без запуска приложения, локального CI и benchmark.
- **Решение:** ACCEPT_BOUNDED / P1 — только изолированный пилот с синтетическими схемами; реальная применимость NEEDS_EVIDENCE.

## Механизм

LLM предлагает бизнес-термины, SQL attributes и семантические отношения по реальной реляционной схеме, профилированию значений и истории SQL. PostgreSQL/pgvector хранит результаты, text-to-SQL использует онтологию. MCP exposes curated read surface. Eval предлагает schema-only vs ontology-assisted execution-accuracy benchmark, но на наших проектах эффект не измерен.

## Блокеры

- В официальных коннекторах нет MSSQL. Не подключать к production AKUZ.
- [Issue #463](https://github.com/NVIDIA/auto-ontology/issues/463): текущий Postgres connector содержит неверную корреляцию схем при чтении cross-schema FK.
- [Issue #486](https://github.com/NVIDIA/auto-ontology/issues/486): SELECT COUNT(*) может быть ошибочно отклонён из-за фильтра пустого списка колонок.
- [Issues #468](https://github.com/NVIDIA/auto-ontology/issues/468) и [#469](https://github.com/NVIDIA/auto-ontology/issues/469): ASCII normalization может ломать кириллицу и PII detection.
- [Issue #497](https://github.com/NVIDIA/auto-ontology/issues/497): отсутствие нужной информации иногда маскируется запросом по похожей таблице.
- [Документация credentials](https://github.com/NVIDIA/auto-ontology/blob/fc43a82600e18b19d159c52023f54f5572f537ac/docs/connections.md): без Vault пароли UI-соединений могут сохраняться в plaintext JSON в каталоге; sample values и query history могут попасть во внешнюю LLM. Только изолированная PostgreSQL и DB-role только для чтения; SQL-agent validation не authority boundary.
- Нагрузка на CPU/I/O, embedding, LLM-вызовы и стоимость данных на наших нагрузках неизвестны.

**Подробный обзор:** [13 ноября](../reviews/auto-ontology/2026-11-13.md). **Применимость к проектам:** [документальная матрица](../portfolio/2026-11-13/source-project-fit.md).
