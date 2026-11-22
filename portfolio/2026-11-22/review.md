# Research intake — fast-anything и profile-guided локальная оптимизация

**Дата/окно:** 2026-11-22, предоставленный пользователем upstream. Исходник [`EL4CTEO/fast-anything@ce0e3889e774a01412c2d181292118fb3512cdde`](https://github.com/EL4CTEO/fast-anything/tree/ce0e3889e774a01412c2d181292118fb3512cdde), GitHub MIT engineering project, не peer-reviewed paper. [Source card](../../studies/fast-anything.md) · [датированный аудит и A/B/C](../../reviews/fast-anything/2026-11-22.md). Дубликат по первичному URL в `research-hub@b809d00376a6001f4e49bb345ec0f7a09c30c908` не найден.

**Цель:** исследовать переносимую методологию `профиль → CPU-hotspot → локальная оптимизация → differential oracle → end-to-end A/B/C → rollback`; Rust — один вариант реализации. Авторские ускорения не воспроизведены.

**Каталог проектов:** [`Artemedi/project-registry@7a976c353579f8da64789daf18fe1088e5ab8dbb`](https://github.com/Artemedi/project-registry/tree/7a976c353579f8da64789daf18fe1088e5ab8dbb). Проведён screening по назначению/стеку всех 45 `PROJECT.md`. Только два документальных кандидата с pinned code anchors; 43 других не названы `NO_FIT`.

| Исследование | Project fit | Почему | Ограничения | Минимальный A/B/C тест | Статус |
| --- | --- | --- | --- | --- | --- |
| [fast-anything](../../studies/fast-anything.md) | **akuzlogparser** | [`akuz_log_parser.py:152–200`](https://github.com/Artemedi/akuzlogparser/blob/d6061aa83cdeadc22e30cfaee36aea94ac131bb2/akuz_log_parser.py#L152-L200) содержит CPU-кандидата `classify`; есть исторические regex замеры | Не подтверждён текущий CPU-share, Unicode и FFI overhead; SSH/IO не ускорятся | Фиксированный synthetic log corpus, A оригинал / B Python / C Rust, independent categories/report oracle, end-to-end wall/CPU/RSS/p95 | `DOCUMENTED_CANDIDATE / BENEFIT_UNPROVEN` |
| [fast-anything](../../studies/fast-anything.md) | **akuz-schema-inventory** | [`parse_sql.py:225–295`](https://github.com/Artemedi/akuz-schema-inventory/blob/f6d4a024cead188050e7addda517780b75e435b7/parse_sql.py#L225-L295) содержит извлечение связей и токенизацию | Не доказан CPU bottleneck, переносимость regex, отсутствие SQLite-доминирования | Frozen synthetic T-SQL, A/B/C с exact oracle edges, gaps и counts, wall/CPU/RSS/p95 | `DOCUMENTED_CANDIDATE / BENEFIT_UNPROVEN` |

**Не shortlisted на этом этапе:** `AKUZ` (ожидания БД и сервисов), `Wiki_PG` (retrieval/DB), `dsh-runtime` (LLM/RPC), остальные 40 — нет подтверждённого CPU-hotspot в данном screening. Это не абсолютный отказ: `DEFERRED_SCREENING`. `Walt` не зарегистрирован в текущем registry, его project-fit нельзя приписывать.

**Приоритет:** (1) `akuzlogparser`, (2) `akuz-schema-inventory`. Практическая ценность методологии 8/10, применимость C неизвестна, сложность эксперимента средняя. **Следующий gate:** Paper2Project document-only analysis, frozen plan и independent reviewer; до измерений `ANALYSIS_ONLY / BLOCKED: MEASUREMENT_MISSING`. Без отдельного разрешения никаких запусков непроверенного upstream, изменений проектов или production.

## Paper2Project — выполненная документальная проверка

Локальный `Paper2Project 1.0.2`, `job-1fd6ba9c847a4a11`. Frozen research snapshot `d4f07b0b88bf62cf676d78d60cdf50147f922ff05069dcbb319dd0acab0f279e`; project snapshots `akuzlogparser:1358285115a7f8d3921911e9e6afbcce069ba2e968ebf4345dbff0297f7c7c6b`, `akuz-schema-inventory:27958666ac2919d4d47c4ac9b7c21c64d7706834f6517db23ba0cc80bcc63bc2`; accepted analysis hash `2104e8027e239507911a5fffea1d0674676eaced41f549435d191294dbb8d14a`.

- Оба target получили `NEEDS_PROJECT_EVIDENCE`; research coverage: `PROVIDED_TEXT_COMPLETENESS_UNATTESTED`. Это не `BENEFIT_PENDING_REVIEW` и не `BENEFIT_DEMONSTRATED`.
- Контекстные цитаты валидированы инструментом и теперь имеют явную привязку к claims; `CLAIM_NOT_LINKED` устранён. Оставшиеся advisory `CHECK_QUALIFIER_NEAR_QUOTE` напоминают, что цитаты содержат оговорки и требуют независимой семантической оценки. Это не автоматическое повышение статуса.
- Внешняя модель не вызывалась; сторонний код/агент/контейнерный эксперимент не запускались. Workspace содержит лишь приватные snapshot источников и документальный анализ; публично опубликованы только обезличенные статусы и хеши.
- Следующий шаг: подтвердить CPU-hotspot на synthetic baseline, затем зарегистрировать независимый oracle и frozen A/B/C план. До этого `BLOCKED: MEASUREMENT_MISSING`; проектные исходники и production не изменены.
