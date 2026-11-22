# Research intake — Helmor: multi-agent operator workbench и Git worktree

**Дата:** 2026-11-22. **Источник:** [`dohooo/helmor@a76cda1888265fb3e3208562d4b62616a4f0266a`](https://github.com/dohooo/helmor/tree/a76cda1888265fb3e3208562d4b62616a4f0266a), Apache-2.0, `package.json 0.46.0`. Это engineering source, не peer-reviewed paper; точный URL/название не обнаружен в старом `research-hub@b809d00376a6001f4e49bb345ec0f7a09c30c908`.

**Обобщённая методология:** `task → worktree → concurrent coding agent → diff/independent test → owner review → bounded ship`. [Canonical source](../../studies/helmor.md) · [source audit и проверяемый A/B/C](../../reviews/helmor/2026-11-22.md).

**Project registry:** `Artemedi/project-registry@7a976c353579f8da64789daf18fe1088e5ab8dbb`. Screened 45 `PROJECT.md` по purpose/stack; shortlisted 3 документационных гипотезы, не подтверждённые интеграционные контракты. Из публичного архива не раскрываются приватные файлы и код проектных конфигураций.

| Исследование | Целевой проект | Почему условно применимо | Ограничения | Минимальная проверка | Доказательный статус |
| --- | --- | --- | --- | --- | --- |
| [Helmor](../../studies/helmor.md) | **dsh-runtime** | По реестру есть собственный agent runtime, workspace и web-контур; гипотеза UI для параллельных задач | Helmor — отдельный desktop, не drop-in компонент; Mac/Windows release, не Linux; Git worktree не sandbox | Сравнить управление frozen synthetic задачами через CLI против Helmor GUI; независимые тесты, конфликты, время оператора | `DOCUMENTED_CANDIDATE / NEEDS_EVIDENCE` |
| [Helmor](../../studies/helmor.md) | **agent-config** | Политика agent permissions/review может быть external guard для ship и per-agent runs | Claude bypassPermissions, Codex dangerFullAccess; не переносить API keys/конфиги в test | Фиктивный agent, корректный отказ dangerous actions, строгая allowlist и независимый тест-оракул | `DOCUMENTED_CANDIDATE / NEEDS_EVIDENCE` |
| [Helmor](../../studies/helmor.md) | **dsh-paper2agent** | Отдельный developer/operator UI для запуска задач и проверки human gate после исследовательского анализа | Не заменяет evidence pipeline/isolated Podman; всё равно нужен отдельно подтверждённый Linux/workflow путь | Paper2Project документальный dry-review → stub Helmor UI → no merge/no production; измерить качество audit handoff | `DOCUMENTED_CANDIDATE / NEEDS_EVIDENCE` |

**Risk/cost:** 7/10 исследовательская ценность инструмента для организации параллельной работы (экспертная, не измеренная); 3/10 актуальная готовность к безусловной интеграции в Linux workflow. Worktrees share common Git metadata; local state is not local model inference; cloud provider/optional Cloudflare companion могут передавать данные наружу. CLI/MCP операции включают destructive workspace delete и ship/merge actions; human confirmation требуется независимо от agent prompt. Участие Helmor в реальной разработке остаётся **BLOCKED: NO_SAFE_COMPATIBLE_LAB**.

**Стратегия:** A = ручные CLI/worktree, B = Helmor GUI с fake agents на официально поддерживаемой однотипной OS, C = Helmor CLI/MCP с independent safety/quality gate. Same host/task/model budget; сравнивать `accepted_valid_tasks/operator-hour`, wrong branch, conflicts, CPU/RAM, токены, leakage, review latency и rollback. `ANALYSIS_ONLY / BENEFIT_UNPROVEN / NOT_PRODUCTION_APPROVED`. Ни один рабочий репозиторий или PR не изменён этим исследованием.

## Paper2Project — выполненный документальный анализ

Локальный `Paper2Project 1.0.2`, `job-64e42e6b31c34b30`. Snapshot исследования: `a54df7cc8730b5f36071319e191f9b174f1837e1de753de4a0883719eee86367`. Замороженные входные карточки проектов: `dsh-runtime=c12abd28e6f5110572ccd8189720e47ff392470fd78dae17457e03812056610c`; `agent-config=f7288f5353cabc3c788a20273ffc23206bb7eebde23b40f62c6c629ebf577dfd`; `dsh-paper2agent=28bfba4d7aea8fff9825f4a6d13358a837d2a2479aa17235898b17e99dc9baa7`. Accepted analysis hash: `7f54dcd9dd7ca66abd83703362e1380e29d11260d5cdd3bfd3acc2aba0c9c6d6`.

- По каждому проекту документальный вердикт **`NEEDS_PROJECT_EVIDENCE`**; source import охватывает исследовательский обзор и не аттестует полноту или бинарную версию upstream. `BENEFIT_DEMONSTRATED` отсутствует.
- Контекстные цитаты зафиксированы; автоматические advisory `NEGATION_MISMATCH` и `CHECK_QUALIFIER_NEAR_QUOTE` остаются **открытыми**, без самостоятельной корректировки статуса. Независимая семантическая проверка требуется до design/integration decision.
- Paper2Project selftest — **PASS**. Внешняя модель не вызывалась, third-party Helmor/agents не запускались, реальные Git worktrees/branches проектов не изменялись, PR/merge от имени Helmor не выполнялись.
- Следующий gate — только fake-agent workspace lab на официально поддерживаемой ОС под ограниченной отдельной учётной записью и с независимым verifier. Linux release compatibility и возможность безопасной интеграции в DSH остаются `BLOCKED: NO_SAFE_COMPATIBLE_LAB`.
