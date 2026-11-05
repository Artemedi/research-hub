# Журнал миграции

| Этап | Состав | Состояние | Проверка |
| --- | --- | --- | --- |
| Пилот | BenchShield, REA, Unreal Agent, RRSI, Harness² | PUBLISHED | Пять Study; 90 исторических/current assessments REA; 20 тестов и CI PASS на ff6ee77 |
| 01 | Hyra 2.0, Vercel Agent Desktop | PUBLISHED | Фрагмент подготовлен gpt-6-luna; проверяющий сверил source pins, article hash, ограничения и импортировал три полные матрицы по 45 строк. 135 новых assessments, два поколения Desktop с explicit supersedes; 1 scoped GUI experiment. 22/22 локальных теста PASS; generation/check/diff PASS |

Нормализовано после проверки партии 01: 7/81 карточек; legacy: 74. Полнота Study, project-fit и Experiment records учитывается отдельно: три источника с полными импортами матриц, 225 исторических/current assessments, 135 текущих пар источник–проект, два структурированных bounded experiments. 45 страниц проектов не означают полноту их исследовательских связей.

Исходные обзоры, матрицы, ledger, архив и код экспериментов в партии 01 не переписывались. Изменены только навигационные ссылки двух карточек, канонические entities, производные страницы и контракт для уже существующих статусов ARCHITECTURAL_REFERENCE_CANDIDATE / FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED. Это перенос прежних выводов, не новые эксперименты.

Проверка сохранности: все 153 ранее существовавшие записи сущностей и прежние current pointers совпали с исходной версией. Постпубликационная сверка проводится по Git blob hashes; CI — [Repository integrity](https://github.com/Artemedi/research-hub/actions).
