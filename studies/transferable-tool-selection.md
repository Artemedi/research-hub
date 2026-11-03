# Training Small LMs for Transferable Tool Selection

**Primary source:** https://arxiv.org/abs/2610.31483 ; [full PDF v1](https://arxiv.org/pdf/2610.31483v1).
**Original PDF SHA-256:** 2c13c3a2558a5c18ed484d62326f62e25ac77ea55cc9dec439a033bd3259145e. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../reports/2026-11-03-full-text-review-2026-10-20-to-26.md). **Project applicability:** [explicit matrix](../reports/2026-11-03-project-mapping-2026-10-20-to-26.md).
**Editorial valuation / effort:** 7/10 ; 7/10. **Proposed disposition:** P2_BM25_BASELINE_FIRST; no implementation approval.

## Methodology

Plan → Retrieve → Select: Qwen3 1.7B/4B/8B получает SFT по synthetic trajectories Llama-4-Maverick, затем RL (GRPO) по coverage и exact-match tool IDs. Проверено ToolBench G3/G2, Gorilla, CRAFT, TaskBench. Метрика — exact match всего gold set, а не фактический успех задачи.

## Authors results

На 2124 инструкциях ToolBench G3 обученный Qwen3-8B даёт 41,5% exact match, 4B — 40,3%, лучший prompting baseline Llama-4-Maverick — 30,6%. На G2 точность заметно ниже; на TaskBench сильный Search-R1 baseline обгоняет обученный вариант. Перенос не универсален.

## Limitations

Gold labels прошли авторскую фильтрацию; corpus shift и retrieval miss опасны; обучение и его затраты не сравнивались с нашим MCP-набором; не доказаны downstream task quality и экономия total latency. Visibility никогда не подменяет authorization.

## Minimal offline experiment

100–200 held-out tools tasks: all-tools vs BM25 Top-K vs BM25+rerank и только затем trained selector. Измерить required-tool recall (особенно false omissions), task success, tokens, p95, GPU selection cost.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
