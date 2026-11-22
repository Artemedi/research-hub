# rust-anything — evidence-gated перенос hot paths в Rust под управлением агента

[Структурированная запись и связи](../catalog/studies/rust-anything.md)

**Тип:** open-source engineering tool / code-migration framework, не научная публикация. **Источник:** [erkamyaman/rust-anything](https://github.com/erkamyaman/rust-anything), pinned [`50d3810b622fdc6cb3aee965fe4c9d4b4f29205b`](https://github.com/erkamyaman/rust-anything/tree/50d3810b622fdc6cb3aee965fe4c9d4b4f29205b), дата source review 23.11.2026. [Лицензия MIT](https://github.com/erkamyaman/rust-anything/blob/50d3810b622fdc6cb3aee965fe4c9d4b4f29205b/LICENSE).

**Ключевая поправка к медиа-описанию:** инструмент **сам не переводит** произвольный код на Rust. Он профилирует исходную программу; `bridge` генерирует crate и FFI/wrapper; Claude/Codex/разработчик вручную пишет Rust; `record` снимает динамический эталон; `diff`, `fuzz`, `gate` проверяют *покрытые случаи*, а `bench` сравнивает скорость. Для небольших частей JavaScript/Python/C/Go/Ruby/Java/Kotlin доступны собственные language adapters; PHP/C# поддерживают более ограниченные bridge/FFI сценарии. Полный перенос целого приложения требует поэтапного ручного восстановления контрактов и обвязки.

**Доказательства производительности:** [README](https://github.com/erkamyaman/rust-anything/blob/50d3810b622fdc6cb3aee965fe4c9d4b4f29205b/README.md) заявляет **19×** на Prettier CLI (128,6 → 6,9 с, 2360 JS/TS-файлов), **32×** на Fuse.js (91,2 → 2,8 мс при 50 тыс. строк). Но [real-world study](https://github.com/erkamyaman/rust-anything/blob/50d3810b622fdc6cb3aee965fe4c9d4b4f29205b/docs/real-world.md) показывает `vercel/ms` с **0,56×** при одиночном вызове через FFI; C `libavutil` не даёт гарантированного ускорения. В Prettier **15 861 / 17 224** записанных случаев выполняются полностью на Rust, остальные используют fallback на старый Prettier, хотя все 17 224 совпадают по выводу. Это **AUTHOR_REPORTED**, без нашего воспроизведения. Универсальное «10–20× для любого приложения» не доказано.

**Предмет доказательства:** replay `gate` сравнивает эталон только на записанных входах. Нет гарантии глобальной эквивалентности, корректного поведения за пределами corpus, безопасной миграции OS/kernel/DB или независимой формальной верификации. `coverage` в gate — отчёт, не обязательный порог. Nondeterministic masking, accepted known diffs и side effects требуют независимого policy/evidence guard. Исходные `record`, `diff`, `gate` **выполняют исходный код**, включая запись файлов, сетевые вызовы и запросы к БД; нужны изоляция и фиктивные данные.

**Применимость к портфелю (условная):** `akuzlogparser` — отдельный CPU-bound parser/classifier benchmark на синтетических логах; `Wiki_PG` — независимая проверка возможности ускорить измеренный Python hot path без изменения SQLite/MCP evidence semantics. `dsh-paper2agent` и `dsh-runtime` не назначены автоматическими target без CPU profiling/конкретного bottleneck. Архитектурный выбор: **partial hot-path bridge**, не rewrite всей АКУЗ/операционной системы.

**Вердикт:** `BOUNDED_CODE_REVIEW / DOCUMENTED_CANDIDATE / NEEDS_EVIDENCE / BENEFIT_UNPROVEN / NOT_PRODUCTION_APPROVED`. В лаборатории не запускались neither upstream binaries nor native agents, не изменялся production/source проекта.

[Датированный аудит](../reviews/rust-anything/2026-11-23.md) · [проектная матрица](../portfolio/2026-11-23/rust-anything.md).
