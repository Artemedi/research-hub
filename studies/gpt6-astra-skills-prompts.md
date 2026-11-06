# GPT-6 Astra — Rethinking skills and prompts (BK-009)

[Структурированная запись и связи](../catalog/studies/gpt6-astra-skills-prompts.md)

**Официальный материал:** [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) (Eric Provencher, OpenAI Developers, **2026-09-11**); [полный Markdown](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra.md), SHA-256 `a1deee4c0b3ca16a20385c27f0692e22d5150fdec81710c04742dd5da29f0468`, проверен 2026-11-06. **Тип:** `OFFICIAL_ENGINEERING_GUIDANCE / NOT_PEER_REVIEWED`. Это рекомендации, не авторский количественный benchmark.

## Содержание и границы

Уточнять короткие trigger descriptions skills вместо broad triggers, применять progressive disclosure (короткий SKILL.md router, references читать по необходимости), в AGENTS.md давать контекстную карту документов, не требовать чтения всего перед простыми правками. Явно задавать безопасные workflow-разрешения и проверяемое условие завершения. Сохранение approval и запретов на реальные side effects необходимо независимо от длины prompt.

## 2026-11-06 — независимый парный A/B на реальной Astra

[Полный отчёт](../reviews/gpt6-astra-skills-prompts/2026-11-06-live-astra-ab.md) · [сценарий](../experiments/2026-11-06-bk009-astra/run-ab.py) · [счётчики и независимые oracles](../data/results/gpt6-astra-skills-prompts/2026-11-06-scored-ab.json).

Codex CLI 0.164.0 с `-m gpt-6-astra`, `medium`; 5 пар одинаковых тривиальных Python/SQL/YAML/Markdown задач на scratch Git copies. **A** — явно избыточные обязательные документы/тесты и длинные skills; **B** — контекстные источники, маленькие roots и точные triggers. Обе группы решили **5/5** задач; обе имели **1/5 нарушений строгой чистоты** из-за одинаковых `__pycache__/*.pyc`. B использовала **309 100** входных токенов против **580 188** у A (−46,72%); wall **131.905** против **151.611 s** (−13,0%), быстрее в 4/5 пар. Нельзя переносить разницу на реальные проекты, считать эффект именно skill descriptions или доказанной экономией тарифа: пять пар, без независимых повторов, baseline искусственно плохой, cache и серверная нагрузка не контролировались.

**Статус:** `BOUNDED_LIVE_MODEL_SYNTHETIC_VERIFIED / NOT_PRODUCTION_VALIDATED`. Применимость: `agent-skills`, `agent-config`, `dsh-team-context` и `dsh-runtime` — проектные гипотезы без кодовой интеграции. Не переписывать глобальные AGENTS.md и не убирать требования безопасности без самостоятельных проекта-специфичных evals и подтверждённого diff. Для dsh-runtime отдельно сохраняется P0 CVE-2026-82533.

**Дополнительные воспроизводимые материалы:** [генератор фикстур](../experiments/2026-11-06-bk009-astra/prepare.py), [независимый scorer](../experiments/2026-11-06-bk009-astra/score-ab.py), [manifest задач и вариантов](../data/results/gpt6-astra-skills-prompts/2026-11-06-fixture-manifest.json).
