# BenchShield — reward-integrity instrumentation

[Структурированная запись и связи](../catalog/studies/benchshield.md)

**Original paper:** https://arxiv.org/abs/2609.11028; [complete PDF](https://arxiv.org/pdf/2609.11028v1).
**Primary version:** arXiv v1; 18 pages. **SHA-256:** `c0dba3c4aa89ec50e3453a61d4334c5d0ba7e29701fdb82183cccfc498e9b1d1` (checked 2026-11-03; PDF binary not redistributed).
**Source type:** `ARXIV_PREPRINT`. **Evidence:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_INDEPENDENTLY_REPRODUCED`.
**Historical first watch:** [15 Sep 2026](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md); [non-normative operator dispositions](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md). For Random Attention the earlier source is the [chronological archive index](../archive/dsh/knowledge/research/README.md).
**Historical closure:** [scientific review](../portfolio/2026-09-03--2026-09-15/review.md); [research-to-project matrix](../portfolio/2026-09-03--2026-09-15/project-fit.md).
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


## 2026-11-04 — собственный offline lifecycle-evidence эксперимент

**Протокол:** [BenchShield reward-integrity replay](https://github.com/Artemedi/research-hub/blob/main/reviews/benchshield/2026-11-04.md), [выполненный скрипт](../experiments/2026-11-04-benchshield-reward-integrity-replay.py), [агрегаты JSON](../data/results/benchshield/2026-11-04.json). **Статус:** `METHODOLOGY_REPLAY_VERIFIED / AUTHORS_CODE_NOT_RUN / NO_DSH_INTEGRATION`.

**Что измерено:** отдельная Python-модель reward-relevant lifecycle, **не оригинальный BenchShield**. Сгенерировано 100 траекторий (10 классов по 10); `reported_reward` доверчивого evaluator указывал PASS в **90**, значение output совпало с независимым oracle в **60**. Инфраструктурный проверяющий классифицировал **30 CLEAR, 30 VIOLATION, 40 ABSTAIN**. Из 40 намеренно смоделированных нарушений 30 доказаны записью/чтением защищённых ресурсов; ещё 10 semantic attacks остаются `ABSTAIN`. Статическая достижимость защищённых путей была в **35** траекториях, включая 5 честных без использования пути. Среди намеренно легитимных примеров не обнаружены ложные обвинения, но это **сконструированная выборка**.

**Проверено отрицательными контролями:** изменение журнала после подписи отклоняется как unverifiable, санкционированное изменение grader при preflight не классифицируется как agent attack, подтверждённый post-handoff write нарушает границу. Повторный запуск (100 случаев) и альтернативный seed (80 случаев) — PASS. LLM, авторская TLA+/static taint/runtime реализация, production evidence, cost и actual DSH verifier **не запускались**. Метрики из научной статьи **не воспроизведены**.

**Граница переноса:** концепция `reported_reward != credible_reward` подходит системе оценивания DSH; обязательны отдельные proof-of-capture, grader/oracle hash, manifest revision, actor/phase/op/path, nullable evidence outcome и `ABSTAIN`. Недостаточно только score или текста tool/agent transcript. **Решение:** `EVIDENCE_BOUNDARY_PRINCIPLE_ACCEPTED / NO_AUTOMATIC_RUNTIME_INTEGRATION`.
