# Warp Skill Doctor — анализ сессий и предложения по навыкам

[Структурированная запись и связи](../catalog/studies/warp-skill-doctor.md)

- **Источник:** [официальная страница Warp](https://www.warp.dev/skill-doctor) и [открытый исходник Skill Doctor](https://github.com/warpdotdev/common-skills/tree/8792394ff1b655e0af451b8fabb68ef0cfcbd208/.agents/skills/skill-doctor); `warpdotdev/common-skills@8792394ff1b655e0af451b8fabb68ef0cfcbd208`, commit 2026-10-20, [MIT](https://github.com/warpdotdev/common-skills/blob/8792394ff1b655e0af451b8fabb68ef0cfcbd208/LICENSE). Инженерный инструмент, не peer-reviewed исследование. Telegram BK-019 от 20.09; проверенная версия позднее закладки.
- **Метод:** сбор сокращённых локальных транскриптов, качественные LLM-оценки по четырём рубрикам, формула итогового балла, предложения diff для навыков и локальный HTML. Вероятная полезность гипотетическая; точность оценок и изменений независимо не подтверждена.
- **Проверено:** в изолированном окружении 37 upstream unit tests прошли. Дополнительный [тест синтетических путей](../experiments/bk019-skill-doctor/attribution-fixture.py) показал принятие несвязанного каталога с совпадающим компонентом имени как принадлежащего проекту; это риск неверного отбора сессий. Реальные чаты, агентные вызовы и приватные данные не открывались.
- **Проекты:** `agent-skills`, `agent-config`, `dsh-team-context`; `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. `LAB_VERIFIED` относится только к синтетическим unit/attribution проверкам; улучшение навыков не измерено; `NO_PRODUCTION_APPROVAL`.
- **Подробно:** [обзор и матрица](../reviews/warp-skill-doctor/2026-11-04.md).
