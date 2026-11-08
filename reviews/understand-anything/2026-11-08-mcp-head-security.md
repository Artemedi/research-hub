# Understand Anything — MCP HEAD и граница безопасности viewer

**Дата:** 08.11.2026. **Тип проверки:** BOUNDED_CODE_REVIEW текущего upstream, не полный аудит всего monorepo и не approval интеграции.

## Пин и область изменения

- Upstream: [Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything).
- Проверенный main HEAD: [a6ea4024767df85ce4f99140d4f12ecfc5a81eb6](https://github.com/Egonex-AI/Understand-Anything/tree/a6ea4024767df85ce4f99140d4f12ecfc5a81eb6), merge PR #726, feat: add Devin platform support and MCP server integration.
- Предыдущий pin исходной карточки: [4e6d3299017a7432da15957874992837a315c5b4](https://github.com/Egonex-AI/Understand-Anything/tree/4e6d3299017a7432da15957874992837a315c5b4). Текущий HEAD опережает его на 7 commits; GitHub compare показывает 28 изменённых файлов.
- Лицензия репозитория и нового MCP package — MIT. MCP package @understand-anything/mcp 2.9.7 требует Node >=22; viewer package — 2.9.8.
- Новый bounded scope: stdio MCP server, changed-files helper, SessionStart/PostToolUse hooks, viewer file-content endpoint и соответствующие тесты. Полный graph builder, все language parsers, UI и все зависимости не аудировались.

## Что добавлено в upstream

Новый [understand-anything-mcp.mjs](https://github.com/Egonex-AI/Understand-Anything/blob/a6ea4024767df85ce4f99140d4f12ecfc5a81eb6/understand-anything-plugin/packages/mcp/bin/understand-anything-mcp.mjs) регистрирует шесть инструментов: understand_status, understand_search, understand_explain, understand_diff, understand_onboard, understand_dashboard. Первые пять помечены readOnlyHint: true; dashboard явно помечен readOnlyHint: false, потому что запускает дочерний viewer и возвращает token-gated URL.

projectPath по умолчанию разрешается через DEVIN_PROJECT_DIR или cwd, но явный аргумент может указывать на любой доступный процессу каталог. resolveProjectRoot проверяет существование директории и канонизирует её через realpathSync, однако allowlist разрешённых project roots в MCP server не обнаружен. Следовательно, граница чтения задаётся вызывающим MCP-клиентом и правами локального процесса, а не отдельной политикой сервера. Это надо учитывать при подключении к агенту, который может выбирать аргументы инструмента.

Новый [changed-files.mjs](https://github.com/Egonex-AI/Understand-Anything/blob/a6ea4024767df85ce4f99140d4f12ecfc5a81eb6/understand-anything-plugin/packages/mcp/lib/changed-files.mjs) использует execFileSync с массивом аргументов, NUL-разделённый Git output и --relative; исключает .ua и .understand-anything, учитывает subproject cwd и untracked files. Для base отклоняются значения с начальным - и ..; shell interpolation не применяется.

SessionStart hook проверяет stale graph только при autoUpdate === true. PostToolUse hook реагирует на строки команд с git commit|merge|cherry-pick|rebase, если auto-update включён и graph существует, и добавляет инструкцию из auto-update-prompt.md. Сам hook не выполняет анализ; дальнейшее обновление выполняет агент по opt-in инструкции. В prompt присутствует команда «не спрашивать подтверждение», поэтому включать autoUpdate следует только при осознанном разрешении локального автоматического обновления knowledge graph.

## Проверки upstream

На чистом checkout a6ea402 выполнены только относящиеся к добавленному коду тесты:

| Набор | Результат |
| --- | ---: |
| tests/mcp/changed-files.test.mjs | 10/10 |
| tests/hooks/post-tool-use-auto-update.test.mjs | 16/16 |
| tests/hooks/session-start-stale-check.test.mjs | 6/6 |
| **Итого** | **32/32 PASS** |

Дополнительно: node --check четырёх новых/изменённых JS-файлов — PASS; ESLint тех же файлов — PASS; upstream checkout git diff --check — PASS. Установлены только root dev dependencies для этих unit tests, с --ignore-scripts.

Ограничение тестового покрытия: в tests/mcp/ обнаружен тест changed-files, но не integration tests самого MCP server и не security tests viewer endpoint. Полный monorepo build, core/dashboard build, полный upstream test suite, реальный MCP client и target project integration не запускались. Поэтому 32/32 — только узкая unit-test область, не общий upstream CI/quality verdict.

SQL parser finding из обзора 04.11 не устарел: в сравнении pin → HEAD файлы sql-parser.ts и parsers.test.ts не менялись; их Git blob SHA на текущем HEAD соответственно c962b8e8372a30fd12e737e7c08714eaf0a6f691 и d9dc3f1b2b4039ab395eb0221fe34e7f8ce2ed4d, совпадают с прежней проверкой. Четыре parser fixtures и девять wiki-parser tests не перезапускались.

## Synthetic security probe: symlink escape

Viewer заявляет token gate, bind на 127.0.0.1, ограничение выдачи файлами из graph и лимит 1 MiB. Это полезные меры, но path allowlist проверяется лексически.

В [viewer.mjs](https://github.com/Egonex-AI/Understand-Anything/blob/a6ea4024767df85ce4f99140d4f12ecfc5a81eb6/understand-anything-plugin/packages/viewer/bin/viewer.mjs#L96-L190) readSourceFile нормализует относительный путь и проверяет, что он присутствует в knowledge-graph.json. Затем fs.statSync(absoluteFile) и fs.readFileSync(absoluteFile) следуют по symlink. Проверки canonical target path относительно canonical project root нет.

В изолированной временной синтетике graph содержал filePath: "escape.txt", а escape.txt был symlink на файл за пределами project root. Запрос к token-gated /file-content.json вернул HTTP 200 и точный внешний sentinel SYNTHETIC_OUTSIDE_SENTINEL_9f41c2. Viewer действительно слушал только 127.0.0.1; запрос предъявил синтетический token. Реальные файлы, пользовательские секреты и рабочие проекты не читались.

**OBSERVED — SYMLINK_ESCAPE**

Это подтверждённый обход именно project-root confinement через symlink в graph-listed path, а не удалённое выполнение кода и не доказательство доступа к произвольному файлу без подходящего graph entry и token. Воспроизводимый [probe script](../../experiments/understand-anything/2026-11-08-viewer-symlink-probe.mjs) копирует только переданный upstream viewer в temp harness; staleness module и static index минимально заглушены, request handler остаётся оригинальным.

Артефакты: [machine evidence JSON](../../data/results/understand-anything/2026-11-08-mcp-head-security.json) · [45-profile project-fit](../../portfolio/2026-11-08/understand-anything-project-fit.md) · [project-fit JSON](../../data/project-fit/understand-anything/2026-11-08-project-fit.json).

Минимальная рекомендация upstream: canonicalize project root и target через realpath, проверять containment после разрешения symlink, а также добавить regression tests для внешнего symlink, внутреннего symlink, dangling link и path traversal. Одной проверки строкового префикса недостаточно; при необходимости исключать symlink через lstat/no-follow semantics и учитывать TOCTOU.

## Применимость к приватному портфелю

На snapshot Artemedi/project-registry@b3af154278a8724230185cba6b1898a106a4f25a прочитаны все 45 PROJECT.md; digest набора профилей: 4cb4be95806cc027a52b5608f1c379c26a438473163b323e4f7f572cc1092a4b. Публично не копировались ни тексты, ни пути, ни индивидуальные hashes карточек.

Единственный прямой профильный shortlist — Harness: профиль явно включает MCP compatibility и integration probes. Это PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE, не проверенный implementation seam. Исходники Harness, его MCP client registration и tests в этой итерации не исследовались; никакая интеграция не запускалась. Остальные профили не дали более прямого профильного target для этого MCP server. Подробная публичная матрица содержит только shortlist и не раскрывает остальные private project IDs.

Следующий минимальный target test: на текущем Harness HEAD поднять disposable stdio MCP client и fake .ua graph; проверить tools/list, understand_status/search/diff, ограничение project roots и отказ dashboard на внешнем symlink. Нужны фиксированный oracle, latency/RAM baseline и owner approval до любых изменений.

## Диспозиция

- BOUNDED_CODE_REVIEW: завершён для MCP server, helper, hooks и viewer security path на a6ea402.
- UPSTREAM_UNIT_TESTS: 32/32 PASS в перечисленном scope.
- SYNTHETIC_LAB: OBSERVED_SYMLINK_ESCAPE на viewer endpoint.
- AUTHOR_RESULTS: неприменимо — это engineering source, а не paper benchmark.
- MCP_SERVER_INTEGRATION: NOT_RUN; upstream integration tests отсутствуют.
- PROJECT_FIT: Harness / PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE.
- PRODUCTION_APPROVAL: NO. Исходники проектов, production, credentials и пользовательские knowledge graphs не менялись.

До upstream path-confinement fix и отдельного Harness integration test dashboard adoption следует считать заблокированным. Остальные read-only MCP tools не получили от этой проверки общего security approval.
