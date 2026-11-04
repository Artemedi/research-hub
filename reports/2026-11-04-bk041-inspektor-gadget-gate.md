# BK-041 — Inspektor Gadget v0.57.0 / eBPF на Bazzite 44

**Дата:** 2026-11-04. **Telegram-источник:** BK-041 (08.10.2026), [inspektor-gadget/inspektor-gadget](https://github.com/inspektor-gadget/inspektor-gadget). **Категория:** полноценный исходный инженерный проект, **не** рецензируемая научная статья. **Результат:** `RELEASE_AND_PERMISSION_GATE_VERIFIED / E_BPF_RUNTIME_BLOCKED / RCA_BENEFIT_UNMEASURED / NO_PRODUCTION_APPROVAL`.

## Первичные источники и версия

- [Официальный репозиторий](https://github.com/inspektor-gadget/inspektor-gadget), [release/tag v0.57.0](https://github.com/inspektor-gadget/inspektor-gadget/tree/v0.57.0) = `29d60de9f7924607784915533dd5f3cc0052ee1a` по `git ls-remote`.
- [Руководство Linux](https://inspektor-gadget.io/docs/main/), [системные требования](https://inspektor-gadget.io/docs/main/reference/requirements/) и [документация CLI](https://inspektor-gadget.io/docs/latest/reference/ig/). Некоторые страницы документации старых команд помечены разработчиками как **outdated**: при запуске предпочитать фактический `ig run --help` релиза, а не старый синтаксис.
- **Официальный архив** `ig-linux-amd64-v0.57.0.tar.gz` — SHA-256 `f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1`; совпал с `digest` GitHub release API. Архив извлечён только в `/tmp`, CLI вернул `v0.57.0`. Пакетный менеджер Bazzite, root-сервисы и настройки ядра не менялись.
- eBPF-код Gadgets пакуется как OCI-образы; установка конкретного Gadget из внешнего registry — **другая доверенная поверхность**. Доступные CLI `--allowed-gadgets`, `--disallow-pulling`, `--verify-image` зафиксированы, но реальная проверка подписи Gadget и блокировка недоверенных образов на этом хосте **не тестировались**.

## Исполненная проверка — только неповышенные привилегии

[Исполняемый тест допуска](../experiments/2026-11-04-bk041-inspektor-gadget-permission-gate.py) · [фактический JSON](2026-11-04-bk041-inspektor-gadget-gate.json).

| Условие | Факт |
| --- | --- |
| Хост | Bazzite 44, Linux `6.18.56-ogc1.1.fc44.x86_64` |
| `/sys/kernel/btf/vmlinux` | существует, BTF available |
| `/proc/sys/kernel/unprivileged_bpf_disabled` | `2` |
| `CapEff` процесса | `0000000000000000` |
| Однократный минимальный вызов `bpf(BPF_MAP_CREATE)` из Python под обычным пользователем | `-1`, `EPERM (1)` |
| Официальный `ig version` и `ig run --help` | успешно, проверены 4 защитные CLI-флага |
| Реальные Gadgets, eBPF attach, перехват syscalls | **0** |
| Повышение привилегий / монтирование / host install | **0** |

**Вывод из опыта:** на данной непривилегированной сессии ядро отклонило минимальную операцию eBPF. Проверен **permission gate**, не fault diagnostic. Установка BTF означает наличие описаний типов ядра, но не гарантирует права на трассировку. `EPERM` не доказывает баг Inspektor Gadget или несовместимость его кода с ядром — это ожидаемое ограничение политики. По этой причине невозможно измерить overhead, потерю событий, достоверность PID/cgroup/namespace attribution, overhead RAM kernel maps/IO, p50/p95 или точность RCA.

**Отрицательный контроль:** намеренно неверный ожидаемый SHA-256 официального архива приводит к отказу теста до любых системных проверок. Процедура распространяет только наши небольшие JSON/скрипты, не бинарники/ключи.

## Предметная применимость к AKUZ/DBA

Для **Linux PostgreSQL** это кандидат на точечное, ограниченное по времени собирание дополнительных доказательств: `trace_open` для доступа к файлам, `trace_exec` для дочерних процессов, TCP/DNS Gadgets для системных сетевых событий. Сопоставлять с `pg_stat_activity`, `pg_stat_io`, системными журналами, pid/cgroup и метриками Prometheus. Ни один eBPF-trace не является SQL-планом, не заменяет `EXPLAIN (ANALYZE, BUFFERS)` и не даёт автоматически причинно-следственного доказательства.

Для `sequential-rca` пригодность **условная**: только как офлайновый evidence-формат, если отдельно подтвердить подходящий schema/parser interface и контракт timestamp/source attribution. Привязка к текущим конкретным строкам RCA-кода не проверена. Для **Windows MSSQL** этот Linux eBPF-инструмент напрямую не подходит (нужны ETW/PerfMon/SQL extended events); нельзя объявлять единое решение на обе СУБД.

**Security/overhead trade-offs:** для работающего Gadget могут потребоваться `CAP_BPF`, `CAP_PERFMON`, и/или другие права в зависимости от hook, kernel и контейнерной среды. Root/privileged контейнер с доступом ко всему `/host` расширяет угрозы; собирать аргументы процессов, пути, socket endpoints потенциально раскрывает чувствительные данные. Разрешены только подписанные, pinned gadget digest и allowlist, filter по нужным PID/cgroup, чёткий срок работы и ограниченный экспорт. Цена CPU, kernel memory, ring-buffer loss, volume и impact на I/O пока **UNKNOWN** — не утверждать `low overhead` без A/B.

**Дальнейший gate, не выполнен:** **только** согласованная disposable Linux-VM/неprod Podman с нужными BPF capabilities; 30–60 секунд per-gadget, 5 повторений и параллельный независимый oracle в виде специально создаваемых open/exec/TCP events. Подсчитать observed/expected, пропуски и неверную атрибуцию, CPU/GPU/RAM/IO, число eBPF events/s, время detach, стоимость export и overhead против no-tracer baseline на том же synthetic workload. Не получать доступ к AKUZ production, живым пациентским данным или секретам.

**Итог по реестру:** `ожидает проверки` / `E_BPF_RUNTIME_BLOCKED_UNPRIVILEGED`, даже несмотря на успешный release/CLI check. Публикация или внедрение не одобрены.

## Повторение проверки только прав

```bash
# Инструмент предварительно скачивается из официального GitHub release v0.57.0,
# проверяется SHA-256 (значение указано выше) и извлекается в отдельный tmp каталог.
python3 experiments/2026-11-04-bk041-inspektor-gadget-permission-gate.py \
  --binary /tmp/inspektor-v0.57.0/ig \
  --release-tar /tmp/inspektor-v0.57.0/ig-linux-amd64-v0.57.0.tar.gz \
  --expected-sha256 f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1
```

Тест сам прекращается при SHA mismatch; `BPF_MAP_CREATE` выполняет только для непривилегированного пользователя с `unprivileged_bpf_disabled=1/2` на x86_64, а при возможном повышенном доступе не загружает BPF-программу. Никаких привилегий/настроек не изменяет.
