# fast-anything — profile-guided AI-assisted локальная оптимизация приложений

[Структурированная запись и связи](../catalog/studies/fast-anything.md)

**Тип:** инженерный open-source инструмент (MIT), не peer-reviewed научное исследование. Авторские заявления и локально проверенная структура кода разделены.

**Первичный источник:** [EL4CTEO/fast-anything](https://github.com/EL4CTEO/fast-anything/tree/ce0e3889e774a01412c2d181292118fb3512cdde) (`ce0e3889e774a01412c2d181292118fb3512cdde`, осмотр 22.11.2026); [README](https://github.com/EL4CTEO/fast-anything/blob/ce0e3889e774a01412c2d181292118fb3512cdde/README.md), [CI](https://github.com/EL4CTEO/fast-anything/blob/ce0e3889e774a01412c2d181292118fb3512cdde/.github/workflows/ci.yml), [MIT LICENSE](https://github.com/EL4CTEO/fast-anything/blob/ce0e3889e774a01412c2d181292118fb3512cdde/LICENSE).

**Исследуемая методология:** `profile → choose measured CPU hotspot → baseline → AI-assisted local rewrite → differential correctness check → end-to-end benchmark → independent review → opt-in / rollback`. Rust — реализация кандидата, а не обязательный результат методологии.

**VERIFIED (статический source inspection):** инструмент ранжирует функции по измеренной доле wall-time × переносимости; порог `WORTH_IT=0.02` (2%), а не «автоматически переписать 5% кода». Записывает реальные вызовы и сверяет с нативным портом; наличие `verify`, `enable/disable`, проверки stale source и сравнительного `bench` подтверждено кодом. Это не проверка корректности всех состояний или любого пользовательского приложения.

**AUTHOR_REPORTED:** примеры ускорения целых демо: Python fuzzy-dedupe **4.91 с → 42 мс (116×)**, TypeScript **3.11 с → 155 мс (20×)**, C# **4.03 с → 312 мс (13×)**. Сценарии в основном fuzzy deduplication; независимого воспроизведения в нашем окружении **нет**.

**Ограничения:** полезно только если существенная часть общего времени приходится на переносимую CPU-функцию; БД, RPC, диск, блокировки и сетевые ожидания сами по себе не ускоряются. Проверка на записанных вызовах не равна формальной эквивалентности; stdout-бенчмарк не покрывает побочные эффекты, p95/p99 и многопользовательскую нагрузку. Добавляются FFI, Rust toolchain, платформенные сборки и расходы на сопровождение.

**Текущий вывод:** `ENGINEERING_SOURCE_REVIEWED / ANALYSIS_ONLY / BENEFIT_UNPROVEN`. Два документальных кандидата: `akuzlogparser` и `akuz-schema-inventory`; для них сначала требуется CPU-профиль на фиксированных синтетических данных. В AKUZ production и в исходники проектов ничего не внедрено.

[Подробная проверка кода и экспериментальный протокол](../reviews/fast-anything/2026-11-22.md) · [портфельная матрица](../portfolio/2026-11-22/review.md).
