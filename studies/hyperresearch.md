# Hyperresearch — исследовательский harness и vault

[Структурированная запись и связи](../catalog/studies/hyperresearch.md)

- **Источник:** [jordan-gibbs/hyperresearch @aece65f9307197119629beacf8aeaf8cc80e999a](https://github.com/jordan-gibbs/hyperresearch/tree/aece65f9307197119629beacf8aeaf8cc80e999a), Jordan Gibbs, MIT, версия 0.13.0; BK-028 / 27.09. Снимок 28.10.2026 новее Telegram-закладки.
- **Подход:** многоступенчатое исследование в Claude Code или Codex, local vault, сбор и сопоставление источников, извлечение пар утверждение–цитата, механическая triage и выборочная LLM-проверка. По README benchmark относится к Claude Code, Codex порт отдельно не оценён. Рейтинг DRACO `AUTHOR_REPORTED`, нами не воспроизведён.
- **Ограничение:** синтетический контрпример показал `supported-mechanical` для утверждения, противоречащего сохранённому claim после общей фразы. На проверенном пути такие auto-passed пары не направляются в `sampled_for_llm`; это не проверка готового отчёта или всех дополнительных lint-слоёв.
- **Проекты:** `agent-skills`, `dsh-paper2agent`, `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`. Только синтетический тест конкретной функции выполнен; полное исследование и LLM/сетевые вызовы `NOT_RUN`, `NO_PRODUCTION_APPROVAL`.
- [Обзор и воспроизводимый контрпример](../reviews/hyperresearch/2026-11-04.md).
