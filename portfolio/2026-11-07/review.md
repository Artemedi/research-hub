# Research Portfolio — полный инвентаризационный проход 83 источников

[Следующий этап: четыре предметных лабораторных проверки](next-evidence-round2.md) — отдельные проверяемые эксперименты.
[Массовый разбор 31 источника с доказательными пробелами](mass-swarm-review.md) — отдельная модельная очередь и ограничения её проверки.
**Дата:** 7 ноября 2026. **Глобальная карта:** приватный `project-registry@838b86a28fcaa3440eeddbe147b6188e0d177963`, 45 project cards. **Исходный публичный каталог:** `research-hub@3180d9c46914f2f54d2a21e642b7ec3efffa2b99`, 83 studies. Это **повторная проверка охвата**, а не заявление о новом научном эксперименте на каждом из 83 источников.

**Сводная матрица для всех 83 источников:** [project-fit](project-fit.md). **Состояние диспетчера:** [архитектура](../../docs/research-orchestrator.md). **Machine-readable evidence:** [доступ к источникам](../../data/results/research-portfolio/2026-11-07-source-audit.json), [83×45](../../data/results/research-portfolio/2026-11-07-coverage.json), [249 DAG stages](../../data/results/research-portfolio/2026-11-07-controller.json), [проверка HEAD](../../data/results/research-portfolio/2026-11-07-source-heads.json). Различие между scan, source reading, author claims и independent verification обязательно.

## Принцип и результаты

Проверены все 83 canonical study ID и все 45 проектных карточек по текущей структуре; без копирования приватных карточек в публичный архив. Матрица включает **3 735** пар study×project: **376** имеют документированную текущую оценку, **3 359** `NOT_EVALUATED`. Это не «3 359 неподходящих проектов», а отсутствие отдельного доказательного вердикта; автоматическая постановка `NO_FIT` запрещена.

| Проверка первичной ссылки | Число | Доказательство и ограничение |
| --- | ---: | --- |
| ArXiv full HTML machine-readable | 47 | HTML содержит статьи с заголовками, **не** самостоятельная научная репликация |
| ArXiv PDF text-extractable | 1 | `kvset`; текст извлекается, отдельно проверять таблицы/фигуры |
| GitHub landing/source repo reachable | 20 | Нужен pinned source@SHA + code/tests для нового engineering review |
| Публичный HTML/technical disclosure содержателен | 11 | Нужен полный методологический/инженерный анализ |
| Короткая landing page или SPA | 2 | `hyra-2`, `warp-skill-doctor`; исторические полноценные источники/код отдельно указаны в прежних карточках |
| DOI/официальный URL не открылся | 1 | `sequential-diagnosis-language-models`: легальная **полная авторская PDF** на erichorvitz.com извлечена, 93 106 текстовых символов; DOI 403 не означает отсутствие full text |
| YouTube landing без полного transcript в новом проходе | 1 | `unreal-agent`; прежний обзор сохраняется, без нового claim |

Все 83 получили проверку source-access/структуры, не научную экспертизу заново. Пять приоритетных арxiv работ отдельно прочитаны по **полным машинно извлечённым текстам** в части Methods/Results/Limitations и ограничениям; цифры ниже — **авторские**, без нашего повторного model benchmark. Указание на полноту чтения первоисточников не означает проверку всех рисунков или повторение вычислений.

### Пять конкретных выводов из первоисточников

