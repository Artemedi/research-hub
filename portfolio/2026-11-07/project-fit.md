# Research-to-project — полный аудит документированных связей, 07.11.2026

Снимки: `research-hub@3180d9c46914f2f54d2a21e642b7ec3efffa2b99` и приватный `project-registry@838b86a28fcaa3440eeddbe147b6188e0d177963`.

**Правило:** ниже только прежние явно зарегистрированные candidates/assessments, **не** новый научный project fit. Отсутствие решения (`NOT_EVALUATED`) не означает `NO_FIT`, и наличие кандидата не означает выполненный A/B или разрешение на внедрение.

Контракт анализа — [исследовательская политика](../../RESEARCH_POLICY.md), полный обзор — [review](review.md), [глобальный оркестратор](../../docs/research-orchestrator.md). [Полная машинная матрица 3 735 записей](../../data/results/research-portfolio/2026-11-07-coverage.json) включает все 45 project ID для каждого источника и актуальный assessment_id при его наличии.

## Фактическое покрытие

| Показатель | Количество |
| --- | ---: |
| Канонических исследований | **83** |
| Проектов в приватной глобальной карте | **45** |
| Пар study×project | **3 735** |
| Текущих явных оценок | **376** |
| `NOT_EVALUATED` | **3 359** |
| Исследований без единой текущей project assessment | **3** |

Три нулевых кейса: `cera-moa`, `kvtether`, `random-attention`. Их нельзя автоматически записывать как неподходящие ни к одному из 45 проектов; требуется source-specific broad triage.

## Поимённый перечень всех источников

