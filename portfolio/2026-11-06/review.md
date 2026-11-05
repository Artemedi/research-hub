# Research intake — BK-041, BK-064 и CVE-2026-82533: ограниченные опыты и решение о времени

**Дата:** 2026-11-06. **Research Hub:** `main@222cab4395c96cc7a5704819602159dce9ff245a` до этой партии. **DSH:** фактически работающий `deepseek-harness@5b9d43878744d6a827a7104a30e0f08a04d81f66`, version `0.1.1-rc.2`. **Режим:** наблюдения/тесты, никаких изменений пользовательских репозиториев или производственных сервисов.

## Краткий результат

| Пункт | Первичный материал и версия | Выполненный test | Статус | Что НЕ доказано |
| --- | --- | --- | --- | --- |
| [BK-041 — Inspektor Gadget](../../reviews/inspektor-gadget/2026-11-06-privilege-gate.md) | [GitHub v0.57.0](https://github.com/inspektor-gadget/inspektor-gadget/releases/tag/v0.57.0), SHA-256 архива проверен | `ig version` PASS; попытка `sudo -n id` → ОС требует пароль; настройки команд восстановлены | `BLOCKED: OPERATING_SYSTEM_AUTHENTICATION` | BPF trace, event attribution, CPU/RAM/IO/overhead и eBPF-detach |
| [BK-064 — Creator Mode](../../reviews/dsh-creator-mode/2026-11-06-local-probe.md) | [7 официальных демонстрационных промптов](https://cdn.deepseek.com/harness/dsh-creator-mode-prompt-collection-en.html), зафиксирован HTML SHA-256 | UI unit **66/66 PASS**; браузерные e2e **4/7 PASS**, из них запуск creator-draft PASS; 3 FAIL = устаревшие roster snapshots | `UI_ENTRY_VERIFIED / E2E_PLUGIN_NOT_RUN` | Ни один плагин из промпта не был сгенерирован/валидирован |
| [CVE-2026-82533](../../reviews/cve-2026-82533/2026-11-06-readonly-risk.md) | [OX Research](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/) + [GHSA-8m2g-8cgm-3vcp](https://github.com/advisories/GHSA-8m2g-8cgm-3vcp) | Read-only локальный source audit, версия `0.1.1-rc.2`, 10/10 существующих header-unit tests PASS | `CURRENT_SOURCE_RISK_CONFIRMED / EXPLOIT_NOT_RUN` | Не проверен факт компрометации; исправление и regression test ещё не применены |

**Решение о приоритетах.** Время необходимо на **remediation CVE**, а не на повтор оригинального exploit. Пока реальная установка DSH уязвима, запуск Creator Mode с `cordis_mount` на живом сервере опасен: он выполняет JavaScript, предложенный моделью. Поэтому сначала patched/isolated disposable runtime, затем ограниченная генерация одного плагина из официального промпта (лучший кандидат — Poster Design Workbench, #4). Привилегированный eBPF-тест — только после отдельного завершения ОС-аутентификации; разрешение пользователя есть, пароль не передавать в чат.

## Доказательства и метод

- Для Creator Mode пройдены 66 компонентных тестов; браузерный кейс реально создаёт draft session в изолированном Playwright scaffold **без модельного API**. Три golden mismatch связаны с дополнительным предустановленным Claude preset; сгенерированный код плагина не оценивался.
- Для CVE исходная функция `isTrustedApiRequest` строит доверие из клиентских заголовков `Host/Origin/Sec-Fetch-Site`, не получает socket peer; все 10 имеющихся тестов проверяют только эти заголовки. Это объясняет невидимость дефекта в зелёном локальном наборе; это не эксплуатационный PoC.
- Для Inspektor Gadget владельцем разрешена root-проверка, но Linux потребовал пароль. Попытка обойти Linux credential gate не выполнялась. Официальная бинарная сборка в `/tmp` и контроль её хеша не затрагивают системные пакеты.
- Вложенные пользователем **полные по структуре транскрипты** [BK-025 и BK-034](../../reviews/telegram-transcripts/2026-11-06-user-provided.md) теперь доступны как отдельный источник `USER_FULL_TRANSCRIPT`, но не независимо сверены с YouTube. Поэтому прежнее условие «текста нет вообще» уточнено, а лабораторный статус не повышен.

## Research → project

| Исследование | Target IDs | Причина соответствия | Ограничения | Минимальный измеримый эксперимент | Evidence |
| --- | --- | --- | --- | --- | --- |
| BK-041 Inspektor Gadget | `AKUZ`, `sequential-rca` | Linux/PostgreSQL kernel-level event evidence | Нужен OS sudo auth; нет BPF-run | Nonprod trace_exec 30–60s + synthetic oracle, 5×, loss + CPU/RAM/IO | `BPF_NOT_RUN / BLOCKED_AUTH` |
| BK-064 Creator Mode | `dsh-runtime`, `agent-skills` | Plugin composition workflow, проверка правил и UI | RCE/privilege boundary в живом DSH не исправлена | Patched offline profile + официальный prompt #4, 3×, независимый GUI oracle, no secrets | `UI_ENTRY_PASS / PLUGIN_NOT_RUN` |
| CVE-2026-82533 | `dsh-runtime` | Актуальный vulnerable code seam подтверждён | No patched candidate, no exploit | Backport/vendor update + negative forged-Host/auth tests в disposable checkout, full CI, rollback | `HIGH_RISK / FIX_NEEDED` |

## Статусы и решение

**Ни BK-041, ни BK-064 нельзя переводить в `проверен экспериментально` как полную функцию.** В коллекции они остаются `ожидает проверки` с новой точной причиной и ссылкой на датированный отчёт. CVE проверена по текущему source snapshot; опасный live-exploit признан избыточным. Проектные исходники, production и приватный registry не менялись. Следующее разрешённое действие — подготовить минимальный исправленный candidate в отдельном worktree; применять к работающему DSH только после owner approval.

**Ресурсные ограничения:** в ходе тестов не проводилось измерение реальной стоимости inference, VRAM, CPU overhead гаджетов, p95 функционального создания плагина; эти показатели в отчёте помечены `NOT_MEASURED`, не `0`.
