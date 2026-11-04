# LIMBO × TelegramBot — ambiguous sendMessage outcome and duplicate publication

**Дата:** 2026-11-04. **Выбранный проект:** `Artemedi/TelegramBot` (автоматизация, а **не** DSH/Wiki_PG).
**Вердикт:** `REAL_TARGET_CONTROL_FLOW_REPLAY_PASS / DUPLICATE_RISK_CONFIRMED_IN_FAULT_MODEL / AT_MOST_ONCE_TRADEOFF / NO_PRODUCTION_APPROVAL`.

## Почему выбран именно этот проект

Портфель содержит прикладные DBA-инструменты, автоматизации, игры и .NET-проект коллеги; предыдущие лаборатории концентрировались на DSH и Wiki_PG. Для очередного эксперимента первым выбран **реальный код другого проекта** и подтверждённая точка побочного эффекта. Альтернативные кандидаты: `BIRD-RL` (DBA, но нужен более тяжёлый PostgreSQL stateful benchmark), `Silent Cue Loss` (документы и форматирование, ещё не подтверждён конкретный ingestion seam), `Concordat` (.NET коллеги, но целевой исходник не предоставлен). В TelegramBot вероятность рискового контракта можно проверить напрямую по `main.py` и `digest.yml`.

## Источники и границы

