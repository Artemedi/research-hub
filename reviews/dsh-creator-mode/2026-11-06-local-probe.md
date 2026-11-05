# BK-064 — Creator Mode: ограниченный воспроизводимый эксперимент

**Дата:** 2026-11-06. **Первичный инженерный материал:** [официальные семь Creator Mode demo prompts](https://cdn.deepseek.com/harness/dsh-creator-mode-prompt-collection-en.html), HTML SHA-256 проверенного снимка `69265766b9b9c0c3dc3afb85153d26bc6565fe14ea86ab88627c9905d2395346`. Коллекция описывает семь демонстраций (3D здания, Transformer, UI-тема, плакат, видеомонтаж, PDF reader, conversation stats). Автор прямо предупреждает, что исходный промпт не всегда воспроизводит показанное без последующих уточнений. **Это исходник с примерами, не эксперимент с контрольной группой и не peer-reviewed research.**

**Target:** локальная реализация DeepSeek Harness из `/home/Trintos/projects/deepseek-harness@5b9d43878744d6a827a7104a30e0f08a04d81f66`, DSH `0.1.1-rc.2`. Тесты запускаются в isolated scaffold / synthetic fixtures; реальные API-ключи/модельные вызовы и рабочие профили не использовались.

## Выполненные прогоны

| Проверка | Фактический результат | Что доказывает |
| --- | --- | --- |
| `vitest.config.ts`, UI-agent-preset `section.client.spec.tsx` + `components.client.spec.tsx` | **66/66 PASS**, 2 файла; лог `/tmp/research-coverage-Bxz4QC/bk064-unit.log` | Кнопка запуска и контроллер выбора Creator preset корректно работают на synthetic UI |
| `vitest.web.config.ts`, `apps/web/tests/agent-preset-authoring.e2e.ts`, Chromium/Playwright | **4/7 PASS**; сценарий `starts a creator-mode session from the section` PASS (875 мс) | Создание черновой сессии с `agentPreset=cordis` и навигация работают в изолированном web scaffold |
| Три остальных e2e | **3 FAIL**, точная причина — *snapshot mismatch* от нового предустановленного Claude-профиля (`Claude (максимальная отдача)`) в списке roster, не сбой исполняемой Creator Mode-сессии | Отчёт фиксирует регрессию test-golden; исправление snapshot не является задачей этого исследования |
| Генерация плагина из одного из семи промптов, функциональное GUI-тестирование, реальный модельный счёт | **NOT_RUN** | Официальная функциональность end-to-end ещё **не** подтверждена |

## Почему полноценный генеративный прогон остановлен

Согласно локальному `apps/cli/config/agent-presets/cordis/agent.cordis.yml`, Creator/cordis preset допускает выполнение **model-written JavaScript** через `cordis_mount` в живом runtime — по документации это эквивалент shell-access. В это же время запущен локальный DSH `0.1.1-rc.2`, попадающий под CVE-2026-82533. Запуск генерируемого плагина против этого веб-сервера одновременно подверг бы машину риску sandbox bypass и создал бы неопределённые модельные/операционные расходы. Поэтому никакого plugin output не было и **нельзя** повышать статус BK-064 до `EXPERIMENTALLY_VERIFIED`.

## Контролируемая следующая постановка

**Выбран официальный промпт №4 — Poster design workbench**: изолированный исправленный DSH, временный профиль без host secrets и shell-on-host, запрет произвольного Cordis mount, фиксированный лимит inference и не-production workspace. Acceptance oracle: (1) доступ из диалога, (2) заголовок по умолчанию `Everything is a plugin`, (3) изменение title/text, (4) изменение цветов shader, (5) default UI без лишних разделов, (6) генерируемый проект не имеет прав на чужие файлы/host API. Baseline: ручная композиция с теми же requirements. Сравнение 3 запуска, pass rate, число исправлений, model tokens/new-vs-cached, p95 latency, CPU/RAM/IO, отсутствие permission escalation, rollback. Промпт не является доказательством качества до выполнения этих проверок.

| Источник | Target IDs | Соответствие | Ограничения | Эксперимент | Evidence |
| --- | --- | --- | --- | --- | --- |
| DSH Creator demo prompts | `dsh-runtime`, `agent-skills` | Авторизация расширений и способность создавать проверяемые UI tools для агентного harness | Исполнение JS опасно на непатченной версии; неизвестна генерационная надёжность | Исправленный isolated web profile, frozen prompt №4, 3 запуска с independent GUI/permission oracle | `UI_ENTRY_VERIFIED / E2E_PLUGIN_NOT_RUN / BLOCKED_SECURITY_GATE` |

Рабочие профили, исходники и production не менялись. Осторожно: unit/e2e прогоны не проверяют творческое качество плагина.
