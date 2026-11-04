# BK-059 — IPFire fireperf 0.3.0: реальный bounded TCP loopback lab

**Дата:** 2026-11-04. **Telegram-источник:** BK-059 (01.11.2026), [официальная страница IPFire](https://www.ipfire.org/fireperf). **Тип первоисточника:** полный инженерный проект/мануал, **не научная рецензируемая статья**. **Вердикт:** `REAL_ORIGINAL_BINARY_LAB_VERIFIED / ISOLATED_LOOPBACK_ONLY / NETWORK_AND_CPU_ADVANTAGE_UNMEASURED / NO_PRODUCTION_APPROVAL`.

## Авторские источники и provenance

- [Официальная техническая статья](https://www.ipfire.org/fireperf), [полная `fireperf(8)` man page](https://man-pages.ipfire.org/fireperf/fireperf.html), [полный авторский исходный архив fireperf-0.3.0](https://source.ipfire.org/releases/fireperf/fireperf-0.3.0.tar.gz) (опубликован 2026-10-26). GPL-3.0-or-later.
- Официальный tar.gz **BLAKE2b-512** `5f21302765f34a3043fc5df984b13f21355742ad787af84fb5c5d89707bbda079e1a84de465053e59a7f3ac2bb25d72fe45ba0084132d3a4067582bac9962a85`. Hash из метаданных IPFire совпал с локальным `b2sum` после скачивания. Это проверка целостности относительно опубликованного хеша, не независимая криптографическая аутентификация автора.
- Авторы заявляют межхостовые benchmarks: `fireperf (io_uring)` 19.0 Gbit/s и 0.071 CPU s/GiB, `iperf3` 15.9 Gbit/s и 0.505 CPU s/GiB на специально описанных VM; **этот эксперимент их нагрузку, CPU-показатели и сравнительный результат не воспроизводил**. Кроме того, официальный мануал прямо предупреждает: тест `127.0.0.1` отражает host network stack, а **не** путь между двумя машинами и не поведение firewall.

## Сборка оригинального пакета

На Bazzite 44 использован **одноразовый rootless Podman** на базе кешированного образа Fedora 44 toolbox. Средства сборки установлены **только внутрь контейнера** (`gcc`, `make`, autotools, `intltool`, `gettext-devel`, `ncurses-devel`, `liburing-devel`); затем из полного авторского архива выполнены:

```bash
./autogen.sh
./configure --disable-man-pages
make -j2
make check
```

Исходник и собранный исполняемый `fireperf 0.3.0` хранились в `/tmp`; **системной установки нет**. `make` создал оригинальную C-программу и связанные unit/test runners. **`make check` не завершился полностью:** `23 PASS`, `1 SKIP` (тест совместимости с iperf), ни одного наблюдавшегося `FAIL`; последовательность остановилась после `tests/transfer.sh` при ожидании `tests/tui.sh` и внешнем завершении runner через примерно 293 с. Нет доказанного дефекта upstream, но **и нельзя объявлять полные 27/27 прошедших тестов**.

## Реальный ограниченный сетевой эксперимент

[Полный Python driver](../experiments/2026-11-04-bk059-fireperf-loopback-lab.py) запускает только **оригинальный compiled fireperf**, не эмуляцию протокола. Выполняется в **новом** rootless Podman контейнере с `--network=none`, `--cpus=2`, `--memory=512m`, `--pids-limit=128`, `--ulimit nofile=1024:1024`. Перед запуском проверяет **отсутствие default IPv4 route**: попытка того же driver на сетевом хосте отклонена заранее. Внешний исходящий или LAN-трафик отсутствует.

- Сервер `fireperf --server --ipv4 --workers=1 --backend=...` слушал отдельный порт **только внутри изолированного net namespace**; клиент подключался строго к `127.0.0.1`.
- Режимы: `--close` (handshake only) и `--exchange=64:256` (64 байта запрос, 256 байт ответ). В обоих случаях `--rate=10` conn/s, `--connections=20`, `--parallel=2`, `--timeout=5`; сервер завершён after test.
- Варианты I/O: `--backend=epoll` и `--backend=auto`, каждый по **3 повтора** на каждый режим. 2×2×3 = **12 авторских CLI прогонов**, **240** запланированных TCP-соединений, **240 успешно открытых**, **0 failed, 0 lost, 0 skipped**.
- Driver парсит и проверяет исходный `--json`: version `start` / `summary`, server type, `connections.total == attempted == 20`, нулевые failure reasons, соответствие расписания. Для обмена подтверждает `20×64 = 1 280` sent и `20×256 = 5 120` received на каждом из 6 прогонов (`7 680/30 720` байт суммарно). Это **независимая арифметическая проверка фикстуры**, не отдельный пакетный sniffer.
- **Отрицательный контроль:** после отсутствия сервера клиент на другом локальном порту завершился `exit=1`, JSON указал `failed=1, rejected=1`, stderr — `Connection refused`. Он **не** выдал успешный TCP-тест без слушателя.

[**Полные 12 трасс сводных метрик и negative JSON**](2026-11-04-bk059-fireperf-loopback.json) сохраняют каждый исходный `summary` (без реального network PII).

| Mode | Backend requested → used | Прогонов | TCP connections | Median of per-run median handshake | Отказы/пропуски |
| --- | --- | ---: | ---: | ---: | ---: |
| close | epoll → epoll | 3 | 60 | 9 µs | 0 |
| close | auto → **epoll** | 3 | 60 | 8 µs | 0 |
| exchange 64:256 | epoll → epoll | 3 | 60 | 8 µs | 0 |
| exchange 64:256 | auto → **epoll** | 3 | 60 | 8 µs | 0 |

**Важно:** `auto` выбрал **epoll**, а не `io_uring`; значит, не проверены `io_uring` и «в семь раз меньше CPU». Наблюдения handshake порядка 8–9 µs **только loopback**. Сценарии ограничены `10` connections/s, не являются saturation, throughput capacity или benchmark firewall. CPU-процессный счётчик в JSON — приблизительный `resource.RUSAGE_CHILDREN` для клиента, ~0.07 CPU s на короткий процесс включая startup, и **не годится** для честного отношения CPU/GiB. `iperf3` на этой машине отсутствует, независимого A/B throughput нет.

## Применение к AKUZ и DBA

Практический предметный fit: **проверка соединений, отказов, RTT handshake и коротких request-response TCP операций между тестовыми хостами**, потенциально при RCA симптомов PG replication/backup, клиентских disconnect и сетевых bottlenecks. `fireperf` — **активный генератор** и способен создать ненормальную нагрузку, даже если одна операция не использует значимый bandwidth. Он не объясняет redo queue SQL Server, wait stats PostgreSQL, storage latency SAN или packet loss до проведения корректного двуххостового эксперимента. `127.0.0.1` не проходит физический firewall, FC SAN, MPIO или маршрутизатор.

Для `sequential-rca` возможен только **импорт метрик из отдельной безопасной лаборатории**, не запуск сетевого бенчмарка из RCA как части аналитики. Контракт evidence и source-line integration point не проверены.

**Trade-offs:** увеличение `--rate`/`--parallel` может нагрузить conntrack, CPU, CPU IRQ, сетевые очереди, хранилища статистики и безопасность соседних сервисов; пример из сайта `10000 conn/s` нельзя переносить в сеть AKUZ. Требуется отдельное письменное согласование, две disposable машины по сторонам тестируемого сегмента, явная изоляция от пациентов/внутренних API, скорость по малым ступеням с hard cap и fallback stop, независимые `ss`/`nstat`/`sar`/packet counters, paired `iperf3` (где это уместно), CPU per GiB, sent/received, drop reasons, p50/p95/p99. Не тестировать production LAN/SAN/AG/backup shared paths по умолчанию.

**Решение реестра:** `проверен экспериментально` в рамках `OFFLINE_ORIGINAL_BINARY_LOOPBACK_12_RUNS`, **не** `PRODUCTION_BENEFIT_VERIFIED` и не разрешение внедрения.

## Повторение

```bash
# Получить оригинальный fireperf-0.3.0.tar.gz (ссылка выше),
# предварительно сверить b2sum с зафиксированным значением.
tar -xzf fireperf-0.3.0.tar.gz
cd fireperf-0.3.0
./autogen.sh
./configure --disable-man-pages
make -j2

# Затем в другом rootless Podman контейнере:
# - передать собранный бинарник + необходимые runtime shared libraries
#   в read/write рабочий /src (на Fedora toolbox liburing.so.2 добавлялась локально);
# - НЕ предоставлять network/host PID/privileged доступ;
# - --network=none и --cpus=2 --memory=512m.
python3 /src/experiments/2026-11-04-bk059-fireperf-loopback-lab.py \
  --binary /src/fireperf-0.3.0/fireperf --trials 3
```

Driver отказывается работать, если присутствует default IPv4 route, или параметры превышают разрешённые ограничения. Ни исходный авторский код, ни production проекты не модифицировались. `make check` выше зафиксирован как **неполный**, не PASS.