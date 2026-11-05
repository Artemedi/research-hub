# DSH Superagent Prototype — Telegram BK-060

- Тип: first-party engineering prototype, не научная репликация.
- Источник: [deepseek-ai/dsh-superagent-prototype](https://github.com/deepseek-ai/dsh-superagent-prototype), [pinned 8c32a9dc5d72c033816c6a8110b37f40cf94fba4](https://github.com/deepseek-ai/dsh-superagent-prototype/tree/8c32a9dc5d72c033816c6a8110b37f40cf94fba4), commit 31.10.2026, package 0.1.0, MIT.
- Проверка: 05.11.2026; [source review, ограничения и shortlist](../reports/2026-11-05-bk060-dsh-superagent-review.md), [45 project decisions](../reports/2026-11-05-bk060-project-triage.json).
- `PROTOTYPE_NOT_PRODUCTION / SOURCE_REVIEWED`; исторический статус **разобран**. Полный upstream suite/typecheck/build `BLOCKED_ENV`, реальный агент `NOT_RUN`.
- Независимо исполнено: [15/15 проверок оригинального in-memory core](../reports/2026-11-05-bk060-core-offline.json), [fixture](../experiments/2026-11-05-bk060-core-offline.mjs); mutant без resume revalidation обнаружен. Подставные Policy/Executor/Outbox: реальный settingsPolicy и security boundary не проверены.
- По коду: versioned admission, Mandate/Ticket/Assignment, stop/resume, durable effects. Обе роли получают full-access; рабочие директории и CLI wrappers не изолируют OS user. Совместимость с собственным runtime, prompt injection resistance, secret isolation и exactly-once внешних эффектов не подтверждены.
- Кандидаты: `dsh-runtime`, `wiki-tasks`, `dsh-claude-primary-agent` — `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. `dsh` — control-plane reference. Все ссылки, точные source locations, индивидуальный triage, риски и A/B gate в отчёте.
- Авторские внутренние результаты не перенесены на опубликованный прототип. Польза production не измерена, внедрение не одобрено.
