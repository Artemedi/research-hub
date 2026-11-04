# BK-029 — 0-CODE: автономный цикл, состояние и границы фильтра

Проверено 2026-11-04: [0-SOFT/0-CODE @47f6a81724e87ff5e916f0eb146516d801a8fb28](https://github.com/0-SOFT/0-CODE/tree/47f6a81724e87ff5e916f0eb146516d801a8fb28), v2.1.1, MIT; этот HEAD от 19.10.2026 новее Telegram-закладки 28.09. Рассмотрены инструкции, исходные механизмы supervisor, state, hooks, budget, safety и тесты по этим границам. Это source review выбранных контрактов, не исчерпывающий аудит всех адаптеров, миграций и внешних инструментов.

## Механика и ограничения

0-CODE задаёт автономный цикл с файловыми документами проекта и контрольной информацией, журналом, hooks и отдельным supervisor для Codex/OpenCode. По README итерационный и денежный лимиты по умолчанию opt-in; проверка затрат зависит от данных соответствующего backend. [Supervisor](https://github.com/0-SOFT/0-CODE/blob/47f6a81724e87ff5e916f0eb146516d801a8fb28/core/supervisor.mjs#L348) при заданном денежном cap для Codex останавливается с `unsupported_budget`, не выдавая видимость работающего лимита. В `loop-limits.mjs` защитный backstop Claude stop-hook равен 100000 и не заменяет явный лимит итераций. Реальное поведение, стоимость и продолжительность цикла `NOT_RUN`.

[core/safety.mjs](https://github.com/0-SOFT/0-CODE/blob/47f6a81724e87ff5e916f0eb146516d801a8fb28/core/safety.mjs#L1) прямо описывает узкий намеренный фильтр; среди сознательно исключённых им классов — `git reset --hard` и `kubectl delete`. Он анализирует строки, а не произвольную вычисляемую shell-программу. Отсутствие запрета в этой функции само по себе не доказывает, что реальный backend разрешит действие: политики хоста, hook mode и другие ограничения требуют отдельного испытания. Установка, миграция, внешние сервисы, системные операции и полный агентный цикл не запускались.

## Изолированная проверка

В `bwrap --unshare-all`, сеть отключена, source readonly, временный HOME/TMP: upstream `node --test tests/unit/safety.test.mjs tests/unit/acceptance.test.mjs` — **49/49** на Node v22.23.2. Это только два набора unit-тестов, не весь upstream suite и не тест реальной защиты системы. Кроме того, [fixture](../experiments/bk029-zero-code/guard-fixture.mjs) передал строковые примеры непосредственно `destructiveReason`: `git reset --hard` и `kubectl delete deployment example` → `null`; `git push --force` → причина. Ни одна из этих команд не выполнялась. Проявленное поведение согласуется с явно описанной границей фильтра, а не объявляется универсальным обходом всех защит.

```sh
bwrap --unshare-all --die-with-parent --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /path/to/node /node --ro-bind /path/to/pinned-source /source --ro-bind "$PWD/experiments/bk029-zero-code/guard-fixture.mjs" /fixture.mjs --tmpfs /tmp --proc /proc --dev /dev --setenv HOME /tmp --setenv TMPDIR /tmp --chdir /source /node --input-type=module -e 'import "/fixture.mjs"'
```

Для авторских тестов заменить финальную команду на `/node --test tests/unit/safety.test.mjs tests/unit/acceptance.test.mjs` с теми же readonly mounts. Fixture `LAB_VERIFIED` только для строковой классификации; full integration и downstream результат `NOT_RUN`.

## Портфель и дальнейшая проверка

Просмотрены все 45 профилей `project-registry@3894522b9c9e785b0f97a8f8d27ddbd4455c79d1`; таблица — исследования, не рекомендации установки.

| Проект | Обоснованная точка сравнения | Риск и следующий тест | Статус |
| --- | --- | --- | --- |
| `agent-config` | [hook rules @489e074](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/hooks/harness.hooks.json#L1) задают защиту путей и операций; сравнить состав политик и ложные решения. | Сравнение на синтетических командах и файлах, без изменения настроек или запуска команд. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| `wiki-tasks` | [recovery doctrine @84cf79d](https://github.com/Artemedi/wiki-tasks/blob/84cf79d73c19/README.md#L5): JSONL state, append-only journal и восстановление. | Две модели состояния нельзя смешивать без изучения порядка записи, отказов и replay; синтетический crash/recovery oracle. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| `dsh-runtime` | [continuation benchmark @b6a1635](https://github.com/Artemedi/dsh-runtime/blob/b6a1635b1200071754e2871b9d9453368e6daf23/benchmarks/agent-continuation/README.md#L5) даёт контекст для сравнения resume и затрат. | Не переносить hooks и не заменять собственные state/events; сначала определить сериализацию, baseline и совместимость. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |

`Harness`, `dsh`, `HermesAgent` и `agent-skills` остаются условными темами без доказанного отдельного интерфейса для этого source snapshot; другие профили не дают более предметного случая. Минимальный A/B: зафиксировать target SHA, фиксированные синтетические события, независимый oracle состояния и последовательности, имитация прерываний и повторной доставки, negative controls опасных строк, минимум несколько повторов; измерять correctness, потери/повторы, p95, CPU/RAM/IO и стоимость. До готового набора и baseline `BLOCKED: MEASUREMENT_MISSING`. Нужны отдельные решения о любом запуске чужих CLI, paid LLM и production; интеграций не было.
