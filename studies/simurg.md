# SIMURG — монитор целостности потоковой генерации

- **Авторы:** Farid Aghayev и Elturan Ahmadbayli; [полный технический отчёт от 2026-08-24](https://github.com/doofzoff/SIMURG/blob/2831a92359cdaf1b38cc14f55e74251e09a91e0b/paper/simurg_paper.pdf), 13 страниц; [SSRN 7451269](https://ssrn.com/abstract=7451269); peer review не установлен.
- **Инженерный источник:** [SIMURG v1.0.4 @ 2831a92359cdaf1b38cc14f55e74251e09a91e0b](https://github.com/doofzoff/SIMURG/tree/2831a92359cdaf1b38cc14f55e74251e09a91e0b), 2026-09-21; [Apache-2.0](https://github.com/doofzoff/SIMURG/blob/2831a92359cdaf1b38cc14f55e74251e09a91e0b/LICENSE). Исходная закладка Telegram BK-011 от 15.09; эта ревизия позднее закладки.
- **Метод:** анализ повторов, символов и сигнатур текста в потоке, удержание начального буфера, оценки ансамбля, прерывание и повтор. Это не самостоятельная проверка истинности медицинских и иных утверждений.
- **AUTHOR_REPORTED:** PDF и более поздний README используют разные результаты; без проверки их нельзя смешивать. PDF: synthetic positives, 77/77 обнаружений, 0/42 clean false alarms; README: 78/80 и лишь один clean тестовый поток. Это не независимая оценка эффективности.
- **INDEPENDENTLY_VERIFIED:** в изолированном тесте исходная `_auroc` выдаёт 1.0 при равных оценках классов (независимый попарный oracle 0.5). При 50 одинаковых clean scores 0.99 `calibrate(alpha=0.02)` ограничивает порог 0.95 и классифицирует 0.99 как corrupt. Пять тестов sentinel прошли; искусственные повторяющиеся русский текст и SQL были ошибочно отмечены как corrupt. [Код эксперимента](../experiments/bk011-simurg/check-fixture.py).
- **Проекты:** `dsh-runtime`, `9router`, `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. `LAB_VERIFIED` относится только к перечисленным синтетическим случаям; `BLOCKED: MEASUREMENT_MISSING` для пользы на проектах; `NO_PRODUCTION_APPROVAL`.

[Полный обзор и матрица](../reviews/simurg/2026-11-04.md) • [предварительная матрица](../collections/telegram/preliminary-project-fit.md)
