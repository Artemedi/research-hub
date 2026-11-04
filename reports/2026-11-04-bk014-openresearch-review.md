# BK-014 — alphaXiv OpenResearch: полнотекстовый gate, Git provenance и экспериментальный runtime

**Дата:** 2026-11-04. **Исходный Telegram-пункт:** BK-014 / 16.09.2026, priority A.
**Класс первоисточника:** полностью доступное инженерное ПО и техническая документация (НЕ рецензируемая научная статья).
**Пользовательский исход:** `Добавлен в карточки` после проверки единственного обратного линка на `dsh-paper2agent`.
**Доказательность:** `SOURCE_REVIEWED / PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE / LAB_NOT_RUN / NO_PRODUCTION_APPROVAL`.

## 1. Первичные источники и ревизии

- [alphaXiv/OpenResearch](https://github.com/alphaXiv/OpenResearch), pin **[23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d](https://github.com/alphaXiv/OpenResearch/tree/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d)**, commit 2026-11-03 18:19:29 −08:00 (2026-11-04 UTC), release/package `v0.2.24`, [MIT](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/LICENSE).
- Прочитаны не только README: [AGENTS.md](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/AGENTS.md), [экспериментальная архитектура](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/arc/experiments.md), [хранение/egress](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/arc/storage.md), [полная публичная документация](https://openresearch.sh/docs/experiments), Rust-исходники, существующие тесты. Архивировано состояние HEAD, не заявлено, что это последняя возможная версия на дату прочтения следующего отчёта.
- Для сопоставления прочитаны [dsh-paper2agent@6d82a42175a71d3327b773df88f1da0707efe43c](https://github.com/Artemedi/dsh-paper2agent/tree/6d82a42175a71d3327b773df88f1da0707efe43c) и [paper2agent-index@125c1a82adbe18e58b27208556b64524b099d7ac](https://github.com/Artemedi/paper2agent-index/tree/125c1a82adbe18e58b27208556b64524b099d7ac); просмотрены все 45 `project-registry/projects/*/*/PROJECT.md` из `project-registry@7d279c8f12ed2577198c7be2d31ffc033a64b1c7`.
- Нет признаков дубликата этой работы в `studies/` на момент обзора. **OpenResearch** (локальный Rust harness) не является научной работой **OpenResearcher** из отдельной публикации; совпадение имен не означает один метод.

## 2. Что технически реализовано в коде (VERIFIED_STATIC)

| Факт и исходные строки | Что подтверждено | Чего это НЕ доказывает |
| --- | --- | --- |
| [`src/compute.rs:24–75`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/compute.rs#L24-L75) и [`:126–147`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/compute.rs#L126-L147) | `SourceSnapshot` применяет `git archive` к точной ревизии ветки, хеширует tar SHA-256, хранит content-addressed payload; неподтверждённые изменения рабочего дерева в снимок не попадают | Нет полной репликации среды: Git SHA и tar не фиксируют все зависимости/драйверы/сеть/model randomness |
| [`src/compute.rs:77–115`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/compute.rs#L77-L115) | При последующей загрузке сверяется digest и размер архива | Не тестировалась устойчивость всей многопроцессной цепи на Bazzite |
| [`src/local/experiments.rs:14–49`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/local/experiments.rs#L14-L49), [`arc/experiments.md`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/arc/experiments.md) | Отдельные `orx/<slug>` ветви, baseline/children, run-to-commit lineage, отделение дерева экспериментов от исходного worktree | Не доказана корректность исследовательской гипотезы или независимость оценщика |
| [`src/store.rs:679–755`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/store.rs#L679-L755), [`arc/storage.md`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/arc/storage.md) | Локальный SQLite WAL для состояния, отдельные файлы логов, каталог артефактов, lifecycle file locks | Не заменяет версионированный архив конечных `research-hub` карточек и критерии качества |
| [`src/local/localrun.rs:50–127`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/local/localrun.rs#L50-L127) | Локальный run запускает пользовательскую shell-команду и передаёт доступное окружение/настройки | **Это не эквивалент Podman `--network=none` / `--cap-drop=ALL`**: не использовать непроверенный scientific code или секреты на хосте |

## 3. Критический FULL_TEXT gate для нашего исследовательского процесса

[`src/commands/paper.rs:1–17`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/commands/paper.rs#L1-L17) прямо декларирует:

- `alphaXiv`: отчёт/обзор по умолчанию, `--full` запрашивает извлечённый текст; полнота извлечения, формулы, таблицы, приложения и соответствие PDF **не проверены**.
- **OpenAlex / bioRxiv / PubMed:** метаданные + **abstract** + ссылка на PDF/полную статью, но `--full` не добывает полный текст. [`src/commands/paper.rs:89–126`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/commands/paper.rs#L89-L126) подтверждает распределение source handlers.
- `orx discover` — поиск по внешним источникам, **не** доказательство полнотекстового анализа: [`src/commands/discover.rs:11–50`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/commands/discover.rs#L11-L50).

**Нельзя применять OpenResearch как замену обязательному полному review.** Наш `research-hub/RESEARCH_POLICY.md` и `dsh-paper2agent/AGENTS.md` требуют полный HTML/PDF/легальную авторскую версию, методы, результаты, ограничения и корректную coverage метку. Без нее: `FULL_TEXT_UNAVAILABLE`, не scientific verdict. Для научных методик в `dsh-paper2agent` обязательны также независимый verifier и исходная спецификация. Полученный из alphaXiv Markdown — только дополнительный источник и повод проверить полноценность, не автоматическое `FULL_TEXT_VERIFIED`.

## 4. Security/privacy и накладные расходы

- `orx up` использует loopback web UI и не имеет обычной application-level авторизации; [README](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/README.md) предупреждает, что на общем удалённом хосте сервис могут открыть другие локальные пользователи. Host/Origin проверки веб-сервера **не равны полноценной межпользовательской ACL**. Не запускать без изолированной VM/SSH доступа только своему пользователю.
- [`arc/storage.md:140–180`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/arc/storage.md#L140-L180): состояние работы локально по архитектурному контракту; **поисковые строки и аргументы обращения к alphaXiv идут во внешние API**, а tool responses идут в модельный контекст и далее выбранному провайдеру. Выбранные remote compute поставщики получают исходный архив, который им предназначен. «Local-first» ≠ «нет никакого исходящего трафика».
- Официальные релизные сборки имеют **opt-out telemetry** (а также функции агентного feedback согласно README). Для экспериментального запуска обязательно явно выключить и независимо проверить сетевой egress. Исходники/локальная сборка не означают автоматическое безопасное выполнение сторонних agent tools.
- CPU/RAM/disk IO: отдельные Git worktrees, tar/zip source snapshots, многократные git refs, SQLite WAL, логи и артефакты **увеличивают** потребление CPU, диска и IOPS. Стоимость remote GPU и latency не оценены. Никакого заявления о приросте производительности без A/B.

## 5. Research-to-Project: 45 карточек, shortlist из одного

| Исследование | Конкретный проект | Обоснование из PROJECT.md + source:line | Ограничение | Следующий минимальный тест | Evidence status |
| --- | --- | --- | --- | --- | --- |
| BK-014 OpenResearch | **`dsh-paper2agent`** | Отдельный Python research-to-project инструмент уже содержит [`src/paper2project/execution.py:251–275`](https://github.com/Artemedi/dsh-paper2agent/blob/6d82a42175a71d3327b773df88f1da0707efe43c/src/paper2project/execution.py#L251-L275) pinned source/input tree hash; [`:308–318`](https://github.com/Artemedi/dsh-paper2agent/blob/6d82a42175a71d3327b773df88f1da0707efe43c/src/paper2project/execution.py#L308-L318) isolated Podman run; [`docs/product/PIPELINE.md`](https://github.com/Artemedi/dsh-paper2agent/blob/6d82a42175a71d3327b773df88f1da0707efe43c/docs/product/PIPELINE.md) описывает Stage 4–6, но не полноценный внедрённый E2E. У OpenResearch есть полезные **механизмы Git snapshot/run lineage** для сравнения подходов | Замена executor по умолчанию **ослабит** изоляцию; независимый oracle и full-text gate не предоставляет; дублирует существующий функционал | Disposable fixture A/B provenance, corruption, crash/restart, egress guard; неprod, только после owner gate | `PROJECT_PROFILE_MATCH / VERIFIED_SOURCE_SEAM / NEEDS_EVIDENCE / LAB_NOT_RUN` |

**Остальные 44 карточки:** triage выполнен по назначению и исследовательским профилям. Ни одна не получила достаточно специфический выигрыш/контракт, чтобы добавлять обратную ссылку. 8 DBA/AKUZ (включая `sequential-rca`) — SQL/RCA требует предметного oracle, не универсального эксперимента; 16 агентных/infrastructure — собственные runtime и skills, где установление OpenResearch как второго оркестратора создаёт дублирование; 4 автоматизации — scheduler/retry вопросы; 6 игр/личных проектов — другой продуктовый слой; 8 внешних референсов — не implementation targets; один другой независимый `paper2agent-index` — только **derived read-only shortlist cache** Stage 3 ([SCHEMA.md](https://github.com/Artemedi/paper2agent-index/blob/125c1a82adbe18e58b27208556b64524b099d7ac/SCHEMA.md)), не runner; 1 проект коллеги без исходников — `AUTHOR_STATED / NEEDS_SOURCE_CODE`. `research-hub` — архив результата, но не 46-я карточка портфеля: в нём уже имеются `studies/reports`, не надо создавать новый project ID.

**Важное различие:** `dsh-paper2agent` [`execution.py:308–318`](https://github.com/Artemedi/dsh-paper2agent/blob/6d82a42175a71d3327b773df88f1da0707efe43c/src/paper2project/execution.py#L308-L318) уже запускает научный код в контейнере `--network=none --read-only --cap-drop=ALL` с read-only mounts; [`:414–445`](https://github.com/Artemedi/dsh-paper2agent/blob/6d82a42175a71d3327b773df88f1da0707efe43c/src/paper2project/execution.py#L414-L445) проверяет неизменность source/input деревьев и сохраняет run outcome. Следовательно, OpenResearch — **архитектурный конкурент/референс** для Git snapshot/provenance, а не «готовое улучшение».

## 6. Минимальный offline A/B: план, не эксперимент

**Выполнение отложено до разрешения владельца.** Базовая среда — отдельный временный каталог/контейнер, без доступа к рабочим агентским home, ключам, данным проектов, SQL production, облачным API. При необходимости настоящий OpenResearch CLI запускать **только в отдельной disposable VM** с denied outbound networking и отдельным HOME; не в реальном пользовательском профиле.

**Набор:** 5 синтетических research inputs с допустимыми полными текстами и заранее подготовленной полнотекстовой coverage ведомостью; 2 фиктивных git project trees, 2 run commands с детерминированным JSON результатом и hash oracle. Преднамеренные отрицательные проверки: отсутствующий full text, dirty/uncommitted tree, изменённый коммит/входные файлы, повреждение source archive, рестарт супервизора, отказ сетевого запроса, несогласованная версия schema.

**A:** существующий `dsh-paper2agent` pinned Python+Podman pipeline (с его текущим source tree hash); **B:** такой же безопасный sandbox плюс **только** заимствованный механизм коммит-снимка/экспериментального дерева, либо OpenResearch как изолированный внешний reference, **не** одновременно менять scoring и source ingest. Один и тот же набор фикстур, 5 прогонов на вариант, переставлять порядок A/B; независимый oracle проверяет точные SHA256, ожидаемые артефакты, full-text coverage flag, no-network/no-secrets, правильную causal lineage и отсутствие потерь после kill/recover.

**Метрики:** correctness 100% по оракулам, unrecovered runs 0, непредусмотренный outbound 0, неожиданные файловые записи 0, время запуска p50/p95, RAM peak RSS, CPU seconds, disk bytes written/IOPS, суммарный размер worktrees/archives/logs, стоимость cloud/API **0**. Если B не добавляет новых проверяемых гарантий при приемлемой стоимости, вердикт `NO_ADOPTION / YAGNI`.

Приоритет по портфелю: **ценность 6/10, сложность 7/10** — воспроизводимость уже частично реализована, переход на Rust runtime и его сеть/хуки добавят больше связности, чем пользы без подтверждённого дефекта в существующем Python executor. Критерии внедрения frozen до запуска; сравнение результатов с baseline без подгонки.

**Реально выполнено 2026-11-04:** независимое чтение полного инженерного исходника, документации, исходников двух owner projects, прямой контроль SHA и triage всех 45 profile cards. Не исполнялись Rust CLI, `cargo test`, GUI, agent sessions, network/API/compute runs или Stage 6. Поэтому `LAB_VERIFIED=FALSE` и `PRODUCTION_APPROVED=FALSE`.

## 7. Решение

**Пользовательский исход — `Добавлен в карточки`:** применимость к `dsh-paper2agent` обоснована реальными source seams, но только в части provenance/experiment orchestration. Никакого доказанного преимущества или готовой интеграции нет. **Не** использовать `orx paper` для автоматического full-text approval и **не** заменять текущий Podman sandbox обычным OpenResearch local run.

[Историческая строка Telegram BK-014](2026-11-04-telegram-bookmarks-reconciliation.md) изменяется только с `ожидает проверки` на `разобран`. Остальные 64 строки сохраняют свои исходные статусы.
