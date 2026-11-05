# Agent Desktop — ссылки и разрешения

Дата записи: 2026-11-05. Перенос структуры: 2026-11-05; выводы и область проверки сохранены.

**Рассмотрен и отложен:** текущий код доступен, но полный source review, сборка и disposable GUI/Wayland проверка **не завершены**. Это промежуточная проверка границ, не завершённый глубокий аудит. Исторический статус **ожидает проверки** сохранён. [Карточка](../../studies/vercel-agent-desktop.md), [triage 45 профилей](../../data/project-fit/vercel-agent-desktop/2026-11-05-initial.json).

## Версия и границы прочитанного

05.11.2026 загружен [vercel-labs/agent-desktop@b43ac4f6e892ef608f8851428613c4009f0e84c7](https://github.com/vercel-labs/agent-desktop/tree/b43ac4f6e892ef608f8851428613c4009f0e84c7), workspace 1.2.0, Apache-2.0. Это **не прежний** SHA `6660fbac768dc7e7332837b90ed465684859afa3` из предварительной матрицы; старые выводы на текущую версию автоматически не перенесены.

Прочитаны README, AGENTS, CONTRIBUTING, SECURITY, command permission preflight, interaction policy, ref token parser и его тесты, начало strict saved-ref resolution, Windows permission probe, Linux refusal tests, начало MCP transport. Весь adapter stack и все тесты не проверены. Исходник доступен: `FULL_TEXT_UNAVAILABLE` не используется; `FULL_TEXT_VERIFIED`, `LAB_VERIFIED`, `PRODUCTION_APPROVED` не присвоены.

## Наблюдаемая архитектура

Инструмент — Rust CLI/C library и stdio MCP, **без встроенной LLM**. Loop observe→act→verify принадлежит вызывающему агенту. Backend — AX/UIA/AT-SPI; отсутствие accessibility tree означает отсутствие видимости, а не разрешение угадывать действия. Это важно для game/canvas interfaces и GUI acceptance.

[crates/core/src/refs/ref_token.rs:19](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/core/src/refs/ref_token.rs#L19) разбирает snapshot-qualified `@snapshot:eN` и отклоняет bare refs; [оригинальные tests](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/core/src/refs/ref_token_tests.rs) проверяют qualified/bare/zero cases. Это проверка синтаксиса, не доказательство свежести цели.

[resolve_saved_ref.rs:29](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/core/src/refs/resolve_saved_ref.rs#L29) различает retained native token и tokenless identity predicate. Во втором случае требуется unique-at-capture и полный live matching; после landing есть confirm. [Linux refusal tests](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/linux/src/tree/resolve/resolve_refusal_tests.rs) отдельно рассматривают replaced window, unreachable owner и timeout. Это прочитанные regression cases, **не локально исполненные тесты**. Нельзя заявлять, что stale-ref race исключён на всех платформах и UI toolkits.

[InteractionPolicy](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/core/src/actions/interaction_policy.rs#L11) по умолчанию запрещает focus stealing и cursor movement. Headless action при этом всё ещё может изменить приложение: отсутствие физического перемещения указателя не равно read-only. [src/command_policy/mod.rs:16](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/src/command_policy/mod.rs#L16) определяет OS permission needs и argument preflight; это не owner approval на каждое действие. Clipboard-команды имеют PermissionNeed::None: отсутствие отдельного OS permission prompt не означает отсутствие доступа к приватным данным.

[Windows permissions](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/windows/src/system/permissions.rs) отображает COM/UIA probe в Granted/Denied/Unknown. Успех создания UIA interface не доказывает доступность любого конкретного target/process/elevation. Реального probe здесь не было.

[src/mcp/mod.rs:17](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/src/mcp/mod.rs#L17) задаёт максимум восемь одновременных calls и 4 MiB transport message. Global flags фиксируются при запуске MCP. Проверка protocol frame size не является защитой данных и не ограничивает все CPU/RAM/desktop effects.

## Privacy и безопасный стенд

Snapshot tree, окно, clipboard, screenshots и debug traces могут содержать приватные данные; README предупреждает об этом. «Без screenshots» не означает «без чувствительного текста». Все tools доступны вызывающему агенту согласно его конфигурации: допустимость действия, исключение секретных окон, model egress, retention и redaction требуют внешней политики и проверки реализации. Никакие реальные окна, clipboard или screenshots пользователя не считывались; агент не запускался.

В этой среде `cargo --version` не найден. Rust toolchain не устанавливался. Tests/clippy/fmt/build `NOT_RUN / BLOCKED_ENV`. Linux AT-SPI/Wayland desktop не предоставлен; отдельная Windows GUI-сессия тоже не подготовлена. Отсутствие стенда не заменено проверкой текущего пользовательского desktop. Source-rule scripts и E2E программы не запускались.

## Портфель и следующий измеримый gate

Те же 45 профилей `project-registry` после BK-060 документальных ссылок (`0e80ec6`; исходные profile snapshot hashes в JSON). Все решения перечислены индивидуально; это не source audit 44 проектов.

| Исследование | Проект-кандидат | Причина по профилю | Ограничение / следующий тест | Evidence |
| --- | --- | --- | --- | --- |
| BK-065 | `Harness` | Отдельный integration workspace для adapter/MCP probes. | Текущий adapter seam не прочитан. Disposable fake application с явным window/process oracle, замена окна и дубли названий. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| BK-065 | `HermesAgent` | Gateway configuration может подключать GUI tool. | Это не код Hermes runtime; MCP support и policy enforcement не подтверждены. Сначала read-only synthetic snapshot, затем отдельно разрешённые действия в тестовом окне. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| BK-065 | `psqlqa` | Профиль desktop plan analyzer даёт конкретный UI acceptance сценарий. | Fork/reference, не выбранное внедрение; версия PyQt и accessibility неизвестны. Синтетический EXPLAIN без подключения к БД, независимый widget oracle. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |

`concept-loom-desktop` — условный UI test consumer, но не подтверждён accessibility coverage; `dsh-claude-primary-agent` и `dsh-runtime` — условные tool hosts, не GUI oracle; `hermes-akuz-agents` — конфигурация, не готовый desktop adapter. DBA, medical, routing и knowledge задачи не становятся GUI targets из-за наличия CLI/MCP. Код коллеги отсутствует, desktop target по brief не подтверждён. Старые предварительные backlinks сохранены без повышения; новые не добавлены.

План после предоставления стенда: scoped host packages по AGENTS (Windows adapter на Windows, Linux adapter на Linux), upstream unit/CLI/MCP tests и lint/build, затем авторская toy UI без секретов и сети. Baseline — ручной widget oracle или прямое чтение состояния fixture. Cases: own/wrong snapshot, process restart/PID reuse, duplicate names, changed window, unavailable accessibility, partial tree, blocked focus/cursor, ambiguous post-action outcome. Не повторять action при неизвестном delivery disposition. Три детерминированных повтора, negative mutation control; ошибки wrong-target/unauthorized action — 0, отличать refused от success. CPU/RSS/IO, p95 и reliability отдельно измерить, а не выводить из README.

Предложенный бюджет: одна эксклюзивная disposable GUI session, один worker, 60 s на case, без network/model credentials, только synthetic window. Ресурсы не измерены. Rollback — закрыть только fixture и удалить его отдельный state. До baseline `BLOCKED: MEASUREMENT_MISSING`. Production, реальные desktop applications и пользовательские permissions не менялись.
