# Аудит закрытия 83 карточек: происхождение обзоров, оставшиеся доказательные барьеры

**Дата:** 07.11.2026. Контрольный исходный `Artemedi/research-hub@cf3e5291da1452751500131e5c6817c3f325a456`, `Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`. Это отдельный слой учёта портфеля, **не массовое научное повышение статусов**, не разрешение на внедрение. Ранее завершённые работы [SIMURG](../../reviews/simurg/2026-11-07-hash-stability.md) и [Chartli](../../reviews/chartli/2026-11-07-svg-validation.md) не запускались повторно.

## 1. Что действительно найдено во всех 83 источниках

[Машинная матрица 83 × review provenance](../../data/results/research-portfolio/2026-11-07-evidence-coverage-83.json) и [воспроизводимая инвентаризация](../../experiments/research-portfolio/2026-11-07-evidence-coverage-83.py) сверяют **все 83 canonical `studies/*.md`** без `INDEX.md`, находят реальный локальный обзор, фиксируют SHA-256 исходной карточки и самого документа, тип ссылки и отметки ограничения **как текст, а не как новый вердикт**.

| Исходная форма доказательств | Карточек | Ограничение |
| --- | ---: | --- |
| Отдельный датированный `reviews/<source>/...` | **51** | Наличие файла не гарантирует independent replication |
| Полный разбор включён в еженедельный `portfolio/.../review.md` | **30** | Нет необходимости дублировать обзор в новом per-card файле |
| Исторический полноценный source review в `archive/dsh/knowledge/research/` | **1** | `self-replicating-prompt-injections`, архив — read-only |
| Датированный обзор под историческим alias | **1** | `unreal-agent-bk025` → `reviews/unreal-agent/2026-11-06-source-audit.md` |
| **Локальный документ обзора найден** | **83/83** | Это **documentary provenance**, не 83 научных `ACCEPT` |

Особенно важно: ранее встречавшаяся цифра **«32 карточки без отдельного review»** не равна 32 непроверенным исследованиям. Все 32 имеют подтверждённый конкретный путь в существующей истории. В частности, `red-teaming-auto-mode` имеет полноценные v1 appendix notes в самой карточке и [историческом недельном обзоре](../2026-09-03--2026-09-15/review.md), а `unreal-agent-bk025` — source audit под нормальным названием `unreal-agent`.

Проверка **не** доказывает, что каждая старая оценка методологии верна; это факт документальной полноты по текущему реестру, позволяющий перейти от массового чтения к предметным `NEEDS_EVIDENCE`, без повторения 83 статей.

## 2. Восемь других полных научных HTML — новые source pins

Из исходных карточек отобраны **8 разных работ**, не используемых в 20-task Claude Swarm пилоте. Получены оригинальные арxiv HTML конкретных версий, SHA всех полных файлов проверен до извлечения трёх ограниченных разделов. Авторские методы/результаты извлечены как публичные текстовые excerpt **только для советующих ролей**, сами полные статьи не копировались в репозиторий. [Сценарий выделения](../../experiments/research-portfolio/2026-11-07-eight-source-packets.py), [все SHA, версии и заголовки](../../data/results/research-portfolio/2026-11-07-eight-source-manifest.json).

