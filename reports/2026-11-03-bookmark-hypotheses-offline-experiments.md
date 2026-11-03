# Offline-эксперименты по избранному: Vectorless Retrieval, DBA Safety, Agent Verification

**Дата:** 2026-11-03. **Статус:** частично подтверждено лабораторными проверками; внедрений нет.
**Цель:** превратить четыре гипотезы из инвентаризации сохранённых материалов в результаты с воспроизводимыми проверками, отделив эффекты от авторских заявлений.

## Границы и версии

- Wiki_PG: Artemedi/Wiki_PG@d55721bb99bff25fae352341cfd630c048693d6b.
- agent-config: Artemedi/agent-config@489e074ab0daaadb732673c193047172a3744862.
- pgbot: pgrundev/pgbot@826531fefd7d (для осмотра исходников, **не запускался**).
- research-hub до добавления отчёта: Artemedi/research-hub@47f2888b3be4b929f7cdfae42aea0aed5cb60fa7.
- project-registry при отборе: Artemedi/project-registry@9e2393c2ed03c2212ed0c61939987809628f9160.
- Исполнено на Bazzite в отдельном временном каталоге. Базы AKUZ, работающие агентные службы, учётные данные и исходники рабочих репозиториев не затрагивались.

## EXP-01. Vectorless RAG: влияние FTS-оператора и дедупликации на Recall@8

**Проверяемая гипотеза:** для DBA-запросов отсутствие semantic-векторов может компенсироваться лексическим поиском с более подходящими правилами выдачи. Это не проверка полного RAG, а поиск **нужного документа**.

Исходный код и разметка — существующие Wiki_PG/ingestion/build_document_store.py, search_document_store.py и source_recall_benchmark.py. SQLite FTS5, tokenizer unicode61; 24 обнаруженных и разобранных Markdown-документа, 190 секций, 0 ошибок парсинга. Все четыре ожидаемых уникальных исходных документа физически находятся в индексе. Оценка по **6** опубликованным в исходниках labelled DBA cases, top-k=8; две формы запроса, question и keywords. Запросы не создавались специально под новую стратегию. Результаты не являются независимым held-out тестом.

| Режим | AND (существующий search) | OR | OR + dedup по source_file | OR + dedup + host |
| --- | ---: | ---: | ---: | ---: |
| Полный вопрос: Recall@8 | 0/6 | 6/6 | **6/6** | 4/6 |
| Ключевые слова: Recall@8 | 3/6 | 5/6 | **6/6** | 4/6 |
| Полный вопрос: MRR@8 | 0.000 | 0.325 | 0.325 | 0.667 |
| Ключевые слова: MRR@8 | 0.389 | 0.464 | 0.502 | 0.667 |

Для question / OR ранги: [3,2,6,5,2,4], для keywords / OR+dedup: [5,1,7,1,3,3]. Метрика ранжирования для host-filter считается только по найденным документам, а потерянные оцениваются нулём: высокий MRR **не** компенсирует падение Recall. Причина двух потерь при host-filter: ожидаемые документы кластера и инцидента имеют пустое поле sections.host, несмотря на наличие текста в индексе. Фильтр корректно исполняет контракт, но метаданные недостаточны.

**Реализация эксперимента:** [experiments/2026-11-03-vectorless-fts5.py](../experiments/2026-11-03-vectorless-fts5.py). Скрипт использует существующий production SQLite AND-код без изменений и читает только готовый временный индекс. Построение индекса:

    python3 Wiki_PG/ingestion/build_document_store.py --wiki-root Wiki_PG --backend sqlite --sqlite-path /tmp/wiki-lexical.sqlite3 --raw-limit 10
    python3 experiments/2026-11-03-vectorless-fts5.py --wiki-root Wiki_PG --database /tmp/wiki-lexical.sqlite3

Wiki_PG здесь — внутренний каталог клонированного Artemedi/Wiki_PG. Воспроизводимость требует указанной ревизии, доступного Python со SQLite FTS5 и тех же шести CASES. Текущий SQLite-код использует строгий AND. Сравнивать время стратегии в миллисекундах по шести тёплым запросам нецелесообразно.

**Ограничения:** 6 случаев, 24 файла, отсутствие независимой выборки, нет проверки качества сформированного ответа, противоположного dense/Chroma результата на **той же самой** выборке, нагрузки, RAM/IO, токенов или p95. Исторический Chroma отчёт использовал другой индекс — сравнение его процентов с этой таблицей будет некорректным. Дедупликация извлекает до 190 секций, что при большом индексе будет дорого: production-вариант потребует ограниченного candidate pool. Ни OR, ни фильтр в исходники не перенесены.

