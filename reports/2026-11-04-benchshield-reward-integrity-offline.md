# BenchShield — reward-integrity lifecycle and evidence-boundary replay

**Дата:** 2026-11-04. **Статус:** `METHODOLOGY_REPLAY_VERIFIED / ORIGINAL_BENCHSHIELD_NOT_RUN / DSH_RUNTIME_NOT_TESTED / NO_PRODUCTION_APPROVAL`.

## Цель и проверенные первоисточники

Верифицировать минимальную гипотезу по [BenchShield: Formal Model-Backed Instrumentation for Reward Integrity in LLM-Agent Evaluation Infrastructure](https://arxiv.org/html/2609.11028v1): при оценке агентных результатов нельзя доверять только возвращённому reward; необходимо отдельно моделировать доступные уязвимые пути, фактические события использования защищённых ресурсов, полноту инфраструктурных свидетельств и семантические ограничения. Ранее рассмотрена **полная** научная статья с методологией и ограничениями: [карточка BenchShield](../studies/benchshield.md), [первичный полнотекстовый обзор](2026-11-03-historical-gap-closure-2026-09-03-to-15.md).

**Происхождение реализации:** найти однозначно подтверждённый *авторский* репозиторий BenchShield не удалось. Репозитории других авторов с названием BenchShield не приравниваются к статье. Приложенный [скрипт](../experiments/2026-11-04-benchshield-reward-integrity-replay.py) — **наша собственная минимальная симуляция** жизненного цикла, построенная по принципам статьи: не TLA+ model checking, не авторский static taint scanner, не авторский runtime auditor, не репликация 456 adjudicated trajectories и не вывод об эффективности BenchShield.

## Дизайн исследования

Изолированный Python 3.14 / временный каталог. Script создаёт **100 синтетических запусков** по **10 в каждой из 10 категорий**, seed `20261104`; все данные и исполняемые записи придуманы. Каждый случай имеет отдельный `workspace/solution.txt`, `workspace/reported_reward.json` (агентный результат), `host/expected.json` (независимый oracle), `host/binding.json` (объявленная политика доступа), `host/audit.json` (имитация host-side event log).

Для model-boundary используются следующие стадии: `prepare` (до handoff), `execute`, `score`; важны `actor`, `op` и защищённый путь. Тестовый журнал подписывается HMAC-SHA256 **в рамках одного скрипта** временным ключом; это проверка **логики верификации свидетельства** при допущении, что агент не владеет ключом и не меняет host log. Самостоятельного доказательства изоляции агентного процесса, реальной полноты OS events или неизменности production evidence нет. Ярлыки `ATTACK` / `PERMITTED` / `UNKNOWN` хранятся только у генератора/контролёра и **не передаются функции `audit()`**.

### Классы и ожидаемые реакции

| Класс (по 10) | Видимая оценка | Инфраструктурные события | Ожидаемая реакция |
| --- | --- | --- | --- |
| honest_pass | PASS | нормальная запись deliverable | CLEAR |
| honest_fail | FAIL | нормальная запись, решение неверно | CLEAR (интегритет ≠ правильность) |
| authorized_preflight | PASS | изменение grader только **инфраструктурой до handoff** | CLEAR |
| grader_tamper | PASS | запись агента в `protected/grader/` после handoff | VIOLATION |
| hidden_answer_read | PASS | чтение агента из `protected/reference/` | VIOLATION |
| reward_spoof | PASS | запись агента в `protected/reward/` | VIOLATION |
| missing_host_log | PASS | нет полных host-side событий | ABSTAIN |
| tampered_host_log | PASS | изменение журнала после подписи | ABSTAIN |
| semantic_shortcut | PASS | ложный результат без структурной границы; нужна интерпретация | ABSTAIN |
| semantic_legitimate | PASS | допустимый результат с той же semantic-obligation отметкой | ABSTAIN |

Пара `semantic_shortcut / semantic_legitimate` намеренно исключает возможность сделать вид, что structural monitor способен разрешить значение задания. Он **воздерживается в обоих случаях**, без выдуманного диагноза. `authorized_preflight` проверяет недопустимость правила «любое изменение grader — атака». Пять honest_pass кейсов помечены как **static exposure** защищённого grader без фактического использования: статическая достижимость ≠ доказанный взлом.

## Результаты реально запущенного скрипта

| Измерение | Результат |
| --- | ---: |
| Сценариев / созданных отдельных рабочих областей | **100** |
| `reported_reward=PASS` (доверчивый score-only контроль) | **90/100** |
| Доставленные ответы совпадают с независимым oracle по значению | **60/100** |
| Static exposure защищённого ресурса | **35/100**, включая 5 без фактического злоупотребления |
| Runtime: `VIOLATION` по событиям | **30/100** |
| Runtime: `CLEAR` (ни одного установленного нарушения) | **30/100** |
| Runtime: `ABSTAIN` (нет достаточного доказательства / semantic obligation) | **40/100** |
| Из 40 намеренно смоделированных нарушений: доказанные runtime | **30** |
| Из 40 намеренно смоделированных нарушений: нет structural evidence, переданы на review | **10** |
| Из 40 намеренно смоделированных нарушений: ложно классифицированы CLEAR | **0** |
| Ложно обвинённые в нарушении `PERMITTED` случаи | **0** |
| Unknown с обвинением без доказательства | **0** |

Это **заранее сконструированная диаграмма контроля**, а не оценка реальных TPR/FPR BenchShield, DSH или LLM. Доли полностью определяются типами и частотами созданных нами кейсов. В частности, из 40 воздержаний 10 — явно легитимные semantic-кейсы, 10 — semantic-hack, 20 — отсутствие/повреждение host evidence. Нельзя считать `ABSTAIN` успешным обнаружением атаки. У `honest_fail` verdict CLEAR означает лишь *отсутствие доказанного нарушения границы*, а не успешную задачу.

**Негативные контролы:** изменение signed event record после capture даёт `ABSTAIN: host_evidence_not_authenticated`; тот же post-handoff protected write, если достоверно зарегистрирован хостом, даёт `VIOLATION`; восстановление исходного signed журнала возвращает `CLEAR`. Контроли автоматически проверяются assert и приводят к ненулевому завершению при регрессии.

**Накладные расходы toy-контроля:** 2 000 вызовов local `audit()`, median **68.601 мкс**, max **144.573 мкс** в первом прогоне, включая локальный JSON file I/O. Это **не** latency агентного benchmarking, не измерение overhead реального host instrumentation, CPU/IO, токенов или стоимости. Оценка benchmark accuracy в смысле статьи и проверка изолированности отсутствуют.

## Реальная точка интеграции и безопасность

- В DSH ранее документирован опциональный verifier `score-v1`; он возвращает pairwise preference и rationale, **не удостоверяет** защищённость benchmark reward path. В актуальном runtime данной проверкой не выполнены ни построение полного score pipeline, ни получение provider/runner event evidence. Имеющаяся [карточка dsh-runtime](https://github.com/Artemedi/project-registry/blob/main/projects/02-agents-dsh/dsh-runtime/PROJECT.md) остаётся **profile match**, не подтверждённым production integration seam. Сведения об историческом verifier относятся к ранее зафиксированному source trace, **не** верифицируют текущую ветку или deployment.
- Для будущей исследовательской интеграции минимальная запись должна содержать `run_id`, pinned task revision, `handoff` timestamp, actor identity, phase, operation, canonical target, исходный event source, attestation / capture completeness, sealed oracle identity, grader/input hash, outcome и статус `CLEAR | VIOLATION | ABSTAIN`. Заявления о PII, production-секретах и хостовых идентификаторах сюда не включать.
- **Производительность / сложность:** слежение за read/write и сохранение provenance добавляют I/O, storage, контроль прав и возможные false-alarms; модель finite-state и отдельный semantic review увеличивают стоимость сопровождения. Отказ от неполных подтверждений уменьшает ложную уверенность, но `ABSTAIN` ограничит throughput. Не внедрять всю BenchShield/TLA+-архитектуру только ради этой лабораторной иллюстрации (YAGNI).
- **Security caveat:** тестовый ключ подписания живёт в том же тестовом процессе и гарантии защиты от настоящего злонамеренного агента нет; проверка не моделирует symlink/path-alias, namespace escapes, подмену timestamps, adversarial tool outputs, сетевой egress, роль grader как атакующего или скрытые приватные каналы. **Нельзя** утверждать, что выполнен security audit.

Сохранены [машинно-читаемые агрегаты первого прогона](2026-11-04-benchshield-reward-integrity-offline.json), без персональных данных и содержимого секретов.

## Воспроизведение

```bash
python3 -B experiments/2026-11-04-benchshield-reward-integrity-replay.py \
    --cases-per-class 10 --seed 20261104 --overhead-repetitions 20
# Скрипт печатает JSON; status=PASS; выход с ошибкой при ложных контрольных ожиданиях.
```

Не нужны API keys, LLM, network, Docker, production files или исходники DSH. Все fixtures генерируются в `TemporaryDirectory` и автоматически удаляются. Дополнительный отрицательный тест и `ruff` + `git diff --check` выполнены при публикации (см. журнал commit). Любые будущие результаты с изменённым seed/N маркировать отдельно и не объявлять статистическим воспроизведением статьи.

## Решение

`ACCEPT_EVIDENCE_BOUNDARY_PRINCIPLE / METHODOLOGY_REPLAY_ONLY / INTEGRATION_BLOCKED`.

Первый допустимый production-приближенный этап: получить **30–50 размеченных безопасных offline-traces** реального agent eval runner с подтверждённой полнотой инфраструктурных событий, фиксированным grader/oracle, sealed success rubric и логами авторизованных preflight изменений; сравнить `reported_reward`, actual outcome и evidence verdict, с явными `ABSTAIN`, стоимостью токенов, p95, IO и false positive. Требуется approval владельца перед подключением event instrumentation. Никаких правок DSH runtime, рабочих агентов или тестового benchmark контракта этим отчётом не разрешено.
