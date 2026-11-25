# OpenResearch — переносимость снимков опыта

1. Закрепить Paper2Project на `c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd` и OpenResearch на `23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d`. Использовать четыре небольших искусственных Git-дерева с одним текстовым файлом. Для каждого создать коммит, затем изменить файл в рабочем дереве.
2. В Paper2Project вызвать штатную регистрацию опыта. Переместить исходный checkout и проверить хеш и фактические байты рабочей копии. Сверить SHA-256 каждого файла штатного ZIP-экспорта по манифесту и проверить, содержит ли он файлы опыта. Дополнительно проверить реакцию на изменение локально сохранённой копии.
3. В OpenResearch вызвать подлинные Rust-методы `SourceSnapshot::create` и `SourceSnapshot::from_run` через один добавленный тест в отдельной копии исходников. Oracle читает архив через системный `tar` и сравнивает его содержимое с известными байтами коммита. Сверить записанный SHA-256 через `sha256sum`. Повторить создание для того же коммита, переместить архив в другую папку данных без исходного checkout, проверить отклонение изменённого архива.
4. Развести два вопроса: наличие воспроизводимой копии в той же рабочей области и перенос источника как отдельного артефакта. Записать, какие байты фиксирует каждый вариант при незакоммиченном изменении. Два прогона должны дать одинаковые агрегаты.

Зависимости Rust загружаются отдельно с `Cargo.lock`. Сборка и тест выполняются без сети в одноразовом окружении, с отдельными данными и без пользовательских томов. Задача проверяет лишь снимки и экспорт. Launcher, supervisor, агенты, удалённые исполнители и научные шаги не запускаются. [Предыдущий опыт](../../reviews/alphaxiv-openresearch/2026-11-06-provenance-ab.md) · [Исходник OpenResearch](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/compute.rs)

## Как воспроизвести

Для Paper2Project в Linux или WSL передать текущий чистый checkout закреплённой ревизии сценарию `python -B experiments/alphaxiv-openresearch/paper2project-snapshot-portability.py CHECKOUT`.

Для OpenResearch извлечь `git archive` закреплённого коммита в отдельный рабочий том. Образ сборки `docker.io/library/rust@sha256:6258907abe69656e41cd992e0b705cdcfabcbbe3db374f92ed2d47121282d4a1`. Получить зависимости командой `cargo fetch --locked --target x86_64-unknown-linux-gnu` с отдельным `CARGO_HOME` в этом томе. Затем выключить сеть контейнера, ограничить его 2 CPU и 4 GiB RAM и запустить следующий фрагмент внутри копии. `/snapshot-test.rs` — файл сценария с read-only bind-mount. Каталог для UI пустой, он нужен компилятору для поиска встроенных ресурсов.

```sh
mkdir -p ui/dist
cp /snapshot-test.rs src/portability_lab.rs
printf '\n#[path = "portability_lab.rs"]\nmod snapshot_portability;\n' >> src/compute.rs
ORX_LAB_ROOT="$(mktemp -d /lab/fixture.XXXXXX)" \
CARGO_PROFILE_TEST_DEBUG=0 GIT_CONFIG_NOSYSTEM=1 \
cargo test --bin orx --locked --offline --no-default-features -j2 \
  snapshots_survive_checkout_loss_and_relocation -- --test-threads=1 --nocapture
```

Три строки подготовки выполняются один раз на свежей копии. Для следующего прогона задаётся новый `ORX_LAB_ROOT`. Тест оставляет исходные методы без правок и добавляет один сценарий. Исходный checkout и исходный архив не меняются.
