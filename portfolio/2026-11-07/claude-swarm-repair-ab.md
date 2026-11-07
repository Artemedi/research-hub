# Claude Swarm: изолированный A/B хирургических исправлений worker lifecycle

**Дата:** 07.11.2026. Продолжение [первого воспроизводимого fault-injection](claude-swarm-failure-injection.md). Изученный upstream: [cj-vana/claude-swarm@31f19199bf3557cda4860231186a06b72c8edb94](https://github.com/cj-vana/claude-swarm/tree/31f19199bf3557cda4860231186a06b72c8edb94); в целевой проект, `dsh-runtime`, оригинальный GitHub repo и production **ничего не внедрено**. Исправления существуют только в временном изолированном checkout и как переносимый [unified diff](../../experiments/research-portfolio/2026-11-07-claude-swarm-recovery.patch.gz) с SHA-256 распакованного diff `84a6ac46a2de4f66af9df6950a826a1e5880d3f348289f7ff9c2d9a2c1fd97a9` (архива gzip: `e6df883e4ebcdb7710873dc4aecb6d4c6271dec5c94f94985a98e43b1452b581`).

## 1. Предпосылка и сравниваемые состояния

- **A — исходный upstream:** [15 наблюдений предыдущего теста](../../data/results/research-portfolio/2026-11-07-claude-swarm-failure-e2e.json), включая три **воспроизведённых дефекта**: `createWorktree(featureId)` удаляет dirty worktree при повторном запуске, успешный worktree worker помечается crashed из-за относительной `.done`, и worker с exit 7 + основным `.done` помечается completed.
- **B — source-pinned исправление:** 39 строк диффа (**24 добавления, 15 удалений**) только в `src/workers/manager.ts` и `src/workers/worktree-manager.ts`. Патч наложен и проверен также на **втором чистом checkout** того же upstream SHA; SHA-256 исправленных файлов `manager.ts=1e3d61fab679960db5608df890a486823a877577bb28754ff4b0c989f8faebb8`, `worktree-manager.ts=583868ad3e95ff81345e8b3aa857c7543af56c0aedefa6c229ce250d3be172e8`. На чистом восстановлении: `npm ci --ignore-scripts`, `npm run build` успешен, `npm test` **107/107**.
- **B — новые fault-injection:** [19/19 детерминированных ожидаемых наблюдений](../../data/results/research-portfolio/2026-11-07-claude-swarm-repair-ab.json), включая контроль **оставшегося уязвимого механизма**. `19/19` — соответствие воспроизводимому oracle, **не** процент устранённых уязвимостей и не регрессионное покрытие всей системы. Как и в A, используются реальные собранные upstream `WorkerManager`/`WorktreeManager`/`TaskLockManager`, временный Git, отдельный tmux server и подставной CLI; реальный Claude Code не выполнялся.

| Рубеж | A: upstream | B: изолированный patch | Интерпретация |
| --- | --- | --- | --- |
| Повторная попытка того же feature ID при dirty worktree | Удаляет незакоммиченный файл `alpha.txt`, пересоздаёт ветку | Отказывает: `explicit recovery required`, сохраняет файл и ветку | **REPAIRED_BOUNDED**; ручное восстановление/очистка обязательны |
| Ошибка создания worktree в `startWorker` | Молча переключается на общий project dir | Возвращает failure, общий режим не используется | **FAIL_CLOSED_BOUNDED** |
| Успешный worker пишет done по инструкции | Относительный путь в worktree; проверка в основном repo возвращает `crashed` | Промпт указывает **абсолютный session-specific done path**; exit 0 + done дают `completed` | **REPAIRED_BOUNDED** |
| CLI пишет done и выходит с кодом 7 | `tee` скрывает ошибку; менеджер возвращает `completed` | Shell сохраняет `PIPESTATUS[0]` в session-specific `.exit`; менеджер возвращает `crashed` | **REPAIRED_BOUNDED** |
| Worker злонамеренно подменяет собственный `.exit` на `0` после отказа | Не проверялось | Вызов менеджера ошибочно возвращает `completed` | **STILL_VULNERABLE**: exit-файл — диагностика, не криптографическая attestation |
| Конфликт файла при одновременном захвате lock | Корректно блокируется; stale lock сохраняется | Корректно блокируется; автоматического recovery нет | **UNRESOLVED** |
| Worker permission flags по умолчанию | `bypassPermissions`, `Bash,Write,Edit` | Не менялись | **HIGH_RISK_DEFAULT** |

## 2. Выбранная минимальная стратегия и trade-offs

- `WorktreeManager.createWorktree()`: один `git branch --list` и `fs.existsSync` перед созданием; удалены автоматические `removeWorktree --force` и `branch -D`. **Дополнительные Git IO/время** одного процесса на старт; **не теряется незакоммиченный прогресс**; stale worktree блокирует запуск до осознанного восстановления. Не заявляется atomic multi-process lock или race-free scheduling.
- `WorkerManager.startWorker()`: fail-closed при ошибке создания Git-worktree вместо fallback в shared mode; абсолютный session-qualified `.done`. **Меньше availability**, больше изоляции и диагностируемости; добавляется путь в промпт, несколько байт FS metadata.
- `checkWorker()` и shell wrapper: сохраняется числовой exit-код CLI до выхода wrapper, успешный verdict требует exit 0 **и** правильного done. Накладные **одна запись и две проверки/чтения файла** на worker; память O(1). На добровольно действующем worker устранён false completion. При **враждебном worker**, который имеет write access к marker-файлам, целостность exit-кода не обеспечена — negative control это явно воспроизвёл.
- Микробенчмарки CPU/RAM/IO/latency на репрезентативной нагрузке не проводились; оценки выше — количество вызовов/операций из исходников. Не надо представлять их как реальные показатели производительности.

## 3. Приёмка и пределы доказательств

Полноценная верификация включала применимость patch к новой исходной ревизии Git, `git diff --check`, TypeScript build, **107/107 upstream vitest**, **19/19 новых fixture checks**, неизменный HEAD синтетической ветки после всех тестов и очистку временных tmux/worktree. Два специальных ZCode критика (`lifecycle_skeptic`, `security_skeptic`) были вызваны как совет, но после повторной ограниченной попытки оба остались **`BLOCKED_PROVIDER`** (timeout и nonzero provider exit). Нет основания называть их результаты независимым рецензированием; [протокол ошибок](../../data/results/research-portfolio/2026-11-07-claude-swarm-repair-council.json).

**Ключевое ограничение:** исправление устраняет три дефекта **для добросовестного worker в проверенном режиме**. Оно не является security sandbox, не предотвращает подделку маркера, не решает проблемы stale locks, concurrent races, dead worker leases, non-worktree/continuous/planner modes, hard-kill между частичными записями и полномочиями `bypassPermissions`. Для тех же feature IDs необходим безопасный ручной recovery после диагностики dirty worktree, а не бесконтрольный retry.

**Решение:** `ACCEPT_BOUNDED_REPAIR_REPRODUCTION`, `REWORK_WORKER_AUTHORIZATION_AND_RECOVERY`, `NO_PRODUCTION_APPROVAL`, `NO_NEW_PROJECT_FIT`. Для включения в `dsh-runtime` или другого target проекта требуется дополнительный fail-stop/permission enforcement, multi-process regression, независимый аудит и явное разрешение.

## 4. Как воспроизвести

[Точный patch](../../experiments/research-portfolio/2026-11-07-claude-swarm-recovery.patch.gz) · [E2E скрипт с 19 оракулами](../../experiments/research-portfolio/2026-11-07-claude-swarm-repair-ab.mjs) · [машинные результаты](../../data/results/research-portfolio/2026-11-07-claude-swarm-repair-ab.json) · [скрипт двух ZCode критиков](../../experiments/research-portfolio/2026-11-07-claude-swarm-repair-council.py).

На **одноразовом** клоне upstream с точным ref `31f19199...` проверить `gzip -dc <patch.gz> | git apply --check`, затем `gzip -dc <patch.gz> | git apply`; выполнить `npm ci --ignore-scripts --no-audit --no-fund`, `npm run build`, `npm test` и `CLAUDE_SWARM_SOURCE=<clone> OUTPUT=<result.json> node <E2E-script>`. Используется только mock CLI из приватного временного каталога, без реальной авторизации Claude. Исходный upstream и все настоящие проекты остаются неизменными.
