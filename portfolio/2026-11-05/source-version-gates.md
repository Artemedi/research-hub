# Research Hub — source-version provenance и невыполненные gates

**Дата записи:** 2026-11-05 (Riga). **Предыдущие публикации:** [первый аудит](evidence-coverage.md) · [закрытие 51 научного полного текста](full-text-closure.md). Основной `research-hub` на начало работы: `e506f86e1e44712ebdffac5f7a716e72513ecae3`; `project-registry` прочитан на `838b86a28fcaa3440eeddbe147b6188e0d177963`. Исторические карточки и assessments не правились.

## Дополнительные проверенные источники

| Study | Новая отдельно документированная версия | Статус и граница |
| --- | --- | --- |
| [Cursor token efficiency](../../reviews/cursor-token-efficiency/2026-11-05-primary.md) | [официальный инженерный материал](https://cursor.com/blog/improved-token-efficiency), HTML SHA-256 `b3acfeaf56c9f2100b212ad1b28c0cffc2340a1f915fd85dba0b7c222fc81466` | Полный технический текст прочитан; `FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED / AUTHOR_REPORTED / NOT_RUN`. HTML hash — **снимок ответа**, не вечная ревизия публикации |
| [Anthropic agent automations](../../studies/anthropic-agent-automations.md) | [оригинальная статья от 08.10.2026](https://claude.dev/blog/building-effective-agent-automations/), HTML SHA-256 `968c4c5a26cd0056035a998aa2fec6586fe159cc55cb2dbf90cbe885307027ae`; существовавший code SHA `8ef47d719eba5379ff8f38133f5defcc499e856f` не заменён | Добавлено происхождение ответа сайта без нового утверждения о запуске hosted workflow; уже существующий `FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED` не переоценён |
| [Sequential Diagnosis](../../studies/sequential-diagnosis-language-models.md) | [авторская PDF-версия](https://erichorvitz.com/sequential_diagnosis_LM.pdf) SHA-256 `92b8989852d2bb4218f7e9d208cb6c29fd74d139803623f98b50feaa569135fa` | PDF **не** тождественна издательской Science edition; это provenance, а не новая клиническая валидация. `CLINICAL_REVIEW_PENDING` неизменен |

Для каждого добавлена **новая** Version запись. Все восемнадцать прежних исторических `ref:null` сохранены с пояснениями; **16 из 18 исследований с исторической неопределённостью** теперь имеют отдельную проверенную версию или наблюдаемый контент-снимок. Различать *pin артефакта* (PDF SHA), *контент-снимок HTML* (может меняться вместе со страницей) и *git tag/SHA* (версия кода).

## Два остаточных пробела идентичности версии

| Источник | Доказательная категория | Что неизвестно | Условие снятия |
| --- | --- | --- | --- |
| [Unreal Agent BK-025](../../studies/unreal-agent-bk025.md) | `FULL_TEXT_UNAVAILABLE` | Не доступен полный исходный ролик [YouTube](https://www.youtube.com/watch?v=eFBSlgXG3U0) или авторизованный транскрипт; нет исходной проверяемой версии | Легальный доступ к исходному видео/полному transcript именно этого ID. Не переносить маркетинговые тезисы из другой статьи |
| [CVE-2026-82533](../../studies/cve-2026-82533-technical-disclosure.md) | `FULL_PRIMARY_TECHNICAL_DISCLOSURE_READ / NO_CODE_REPRODUCTION` | Официальная OX [статья](https://www.ox.security/blog/cve-2026-82533-deepseek-harness-ai-agent-sandbox-escape/) от 08.09.2026 открывается поисковым индексом, но прямой HTTP на Bazzite дал 403: **не удалось** получить immutable content hash или tag самой публикации | Читаемый первичный документ с зафиксированной ревизией/доказуемым snapshot либо официальный versioned advisory. Публикация 08.09 сама по себе не доказывает неизменность текста |

## Четыре Telegram-пункта с внешними блокерами

| BK | Проверено повторно | Статус в ledger | Condition / gate |
| --- | --- | --- | --- |
| BK-025 | `yt-dlp --list-subs`: YouTube требует sign-in; исходный transcript отсутствует | `ожидает проверки / FULL_TEXT_UNAVAILABLE` | Доступ к полной исходной записи. Никаких выводов о методе или цене без неё |
| BK-034 | `yt-dlp --list-subs`: тот же sign-in blocker. [Glasp](https://glasp.co/youtube/qLfSDQ5NGh0) даёт пересказ и начало transcript, но **не проверенную полную запись** | `ожидает проверки / VIDEO_FULL_TEXT_UNAVAILABLE_RELATED_REPO_REVIEWED` | Полный transcript данного видео и независимые evidence для описанной loop-конфигурации. Репозиторий AutoResearch уже рассмотрен отдельно |
| BK-041 | Официальный Inspektor Gadget код/версия ранее проверены. В исходном протоколе unprivileged `BPF_MAP_CREATE` завершился `EPERM`; привилегированных eBPF трасс нет | `ожидает проверки / BPF_PERMISSION_GATE_VERIFIED_TRACING_BLOCKED` | Явное разрешение владельца на sudo/eBPF и отдельное изолированное измерение; никаких попыток обхода доступа |
| BK-064 | [официальная страница](https://cdn.deepseek.com/harness/dsh-creator-mode-prompt-collection-en.html) HTTP200, содержит примеры промптов; наличие страницы ≠ измеренный переносимый протокол | `ожидает проверки / NOT_YET_VALIDATED` | Frozen test matrix на собственных non-production fixtures и независимый oracle, без paid LLM и без изменения agent harness до owner approval |

**Очередь состоит из реальных незавершённых экспериментальных/доступовых gates, а не 4 потерянных карточек.** Не переводить их в «проверен экспериментально» по факту чтения чужого пересказа или исходников.

## Остальное доказательное покрытие

- `51/51` papers имеют датированную запись полнотекстовой проверки в модели; авторские результаты не были заново воспроизведены.
- Инженерные источники по текущим Review: `24 PARTIAL_SOURCE_REVIEW`, `3 FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED`, `0 HISTORICAL_REVIEW_RECORDED` (всего 27). Для Cursor новая полная статья заменила историческую запись только как current pointer; история сохранена. Частичный технический scope — **не** автоматическая ошибка регистрации и не разрешение на опасные опыты.
- Отдельно 4 paper bounded-code эксперимента стали дополнительно полнотекстово рассмотрены, не теряя прежней области lab; новая научная запись не значит новую лабораторную.
- `450` исторических Assessment и `360` current pointers не изменены. Привязка к 45 проектам остаётся предварительной, пока не подтверждены source seam и project-specific baseline/результат.
- Не изменялись исходники проектов, настройки агентов, production SQL, права Linux, тарифные LLM-провайдеры, eBPF, конфигурации деплоя или приватные PROJECT.md.

## Заключительный критерий завершения

Документальный полный научный текст **закрыт**. Все доступные первичные version/content artifacts по найденным источникам **проверены в своих пределах**. Полное закрытие четырёх экспериментальных/digital-access пунктов объективно требует новых доступов и отдельного разрешения или новой измерительной программы. Никакие `FULL_TEXT_UNAVAILABLE`, `NOT_RUN`, `NEEDS_EVIDENCE` и `CLINICAL_REVIEW_PENDING` автоматически не повышены.
