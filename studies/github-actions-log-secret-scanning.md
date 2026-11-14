# GitHub Actions workflow-log secret scanning — public preview

[Структурированная запись и связи](../catalog/studies/github-actions-log-secret-scanning.md)

- Первоисточник: [GitHub Changelog 2026-11-09](https://github.blog/changelog/2026-11-09-secret-scanning-detects-secrets-in-github-actions-workflow-logs/) и [официальная документация](https://docs.github.com/en/enterprise-cloud@latest/code-security/concepts/secret-security/secret-scanning). FULL_TEXT_VERIFIED (engineering documentation; не peer-reviewed paper).
- Механизм: после завершения новых workflow runs GitHub ищет поддерживаемые provider-pattern secrets в логах; находки попадают в alerts и сохраняются после удаления логов.
- Ограничения: только GitHub Enterprise Cloud с Secret Protection или Advanced Security; выключено по умолчанию; нет backfill, generic/custom/AI patterns и masked secrets; нет уведомлений в preview. Независимых benchmark-метрик нет.
- PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE: [TelegramBot](https://github.com/Artemedi/project-registry/blob/421268e5c60fd1b5f37bd69a84b923ff28ce3e86/projects/03-automations/TelegramBot/PROJECT.md). Workflow использует secrets: [TelegramBot@5033f9b:.github/workflows/digest.yml:36-46](https://github.com/Artemedi/TelegramBot/blob/5033f9b4aee584cdfdf27308f2430420545750cc/.github/workflows/digest.yml#L36-L46). Это exposure surface, НЕ подтверждение утечки. Доступность enterprise-функции для репозитория UNKNOWN.
- Минимальный A/B: только после проверки entitlement, в отдельном disposable repo, безопасный документированный тестовый токен; A — baseline alerts, B — preview scanner, проверка обнаружения/ложных срабатываний/задержки, ноль действующих секретов и ноль production runs. При отсутствии entitlement: BLOCKED; не подменять тест локальным regex.
- Ценность 5/10 при наличии entitlement, иначе 1/10; сложность 2/10 при наличии entitlement, иначе BLOCKED.
- Вердикт: CONDITIONAL_ENGINEERING_CANDIDATE / PROJECT_PROFILE_MATCH / NEEDS_EVIDENCE. [Недельная матрица](../reports/2026-11-11-portfolio-research.md).
