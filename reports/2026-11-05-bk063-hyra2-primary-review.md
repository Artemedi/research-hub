# BK-063 — Hyra 2.0: полный инженерный текст найден, реализация не воспроизведена

**Добавлен в карточки как архитектурный reference.** Статус **разобран**, не «проверен экспериментально». [Карточка](../studies/hyra-2.md), [все 45 решений](2026-11-05-bk063-project-triage.json). Это новый факт после [исторического ожидания полного текста](2026-11-04-telegram-bookmarks-reconciliation.md); прежний вывод не переносится молча.

## Первичный материал и воспроизводимость доступа

Полностью прочитан официальный инженерный материал **Hyra 2.0: The Next Step for Auto Research**, Hyra Team, [canonical page](https://hy.tencent.com/research/hyra2), проверено 05.11.2026. Статический HTML не содержал статьи; её собственный публичный frontend получает full content через read-only `POST https://api.hunyuan.tencent.com/api/blog/publicDetail`, JSON `{"id":0,"customUrl":"hyra2"}`. Запрос выполнен без cookies, auth и секретов; `accept-language: en`, `Origin: https://hy.tencent.com`. POST здесь читает публичную публикацию, ничего не публикует.

Ответ `data.detail`: id 100127; full content 34143 символа, SHA-256 UTF-8 content **03c939a9f924c2026e5d4b47da591fe1f223a6a50e71dc3dfbe3d4b96b645688**. Hash включает временные media query strings полученной версии, поэтому будущий ответ может отличаться даже без изменения прозы. Raw response/full copyrighted article не переиздаются. Это content snapshot, **не git SHA реализации**. Название/автор не доказывают дату первой публикации; сохранена Telegram-дата 02.11 как историческая дата записи.

Дополнительно прочитан README [официального results repo](https://github.com/Tencent-Hunyuan/Hyra-results): это набор результирующих artifacts, а не исходники всего orchestrator. Ни модели, ни datasets не скачивались. `FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED`; `SOURCE_IMPLEMENTATION_UNAVAILABLE / NOT_REPRODUCED`. Научные статьи отдельных результатов не считаются автоматически разобранными.

## Что описывает автор

Статья описывает Overall/Mission/Worker роли, persistent task queue и асинхронную доску обсуждений. Завершение задач связывается с code versions, logs и raw traces; отдельный reviewer должен сначала видеть проблему и evidence. Разделены project state, agent memory и reusable Books. В Books различаются observations, independently verified results и human-approved conventions. Существенный compute и публикация shared knowledge требуют человеческого разрешения. Перечисленные модели и научные результаты — заявления авторов, не независимые результаты данного обзора. [Первичный текст](https://hy.tencent.com/research/hyra2).

## Оценка метода и пределы вывода

Полезен не сам набор ролей, а различение **статуса наблюдения и права изменить общий стандарт**. Это позволяет сформулировать проверяемый контракт: отдельный run может сохранить наблюдение, но не присвоить ему независимую верификацию или согласие владельца. Перенос такого принципа — наша гипотеза, а не доказательство действующего enforcement Hyra.

Публикация не даёт полного scheduler/policy implementation, точных prompts, целостных execution traces и доступного end-to-end replay. Поэтому нельзя проверить, что отказ review действительно блокирует promotion, delegated workers не обходят compute gate, а provenance сохраняется при restart/retry. Human approval, описанный в статье, — `AUTHOR_STATED`, не доказанная security boundary. Worker diversity не гарантирует независимость ошибок.

Показанные outputs сами по себе не устанавливают причинную пользу hierarchy/memory/self-improvement. Нужны сопоставимые задания, baseline без предлагаемого механизма, одинаковый compute budget и учёт вмешательств человека, failed runs и отбора удачных примеров. Здесь не оценивались ни benchmark scores, ни биологические/математические заявления outputs. Никакого scientific replication verdict из инженерного описания не следует.

Лицензия article content не трактуется как лицензия orchestrator/model artifacts. Каждый artifact требует отдельной проверки условий и версии. Нет измерений CPU/GPU/VRAM, token cost, p95, reliability или выгоды проектов; самостоятельный shared memory deployment создал бы privacy и permission риски. Отсутствующие числа не заменены оценкой из рекламного текста.

## Исследование → проекты

Все 45 PROJECT.md каталога `Artemedi/project-registry@0e80ec6ecbf52173b899c0cc037a5ee076e2d1b1` учтены в JSON; shortlist — три документальных соответствия. Код всех 44 проектов не аудирован. Brief коллеги рассмотрен как `AUTHOR_STATED / NEEDS_SOURCE_CODE`.

| Исследование | Проект и current pinned contract | Почему подходит / ограничение | Минимальный следующий тест | Evidence |
| --- | --- | --- | --- | --- |
| Hyra 2.0 | [dsh-paper2agent@6d82a42175a71d3327b773df88f1da0707efe43c/docs/product/PIPELINE.md:7](https://github.com/Artemedi/dsh-paper2agent/blob/6d82a42175a71d3327b773df88f1da0707efe43c/docs/product/PIPELINE.md#L7) | Stage artifacts/verdicts и human choice — предмет для сравнения evidence-first review. Документ прямо DESIGN ONLY; существующий automation seam не доказан. | Одинаковые authored dossiers: нынешний review против evidence-first reviewer, слепой oracle по подложным citations и missing evidence. | `VERIFIED_DESIGN_CONTRACT / HYPOTHESIS_BENEFIT` |
| Hyra 2.0 | [dsh-team-context@373ba695512052753b1a9eb2183bac30ea795016/docs/architecture.md:26](https://github.com/Artemedi/dsh-team-context/blob/373ba695512052753b1a9eb2183bac30ea795016/docs/architecture.md#L26) | Knowledge governance и promotion policy; отделены от live runtime. Books taxonomy — возможный reference, не готовая интеграция. | Synthetic observation→verified→convention lifecycle, wrong evidence/unauthorized promotion должны отклоняться. | `VERIFIED_DOCUMENTED_BOUNDARY / NEEDS_MEASUREMENT` |
| Hyra 2.0 | [wiki-tasks@84cf79d73c19d5372bfcd692d9f668f3d430ca1e/README.md:29](https://github.com/Artemedi/wiki-tasks/blob/84cf79d73c19d5372bfcd692d9f668f3d430ca1e/README.md#L29) | Recovery-first task context даёт сценарий provenance после restart; исследовательский scheduler не реализован этой ссылкой. | Authored queue/recovery trace: duplicate completion, stale evidence, replay after restart; baseline current rules. | `VERIFIED_DOCUMENTED_WORKFLOW / HYPOTHESIS_BENEFIT` |

Для DBA, routing, медицинского профиля и reference forks общий «agent» vocabulary недостаточен. DSH runtime/Harness условны: низкоуровневые contracts статьи не опубликованы. Отдельный source review BK-060 не доказывает совместимость с Hyra. Другие knowledge consumers не добавляются механически вместо shortlist.

Ценность 7/10 как governance reference, сложность воспроизведения полной системы 9/10; субъективные приоритеты. **Ни один A/B не запущен.** Сначала три детерминированных replay каждого authored case без моделей/сети; baseline existing rules, independent expected state transitions, ноль ложных promotions и ноль потери provenance. Бюджет предлагаемого local validator: один worker, ≤60 s/run, ≤512 MiB; фактических измерений нет. Model-based comparison потребует отдельного бюджета и human gate, контент проектов не передавать внешним моделям автоматически. До этого `BLOCKED: MEASUREMENT_MISSING`; production изменений нет.
