# Goal-Aware Dynamic Multi-Agent Collaboration (GAD)

**Primary source:** https://arxiv.org/abs/2610.39193 ; [full PDF v1](https://arxiv.org/pdf/2610.39193v1).
**Original PDF SHA-256:** 5338392c1e65f133e460c8d33adf826872fb5fd45abdfb6240ee021762cfac93. The PDF itself is not redistributed.
**Full-text review date:** 2026-11-03. **Evidence:** FULL_TEXT_REVIEWED_2026-11-03 (original PDF methods/results/limits inspected; *not* locally reproduced).
**Report:** [weekly source review](../reports/2026-11-03-full-text-review-2026-10-27-to-11-02.md). **Project applicability:** [explicit matrix](../reports/2026-11-03-project-mapping-2026-10-27-to-11-02.md).
**Editorial valuation / effort:** 9/10 ; 7/10. **Proposed disposition:** P2_ACCEPTANCE_DAG; no implementation approval.

## Methodology

Динамический DAG многоагентных subtasks, сохранённые original goal/subgoal/acceptance conditions, раннее промежуточное verification. К каждому worker передаются только доказательства от выполненных dependencies, а не вся смешанная multi-agent история. Испытания Terminal-Bench 2.1 и SWE-bench Pro Hard-51, несколько backbones.

## Authors results

На Terminal-Bench 2.1 Claude Sonnet 4.6 GAD 71,9% против 65,2% у сильнейшего MAS baseline; Qwen3.7-Plus 64,0% против 57,3%. На SWE-Pro результаты тоже положительные для отдельных cells, но стоимость высока.

## Limitations

До трёх workers, большие лимиты calls, отдельный semantic verifier от LLM (не независимый test oracle), контекст и budget не всегда нормированы. Нельзя обещать эти выигрыши при другом времени/цене API, автономности и зависимости задач.

## Minimal offline experiment

30–50 coding/research DAG tasks: existing team flow vs explicit acceptance conditions vs dependency-scoped evidence. Test/build oracle, false accepts, rereads, tokens, wall time and retries.

**Project fit:** PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE, not VERIFIED_FIT. For colleague project AUTHOR_STATED / NEEDS_SOURCE_CODE.
