# Google MCP Toolbox for Databases — PostgreSQL live read-only MCP

**Категория:** ENGINEERING_IMPLEMENTATION; не исследовательская статья.
**Первичный источник:** [Google MCP Toolbox](https://github.com/googleapis/mcp-toolbox), [официальный release v1.15.0](https://github.com/googleapis/genai-toolbox/releases/tag/v1.15.0); источник main исследован на [3e536bb](https://github.com/googleapis/genai-toolbox/tree/3e536bb683c914b26bdf9046a65b805a160af8dc). Бинарник зафиксирован отдельно в лабораторном отчёте.
**Прямые измерения:** [PostgreSQL 18.3 / Wiki_PG MCP lab](../reports/2026-11-04-mcp-toolbox-vs-wikipg-postgres-lab.md), [воспроизводимый MCP-тест](../experiments/2026-11-04-mcp-toolbox-wikipg-compare.py).
**Статус:** `BOTH_MCP_EXECUTED / LIMITED_FIXTURE_PASS / NOT_DROP_IN_REPLACEMENT / NO_PRODUCTION_APPROVAL`.

## Что испытано

- Скачан официальный исполняемый Toolbox v1.15.0; действительно запущен как **MCP stdio сервер** с единственным разрешённым `postgres-sql` инструментом (фиксированный `SELECT ... FROM pg_settings WHERE name=$1`, PostgreSQL роль без write grants). Wiki_PG запускается через исходный `mcp_wiki_server.py` и получает данные из двух вымышленных снапшотов.
- Оба реальных MCP API корректно передали четыре значения `max_connections`, `random_page_cost`, `wal_level`, `work_mem`: **80/80** измеряемых RPC у каждого после прогрева. Сам последний снимок Wiki_PG **специально синтезирован из live oracle**, поэтому это проверка контракта, а не независимое подтверждение исторической достоверности данных.
- При изменении живого `work_mem` на **8 MiB** Toolbox вернул **8192 kB**, а Wiki_PG сохранил **4096 kB** с прежними `captured_at` и `source_file`. Конфигурация disposable PostgreSQL восстановлена. Исторический запрос к снимку от 2026-11-03 возвращает ранее записанные **8192 kB**; при отсутствии даты Wiki_PG вернул `status=no_snapshot`, но **`isError=false`**.
- В одном локальном stdio micro-lab median RPC по `work_mem` **0.759 мс Toolbox** против **1.269 мс Wiki_PG**. Клиентская сериализация результата: 183 байта против 7157 байт из-за provenance и дублирования структуры в SDK. Это **разные языки/транспорты**, никакой доказанной production-победы по CPU/p95 нет.
- SQL-подобная строка в параметре не исполнилась: Toolbox использовал bind variable, Wiki_PG отказал при validation. PostgreSQL роль без write privileges, INSERT запрещён даже при отключённом сеансовом read-only GUC. Конфигурация Toolbox по умолчанию пометила `postgres-sql` как `readOnlyHint=false / destructiveHint=true`: metadata ≠ privilege enforcement.

## Решение по проектам

- [Wiki_PG](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/Wiki_PG/PROJECT.md): Toolbox можно исследовать как **дополнительный live SQL evidence producer**, а не замену исторических отчётов/реестра кластеров/backup status/RAG. Оставить существующий temporal/source contract.
- [dsh-runtime](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh-runtime/PROJECT.md): потенциальный адаптер по проектному профилю, **без прогона** runtime и без решения о внедрении.

**Следующий gate:** сопоставимый набор DBA-инцидентов на PostgreSQL 15/18, read-only права, прямой oracle, timestamps, error statuses, метрики p95/CPU/IO и контроль параллельности. Никаких изменений production, MCP allowlists, пользовательских баз или работающих агентных hooks.
