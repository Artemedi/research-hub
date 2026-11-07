# YouTube Skills — проверка границы внешнего TranscriptAPI и хранения секрета

**Дата:** 07.11.2026. Предметное дополнение к [инженерному обзору 04.11](2026-11-04.md); прежнюю проверку исходных Markdown-инструкций и условную матрицу применимости не повторяем. Первоисточник: [ZeroPointRepo/youtube-skills @ 4f7994b94e7d5e250c3b51102d609992e04d5d0d](https://github.com/ZeroPointRepo/youtube-skills/tree/4f7994b94e7d5e250c3b51102d609992e04d5d0d), MIT, опубликованные `README.md`, `skills/`, `clawhub/` и authentication guides. Это **пакет инструкций**, не опубликованный научный эксперимент или собственный YouTube transcript backend.

## Method / source

Исходный полный Git-репозиторий зафиксирован по HEAD, вместо маркетингового excerpt изучены **все 60 Markdown-файлов** в двух namespaces: 12 `skills/*/SKILL.md`, 12 `clawhub/*/SKILL.md`, 24 `references/auth-setup.md`, 12 `skills/*/references/curl-examples.md`. Проверен проектный README с заявленным маршрутом выполнения, frontmatter навыков, исходные примеры HTTP и инструкции по получению API-ключа.

**Конкретные места:** [`skills/youtube-full/SKILL.md:1–38`](https://github.com/ZeroPointRepo/youtube-skills/blob/4f7994b94e7d5e250c3b51102d609992e04d5d0d/skills/youtube-full/SKILL.md#L1-L38) требует `TRANSCRIPT_API_KEY`, Bearer Authorization, явный `User-Agent` и обращение к `https://transcriptapi.com/api/v2/youtube/...`. [`skills/youtube-full/references/auth-setup.md`](https://github.com/ZeroPointRepo/youtube-skills/blob/4f7994b94e7d5e250c3b51102d609992e04d5d0d/skills/youtube-full/references/auth-setup.md) описывает две ветви: пользователь приносит секрет или агент предлагает создать аккаунт, получить OTP, вызвать registration/verification endpoints и *постоянно сохранить* ключ в среде агента. Она также предписывает временно сохранять ответы с токеном в файле, избегать вывода токена и очистить временные файлы. Это описание действий из **неисполненного** документа — не подтверждение работы сервиса или секретного хранилища.

## Independent bounded experiment and oracle

[Проверка всех pinned оригинальных файлов](../../experiments/youtube-skills/2026-11-07-pinned-provider-boundary.py) и [машинный manifest с SHA](../../data/results/youtube-skills/2026-11-07-provider-boundary.json) созданы из `git ls-files` с нулём сетевых вызовов. Отдельный [Python-оракул](../../experiments/youtube-skills/2026-11-07-provider-boundary-oracle.py) заново перечитывает **все 24 source files и 24 auth guides по SHA**, independently сверяет Git pin, собственное перечисление tracked Markdown, структуру frontmatter, ключ, endpoints и обещанную persistent-key ветвь; две намеренные подмены входного текста (удаление имени env переменной и инструкции persist) отвергнуты. [Результаты оракула](../../data/results/youtube-skills/2026-11-07-provider-boundary-oracle.json).

| Проверяемое утверждение | Измерено в pinned исходнике |
| --- | ---: |
| Публичные навыки: canonical названия в двух namespaces | **12 + 12 = 24** |
| `SKILL.md` с внешним TranscriptAPI v2 и `TRANSCRIPT_API_KEY` | **24/24** |
| Auth guides с веткой registration + OTP verification + persistent key storage | **24/24** |
| Уникальные SHA всех `auth-setup.md` | **1** на 24 копии |
| `curl-examples.md` для основного `skills/` | **12/12** |
| Исполняемые исходники собственного backend в этих каталогах | **0**, все 60 files — Markdown |
| Контрольные подмены секретного контракта | **2/2** отвергнуты |
| Реально созданные аккаунты / прочитанные API-ключи / внешние API вызовы | **0 / 0 / 0** |

**Что доказано:** пакет представляет собой 24 варианта инструкций и делегирует получение данных внешнему сервису; тот же текст авторизации повторяется в обеих поставках. Вся доступность, цены, задержки, точность, полнота транскрипций, YouTube ToS, текущая схема API и защита ключа на сервере **не измерялись**.

**Важное условие безопасности:** если агент буквально следует auth instructions, он может запросить секрет у пользователя, инициировать регистрацию и записать ключ в долговременную среду. Это требует *отдельного разрешения пользователя*, безопасного secret store, whitelist домена/операций, запрета логирования Bearer и изоляции от untrusted tool text. Это **эксплуатационный риск дизайна инструкций**, а не обнаруженная уязвимость или совершённая утечка. Мы не исполняли ни регистрацию, ни `npx` установки, ни `curl` к сервису.

## Ограничения и applicability к 45 PROJECT.md

Сохраняется ранее выполненная [матрица source → projects](2026-11-04.md), актуальный `Artemedi/project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`. Нет доказанного нового source seam ни у одного target; допущения по продуктовым возможностям не повышены.

| Работа | Проект | Обоснование | Минимальный следующий тест | Доказательный статус |
| --- | --- | --- | --- | --- |
| YouTube Skills | `agent-skills` | Распространяемые Markdown skills могут быть добавлены как внешний источник данных; есть централизованный авторский auth guide, но не интеграционный контракт | Offline validator для skill schema/permissions; отдельное формальное разрешение на установку и секреты; read-only mock TranscriptAPI, failure/timeout/denial oracle | `DOCUMENTARY_SOURCE_VERIFIED / NO_FIT_UPGRADE` |
| YouTube Skills | `HermesAgent` | Frontmatter содержит Hermes metadata, авторский README заявляет установку, но совместимость на текущем target SHA не исполнена | Изолированная dummy-копия профиля без настоящего ключа, тест секретов/отказов и лимитов трафика; не писать в реальный профиль | `PROFILE_MATCH / RUNTIME_NOT_RUN` |
| YouTube Skills | `TelegramBot` | Возможность транскрипций из ссылок является тематической, не гарантированной API реализацией на target | Синтетические YouTube URLs + подложный TranscriptAPI response, защищённые авторизационные границы, latency/IO/storage, проверка согласия владельца | `PROFILE_MATCH / NEEDS_EVIDENCE` |

Trade-offs: библиотека навыков лёгкая по размеру/зависимостям (60 Markdown файлов, 0 backend modules), но делает агента зависимым от стороннего провайдера, API-ключа, квот и сети, добавляет задержку внешних запросов, риск дополнительного хранения пользовательских транскриптов и сложность эксплуатации секретов. По фактическим CPU/RAM/IO или качеству ответов **нет измерений**, поскольку API не вызывался. Отсутствие собственного backend не означает, что чужой backend непригоден.

**Итог:** `ACCEPT_BOUNDED_SOURCE_STRUCTURE_AND_AUTH_BOUNDARY`; `BLOCKED_EXTERNAL_PROVIDER_NOT_TESTED`; `NO_NEW_FIT`; `NO_PRODUCTION_APPROVAL`. Имеющийся исторический review корректен в своих границах; улучшена независимость доказательства конкретной структуры. Повторять этот static audit без изменения source SHA не нужно.
