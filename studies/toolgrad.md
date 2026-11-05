# ToolGrad — verified chain-first tool-use dataset generation

[Структурированная запись и связи](../catalog/studies/toolgrad.md)

**Original paper:** https://aclanthology.org/2026.findings-acl.950/; [complete PDF](https://aclanthology.org/2026.findings-acl.950.pdf).
**Primary version:** ACL 2026 Proceedings; 17 pages. **SHA-256:** `373e90c6049d46ea1e3aa19906f5b45f6a51123d37321d9e98eb856bd6d48144` (checked 2026-11-03; PDF binary not redistributed).
**Source type:** `PEER_REVIEWED_ACL_FINDINGS`. **Evidence:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_INDEPENDENTLY_REPRODUCED`.
**Historical first watch:** [15 Sep 2026](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md); [non-normative operator dispositions](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md). For Random Attention the earlier source is the [chronological archive index](../archive/dsh/knowledge/research/README.md).
**Historical closure:** [scientific review](../portfolio/2026-09-03--2026-09-15/review.md); [research-to-project matrix](../portfolio/2026-09-03--2026-09-15/project-fit.md).
**Editorial value / disposition:** 8/10; `P1_BOUNDED_TEST_GENERATOR` (research only, no production authorization).

## Methodology and sample

Answer-first generation: сначала в sandbox строятся работающие API chains с textual gradient feedback, затем синтезируется пользовательский запрос и expected output. Выбор базовых инструментов/верификация процедурными API executors; benchmarking против DFS query-first на ToolBench и single-turn BFCL v1/v2. Полный текст Findings of ACL 2026, страницы 19040–19056, DOI 10.18653/v1/2026.findings-acl.950, опубликован в июле; сентябрь — дата блога Google.

## Authors results (not local measurements)

Generation pass 99,8% против 63,8% DFS, средняя длина gold chain 3,4 против 2,1; 500 сгенерированных примеров использованы для SFT. Сравнения качества tool calls относятся к модельным benchmark, а не к DSH end-to-end task success.

## Limitations / transfer confounders

Обучение SFT и single-turn tool use; авторы явно исключают multi-turn agents (BFCL v3/v4), оставляют RL как future work. ToolBench judge только частично сверялся с людьми (8 queries × 12 model responses, два annotators). Для наших файлов и SQL APIs нужны чистые сбрасываемые инструменты, независимый state oracle и запрет destructive calls.

## Smallest discriminating experiment

8–12 safe synthetic tools, 100 verified chains длиной 2–6 действий в disposable env; сравнить ручные tests vs chain-first generator vs DFS. Отдельно validity of final state, redundant calls, coverage, tool/LLM spend.

## Project-fit decision

Методика верифицированной генерации tool chains и replayable regressions, не автоматическое обучение production модели.

**Gate:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE`. Owner gate and independent outcome oracle required before any code changes.
