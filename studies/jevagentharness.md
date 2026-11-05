# JevAgentHarness

**Историческая запись:** [12–19 октября 2026](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md). **Дата full-text review:** 2026-11-03. **Уровень:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_REPRODUCED / PROPOSED_ONLY`.

**Сводный отчёт:** [методы, результаты, ограничения](../portfolio/2026-10-12--2026-10-19/review.md). **Проекты:** [явная матрица соответствия](../portfolio/2026-10-12--2026-10-19/project-fit.md).

## Методология, результаты, caveats и безопасный эксперимент

**Полный источник:** https://arxiv.org/abs/2610.21412; [PDF v1](https://arxiv.org/pdf/2610.21412v1), 44 страницы, SHA-256 `16af19adf3eed2a5fcce32cd4402cd71215f11f58d696d683809700d449feb06`.

**Методика.** `AgentDecisionBench` сравнивает точность isolated multiple-choice decision и реальную успешность целого агента в задачах tool choice, аргументов и stopping. `JevAgentHarness` разрешает delegate небольшой модели только выше **calibrated threshold**, заданного по траекториям конкретного агента; сомнительные шаги возвращает LLM. `AgentDecision-4B` дополнительно обучен на состояниях после собственных ошибок агента. Проверки в DecisionGym, ALFWorld, mini-SWE-agent и др.

**Результаты авторов.** Самая точная isolated-choice модель решала лишь **69,5%** полноценных agent tasks; AgentDecision-4B — **91,5%**, Jev — **82,0%** в описанном comparison. Без настроенного порога success падал до **−19 п.п.** В подходящем DecisionGym с выделенной GPU наблюдались **−86,3% cost и ускорение до 2,5×**, но для coding agent более скромные **7,0–10,5% экономии**, а некоторые тяжёлые задачи становились медленнее.

**Ограничения.** Англоязычные наборы, преимущественно Gemini executor; доказана **non-inferiority в допуске 3/5 п.п.**, не эквивалентная успешность. Confidence threshold и training подлежат повторной калибровке для каждого нового агента и набора инструментов; отдельный shared GPU может ухудшить latency и IO. Решение `which tool` не равно выбору провайдера в `9router`, менять routing/Model Trust нельзя автоматически.

**Проверяемое применение.** Shadow-only 100+ записанных решений из синтетических задач. Baseline крупная модель против calibrated cascade; task-level success с независимым oracle, conditional error, refusal quality, p50/p95 и полный GPU serving cost. Если задача не имеет дешёвого дискретного выбора — `NO_FIT`.

**Оценка применимости:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE`; у внешнего проекта `AUTHOR_STATED / NEEDS_SOURCE_CODE`. Source-level seam или measured benefit не подтверждены.
