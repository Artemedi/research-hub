# REA — границы статического анализа

Дата записи: 2026-11-05. Перенос структуры: 2026-11-05; выводы и область проверки сохранены.

**Рассмотрен и отложен:** актуальный первичный код доступен, но полноценный source review и независимая проверка parser/provider pipeline **не завершены**. Это промежуточная проверка границ, а не завершённый глубокий разбор. Исторический статус остаётся **ожидает проверки**. [Карточка](../../studies/reverse-engineer-anything.md), [triage всех 45 профилей](../../data/project-fit/reverse-engineer-anything/2026-11-05-initial.json).

## Проверенные источники

05.11.2026 загружен [morluto/rea@970969cb53f788976e64eae387076fcea104b603](https://github.com/morluto/rea/tree/970969cb53f788976e64eae387076fcea104b603), package.json 6.8.0. Прочитаны README, AGENTS, security boundary, managed-code contracts, соответствующие provider metadata, начало provider dispatcher и snapshot admission, bounded reader. Изучены testing lanes и структура managed parser/tests. Остальной большой репозиторий **не считается полностью проверенным**. `FULL_TEXT_UNAVAILABLE` здесь неверен: исходник доступен. `FULL_TEXT_VERIFIED`, `LAB_VERIFIED`, `PRODUCTION_APPROVED` не присвоены.

Корневая лицензия MIT. [THIRD_PARTY_NOTICES.md](https://github.com/morluto/rea/blob/970969cb53f788976e64eae387076fcea104b603/THIRD_PARTY_NOTICES.md) сохраняет отдельные third-party terms; лицензия REA не даёт права на сторонние commercial tools или анализ любого бинарника. Полного license audit не было.

## Что установлено по коду

REA — локальный CLI/MCP workflow, а не единый безопасный sandbox. [SECURITY.md:27](https://github.com/morluto/rea/blob/970969cb53f788976e64eae387076fcea104b603/SECURITY.md#L27) описывает capability-token bridges и прямо отделяет их от OS isolation. Same-user malicious process не входит в защищаемую границу. Внешние provider parsers работают с правами своего пользователя. Локальное выполнение также не означает, что данные не попадут model provider вызывающего агента.

Есть предметно более узкий путь для игровых .NET assemblies: [src/dotnet/ManagedStaticProvider.ts:49](https://github.com/morluto/rea/blob/970969cb53f788976e64eae387076fcea104b603/src/dotnet/ManagedStaticProvider.ts#L49) отделяет execution-free PE/CLI provider от иных операций. [ManagedStaticProviderMetadata.ts:9](https://github.com/morluto/rea/blob/970969cb53f788976e64eae387076fcea104b603/src/dotnet/ManagedStaticProviderMetadata.ts#L9) объявляет static effects и ограничения: metadata/CIL не равны исполненному поведению или восстановленному C#. Это **декларация контракта плюс прочитанный dispatch**, не доказательство всех транзитивных путей.

[ManagedSnapshot.ts:31](https://github.com/morluto/rea/blob/970969cb53f788976e64eae387076fcea104b603/src/dotnet/ManagedSnapshot.ts#L31) задаёт 128 MiB admission для одного PE snapshot. `readManagedSnapshot` использует bounded reader и вычисляет SHA-256. `verifyManagedSourceIdentity` сравнивает наблюдённый digest с выбранным target. [BoundedFileBytes.ts:10](https://github.com/morluto/rea/blob/970969cb53f788976e64eae387076fcea104b603/src/process/BoundedFileBytes.ts#L10) проверяет byte limit и cancellation; версия без expectedSize читает до EOF с обнаружением overflow. Это resource policy, не абсолютная граница heap/RSS или доказательство безопасности parser на враждебном входе.

[docs/managed-code-analysis.md](https://github.com/morluto/rea/blob/970969cb53f788976e64eae387076fcea104b603/docs/managed-code-analysis.md) различает build-local metadata token, MVID и digest; partial/unavailable coverage не означает отсутствие типа/метода. Unity IL2CPP не следует выдавать за обычный managed PE parser: для него другой путь. Native decompilation, dynamic process capture, browser/ADB/Frida и установка provider — отдельные поверхности риска. Эти режимы здесь не запускались.

## Портфель и неподтверждённые кандидаты

Реестр: `Artemedi/project-registry@0e80ec6` (после документальных BK-060 backlinks; профили относительно `fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6` не изменены). Все 45 ID индивидуально перечислены в JSON. Это profile triage, не проверка исходников всех проектов.

| Исследование | Проект-кандидат | Предметное основание | Ограничение и минимальный следующий тест | Evidence |
| --- | --- | --- | --- | --- |
| BK-062 | `MyPartyIsGrinding` | Профиль модов: metadata/call relationships могут помочь анализу разрешённой assembly. | Не прочитан текущий game/mod binary contract. Собственный toy PE с независимым metadata oracle, затем отдельно разрешённый артефакт. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| BK-062 | `WarOfGenesisIdleLoot` | Профиль C# mod: static member inventory и build comparison. | Mono/IL2CPP/runtime form не подтверждены для конкретного входа; нельзя обещать декомпиляцию/поведение. Тот же toy baseline плюс malformed PE и duplicate names. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| BK-062 | `game-localization-guide` | Профиль извлечения ресурсов: сравнить inventory и provenance. | Сначала выбрать конкретный engine/container и разрешённый fixture; managed parser не доказывает извлечение всех форматов. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |

Это кандидаты для дальнейшего изучения, **не новые подтверждённые implementation seams**. Старые предварительные backlinks не повышены и не дублируются. `psqlqa` остаётся условным лишь для разрешённой package inspection. DBA/RCA, медицинские профили, routing, memory, task governance и reference forks не получают связь только потому, что REA может анализировать произвольную программу. Проект коллеги рассмотрен по brief: source неизвестен, публикации его содержимого нет.

## Неисполненный gate

Runtime/target execution, provider installation, setup, реальные бинарники, credentials и сетевые LLM не использовались. Зависимости отсутствуют; `npm ci` намеренно не запускался. Полные tests/lint/build `NOT_RUN / BLOCKED_ENV`; повторять историю BK-060 с авторазрешением пакетов не требуется. Это не результат отрицательного parser-теста.

Следующий минимальный план: завершить чтение managed parser и фактического dispatch/retention path, выбрать существующие original managed boundary tests, подготовить dependency-complete offline стенд. Только authored fixture: known module/MVID/types/methods/CIL, независимый ECMA-335 oracle, negative twins (truncation, overlapping sections, malformed heaps, capacity overflow, cancelled read). Сравнить original output с oracle в трёх детерминированных повторах; mutation control должен нарушать ожидаемый факт. Ни один fixture не исполнять. Предел предложенного опыта: 1 CPU worker, 512 MiB budget, 60 s timeout, read-only source и входы, временный output без model/network; фактические CPU/RSS/IO пока не измерены.

Для игровых целей дополнительно нужны разрешение на выбранный материал, pinned current source и baseline. До них `BLOCKED: MEASUREMENT_MISSING`. Следующая публикация должна ссылаться на этот промежуточный отчёт и явно отделять завершённый source review от этой проверки границ. Production-интеграции нет.