- **Полная оригинальная научная статья:** [Jiapeng Li, Where Does Exactly-Once Live? / LIMBO, arXiv:2609.29095](https://arxiv.org/html/2609.29095), [arXiv abstract/версии](https://arxiv.org/abs/2609.29095). Ранее рассмотрен полный 23-страничный первоисточник, а для этого теста дополнительно просмотрены **авторские полные LaTeX-секции `paper/sections/formulation.tex`, `benchmark.tex`, `discussion.tex`** из исходного репозитория, включая Proposition о late commit, контракт ключей и ограничения. Это не abstract-only исследование.
- **Авторский код:** [jaxblack/limbo-bench@2db09fb](https://github.com/jaxblack/limbo-bench/tree/2db09fba22a0572a70639162a808906409f612a8), `limbo/world.py`, `limbo/runtime.py`, `limbo/services.py` — реальные классы `World`, `ToolRuntime`, `FaultSpec`, `build_tools`. Код действительно исполнен, но **полный авторский LLM/CLI benchmark с 25 930 эпизодами не воспроизведён**.
- **Реальный целевой исходник:** [Artemedi/TelegramBot@b47c527](https://github.com/Artemedi/TelegramBot/tree/b47c527d40d0e7b0aa5311677eca9e8a14fd1b9e). В `main.py:187-204` `send_telegram` делает POST `sendMessage` через `urllib.request.urlopen` (без стабильного operation key); `main.py:262-269,318-321` сперва отправляет, **потом** обновляет `post_state.json` и `seen_videos.txt`. В `.github/workflows/digest.yml` отдельный шаг `Save state` выполняет `git add`, `git commit`, `git push` **после** выполнения скрипта. `concurrency: video-digest-poster` упорядочивает задания, но не связывает внешний Telegram POST атомарно с Git commit.
- **Telegram Bot API:** [официальная документация `sendMessage`](https://core.telegram.org/bots/api#sendmessage) содержит поля адреса, форматирования и возвращаемое `Message`, **не документирует `idempotency_key`**. При отсутствии достоверного результата POST API нет доказанной общей линейризуемой истории исходящих сообщений для автоматического read-back. `getUpdates` — канал получения обновлений, **не эквивалент** запроса статуса ранее выполненной исходящей операции.
- **Среда:** Python **3.11.16** для TelegramBot (как в workflow); `google-genai~=2.29.0` только чтобы импортировать реальный модуль. Fake env `TELEGRAM_BOT_TOKEN=OFFLINE_TEST_NOT_A_TOKEN` и `GEMINI_API_KEY=OFFLINE_TEST_NOT_A_KEY`. Модуль `generate_science_post` и выбор YouTube видео заменены локальными детерминированными функциями; настоящий `send_telegram` и `main.main()` оставлены **исходными**. Все вызовы `urllib.request.urlopen` перехватывает тестовый транспорт с hardcoded разрешённым адресом и подставляет JSON; запрещены другие endpoint. Результаты — исключительно временные `seen_videos.txt`, `post_state.json`, fake ledger; **Telegram/Gemini/YouTube не вызывались**.

## Что действительно запущено

[Исполняемый replay](../experiments/2026-11-04-limbo-telegrambot-send-retry.py) создаёт 20 независимых fake video IDs на каждый из **9 сценариев**, всего **180 отдельных двойных запусков** исходного `TelegramBot.main()` с настоящим JSON-построением `send_telegram`. Независимый oracle считает **сервисные эффекты** в `MockTelegram.effects`, не доверяя локальным файлам TelegramBot. Каждый случай повторяет операцию в новом локальном состоянии; delayed commit срабатывает в детерминированном виртуальном сервисе после второго запуска (без sleep).

| Fault (по 20 случаев) | Наблюдение первого запуска | Итог ledger: постов на логическое видео | Случаев с дублированием |
| --- | --- | ---: | ---: |
| `success` | 200 OK, state записан | 1 | **0/20** |
| `timeout_pre` | timeout, сервис не записал | 1 после повторной попытки | **0/20** |
| `timeout_post` | timeout, сервис записал до потери ответа | 2 | **20/20** |
| `http500_pre` | HTTP 500, сервис не записал | 1 после retry | **0/20** |
| `http500_post` | HTTP 500, сервис записал до ошибки | 2 | **20/20** |
| `timeout_late` | timeout, in-flight запись исполнится позже | 2 после settle | **20/20** |
| `duplicate_delivery` | 200 OK, один запрос доставлен дважды сервисом | 2 | **20/20** |
| `crash_after_ack` | сервис записал, процесс умер до `save_post_state` | 2 после рестарта | **20/20** |
| `state_lost_after_ack` | сервис записал, новое задание не видит изменения checkout | 2 | **20/20** |

Итого **120/180** дублированных synthetic trajectories; **это доля специально сконструированной выборки, не оценка частоты сбоев Telegram в production**. Модель HTTP500-after-commit не утверждает, что Telegram фактически возвращал такие 500. В режиме `crash_after_ack` использован `SystemExit`, который не перехватывается `except Exception` и тем самым моделирует прерывание до финального сохранения. Режим `state_lost_after_ack` удаляет **только временные тестовые файлы** между двумя invocations — это имитация неприменённого `git push`, а не факт существования такого инцидента.

**Тест наблюдательной эквивалентности:** в каждой из 20 пар `timeout_pre` и `timeout_post` первая попытка видит одинаковый `RuntimeError`, а `seen_videos.txt` и `post_state.json` побайтно одинаковы (в обоих случаях не подтверждены). Сервисный ledger скрыто различается: **0** против **1** эффекта. После blind retry оба worlds получают один новый эффект, поэтому в `timeout_post` появляется дубль. **Локальный клиент не может сделать корректный exactly-once выбор только по этим наблюдениям.**

## Контроль с настоящим исходным LIMBO (не Telegram API!)

Авторский `World` + `ToolRuntime` запущен для 20 семян × 3 режима (`timeout_post`, `timeout_late`, `duplicate_delivery`) × 2 исходных контракта: `social_publish(platform=x)` **без** ключа и `social_publish(platform=mastodon)` **со стабильным ключом**. Итого **120 оригинальных LIMBO service episodes**:

| Авторский симулированный контракт | timeout_post | timeout_late | duplicate_delivery |
| --- | ---: | ---: | ---: |
| x: без идемпотентности | 20/20 дублей | 20/20 | 20/20 |
| mastodon: тот же стабильный key | 0/20 | 0/20 | 0/20 |

Это демонстрирует **контрактный механизм**, а не обещание, что Telegram поддерживает Mastodon-подобный `idempotency_key`. Печатные результаты авторов (например, 28%→4% при расширенном контракте на модельном benchmark) относятся к **их собственным моделям и сценариям** и нами не воспроизведены.

## Что может сделать TelegramBot без поддержки key на сервере

Локальный outbox/резервирование `PENDING` *до* отправки + запрет автоматической повторной публикации при неизвестном исходе обеспечивает только **at-most-once retry decision в одном контролируемом процессе**, при условии durable store/fencing. При `timeout_pre` пост мог вообще не появиться; при `timeout_post` он уже появился. Результат `UNKNOWN/UNCERTAIN` должен приводить к ручной сверке/эскалации, а **не** к `SENT`. Изолированная toy-model с 20 случаями на режим показывает: `timeout_pre` → 20/20 пропусков при остановке retry; `timeout_post` и `timeout_late` → 0 дублей, но требуется reconciliation. Это модель policy, **не патч TelegramBot**.

Следовательно, нельзя добросовестно обещать и «ни одного дубля», и «каждое видео доставлено» при неидемпотентном внешнем write и неоднозначном ответе без надёжной внешней сверки или серверного контракта. Дополнительный локальный файл `seen_videos` и однопоточный GitHub Actions concurrency этой невозможности не решают.

## Архитектурная рекомендация / trade-offs

1. **Краткосрочно:** явно сохранять состояние `READY | SENDING | SENT(message_id) | UNCERTAIN` и ключ логической операции `chat_id + thread_id + video_id` **в устойчивом хранилище**, не на уровне простого необработанного `git push`. HTTP 200 с валидным `ok/message_id` можно сохранять как подтверждение (сегодня `send_telegram` просто возвращает bytes, без проверки JSON `ok`), но *само подтверждение* и запись `SENT` также имеют окно сбоя. Обязательны блокировка повторов и наблюдаемая очередь `UNCERTAIN`; не помечать UNKNOWN как опубликованный.
2. **Изоляция:** при параллельном запуске (вне `concurrency` GitHub Actions) нужен operation-level lock / compare-and-set; для long-lived pending нужен stale-handling **без автоматического повторного non-idempotent POST**. Дубли от **внутренней redelivery у сервиса** локальная блокировка не устранит. Для ручной сверки можно включать стабильную метку видео в текст, но это **не idempotency key**.
3. **Долгосрочно:** если нужен строгий delivery contract, нужен сервис/посредник с **поддерживаемой** идемпотентностью и подтверждённой операцией read-back — нельзя просто добавить произвольное поле в `sendMessage`. Без него выбор policy: **at-least-once** (дубли допустимы) или **at-most-once** (пропуски/ручной разбор), но не guaranteed exactly-once. Отдельно контролировать уже заявленную бизнес-политику **не чаще одного видео в час и не подряд из одного канала**.
4. **Цена:** durable outbox повышает IO и операционную сложность; ручная очередь `UNCERTAIN` снижает throughput и добавляет SLA на разбор; retry повышает полноту доставки, но увеличивает дубли; блокировка ненадёжного write ограничивает параллельность. Требуется тест редактирования/удаления опубликованного сообщения, если бизнес разрешит компенсацию, но компенсация не превращает выполненные дубли в exactly-once.

## Верификация и репродукция

- **Оригинальный LIMBO:** после установки зависимостей выполнен полный доступный `python -m unittest discover` — **65/65 PASS**; первоначально без `numpy/pandas` только 33 unit-теста `test_env.py` проходили, 2 других модуля не импортировались. После установки requirements все 65 прошли. Нет реальных LLM, оплаченных вызовов или реального provider.
- **Наш скрипт:** Python 3.11 (как TelegramBot workflow), `py_compile`, Ruff (`E4,E7,E9,F`) PASS; 180 основных и 63 в альтернативном прогоне (`cases-per-mode=7`) PASS. **Мутационный отрицательный контроль** с ошибочно изменённым oracle `EXPECTED["timeout_post"]=1` падает `AssertionError: ("timeout_post", 2)`, следовательно тест обнаруживает возвращение дубля.
- Никаких изменений исходников `TelegramBot`, `limbo-bench`, действующего GitHub Actions, расписания или внешних сервисов. Отчёт, исполненный Python и JSON-агрегаты — только в `research-hub`; проектная карточка меняется только в `project-registry`.

```bash
git clone https://github.com/Artemedi/TelegramBot /tmp/limbo-test-telegram
git -C /tmp/limbo-test-telegram checkout b47c527d40d0e7b0aa5311677eca9e8a14fd1b9e

git clone https://github.com/jaxblack/limbo-bench /tmp/limbo-test-paper
git -C /tmp/limbo-test-paper checkout 2db09fba22a0572a70639162a808906409f612a8

uv venv --python 3.11 /tmp/limbo-test-venv
uv pip install --python /tmp/limbo-test-venv/bin/python 'google-genai~=2.29.0'
# Optional original full suite:
uv pip install --python /tmp/limbo-test-venv/bin/python -r /tmp/limbo-test-paper/requirements.txt
(cd /tmp/limbo-test-paper && /tmp/limbo-test-venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q)

PYTHONDONTWRITEBYTECODE=1 /tmp/limbo-test-venv/bin/python \
  experiments/2026-11-04-limbo-telegrambot-send-retry.py \
  --telegram-root /tmp/limbo-test-telegram \
  --limbo-root /tmp/limbo-test-paper \
  --telegram-commit b47c527d40d0e7b0aa5311677eca9e8a14fd1b9e \
  --limbo-commit 2db09fba22a0572a70639162a808906409f612a8 \
  --cases-per-mode 20
```

[**Фиксированные результаты 180 + 120 случаев**](2026-11-04-limbo-telegrambot-send-retry.json) не содержат исходных реальных сообщений или секретов. Это offline-fault-test, а **не** статистическое измерение реальной частоты Telegram API ошибок и не разрешение изменять производство.

## Gate

`TG_PUBLISH_AMBIGUITY_REPRODUCED / NO_KEYS_ON_TELEGRAM_CONTRACT / SAFE_POLICY_REQUIRES_OWNER_DECISION`.

**Следующий шаг только после подтверждения владельца:** выбрать политику `UNCERTAIN` vs automatic retry и согласовать хранилище outbox, способ ручного reconciliation и допустимость повторов/пропусков. Затем сделать минимальный патч и тесты на отдельной ветке с rollback. Переписывать весь TelegramBot/сервис под новый framework или внедрять LLM-guided retry здесь не обосновано.
