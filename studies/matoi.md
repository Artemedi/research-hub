# Matoi

**Историческая запись:** [12–19 октября 2026](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md). **Дата full-text review:** 2026-11-03. **Уровень:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_REPRODUCED / PROPOSED_ONLY`.

**Сводный отчёт:** [методы, результаты, ограничения](../portfolio/2026-10-12--2026-10-19/review.md). **Проекты:** [явная матрица соответствия](../portfolio/2026-10-12--2026-10-19/project-fit.md).

## Методология, результаты, caveats и безопасный эксперимент

**Полный источник:** https://arxiv.org/abs/2610.21394; [PDF v1](https://arxiv.org/pdf/2610.21394v1), 55 страниц, SHA-256 `ff01afd79911ebee7a431a4bc380dfa66bc819d541f74ca5ece14f8add22fc9f`. **Авторский технический preprint, не peer reviewed.**

**Методика.** Схема отделяет (1) доказательство возможных последствий, (2) **действующую** authority+grant, (3) durable occurrence/reservation с явным unknown при remote commitment. Семантическая модель ограничена конечными ветвями, коллекциями и negative lookups; следует текущее право на эффект, а не кешированное «разрешение». Испытания: оригинальные JS/Python checker, paired matched-wire cost и синтетический Banking scenario.

**Результаты авторов.** Matched-wire на **144 authored inputs / 1440 cells** с одинаковой compact serialization показывает скромное **−3,49% lifecycle cost в JS** и **−1,79% в Python** относительно полного recheck; ряд статистических интервалов пересекает нейтральное значение. Отдельная Banking mapping покрывает лишь **5/16** benign user plans и **7/9** attack plans; пять разрешённых synthetic transfers и 35 скрещиваний attack/policy были обработаны в описанных ограничениях.

**Ограничения.** Авторский `Discussion and Limitations` прямо исключает произвольные tools, атомарные remote side effects, end-to-end production superiority, full mediation без инструментирования receivers. Benchmark — scripted synthetic tools, не реальный банк и не автономные агенты; hidden writer, provider duplication и поздний remote commit сохраняют риск. Отдельные эксперименты с разными cost boundaries **не** суммировать в одно «ускорение».

**Проверяемое применение.** Только как reference при проектировании границ actor/tool authorization: таблица «requested effect / allowed now / observed evidence / durable occurrence». Offline 20 synthetic actions с revoked grant, queue/callback, uncertain retry; baseline `always fresh` против selective evidence reuse, корректность fail-closed и полный validation overhead. Не заменять существующий authorization gate.

**Оценка применимости:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE`; у внешнего проекта `AUTHOR_STATED / NEEDS_SOURCE_CODE`. Source-level seam или measured benefit не подтверждены.
