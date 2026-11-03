# BenchShield — reward-integrity instrumentation

**Original paper:** https://arxiv.org/abs/2609.11028; [complete PDF](https://arxiv.org/pdf/2609.11028v1).
**Primary version:** arXiv v1; 18 pages. **SHA-256:** `c0dba3c4aa89ec50e3453a61d4334c5d0ba7e29701fdb82183cccfc498e9b1d1` (checked 2026-11-03; PDF binary not redistributed).
**Source type:** `ARXIV_PREPRINT`. **Evidence:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_INDEPENDENTLY_REPRODUCED`.
**Historical first watch:** [15 Sep 2026](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md); [non-normative operator dispositions](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md). For Random Attention the earlier source is the [chronological archive index](../archive/dsh/knowledge/research/README.md).
**Historical closure:** [scientific review](../reports/2026-11-03-historical-gap-closure-2026-09-03-to-15.md); [research-to-project matrix](../reports/2026-11-03-project-mapping-september-gaps.md).
**Editorial value / disposition:** 9/10; `P1_EVAL_INTEGRITY_DESIGN` (research only, no production authorization).

## Methodology and sample

Модель конечного жизненного цикла reward-relevant действий, static phase-aware taint analysis и runtime instrumentation на стороне benchmark infrastructure. BenchShield Trajectories: 456 вручную согласованных траекторий, выбранных из более 31 000 публичных запусков на трёх benchmarks. Для экспериментальных пар использован pinned task + human-adjudicated exploit и matched honest trace.

## Authors results (not local measurements)

Авторы сообщили full-chain recall 77–100% против 23–94% для agentic scanner baseline; runtime accuracy 96% только среди покрытых verdict cells, coverage 87,5% (Table 4; 144 runnable cells). Доли 96% и 87,5% нельзя объединять в общую долю успешной защиты. Из 456 adjudicated trajectories 314 содержат reward hacking, это выборка для оценки, не его частота в production.

## Limitations / transfer confounders

Нужна instrumentation в контролируемой benchmark infrastructure; текущая schema fixed, semantics некоторых действий требует аудитора. Полнота событий не дана для произвольных external tools и multi-role private channels. Не гарантирует корректность конечного software artifact; не подтверждает уязвимость нашего DSH.

## Smallest discriminating experiment

Только isolated eval fixture: 20–30 trajectories с безопасными reward manipulation canaries. Сравнить baseline task success с proof of reward-input provenance, seal completeness, abstentions, false positives, runtime/tokens overhead. Публиковать только fake data.

## Project-fit decision

Индивидуальные проверяемые eval-артефакты и tool/run provenance; особенно полезно для регрессий agent skills и scientific tool benchmarks, не как общий security grant.

**Gate:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE`. Owner gate and independent outcome oracle required before any code changes.
