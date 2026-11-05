# BK-041 — Inspektor Gadget: разрешение получено, ОС-аутентификация блокирует запуск

**Дата:** 2026-11-06. **Источник:** [Inspektor Gadget v0.57.0](https://github.com/inspektor-gadget/inspektor-gadget/releases/tag/v0.57.0), проверенная сборка. **Статус:** `PRIVILEGED_TEST_AUTHORIZED / SUDO_AUTH_REQUIRED / E_BPF_ATTACH_NOT_RUN`. Предыдущая [непривилегированная проверка](2026-11-04.md) сохраняется без изменения её исходных результатов.

## Что действительно сделано

- Владелец явно разрешил привилегированный eBPF-эксперимент. Хост Bazzite 44, ядро `6.18.56-ogc1.1.fc44.x86_64`, пользователь `Trintos` (UID 1000, группа `wheel`). Установка и конфигурация Linux не менялись.
- Официальный архив релиза `ig-linux-amd64-v0.57.0.tar.gz` скачан **только во временный каталог**; SHA-256 `f5e3233c6c1ffc3ad068326913e11def23c7cef6c764e585c2205cda0e2f76f1` совпал с ранее проверенным авторским digest. Извлечённый `ig version` вывел `v0.57.0`.
- Для разрешённого теста временно разрешено вызывать `sudo` через конфигурацию Desktop Commander; выполнен **только** `sudo -n id`. Результат: `sudo: требуется указать пароль`. В секции `finally` исходный список `blockedCommands` восстановлен, включая запрет `sudo`.
- **Ни одна** привилегированная eBPF-программа, BPF map, trace_exec/trace_open gadget или сторонний OCI-образ не запускались. Не выполнялись `sysctl`, `setcap`, установка пакета, изменение сервиса, перезапуск и не осуществлялся сбор аргументов, файлов, сокетов либо данных процессов.

## Фактический вывод и блокировка

Старый независимый непривилегированный `bpf(BPF_MAP_CREATE)` завершался `EPERM`; новый privilege gate упёрся в необходимость ОС-пароля. Поэтому запрещено говорить `E_BPF_VERIFIED`, `LOW_OVERHEAD`, `NO_LOSS` или `RCA_READY`. Это `BLOCKED: OPERATING_SYSTEM_AUTHENTICATION`, не ошибка Inspektor Gadget.

**Минимальный следующий тест после локальной ОС-аутентификации:** в доверенной терминальной сессии на временном непродуктивном хосте/контейнере выполнить pinned `ig run trace_exec` с ограничением UID/PID и 30–60 сек, без захвата чужих команд, 5 повторов; синтетический независимый oracle из фиксированного списка exec-событий. Сопоставить expected/observed и attribution, event loss, p95, CPU, kernel memory, RAM, IO с no-tracer baseline; гарантировать detach и отсутствие остающихся BPF links. Для privileged запусков использовать только явно доверенный gadget digest, без `:latest`.

| Research item | Target IDs | Причина | Ограничения | Следующий шаг | Evidence |
| --- | --- | --- | --- | --- | --- |
| Inspektor Gadget | `AKUZ` (Linux/PostgreSQL), `sequential-rca` | Kernel event evidence дополняет, но не заменяет DBA-планы/метрики и RCA | Нет OS-auth и runtime traces; нет текущего source seam | 30–60 секунд не-prod с независимым synthetic oracle и bounded overhead | `RELEASE_HASH_VERIFIED / BPF_NOT_RUN / NEEDS_AUTH` |

Изменений в работающих проектах и приватном реестре нет. Начальная публикация release-аудита сохранила своё доказательное значение.
