# LynxDB — одно-бинарный аналитический движок для логов и PPL-запросов

[Структурированная запись и связи](../catalog/studies/lynxdb.md)

**Тип:** авторский open-source engineering source, не peer-reviewed исследование. **Первичный источник:** [lynxbase/lynxdb](https://github.com/lynxbase/lynxdb), pinned [`6623322ab58f605efb35c636db8ee10b3884f6a8`](https://github.com/lynxbase/lynxdb/tree/6623322ab58f605efb35c636db8ee10b3884f6a8), [README](https://github.com/lynxbase/lynxdb/blob/6623322ab58f605efb35c636db8ee10b3884f6a8/README.md), [LICENSE](https://github.com/lynxbase/lynxdb/blob/6623322ab58f605efb35c636db8ee10b3884f6a8/LICENSE) (Apache-2.0). Источники прочитаны 23.11.2026. Go `1.26.0`.

**VERIFIED:** единый PPL-компилятор и исполнитель для чтения файлов/stdin и запросов к постоянному single-node HTTP-серверу. Временные local-query индексы тоже используют файловое columnar storage; сервер хранит индексированные события, выполняет query и принимает логи по HTTP/syslog/OTLP/Elasticsearch bulk/Splunk HEC. Возможны фильтрация, агрегация, группировка, поиск и `explain` с частичным покрытием OpenSearch PPL.

**NOT_VERIFIED / CONTRADICTED AS CURRENT FEATURE:** заявленный «распределённый кластер» не подтверждается pinned source: официальное [architecture overview](https://github.com/lynxbase/lynxdb/blob/6623322ab58f605efb35c636db8ee10b3884f6a8/docs/site/docs/architecture/overview.md) говорит **single-node**; [Kubernetes](https://github.com/lynxbase/lynxdb/blob/6623322ab58f605efb35c636db8ee10b3884f6a8/docs/site/docs/deployment/kubernetes.md) имеет `replicas: 1`. Elasticsearch-compatible `_cluster/health` — заглушка single-node. «LynxFlow» как отдельный компонент/query API в просмотренном pinned README/architecture и названиях пакетов не подтверждён; реализованы PPL → IR → row/columnar operators.

**Ключевые ограничения:** `README.md` предупреждает о нестабильности API/storage/query semantics между релизами; нормальный ingest может вернуть успех до durable Sync, а store **не имеет event write-ahead log** и теряет незафиксированные buffered events при crash; native ingest может частично принять prefix. Индексы и retention являются локальными. PPL поддерживает не все команды и отличается семантикой от OpenSearch (например `distinct_count` и `percentile` имеют режимы приближённых вычислений; `join` хранит правую сторону в памяти).

**Потенциальная применимость:** только документально подтверждённые идеи для автономного анализа **санитизированных копий** логов `akuzlogparser`, read-only диагностических данных `Wiki_PG` и evidence-процесса `akuz-issue`. Не подключать production collectors/SSH/MCP и не заменять существующие парсеры без точной event/parsing fidelity и оценки RAM/IO, PPL semantics, retention, data-loss/PII-risk.

**Вердикт:** `BOUNDED_CODE_REVIEW / DOCUMENTED_CANDIDATE / NEEDS_EVIDENCE / BENEFIT_UNPROVEN / NOT_PRODUCTION_APPROVED`. Не проводились независимый benchmark, эксплуатация кластера, binary execution, импорт реальных логов или изменения исходников целевых проектов.

[Инженерный аудит, A/B/C и риски](../reviews/lynxdb/2026-11-23.md) · [Портфельная оценка](../portfolio/2026-11-23/lynxdb.md).
