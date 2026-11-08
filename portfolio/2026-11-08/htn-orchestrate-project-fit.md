# HTN-Orchestrate — project fit

**Registry snapshot:** Artemedi/project-registry@421268e5c60fd1b5f37bd69a84b923ff28ce3e86. Прочитаны все 45 текущих PROJECT.md; digest набора 220d181737e91bb15b8ee371fd08889be1e19a81fa56d8b7c217d5a78f4ecc73. Private card text и индивидуальные hashes не публикуются.

| Исследование | Целевой проект | Основание по профилю | Проверенный implementation seam | Следующий минимальный тест | Статус |
| --- | --- | --- | --- | --- | --- |
| HTN-Orchestrate | dsh-runtime | Agent loop, tool orchestration, continuation/reliability — профильные области для hierarchical task decomposition. | Не проверен; конкретный source:line и baseline не подтверждены. | Held-out A/B: single agent vs fixed DAG vs HTN на 20–50 зависимых задачах, independent oracle, latency/tokens/cost и dependency violations. | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |
| HTN-Orchestrate | hermes-akuz-agents | Multi-agent orchestration и DBA handoff соответствуют теме исследования. | Не проверен; профиль описывает преимущественно документацию, tests/CI и runtime seam не подтверждены. | Сначала подтвердить реальный runtime seam и минимальный offline runner; затем тот же held-out A/B. | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |

Остальные 43 профиля прошли профильный triage; более прямого соответствия не найдено. Это не source-level NO_FIT для всех возможных будущих сценариев. Ни исходники dsh-runtime/Hermes, ни production не изменялись. Существующие private backlinks уже присутствуют; новых не добавляли.
