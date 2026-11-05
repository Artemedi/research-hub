# BK-065 — Agent Desktop: original CLI на искусственном Wayland desktop

**Рассмотрен и отложен для внедрения.** Исторический статус **проверен экспериментально** относится к Linux toy UI и перечисленным original tests. Ни безопасность всего desktop агента, ни Windows/macOS, ни польза целевых проектов не доказаны. [Карточка](../studies/vercel-agent-desktop.md), [все 45 профилей](2026-11-05-bk065-followup-project-triage.json), [предыдущий gate](2026-11-05-bk065-agent-desktop-source-gate.md).

## Код и границы

Pinned [vercel-labs/agent-desktop@b43ac4f6e892ef608f8851428613c4009f0e84c7](https://github.com/vercel-labs/agent-desktop/tree/b43ac4f6e892ef608f8851428613c4009f0e84c7), workspace 1.2.0, Apache-2.0, 05.11.2026. Предыдущий разбор refs, strict identity, interaction policy, permission preflight и privacy дополнен чтением MCP child-call/output collection, Linux refusal tests и исследованием test/build paths. Весь platform stack построчно не аудирован.

Это инструмент accessibility automation без встроенной LLM. Observe→act→verify, owner authorization и model egress принадлежат внешнему агенту. [Qualified ref parser](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/core/src/refs/ref_token.rs#L19) и [strict resolver](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/crates/core/src/refs/resolve_saved_ref.rs#L29) дают проверяемую защиту от некоторых неверных ссылок, не общее доказательство отсутствия race/wrong-target action.

Headless actions меняют приложение. OS permissions не равны согласию владельца на конкретное действие. Snapshot text, clipboard и traces способны раскрывать приватные данные даже без screenshot. [MCP read_all](https://github.com/vercel-labs/agent-desktop/blob/b43ac4f6e892ef608f8851428613c4009f0e84c7/src/mcp/call.rs#L61) использует read_to_end: входной transport frame cap нельзя выдавать за общий output/RAM budget. OOM exploit здесь не проверялся. Нужны внешние tool allowlists, scope приложения, redaction/retention и запрет автоматического retry при неизвестном delivery.

## Реальный ограниченный запуск

[Результаты и hashes](2026-11-05-bk065-desktop-evidence.json), [авторский GTK fixture](../experiments/2026-11-05-bk065-gui-probe.py), [изолированный runner](../experiments/2026-11-05-bk065-isolated-gui.sh). Linux Bazzite, rustc/cargo 1.97.1, Python/GTK3, cage headless compositor, AT-SPI и private DBus. Public crates сначала получены отдельным `cargo fetch --locked --target x86_64-unknown-linux-gnu`; это **не полностью air-gapped acquisition**. Последующие compilation/tests — offline/locked, read-only source и cache, без пользовательского home/secrets/desktop/network. Toolchain и системные библиотеки читались, source не менялся.

| Проверка | Фактический результат |
| --- | --- |
| Core lib suite | **1683 PASS**, 0 fail, 0 ignored; 24.84 s |
| Linux lib без desktop | 2171 PASS, **3 fail**, 233 ignored; 54.37 s |
| Linux lib на private desktop / writable workdir | 2173 PASS, **1 fail**, 233 ignored; 54.14 s |
| Оставшийся source-scanner отдельно из source cwd | **1 PASS**, 2406 filtered out; 0.01 s |
| cargo fmt --all -- --check | PASS |
| clippy core --all-targets -- -D warnings | PASS; не весь platform workspace |
| Debug CLI offline locked build | PASS; не release/performance build |
| Toy UI: 4 cases × 3 fresh homes | **12/12 PASS** |

Первые отказы: отсутствие desktop, DBus identity и writable cwd. После synthetic passwd/group/machine-id, private compositor и writable /work два исчезли. Оставшийся test читает source-relative actions directory; /work его не содержит. Отдельный запуск из /source прошёл. **Единого fully-green Linux suite запуска нет**; 233 ignored не считаются passed. Это ограничения тестового окружения, а не доказательство исправления/отсутствия upstream bugs. Полные CLI/MCP integration suites, Windows/macOS и live ignored tests не запускались.

Compile budget: два jobs, 4 GiB virtual-address cap и 180 s timeout; не измеренный peak RSS. GUI: private namespace, no network/host display sockets, synthetic identity, temporary home/state, software renderer; 60 s/run и 12 s/subprocess. Только authored окно и кнопка. Original CLI snapshot→qualified ref→click увеличивает **независимый GTK clicked counter** до 1. Bare ref, unknown snapshot и ref уничтоженного widget дают INVALID_ARGS / SNAPSHOT_NOT_FOUND / STALE_REF, counter остаётся 1. Каждый run — fresh state. Это negative twins, не подмена upstream implementation. Никакие пользовательские окна или clipboard не читались; GitHub/Telegram/LLM agents не запускались.

Не проверены PID reuse, process restart, дубли окон, полные permission denials, malicious tree, delivery ambiguity, Windows/macOS и другие toolkits. Нет p95/reliability/CPU/RSS benchmark, сравнения с альтернативами или доказанной project benefit.

## Исследование → проекты

Все 45 профилей `project-registry@0e80ec6ecbf52173b899c0cc037a5ee076e2d1b1` в JSON; краткий список ниже не заменяет портфель. Внешний .NET brief — `AUTHOR_STATED / NEEDS_SOURCE_CODE`.

| Исследование | Кандидат | Основание / предел | Следующий тест | Evidence |
| --- | --- | --- | --- | --- |
| Desktop | Harness | [README@70fe47a95a7bd9ce47583033e1740f03d134ab1c:1](https://github.com/Artemedi/Harness/blob/70fe47a95a7bd9ce47583033e1740f03d134ab1c/README.md#L1): integration workspace; готовый desktop adapter seam не подтверждён. | Own evaluator + synthetic UI, baseline без MCP, фиксировать delivery. | `VERIFIED_WORKSPACE_DESCRIPTION / NEEDS_IMPLEMENTATION_EVIDENCE` |
| Desktop | HermesAgent | Gateway configuration profile; runtime implementation и desktop policy не прочитаны. | Сначала доказать MCP host/permission boundary, затем scoped toy UI. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| Desktop | psqlqa | Desktop analyzer fork/reference. [pyproject@b2e09ff24b06f3b7a92f7cf353cd3473c2a94aea:1](https://github.com/Artemedi/psqlqa/blob/b2e09ff24b06f3b7a92f7cf353cd3473c2a94aea/pyproject.toml#L1) подтверждает лишь tooling, **не accessibility seam**. | Собственный EXPLAIN fixture без БД, widget oracle, проверить реальный toolkit. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |

Ценность 6/10 как инструмент GUI acceptance, сложность 8/10 из-за permissions, toolkit coverage и wrong-target costs; оценки субъективные. Для всех трёх `BLOCKED: TARGET_MEASUREMENT_MISSING`. Новые backlinks не требуются: прежние preliminary links не повышаются до ready integration. Приоритет — target seam/baseline, затем negative delivery cases в disposable session. Никаких production integrations или разрешений на реальный desktop этот отчёт не даёт.
