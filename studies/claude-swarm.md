# Claude Swarm — оркестрация параллельных Claude workers

- **Источник:** [cj-vana/claude-swarm](https://github.com/cj-vana/claude-swarm), инженерный MCP-сервер и набор инструкций; [MIT](https://github.com/cj-vana/claude-swarm/blob/31f19199bf3557cda4860231186a06b72c8edb94/LICENSE).
- **Версия:** [31f19199bf3557cda4860231186a06b72c8edb94](https://github.com/cj-vana/claude-swarm/tree/31f19199bf3557cda4860231186a06b72c8edb94), 2026-02-11, package 0.1.0; дата проверки 2026-11-04. Исходная Telegram-закладка BK-016 — 17.09.2026.
- **Назначение:** долгоживущие задачи, tmux workers, Git worktree, state/checkpoint, тесты, протоколы ограничений и повторные запуски.
- **Проверено по исходнику:** стандартный worker использует `bypassPermissions`; при ошибке создания worktree допускается общий каталог. В штатной точке инициализации worker manager и protocol registry создаются отдельно, а подключение enforcement к manager в исходном дереве не вызывается. Само сообщение о включении протокола не доказывает исполнения ограничений.
- **Не проверено:** запуск MCP, workers, протоколов и зависимостей; динамический тест остановки, конкурентности и восстановления; стоимость LLM. `SOURCE_REVIEWED / PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE / LAB_NOT_RUN / NO_PRODUCTION_APPROVAL`.
- **Кандидаты:** `dsh-runtime`, `dsh-claude-primary-agent`, `wiki-tasks` — см. [обзор и матрицу](../reports/2026-11-04-bk016-claude-swarm-review.md). Не устанавливать и не активировать автоматически.