**1. [Goal-Aware Dynamic Collaboration (GAD)](https://arxiv.org/html/2610.39193).** Growing execution graph хранит отдельную goal/acceptance conditions и зависимости; независимый verifier и dependency-aware context снижают потерю контекста. В авторских TB 2.1 сравнительных условиях улучшение против лучшего single-agent baseline на 14,6 и 7,8 процентных пункта для указанных моделей; задачи и измерения **не наши**. Авторские token comparisons около 50k против 105–170k на подмножестве совместно решённых задач не являются тарифным прогнозом для ZCode. **Кандидаты** из текущей матрицы: `dsh-runtime`, `agent-skills`, `hermes-akuz-agents`. **Следующий тест:** сначала проверить статический acceptance DAG на 20–30 synthetic episodes с независимым oracle, сравнить с фиксированным советом и одним агентом. **NO PRODUCTION APPROVAL**.

**2. [HTN-Orchestrate](https://arxiv.org/html/2610.22195).** Hierarchical Task Network с DAG зависимостей и replanning после результатов исполнителей. Авторский BrowseComp 89,73% против Agent Team на +2,45 pp при заявленных условиях — не benchmark нашей системы. **Кандидаты:** `dsh-runtime`, `hermes-akuz-agents`. **Тест:** per-study rooted DAG, dependency-unblock, crash recovery, fairness/branching limit, итоговый reviewer, comparator без LLM calls. Опасность: overhead planning, неверные зависимости, каскад повторов.

**3. [Agent Error Dataset (AED)](https://arxiv.org/html/2609.40111).** Локализация ошибки + цитированная trace diagnosis + replay correction только на **подтверждённом checkpoint**. Авторское повышение verifier success **18,4% → 51,1%** — 32,7 pp *для тестового исходного failure pool*, не «вся модель на 32,7% лучше». Статья отдельно ограничивает supplied-location и обучение, ошибки разметки, пересекающиеся когорты. **Кандидаты:** `akuz-issue`, `sequential-rca`, `dsh-runtime`. **Тест:** 20 controlled failing traces, paired original-action retry vs correction, независимые labels и no-leakage policy; не включать исправления запросов SQL автоматически.

**4. [Agent Mosaic](https://arxiv.org/html/2610.30418).** Контроль запрещённых **составных выводов из нескольких документов** — не защита отдельных source strings. В авторских 30 синтетических сценариях benign requests показывали leaks (среди прочего Hermes 8,75%; mixed simulated GPT 7,08%); правила и метки уменьшали, но не устраняли риск. Нет независимого proof production leak в нашем Hermes и клинических данных. **Кандидаты:** `HermesAgent`, `agent-config`, `dsh-team-context`. **Тест:** synthetic cross-source canaries, негативные случаи разрешённых single-source ответов, blocklist aggregation. Никогда не отправлять ZCode приватные snippets, медицинские записи, токены.

**5. [BenchShield](https://arxiv.org/html/2609.11028).** Чётко отделяет task outcome от integrity verdict `Checked / VectorExposed / AgentViolation / Inconclusive`; инструмент доверяет host-side events, а не заявлению самого агента. Авторские integrity measurements зависят от конкретного sandbox/coverage; наш текущий скан и DAG-прототип их не воспроизводят. **Кандидаты:** `agent-skills`, `dsh-runtime`, `dsh-paper2agent`. **Тест:** 20 synthetic provenance/evidence bundles с фальсифицированными evidence, unsigned/missing tool results и требованием `INCONCLUSIVE`, если coverage неполный.

Общий вывод пяти источников: **контроль цели и зависимостей + независимое доказательство результата + recovery по адресному контрпримеру** лучше неподтверждённого «совет сам согласился». Но улучшение latency/quality на нашем ZCode и реальных проектах **не измерено**; предложенные исследования — не разрешение на внедрение.

## Engineering sources и версии

Проверен HTTP/HEAD у **20** публичных GitHub repo ссылок. У **`hyperresearch`** и **`understand-anything`** свежий HEAD отличается от explicit 40-digit SHA в первичной ссылке: `NEW_VERSION_REVIEW_REQUIRED`. Ранее pinned обзоры не становятся ошибочными автоматически; новая версия требует отдельного diff/source+tests audit.

`hyra-2` доступен ранее через специальный публичный read API и уже рассмотрен в собственном dated review; нынешний SPA HTTP200 с 0 main text **не** опровергает предыдущее заключение. `warp-skill-doctor` имеет pinned открытый исходный код; короткая маркетинговая страница не заменяет code review. `unreal-agent` и видеодемонстрация требуют сверки полного доступного transcript/авторской реализации прежде новых claims.

## Статусы глобального диспетчера

Контроллер провёл три детерминированных стадии для каждого источника: access, consistency матрицы, review gate. 249/249 stage completions, два физических workers, целостность 83 study state, отдельные negative/mutation tests PASS. **0 LLM-запросов в контроллере** — это проверка DAG, не новый real scientific review.

| Verdict по стадии | Studies | Следующее действие |
| --- | ---: | --- |
| Сохранить предыдущий review, без внедрения | 50 | Только новые факты/версии или измеримый target test |
| `REWORK_PIN_AND_TEST_SOURCE_CODE` | 20 | Pin SHA, source boundary, upstream tests, безопасный A/B |
| `REWORK_INDEPENDENT_SOURCE_AND_TEST_COVERAGE` | 7 | Уточнить ранее ограниченный review; проверить известные источники, не переписывать прошлое |
| `REWORK_LEGAL_FULL_SOURCE_OR_TRANSCRIPT` | 3 | Альтернативы и уже закреплённые тексты/видео; `DOI_403` для Science не отсутствие полного текста |
| `REWORK_45_PROJECT_TRIAGE_WITHOUT_INFERRED_FIT` | 3 | `cera-moa`, `kvtether`, `random-attention`: нет текущих assessment; проверить 45 profiles или явно NO_FIT |

Автоматические review-gate verdicts **не меняют canonical current_review_id и не заменяют научный вердикт**. У source-access 11 HTTP технических статей требуется содержательный review, а не approval только по размеру текста. Сопоставления и детали по каждой из 83 строк — в JSON, человеческая матрица — [project-fit](project-fit.md).

## Испытание ZCode как ограниченного advisory-инструмента

Отдельный внешний GLM-5.3-Flash получал **только короткие выдержки публичных canonical source cards**, без полных статей, приватной карты проектов или инструментов. Из 31 приоритетного кандидата обработаны **8**, по ним эксперт+критик выдали оба валидных ответа только **для `random-attention`** (скрининг, не full scientific review). На остальных **7** цепочка неполная; после пяти последовательных отказов сработал установленный circuit breaker. Всего **14 вызовов** и **18 811 токенов, отражённых в успешных ответах**; дельта фактического биллинга отдельно не проверена.

**Никакого нового scientific ACCEPT или project-fit APPROVAL из ZCode нет**. Оставшиеся 23 задания не были отправлены провайдеру; их metadata/access и матрица из независимого offline прохода учтены. [Машинный протокол отказов](../../data/results/research-portfolio/2026-11-07-zcode-screening.json). Этот опыт — честная проверка ограничений неофициального канала, а не будто бы завершённый совет на 31 работе.

## Ограничения, риски и решения

- Полный научный review всех 83 **с нуля** и репликация 83 авторских экспериментов в этом проходе **не выполнялись**. Ранее подтверждённые full-text reviews сохранены; новым claims без первоисточника статус `FULL_TEXT_UNAVAILABLE`. Упоминания paper-результатов в этом отчёте — `AUTHOR_REPORTED`.
- Текущие карточки PROJECT.md важны для broad screening, но 3 359 `NOT_EVALUATED` пар по машиночитаемому реестру нельзя назвать экспертным NO_FIT. Практические shortlist прежних обзоров **не** развёрнутые интеграционные seam.
- Публикация **не** включает защищённые PDF, полнотекстовые авторские файлы, приватные source из реестра или реальные clinical/DB данные.
- Исключения источников без полного текста не подменять выводами по аннотации. Конфликтный/модельный review направить `REWORK`, итоговое решение приниматься по независимым evidence.
- Отдельное одновременное исполнение сотни ZCode запросов не реализовано и небезопасно в текущем wrapper. Исторически режим 1–2 физических слотов стабильнее; прежние большие советы попадали в timeout и ошибку preview count 6 vs 20.
- Всю работу нужно верифицировать тестами и diff; временные исследовательские скрипты/сырые источники Bazzite не являются частью публикации.

## Что дальше по приоритету

**P1 (максимум научной и архитектурной пользы):** независимый held-out A/B по GAD+HTN, источник/provenance gate BenchShield и AED checkpoint repair; общая инфраструктура результата должна проверять project-specific evidence, а не перечислять агентов. **P1 security:** Agent Mosaic synthetic multi-document canary для Hermes/контекста, без реальных данных.

**P2:** pinned source reviews 20 GitHub источников, приоритет устаревших `hyperresearch` и `understand-anything`, а также explicit no-fit по трём источникам без current assessments; легальный transcript видео и SPA/technical source alternatives.

**P3:** расширить project-fit от текущих документированных 376 пар только там, где источник действительно прошёл source gate и есть meaningful hypothesis, иначе честно `NOT_EVALUATED`. Ни один target source не изменять до отдельного performance/security/human gate.

**Финальный вердикт текущего прохода:** `PORTFOLIO_ACCESS_AND_COVERAGE_AUDITED / NO_NEW_PRODUCTION_APPROVAL / EVIDENCE_GAPS_RECORDED`. Не объявлять все исследования независимо воспроизведёнными.

## Воспроизведение проверок без ZCode

На авторизованном компьютере с **отдельной** разрешённой read-only копией private project-registry, Python 3, Node и `pdftotext`:

```bash
H=/path/to/research-hub
W=/var/tmp/research-repro-20261107
mkdir -p "$W"
cd "$H"
export RESEARCH_HUB_ROOT="$H"
export RESEARCH_AUDIT_WORK="$W"
export PROJECT_REGISTRY_ROOT=/path/to/authorized-project-registry
export RESEARCH_SOURCE_AUDIT="$W/source-audit.json"
export RESEARCH_COVERAGE_OUT="$W/coverage.json"

python3 -B experiments/research-portfolio/source-audit.py --self-test
python3 -B experiments/research-portfolio/source-audit.py --workers 2 --out "$W/source-audit.json"
python3 -B experiments/research-portfolio/coverage.py
python3 -B experiments/research-portfolio/controller.py --self-test
# Для controller нужны также локальные metadata source-alternates.json из подтверждённого legal-source preflight:
python3 -B experiments/research-portfolio/controller.py \
  --source "$W/source-audit.json" \
  --coverage "$W/coverage.json" \
  --alternates /path/to/2026-11-07-source-alternates.json \
  --out "$W/controller.json" --workers 2
python3 -B experiments/research-portfolio/render-project-matrix.py \
  --coverage "$W/coverage.json" --out "$W/project-fit.md"

node scripts/build-catalog.mjs --check
node scripts/check.mjs
node --test scripts/check.test.mjs scripts/entity-model.test.mjs scripts/document-assessment.test.mjs
```

Данные из интернета меняются, поэтому точные HTML body hashes и HTTP accessibility будут отличаться со временем. Детерминированный controller проверяет **структуру и переходы**, а не опубликованные научные выводы. Не запускать модельные или production-плагины в качестве теста документации.