**Вердикт:** BENEFIT_ON_SMALL_FIXTURE / NO_PRODUCTION_APPROVAL. Следующий gate — минимум 100 независимо размеченных запросов, покрытие метаданных host, одинаковый корпус FTS/dense/hybrid, source-recall и answer correctness плюс p50/p95, RAM/IO, стоимость индексации, бюджет и откат.

## EXP-02. Минимальные права DBA-диагностики

На изолированном контейнере PostgreSQL 18.3 (image локально, сеть отключена, память 384 MiB, CPU 1) создана база lab и роль observer. Роль получила CONNECT, USAGE, SELECT на одну учебную таблицу и членство в pg_monitor; на уровне роли выставлены default_transaction_read_only=on и statement_timeout=150ms.

- SELECT тестовой строки — PASS.
- Чтение pg_stat_activity — PASS.
- CREATE TABLE — ожидаемый отказ: read-only transaction.
- INSERT после явного отключения default_transaction_read_only в том же сеансе и начала следующей команды — ожидаемый отказ: permission denied for table fixture.
- SELECT pg_sleep(0.5) — отменено по statement_timeout.

Контейнер удалён; проверка количества строк после попытки INSERT показала 1 (без изменений). Настройка default_transaction_read_only и statement_timeout может быть переопределена ролью: **настоящая граница запрета записи — объектные права**, а не session GUC.

**pgbot v0.9.0 НЕ тестировался:** исходники клонированы, но загрузка проверяемого release tar.gz прервалась TLS error; Go compiler не обнаружен. Ни claims pgbot, ни сравнение с Wiki_PG на одинаковых инцидентах не подтверждены. Статус PGBOT_RUNTIME_UNAVAILABLE. Сценарий тестирует лишь prerequisite — ограниченную диагностическую роль.

## EXP-03. Agent-config: регрессионный baseline, не A/B verifier

На изолированном чистом checkout Artemedi/agent-config@489e074ab0da:

    PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q --disable-warnings --no-header tests/test_model_assist.py tests/test_review.py

**Результат 33 passed, 0 failed, 0.08 s.** Тесты выполнялись без реальных вызовов моделей. Навык Open Steps os-check-work просмотрен, но не исполнялся на модельных сессиях; VeriHarness и RRSI/Harness² не запускались. Эффективность независимого reviewer и сокращение false accept/false reject не измерены.

**Вердикт:** BASELINE_PASS / EFFECT_UNMEASURED. Следующий gate — 30–50 фиксированных кейсов на исходниках, включая ложные отчёты об успешных тестах, недостающие файлы, инвертированные утверждения и ошибочный патч; oracle — локально воспроизводимая проверка. Сравнить current agent-config, дополнительный verifier и independent review при одном budget.

## EXP-04. Integrity smoke-test научного архива

В research-hub проверены **66 Markdown-файлов вне неизменяемого archive/** и **331 относительная Markdown-ссылка**. Отсутствующих локальных целей: **0**. В изолированной искусственной копии одна намеренно сломанная ссылка была распознана: 1/1.

Это проверяет только существование локальных targets по базовому Markdown-синтаксису. Полные тексты статей, внешние URL, соответствие цитат утверждениям, проверка DOI и доступность источников этим экспериментом **не** проверены. Исторический архив не изменялся. Для научных публикаций продолжает действовать правило FULL_TEXT_UNAVAILABLE при отсутствии полного текста.

## Дополнительные test failures и ограничения среды

В Wiki_PG выбранные retrieval-тесты:

    python3 -m pytest -q Wiki_PG/ingestion/tests/test_controlled_retrieval_benchmark.py Wiki_PG/ingestion/tests/test_retrieval_benchmark.py Wiki_PG/ingestion/tests/test_source_recall_benchmark.py

**18 passed / 2 failed** на чистом checkout. Обе ошибки — ModuleNotFoundError: chromadb в тестах controlled_retrieval_benchmark; среда не имела этой зависимости. Это **не** подтверждённый функциональный баг алгоритма, но и не полноценное прохождение suite. Никаких пакетов в основную систему не устанавливалось.

## Решения и границы публикации

1. **Wiki_PG:** экспериментальное преимущество OR + source-level dedup на малой выборке записать в карточку как измеренный smoke-test, не как разрешение менять код. Исправлять пустые host-метаданные только после анализа контрактов и регрессий.
2. **agent-config:** зафиксировать 33/33 как baseline; перенос open-steps/VeriHarness или новый harness не одобрять до replay A/B.
3. **research-hub:** оставить исходные авторские исследования отдельно от наших измерений. Публиковать исследовательскую гипотезу и локальный oracle, но не приписывать проекту эффект, который в нём не воспроизводился.

GitHub Issues не создавались. Исходники пользовательских проектов, конфигурации работающих агентов и production не изменялись. Все правки по итогам ограничены этим документом, воспроизводящим offline-скриптом, ссылкой из README и разделами результатов соответствующих карточек project-registry.
