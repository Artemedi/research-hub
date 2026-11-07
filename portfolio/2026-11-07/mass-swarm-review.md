# Массовый разбор роя — 31 доказательный пробел

[Следующий этап: четыре предметных лабораторных проверки](next-evidence-round2.md) — отдельные проверяемые эксперименты.
Дата: 07.11.2026. Входные данные: [83 первоисточника](review.md),
[глобальная матрица 83×45](project-fit.md) и [архитектура оркестратора](../../docs/research-orchestrator.md).

Здесь 31 исследование проходило новый source-based screening: 19 pinned-code
excerpts, 10 извлечённых текстов научных/технических публикаций, 1 короткая
landing-page и 1 source repository без достоверного implementation excerpt.
**Полный обзор, независимое воспроизведение и новые привязки к проектам не утверждаются.**

[Независимая экспертиза GPT-6](senior-review.md) — итоговая приёмка доказательств и адресные REWORK.

## Подсчитанные результаты

- Пакетов с исходными доказательствами: **31/31**.
- Итоговые статусы модельных заданий: BLOCKED: 6, BLOCKED_SOURCE: 1, SCHEMA_PASS: 24.
- Модельных вызовов: 30.
- Учтённых моделью входных и выходных токенов: 65139.
- Списания по балансам: {'ZCode Start Plan/model:glm-5.3': 0, 'ZCODE WEEKEND BUILD/model:glm-5.3-flash': 0, 'ZCode Start Plan/model:glm-5.3-flash': -100974}.
- Научный ACCEPT по новому прохождению: **0**; project-fit APPROVED: **0**.

## Все исследовательские задачи

