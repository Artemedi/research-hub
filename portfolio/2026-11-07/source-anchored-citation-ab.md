# Цитирование по полным arXiv HTML: независимый claim-oracle и рой ZCode

**Дата:** 07.11.2026. Продолжение [контрпроверок III](target-counterchecks-round3.md) и [IV](target-counterchecks-round4.md). Проверялась **точность соотнесения утверждения с выбранной ссылкой**, а не научная истинность результатов работ, не весь paper-to-agent workflow и не производственная система.

## Первичные полные тексты и закрепление доказательств

| Первичный источник | Содержимое/проверка полноты | SHA-256 полученного HTML |
| --- | --- | --- |
| [HTN-Orchestrate, arXiv:2610.22195](https://arxiv.org/html/2610.22195) | Доступны `3 Method`, `4 Empirical Evaluations`, Appendix A с `Experimental Details` и `Evaluation Judges`. **Отдельного заголовка `Limitations` нет**: это ограничение полноты научной экспертизы. | `db0746b460b880aab51e9a9d3878a32ae6690bacc3807774ba581963b970f7db` |
| [Agent Mosaic, arXiv:2610.30418](https://arxiv.org/html/2610.30418) | Доступны `3 Benchmark and Experimental Design`, `4 Human Annotation and Automated Measurement`, `5 Analysis and Results`, явный `Limitations`. | `80b01bba9c64a4bee86dec3badaccc39e8e801121c0610544affb5e67cfe190a` |

Для каждой работы использован **полный легальный первоисточник HTML**, а не abstract/пересказ. Однако из них вручную выбрано **только восемь опорных абзацев** с разделами/HTML ID и SHA-256; полный Method/Results/Limitations review обеих работ заново **не выполнялся**. В репозиторий не копируются полные тексты и абзацы; публикуются только хеши, URL, идентификаторы разделов, утверждения эксперимента и результаты.

**Целевой источник:** чистая архивная копия `Artemedi/dsh-paper2agent@6d82a42175a71d3327b773df88f1da0707efe43c`, извлечённая `git archive` в `TemporaryDirectory`, без локальных незакоммиченных правок проекта.

## A/B и независимый от модели oracle

Восемь source-anchored пассажей: HTN — размер выборки BrowseComp, типы независимого judge, сравнительные результаты, использование prerequisite результатов; Mosaic — синтетический benchmark, факторный дизайн, human annotations, ограничения live-vs-simulation. По каждому вручную составлено **четыре утверждения**, с исходной цитатой в неизменяемом target snapshot: буквальное следование, корректная переформулировка и два отрицательных контроля (подмена числа, объекта, инверсия, неподтверждённое расширение).

Gold labels заданы **исследователем до обращения к ZCode**, не совпадением с выводом модели. Это независимый от ZCode, но не независимый межаннотаторный oracle. Реальный `App.submit_analysis()` целевого исходника получал всю цепочку project+research citation по одной source line.

| Стратегия | 16 подтверждённых | 16 неподтверждённых | Интерпретация |
| --- | ---: | ---: | --- |
| A: реальный `submit_analysis` | 16/16 приняты структурно | 16/16 приняты структурно | **Это не semantic claim-checker**, а проверка scope/диапазона |
| B: внешний literal-substring auto-pass | **5/16** автоматических pass | **0/16** ложных pass | Выраженно низкий recall; часть буквальных фраз не совпадает из-за HTML/math нормализации |
| C: ZCode source reviewer | **16/16** правильно | **0/16** ложных pass | Модельно-опосредованная проверка выбранной цитаты |
| D: согласованное мнение двух ролей ZCode | **16/16** правильно | **0/16** ложных pass | Совпадающие ответы двух ролей одной модельной семьи |

**Рой:** `source_reviewer` и `counterexample_critic`, четыре batch × две роли = **8/8 COMPLETE**, 0 timeout, физическая конкуренция 1, checkpoint после каждого вызова; все 32 claims проверены. Модель `glm-5.3-flash`, 6 008 reported input tokens + 6 193 output tokens + 7 552 cache-read input tokens; суммарная длительность вызовов **137,24 с**, медиана **16,85 с**. Денежная стоимость, статистическая погрешность на случайной выборке и production latency **не установлены**.

Взаимное согласие двух ролей **не является независимым научным доказательством**, поскольку обе роли используют одну модель. Область теста: восемь коротких специально подобранных passages; не исследованы сложные многосоставные claims, интерпретация таблиц/уравнений, выводы через разные источники, неполные цитаты, adversarial prompt injection внутри HTML и медицинские записи.

**Вывод:** `ACCEPT_BOUNDED_REAL_SOURCE_CITATION_AB`, `REWORK_SEMANTIC_GATE_BEFORE_ROLLOUT`, `NO_NEW_FIT`, `NO_PRODUCTION_APPROVAL`. Это подтверждает возможность semantic review на узком корпусе реальных источников, но **не** обоснование автоматического опубликования цитат и тем более не научный ACCEPT самих работ.

## Воспроизведение

[Source-anchored скрипт](../../experiments/research-portfolio/2026-11-07-source-anchored-citation-ab.py) / [полные агрегаты, anchors, 32 оценки и checksum каждого model-вызова](../../data/results/research-portfolio/2026-11-07-source-anchored-citation-ab.json). Получить из официального источника HTML в локальный `PAPER_HTML_DIR` с именами `2610.22195.html` и `2610.30418.html`; проверить точные SHA-256, иначе `FULL_SOURCE_HASH_MISMATCH`, без silent fallback на новую версию. Указать `P2P_SOURCE` с pinned `origin/main`, авторизованный `ZCODE_WRAPPER`, локальный `CHECKPOINT`, путь `OUTPUT`. Все промежуточные полные тексты и модельные outputs с содержанием цитат хранятся вне публичного Git; целевые исходники не изменяются.

**Следующий gate:** сторонняя слепая разметка порядка сотен claim↔evidence пар из различных полных научных работ, разделение семантического и фактического oracle, adversarial/multi-hop cases, confidence/abstention, повторные прогоны и стоимость verified completion. Без этого broad fit или внедрение не предлагается.
