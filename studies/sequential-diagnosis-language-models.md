# Sequential diagnosis with language models — MAI-DxO / SDBench

**Исход research-intake:** `Добавлен в карточки` (BK-056). **Научный источник:** `FULL_TEXT_REVIEWED_2026-11-05`; опубликованный MAI-DxO/SDBench **не воспроизводился**. **Применение к TrinMedicalBot:** `WELLO_AB_OPERATIONAL_VERIFIED / PRODUCTION_DEPLOYED_2026-11-05 / CLINICAL_REVIEW_PENDING`. **Отдельный проект sequential-rca:** `FIT_CANDIDATE / NEEDS_EVIDENCE`. Production deployment — констатация факта, **не** `CLINICALLY_APPROVED`.

- **Статья:** Harsha Nori et al., *Sequential diagnosis with language models*, *Science* 394(6822), 423–428 (22.10.2026), DOI [10.1126/science.aeh7930](https://doi.org/10.1126/science.aeh7930), PMID [42912144](https://pubmed.ncbi.nlm.nih.gov/42912144/).
- **Полный первоисточник:** [авторская PDF-версия](https://erichorvitz.com/sequential_diagnosis_LM.pdf), титульная дата 08.11.2025; это авторская версия, а не тождественный издательский PDF. Первая техническая версия: [arXiv:2506.22405](https://arxiv.org/abs/2506.22405). Различать дату технического отчёта и публикацию в *Science*.
- **Происхождение в Telegram:** исторический [BK-056](../collections/telegram/README.md) был помечен «разобран» 04.11.2026; это первая нормализованная карточка источника, а не новая публикация и не дубль отдельной study-карточки.
- **Репликация оригинального SDBench:** не выполнялась (`NOT_RUN`); опубликованный [SDBench](https://github.com/microsoft/sdbench) не воспроизводился. **Локальный адаптированный A/B:** выполнен на синтетике через Wello, это другая метрика и другой эксперимент.
- **Обзор до эксперимента:** [методология, ограничения, матрица и план](../reviews/sequential-diagnosis-language-models/2026-11-05-project-fit.md). **Следующая запись от 05.11.2026:** [144 Wello-вызова, реализация и фактическое внедрение](../reviews/sequential-diagnosis-language-models/2026-11-05-challenger.md).

## Фактический результат для TrinMedicalBot (05.11.2026)

**Инженерный A/B выполнен:** 60 вымышленных русскоязычных одиночных случаев и 12 продолжений диалогов на arm; **72 DxO-lite v2 + 72 Challenger v2 = 144 реальных Wello-запроса**. Технически все HTTP 200/stop, без автоматического обнаружения ложных языковых отказов в исправленной паре; **клиническую правильность это не подтверждает**. До исправления был воспроизводимый критичный отказ модели на экстренном TRI-06 (3/3), поэтому исходный v1 был отклонён. Метрики и исходные ограничения — в [A/B-протоколе TrinMedicalBot](https://github.com/Artemedi/TrinMedicalBot/blob/main/eval/CHALLENGER-LIVE-AB-2026-11-05.md).

**Внедрение подтверждено операционно:** 05.11.2026 обновлён живой профиль Hermes TrinMedicalBot: DxO-lite + одноагентный Challenger, русскоязычная экстренная эскалация, лекарственный fail-closed с инструментами поиска/чтения источников, Telegram `busy_input_mode: queue`. [Коммит внедрения](https://github.com/Artemedi/TrinMedicalBot/commit/7f0b5877ac857be13864dd6d9197b8e667b124d7) и [ограничение повторных попыток чтения при блокировке URL](https://github.com/Artemedi/TrinMedicalBot/commit/2eabba7e2518b54a39af49c087bc021ce884310f). Пройдены **44/44 локальных инфраструктурных теста**, общий gateway работал, Telegram-адаптер имел состояние `connected`; **новый входящий Telegram-запрос после развёртывания не проверялся**.

**Открытый gate:** независимый квалифицированный слепой клинический разбор ответов отсутствует; работающая защита URL блокирует чтение некоторых лекарственных инструкций; фактическая стоимость не измерена, дополнительный Hermes smoke-test занял до ~143 с. Нельзя объявлять `CLINICALLY_VALIDATED`, процент медицинской точности или воспроизведение результатов Science. Полный [отчёт-последействие и матрица статусов](../reviews/sequential-diagnosis-language-models/2026-11-05-challenger.md).

## Проверенная методология (из полного текста)

SDBench моделирует диагностический диалог: диагностический агент постепенно запрашивает анамнез или исследования; Gatekeeper раскрывает записанные и иногда синтезированные данные случая; Judge сравнивает финальный диагноз с исходным по шкале 1–5; отдельный расчёт оценивает стоимость исследований. Материал: 304 NEJM-CPC и 325 MIMIC-IV-ED случаев.

MAI-DxO использует одну языковую модель в пяти виртуальных ролях: Hypothesis (до трёх дифференциальных гипотез), Test-Chooser (дискриминирующие исследования), Challenger (опровержение и борьба с anchoring), Stewardship (стоимость и избыточность), Checklist (согласованность). Роли — **виртуальный консилиум**, а не пять обязательно независимых моделей. Исследованы режимы Instant Answer, Question Only, Budgeted, No Budget и Ensemble.

**AUTHOR_REPORTED:** при GPT-5 No Budget NEJM-CPC 83,2% против 78,9% для GPT-5 с baseline prompt и 36,1% для врачей с разрешёнными справочными ресурсами; MIMIC-IV-ED 80,3% против 46,8% врачей. Бюджетный вариант NEJM достигал 80,9% при оценочной стоимости обследований $2 241 против $5 430 для No Budget (83,2%). Эти доллары — **стоимость клинических исследований в модели**, а не API-токенов.

**LIMITATIONS:** случаи заранее отобраны и все содержат патологию; нет обычных здоровых обращений. Gatekeeper может достраивать отсутствующие результаты, Judge оценивает диагноз, но не безопасность лечения и исходы пациентов. Врачи и ИИ работали в текстовом симуляторе, сравнение не распространяется на работу медицинских команд в реальной клинике. Данные не доказывают 83% точности TrinMedBot и не разрешают автономную диагностику.

## Применимость к портфелю

| Проект | Установленная точка применения | Условие / статус |
| --- | --- | --- |
| [TrinMedicalBot](https://github.com/Artemedi/project-registry/blob/main/projects/03-automations/TrinMedicalBot/PROJECT.md) | [DxO-lite + Challenger v2 в SOUL.md@2eabba7](https://github.com/Artemedi/TrinMedicalBot/blob/2eabba7e2518b54a39af49c087bc021ce884310f/SOUL.md), с проверкой альтернатив/опровергающих признаков; [A/B и деплой](../reviews/sequential-diagnosis-language-models/2026-11-05-challenger.md). | `PRODUCTION_DEPLOYED / CLINICAL_REVIEW_PENDING` — 144/144 успешных API-ответа (операционная проверка), 44/44 теста; нет независимой клинической оценки и Telegram end-to-end smoke. |
| [sequential-rca](https://github.com/Artemedi/project-registry/blob/main/projects/01-dba-akuz/sequential-rca/PROJECT.md) | Та же общая методология последовательного запроса доказательств, но для DBA; [replay.py@13fa0c9:L11-L39](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/replay.py#L11-L39). | `FIT_CANDIDATE / NEEDS_EVIDENCE` — самостоятельный offline benchmark; клинические цифры не переносим. |

Остальные 43 профиля просмотрены на уровне карточек: нет столь прямого диагностического workflow / выбранной безопасной точки для этой статьи. Общая применимость рассуждений к агентам сама по себе не является основанием для backlinks.

**Следующий шаг:** независимая слепая оценка 144 ответов специалистом, включая лекарственные регрессии и экстренные сценарии; устранение ограничений источников/latency, контролируемый входящий Telegram smoke. Платные Wello A/B-запросы и развёртывание TrinMedicalBot уже выполнены по решению владельца 05.11.2026. Production SQL и исходный SDBench не изменялись.
