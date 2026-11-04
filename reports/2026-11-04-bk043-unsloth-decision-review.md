# BK-043 — Unsloth decision model: руководство, notebook и код

Дата обзора 2026-11-04. [Официальное руководство](https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth) (веб-содержимое меняется), [notebook @d85d113eacfc8a87a7003e73ffb2a86403a94344](https://github.com/unslothai/notebooks/blob/d85d113eacfc8a87a7003e73ffb2a86403a94344/nb/Qwen3_5_%284B%29-Decision.ipynb), [библиотека @e2ffc740508707b8f069b3e90aa94de8daea8da0](https://github.com/unslothai/unsloth/tree/e2ffc740508707b8f069b3e90aa94de8daea8da0). HEAD соответствовал этим снимкам на момент получения. Telegram BK-044 — точный повтор URL BK-043, отдельное исследование не создаётся.

## Метод и качество доказательств

Руководство описывает decision head над LLM с `choice`, `noul`, `score` и подготовкой размеченных `state/questions/gold`. В [реализации `split_holdout`](https://github.com/unslothai/unsloth/blob/e2ffc740508707b8f069b3e90aa94de8daea8da0/unsloth/models/decision.py#L1838) разбиение группирует все вопросы строки и перемешивает ID строк; само по себе это не доказывает отсутствие семантических дублей между строками или отсутствия источниковой утечки. Notebook калибрует на `eval_items`, затем отдельно считывает `typed-decisions` test для оценки. Следует отдельно сохранять неизменяемые данные, проверить группировки и оценивать калибровку на независимом test, особенно если настройки отбирались по holdout. Авторы заявляют деконтаминацию опубликованных benchmark sets; мы её независимо не проверили.

На одной странице приведены разные рецепты: верхняя benchmark-таблица описывает LoRA r=64 и одну эпоху для нескольких моделей (включая 0.8B/2B), UI-пошаговый пример задаёт r=16, 2 эпохи и 2e-4, а кодовый пример Qwen3.5-4B — r=16, learning rate 2e-5 и `max_steps=240`. Закреплённый notebook использует r=16, 2e-4 и 60 steps. Это не доказательство ошибки: строки относятся к разным сценариям, но нельзя приписывать результаты таблицы именно показанному 4B notebook. Утверждения о VRAM/времени/accuracy зависят от модели и устройства; GPU-обучение, веса и статистика `NOT_RUN`.

Изучены `FastDecisionModel` dataset/split/evaluate/calibrate и [тест воспроизведения последовательности notebook](https://github.com/unslothai/unsloth/blob/e2ffc740508707b8f069b3e90aa94de8daea8da0/tests/test_decision_from_lm.py#L421): он использует маленькую тестовую модель и тренировку на двух шагах, а не воспроизведение таблицы. Тест нами не запускался из-за отсутствующих модели/ML-зависимостей. Длинные training inputs обрезают конец state; нужны проверки на потери контекста и изменение распределения. Source файлы Unsloth маркируют себя `AGPL-3.0-only`; модели, датасеты, библиотеки и способ поставки требуют отдельной проверки лицензий, без юридического вывода.

## Применимость к портфелю

Проверены все 45 профилей `project-registry@8fbec35ec2d2d3f2de0214de51acfba40b412c5f`. Приведённые статусы — проектные гипотезы, не перенос метрик tutorial.

| Проект | Конкретный сценарий | Ограничения / следующий тест | Статус |
| --- | --- | --- | --- |
| `9router` | Выбор из уже разрешённых provider/model кандидатов; [hard allowlist @d15f5bf](https://github.com/Artemedi/9router/blob/d15f5bf3289e50bddda8263cddd239d7078e4ef0/docs/hard-routing-boundary.md#L3). | Фильтры прав и возможностей не делегируются обученной модели; нужен offline replay с policy oracle. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| `dsh-runtime` | Выбор разрешённого маршрута делегирования; [session authorization @b6a1635](https://github.com/Artemedi/dsh-runtime/blob/b6a1635b1200071754e2871b9d9453368e6daf23/.agents/notes/implemented/feature/2026-08-18-model-selected-subagent-routes.md#L11). | Нужны размеченные задачи и контракт; source проекта не интегрирован и user policy не менялась. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |

`sequential-rca` и `wiki-tasks` пока не имеют подтверждённого task-specific decision dataset и границы модели, прочие профили не дают более сильного матча. Не запускать обучение на чувствительных данных.

**План:** до обучения выбрать pinned baseline и модели/зависимости, отдельные источниковые train/calibration/test groups с контролем дубликатов, oracle task quality и недопущения запрещённых маршрутов, fixed seeds и повторения, negative controls, calibration/ECE и accuracy по группам, latency p50/p95, GPU VRAM/CPU/RAM/IO и стоимость, требования лицензий, конфиденциальности и rollback. Не сравнивать напрямую несопоставимые benchmark/VRAM цифры. До готового набора и согласованных ресурсов `BLOCKED: MEASUREMENT_MISSING`.
