# Claude Swarm — отказоустойчивость worktree и подтверждение завершения

**Дата:** 07.11.2026. Инженерная контрпроверка ранее принятого ограниченного набора [107 upstream тестов](../../data/results/research-portfolio/2026-11-07-claude-swarm-upstream-tests.json). **Source pin:** [cj-vana/claude-swarm@31f19199bf3557cda4860231186a06b72c8edb94](https://github.com/cj-vana/claude-swarm/tree/31f19199bf3557cda4860231186a06b72c8edb94). Полная инженерная проверка исходников `src/workers/manager.ts`, `worktree-manager.ts`, `lock-manager.ts`; точные SHA-256 файлов сохранены в JSON.

**Область:** реальный собранный upstream TypeScript-код `WorkerManager`, `WorktreeManager`, `TaskLockManager` на *отдельном временном Git-репозитории*. Запускался настоящий `tmux` с частным `TMUX_TMPDIR`. Команда `claude` намеренно подменена synthetic shell script, не запускающим модель, не загружающим реальные сессии или токены и не отправляющим пользовательские данные вовне. Ни один исходный целевой проект не изменялся. `npm ci --ignore-scripts`, `npm run build`, upstream `vitest`: **107/107 PASS**; сценарии ниже дополняют, а не заменяют upstream тесты.

## Независимые runtime-оракулы: 15/15 воспроизведены

| Условие отказа / негативный контроль | Наблюдение на pinned upstream | Диспозиция |
| --- | --- | --- |
| Два одновременно созданных worktree, незакоммиченные файлы | Изоляция каталогов соблюдается; файлы `alpha.txt` и `beta.txt` не пересекаются | **PASS_BOUNDED** |
| Atomic file lock у A и попытка B | B получает конфликт; без explicit `releaseAll` stale lock сохраняется и мешает повторному захвату | **PERSISTENT_LOCK_NEEDS_RECOVERY** |
| Ручной `releaseAll(A)` | B получает освобождённую блокировку | **PASS_MANUAL_RECOVERY** |
| Повторное `createWorktree(alpha)` с незакоммиченным `alpha.txt` | **Файл исчезает**, worktree пересоздаётся, ветка снова указывает на исходный HEAD | **REWORK_DESTRUCTIVE_RETRY** |
| Worker успешно создаёт `.done` относительно `cwd` worktree и завершается с exit 0 | `checkWorker()` выдаёт **crashed**, так как ищет `.done` в основном проекте | **REWORK_DONE_PATH_MISMATCH** |
| Mock CLI пишет `.done` в основной проект и завершается exit 7 | `checkWorker()` выдаёт **completed** по наличию маркера; shell pipeline пишет `WORKER_EXITED` | **REWORK_FALSE_COMPLETION** |
| Сгенерированные флаги worker без overrides | `--permission-mode bypassPermissions` и `Bash,Read,Write,Edit,Glob,Grep` | **HIGH_RISK_DEFAULT** |
| Основной Git HEAD после теста | Не изменён; временный tmux server и worktrees очищены | **PASS_ISOLATION** |

15 отдельных assert с наблюдаемыми значениями и ожидаемыми состояниями опубликованы в [машинных доказательствах](../../data/results/research-portfolio/2026-11-07-claude-swarm-failure-e2e.json). Формулировка `15/15` означает, что **в том числе ошибочные свойства удалось воспроизвести**, а не что Claude Swarm успешно прошёл 15 проверок качества. Ещё одна подтверждённая граница: блокировки после аварийного завершения не имеют доказанной автоматической lease/TTL-recovery.

## Причины и минимальные контрмеры (без внедрения)

1. **Destructive retry:** [`WorktreeManager.createWorktree`](https://github.com/cj-vana/claude-swarm/blob/31f19199bf3557cda4860231186a06b72c8edb94/src/workers/worktree-manager.ts) перед созданием вызывает `removeWorktree(featureId)`, использует `git worktree remove --force`, затем удаляет одноимённую ветку. Незакоммиченный прогресс уничтожается, даже когда предшествующий worker фактически продолжал работу. Требование: fail-closed при занятом/dirty worktree, явное checkpoint/archive и только после подтверждения stop + доступного rollback — осознанный reset. Trade-off: дополнительные Git IO/диск, но исключение silent loss.
2. **Done path:** [`WorkerManager.startWorker()`](https://github.com/cj-vana/claude-swarm/blob/31f19199bf3557cda4860231186a06b72c8edb94/src/workers/manager.ts) запускает CLI в `workingDir=worktreePath`, промпт указывает относительное `.claude/orchestrator/workers/<id>.done`, а `checkWorker()` ищет маркер в `projectDir`. Требование: один абсолютный session-scoped путь и проверка соответствия session/feature ID + git SHA; отрицательные тесты устаревшего/чужого маркера.
3. **False completion:** `checkWorker()` классифицирует результат только по наличию `.done`; wrapper использует конвейер `claude ... | tee` без `set -o pipefail` и завершает `WORKER_EXITED` после mock exit 7. Требование: exit-code marker, атомарная запись статуса, проверка commit/verification state и отрицательный case exit nonzero+done; fail-closed при неоднозначности.
4. **Permissions:** по умолчанию `bypassPermissions` в сочетании с `Bash,Write,Edit`. До pilot на внешних агентных задачах необходима минимальная allowlist, реальное ограничение FS/credentials вне промпта и проверка enforcement; простая смена флага без ограничения процесса не является sandbox.

**Независимая модельная критика:** два последовательных запроса ZCode для ролей `safety_critic` и `failure_critic` завершились timeout 50 секунд, поэтому **2× `BLOCKED_PROVIDER`**, никаких правдоподобных выдуманных PASS и новых модельных выводов. Runtime-оракул — фактические Git/tmux файловые состояния. Повторять эти неудачные роли без нового основанного на рисках протокола не требуется.

## Воспроизведение

- [Изолированный E2E-скрипт](../../experiments/research-portfolio/2026-11-07-claude-swarm-failure-e2e.mjs), [данные 15 проверок](../../data/results/research-portfolio/2026-11-07-claude-swarm-failure-e2e.json).
- [Запуск и checkpoint ZCode-критиков](../../experiments/research-portfolio/2026-11-07-claude-swarm-critics.py), [два таймаута](../../data/results/research-portfolio/2026-11-07-claude-swarm-critics.json).
- Извлечь только публичный исходник `31f1919` в отдельный временный каталог; `npm ci --ignore-scripts`, `npm run build`, `npm test`; запустить скрипт с `CLAUDE_SWARM_SOURCE=<clean clone>`, `OUTPUT=<local result JSON>`. Сценарий сам создаёт/удаляет синтетический Git repo, отдельный tmux socket и fake CLI.

**Вердикт:** `REWORK_UPSTREAM_WORKER_LIFECYCLE`, `ACCEPT_SYNTHETIC_REPRODUCTION`, `NO_NEW_PROJECT_FIT`, `NO_PRODUCTION_APPROVAL`. Никакой перенос worker manager на `dsh-runtime` или `dsh-claude-primary-agent` до новых отказоустойчивых E2E. Следующая проверка — адресное исправление только на изолированной fork/worktree копии, повторный fault-injection A/B, отдельные расходы CPU/RAM/FS IO/latency, затем ручной owner gate.
