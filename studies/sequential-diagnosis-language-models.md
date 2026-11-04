# Sequential diagnosis with language models — MAI-DxO / SDBench

**Исход:** `Добавлен в карточки` (после проверки backlinks). **Evidence:** `FULL_TEXT_REVIEWED_2026-11-05 / FIT_CANDIDATE / NEEDS_EVIDENCE`. **Не** `LAB_VERIFIED` и **не** `PRODUCTION_APPROVED`.

- **Статья:** Harsha Nori et al., *Sequential diagnosis with language models*, *Science* 394(6822), 423–428 (22.10.2026), DOI [10.1126/science.aeh7930](https://doi.org/10.1126/science.aeh7930), PMID [42912144](https://pubmed.ncbi.nlm.nih.gov/42912144/).
- **Полный первоисточник:** [авторская PDF-версия](https://erichorvitz.com/sequential_diagnosis_LM.pdf), титульная дата 08.11.2025; это авторская версия, а не тождественный издательский PDF. Первая техническая версия: [arXiv:2506.22405](https://arxiv.org/abs/2506.22405). Различать дату технического отчёта и публикацию в *Science*.
- **Происхождение в Telegram:** исторический [BK-056](../reports/2026-11-04-telegram-bookmarks-reconciliation.md) был помечен «разобран» 04.11.2026; это первая нормализованная карточка источника, а не новая публикация и не дубль отдельной study-карточки.
- **Репликация:** не выполнялась (`NOT_RUN`). Опубликованный [SDBench](https://github.com/microsoft/sdbench) — исходный воспроизводимый benchmark, а не подтверждение применимости к нашему Telegram-боту.
- **Обзор 05.11.2026:** [методология, ограничения, матрица и проверяемый план](../reports/2026-11-05-sequential-diagnosis-trinmedicalbot-review.md).

## Проверенная методология (из полного текста)

SDBench моделирует диагностический диалог: диагностический агент постепенно запрашивает анамнез или исследования; Gatekeeper раскрывает записанные и иногда синтезированные данные случая; Judge сравнивает финальный диагноз с исходным по шкале 1–5; отдельный расчёт оценивает стоимость исследований. Материал: 304 NEJM-CPC и 325 MIMIC-IV-ED случаев.

MAI-DxO использует одну языковую модель в пяти виртуальных ролях: Hypothesis (до трёх дифференциальных гипотез), Test-Chooser (дискриминирующие исследования), Challenger (опровержение и борьба с anchoring), Stewardship (стоимость и избыточность), Checklist (согласованность). Роли — **виртуальный консилиум**, а не пять обязательно независимых моделей. Исследованы режимы Instant Answer, Question Only, Budgeted, No Budget и Ensemble.

**AUTHOR_REPORTED:** при GPT-5 No Budget NEJM-CPC 83,2% против 78,9% для GPT-5 с baseline prompt и 36,1% для врачей с разрешёнными справочными ресурсами; MIMIC-IV-ED 80,3% против 46,8% врачей. Бюджетный вариант NEJM достигал 80,9% при оценочной стоимости обследований $2 241 против $5 430 для No Budget (83,2%). Эти доллары — **стоимость клинических исследований в модели**, а не API-токенов.

**LIMITATIONS:** случаи заранее отобраны и все содержат патологию; нет обычных здоровых обращений. Gatekeeper может достраивать отсутствующие результаты, Judge оценивает диагноз, но не безопасность лечения и исходы пациентов. Врачи и ИИ работали в текстовом симуляторе, сравнение не распространяется на работу медицинских команд в реальной клинике. Данные не доказывают 83% точности TrinMedBot и не разрешают автономную диагностику.

## Применимость к портфелю

| Проект | Установленная точка применения | Условие / статус |
| --- | --- | --- |
| [TrinMedicalBot](https://github.com/Artemedi/project-registry/blob/main/projects/03-automations/TrinMedicalBot/PROJECT.md) | Существующий DxO-lite: аварийная эскалация → решение, стоит ли задавать до двух уточнений → осторожный ответ; [SOUL.md@e0a3e4e:L18-L28](https://github.com/Artemedi/TrinMedicalBot/blob/e0a3e4e7e333a284038fe155adf29340e54fbe29/SOUL.md#L18-L28). | `FIT_CANDIDATE / NEEDS_EVIDENCE` — эксперимент с Challenger/явным пересмотром гипотез на синтетических диалогах; клинический oracle не утверждён. |
| [sequential-rca](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/sequential-rca/PROJECT.md) | Та же общая методология последовательного запроса доказательств, но для DBA; [replay.py@13fa0c9:L11-L39](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/replay.py#L11-L39). | `FIT_CANDIDATE / NEEDS_EVIDENCE` — самостоятельный offline benchmark; клинические цифры не переносим. |

Остальные 43 профиля просмотрены на уровне карточек: нет столь прямого диагностического workflow / выбранной безопасной точки для этой статьи. Общая применимость рассуждений к агентам сама по себе не является основанием для backlinks.

**Следующий шаг:** offline-план A/B и независимая клиническая оценка. Без отдельного разрешения не выполнялись платные запросы, изменения медицинского профиля, Telegram/systemd, production SQL или установка исходного SDBench.
