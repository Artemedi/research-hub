# BK-014 — alphaXiv OpenResearch: reproducibility/provenance vs dsh-paper2agent

**Дата:** 2026-11-06. **Итог:** `SOURCE_BUILT_AND_COMPUTE_TESTED / ORIGINAL_BASELINE_EXECUTED / SOURCE_DERIVED_ARCHIVE_PROXY_AB / NO_ADOPTION`. Это инженерное исследование с ограниченным offline A/B, **не запуск всего orx workflow и не доказательство улучшения research quality**.

## 1. Полнота первоисточников и version pin

**Исходная программа:** [alphaXiv/OpenResearch](https://github.com/alphaXiv/OpenResearch/tree/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d), коммит `23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d`, `Cargo.toml` v0.2.24, MIT. Прочитаны исходники `src/compute.rs` (`SourceSnapshot::create / from_run / archive / digest_file / install_content_addressed`), `src/local/experiments.rs`, `src/local/localrun.rs`, `src/commands/paper.rs`, полные README, `arc/experiments.md`, `arc/storage.md` и официальная [документация экспериментов](https://openresearch.sh/docs/experiments). [Предыдущий source review](2026-11-04.md) содержит ссылки path:line и риски. **Это открытая инженерная реализация, не отдельная рецензируемая научная статья; термин FULL_TEXT_VERIFIED нельзя автоматически переносить на бумаги, найденные инструментом.**

**Базовый проект:** [Artemedi/dsh-paper2agent@6d82a42175a71d3327b773df88f1da0707efe43c](https://github.com/Artemedi/dsh-paper2agent/tree/6d82a42175a71d3327b773df88f1da0707efe43c), только detached scratch clone. Для A **реально импортирована и запущена** `paper2project.execution.tree_hash` из оригинального Python-кода, а контракт `container_argv` проверен прямым вызовом. Он считает SHA256 по именам, правам, содержимому **включая .git**, отказывает на symlink/special files и ограничивает максимальные размеры. Его executor уже обеспечивает Podman `--network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges` с исходниками и входами как read-only mounts. Сам текущий production проект и runtime не изменялись.

## 2. Сборка и подлинные тесты OpenResearch

В одноразовом каталоге Bazzite Rust зависимостям позволили скачивание с crates.io в **отдельной фазе `cargo fetch --locked`**. Ни user SSH tokens, ни HOME, ни агентные profiles не монтировались. Затем `cargo test --locked --offline --no-default-features -j2 --no-run` и `cargo build --locked --offline -j2 --no-default-features` **PASS** в rootless Podman `docker.io/library/node:22` с `--network=none`, read-only rootfs, dropped caps, fake HOME. Пин исходников проверен по `git rev-parse HEAD`.

**Оригинальные Rust unit-тесты compute области:** `cargo test --locked --offline --no-default-features -j2 compute::tests -- --test-threads=2` — **8/8 PASS, 0 FAIL**. [Сохранённый журнал](../../data/results/alphaxiv-openresearch/2026-11-06-orx-compute-tests.txt). Это действительно исполняемые тесты автора, но они **не покрывают вызов `SourceSnapshot::create` и полный experimental run**: не следует приравнивать 8 PASS к end-to-end верификации системы, daemon/restart, web UI, SSH, managed compute или model agents.

## 3. Реальный ограниченный A/B на синтетическом Git

[Воспроизводимый Python runner](../../experiments/2026-11-06-bk014-openresearch-provenance-ab.py), [полный машинный JSON с 25 парами и 5 негативными наборами](../../data/results/alphaxiv-openresearch/2026-11-06-provenance-ab.json). Изоляция: rootless Podman Node:22, **network none**, read-only rootfs, dropped capabilities, fake HOME, synthetic Git fixtures; оба pinned repos монтировались в контейнер как `:ro`, временная директория тестовых данных отдельно. Реальные SSH, научные статьи, агентные профили, токены, SQL-базы, пользователи и web-сервисы **не использовались**.

**A — текущая техника `dsh-paper2agent`:** исполнение настоящей `execution.tree_hash(repo)` по текущему source tree, включая Git metadata. Результат — digest **без сохранённого набора исходных байтов**. Если checkout исчезает, по одному хешу нельзя восстановить его содержимое.

**B — SOURCE-DERIVED proxy, не настоящий orx API:** точное воспроизведение алгоритма из `src/compute.rs` вызовом `git archive --format=tar <commit>`, SHA256 и content-addressed таром `<sha256>.tar`, с независимым checksum- и tar file-contents oracle. **Класс `SourceSnapshot::create` из Rust-библиотеки напрямую в этих 25 прогонах не вызывался.** Авторский исходный код OpenResearch дополнительно компилировался и прошёл указанные 8 тестов, но реальный orx CLI snapshot lifecycle не проверен. Отличие A/B **заложено в контрактах**: A хеширует текущий каталог со служебными файлами, B архивирует только коммит. Это не сравнение одинаковых функций.

**План:** пять фиксированных seeds `20261106–20261110`, на каждую 5 повторений A/B, порядок вызова в паре переставлялся. Пять маленьких Git-деревьев с **синтетическим** `papers/full.txt`, разделами Methods/Results/Limitations, Python `src/analyze.py` и JSON inputs. Проверка полнотекстового входа **внешняя и обязательная**, не встроена в OpenResearch.

| Метрика, 25 запусков на вариант | A: реальный Python `tree_hash` | B: Git archive proxy |
| --- | ---: | ---: |
| p50 wall | 2.6991 ms | 1.8550 ms |
| p95 wall nearest rank | 3.3297 ms | 2.2269 ms |
| p50 учтённое CPU | 2.6810 ms | 1.8890 ms |
| Суммарные логические tar-байты, записанные в тесте | 0 | **256 000** |
| Независимый oracle | 25 совпавших исходных хешей | 25 проверенных SHA256 + содержимое tar |

**Нельзя заключать, что OpenResearch быстрее:** B не включает SQLite metadata, supervisor, agent invocation, network, model, а A дополнительно хеширует изменчивый `.git`. Реальная нагрузка имеет другие масштабы, B тратит место под архивы и IO. `0` tar-байтов у A **не означает нулевой disk IO** (исходники читаются для хеширования). Max RSS `20 496 KiB` — cumulative whole-process, не per-variant. GPU/VRAM N/A, LLM requests 0, model tokens N/A, облачные расходы 0.

## 4. Отрицательные контроли — 5 из 5 для каждого

| Сценарий | Наблюдение A (original) | Наблюдение B (source-derived) | Вывод |
| --- | --- | --- | --- |
| Изменили только `.git/config`, code/HEAD без изменений | Digest текущего дерева изменился **5/5** | Commit tar digest стабилен **5/5** | Метаданные входят в A-хеш намеренно; это более строгий контроль, но может порождать повторные проверки |
| Создали незакоммиченную правку научного файла | A заметил изменение **5/5** | В archive по коммиту правка **не попала 5/5** | B **должен иметь отдельный dirty preflight**, если ожидается текущий workspace |
| Изменили файл и создали Git-коммит | Оба digest изменились **5/5** | Новый committed archive SHA **5/5** | Оба обнаруживают новую ревизию, в разных формах |
| Изменили байт хранимого tar | A N/A, тар не хранит | SHA256 отказал **5/5** | B позволяет защищать persisted payload от corruption |
| Удалили временный checkout после копирования снимка | A: digest не восстанавливает source | Копия tar осталась валидной и содержала все исходные файлы **5/5** | Архив переносит фактический committed source, а не только checksum |
| Удалили полный текст Methods/Results/Limitations | Сам A-геш не классифицирует scientific coverage | Сам B snapshot не классифицирует coverage | **Внешний FULL_TEXT gate** заблокировал **5/5** случаев `FULL_TEXT_UNAVAILABLE` |

**Обязательная оговорка:** локальный Python oracle не имитирует падение/рестарт реального `orx` supervisor, SQLite WAL recovery, ошибку remote backend, межпользовательскую ACL, upload в облако или утечку секретов. Успех corruption check для локального proxy не доказывает, что вся цепь реальных orx runs всегда обнаруживает повреждённый snapshot. Исторический исходный Rust метод `from_run` имеет проверку хеша, но её реальный E2E путь здесь не выполнен.

## 5. Безопасность и сравнение с действующим процессом

OpenResearch local executor запускает пользовательские исследовательские команды в доступном окружении своего хоста (`src/local/localrun.rs`); **он не гарантирует Podman isolation**, которую уже обеспечивает `dsh-paper2agent`. Поэтому **не заменять** безопасный Python runner на `orx local run`. В официальном README отмечена отсутствие полноценной межпользовательской application ACL для remote dashboard на общем хосте. Кроме того, official release opt-out telemetry и внешние источники/model providers означают, что local-first **не всегда** outbound-free. В тесте не запускали dashboard, агентные сессии, `orx paper` или telemetry-enabled release.

**FULL_TEXT policy:** `orx paper --full` не гарантирует полную статью для PubMed/OpenAlex/bioRxiv; alphaXiv extracted version тоже требует отдельной проверки метода, таблиц и приложений. Нельзя автоматически превращать abstract в `FULL_TEXT_VERIFIED`. В нашем тесте было 5 явно синтетических full-text фикстур и пять отрицательных случаев, но **не тестировалась загрузка статей** и методологическая оценка реальных работ.

## 6. Применение к dsh-paper2agent и граница YAGNI

| Исследование | Project ID | Наблюдение | Вывод / следующий gate |
| --- | --- | --- | --- |
| BK-014 OpenResearch | `dsh-paper2agent` | B позволяет сохранить точную версию committed source + digest и восстановить её без исходного checkout; A фиксирует текущие файлы и обнаруживает dirty change | `DOCUMENTED_CANDIDATE / PROVENANCE_ARCHIVE_OPTION_ONLY`. При доказанном дефекте воспроизведения — добавить минимальный **неизменяемый source tar** и manifest `commit/digest/size` как **дополнение** к существующим `tree_hash` и Podman; сначала определить независимый raw-vs-committed invariant, dirty preflight, archive size limit/retention, repeated offline test |

**Не внедрять второй оркестратор.** Для реального подтверждения пользы нужен проектный сценарий, где после изменения или удаления исходного checkout A воспроизвести run **не может**, а B восстанавливает его из архива; при этом проходя validation full-text, независимый experiment oracle, no-network, output redaction, rollback. Сравнить CPU/память/IO и потребление диска на реальных *несекретных копиях*, без старта внешнего агента и с owner approval. Пока эффект на продуктивность исследования **не измерен**.

**Вердикт:** `разобран / BOUNDED_EXECUTED_PROVENANCE_COMPARISON / ORX_E2E_NOT_TESTED / NO_PRODUCTION_APPROVAL`. Новых методов scientific scoring, выгоды LLM и code changes для целевого `dsh-paper2agent` не заявлено; владельцу предлагается только опциональный тонкий source archive при доказанной потребности.
