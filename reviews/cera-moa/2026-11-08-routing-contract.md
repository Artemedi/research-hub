# CERA-MoA — routing contract и актуальная оценка применимости

**Дата:** 8 ноября 2026. **Scope:** закрытие отсутствующей оценки по актуальным 45 проектным профилям и независимая синтетическая проверка опубликованного правила маршрутизации. Это не новый source version и не повторная полная рецензия.

**Первоисточник:** [CERA-MoA, arXiv:2609.18779v1](https://arxiv.org/html/2609.18779v1), 16 сентября 2026. Полный легальный HTML повторно получен; SHA-256 `13f6536287ff7ebec0a21663f4d21fc61ce05c82d14ab14448f4080bed18bf0f` совпадает с [полным обзором 05.11](2026-11-05-full-text.md). Повторно проверены §3.2–3.4, §4.1–4.6, Appendix B.1–B.2, E.1–E.3 и F. Предыдущий `FULL_TEXT_REVIEWED` остаётся каноническим полным обзором; этот follow-up его не подменяет.

## Метод и авторские результаты

CERA-MoA совместно обучает маршрутизатор и популяцию specialist policies. Для shared-backbone setting авторы используют четыре независимых LoRA-адаптера на общей Qwen3-4B; для heterogeneous setting — три отдельные open-weight модели. Familiarity estimator получает hidden states из двух промежуточных слоёв начального prompt, сравнивает trainable predictor head с frozen target head и вычисляет `f_i(q)=exp(-λ d_i(q))`. Во время обучения приоритет дополнен UCB exploration и исторической entropy; при inference эти добавки выключены. Выбирается минимальный prefix агентов в порядке priority, для которого сумма familiarity scores достигает `τ`; если сумма всей популяции ниже `τ`, активируются все агенты. Обучение использует DAPO/GSPO, LIFO buffers и `G=8` completion rollouts.

Авторский training corpus — 32 000 примеров в четырёх доменах; отдельно указаны ID test splits и шесть OOD benchmarks. Это авторский эксперимент на 4× NVIDIA H200 141 GB, около 500 GB host RAM и 96 CPU cores. Авторы оценивают примерно один H200 GPU-day на 1 000 optimizer steps; конфигурация допускает до 6 000 steps. Полный масштаб здесь не запускался.

**Авторские результаты, не наша репликация:** для Qwen3-4B OOD average CERA-MoA — 72,8 против 71,5 у AT-GRPO; для heterogeneous pool — 71,8 против 69,1. В Table 3 adaptive routing использует 367,77 average tokens против 666,37 у fixed Top-2 (−44,8%), при ID delta −0,1 pp и OOD delta +0,3 pp. Против fixed Top-1 адаптивный режим даёт +1,8 pp ID / +2,7 pp OOD, но требует на 12,9% больше токенов. Router latency 11,87 ms сопоставлена авторами с 1 350,32 ms native generation; отдельная vLLM строка — 154,09 ms при batch 32, тогда как router измерен при batch 1. Поэтому отношение 7,7% между этими двумя строками нельзя трактовать как парное overhead-измерение.

## Ограничения и воспроизводимость

- Familiarity оценивается по исходному prompt; авторы прямо ограничивают текущую конструкцию single-turn / fixed-trajectory и оставляют step-wise multi-turn adaptation будущей работой.
- Для open-ended code generation текущая схема обычно возвращает ответ одного наиболее familiar expert, а не синтезирует несколько решений.
- Сумма familiarity — routing score, не калиброванная вероятность правильности ответа и не гарантия качества.
- В полном HTML не найдено ссылки на авторский training-code repository или опубликованный checkpoint. Перечислены версии библиотек и инфраструктура, но этого недостаточно для закреплённого независимого запуска.
- Авторские таблицы, latency и GPU-day остаются `AUTHOR_REPORTED / NOT_REPRODUCED`; арифметическая сверка табличных чисел не подтверждает исходные benchmark measurements.

## Независимая проверка

**Synthetic routing-contract lab:** 10 000 детерминированных сценариев, seed `20261108`: 7 500 training-like (familiarity + UCB/entropy priority) и 2 500 inference-like (priority=familiarity), с N=3/4 и `τ` 0,5–0,9. Familiarity строилась из синтетических расстояний в допустимом диапазоне, а не из model hidden states. Проверены prefix ordering, минимальность prefix, пороговая сумма, stable ties и fallback на всю популяцию. **3 645/10 000** синтетических случаев ушли в all-agent fallback; это характеристика fixture, не оценка авторской системы. Независимый oracle регенерировал сценарии другой реализацией правила; SHA-256 digest совпал, **10 000/10 000** проверок пройдены.

Отдельно пересчитана арифметика опубликованных таблиц: Qwen OOD mean 72,7833 (округляется до 72,8), heterogeneous OOD mean 71,8333 (71,8), token reduction против Top-2 44,8099% (44,8%). Это `AUTHOR_TABLE_ARITHMETIC_CHECK`, не независимый benchmark.

Артефакты: [synthetic implementation](../../experiments/cera-moa/2026-11-08-routing-contract.py), [independent oracle](../../experiments/cera-moa/2026-11-08-independent-oracle.py), [raw result](../../data/results/cera-moa/2026-11-08-routing-contract.json), [oracle result](../../data/results/cera-moa/2026-11-08-independent-oracle.json).

## Project fit

Инвентаризированы все 45 `PROJECT.md` на приватном `project-registry@b3af154278a8724230185cba6b1898a106a4f25a`; содержимое карточек в публичный архив не переносилось. Итог для публично оцениваемой части: **`NO_FIT / NO_CURRENT_TARGET`**, shortlist пуст; 29 профилей — `NO_CURRENT_FIT`, 15 внешних/legacy/reference/index карточек — `REFERENCE_NO_TARGET`, один внешний профиль намеренно `NOT_EVALUATED` из-за ограничения конфиденциальности.

Три ближайших по тематике проекта дополнительно проверены на текущем source HEAD:
- `bitvec-dsh@40cee2f72ff4cb6656d201f88fa63d42dec286f2`: extraction промежуточных hidden states и обучение bridge действительно присутствуют (`bridge/bridge/extract.py`, `bridge/bridge/train.py`; тесты extraction/training существуют). Но это reader→generator bridge, не популяция LoRA-specialist policies и не CERA router.
- `9router@d15f5bf3289e50bddda8263cddd239d7078e4ef0`: provider/model proxy и fallback; нет доступа к внутренним hidden states и trainable weights opaque API providers.
- `dsh-runtime@b6a1635b1200071754e2871b9d9453368e6daf23`: agent/tool orchestration; в просмотренном tracked source не найдено model-training/hidden-state/LoRA serving seam.

Другие agent/config, DBA, memory, automation, research-tool и .NET профили также не владеют контролируемым trainable inference backend, необходимым для метода. Поэтому ни один из ближайших проектов не повышен до conditional fit. В приватный registry backlinks не добавлялись: для `NO_FIT` это запрещено политикой.

## Решение

- **Source:** `FULL_TEXT_REVIEWED` в обзоре 05.11; текущий follow-up — `PARTIAL_SOURCE_REVIEW`, та же версия и тот же HTML hash.
- **Author results:** `AUTHOR_REPORTED / NOT_REPRODUCED`.
- **Independent lab:** `SYNTHETIC_ROUTING_CONTRACT_PASS` (10 000 сценариев, independent oracle PASS); не научная репликация.
- **Project fit:** `NO_FIT / NO_CURRENT_TARGET` по 44 оценённым профилям; один профиль — `NOT_EVALUATED` из-за ограничения конфиденциальности.
- **Production:** `NO_PRODUCTION_APPROVAL`; никаких target source, production, model weights или registry карточек не меняли.

Возвращаться к предметному A/B имеет смысл только после появления owner-approved self-hosted trainable backend с доступом к hidden states, несколькими LoRA policies и достаточным GPU budget. Тогда минимальный held-out benchmark должен сравнить static routing, fixed Top-1/Top-2 и learned cumulative-threshold routing, отдельно измеряя quality, tokens, active experts, p95 latency и VRAM/GPU-hours.
