# HTN-Orchestrate — paired ablation audit и synthetic DAG follow-up

**Дата публикации:** 08.11.2026. **Исходные вычисления и synthetic lab выполнены:** 07.11.2026; synthetic lab в этой итерации не перезапускался. Дополнительная проверка двух upstream test modules выполнена 08.11.2026 на том же pinned SHA.

## Связь с предыдущим full-text review

Полный arXiv v1 HTML/PDF, Methods, Results, Limitations и авторские benchmark уже разобраны в [full-text review от 03.11.2026](../../portfolio/2026-10-12--2026-10-19/review.md#1-htn-orchestrate--hierarchical-task-network-framework-for-multi-agent-orchestration). PDF v1 SHA-256 в каталоге: 781ff3cd5f16673d7f7b9f8a2cb6a8381d6eb5e1332c6e55bed2dcbbd300b452.

Текущий follow-up не переобъявляет тот анализ и не называет синтетический тест репликацией статьи. Он добавляет две ограниченные проверки: точную статистическую переоценку опубликованных парных counts из Appendix C.3 Table 11 и отдельный независимый static-DAG surrogate.

## Авторские результаты и независимая статистическая переоценка

Основание — 200 парных BrowseComp задач, по одному запуску каждого варианта. Из опубликованных counts заново вычислен exact two-sided McNemar test по дискордантным парам:

| Сравнение из Table 11 | HTN correct | Ablation correct | Δ | Exact McNemar p |
| --- | ---: | ---: | ---: | ---: |
| Upfront decomposition | 184/200 | 181/200 | +1.5 п.п. | 0.5811 |
| Single-agent leaf | 184/200 | 179/200 | +2.5 п.п. | 0.3593 |
| No rebuilding | 184/200 | 179/200 | +2.5 п.п. | 0.2668 |

Во всех трёх парах p > 0.05. Это не подтверждает статистически значимое преимущество HTN на данном 200-task subset. Это также **не** доказывает равенство методов: малый эффект, мощность теста и дисперсия требуют отдельного дизайна. Counts взяты из авторской таблицы; исходные ответы/трейсы не получены, поэтому это независимая арифметическая переоценка, а не воспроизведение author outcomes. Подмножество из 200 задач не заменяет полный benchmark из статьи.

## Ограниченный source-code review

Upstream repository: [ycdeng-ntu/htn-orchestrate](https://github.com/ycdeng-ntu/htn-orchestrate), pin [0bccf18d813298e5c2a33961dbf56b907bd8b133](https://github.com/ycdeng-ntu/htn-orchestrate/tree/0bccf18d813298e5c2a33961dbf56b907bd8b133). Текущая main branch на момент follow-up указывает на тот же SHA; source drift не обнаружен.

Проверены:

- [HTNTree readiness и dependency gate](https://github.com/ycdeng-ntu/htn-orchestrate/blob/0bccf18d813298e5c2a33961dbf56b907bd8b133/workflows/dynamic_htn_informed_research/htn/task_tree.py#L68-L90): pending leaf готов только при завершении всех зависимостей; planner-routed leaves не исключаются из frontier.
- [Completion/failure semantics и transactional decomposition](https://github.com/ycdeng-ntu/htn-orchestrate/blob/0bccf18d813298e5c2a33961dbf56b907bd8b133/workflows/dynamic_htn_informed_research/htn/task_tree.py#L142-L158): semantic completion outcome отделён от execution status; failed leaf не завершает зависимые узлы; decomposition валидирует candidate tree до мутации.
- [Task status и semantic outcomes](https://github.com/ycdeng-ntu/htn-orchestrate/blob/0bccf18d813298e5c2a33961dbf56b907bd8b133/workflows/dynamic_htn_informed_research/htn/task_node.py#L15-L55).
- [Epoch timeout/recovery driver](https://github.com/ycdeng-ntu/htn-orchestrate/blob/0bccf18d813298e5c2a33961dbf56b907bd8b133/workflows/dynamic_htn_informed_research/htn/epoch.py#L1-L150).
- [Тест: timeout leaf не разблокирует зависимую работу](https://github.com/ycdeng-ntu/htn-orchestrate/blob/0bccf18d813298e5c2a33961dbf56b907bd8b133/tests/workflows/dynamic_htn_informed_research/test_epoch_recovery.py#L59-L150).
- [Planning contract tests](https://github.com/ycdeng-ntu/htn-orchestrate/blob/0bccf18d813298e5c2a33961dbf56b907bd8b133/tests/workflows/dynamic_htn_informed_research/test_result_informed_planning.py#L1-L150).

Два целевых upstream test modules были исполнены на checkout ровно `0bccf18d813298e5c2a33961dbf56b907bd8b133`: `test_result_informed_planning.py` и `test_epoch_recovery.py` — **43/43 PASS**. Окружение: Python 3.14.8, pytest 9.2.0, pytest-asyncio 1.4.1.post1; async plugin установлен только в `/tmp/htn-test-deps`, глобальное окружение и upstream checkout не изменялись. Один warning от AnyIO касается deprecated pytest `CallSpec2` alias. Полный upstream suite, full monorepo build и benchmark не запускались. Это targeted upstream test execution, не полный runtime coverage и не performance benchmark.

## Независимый synthetic lab

Эксперимент 07.11.2026 использовал собственный простой dependency-gated DAG scheduler и отдельный brute-force topological-order oracle. Оригинальный HTN runtime, LLM, BrowseComp и production не запускались.

| Класс | Сценарии | Результат |
| --- | ---: | --- |
| Валидные DAG | 20 | 20/20 PASS |
| Циклические зависимости | 5 | 5/5 ожидаемо BLOCKED |
| Недостающие evidence prerequisites | 5 | 5/5 ожидаемо NEEDS_EVIDENCE |
| Resume idempotence для валидных DAG | 20 | 20/20 PASS |

Итого 30/30 oracle cases совпали с ожидаемым статусом; 20/20 synthetic resume checks прошли. Это проверяет простые dependency invariants и идемпотентность surrogate scheduler. Это **не** тест динамической HTN-декомпозиции, LLM planning, реального epoch recovery или авторского benchmark.

[Portable experiment script](../../experiments/htn-orchestrate/2026-11-07-offline-audit.py) — исходная логика сохранена; изменён только output path с временного /mnt/data на repository data/results. [Результат с 30 case records](../../data/results/htn-orchestrate/2026-11-07-paired-audit.json).

## Project fit на текущей глобальной карте

На snapshot Artemedi/project-registry@421268e5c60fd1b5f37bd69a84b923ff28ce3e86 профильный triage охватил 45 PROJECT.md. Текущий digest набора: 220d181737e91bb15b8ee371fd08889be1e19a81fa56d8b7c217d5a78f4ecc73. Публичный отчёт не копирует private card text, пути или индивидуальные hashes.

Два profile-level кандидата сохраняются:

- dsh-runtime — agent loop/tool orchestration и continuation/reliability как исследовательская область; конкретный HTN extension point и актуальный baseline не подтверждены.
- hermes-akuz-agents — multi-agent orchestration и DBA handoff; профиль пока документационный, без обнаруженных tests/CI и подтверждённого runtime seam.

Оба решения: PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE, не FIT_CANDIDATE. Их предварительные backlinks уже присутствуют в private registry; новых соответствий и registry edits в этой итерации нет.

## Диспозиция и блокеры

- **AUTHOR_REPORTED:** исходные результаты статьи остаются авторскими.
- **NOT_REPRODUCED:** нет исходных BrowseComp traces, повторов и полного benchmark.
- **STATISTICAL_REANALYSIS:** три exact McNemar p-values пересчитаны из опубликованных paired counts; значимого преимущества на subset не обнаружено.
- **SYNTHETIC_LAB:** 30/30 static DAG oracle cases и 20/20 surrogate resume checks PASS.
- **CODE_REVIEW:** ограниченный review source/tests на актуальном pinned SHA; upstream tests не исполнялись.
- **PROJECT_FIT:** dsh-runtime и hermes-akuz-agents — профильные кандидаты, implementation seams не доказаны.
- **PRODUCTION_APPROVAL:** NO.

**Открытый P1-блокер:** held-out A/B на 20–50 зависимых research tasks с независимым oracle: single agent vs fixed DAG vs HTN. До теста нужны frozen task set, baseline commit, repetitions, success/failure taxonomy, dependency violations, rework, p50/p95 latency, tokens/cost, CPU/RAM и acceptance/noise rule. Никакой интеграции или production изменений до отдельного human gate.
