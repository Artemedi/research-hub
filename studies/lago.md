# LAGO: полное ретроспективное ревью

**Историческая запись:** [12–19 октября 2026](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md). **Дата full-text review:** 2026-11-03. **Уровень:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_REPRODUCED / PROPOSED_ONLY`.

**Сводный отчёт:** [методы, результаты, ограничения](../reports/2026-11-03-full-text-review-2026-10-12-to-19.md). **Проекты:** [явная матрица соответствия](../reports/2026-11-03-project-mapping-2026-10-12-to-19.md).

## Методология, результаты, caveats и безопасный эксперимент

**Полный источник:** https://arxiv.org/abs/2610.19843; [PDF v1](https://arxiv.org/pdf/2610.19843v1), 16 страниц, SHA-256 `f54fe3c3751290e8e593326b66d2ccff8b44e255f4b0ffe52ecafaee2b487943`.

**Методика.** `Meta-agent` управляет специализированными `options`: повторно использует или создаёт агента, назначает задачу, проверяет результат, сохраняет только подходящий reusable option. Базовая модель на основном эксперименте `Qwen3.5-35B-A3B` заморожена. Официальный SWE-bench Verified на 500 задачах и отдельное строго одинаковое сравнение на **150** репозиторий-стратифицированных задачах с mini-SWE-agent и Terminus 2 (температура 0, один attempt, Docker oracle); 50-task component ablation.

**Результаты авторов.** LAGO решает **58,6% из 500** полного SWE-bench Verified — это только его собственный absolute score. На **совпадающих 150** задачах: mini-SWE-agent **49,3%**, Terminus 2 **57,3%**, LAGO **60,3%**. На 50-task ablation полный LAGO **30/50**, без decomposition **26/50**, без library **24/50**.

**Ограничения.** У 150-task сравнения широкая ошибка (авторы оценивают примерно ±8 п.п.), 500-task конкурентных reruns нет. Budget/context scaffold не полностью нормированы. Участие options и деформация знания не отделены причинно; даже shuffled content даёт **28/50**, а utility зависит от baseline/LLM/router. Рост банка options требует dedup и governance.

**Проверяемое применение.** В offline coding fixture: текущие Agent Skills/approved runbook против bounded options reuse, отдельно spawn/verify/dedup. Отслеживать actual test pass, missed constraints, library growth, work/tokens, malicious skill propagation. Не создавать self-updating production skills.

**Оценка применимости:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE`; у внешнего проекта `AUTHOR_STATED / NEEDS_SOURCE_CODE`. Source-level seam или measured benefit не подтверждены.
