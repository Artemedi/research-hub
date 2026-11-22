# gnhf — автономные ограниченные Git-итерации coding-агентов

[Структурированная запись и связи](../catalog/studies/gnhf.md)

**Тип:** инженерный open-source оркестратор (MIT), не рецензированное научное исследование. Название — *good night, have fun*. Источник: [kunchenguid/gnhf@98d6a5f3d588ee6e241558f06dfc0d495e6354d6](https://github.com/kunchenguid/gnhf/tree/98d6a5f3d588ee6e241558f06dfc0d495e6354d6), [README](https://github.com/kunchenguid/gnhf/blob/98d6a5f3d588ee6e241558f06dfc0d495e6354d6/README.md), [LICENSE](https://github.com/kunchenguid/gnhf/blob/98d6a5f3d588ee6e241558f06dfc0d495e6354d6/LICENSE). Проверено 22.11.2026; `package.json`: версия `0.1.53`, Node >=20, TypeScript.

**Обобщённая исследуемая методология:** `frozen objective → smallest bounded step → isolated Git worktree → agent execution → independent validation → commit/evidence → stop/rollback → morning review`. Интерес представляют долговечный цикл и его контроль, а не обязательное внедрение gnhf как зависимости.

**VERIFIED (static source review):** одна CLI-итерация вызывает внешний агент, записывает результат/learned notes, коммитит изменение по сообщению агента, поддерживает worktree, ограничители числа итераций, токенов и времени, обработку rate limits, ошибки и остановку. `--push` необязателен. CI проверяет код самого gnhf; нет доказательства качества всех коммитов, произведённых внешними агентами.

**Высокорисковые свойства:** [Claude-адаптер](https://github.com/kunchenguid/gnhf/blob/98d6a5f3d588ee6e241558f06dfc0d495e6354d6/src/core/agents/claude.ts#L171-L190) при отсутствии явного режима добавляет `--dangerously-skip-permissions`; [Codex-адаптер](https://github.com/kunchenguid/gnhf/blob/98d6a5f3d588ee6e241558f06dfc0d495e6354d6/src/core/agents/codex.ts#L95-L118) — `--dangerously-bypass-approvals-and-sandbox`; ACP использует `permissionMode: "approve-all"`. [Git rollback](https://github.com/kunchenguid/gnhf/blob/98d6a5f3d588ee6e241558f06dfc0d495e6354d6/src/core/git.ts#L293-L295) включает `git clean -fd`, удаляющий неотслеживаемые файлы. [Успех итерации](https://github.com/kunchenguid/gnhf/blob/98d6a5f3d588ee6e241558f06dfc0d495e6354d6/src/core/orchestrator.ts#L690-L704) зависит от `result.output.success`, независимый обязательный test gate перед коммитом отсутствует. По умолчанию лимиты итераций, времени и токенов не заданы.

**Прочие ограничения:** журналы/промпт лежат локально, не в общедоступном журнале коммитов; telemetry упомянута автором, можно отключить `GNHF_TELEMETRY=0` (в реализации включение зависит от website ID в сборке/окружении). External agents могут читать/передавать рабочие файлы; Git worktree **не** является security sandbox. Проверки реальных overnight runs и расхода токенов не проводились.

**Решение:** `BOUNDED_CODE_REVIEW / RESEARCH_CANDIDATE / NEEDS_EVIDENCE / NOT_PRODUCTION_APPROVED`. Сначала изолированный dry-run с stub agents, контрпримером ошибочного `success=true`, проверкой rollback и независимым offline oracle; реальную автономную работу на DSH/AKUZ не запускать.

[Датированный исходный аудит](../reviews/gnhf/2026-11-22.md) · [портфельная матрица](../portfolio/2026-11-22/gnhf.md).
