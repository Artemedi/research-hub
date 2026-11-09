# Портфельный аудит — 2026-11-09

**Исходный портфель:** 83 исследования, инвентаризация от 2026-11-07.
**research-hub baseline:** 7f4facb5623ee90e64d98532ad8a33d8fb75e7c9.
**Private project registry snapshot:** 421268e5c60fd1b5f37bd69a84b923ff28ce3e86, 45 профилей.
**Scope:** продолжение очереди существующего портфеля; weekly discovery не запускался и новые источники не добавлялись.

## Выбор источника

Сначала проверены последние опубликованные follow-ups и current review pointers: Agent Mosaic, AED, CERA-MoA, Understand Anything и HTN-Orchestrate. Их результаты не повторялись. В каталоге для agent-risk оставался только исторический agent-risk-review от 2026-11-03, а portfolio queue отмечала отсутствие независимого targeted-replay oracle. Поэтому выбран один следующий открытый источник — **agent-risk**.

## Результат итерации

- Полный PDF v1 (43 страницы) получен и SHA-256 сверён с карточкой источника.
- Прочитаны Methods, Results, Limitations, Ethical Considerations и экспериментальные приложения.
- Companion repository pinned на a1ab24aaf3c1e5bfbe47a24eaf4cf411bf0b3f1b; unit tests: 147 passed, 2 skipped, 0 failed; author finite-check suite: 15/15 PASS (621.9 s).
- Независимый deterministic synthetic lab: 200 сценариев; targeted continuation совпал с full live oracle на 171/171 blocked cases; log-only bounds [0.135, 0.890] содержали live harm 0.665; synthetic continuation calls составили 50% live calls при исключённой стоимости уже имеющегося prefix log. Нарушения A1/A2/T дали ожидаемые расхождения.
- Авторские 16 runs / около 49 000 episodes не воспроизводились. Production approval отсутствует.

Подробности: [предметный обзор](../../reviews/agent-risk/2026-11-09-replay-assumptions.md), [project-fit](agent-risk-project-fit.md), [synthetic experiment](../../experiments/agent-risk/2026-11-09-replay-boundary.py), [evidence JSON](../../data/results/agent-risk/2026-11-09-replay-boundary.json).

## Project fit

Прочитаны все 45 PROJECT.md на указанном registry snapshot. Текущий shortlist — dsh-runtime и agent-config; HermesAgent отложен. Source-level seams остаются NOT_EVALUATED, target source repositories не проверялись. В трёх текущих карточках уже есть backlinks на agent-risk; новых оснований для изменения приватного registry не возникло, поэтому registry не изменялся.

## Практическая оценка и следующий минимальный тест

- dsh-runtime: потенциальная ценность **6/10**, сложность **8/10**. Релевантность выше при наличии durable per-step logs и restorable snapshots; основная цена — полнота state capture/restore и доказательство A1/A2/T.
- agent-config: потенциальная ценность **5/10**, сложность **6/10**. Возможен pre-change review для policy/config hooks, но replay engine и evidence persistence профилем не подтверждены.
- Основные риски: ложная уверенность при потере harm timing; snapshot storage и restore IO; несовпадение hidden/runtime state; agent awareness/announced gate; стоимость targeted reruns. CPU/RAM/VRAM/IO, latency, tokens и денежная стоимость в target projects не измерялись.
- Следующий project-specific offline test: 20–40 новых synthetic trajectories, три arms (log-only, full rerun, targeted replay), независимый oracle, seeded repeats. Приёмка: targeted replay совпадает с live oracle при A1/A2/T; log-only bounds содержат oracle; A1/A2/T negative controls должны обнаруживать нарушение; ни одного false approval. Измерить snapshot bytes, restore IO, calls, latency и CPU/RAM; production не затрагивать.

## Статусы

- AUTHOR_REPORTED: сохранены как результаты авторов.
- CODE_REVIEW: ограниченный review pinned companion package и tests.
- SYNTHETIC_LAB: PASS только для опубликованного deterministic fixture.
- AUTHOR_EXPERIMENT_REPRODUCTION: NOT_REPRODUCED.
- PROJECT_PROFILE_MATCH: NEEDS_CURRENT_CODE / NEEDS_EVIDENCE.
- PRODUCTION_APPROVAL: отсутствует.

Следующий запуск должен выбрать другой ещё не закрытый источник из текущей очереди. Повтор agent-risk без новых данных не требуется.
