# Telegram follow-up — 5 ноября 2026

Окно проверки: 05.11.2026, продолжение восстановленного backlog, не поиск новых публикаций. Каталог `Artemedi/project-registry@0e80ec6ecbf52173b899c0cc037a5ee076e2d1b1`, 45 карточек. Ранее опубликованные обзоры не перезаписывались.

| Источник | Новый факт | Отчёт и матрица | Предел |
| --- | --- | --- | --- |
| BK-062 REA | 48 original PE layout cases и обнаруженный mutant | [review](2026-11-05-bk062-rea-bounded-followup.md), [45 профилей](2026-11-05-bk062-followup-project-triage.json) | Не весь metadata/CIL pipeline или target benefit |
| BK-063 Hyra 2.0 | Полный официальный инженерный текст найден и прочитан | [review](2026-11-05-bk063-hyra2-primary-review.md), [45 профилей](2026-11-05-bk063-project-triage.json) | Нет orchestrator source/replay или scientific replication |
| BK-065 Agent Desktop | Original CLI: 12 private Wayland toy UI cases; core1683 PASS | [review](2026-11-05-bk065-agent-desktop-bounded-followup.md), [45 профилей](2026-11-05-bk065-followup-project-triage.json) | Linux suite failures/ignored retained, не Windows/macOS или target benefit |

## Повторно проверенные препятствия

**BK-025** [исходное видео](https://www.youtube.com/watch?v=eFBSlgXG3U0) и **BK-034** [исходное видео](https://www.youtube.com/watch?v=qLfSDQ5NGh0): анонимное metadata-only чтение через yt-dlp с `--ignore-config --skip-download --no-playlist --dump-single-json --no-warnings --socket-timeout 8 --retries 0` снова вернуло YouTube sign-in/bot gate. Медиа не скачивалось, cookies/аккаунт пользователя не использовались. Полной первичной transcript/video проверки нет. Найденные пересказы и отдельный [обзор Karpathy code](2026-11-04-bk034-autoresearch-review.md) не заменяют исходное видео. Статусы ожидания сохранены; `FULL_TEXT_VERIFIED` не присвоен.

**BK-041** Inspektor Gadget: read-only recheck на Linux показывает `CapEff=0000000000000000`, `kernel.unprivileged_bpf_disabled=2`. Это согласуется с прежним [EPERM permission gate](2026-11-04-bk041-inspektor-gadget-gate.md), но не новый успешный eBPF tracer experiment. Повышение прав, смена capabilities/sysctl и реальный trace не выполнялись. До отдельно разрешённой привилегированной среды остаётся blocked.

Эти результаты доступа не являются отрицательным результатом научного метода или доказательством дефекта инструментов. Ledger сохраняет source-specific основания; успешные ограниченные проверки других источников не закрывают эти gates.

## Следующие приоритеты

1. REA: полноценная authored managed assembly с независимыми metadata/CIL ожиданиями, затем отдельно разрешённый artifact.
2. Desktop: доказать конкретный project adapter seam и baseline, после этого тестировать restart/ambiguity/delivery в отдельной synthetic session.
3. Hyra: deterministic evidence-promotion/recovery replay; не запускать дорогостоящую research swarm по одному описанию.

Это предложенные планы, не выполненная интеграция. Исходники проектов, реальные приложения, GitHub/Telegram agents и production не запускались и не изменялись. [Исторический ledger и точные текущие количества](2026-11-04-telegram-bookmarks-reconciliation.md).

Проверка артефактов: JSON parsing/counts, 135 уникальных project decisions и их текущие card hashes, относительные Markdown links, pinned source line bounds; остальные 62 ledger entries побайтово по значениям не изменены. Node syntax check fixture, Python py_compile и bash -n прошли. `git diff --check` — без ошибок. Это integrity checks документов, не замена отсутствующих upstream/platform tests.