| Исследование | Материал | Статус микроагента | Доказательный вывод / следующий тест |
| --- | --- | --- | --- |
| [alphaxiv-openresearch](../../studies/alphaxiv-openresearch.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Конструкция reqwest-клиентов централизована в src/net.rs: loopback_client() задаёт no_proxy() для локальных серверов, remote_client() учитывает HTTP(S)_PROXY/NO_PROX / На revision 76e1118 открыть clippy.toml и найти disallowed-methods для net::loopback_client/remote_client — независимый oracle: конфиг линтера, а не коммен |
| [cera-moa](../../studies/cera-moa.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | In the shared-base setting CERA-MoA runs N=4 LoRA agents on one 4B base model, aggregate ~4.4B parameters. / Rebuild 4-agent LoRA MoA on a 4B model; sum base+adapter checkpoints to verify ~4.4B against the paper's figure as independent oracle. |
| [chartli](../../studies/chartli.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Юнит-тесты (vitest) проверяют, что renderSvg для normalizeData([[0],[5],[10]]) возвращает строку, содержащую '<?xml version', '<svg', '</svg>' и '<circle'. / В чистой копии ревизии запустить vitest и дополнительно прогнать выведенный SVG через xmllint --noout как независимый oracle валидности XML. |
| [claude-swarm](../../studies/claude-swarm.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Точка входа реализует MCP-сервер, оркестрирующий параллельные worker-сессии Claude Code через tmux с персистентным состоянием в файлах (notebook pattern). / Склонировать репозиторий на ревизии 31f1919, вычислить sha256 файла src/index.ts и сверить с 7e6cf91e…01124 из фрагмента. |
| [dsh-creator-mode](../../studies/dsh-creator-mode.md) | SOURCE_TEXT_EXTRACTED | BLOCKED | Требуется полный независимый review исходника и минимальный A/B по указанной теме |
| [dsh-superagent-prototype](../../studies/dsh-superagent-prototype.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Published dsh-superagent code is a reference-only research prototype, adapted for release and explicitly not identical to the implementation described in the paper. / Locate the paper's public text, list its architecture components, and compare against the inject list in SOURCE:src/index.ts; oracle: published paper, not  |
| [hyperresearch](../../studies/hyperresearch.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Тесты scholar-CLI сознательно провайдер-агностичны: реестр подменяется фейками, CLI зависит только от абстракций (SearchProvider, Paper, ProviderError), поэтому тест / Прогнать pytest в песочнице без сети и ключей; независимый оракул — зелёный прогон плюс grep на отсутствие прямых импортов провайдеров вне реестра. |
| [inspektor-gadget](../../studies/inspektor-gadget.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Репозиторий содержит тест package version_test, импортирующий regexp/testing — формат версии (semver) проверяется автотестом, а не только декларацией в version.go. / Независимо открыть pkg.go.dev/inspektor-gadget и сверить, что TestVersion валидирует semver-regex и CI зелёный. |
| [ipfire-fireperf](../../studies/ipfire-fireperf.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | fireperf — генератор нагрузки в духе iperf3, но заточен под stateful-устройства: открывает сотни тысяч соединений в секунду и отчитывается по каждому, тогда как iper / В изолированном стенде прогнать fireperf через nftables-шлюз и сверить его отчёт по соединениям со счётчиком conntrack (/proc/net/stat/nf_conntrack) как не |
| [julia-1](../../studies/julia-1.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | Анонс утверждает: Julia 1 — компактная decision-модель на базе mmBERT-small (144.3M параметров), работает на CPU и выбирает среди поданных с вопросом вариантов (клас / Сверить 144.3M и архитектуру с config.json/модель-картой jhu-clsp/mmBERT-small на Hugging Face как независимым oracle. |
| [karpathy-autoresearch](../../studies/karpathy-autoresearch.md) | PINNED_CODE_EXCERPTS_AVAILABLE | BLOCKED | Требуется полный независимый review исходника и минимальный A/B по указанной теме |
| [kvtether](../../studies/kvtether.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | The harness records primitive invocations synchronously and exports them asynchronously in the same order, keeping lifecycle export off the critical path while prese / Perturb async export ordering on a fixed trace; assert server-side reconstructed event order equals the synchronous harness log (independent oracle). |
| [local-knowledge-graph](../../studies/local-knowledge-graph.md) | PINNED_CODE_EXCERPTS_AVAILABLE | BLOCKED | Требуется полный независимый review исходника и минимальный A/B по указанной теме |
| [mcp-toolbox-postgres](../../studies/mcp-toolbox-postgres.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Пакет internal/log реализован на стандартном log/slog: импорт log/slog в log.go вместе с bytes и encoding/json в log_test.go согласуется со структурным JSON-логирова / Склонировать репо на revision 8d54da0 и запустить go test ./internal/log/ -v; oracle — код выхода go test, а не текст README |
| [microsoft-skill-recorder](../../studies/microsoft-skill-recorder.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Skill Recorder — публичный инструмент Microsoft: записывает реальную рабочую сессию (клики, переключения окон и приложений, страницы, команды/вывод) и превращает её  / Склонировать публичный репозиторий в чистый каталог, git checkout 505c97ae47be5642c0e1b44ebb8d1c1530c298fa и сверить SHA-256 README.md с a853ba63…b57f14 —  |
| [novafabric](../../studies/novafabric.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | Авторы сами фиксируют: накладные расходы захвата на CPU-хосте T1 неотличимы от нуля (CI [−10.5%, +16.9%] содержит ноль) из-за доминирования инференса — это утвержден / Замерить capture-overhead на GPU-хосте или с заглушенной моделью, N≥100 прогонов; независимый оракул — внешний счётчик времени/egress вне пайплайна. |
| [open-steps](../../studies/open-steps.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Оценка дневных измерений выполняется локальным скриптом evals/score.py без AI-суждений, а перезапись README возможна только по явному флагу --readme, не как побочный / Получить evals/score.py из публичного репозитория на ревизии 4fa744b независимо и сверить SHA-256 файла со значением sha из пакета. |
| [pgbot](../../studies/pgbot.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Промпт объяснения плана строится только вокруг уже отрендеренного pgbot плана: EXPLAIN в plan-only форме, запрос не выполняется, модели явно запрещено придумывать уз / Подать в BuildPlanPrompt план с единственным узлом Seq Scan и проверить ответ модели: не содержит ли Index Scan или чисел вне входа; oracle — множество узл |
| [random-attention](../../studies/random-attention.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | Выдержка явно фиксирует главный вывод авторов: сигнал селекции KV почти ничего не даёт при eviction в decode-фазе длинного CoT-рассуждения, но сформулирован только д / Независимый oracle: на одной модели и задаче при 4× сравнить uniform-random eviction с лучшим training-free базлайном, сверяя accuracy против воспроизведён |
| [rea](../../studies/reverse-engineer-anything.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Точка входа поднимает MCP-сервер через serveStdio, снапшотит окружение и фиксирует RECORDED_MCP_CATALOG_SHA256 — хеш каталога инструментов как якорь воспроизводимост / Независимо пересчитать SHA-256 файла src/main.ts в ревизии abfccc06 (sha256sum) и сверить с 5e54c306a528...; расхождение аннулирует якорь. |
| [self-replicating-prompt-injections](../../studies/self-replicating-prompt-injections.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | Authors report a novel prompt-injection variety that self-propagates like a worm, demonstrated only in simulated tool calls during training/eval; no impact outside t / Cross-check dates, model name and worm claim verbatim against the vendor's official disclosure page plus one independent advisory. |
| [simurg](../../studies/simurg.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | core.py декларирует process-stable hash для sketch/SimHash-оценителей, чтобы результаты бенчмарка воспроизводились между запусками. / Прогнать один фиксированный инпут через sketch/SimHash-оценитель в двух свежих процессах с разными PYTHONHASHSEED и сравнить вывод с внешним эталоном (sha2 |
| [tencent-teamai-cli](../../studies/tencent-teamai-cli.md) | PINNED_CODE_EXCERPTS_AVAILABLE | BLOCKED | Требуется полный независимый review исходника и минимальный A/B по указанной теме |
| [toolgrad](../../studies/toolgrad.md) | SOURCE_TEXT_EXTRACTED | BLOCKED | Требуется полный независимый review исходника и минимальный A/B по указанной теме |
| [understand-anything](../../studies/understand-anything.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Публичный API плагина реэкспортирует сборщики контекста для четырёх потоков: чат (buildChatContext, buildChatPrompt), дифф (buildDiffContext), объяснение (buildExpla / Импортировать собранный index.js в чистый Node-процесс и сравнить фактический список экспортов с этим набором; oracle — независимый import, а не вывод сбор |
| [unsloth-decision-model](../../studies/unsloth-decision-model.md) | SOURCE_TEXT_EXTRACTED | SCHEMA_PASS | Unsloth's docs describe fine-tuning small LLMs (Qwen3.5-0.8B) into decision models that score provided options and return a choice with probability, self-reporting B / If a checkpoint is published, run an independent harness on a held-out BANKING77 split and compare measured accuracy against the claimed 73%. |
| [vercel-agent-desktop](../../studies/vercel-agent-desktop.md) | PINNED_CODE_EXCERPTS_AVAILABLE | BLOCKED | Требуется полный независимый review исходника и минимальный A/B по указанной теме |
| [warp-skill-doctor](../../studies/warp-skill-doctor.md) | SOURCE_TOO_SHORT_OR_LANDING | BLOCKED_SOURCE | Требуется полный независимый review исходника и минимальный A/B по указанной теме |
| [yahont-ce](../../studies/yahont-ce.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Репозиторий содержит Python-бэкенд на FastAPI/uvicorn: backend/onyx/main.py импортирует FastAPI, CORSMiddleware, Sentry-интеграции и GoogleOAuth2. / В свежем клоне на ревизии 367b48d сверить с независимым оракулом: манифест зависимостей backend объявляет fastapi/uvicorn, и файл main.py действительно инс |
| [youtube-skills](../../studies/youtube-skills.md) | READABLE_REPO_WITHOUT_VERIFIED_IMPLEMENTATION_EXCERPT | SCHEMA_PASS | Проект реализует доступ к YouTube (транскрипты, поиск, каналы, плейлисты) через вызов внешнего API TranscriptAPI, отказываясь от yt-dlp и headless-браузеров из-за бл / В HEAD репозитория найти endpoint TranscriptAPI в коде (grep по базовому URL); независимый оракул — метаданные GitHub API/skills.sh для ZeroPointRepo/youtu |
| [zero-code](../../studies/zero-code.md) | PINNED_CODE_EXCERPTS_AVAILABLE | SCHEMA_PASS | Выдержка parseJsonc показывает посимвольный препарсер: удаляет // и /* */ вне строк в двойных кавычках, сохраняя байты строк; вход не исполняется — только накапливае / Прогнать parseJsonc на фиксированном корпусе кейсов (комментарии внутри строк, экранированные кавычки, переводы строк) и сравнить вывод с эталонным JSONC-п |

## Три источника без текущего project-assessment: отдельный профильный screening

Для каждого ниже недостаточно одной тематической ассоциации. Предварительный shortlist
**не становится доказанным FIT**, пока не прочитан конкретный source seam проекта и не измерено влияние.

- **cera-moa**: кандидат 9router или dsh-runtime лишь при доступе к hidden-state/обучению
  LoRA-специалистов. Простой прокси удалённых моделей не реализует данный метод.
- **kvtether**: кандидат dsh-runtime / Harness лишь если harness управляет собственным serving
  KV cache и событиями жизненного цикла. Для ZCode и Wello через обычный API интерфейса KV нет.
- **random-attention**: гипотеза для локального inference backend с поддержкой KV eviction.
  Авторские ограничения относятся к decode-phase reasoning; нельзя переносить их на API-сессии
  либо обычные SQL-операции без отдельного A/B.

[Результаты пяти критических ролей](cluster-critics.md) — проверка достаточности вторичных выводов.

## Правила принятия

1. HTTP 200, sha256 исходного материала, source path и LLM-ответ достаточны для
   **прозрачного скрининга**, но недостаточны для source-level / scientific verification.
2. Каждая роль получала исключительно публичные excerpts, без tools, токенов, SQL
   и приватных PROJECT.md. Неуспешные/неполные ответы остаются BLOCKED.
3. Внешняя экспертиза отдельно проверяет все фактические, численные и проектные claims
   на исходниках; без подтверждённого независимого oracle никакой production APPROVAL.

[Машинные данные и anchor hashes](../../data/results/research-portfolio/2026-11-07-mass-swarm.json)
[Независимый offline-аудит происхождения фрагментов](../../data/results/research-portfolio/2026-11-07-mass-anchor-audit.json)
разделяют источник, ранее установленный статус и текущий результат роя.

**Вердикт этапа: SOURCE_PACKS_COMPLETE; MODEL_SCREENING_PARTIAL; SCIENTIFIC_REPRODUCTION_PENDING.**
