# BK-064 — Creator Mode: кодогенерация и изолированная проверка Poster Workbench

**Дата:** 2026-11-06. **Итог:** SOURCE_REVIEWED / EXTERNAL_CODEX_OFFLINE_PROBE_PASS / REAL_DSH_CREATOR_E2E_NOT_RUN. Исследование инженерной демонстрации, а не peer-reviewed benchmark.

## Первоисточник и безопасность

Источник: [7 официальных Creator Mode prompts](https://cdn.deepseek.com/harness/dsh-creator-mode-prompt-collection-en.html), полный исходник проверен в [предыдущем обзоре](2026-11-06-local-probe.md); HTML SHA-256 69265766b9b9c0c3dc3afb85153d26bc6565fe14ea86ab88627c9905d2395346. Сам автор предупреждает: один запрос не гарантирует точного повтора видео. Промпт №4 — **Poster Design Workbench**: доступ из разговора, title «Everything is a plugin», настройка title/text/shader colors, минимальный default UI, шейдер и английский шрифт сайта.

Локальный исходник DSH: deepseek-harness@5b9d43878744d6a827a7104a30e0f08a04d81f66, версия 0.1.1-rc.2; официальное исправление [CVE-2026-82533 начинается с 0.1.2-alpha.1](https://github.com/advisories/GHSA-8m2g-8cgm-3vcp). На этой машине **не запускалась модель внутри Creator Mode**, не выполнялись cordis_define/cordis_run на работающем сервере, не включался cordis_mount, не применялся security patch.

Проверенная документация DSH skill cordis-plugin-development, SHA-256 01811d3ee9c03a466abae12d54d229e7de7bd74ca6b730c54ce9d5e696b294aa: dynamic Client plugin — JS function body, поддерживает React.createElement и useState, документирован Scoped Run card Slot tool.view.cordis, key=self. Нормальная workflow требует сначала реального cordis_inspect_list/query; в данном тесте **Provider не опрашивался**, поэтому совместимость с фактическим активным browser Slot ещё не доказана.

## Host/Client native tests существующего DSH

| Проверка | Фактический результат | Доказательная область |
| --- | --- | --- |
| Host: tool-cordis lifecycle; cordis-host-runner composition, runner, sandbox-context, sandbox, versioning | **102/102 PASS**, 6 suites | Изоляция API на уровне unit test, события жизненного цикла, откат; не генерация плаката |
| Client: evaluator, guard, plugin, runner, orchestrator | **108/108 PASS**, 5 suites | Исполнение и остановка dynamic plugin, approvals/errors при замоканных зависимостях; не полноценный Creator session |
| Ранее проверенный Creator UI | 66/66 PASS; Chromium E2E 4/7 PASS, из которых реальный Creator draft PASS, 3 FAIL — outdated preset roster snapshot | Нельзя трактовать это как end-to-end plugin generation |

Выполнено через локальные Vitest suites с DSH_SNAPSHOT=replay без изменений DSH исходников. Временные логи на Bazzite: /tmp/bk064-cordis-host-tests.log и /tmp/bk064-cordis-client-tests.log. Ранее измеренные UI результаты см. предыдущий обзор.

## Один внешний генератор, не DSH Creator

Запущен **Codex CLI 0.164.0** в workspace-write sandbox, отдельный временный каталог /tmp/bk064-creator-isolated-20261106. Кодогенератор авторизован через ChatGPT; effective model не закреплён и не сравнивался. Первая попытка зависла в ожидании stdin, к генерации не приступила; после закрытия ввода **один успешный запрос** создал только два ожидаемых файла.

Репродуцируемые материалы:
- [INSTRUCTIONS.md — официальный prompt №4 и проверенный ограниченный contract](../../data/fixtures/dsh-creator/2026-11-06/INSTRUCTIONS.md).
- [code.client.js — фактический model-written Cordis Client plugin](../../data/fixtures/dsh-creator/2026-11-06/code.client.js), 2592 байта, SHA-256 ef8c7513520ce1996d0dbb41bd2630118c1645fbde6b3d2778c82237583050f2.
- [manifest.json — декларация ограничений](../../data/fixtures/dsh-creator/2026-11-06/manifest.json), SHA-256 e3d86f36bcf51c52c261f79d6c81b00e29c025e3a5bb8f9693ddef31fa260e18.

Codex report: input_tokens 116611, cached_input_tokens 102272, output_tokens 1300, reasoning_output_tokens 12; это **не счёт DSH Creator и не подтверждение стоимости**. Успешный модельный запрос занял около 44.91 s; одно наблюдение, p95 и variance неизвестны, реальная стоимость в USD неизвестна. Generated code доступен в Run card, но не как самостоятельная боковая панель. Фон — CSS radial/linear gradient, шрифт — system sans-serif: **это не точные assets сайта**, как прямо сказано в manifest. Нет persistence/export.

## Исполнение в disposable контейнере без доступа к DSH

Код агента **не исполнялся на host runtime**. [Открытый воспроизводимый контрактный проверяющий скрипт](../../experiments/2026-11-06-bk064-poster-probe.cjs) запустил код внутри docker.io/library/node:22 в rootless Podman, с --network=none --read-only --userns=keep-id --cap-drop=all --security-opt=no-new-privileges, pids=64, RAM=256 MiB, CPU=1 и read-only mount только временного каталога. Реальных DSH файлов настроек, секретов, runtime, service token и production-контента внутрь контейнера не передавалось.

**9/9 PASS** по synthetic React+Slots oracle: исходный title, редактирование title и text, два независимых цвета shader в preview, минимум заголовков, registration в документированном slot, disposer/cleanup, отсутствие Slots service, отказ на синтаксически испорченный JS. Полное [машинное evidence JSON](../../data/results/dsh-creator/2026-11-06-offline-poster-probe.json). Внутреннее выполнение checks: 4.086 ms; process maxRSS 47248 KiB, wall вместе со стартом контейнера ≈5.45s. Это не стоимость и не производительность реальной генерации или браузера. Контейнерная изоляция не была протестирована на escape и не является security certification.

**НЕ проверено:** реальный React browser rendering, cordis_inspect Provider, approvals, installation, Cordis Host + Client end-to-end, устойчивость 3 независимых генераций, отсутствие ошибок после повторного редактирования плагина в Creator, визуальное соответствие официальному сайту и фактическая модельная цена.

## Research → Project

| Проект | Соответствие | Следующее действие |
| --- | --- | --- |
| **dsh-runtime** | SOURCE_SEAM / CONDITIONAL_CANDIDATE: UI, cordis preset, Client/Host runner и plugin contracts в исходниках; модельная надёжность Creator не подтверждена | **Сначала P0 CVE-2026-82533 remediation** в отдельном clean worktree, negative regression и owner-approved staged deployment; затем настоящий Creator test в disposable patched environment, 3 промпта/seed и independent GUI+security oracle |
| **agent-skills** | DOCUMENTED_CANDIDATE: QA rubric и cordis-plugin-development contract пригодны для будущей проверки генерации плагинов | Не создавать новый глобальный skill; добавить проверку source provenance/permissions/cleanup лишь после измерения на нескольких независимых fixtures |
| **deepseek-harness** | UPSTREAM_REFERENCE_ONLY: tracking fork/reference source, а не runtime owner | Не менять tracking fork ради BK-064; сравнивать фиксированные upstream API и patched version |

Инженерный tradeoff: генерация UI через чат может ускорить прототипирование, но dynamic JS увеличивает поверхность привилегий и сложность approval, а ошибки provider API и реальная inference стоимость не устраняются синтетическими проверками. Нельзя переносить 9/9 PASS на реальный security, надёжность или экономику.

## Решение

**BK-064 считать «разобран»**, но **не «проверен экспериментально» по полной функции Creator Mode**. Есть полноценный первичный инженерный материал, отдельно сгенерированный плагин и 9/9 безопасных offline контрактных проверок, но настоящий workflow conversation→Creator model→Cordis define→approve→run→browser **NOT_RUN_SECURITY_GATE**. Внедрения/изменений пользователя нет. Новый отдельный проект/обвязка не нужны (YAGNI).