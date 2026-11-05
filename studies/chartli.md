# Chartli — числовые графики в терминале

[Структурированная запись и связи](../catalog/studies/chartli.md)

- **Источник:** [ahmadawais/chartli @3b39b97aeb564646437b2b7501b60541994d7575](https://github.com/ahmadawais/chartli/tree/3b39b97aeb564646437b2b7501b60541994d7575), v1.0.0; README и Rust manifest указывают Apache-2.0, отдельного LICENSE в снимке нет. BK-050 / 16.10.
- **Назначение:** отображение численных рядов в ASCII, Unicode, Braille, SVG и других формах; визуализация, не новая диагностическая модель.
- **Тест:** synthetic fixture оригинального TypeScript parser/normalizer показал пропуск первой строки в scientific notation, нулевую подстановку отсутствующей ячейки и NaN на ошибочном числе; положительный контроль прошёл. CLI, SVG и downstream-проекты `NOT_RUN`.
- **Проекты:** `akuzlogparser` и `akuz-schema-inventory` — узкие гипотезы presentation diagnostics, `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`; вход должен строго валидироваться и сохранять единицы и независимые сырые значения. [Обзор](../reviews/chartli/2026-11-04.md), `NO_PRODUCTION_APPROVAL`.
