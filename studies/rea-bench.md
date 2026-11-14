# ReA-Bench — auditing responsible agent trajectories

[Структурированная запись и связи](../catalog/studies/rea-bench.md)

**Тип:** научный preprint и benchmark; [полный arXiv 2611.16493v1](https://arxiv.org/pdf/2611.16493v1), 12.11.2026; 50 страниц; SHA-256 6ead6b710dc427d12afa848929e8e0cc3fda6d958e7a6367b7e37e6bfd8e43f3.

**Маршрут:** Добавлен в карточки, P1, целевой project dsh-runtime для offline evaluation design; PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE.

Авторы выделяют шесть уровней риска в audit trajectories, включая пропущенные правила, скрытые эффекты и недостающие сведения дочерних агентов. Помимо recall нужен FPR по сложным законным действиям. В одном сравнении GPT-sol показал 88,5% recall при 54% false-positive rate на отобранных benchmark samples; Grok-high 71% при 5,5% FPR. Нельзя объявлять одну модель лучшим auditor по единственной метрике.

**Ограничения:** модельные суждения и построенные траектории, одна оценка на конфигурацию, перекосы risk и benign состава, отсутствие независимых целевых метрик DSH. [Обзор](../reviews/rea-bench/2026-11-14.md) · [матрица](../portfolio/2026-11-14/review.md).