| Работа | Методы и результаты источника | Настоящий остающийся gate | Текущая диспозиция |
| --- | --- | --- | --- |
| [Agent Risk, 2610.16280v1](https://arxiv.org/html/2610.16280v1) | Risk specification / approval gates / sandbox trace comparisons; доказательность прежних логов для policy change зависит от предпосылок и контрфактических исходов | Только неисполняемый counterfactual replay с независимыми исходами и точным source path проекта | `FULL_TEXT_PREVIOUSLY_REVIEWED / NOT_REPLICATED` |
| [Agentic Self-Awareness, 2610.19226v1](https://arxiv.org/html/2610.19226v1) | Know–act–hold, парные feasible/blocked задания, отдельная оценка false abstention | Анонимные синтетические пары с независимой task-authority рубрикой и blind judge; не выводить subjective awareness | `FULL_TEXT_PREVIOUSLY_REVIEWED / NOT_REPLICATED` |
| [MemScope, 2610.21170v1](https://arxiv.org/html/2610.21170v1) | Локальная правка memory provider по diagnostic evidence; GAIA/xBench в авторской оценке | Held-out raw trace/patch regression, tool budget и multi-task contamination; инструмент автоподбора ограничений не нашёл явный `Limitations` header — **не утверждать, что ограничений у статьи нет** | `FULL_TEXT_PREVIOUSLY_REVIEWED / NOT_REPLICATED` |
| [HarnessSecurity-Bench, 2610.07639v1](https://arxiv.org/html/2610.07639v1) | Изолированные Docker trials, функциональный и security oracle, часть решений принимает LLM reviewer | Отдельный deterministic oracle для эффектов и false approvals, без опасных живых действий | `FULL_TEXT_PREVIOUSLY_REVIEWED / NOT_REPLICATED` |
| [Matoi, 2610.21394v1](https://arxiv.org/html/2610.21394v1) | Effect identity, авторизация, checked reuse, scheduler, собственные локальные benchmarks | Внешний verifier и доказательство authority checks в целевом runtime, без новой all-purpose транзакционной системы | `FULL_TEXT_PREVIOUSLY_REVIEWED / NOT_REPLICATED` |
| [Poisoned Skills, 2610.37738v1](https://arxiv.org/html/2610.37738v1) | Конфигурационные Markdown-файлы как supply-chain input; авторская оценка нескольких моделей | Только безопасные фикстуры доверенных/недоверенных skills и происхождения контента; **не** распространять атакующие payloads | `FULL_TEXT_PREVIOUSLY_REVIEWED / NOT_REPLICATED` |
| [Trust Region Injection, 2610.38867v1](https://arxiv.org/html/2610.38867v1) | Изменение позиции недоверенного текста влияет на авторские ASR; `trust region` — наблюдаемый эффект, **не** измерение внутренних убеждений модели | Изолированные benign boundary/role handling controls, без переносимых атак и production разрешений | `FULL_TEXT_PREVIOUSLY_REVIEWED / NOT_REPLICATED` |
| [Red-Teaming Auto Mode, 2609.19587v2](https://arxiv.org/html/2609.19587v2) | Мониторы действий, 4000 benign replay actions, более дорогой multi-context monitoring | Предыдущий источник был **v1**; v2 отличается в Methods/Results, но нет доказательства текущего дефекта в наших агентах. Нужны отдельные синтетические role/compaction/authorization отрицательные проверки | `V2_SOURCE_RECHECKED / NO_NEW_TARGET_BUG_CLAIM` |

**Ограничения материала:** автоматическая вырезка отдельных HTML секций может взять слишком позднюю «Method» часть (например, Matoi) и пропустить размеченные limitations (MemScope). Источник **полностью доступен**, но модельному review передавались лишь excerpts; это не новая полная независимая экспертиза каждой статьи. Полнота ранее выполненных первичных обзоров остаётся отдельно подтверждаемым историческим основанием.

## 3. Фактический рой и независимая проверка его отказа

Были запланированы **4 source batches × 2 роли ZCode**, `source_grounder` и `method_falsifier`, физическая конкуренция **1**, без инструментария, вход — только короткие публичные арXiv passages, без registry `PROJECT.md`, приватных исходников, секретов, медицинских и SQL production данных. Никакие gold-метки и production rights модели не передавались.

На реальном провайдере первая роль истекла по **52 s**; следующие две завершились ненулевым exit code. По заранее заданному правилу **3 последовательных отказа → fail closed** исполнение прекращено: **3 попытки, 0 COMPLETE, 5 ролей не запускались**. [Точные receipts, elapsed/exit/sha](../../data/results/research-portfolio/2026-11-07-eight-source-zcode-advisory.json). [Независимый oracle](../../experiments/research-portfolio/2026-11-07-eight-source-zcode-oracle.py) и [машинный вывод](../../data/results/research-portfolio/2026-11-07-eight-source-zcode-oracle.json) подтвердили 8 SHA полного материала, 0 проверенных модельных цитат, 3 `BLOCKED_PROVIDER`. Утверждать, что «совет согласился», здесь **фактически невозможно**. Дальше использовать собранные материалы напрямую, не повторять ошибки провайдера ради фиктивной приёмки.

## 4. Точечная независимая инженерная проверка Hyperresearch

Отдельно выбрана уже существующая карточка [Hyperresearch](../../studies/hyperresearch.md), поскольку у неё до этого были независимые синтетические контрпримеры citation triage, но не исполнялись два upstream claim/source-ranking test suites на текущем закреплённом исходнике.

На [`jordan-gibbs/hyperresearch@aece65f`](https://github.com/jordan-gibbs/hyperresearch/tree/aece65f9307197119629beacf8aeaf8cc80e999a) оригинальные два набора `pytest` прошли **54/54**; `collect-only` дал **28+26**, исходники/тесты pin по SHA. [Предметный обзор](../../reviews/hyperresearch/2026-11-07-upstream-tests.md), [run script](../../experiments/hyperresearch/2026-11-07-pinned-upstream-tests.py), [JSON](../../data/results/hyperresearch/2026-11-07-upstream-tests.json). Эти тесты подтверждают отдельный source contract, **не** отменяют прежние `75/100` false support на специально составленном citation-stress corpus. `REWORK_MECHANICAL_CITATION_GATE` остаётся.

## 5. Дальнейшая очередь и критерий действительного закрытия

Исходные 83 карточки документально учтены. Для **содержательного исследовательского закрытия** сохраняется разделение:

- `DOCUMENTED / RESEARCH_ONLY`: методы, авторские результаты, ограничения и вывод о применимости уже имеются в конкретном обзоре; когда не существует исходного target seam, дальнейший эксперимент не обязателен ради видимости прогресса.
- `LAB_VERIFIED_BOUNDED`: есть pinned исходники, независимо составленный oracle, реальные executable receipts и ограничения распространения результата. **Не** переносить на whole-paper scientific replication.
- `REWORK / NEEDS_EVIDENCE`: остаётся конкретный применимый target, который можно оценить offline; план следующего теста со штрафом за риск/стоимость. Повторение тех же старых тестов не является прогрессом.
- `BLOCKED_SOURCE / BLOCKED_PROVIDER / NO_CURRENT_TARGET`: явный, проверяемый отрицательный или отложенный вердикт. **Не** равнозначен успеху технологии.

В следующих итерациях выбирать **новые** исходные проекты со свободным независимым oracle (например, held-out citation semantic gate, отсутствие нормальной source-aware model verification) и закрывать их по одному конкретному проверяемому свойству. Сначала source-anchored proof, затем проект-fit и только потом изменение допустимого кода по отдельной owner approval. При отключённом ZCode рой не имитировать — собственная external verification имеет приоритет. `NO_NEW_PROJECT_FIT`, `NO_PRODUCTION_APPROVAL`, пока нет реальных измерений и проверенного target source seam. Архив и исходники всех 83 карточек не переписывать.
