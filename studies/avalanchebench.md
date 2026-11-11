# AvalancheBench — latent-world recovery and cascading analytical errors

- Источник: [arXiv:2605.24183v2](https://arxiv.org/html/2605.24183v2); v1 2026-05-22, существенное обновление v2 2026-11-04.
- FULL_TEXT_VERIFIED: авторский HTML, разделы 2–5 и ограничения; [код и данные](https://github.com/snowflake-labs/avalanchebench/tree/38cf3234b5c0bdbb649c67bc0ef14908d1e27dc5), Apache-2.0, release 0.1.0.
- Метод: 3 синтетических многовопросных задания, 58 вопросов, latent-world ground truth, аналитическая fidelity, денежная стоимость и CATC, анализ ошибок и зависимостей.
- Результаты авторов: лучший macro fidelity 0.82; 51.5% потерянных баллов из-за интерпретации требований, 29% из-за повторного использования чужого ошибочного результата. Не переносить эти проценты на AKUZ.
- Ограничения: синтетика, Snowflake/AISQL и внешние модели, 3 повтора, LLM-judge недетерминирован, latency не измеряли, локального PostgreSQL adapter в релизе нет.
- PROJECT_PROFILE_MATCH: [Wiki_PG](https://github.com/Artemedi/project-registry/blob/421268e5c60fd1b5f37bd69a84b923ff28ce3e86/projects/01-dba-akuz/Wiki_PG/PROJECT.md). Реальный локальный benchmark seam: [Wiki_PG@d55721b:controlled_retrieval_benchmark.py:46-73](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/controlled_retrieval_benchmark.py#L46-L73); это retrieval benchmark, НЕ доказательство готового multi-question evaluator.
- Минимальный A/B: 12 обезличенных синтетических многосоставных вопросов; A — существующий pipeline, B — проверка shared intermediate facts по oracle и запрет reuse без provenance. 3 повтора, exact-answer accuracy, число propagated errors, tokens и p95. Лимит 4 CPU / 8 GiB, без Snowflake/production. Gate: ноль регрессий correctness и ≥20% относительного снижения propagated errors при p95 ≤115% baseline.
- Ценность 8/10; сложность 5/10 для локального теста, 9/10 для переноса официального бенчмарка.
- Вердикт: ACCEPT_RESEARCH_ONLY / PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE; внедрение не разрешено. [Недельная матрица](../reports/2026-11-11-portfolio-research.md).
