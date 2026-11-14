# SPILLWAY — separating action target admission from untrusted text sanitization

[Структурированная запись и связи](../catalog/studies/spillway.md)

**Тип:** полная научная работа + Apache-2.0 код; [arXiv 2611.07222v1](https://arxiv.org/pdf/2611.07222v1), 04.11.2026; [upstream code @e4ca913](https://github.com/saintmachines/spillway/tree/e4ca913cf97e7456238d911f00f22f63b7fd108f); PDF 16 страниц, SHA-256 26e3f9b50deb9b5528ea4d61a86f87ceef9e2ef852a3d7bdfec35bb578b3aec4.

**Маршрут:** Добавлен в карточки, P1 для dsh-runtime, безопасность целевого tool-call; PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE.

Метод отделяет детерминированную проверку адресатов/ресурсов действия по user task и типизированным данным от удаления prompt-injection текста на ingress; optional judge имеет ограниченную роль. Авторы наблюдали ноль успешных стандартных атак на **12 заданных AgentDojo cells** (2847 attacked pairs), не универсальную гарантию безопасности. Новая версия библиотеки имеет отличия от настройки paper; её результатам нельзя приписывать прежние цифры без теста.

**Риски:** typed tool result provenance может отсутствовать, легитимный target появиться в untrusted данных, ложные блокировки, конфигурационная зависимость, prompt sanitization не заменяет настоящие permissions. [Обзор](../reviews/spillway/2026-11-14.md) · [матрица](../portfolio/2026-11-14/review.md).
