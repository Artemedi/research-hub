# MemComposer

**Историческая запись:** [12–19 октября 2026](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md). **Дата full-text review:** 2026-11-03. **Уровень:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_REPRODUCED / PROPOSED_ONLY`.

**Сводный отчёт:** [методы, результаты, ограничения](../portfolio/2026-10-12--2026-10-19/review.md). **Проекты:** [явная матрица соответствия](../portfolio/2026-10-12--2026-10-19/project-fit.md).

## Методология, результаты, caveats и безопасный эксперимент

**Полный источник:** https://arxiv.org/abs/2610.21091; [PDF v1](https://arxiv.org/pdf/2610.21091v1), 30 страниц, SHA-256 `23dbaad05dd483ba39d2a761f4b62b24c9911e70923fd9649d9df52673d9d116`.

**Методика.** Trainable `composer` по запросу и top-10 retrieved past trajectories динамически выбирает количество, состав и порядок **procedural memories**. `ExPO` оптимизирует полные task success через GRPO; исполнители Qwen3-4B и Ministral-3-8B, исходные memory banks и retriever заморожены. Оценка: три домена τ²-bench, четыре trial/task, `pass1` и `pass4`; baselines — no-memory, similarity, complexity, reranker, MemRL, Memento.

**Результаты авторов.** Средний `pass1` Qwen3-4B: **50,8%** у MemComposer против **45,0%** наиболее сильного из отдельных представленных baselines Memento; Ministral 8B: **63,5%** против **58,9%** MemRL. Авторы также сообщают сокращение среднего memory-token use на **16,9% и 4,9%** относительно сильнейших baseline по двум исполнителям. Результаты для трёх service domains не являются доказательством выигрыша на базе знаний DBA.

**Ограничения.** Только 4B и 8B executors, отдельный обучаемый компонент и RL training overhead. Порядок выдачи обучается одновременно с отбором, поэтому вклад order не изолирован полностью; нет полного permutation oracle. Изучена **procedural memory**, а не семантические документы, знания пользователя или SQL схемы. Нельзя переносить цифры напрямую на `Wiki_PG`.

**Проверяемое применение.** Сначала offline ablation над собственными разрешёнными trajectory memories: BM25/embeddings top-k, fixed order, rule-based dynamic-k, и только потом learned composer. Оценить task success, pass^k, false recall, tokens и training+online cost.

**Оценка применимости:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE`; у внешнего проекта `AUTHOR_STATED / NEEDS_SOURCE_CODE`. Source-level seam или measured benefit не подтверждены.
