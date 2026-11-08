# Understand Anything — project fit

**Registry snapshot:** Artemedi/project-registry@b3af154278a8724230185cba6b1898a106a4f25a. Прочитаны все 45 PROJECT.md; digest набора профилей 4cb4be95806cc027a52b5608f1c379c26a438473163b323e4f7f572cc1092a4b. Частное содержимое, пути и индивидуальные hashes карточек не публикуются.

| Исследование | Целевой проект | Основание по профилю | Проверенный implementation seam | Следующий минимальный тест | Статус |
| --- | --- | --- | --- | --- | --- |
| Understand Anything MCP / viewer | Harness | Профиль прямо указывает MCP compatibility и integration probes; upstream предоставляет stdio MCP server с graph/status/search/diff tools. | Не проверен: исходники Harness и текущая регистрация MCP клиента не читались. | Disposable stdio MCP client + fake graph; tools/list, status/search/diff, project-root scope, dashboard symlink negative control; latency/RAM и fixed oracle. | PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE |

Остальные 44 профиля прошли профильный triage; более прямого соответствия текущему MCP server не найдено. Это не утверждение о невозможности будущего применения и не source-level NO_FIT. Для Harness source-code fit остаётся NEEDS_EVIDENCE, пока не проверен его актуальный repo@SHA/path и тестовый контракт.

**Риски/ограничения:** viewer на текущем upstream HEAD выдаёт содержимое внешнего файла через graph-listed symlink; до исправления path confinement dashboard не следует подключать к чувствительным project trees. MCP server принимает caller-supplied projectPath без отдельного allowlist. Никакие private source contents не переносились в публичный отчёт.
