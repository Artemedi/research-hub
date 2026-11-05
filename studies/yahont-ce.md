# Yahont CE — поиск и корпоративный контекст

- **Источник:** [pipedude/yahont-ce @367b48da9de2d296f905aca4bf0eb384043bf643](https://github.com/pipedude/yahont-ce/tree/367b48da9de2d296f905aca4bf0eb384043bf643), v0.4.0, Telegram BK-053 / 22.10; source snapshot 04.11 новее закладки.
- **Подход:** производная Onyx, индексация источников и гибридный поиск, локальные или внешние модели, ссылки на документы и внешние действия. Документированные ACL/filters не доказывают корректности развёрнутой конфигурации.
- **Лицензии:** корневой MIT, но `web/src/ee` и `web/src/app/ee` имеют отдельную Onyx Enterprise License; нельзя считать весь снимок единым MIT-кодом. Условия компонентов и конкретной поставки требуют отдельной проверки.
- **Ограниченный тест:** synthetic inputs показали, что helper OpenSearch ID нормализует `a/b` и `ab` в одинаковую строку; эффект на end-to-end индексацию не проверен. Деплой, доступы, качество RAG и реальные данные `NOT_RUN`.
- **Проекты:** `Wiki_PG`, `dsh-team-context`, `MyWiki` — кандидаты для независимого retrieval/ACL сравнения, `PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE`, не рекомендация переноса корпуса. [Обзор](../reviews/yahont-ce/2026-11-04.md), `NO_PRODUCTION_APPROVAL`.
