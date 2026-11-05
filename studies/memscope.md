# MemScope

**Историческая запись:** [12–19 октября 2026](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md). **Дата full-text review:** 2026-11-03. **Уровень:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_REPRODUCED / PROPOSED_ONLY`.

**Сводный отчёт:** [методы, результаты, ограничения](../portfolio/2026-10-12--2026-10-19/review.md). **Проекты:** [явная матрица соответствия](../portfolio/2026-10-12--2026-10-19/project-fit.md).

## Методология, результаты, caveats и безопасный эксперимент

**Полный источник:** https://arxiv.org/abs/2610.21170; [PDF v1](https://arxiv.org/pdf/2610.21170v1), 19 страниц, SHA-256 `d0f7e2c555c0cdfdd5156abc07ae96a9f31f06076bceb6a7177107b6c7d17b90`.

**Методика.** `Patch Agent` диагностирует память не по итоговому score, а по raw tool traces, актуальному memory state и provider code. Изменения локализованы под provider identity и memory compatibility; сравниваются summary-only, trace-only и trace+memory inspection. Эксперименты: GAIA, xBench DeepSearch-2505, ALFWorld unseen; DeepSeek V3.2 / Kimi K2.7 Code, GPT-4o-mini judge для web tasks, deterministic environment success для ALFWorld.

**Результаты авторов.** Диагностическая ablation GAIA: trace+memory **86,67%**, trace-only **70,00%**, summary-only **63,33%** (не все варианты MemScope одинаково успешны). На 70 paired вопросах xBench после эволюции **49→55** правильных у DeepSeek и **50→53** у Kimi; ALFWorld unseen **34/67 (50,75%)→48/67 (71,64%)**. Из 14 архивированных переходов median code-change ratio **4,4%**.

**Ограничения.** Self-modifying provider — риск непреднамеренного drift; локальная диагностика не является доказательством правильности патча. Web бенчмарки частично оценивались LLM judge; код и состояние памяти менялись одновременно, а 14 transitions — небольшая выборка. Сравнение с baseline привязано к конкретным setup; нельзя разрешать Patch Agent править production memory код.

**Проверяемое применение.** На отдельной копии/fixture намеренно внедрить 10–15 defects (stale retrieval, broken early guard, missing evidence). Сравнить summary-only vs trace-only vs trace+memory диагностику: точность локализации, false positives, changed lines, regression tests, tokens и стоимость. Патчи только в throwaway copies; human review обязателен.

**Оценка применимости:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE`; у внешнего проекта `AUTHOR_STATED / NEEDS_SOURCE_CODE`. Source-level seam или measured benefit не подтверждены.
