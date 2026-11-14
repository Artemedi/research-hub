# Static analysis of code-library hallucinations — Python detection and mitigation limits

[Структурированная запись и связи](../catalog/studies/static-library-hallucinations.md)

**Тип:** рецензируемая научная работа, TMLR 10/2026; [полный PDF arXiv 2604.07755v3](https://arxiv.org/pdf/2604.07755v3), версия от 06.11.2026; 24 страницы; SHA-256 e87497abdfc08f6aca58580a642d5c3188bc4a3bd2d5884f68c55032214996c6.

**Маршрут:** Добавлен в карточки, P2/P1 prevention-evaluation для dsh-paper2agent, PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE, авторская методика изучена, код/модели и benchmark нами не запускались.

Работа оценивает Mypy, Pyright, grammar constraints и repair на Python library hallucinations по DS-1000, ODEX, BigCodeBench. Авторы показывают, что обнаружение (даже до 85% на отдельных наборах) не означает коррекцию; ручная проверка снижает верхнюю оценку истинного обнаружения до примерно 77% из-за ложных срабатываний. Repair не устранил hallucinations устойчиво, а constrained decoding помог не во всех benchmark.

**Ограничения:** только Python, динамические типы и контроль потока, перенос на .NET/Roslyn не доказан. Не использовать статический анализ как независимое доказательство корректного авторского API. [Подробный обзор](../reviews/static-library-hallucinations/2026-11-14.md) · [матрица](../portfolio/2026-11-14/review.md).
