# HTN-Orchestrate

[Структурированная запись и связи](../catalog/studies/htn-orchestrate.md)

**Историческая запись:** [12–19 октября 2026](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md). **Дата full-text review:** 2026-11-03. **Уровень:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_REPRODUCED / PROPOSED_ONLY`.

**Сводный отчёт:** [методы, результаты, ограничения](../portfolio/2026-10-12--2026-10-19/review.md). **Проекты:** [явная матрица соответствия](../portfolio/2026-10-12--2026-10-19/project-fit.md).

## Методология, результаты, caveats и безопасный эксперимент

**Полный источник:** https://arxiv.org/abs/2610.22195; [PDF v1](https://arxiv.org/pdf/2610.22195v1), 20 страниц, SHA-256 `781ff3cd5f16673d7f7b9f8a2cb6a8381d6eb5e1332c6e55bed2dcbbd300b452`.

**Методика.** Двухуровневый `Planner → local Orchestrators` поддерживает HTN: дочерние задания не декомпозируются раньше, чем получены результаты необходимых зависимостей. Итог листьев агрегируется по AND-семантике, при несостоятельной ветке сеть перепланируется. Пять бенчмарков: BrowseComp, FSR, FSO, SUPERChem, PRL-Bench; авторы сравнивают ReAct, Agent Team и DeepSeek Harness с одной базовой моделью для соответствующих harness-строк.

**Результаты авторов.** На BrowseComp получено **89,73%** против **87,28%** у Agent Team и **80,33%** у DeepSeek Harness; SUPERChem **73,44%** против **68,75%** Agent Team и **66,80%** DeepSeek Harness. Результаты относятся к таблице авторов и их конкретным настройкам, не к нашему `dsh-runtime`.

**Ограничения.** Авторы указывают необходимость проверки более глубоких HTN и других backbone; работа не даёт причинной декомпозиции всех различий harness, а стоимость планирования, fan-out и инструментария в разных средах не универсальна. Научный выигрыш зависит от того, есть ли реальные межзадачные зависимости.

**Проверяемое применение.** Сравнить offline на 20–30 задачах с зависимостями: fixed workflow, простой DAG scheduler и HTN с deferred expansion. Независимый oracle — корректность конечного артефакта и соблюдение preconditions, метрики wall-time, total tokens/tools и доля ложных перепланирований. Не писать новый оркестратор без превосходства над простым DAG.

**Оценка применимости:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE`; у внешнего проекта `AUTHOR_STATED / NEEDS_SOURCE_CODE`. Source-level seam или measured benefit не подтверждены.
