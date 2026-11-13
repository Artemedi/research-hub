# Drift Inspector — Atomic Contribution Claims для анализа научных направлений

[Структурированная запись и связи](../catalog/studies/drift-inspector.md)

- **Первоисточник:** [EMNLP 2026, полный PDF](https://aclanthology.org/2026.emnlp-demos.13/); [код @6c643d6ebfaa771d01c743d921dac839dd771c40](https://github.com/Hamyrappy/drift-inspector/tree/6c643d6ebfaa771d01c743d921dac839dd771c40).
- **Доказательства:** полный текст/методика/результаты/limitations прочитаны; проверены авторский код и CSV основного корпуса. Часть вычислений подтверждена независимо, но полный upstream experiment и проектный A/B не воспроизводились.
- **Решение:** ACCEPT_BOUNDED / P1 для offline discovery; польза для портфеля NEEDS_EVIDENCE. Статья не заменяет full-text gate. MIT-код, CC BY 4.0 claim-данные — по документам авторов.

## Основной метод и результаты

LLM извлекает Atomic Contribution Claims (ACC) из аннотаций. SPECTER2, UMAP и HDBSCAN объединяют утверждения в темы; доля публикаций считается по уникальным статьям, не по количеству утверждений. Подтверждённый в опубликованном CSV эксперимент: 4 488 статей, 16 576 ACC, 80 кластеров, 5 980 noise claims (36,08%), по 748 работ на каждый год 2020–2025. Авторы сообщают 94,5% agreement LLM-judge с большинством человеческих оценок; это проверка соответствия аннотации, не истинности научных результатов. Онлайн-атлас 2018–2026 насчитывает 117 888 статей и 570 179 claims, но такой же human validation не прошёл.

## Блокеры

- 36,08% ACC остаются вне кластеров: нельзя автоматически отбрасывать редкие новинки.
- В [assign.py](https://github.com/Hamyrappy/drift-inspector/blob/6c643d6ebfaa771d01c743d921dac839dd771c40/src/acc/assign.py) ближайший центроид назначается без порога abstention; перенос на медицинские/DBA данные нуждается в отдельном тесте.
- В [аудите](https://github.com/Hamyrappy/drift-inspector/blob/6c643d6ebfaa771d01c743d921dac839dd771c40/artifacts/audit/extractor_ablation_JUDGE_FINDINGS.md) LLM-judge ablation остановилась на 14/600; нельзя утверждать равенство качества экстракторов.
- Abstract-only остаётся AUTHOR_CLAIM_FROM_ABSTRACT. Действующая [RESEARCH_POLICY](../RESEARCH_POLICY.md) требует полный текст для оценки научной достоверности; отсутствие полного текста — FULL_TEXT_UNAVAILABLE.
- Статистика описательная; состав конференций, неполный 2026 год и настройки кластеризации влияют на тренды.

**Подробный обзор:** [13 ноября](../reviews/drift-inspector/2026-11-13.md). **Применимость к проектам:** [документальная матрица](../portfolio/2026-11-13/source-project-fit.md).
