# agent-risk — project fit

**Дата оценки:** 2026-11-09
**Private registry snapshot:** `Artemedi/project-registry@421268e5c60fd1b5f37bd69a84b923ff28ce3e86`
**Покрытие:** прочитаны все 45 актуальных `PROJECT.md`. Частный текст, исходники и внутренние сведения карточек в публичный репозиторий не копировались.
**Scope:** profile-level assessment only; target source repositories и runtime не проверялись.

| Study | Project ID | Profile-level fit | Source-level seam | Ограничение / следующий gate |
|---|---|---|---|---|
| agent-risk | `dsh-runtime` | **SHORTLIST / PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE** — профиль описывает основной agent runtime и измерительный контур; pre-change replay тематически релевантен изменениям runtime/gate. | `NOT_EVALUATED` | Проверить pinned current source, durable per-step log и полный restorable snapshot; затем 20–40 offline trajectories, log-only vs full rerun vs targeted replay, independent oracle и A1/A2/T negative controls. |
| agent-risk | `agent-config` | **SHORTLIST / PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE** — профиль конфигурационного и hook/review слоя допускает применение метода к оценке изменений policy/config до включения. | `NOT_EVALUATED` | Проверить current hooks, persistency review evidence и точку принятия решения; отдельно измерить false allow/deny, стоимость и regressions на синтетических policy changes. |
| agent-risk | `HermesAgent` | **DEFERRED / NO_DIRECT_REPLAY_SEAM_IN_PROFILE** — профильный контекст близок к работающей агентной конфигурации, но не показывает прямой replay/snapshot approval boundary. | `NOT_EVALUATED` | Вернуться только при обнаружении durable episode logs, restorable execution state и pre-change decision gate. |

**Сводка 45 профилей:** 2 SHORTLIST, 1 DEFERRED, 42 без прямого профильного соответствия для текущего метода, 0 NOT_EVALUATED на уровне чтения профилей. Это не означает, что 42 проекта вообще не могут использовать идеи paper; они лишь не вошли в обоснованный shortlist этой работы.

## Решение

`PROJECT_PROFILE_MATCH / NEEDS_CURRENT_CODE` для `dsh-runtime` и `agent-config`. `DEFERRED` для `HermesAgent`. У всех трёх source-level seam остаётся `NOT_EVALUATED`; ни один target repo не был прочитан в этой итерации. Это не implementation recommendation и не production approval.

Новые private backlinks не добавлялись: существующие связи уже отражают profile-level связь, а новые source-level основания пока отсутствуют. Private registry не изменялся.
