# Harness² — Recursive Agent Harnessing for an Open World

**Источник:** [полный HTML v1, arXiv 2610.14224](https://arxiv.org/html/2610.14224v1). **Проверенный код:** [google-research/harness2@68688175](https://github.com/google-research/harness2/tree/6868817518876de8fd170c6a8354daca273b6191), Apache-2.0.
**Эксперимент:** [2026-11-04 — RRSI/Harness² overfitting lab](../reviews/rrsi-harness2/2026-11-04.md), [offline-скрипт](../experiments/2026-11-04-rrsi-harness2-selector-smoke.py).
**Статус:** `SELECTION_POOL_CONTRACT_VERIFIED / PROPOSE_PROBE_COMPOSE_NOT_RUN / NO_PRODUCTION_APPROVAL`.

## Подтверждено собственными проверками

На Bazzite **70 pytest tests + 73 subtests passed**, нулевые ошибки. Внимание: установленный Python 3.14.8, тогда как `pyproject.toml` объявляет `>=3.12,<3.14`. Это **smoke test вне поддерживаемого runtime**; перед полноценным использованием установить изолированную 3.12/3.13 среду.

Запущена оригинальная `harness2.core.selection.selection_pool` на синтетических run objects. При `mode=agg,k=2` пул содержит **agg1/agg2**, при `mode=sequential,k=2` — **c1/c2**, а `base1` отсутствует в обоих случаях **по авторскому дизайну**. Проверена детерминированная анонимизация через `assign_ids`. Это не уязвимость и не дефект метода: функция отвечает за состав кандидатов для выбора между *refined rollouts*, а не за внешний quality gate относительно baseline.

**Не запускалось:** автономные agent-model шаги Propose/Probe/Compose, Codex/OpenCode executor, grader, continual improvement harness, model-token accounting, замеры latency и transfer на рабочих задачах. Результаты RRSI selector из общего протокола не являются benchmark Harness².

## Применимость

[agent-config](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/agent-config/PROJECT.md) — использовать только принципы отдельного evaluation/holdout. [dsh-runtime](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh-runtime/PROJECT.md) — профильная идея накопления опыта harness, **без evidence для внедрения**.

**Решение:** `RESEARCH_PRINCIPLE_ONLY`. При любом будущем тесте сравнивать выбранный output с неизменным base в независимом контрольном контуре, не допускать утечки benchmark rubric, учитывать стоимость параллельной генерации, изоляцию executor и откат. Никаких изменений исходников проектов.
