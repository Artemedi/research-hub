# Drift Inspector — протокол ограниченного offline-пилота

**Статус: PLANNED, ничего не запускалось.** Источник — [карточка](../../studies/drift-inspector.md) и [review 13.11.2026](../../reviews/drift-inspector/2026-11-13.md) (ACCEPT_BOUNDED / P1 screening, польза для проектов — NEEDS_EVIDENCE). Код автора закреплён на `6c643d6ebfaa771d01c743d921dac839dd771c40`.

Границы: discovery-only слой research-hub. Не интегрировать в DSH Runtime и production, не менять `dsh-paper2agent`, не отправлять закрытые статьи, внутренние материалы, секреты и PHI во внешние endpoints. Начинать только с разрешённых открытых метаданных. Любой abstract-only результат остаётся `AUTHOR_CLAIM_FROM_ABSTRACT` / SCREENED и не считается проверенной находкой ([RESEARCH_POLICY](../../RESEARCH_POLICY.md)).

## Шаги

| Шаг | Что делаем | Результат |
| --- | --- | --- |
| A | Воспроизвести paper-level prevalence и динамику на опубликованном `artifacts/baseline/acc_clusters_emnlp.csv` при неизменных кластерных метках и year coverage | `data/results/drift-inspector/` |
| B | 1–3 тыс. открытых metadata/abstract из нескольких дисциплин, замороженный test split, 100–150 независимых ACC-разметок, включая outliers и negative controls | corpus manifest + разметка |
| C | На идентичном корпусе сравнить BM25/ключевой поиск, текущий shortlist и ACC + similarity threshold | таблица метрик |

Ожидаемые опорные числа шага A (подтверждены чтением CSV в review, не воспроизведены): 4 488 papers, 16 576 ACC, 80 кластеров, 5 980 noise ACC (36,08%), по 748 работ на год 2020–2025.

## Метрики шага C

precision@K и recall@K проектного shortlist, missed relevant studies, forced assignment, outlier rescue, inter-rater reliability, latency, токены и стоимость, CPU/RAM/IO, стабильность трендов.

Порог `min_similarity` — доработка к авторскому `src/acc/assign.py` (там argmax cosine без abstention). Значение порога и формула не заданы исследованием: подбирать на отдельном dev-split, не на test; ниже порога — `UNASSIGNED` / `NEEDS_REVIEW`. Не выдумывать алгоритм там, где автор его не дал.

## Критерии решения

- **Go:** измеренный прирост recall при заранее заявленном допустимом precision и стоимости. Пороги фиксировать до запуска шага C.
- **No-go:** неверные назначения, неприемлемый рост false positives либо отсутствие положительного эффекта.

## Планируемая раскладка

Каталоги создаются по мере выполнения шагов, а не заранее; скрипты — в `experiments/drift-inspector/`, результаты — в `data/results/drift-inspector/`. Новые файлы регистрировать в `catalog/structure.json`.

## Открытые вопросы

- Независимые разметчики ACC и источник негативных контролей не определены.
- Состав корпуса шага B (дисциплины, окно дат, лицензии метаданных) не выбран.
- Бюджет вызовов LLM-экстрактора и допустимая стоимость не заданы.
