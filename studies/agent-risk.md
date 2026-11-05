# agent-risk

**Историческая запись:** [12–19 октября 2026](../archive/dsh/knowledge/research/2026-10-19-deepseek-harness-research-watch-reconstructed.md). **Дата full-text review:** 2026-11-03. **Уровень:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_REPRODUCED / PROPOSED_ONLY`.

**Сводный отчёт:** [методы, результаты, ограничения](../portfolio/2026-10-12--2026-10-19/review.md). **Проекты:** [явная матрица соответствия](../portfolio/2026-10-12--2026-10-19/project-fit.md).

## Методология, результаты, caveats и безопасный эксперимент

**Полный источник:** https://arxiv.org/abs/2610.16280; [PDF v1](https://arxiv.org/pdf/2610.16280v1), 43 страницы, SHA-256 `2b6b107ed057dbfe7b7133143fe1bd7beef1178700b22bbc7af23caac204d21e`.

**Методика.** Формальная схема оценки изменённой gate/model policy по уже зарегистрированным эпизодам: повторное вычисление решения до **first deviation**; случаи `agree`, `stop` и `continue` требуют соответственно известного исхода, объявленной стоимости stop либо данных о продолжении/сохранённого state/bounds. Доказательства условны по предположениям `A1/A2` (неизменённая среда и отсутствие распознавания новой политики). Эксперименты в bash sandbox: лог 7200 эпизодов, paired live runs, targeted restoration/rerun.

**Результаты авторов.** Исходный лог не позволил принять решение ни об одном из двух retry gates; адресный повтор только веток после first deviation дал сопоставимые с live решения **примерно при половине agent calls** постфактум выбранного live теста. Без per-step harm time предел риска для stop gate в примере вырос **до 2,5 раза**.

**Ограничения.** Авторский `Limitations`: конечные пространства путей, независимость эпизодов для статистических гарантий, честные модели из ограниченной семьи, восстановление только проверенного файлового дерева, stop losses объявлены, но не проверены, тестирование aware-of-oversight остаётся открытым. Из логов нельзя честно вывести counterfactual после никогда не виденного отказа.

**Проверяемое применение.** 20–40 offline agent trajectories с deterministic state snapshot и synthetically injected gate changes: log-only, full rerun, targeted rerun. Мерить согласие с live oracle, uncertain mass, harm-before-stop и CPU/token cost. До owner gate — только аналитический replay, не самостоятельная политика допуска.

**Оценка применимости:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE`; у внешнего проекта `AUTHOR_STATED / NEEDS_SOURCE_CODE`. Source-level seam или measured benefit не подтверждены.
