# Helmor — локальная рабочая станция для параллельных coding-агентов

[Структурированная запись и связи](../catalog/studies/helmor.md)

**Тип:** инженерный open-source инструмент, **не** академическая публикация. **Первоисточник:** [dohooo/helmor](https://github.com/dohooo/helmor), pinned [`a76cda1888265fb3e3208562d4b62616a4f0266a`](https://github.com/dohooo/helmor/tree/a76cda1888265fb3e3208562d4b62616a4f0266a), [README](https://github.com/dohooo/helmor/blob/a76cda1888265fb3e3208562d4b62616a4f0266a/README.md), [LICENSE](https://github.com/dohooo/helmor/blob/a76cda1888265fb3e3208562d4b62616a4f0266a/LICENSE) (Apache-2.0). Осмотр 22.11.2026; исходный `package.json` — версия `0.46.0`.

**Обобщённая методология:** `one task → dedicated Git branch/worktree → parallel agent sessions → inspect diff/tests → independent review → explicit ship/merge`. Helmor — прежде всего Tauri/React настольный операторский интерфейс с Bun/TypeScript sidecar и Rust/SQLite, а не автоматический Ralph-loop и не безопасный sandbox.

**VERIFIED (bounded source inspection):** `Worktree` — исходный режим; также существуют `Local` (работа на корне репозитория), `Chat`, `NonGit`. Рабочие файлы/SQLite в release по умолчанию `~/helmor/` (debug `~/helmor-dev/`, переменная `HELMOR_DATA_DIR` переопределяет путь). CLI/MCP реализуют управление workspace/session и отправку prompts; «ship» выполняет GitHub/GitLab действия, часть через инструкции агенту.

**Критическое разграничение:** Git worktree изолирует рабочие деревья и ветки, **не** процессы, учётные данные, сеть, общий Git common-dir, а также пользовательские терминалы. Claude adapter переводит любое значение, кроме `plan`, в `bypassPermissions` и включает `allowDangerouslySkipPermissions`. Codex вне `plan` получает `dangerFullAccess`; даже Codex `plan` устанавливает `workspaceWrite` с writable roots (не гарантированный read-only).

**Платформа:** upstream README предоставляет готовые сборки для macOS/Windows, но не Linux; наличие кода Tauri не доказывает работоспособность Linux release без собственного портирования и проверки. «Всё локально» относится к состоянию приложения: подключённые внешние агенты/провайдеры и optional Cloudflare mobile tunnel могут обмениваться данными с удалёнными сервисами.

**Текущий результат:** `BOUNDED_CODE_REVIEW / ANALYSIS_ONLY / BENEFIT_UNPROVEN / NOT_PRODUCTION_APPROVED`. В проектах не найден подтверждённый готовый интеграционный контракт; возможные цели документального исследования: DSH runtime/operator workflow, политика agent permission/review, human gate для исследовательских результатов. Никакого запуска Helmor, агента, Git push или изменения рабочих проектов не было.

[Датированный исходный аудит](../reviews/helmor/2026-11-22.md) · [портфельный project fit](../portfolio/2026-11-22/helmor.md).
