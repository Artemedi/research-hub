# BK-053 — Yahont CE: retrieval, ACL и лицензии

Проверено 04.11.2026: [pipedude/yahont-ce @367b48da9de2d296f905aca4bf0eb384043bf643](https://github.com/pipedude/yahont-ce/tree/367b48da9de2d296f905aca4bf0eb384043bf643), v0.4.0; HEAD на момент проверки совпал со снимком, commit 04.11 позднее Telegram-закладки. Проект основан на Onyx. Просмотрены README, архитектура поисковых фильтров, ключевые access/index contracts, выборка тестов и лицензии. Исходников много: это направленный source review retrieval/ACL/licensing, не полный security audit или подтверждение развёртывания.

## Лицензия и область продукта

Корневой [LICENSE](https://github.com/pipedude/yahont-ce/blob/367b48da9de2d296f905aca4bf0eb384043bf643/LICENSE) — MIT, однако [web/src/ee/LICENSE](https://github.com/pipedude/yahont-ce/blob/367b48da9de2d296f905aca4bf0eb384043bf643/web/src/ee/LICENSE) и [web/src/app/ee/LICENSE](https://github.com/pipedude/yahont-ce/blob/367b48da9de2d296f905aca4bf0eb384043bf643/web/src/app/ee/LICENSE) содержат отдельную Onyx Enterprise License. README прямо разделяет эти области и перечисляет отсутствующие в CE enterprise-возможности, включая группы и синхронизацию прав. Это не юридическое заключение о конкретной сборке, транзитивных пакетах или лицензиях моделей: их необходимо разбирать отдельно до использования.

README заявляет гибридный поиск и ссылки на документы, локальные и облачные модели и интеграции. [FILTER_SEMANTICS](https://github.com/pipedude/yahont-ce/blob/367b48da9de2d296f905aca4bf0eb384043bf643/backend/onyx/document_index/FILTER_SEMANTICS.md) описывает сочетание visibility, tenant, ACL и knowledge-scope filters в OpenSearch; несколько типов knowledge scope объединяются OR внутри группы при AND с ACL. [access.py](https://github.com/pipedude/yahont-ce/blob/367b48da9de2d296f905aca4bf0eb384043bf643/backend/onyx/access/access.py) формирует ACL пользователя и публичных документов, но runtime, другие backends и полнота действительного исполнения этих ограничений не проверялись. Не предполагать, что самохостинг автоматически означает отсутствие исходящей сети: конкретные провайдеры и connectors настраиваются отдельно.

## Изолированный helper test

[Оригинальный helper](https://github.com/pipedude/yahont-ce/blob/367b48da9de2d296f905aca4bf0eb384043bf643/backend/onyx/document_index/opensearch/string_filtering.py) удаляет символы вне ограниченного набора из ID. Наш [fixture](../experiments/bk053-yahont/id-fixture.py), bwrap без сети и с readonly source, на искусственных строках получил `a/b → ab` и `ab → ab`; `doc_1` сохраняется, строка только из удаляемых символов отклоняется. Функция сама по себе не инъективна. Это **не** доказательство перезаписи документа, утечки ACL или коллизии индекса: полный путь формирования идентификатора и backend не запускались. Для проверки влияния нужны тесты конкретного call path, namespace и документа с независимым oracle. Upstream suite, развёртывание, retrieval/ACL и реальные данные `NOT_RUN`.

```sh
bwrap --unshare-all --die-with-parent --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /path/to/source/backend/onyx/document_index/opensearch/string_filtering.py /source.py --ro-bind "$PWD/experiments/bk053-yahont/id-fixture.py" /fixture.py --tmpfs /tmp --proc /proc --dev /dev --setenv HOME /tmp --chdir /tmp /usr/bin/python3 -B /fixture.py /source.py
```

`LAB_VERIFIED` относится только к pure helper; безопасность и качество системы не квалифицированы.

## 45 проектных профилей и план

Проверен `project-registry@98ae503a24dd42f7d5a9dcdef916cb6808c239b0`.

| Проект | Гипотеза | Ограничение / следующий тест | Статус |
| --- | --- | --- | --- |
| `Wiki_PG` | [read MCP/evidence слой @cd1ff7a](https://github.com/Artemedi/Wiki_PG/blob/cd1ff7a5171eb8d9fc6381d2b3bc1560cbc2087d/docs/universal-system-mcp.md#L11): сравнение локального retrieval по материалам PG. | Нужны held-out вопросы, ACL oracle, источники и точность citations, данные не переносились. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| `dsh-team-context` | [knowledge plane @373ba69](https://github.com/Artemedi/dsh-team-context/blob/373ba695512052753b1a9eb2183bac30ea795016/docs/architecture.md#L53): сравнение индексации и локального retrieval. | Контракты хранения и происхождения, различие CE/EE и зависимости до любой интеграции. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |
| `MyWiki` | Профиль подтверждает локальный Markdown corpus для поиска. | Только synthetic или отдельно разрешённый corpus; приватность и выгода ещё не измерены. | `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE` |

`HermesAgent` и `hermes-akuz-agents` остались условными: профиль сам по себе не подтверждает подходящий retrieval contract или безопасный доступ к корпусу. Остальные не имеют более предметного сценария. A/B план: pinned source и baseline, искусственный corpus с public/private/tenant-separated документами и конфликтующими ID, oracle access и цитат, held-out questions и negative controls, recall/precision, leakage=0, p95, CPU/RAM/IO/storage и стоимость внешних моделей, лицензии, rollback. Никакого реального corpus, production или сетевого LLM; до данных `BLOCKED: MEASUREMENT_MISSING`.