| Источник | Текущая проверка источника | Существующий shortlist: до 3 project ID, **не approval** | Ограничения / минимальный следующий gate |
| --- | --- | --- | --- |
| [`agent-error-dataset`](../../studies/agent-error-dataset.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `akuz-issue`, `sequential-rca`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`agent-mosaic`](../../studies/agent-mosaic.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `agent-config`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`agent-risk`](../../studies/agent-risk.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `agent-config`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`agent-transfer-protocol`](../../studies/agent-transfer-protocol.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`agentic-self-awareness`](../../studies/agentic-self-awareness.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `sequential-rca`, `agent-skills`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`alphaxiv-openresearch`](../../studies/alphaxiv-openresearch.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `BOUNDED_CODE_REVIEW` | `dsh-paper2agent` | Проверить pinned source+tests, source seam и negative controls |
| [`anthropic-agent-automations`](../../studies/anthropic-agent-automations.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED` | `HermesAgent`, `TelegramBot`, `wiki-tasks` | Проектный эффект не измерен; удержать без автоматического внедрения |
| [`behavior-beyond-text`](../../studies/behavior-beyond-text.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `agent-config`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`benchshield`](../../studies/benchshield.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-skills`, `dsh-runtime`, `dsh-paper2agent` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`bird-rl`](../../studies/bird-rl.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `akuz-schema-inventory`, `sequential-rca`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`cera-moa`](../../studies/cera-moa.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | **NO_DOCUMENTED_SHORTLIST** | Нужна source-first оценка 45 profiles; нет документированного решения |
| [`chartli`](../../studies/chartli.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `akuz-schema-inventory`, `akuzlogparser` | Проверить pinned source+tests, source seam и negative controls |
| [`claude-swarm`](../../studies/claude-swarm.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `dsh-claude-primary-agent`, `dsh-runtime`, `wiki-tasks` | Проверить pinned source+tests, source seam и negative controls |
| [`concordat`](../../studies/concordat.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `dsh-runtime`, `developer-safe-dotnet-core` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`covert-assistance`](../../studies/covert-assistance.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `agent-config`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`cursor-token-efficiency`](../../studies/cursor-token-efficiency.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED` | `HermesAgent`, `dsh-runtime` | Проектный эффект не измерен; удержать без автоматического внедрения |
| [`cve-2026-82533-technical-disclosure`](../../studies/cve-2026-82533-technical-disclosure.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `FULL_PRIMARY_TECHNICAL_DISCLOSURE_READ` | **NO_DOCUMENTED_SHORTLIST** | Проектный эффект не измерен; удержать без автоматического внедрения |
| [`daedalus`](../../studies/daedalus.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-skills`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`decision-geometry-harness`](../../studies/decision-geometry-harness.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `agent-config`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`drag`](../../studies/drag.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `Wiki_PG`, `sequential-rca`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`dsh-creator-mode`](../../studies/dsh-creator-mode.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `BOUNDED_CODE_REVIEW` | `agent-skills`, `dsh-runtime` | Уточнить полный исходник/тест; независимый target A/B ещё не выполнен |
| [`dsh-superagent-prototype`](../../studies/dsh-superagent-prototype.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `Wiki_PG`, `Harness`, `HermesAgent` | Проверить pinned source+tests, source seam и negative controls |
| [`exactly-once-limbo`](../../studies/exactly-once-limbo.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `TelegramBot` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`experienceindex`](../../studies/experienceindex.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `Wiki_PG`, `dsh-team-context`, `paper2agent-index` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`geoagent`](../../studies/geoagent.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `akuz-schema-inventory`, `dsh-paper2agent`, `developer-safe-dotnet-core` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`goal-aware-dynamic-collaboration`](../../studies/goal-aware-dynamic-collaboration.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-skills`, `dsh-runtime`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`gpt6-astra-skills-prompts`](../../studies/gpt6-astra-skills-prompts.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `FULL_TEXT_REVIEWED` | `agent-config`, `agent-skills`, `dsh-runtime` | Проектный эффект не измерен; удержать без автоматического внедрения |
| [`harness2`](../../studies/harness2.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-config` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`harnesssecurity-bench`](../../studies/harnesssecurity-bench.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`htn-orchestrate`](../../studies/htn-orchestrate.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `dsh-runtime`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`hyperresearch`](../../studies/hyperresearch.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `agent-skills`, `dsh-paper2agent` | Проверить pinned source+tests, source seam и negative controls |
| [`hyra-2`](../../studies/hyra-2.md) | `SHORT_LANDING_NOT_FULL_TEXT_CONFIRMED` / `FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED` | `Harness`, `HermesAgent`, `TencentDB-Agent-Memory` | Проверить полный легальный alternate/source или transcript; без него — BLOCKED |
| [`inspektor-gadget`](../../studies/inspektor-gadget.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `BOUNDED_CODE_REVIEW` | `AKUZ`, `Wiki_PG`, `sequential-rca` | Проверить pinned source+tests, source seam и negative controls |
| [`ipfire-fireperf`](../../studies/ipfire-fireperf.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `PARTIAL_SOURCE_REVIEW` | `AKUZ`, `sequential-rca` | Уточнить полный исходник/тест; независимый target A/B ещё не выполнен |
| [`jevagentharness`](../../studies/jevagentharness.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`julia-1`](../../studies/julia-1.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `PARTIAL_SOURCE_REVIEW` | `9router`, `dsh-runtime` | Уточнить полный исходник/тест; независимый target A/B ещё не выполнен |
| [`karpathy-autoresearch`](../../studies/karpathy-autoresearch.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `BOUNDED_CODE_REVIEW` | `Wiki_PG`, `agent-skills`, `dsh-runtime` | Проверить pinned source+tests, source seam и negative controls |
| [`kvset`](../../studies/kvset.md) | `FULL_PDF_TEXT_EXTRACTABLE` / `FULL_TEXT_REVIEWED` | `dsh-paper2agent` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`kvtether`](../../studies/kvtether.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | **NO_DOCUMENTED_SHORTLIST** | Нужна source-first оценка 45 profiles; нет документированного решения |
| [`lago`](../../studies/lago.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-skills`, `dsh-runtime`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`local-knowledge-graph`](../../studies/local-knowledge-graph.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `sequential-rca` | Проверить pinned source+tests, source seam и negative controls |
| [`maadbench`](../../studies/maadbench.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-skills`, `dsh-runtime`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`matoi`](../../studies/matoi.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `dsh-runtime`, `developer-safe-dotnet-core` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`mcp-toolbox-postgres`](../../studies/mcp-toolbox-postgres.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `Wiki_PG` | Проверить pinned source+tests, source seam и negative controls |
| [`memcomposer`](../../studies/memcomposer.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `dsh-runtime`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`memory-centric-continual-learning`](../../studies/memory-centric-continual-learning.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `Wiki_PG`, `agent-skills`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`memscope`](../../studies/memscope.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-skills`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`microsoft-skill-recorder`](../../studies/microsoft-skill-recorder.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `agent-config`, `agent-skills`, `dsh-team-context` | Проверить pinned source+tests, source seam и negative controls |
| [`novafabric`](../../studies/novafabric.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `PARTIAL_SOURCE_REVIEW` | `sequential-rca`, `dsh-runtime`, `hermes-akuz-agents` | Уточнить полный исходник/тест; независимый target A/B ещё не выполнен |
| [`open-steps`](../../studies/open-steps.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `agent-config`, `agent-skills`, `dsh-team-context` | Проверить pinned source+tests, source seam и negative controls |
| [`package-hallucination-rule-files`](../../studies/package-hallucination-rule-files.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-config`, `agent-skills`, `developer-safe-dotnet-core` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`paper2agent`](../../studies/paper2agent.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `FULL_TEXT_REVIEWED` | `dsh-paper2agent`, `paper2agent-index` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`pgbot`](../../studies/pgbot.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `Wiki_PG`, `sequential-rca`, `hermes-akuz-agents` | Проверить pinned source+tests, source seam и negative controls |
| [`poisoned-skills`](../../studies/poisoned-skills.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `agent-config`, `agent-skills` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`polar`](../../studies/polar.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`random-attention`](../../studies/random-attention.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | **NO_DOCUMENTED_SHORTLIST** | Нужна source-first оценка 45 profiles; нет документированного решения |
| [`rea`](../../studies/reverse-engineer-anything.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `psqlqa`, `MyPartyIsGrinding`, `WarOfGenesisIdleLoot` | Проверить pinned source+tests, source seam и negative controls |
| [`realm`](../../studies/realm.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `Wiki_PG`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`recap`](../../studies/recap.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `Wiki_PG`, `dsh-runtime`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`red-teaming-auto-mode`](../../studies/red-teaming-auto-mode.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `HermesAgent`, `agent-config`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`remory`](../../studies/remory.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | **NO_DOCUMENTED_SHORTLIST** | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`reva`](../../studies/reva.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `Wiki_PG`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`rrsi`](../../studies/rrsi.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-config` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`self-replicating-prompt-injections`](../../studies/self-replicating-prompt-injections.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `HISTORICAL_REVIEW_RECORDED` | `HermesAgent`, `agent-config`, `dsh-team-context` | Уточнить полный исходник/тест; независимый target A/B ещё не выполнен |
| [`sequential-diagnosis-language-models`](../../studies/sequential-diagnosis-language-models.md) | `SOURCE_UNREACHABLE_OR_TOO_LARGE` / `FULL_TEXT_REVIEWED` | `sequential-rca` | Проверить полный легальный alternate/source или transcript; без него — BLOCKED |
| [`silent-cue-loss`](../../studies/silent-cue-loss.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `Wiki_PG`, `dsh-paper2agent` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`simurg`](../../studies/simurg.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `9router`, `dsh-runtime` | Проверить pinned source+tests, source seam и negative controls |
| [`squidagent`](../../studies/squidagent.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `dsh-runtime`, `hermes-akuz-agents` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`statecomp`](../../studies/statecomp.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `dsh-runtime`, `dsh-team-context` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`swrouter`](../../studies/swrouter.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `9router`, `HermesAgent`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`tencent-teamai-cli`](../../studies/tencent-teamai-cli.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `BOUNDED_CODE_REVIEW` | `agent-skills`, `dsh-team-context`, `teamai-cli` | Проверить pinned source+tests, source seam и negative controls |
| [`toolgrad`](../../studies/toolgrad.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `BOUNDED_CODE_REVIEW` | `agent-skills`, `dsh-runtime`, `dsh-paper2agent` | Уточнить полный исходник/тест; независимый target A/B ещё не выполнен |
| [`transferable-tool-selection`](../../studies/transferable-tool-selection.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `akuz-schema-inventory`, `HermesAgent`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`trust-region-injection`](../../studies/trust-region-injection.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-config`, `agent-skills`, `dsh-runtime` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`understand-anything`](../../studies/understand-anything.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `akuz-schema-inventory`, `dsh-team-context`, `MyWiki` | Проверить pinned source+tests, source seam и negative controls |
| [`unreal-agent`](../../studies/unreal-agent-bk025.md) | `VIDEO_LANDING_ONLY_NO_TRANSCRIPT_VERIFIED` / `FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED` | `sequential-rca`, `HermesAgent`, `agent-config` | Проверить полный легальный alternate/source или transcript; без него — BLOCKED |
| [`unsloth-decision-model`](../../studies/unsloth-decision-model.md) | `PRIMARY_HTML_TEXT_AVAILABLE` / `PARTIAL_SOURCE_REVIEW` | `9router`, `dsh-runtime` | Уточнить полный исходник/тест; независимый target A/B ещё не выполнен |
| [`vercel-agent-desktop`](../../studies/vercel-agent-desktop.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `psqlqa`, `Harness`, `HermesAgent` | Проверить pinned source+tests, source seam и negative controls |
| [`veriharness`](../../studies/veriharness.md) | `FULL_HTML_MACHINE_ACCESSIBLE` / `FULL_TEXT_REVIEWED` | `agent-skills`, `dsh-paper2agent`, `developer-safe-dotnet-core` | Проверить методы/результаты/ограничения; target oracle/A-B отсутствует |
| [`warp-skill-doctor`](../../studies/warp-skill-doctor.md) | `SHORT_LANDING_NOT_FULL_TEXT_CONFIRMED` / `PARTIAL_SOURCE_REVIEW` | `agent-config`, `agent-skills`, `dsh-team-context` | Проверить полный легальный alternate/source или transcript; без него — BLOCKED |
| [`yahont-ce`](../../studies/yahont-ce.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `Wiki_PG`, `dsh-team-context`, `MyWiki` | Проверить pinned source+tests, source seam и negative controls |
| [`youtube-skills`](../../studies/youtube-skills.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `HermesAgent`, `agent-skills`, `TelegramBot` | Проверить pinned source+tests, source seam и negative controls |
| [`zero-code`](../../studies/zero-code.md) | `GITHUB_REPOSITORY_LANDING_AVAILABLE_NOT_FULL_CODE_REVIEW` / `PARTIAL_SOURCE_REVIEW` | `agent-config`, `dsh-runtime`, `wiki-tasks` | Проверить pinned source+tests, source seam и negative controls |

## Интерпретация

- `NO_DOCUMENTED_SHORTLIST` означает **нет сохранённого положительного shortlist**, а не отрицательное решение по всем 45 проектам.
- Если источник частичный, статус code/head/source URL текущего audit не отменяет качественный предыдущий pinned review.
- Для инженерных источников сначала читать актуальный source@SHA и tests; `GitHub HTTP 200` подтверждает доступ, но не выполнение и безопасность.
- Для клинического исследования `sequential-diagnosis-language-models` доступна [полная легальная авторская PDF](https://erichorvitz.com/sequential_diagnosis_LM.pdf), несмотря на HTTP403 по DOI.
- Внешний `developer-safe-dotnet-core` документирован только author brief; без исходного кода любые утверждения об API и внедрении остаются `NEEDS_SOURCE_CODE`.
- Публичная матрица не публикует содержимое частных PROJECT.md, токены или секреты. Исторические привязки не получают продвинутые статусы из этого скрининга.
- Обновлять приватный registry backlink только при настоящем новом полном обзоре с доказанным profile match, не после автоматического HTTP-прохода.

Итог: `EXPLICIT_ASSESSMENTS_PRESERVED / 83_SOURCES_SCREENED / 3359_PAIRS_NOT_EVALUATED / NO_NEW_PRODUCTION_APPROVAL`.
