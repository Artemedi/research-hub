# BK-026 — Julia 1: source review и границы вероятностей

Проверено 2026-11-04: [историческая ссылка](https://supersoniclabs.ia.br/julia-1/) перенаправляет на [страницу автора](https://supersoniclabs.ai/julia-1/); официальный [модельный репозиторий @a85b127321d580d65176c89ced8273f305745d85](https://huggingface.co/SupersonicLabs/Julia-1/tree/a85b127321d580d65176c89ced8273f305745d85) и его код, policy, результаты, тесты и документация. HEAD автора при проверке совпадал с этой ревизией. Git LFS указатель перечисляет 577189056 байт, SHA-256 `df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72`: реальные веса не скачивались и их содержимое не проверялось. Apache-2.0 относится к опубликованным артефактам; обучение целиком не раскрыто. Проверка сосредоточена на decision API и routing, не является аудитом всех native kernels или безопасности.

## Устройство и доказательства

`julia/typed.py` преобразует несколько независимых вопросов choice/score/noul в строки, нормирует logits softmax и возвращает исходные вероятности; score — математическое ожидание индекса шкалы. `julia/inference.py` и `julia/router/router.py` используют `display_probabilities`: при победителе >0.95 и остальных <0.045 результат превращается в 1 и 0; иначе малые <0.01 обнуляются и остаток нормируется. Это документированные правила представления, но потребитель не должен трактовать отображаемые 1/0 как сырую уверенность или калиброванную оценку. Typed API отличается и это различие важно для любого threshold gate. `inference-policy.json` содержит `calibration: null`, `replacement_qualified: false`, а 8192 — позиционный предел, не доказательство качества на длинном контексте.

Иерархический Router сужает группы и возвращает область вероятности `final_candidates`; он может выбыть правильный вариант. `strict_encoding` призван отклонять обрезание и инъекцию marker tokens, но эти гарантии в реальном движке нами не исполнялись. У авторов есть CPU и H200 results: 1463/2000 typed и 64/100 Banking77 в H200, 1451/2000 и 60/100 на CPU; 100-элементные пилоты малы, сравнение с Jev использует опубликованный reference, а не новый парный замер. Эти значения `AUTHOR_REPORTED`, не наши замеры. 52-locale MASSIVE оценивает scenario, не intent или slot filling.

## Проверка

На полностью синтетическом вводе выполнен [fixture](../experiments/bk026-julia/display_fixture.py), который непосредственно импортирует только оригинальный `julia/probabilities.py`: 3/3. Изоляция Linux `bwrap --unshare-all`, исходник readonly, временный HOME, без сети. Проверялись `[.955,.044,.001] → [1,0,0]`, контроль `[.951,.049]` и перераспределение значения `.005`. Это `LAB_VERIFIED` только для этой функции, не для инференса или downstream accuracy. Полный upstream suite и веса `NOT_RUN` (torch/transformers отсутствуют; установка чужих исполняемых зависимостей не выполнялась). Воспроизведение, из каталога research-hub, после отдельной загрузки точного исходного снимка в `/path/to/source`:

```sh
bwrap --unshare-all --die-with-parent --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /path/to/source /source --ro-bind "$PWD/experiments/bk026-julia/display_fixture.py" /fixture.py --tmpfs /tmp --proc /proc --dev /dev --setenv HOME /tmp --chdir /tmp /usr/bin/python3 -B /fixture.py /source/julia/probabilities.py
```

## Портфель и возможное применение

Просмотрены 45 профилей `project-registry@fee228810cfddfdc3da3fd247008f7918ed7f018`. Ни один авторский benchmark не доказывает пользу для этих проектов.

| Проект | Конкретная гипотеза и опора | Ограничение и следующий тест | Статус |
| --- | --- | --- | --- |
| `9router` | Исследовать локальное ранжирование уже разрешённых provider/model кандидатов; [контракт allowedCandidates @d15f5bf](https://github.com/Artemedi/9router/blob/d15f5bf3289e50bddda8263cddd239d7078e4ef0/docs/hard-routing-boundary.md#L3) задаёт жёсткий верхний предел, не делегируя полномочия модели. | Offline replay с policy oracle: ни одной попытки вне allowlist, fallback и modalities сохранены; проверить качество, стоимость и p95. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| `dsh-runtime` | Исследовать выбор среди заранее разрешённых маршрутов делегирования; [описанный session policy @b6a1635](https://github.com/Artemedi/dsh-runtime/blob/b6a1635b1200071754e2871b9d9453368e6daf23/.agents/notes/implemented/feature/2026-08-18-model-selected-subagent-routes.md#L11) сохраняет user authorization. | Это гипотеза, не готовая интеграция; отдельно проверить контракт вызова и сохранение ограничений. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |

`sequential-rca` и `TelegramBot` не получили backlinks: профиль сам по себе не подтверждает конкретный пригодный decision dataset и интерфейс. Остальные профили не дают достаточно предметного сценария для данного материала; generic routing сходство недостаточно.

**Минимальный A/B (план, не запуск):** зафиксировать актуальные target SHA и неизменные разрешённые маршруты, независимую разметку task success и policy oracle, стратифицированные анонимные offline cases; baseline текущего выбора против варианта с Julia, перемешивание опций и negative control запрещённого маршрута, многократные повторы и доверительные интервалы. Измерить accuracy, ошибочные отказы, нарушения допуска (ноль), p50/p95, CPU/RAM/IO и полную стоимость. Отдельно согласовать загрузку модели, ресурсы, лицензии, failure fallback и rollback; без данных `BLOCKED: MEASUREMENT_MISSING`. Production не менялся.
