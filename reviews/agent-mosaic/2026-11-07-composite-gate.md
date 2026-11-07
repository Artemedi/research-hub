# Agent Mosaic — полнотекстовый follow-up и synthetic composite-gate lab

- **Дата:** 2026-11-07
- **Источник:** [Agent Mosaic — Composite Disclosure Risk, arXiv:2610.30418v1](https://arxiv.org/html/2610.30418v1)
- **Полный легальный текст:** arXiv HTML v1, Methods, Results, Limitations, Future Work и Ethical Considerations прочитаны.
- **SHA-256 HTML:** `80b01bba9c64a4bee86dec3badaccc39e8e801121c0610544affb5e67cfe190a`
- **Предыдущий обзор:** [полнотекстовая карточка](../../studies/agent-mosaic.md), assessment от 2026-11-03. Этот follow-up добавляет новый изолированный эксперимент и обновлённый project-fit; авторские результаты не переобъявляются воспроизведёнными.

## Краткий вывод

Исследование показывает, что разрешение читать каждый документ по отдельности не гарантирует конфиденциальность результата, если агент может объединить факты из нескольких доступных источников. Особенно важен результат про отказ: формулировка «не могу раскрыть» сама по себе не безопасна, если в ней уже присутствует запрещённая связь.

Наш независимый синтетический тест подтвердил более узкое инженерное свойство: простая document-level ACL пропускает защищённые комбинации; проверка структурированных claims снижает утечки, но обходится неполной атрибуцией; привязка выпускаемого текста к детерминированному renderer устраняет эти контролируемые обходы ценой большого числа безопасных отказов от выпуска. Это контрактный тест механизма, не тест LLM и не интеграция в проект.

## Что измеряли авторы

Авторы подготовили 30 синтетических примеров в трёх областях — кибербезопасность, медицина и военная тематика, по 10 примеров на область. Для симуляции использовали три модели, три типа запроса, наличие/отсутствие distractor, classification headers и aggregation rules; пять повторов конфигураций дали 10 800 финальных ответов. Отдельно проверены два live agent harness — Pi и Hermes, суммарно 1 440 ответов.

Для проверки judge авторы вручную разметили 120 различных ответов тремя волонтёрами. Согласие людей по метке mosaic было Krippendorff's alpha 0.810, по метке refusal — 0.962. Это полезная проверка разметки, но не устраняет ограничения выбранного judge и небольшого human-labelled набора.

**Авторские результаты (не наши измерения):**

- На benign-запросах, которые должны были разрешаться по одному документу, запрещённая комбинация появилась в 7.08% симуляционных GPT-5.6-Sol ответов (85/1,200; 95% CI 3.75–10.67%), в 12.50% Pi live ответов (30/240) и в 8.75% Hermes live ответов (21/240).
- По всем типам запросов симуляционный pooled disclosure при обоих safeguards оставался 32.37%; авторы сообщают снижение pooled disclosure на 36.26 процентного пункта, но не устранение риска.
- Отказ не был надёжным индикатором безопасности: среди 410 mosaic-positive ответов Claude в условии с обоими safeguards 404 также имели метку refusal.

Результаты относятся к конкретному синтетическому корпусу, конфигурациям и harness/model snapshots. Их нельзя переносить на текущие пользовательские проекты как измеренную частоту утечки.

## Methods, Results и ограничения

Метод строится на синтетических документах с индивидуальными classification labels и специально заданными отношениями, которые становятся запрещёнными только при объединении нескольких фактов. Авторы сравнивали benign, explicit и adversarial intents, headers/rules, distractors и поведение live harness. Этическая секция прямо указывает, что документы и классификации синтетические.

Ограничения, влияющие на переносимость:

1. Всего 30 исходных примеров, по 10 на домен; синтетические документы прошли экспертную проверку правдоподобия, но это не реальный корпус и не оценка распространённости риска в production.
2. Distractor ограничен одним документом; набор запросов и adversarial suffixes фиксирован. Адаптивные атаки, длинные многошаговые сессии и широкий набор отношений требуют отдельной оценки.
3. Основная метрика относится к финальному ответу. Промежуточные reasoning traces, tool outputs, shared memory и multi-agent handoffs не исследованы как полноценные end-to-end каналы.
4. Judge выбирался и оценивался на одном и том же небольшом наборе из 120 ответов; интервалы не включают всю неопределённость judge и human annotation.
5. Сравнение Pi/Hermes — сравнение целых harness-конфигураций, а не изолированный причинный тест отдельного инструмента. Указанные model aliases не эквивалентны неизменяемым весам.
6. В полном тексте не найден опубликованный benchmark source/test repository, достаточный для повторного запуска авторского набора. Поэтому 10,800 simulation outputs и 1,440 live outputs здесь имеют статус **AUTHOR_REPORTED / NOT_REPRODUCED**.

В Future Work авторы предлагают deterministic harness controls на retrieval, tool execution и answer release, с учётом происхождения фактов и запрещённых комбинаций. Multi-agent disclosure обозначен как отдельное будущее направление, а не уже доказанный результат статьи.

## Независимый synthetic lab

**Цель:** проверить контракт контроля композиционного раскрытия, а не воспроизвести модельные результаты авторов.

**Fixture:** 30 полностью синтетических случаев — 10 на каждый из трёх абстрактных доменов; в каждом два доступных документа уровня SECRET, clearance пользователя SECRET и одна связь TOP_SECRET, возникающая только из пары фактов. Для каждого случая проверены 9 вариантов ответа, всего 270 outputs.

Сравнивались три механизма:

1. **Document ACL only:** проверяет доступность каждого источника по отдельности.
2. **Structured claim gate:** проверяет известные fact IDs, source provenance и запрещённые пары.
3. **Output-bound gate:** дополнительно выпускает только точный текст, детерминированно отрендеренный из проверенных claims; несовпадение текста и claims даёт INCONCLUSIVE и не выпускается.

Отдельный oracle реализован в другом скрипте. Он независимо проверяет маркер запрещённой связи в финальном тексте и сопоставляет заявленные источники с отдельным fixture catalogue. Он не импортирует код gate.

| Результат | Document ACL only | Structured claim gate | Output-bound gate |
|---|---:|---:|---:|
| ALLOW | 240 | 120 | 90 |
| DENY | 0 | 60 | 60 |
| INCONCLUSIVE | 30 | 90 | 120 |
| False disclosure release | 90 | 30 | 0 |
| Unverified release | 60 | 0 | 0 |
| Safe outputs not released | 0 | 0 | 0 |

Oracle labels: 90 ALLOW, 120 DENY, 60 INCONCLUSIVE. Независимый checker подтвердил **270/270** строк и совпадение всех трёх таблиц.

**Наблюдение:** document ACL пропустил 90 запрещённых композиций и выпустил ещё 60 ответов с неподтверждённой provenance. Structured gate всё ещё пропустил 30 ответов, где текст содержал запрещённую связь, но provenance намеренно не указывала второй источник. Output-bound gate не выпустил ни одного такого ответа, однако 120/270 вариантов стали INCONCLUSIVE; 60 из 120 oracle-denied случаев были безопасно остановлены, но не классифицированы как DENY из-за неполной provenance.

**Интерпретация и trade-off:** exact output binding снижает false release в этом контролируемом наборе до нуля, но зависит от того, что финальный текст действительно строится из проверенных claims. Цена — высокий abstention/non-release rate. Свободный natural-language ответ, который не проходит через такой renderer, не защищён этим результатом.

**Граница доказательства:** ни одна LLM, Hermes, Pi, retrieval API, реальный project source, реальный документ или production service не запускались. Oracle использует синтетические маркеры, а не semantic model; эксперимент не проверяет, способен ли LLM корректно извлечь все claims из произвольного текста. Это **SYNTHETIC POLICY-CONTRACT OBSERVATION**, не научная репликация и не production approval.

Артефакты:
- [experiment script](../../experiments/agent-mosaic/2026-11-07-composite-gate.py)
- [independent oracle script](../../experiments/agent-mosaic/2026-11-07-composite-gate-oracle.py)
- [raw experiment evidence](../../data/results/agent-mosaic/2026-11-07-composite-gate.json)
- [independent oracle result](../../data/results/agent-mosaic/2026-11-07-composite-gate-oracle.json)

## Project fit

Проверены все 45 PROJECT.md на актуальном private registry HEAD `838b86a28fcaa3440eeddbe147b6188e0d177963`. В публичный архив перенесены только project IDs, SHA карточек и краткие high-level причины; содержимое частных карточек и частный код не копировались.

Shortlist из трёх **профильных кандидатов**, не подтверждённых интеграций:

- **TrinMedicalBot** — профиль медицинского ассистента; риск cross-source disclosure релевантен как отдельный confidentiality question, но клиническое качество здесь не оценивалось.
- **dsh-team-context** — потенциальный слой source labels/provenance для governed knowledge; он не владеет выпуском финального ответа.
- **dsh-runtime** — потенциальный слой deterministic answer-release enforcement; точка интеграции в текущем source HEAD в этом запуске не закреплена.

Восемь проектов оставлены в CONDITIONAL_NEEDS_EVIDENCE; остальные классифицированы как NO_CURRENT_FIT, reference-only или NOT_EVALUATED. Полная матрица и причины: [45-project fit matrix](../../portfolio/2026-11-07/agent-mosaic-project-fit.md).

## Решение

- **Source:** FULL_TEXT_REVIEWED, arXiv v1.
- **Author results:** AUTHOR_REPORTED / NOT_REPRODUCED.
- **Independent lab:** SYNTHETIC POLICY-CONTRACT OBSERVED; independent oracle PASS 270/270.
- **Project fit:** три PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE; source-level integration seam не подтверждён.
- **Production:** NO_PRODUCTION_APPROVAL. Не менялись исходники проектов, медицинские/пользовательские данные и production.

Следующий допустимый шаг — отдельный synthetic LLM claim-extraction test с заранее размеченным независимым oracle и проверкой refusal-leak/provenance-omission. До него необходимо закрепить конкретный output hook на актуальном target source. Реальные документы и production-трафик для этого не нужны.
