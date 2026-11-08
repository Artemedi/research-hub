# Agent Error Dataset — checkpoint-bound correction and synthetic replay A/B

**Дата:** 8 ноября 2026. **Источник:** [Agent Error Dataset v2, arXiv:2609.40111](https://arxiv.org/html/2609.40111v2), 1 октября 2026. Полный легальный HTML повторно загружен: 2 118 878 bytes, SHA-256 `31af8d0a1d4da3a4c4184def8fed7e6f76a6483005804f0868133b682d7aab14`; hash совпадает с [полнотекстовым обзором от 05.11](2026-11-05-full-text.md). Это **дополнение с узким экспериментом**, не повторная полная рецензия и не новый source version.

**Registry:** `Artemedi/project-registry@b3af154278a8724230185cba6b1898a106a4f25a`, 45/45 PROJECT.md прочитаны и хешированы. **Research hub baseline:** `e1b303fd73b4492c4ef1a4ad7ff9a23a8d8df81a`.

## Перепроверенные положения первоисточника

AET описывает пять стадий: сбор natural failures с action/observation traces; diagnosis с trace citation и proposed correction; структурная и семантическая проверка доступности доказательства; replay исправления против retry исходного действия из того же checkpoint при согласованных policy/harness/budget/verifier; затем отдельные views для diagnosis, recovery и preference training. Diagnosis record не требует replay; recovery target требует исполненной успешной continuation. Успешный replay показывает полезность correction в заданных условиях, но **не доказывает единственную причинную гипотезу**.

**Авторские результаты, не наши измерения:** на 3 062 matched replay pairs first-proposal corrections повысили verifier pass с 18,4% до 51,1% (+32,7 pp; task-clustered 95% interval 28,4–37,0). Это supplied-failure-location cohort, а не автономное обнаружение ошибки или оценка общего deployment recovery rate. Citation-first output yield 93,5% — доля сформированных trace-cited диагнозов, не независимая accuracy. В отдельном supplied-location сравнении результаты 31,3% / 26,0% / 18,6% относятся к иной постановке и не дают уверенного paired преимущества над generic reconsideration.

## Methods, Results и Limitations — важные границы

- Коллекция содержит 50 228 error–diagnosis pairs, 38 278 source blobs и 9 961 исходную задачу. Эти величины не являются количеством независимых executions или однородных training examples.
- Appendix D.2 разделяет ungrounded, E0, E1 и E2. E2 требует, чтобы все treatment trials прошли, все controls провалились, было не менее двух trials на arm и оба arm завершили запланированные counts. Названный, но не исполненный checkpoint не становится успешным replay.
- Appendix D.3 требует lineage: branch/source trace, pre-action prompt, restored state, trial, applied action и actor transcript; native message/tool-call IDs и порядок результатов должны совпадать. Реконструированные external logs относятся к отдельной fidelity stratum. Наличие цитаты доказывает присутствие события, но не entailment, причинность или уникальный root cause.
- Appendix E.3: в matched ALFWorld audit exact-step agreement составил 46,8%, within-one-step — 53,9%; citation admission 75,2% у panel против 88,2% у solo pipeline. В отдельном полном citation audit прошло 6 381 из 11 116 попыток. Эти показатели имеют разные populations и не дают одного универсального уровня точности.
- Appendix A предупреждает, что failure-only cohorts не оценивают deployment failure rates; frozen diagnosis experiments использовали более ранний release с неполным policy context (без system prompts и tool lists). Внутренние holdouts разделяют environment/harness/policy с training, а поздние проверки pipeline не исправляют автоматически старые frozen subsets.
- Appendix K.1: в 1 744 переходах multi-round repair 61,0% повторно указывали тот же шаг, 20,8% двигались позже, 18,2% — раньше. Большее число repair rounds само по себе не доказывает прогресс.

## Независимый synthetic lab

**Цель:** проверить минимальный safety contract для одной коррекции из сохранённого checkpoint. Это не воспроизведение AED dataset, model training или авторского benchmark.

**Дизайн:** 30 полностью синтетических cases, три повтора каждого (90 paired trials):
- 15 детерминированно исправимых ошибок: missing value, invalid target, revision mismatch;
- 5 transient failures, для которых исходный retry может пройти;
- 5 ambiguous traces с несколькими ошибочными событиями;
- 5 misleading traces с decoy event от другого action ID и реальным permission denial.

Сравнивались один retry исходного действия из того же checkpoint и один correction, допускаемый только при совпадении checkpoint hash, action ID, единственного terminal event, event hash, error code и ровно одного контрактного изменения поля. Никакого автоматического повторного цикла и никаких внешних side effects.

| Результат | Значение |
|---|---:|
| Paired trials | 90 |
| Baseline original-action retry: успешные | 15/90 (только transient subset) |
| Evidence-bound corrections: приняты | 45/45 исправимых повторов |
| Принятые corrections с правильным конечным state | 45/45 |
| Abstain на transient / ambiguous / misleading | 45/45 |
| False accepted corrections | 0 |
| Negative controls: stale checkpoint, forged event, wrong action binding, wrong correction, changed operation, extra action field | 270/270 blocked |
| Независимый oracle | PASS |

**Интерпретация:** в этом искусственном контракте exact checkpoint + exact action/event binding отделили локально исправимые ошибки от неоднозначных, неавторизованных и transient случаев. Но консервативный gate отказался от 15 transient recoveries, которые baseline retry успешно завершил. Это демонстрирует trade-off coverage против риска неподтверждённой коррекции, а не преимущество по общей accuracy. Измеренные миллисекунды исполнения скрипта не являются latency benchmark; CPU/RAM/IO, модельная стоимость и производительность реальных инструментов не измерялись.

Артефакты: [experiment](../../experiments/agent-error-dataset/2026-11-08-checkpoint-replay-ab.py), [independent oracle](../../experiments/agent-error-dataset/2026-11-08-independent-oracle.py), [90 paired trials](../../data/results/agent-error-dataset/2026-11-08-checkpoint-replay-ab.json), [oracle result](../../data/results/agent-error-dataset/2026-11-08-independent-oracle.json).

## Project fit — 45 текущих профилей

[Полная матрица 45 PROJECT.md](../../portfolio/2026-11-08/agent-error-dataset-project-fit.md) · [machine-readable assessments](../../data/project-fit/agent-error-dataset/2026-11-08-project-fit.json).

Shortlist: `sequential-rca`, `dsh-runtime`, `akuz-issue`. Это только `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`, не verified integration:
- `sequential-rca` — ближайший профиль для sequential trace-grounded RCA; требуется clean source baseline и независимый final-state oracle.
- `dsh-runtime` — checkpoint/tool-result recovery находится в области runtime; неизвестный исход внешнего side effect нельзя превращать в automatic retry.
- `akuz-issue` — подходящее место для сохранения цепочки evidence → diagnosis → remediation → validation, но не исполнитель agent actions.

Ещё 9 профилей условно смежны, 17 получили `NO_CURRENT_FIT`, 14 — `REFERENCE_NO_TARGET`, 1 — `CONTROL_PLANE_REFERENCE`, 1 — `NOT_EVALUATED`. Причины и SHA всех 45 карточек находятся в матрице. В приватных карточках этих трёх проектов соответствующие ссылки уже есть в разрешённом разделе связанных исследований; нового соответствия не возникло, поэтому registry не менялся.

## Ограничения и вердикт

- Полный текст v2 подтверждён по тому же SHA, что и 05.11; прежний полнотекстовый обзор не заменён.
- Авторские 3 062 replay pairs и 18,4% → 51,1% остаются `AUTHOR_REPORTED / NOT_REPRODUCED`.
- Наш результат — `SYNTHETIC_LAB_PASS` только для 30 заданных fixtures и 270 negative controls. Диагностика выполнялась детерминированными правилами, не LLM.
- Не использовались AED dataset, реальные traces, SQL, patient data, live agents, external tools, production или проектный код. Нет доказательства causal RCA, project benefit, generalization или безопасного side-effect replay.
- **Итог:** `FULL_TEXT_REVIEWED (prior) / AUTHOR_REPORTED / NOT_REPRODUCED / SYNTHETIC_LAB_PASS / PROJECT_PROFILE_MATCH_NEEDS_EVIDENCE / NO_PRODUCTION_APPROVAL`.
