# BK-041 — Inspektor Gadget: привилегированная eBPF-трассировка в Podman

**Дата:** 2026-11-06. **Источник:** [официальный Inspektor Gadget v0.57.0](https://github.com/inspektor-gadget/inspektor-gadget/releases/tag/v0.57.0), Git tag `29d60de9f7924607784915533dd5f3cc0052ee1a`. **Статус:** `BOUNDED_SYNTHETIC_EBPF_VERIFIED / NOT_PRODUCTION_READY`. Это измеренный инженерный эксперимент, не независимый peer-reviewed benchmark и не доказательство безопасности инструмента.

## Версии и строго ограниченная модель

На Bazzite 44 Linux `6.18.56-ogc1.1.fc44.x86_64` пользователь авторизовал привилегированный eBPF-тест в локальном Konsole. Никаких паролей не передавалось в чат. Бинарный архив `ig-linux-amd64-v0.57.0.tar.gz` подтверждён SHA-256 `f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1`. OCI gadget `ghcr.io/inspektor-gadget/gadget/trace_exec@sha256:9182278eb6a11b6e2d59a748674b646a8512b715d3563ec3afdf340a2f55d435` закреплён digest, запуск с `--allowed-gadgets`, `--pull never`, штатная `--verify-image` не отключалась. Пакеты, BPF/kernel sysctls, конфигурация ОС, реальные рабочие контейнеры и проекты не менялись.

Режим: пользовательский rootless Podman (сокет `/run/user/1000/podman/podman.sock`), cached `docker.io/library/node:22`, временный контейнер `bk041-ig-synthetic-20261106`, `network=none`, rootfs RO, dropped caps, no-new-privileges, pids 64, memory 256 MiB, CPU 1. В изолированном контейнере выполнялись 40 независимых `/tmp/bk041exec` и 5 `/tmp/bk041neg` (копии `/usr/bin/true`), количества верифицированы отдельно по меткам тестового shell. Привилегия использовалась только для команды `ig`, Python workload запускался как UID 1000. Трассировщик не запускал код на рабочем PostgreSQL и не получал никаких SQL-данных.

## Исходные отрицательные наблюдения — сохраняем

[Первичный тест системных прав](2026-11-04.md), [последующий privilege gate](2026-11-06-privilege-gate.md) и новые [host-пробы](../../data/results/inspektor-gadget/2026-11-06-host-diagnostics.json) — отдельная доказательная область. После `sudo -v` первый `ig run` с `--comm bk041exec --uid 1000` закончился с exit 0, но **0/40** событий. Повторный опыт с началом нагрузки через 23 s после старта и 40-s таймаутом также дал **0/40** как для `--comm`, так и для `--filter-expr.exec 'proc.comm == "bk041exec"'`, хотя debug-журнал подтверждает создание eBPF collection, attaches tracepoints и `running...`. Важная оговорка: версия/режим по умолчанию могут ограничивать область наблюдения контейнерами; эти host-пробы **не являются доказательством потери событий ядром**.

## Положительная проверка именно на Podman

Gadget был закреплён digest, контейнер создан **до** инициализации IG, чтобы rootless Podman API распознал namespace. Запуск `ig -v run ... --runtimes podman --podman-socketpath /run/user/1000/podman/podman.sock`; готовность определялась по debug `msg=running...` после логов attach. В логах видно подключение к mntns тестового контейнера. Отдельные контейнерные испытания (одинаковый `trace_exec`, разный способ фильтрации) дали:

| Испытание | Ожидаемые exec | Получено JSON | Уникальные PID | Ложные negative (из 5) | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `--comm bk041exec` | 40 | **0** | 0 | 0 | 0 |
| `--filter.exec 'proc.comm==bk041exec'`, запуск 1 | 40 | **40** | 40 | 0 | 0 |
| Тот же фильтр, запуски 2–5 | 4 × 40 | **4 × 40** | 4 × 40 | **0 из 20** | 0 |

**Итого при `--filter.exec`: 5/5 прогонов, 200/200 ожидаемых exec, 0/25 отрицательных контролей, 200 уникальных PID в сумме по отдельным прогонам, 0 ошибок парсинга JSON и штатный выход IG каждый раз.** Все 200 сырых record `proc.comm` сверены с `bk041exec`. Состав eBPF link/map после завершения не проверен напрямую через `bpftool`, но процессы IG отсутствуют, временный контейнер удалён; шесть чужих заранее существовавших Podman-контейнеров оставались работать.

**Не делать необоснованный вывод о баге `--comm`:** альтернативный `--filter.exec` дал положительный результат, `--comm` на том же тесте — ноль, но причины отличия (kernel pre-exec comm, semantics фильтрации, стадии pipeline) не расследованы до конкретной строки source. Для воспроизведения **использовать проверенную пару gadget+CLI `--filter.exec`**, а `--comm` не считать доказанно эквивалентным.

## Накладные расходы — не доказаны

Один baseline 40 executions: `0.10276 s`; 5 traced samples: `0.09922`, `0.09774`, `0.10234`, `0.10514`, `0.11688 s`; относительный диапазон против одиночного baseline от **−4.89% до +13.74%**. Это короткая нагрузка, одиночный baseline, без рандомизации/A-B, без counters CPU/RAM/IO, BPF maps, dropped events и p95. **Достоверный overhead и нулевая потеря kernel events НЕ установлены**. Отдельно не тестировалась интенсивная real-world нагрузка на PostgreSQL/AKUZ.

## Существенный privacy/security результат

**При `--output json` параметр `--fields proc.comm,proc.pid,...` НЕ ограничил фактические сериализованные поля:** все 200 реальных событий содержат `args`, `cwd`, `exepath`, `parent_exepath`, `file`. Это сопоставимо с [официальной документацией JSON-формата](https://inspektor-gadget.io/docs/latest/reference/run/). При любом запуске на реальной машине данные аргументов процессов и пути могут быть чувствительными. **В `research-hub` НЕ публикуются необработанные events, stdout JSONL, raw stderr/traces или логи с данными посторонних процессов**; публикуются только агрегированные счётчики и воспроизводимые скрипты. `--filter.exec` ограничил полученные записи, но не доказывает, что внутренний kernel tracer никогда не обрабатывал события других контейнеров.

Исходные данные: [агрегированный результат](../../data/results/inspektor-gadget/2026-11-06-podman-trace.json), [два отрицательных host опыта](../../data/results/inspektor-gadget/2026-11-06-host-diagnostics.json), [первый короткий host опыт](../../data/results/inspektor-gadget/2026-11-06-host-pilot.json). [Реально выполненный контейнерный тест](../../experiments/2026-11-06-bk041-podman-trace.py), [host диагностический тест](../../experiments/2026-11-06-bk041-host-diagnostic.py). Эти scripts запускают реальный привилегированный eBPF tracer: использовать **только** на контролируемом безопасном не-production контейнере, предварительно прочитав код.

## Проекты и решение

| Исследование | Target IDs | Решение | Граница применимости и следующий шаг |
| --- | --- | --- | --- |
| BK-041 Inspektor Gadget | `AKUZ` | `BOUNDED_EBPF_VERIFIED / CONDITIONAL_CANDIDATE` | Linux/PostgreSQL: потенциальный supplemental evidence для exec, file/network RCA; **только container synthetic exec проверен**. Перед production — разрешение владельца, независимая source-level интеграционная точка, ограничение данных, контроль overhead и отката; Windows MSSQL вне области |
| BK-041 Inspektor Gadget | `sequential-rca` | `DOCUMENTED_CANDIDATE / INTEGRATION_NOT_TESTED` | Возможный offline evidence формат для timestamp+PID+source при безопасной redaction; schema/parser, цепь атрибуции и актуальный source-code seam НЕ проверялись; не внедрять |

**Решение реестра:** `проверен экспериментально` **строго в границах 5×40 rootless Podman synthetic exec через `--filter.exec`**, а не «внедрён», «низкий overhead», «готов к RCA» или «безопасен для production». Функциональная пригодность доказана; практический эффект на проектах пока гипотеза. Следующий эксперимент, если потребуется: isolated PostgreSQL Podman workload с независимой нагрузкой, 5–10 рандомизированных A/B, perf/CPU/memory/IO/BPF counters + проверенный sanitizing, и отдельная source review причин `--comm` нулевого результата.
