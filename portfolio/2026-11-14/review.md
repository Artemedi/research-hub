# Research Intake — новые источники и повторная оценка 11–14 ноября 2026

**Срез 14.11.2026**, после портфельного обзора 04–11.11.2026. Точка начала: research-hub main 113b6ae10f2255b41086238c00a6d5cbd917c288 и project-registry 45 PROJECT.md; текущие рабочие исходники целевых проектов прочитаны по указанным в обзорах immutable SHA. Применён [research-intake](https://github.com/Artemedi/agent-skills/tree/163d928460247d3d40a936504fda8d5d82ae7cc2/research-intake), включая трехисходный контракт. Не заявляется сплошной сбор всего arXiv: окно = известных новых сигналов 12–14.11 + два пропущенных v3 и пропущенный SPILLWAY 04.11.

## Discovery / dedup

- Telegram BK ledger: 65 записей, 0 awaiting review; не создавать новые BK-ID и не переписывать историческую таблицу.
- Scientific Journal Review от 14.11: 0 новых журнальных работ в покрытом Gmail-интервале; сам плагин Journal Review в этом контексте не установлен. Эти два факта не равны отсутствию новых научных работ вообще.
- Основной research-hub: 88 зарегистрированных исследований, актуальные 11.11 карточки AvalancheBench v2, Adaptive Injection Swarms и Actions log scanning **не дублировались**.
- **Повторно открыт прежний FULL_TEXT_UNAVAILABLE:** JetStream v3 (полный PDF 14 pp теперь получен), статические галлюцинации библиотек v3 (полный TMLR PDF 24 pp). Ранний статус был корректным на момент прежнего обзора, нынешняя запись **датированная** и не переписывает архивную историю.
- **Новые первоисточники:** database debugging field study (12.11), ReA-Bench (12.11), MobileProbe (12.11); **пропущенный в предыдущем окне первоисточник:** SPILLWAY (04.11). Все шесть полных PDF прочитаны по method/results/limitations. Бенчмарки авторов НЕ воспроизводились, private source and production не использовались.

## Матрица «исследование → конкретный проект»

Статус в последнем столбце — дословная evidence qualification, а не одобрение внедрения. Review перечисляет source seam и отдельно его недостающие контракты.

| Исследование | Целевой проект | Предметное соответствие PROJECT.md | Ограничения | Минимальный следующий тест | Статус |
| --- | --- | --- | --- | --- | --- |
| JetStream | akuz-optimizer-twin | Есть отдельный PostgreSQL 18 twin для EXPLAIN и проверки планов; необходимо понять пределы специальных ускорителей, но целевой исполнитель не построен | Twin почти пустой и не исполняет аналитические SELECT; цифры JetStream TPC-H здесь не измеримы; чужой extension не ставить | Отдельная полностью искусственная populated PG/DuckDB fixture, gold-query outputs, update-stream correctness, total maintenance cost | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |
| Static library hallucination analysis | dsh-paper2agent | Проект выполняет Python author-code adapters с независимым comparator и источниками, закреплёнными по SHA | Pyright/Mypy не доказаны в текущем workflow, Python-only; static green не scientific correctness | 30–50 frozen Python API fixtures, A existing checks vs B pre-run static warnings, independent execution oracle и false positive rate | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |
| Database agent observability field study | sequential-rca | Offline RCA принимает observations и проверяет доказательные causal claims, умеет abstain | Полевая выборка восемь инцидентов, нет причинного теста; production access не требуется | A truncated lock/deadlock evidence vs B recorded bounded flight-recorder evidence на 12 synthetic incidents, independent DBA oracle | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |
| Database agent observability field study | Wiki_PG | DBA knowledge/diagnostic snapshots уже различают отсутствующие и доступные сведения | Есть snapshot parser, но нет подтверждённого live lock recorder/разрешения дополнительных наблюдений | Compare read-only snapshot completeness and time-provenance on 12 synthetic transient concurrency incidents | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |
| ReA-Bench | dsh-runtime | Tool-call lifecycle пишет реальные call/result sequence, возможна изолированная проверка error/benign audit | 8 model configs и одна оценка на config, высокая доля hard benign negatives, нет целевого DSH oracle | 30–60 fictional call trajectories, policy snapshots and effective side-effects; recall@FPR≤5%, benign false blocks | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |
| SPILLWAY | dsh-runtime | В agent-loop есть prepare→dispatch; можно офлайн проверить target admission перед side effects | Paper zero относится только к 12 AgentDojo cells; нынешний SDK отличается; policy/admission в DSH не проверены | 20–30 fake recipient/taint-negative fixtures, A current mock vs B deterministic target allowlist, unauthorized dispatch and benign completion | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |
| MobileProbe | NO_FIT | В 45 карточках нет Android mobile GUI agent с управляемым виртуальным экраном и action oracle | 83 сценария/12 приложений Android, неприменимы напрямую к desktop/tool agents | Пересмотреть только при появлении соответствующего Android/mobile проекта и безопасного AVD lab | NO_CURRENT_MOBILE_AGENT_TARGET / DEFERRED |

## Практические приоритеты и строгость доказательств

1. **P1 — безопасная forensic observability и false diagnosis:** database field study → sequential-rca/Wiki_PG, но фактически разрешены только offline replay и synthetic evidence; из наблюдения нет оснований выдавать агентам production SQL доступ.
2. **P1 — контроль действий и аудита:** SPILLWAY + ReA-Bench на dsh-runtime; измерять реальные эффекты, предупреждать false-denials и отсутствие внешних правил. Не клонировать новые runtime middleware или обязывать paid judge.
3. **P2 — проверяемый результат с ограничениями:** JetStream как архитектурный справочник для PostgreSQL/OLAP и dsh-paper2agent static-check research; пустой optimizer twin не является экспериментальным аналогом JetStream.
4. **Deferred — MobileProbe:** научный источник настоящий, но ни один зарегистрированный портфельный проект не имеет эквивалентного mobile-agent interface.

## Стоимость, воспроизводимость и gates

В каждом предлагаемом тесте fixed SHA/source bundle, pre-registered positive/negative fixtures, независимый deterministic/DBA oracle, frozen calibration/holdout, минимум 3 повторения для nondeterministic results, CPU/RAM/VRAM/IO/latency и token/LLM cost (как UNKNOWN, если не измерены), остановка при false benefit. Без согласованного baseline **BLOCKED: MEASUREMENT_MISSING**, не выдумывать PASS. Никаких платных LLM, сетевых offensive attacks, чужих executables, sudo/eBPF, production SQL, пользовательских конфигураций или DB grants.

**Источники для полного review:** [JetStream](../../reviews/jetstream/2026-11-14.md), [static library detection](../../reviews/static-library-hallucinations/2026-11-14.md), [database field study](../../reviews/database-agent-observability/2026-11-14.md), [ReA-Bench](../../reviews/rea-bench/2026-11-14.md), [SPILLWAY](../../reviews/spillway/2026-11-14.md), [MobileProbe](../../reviews/mobileprobe/2026-11-14.md). Исторический [11.11 review](../2026-11-11/review.md) остаётся неизменным.

**Результат route:** 5 источников «Добавлен в карточки», 1 источник «Рассмотрен и отложен». User-facing outcome и project-specific evidence **независимы**. Runtime integration / production authorization не предоставлены.
