# Microsoft Skill Recorder — запись действий и создание навыка

[Структурированная запись и связи](../catalog/studies/microsoft-skill-recorder.md)

- **Источник:** [microsoft/skill-recorder](https://github.com/microsoft/skill-recorder/tree/505c97ae47be5642c0e1b44ebb8d1c1530c298fa), release package 0.8.0, commit `505c97ae47be5642c0e1b44ebb8d1c1530c298fa` от 2026-11-02, MIT. BK-022 / 25.09 — историческая ссылка; рассмотренная версия позднее закладки. Инженерное приложение, не paper.
- **Метод:** записать экран/события и необязательную речь, собрать шаги, передать выбранные данные Copilot для анализа и предложить редактируемый skill или automation. **Analyze отправляет данные во внешнее облако**; запись до анализа хранится локально согласно README.
- **Проверено:** 14 независимых от GUI тестов structured PII и disclosure прошли; на синтетическом русском медицинском описании структурный детектор PII не вернул совпадений, тогда как email-контроль сработал. Это только отдельный слой, не end-to-end тест всей redaction-системы. В исходном пути при ошибке общего сканирования текст может идти без маскирования, а кадры удерживаются.
- **Проекты:** `agent-skills`, `agent-config`, `dsh-team-context`; `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. `LAB_VERIFIED` — только синтетические проверки, совместимость рабочих сред и качество генерации не установлены; `NO_PRODUCTION_APPROVAL`.
- [Полный обзор и матрица](../reviews/microsoft-skill-recorder/2026-11-04.md) · [воспроизводимый fixture](../experiments/bk022-skill-recorder/pii-fixture.mjs).
