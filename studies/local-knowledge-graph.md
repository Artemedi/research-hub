# Local Knowledge Graph — граф шагов рассуждения модели

[Структурированная запись и связи](../catalog/studies/local-knowledge-graph.md)

- **Источник:** [punnerud/Local_Knowledge_Graph@58fce402c7d15a3f5abcc8d0b1e920c1be5071b5](https://github.com/punnerud/Local_Knowledge_Graph/tree/58fce402c7d15a3f5abcc8d0b1e920c1be5071b5), Morten Punnerud-Engelstad, commit 2026-08-13, package `mpe-lkg` 0.9.1. BK-024 / 25.09; инженерный проект, не peer-reviewed paper.
- **Лицензия:** [mpedb License 1.0](https://github.com/punnerud/Local_Knowledge_Graph/blob/58fce402c7d15a3f5abcc8d0b1e920c1be5071b5/LICENSE), не OSI-approved; содержит условия для крупных групп. Оценка применимости условий требует отдельной проверки владельца.
- **Метод:** граф строится из собственных шагов модели, cosine similarity используется при выборе пути для синтеза ответа; RDF различает embedding, exact и opinion. Это не готовый индекс документов/RAG и similarity не доказывает факт или причинность.
- **Проверено:** 21 upstream graph tests прошли offline. На искусственном графе исходный `strongest_path` использовал обратное направление заданного ребра; отдельный fixture показывает различие максимума произведения и максимума геометрического среднего. Выводы относятся к заданным graph API inputs, не к частоте в настоящих ответах.
- **Проект:** `sequential-rca` — сравнительный research candidate по trace/evidence графу; `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. `LAB_VERIFIED` — только два synthetic графа и 21 тест; качество RCA, retrieval, LLM и польза `NOT_MEASURED`; `NO_PRODUCTION_APPROVAL`.
- [Обзор и матрица](../reviews/local-knowledge-graph/2026-11-04.md) · [воспроизводимый fixture](../experiments/bk024-local-knowledge-graph/paths-fixture.py).
