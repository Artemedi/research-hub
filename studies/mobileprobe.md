# MobileProbe — trajectory-aware injection testing for Android GUI agents

[Структурированная запись и связи](../catalog/studies/mobileprobe.md)

**Тип:** научная работа; [полная arXiv 2611.16693v1](https://arxiv.org/pdf/2611.16693v1), 12.11.2026; SHA-256 6257113fda476ea1be2afc1bb55f9e0d0102b4ba3343d37c321d68928c724222.

**Маршрут:** Рассмотрен и отложен, NO_CURRENT_MOBILE_AGENT_TARGET. В проектном реестре нет подтверждённого Android/mobile GUI agent, для которого исследовались attack surfaces. Не переносить результат автоматически на браузер, desktop GUI, Telegram-бота или DSH Runtime.

MobileProbe подбирает момент внедрения на траектории Android-агента и адаптирует содержимое экрана в синтетическом тестовом окружении. Авторы сообщают высокий ASR для 83 attack instances на 12 приложениях и трёх mobile agents. Это не реальная частота нападений на наши проекты.

**Ограничения:** симулированные Android устройства, ручные attack goals/oracles, только поддержанные приложения, не всегда достижим выбранный экран. Повторный intake при появлении соответствующего mobile application + доступного sand-boxed target. [Обзор](../reviews/mobileprobe/2026-11-14.md) · [матрица](../portfolio/2026-11-14/review.md).
