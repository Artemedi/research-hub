# Decision Geometry — независимая проверка ceiling/mismatch и границы изменений harness

**Дата:** 2026-11-07. Это новая датированная *контрпроверка*, а не переписывание [карточки работы](../../studies/decision-geometry-harness.md). Предыдущий full-text review от 2026-11-03 уже был зафиксирован в [историческом недельном обзоре](../../portfolio/2026-10-27--2026-11-02/review.md). Проверка направлена на оставшийся пробел — воспроизводимый независимый oracle, **не** на повторение пройденного.

**Оригинал:** [Your Policy Is Secretly a Harness: The Decision Geometry of Agent Interfaces](https://arxiv.org/html/2610.37255v2), arXiv:2610.37255 **v2** (28.10.2026). Полный HTML, Sections 2–7, Appendix B–F, включая теоремы и экспериментальные ограничения; локальная длина 648 439 байт, **SHA-256** `5e37b2455cbe94cf1abbf932d28c96e5ee9f9bff18a547c76f1541387a58e4ce`. Этот SHA относится к HTML, а `d678315eba5c30fd26966f6a33ea635b2889391b0d8eacc718f085063cea5319` из исторической карточки — к отдельному оригинальному PDF v2; файлы не должны иметь одинаковый хеш.

**Авторская реализация:** [2020-qqtcg/HRP@c91d859c21f38f10e358091265eea6e571e23e47](https://github.com/2020-qqtcg/HRP/tree/c91d859c21f38f10e358091265eea6e571e23e47), корневая лицензия MIT (проект содержит vendored third-party код с собственными лицензиями). Выполнен *настоящий исходный* [`environment/hrp_miniwob/oracle.py`](https://github.com/2020-qqtcg/HRP/blob/c91d859c21f38f10e358091265eea6e571e23e47/environment/hrp_miniwob/oracle.py), SHA-256 `485f954eddf8b674f842ff7dbb723e17600d755ae47417a93bd9a8e8e565d15d`. Исходный репозиторий в отдельном временном checkout; его код **не изменён**. Собственные скрипты и агрегированные доказательства находятся в этом публичном хабе.

## Суть научного результата и что в нём проверялось

Статья представляет harness как encoder/decode/executor, который изменяет распределение **семантических действий** модели. В KL-regularized управлении регуляризованный return (J) можно выразить как **ceiling (C) минус mismatch (M)**, при одинаковых определениях `reference policy`, reward и коэффициента `tau`. Изменение harness может изменить и доступный максимум, и расхождение замороженной политики. Поэтому **оценка одного frozen checkpoint не измеряет предел интерфейса**.

В MiniWoB++ (§4.2) авторы утверждают, что одна перестановка полей наблюдения при сохранении оптимальных решений снизила успех модели **85,0% → 19,2%**. Для пяти coding-agent harness на Terminal-Bench Lite (§6.3) фиксированный Qwen3.5-9B демонстрировал **47,9–64,1%** task success; teacher-based ceiling и mismatch оценивались по ограниченным состояниям и action categories. Это **авторские**, не воспроизведённые нами benchmark claims. Определение идеального ceiling для реальных открытых action spaces невозможно без аппроксимаций; stronger teacher — **proxy**, а не математический oracle.

В Appendix **D.5** авторы приводят точный двухдействийный контроль: source rewards `(1, 0)`, новый интерфейс rewards `(0, u)`, reference `(0.5, 0.5)`, `tau > 0`. Политика source optimum выбирает первое действие с вероятностью `p = sigmoid(1/tau)`. При **`1 < u < exp(1/tau)`** новый интерфейс имеет **более высокий ceiling**, но **более низкий return для замороженной source policy**. Адаптация к новому optimal policy даёт `C2 > C1`, то есть обращает локальную оценку. Проверяли **этот** строгий случай.

## Эксперимент и полностью независимый от модели oracle

[Прямой запуск авторского решателя + внешний аналитический baseline](../../experiments/decision-geometry-harness/2026-11-07-bandit.py) • [машинные результаты всех 30 случаев](../../data/results/decision-geometry-harness/2026-11-07-bandit.json).

Для пяти `tau` (0.35, 0.5, 0.75, 1.0, 1.25) × шести `u` (0.8, 1.0, 1.2, 1.3, середина интервала `(1+exp(1/tau))/2`, 1.05 × `exp(1/tau)`) выполнены **30 независимых параметрических вычислений**. `gamma=0.8`, задача завершается после одного действия, поэтому discounted continued value нулевой и обозначения однозначны. Вычислены `C1`, `C2`, `J1`, `J2_frozen`, `J2_adapted`, `M2`.

**Независимость вычислений:** авторский `solve()/evaluate()` — один способ; отдельные скалярные `logsumexp`/KL-формулы прямо из Appendix D.5 — второй. Третий [`Decimal`-верификатор](../../experiments/decision-geometry-harness/2026-11-07-bandit-oracle.py) вообще **не импортирует** NumPy и код авторов: пересчитывает 30 строк с 70 десятичными знаками, проверяет все поля, знаки и outcome labels, и отвергает две намеренные подмены — численный `J` и флаг reversal. Дополнительная Monte Carlo проверка выборки `20 000` семантических действий на случай использует 5SE + conservative tolerance, не служит отдельной доказательной базой математического тождества.

| Контроль | Результат | Граница |
| --- | ---: | --- |
| Авторский finite-MDP решатель vs независимые аналитические формулы | **30/30 PASS** | Только one-step bandits, не реальные LLM |
| Случаи «`C2>C1`, но `J2_frozen<J1`» | **15/30** | Сконструированы аналитически, не оценка частоты в мире |
| Переименование **семантических** действий с одновременной перестановкой policy/rewards | **30/30 инвариантны** | Не доказывает инвариантность языковой модели к перестановке текста |
| Monte Carlo vs analytic | **30/30** | Seeded synthetic sampling; нет API/model tokens |
| Недопустимые `tau/reference/next_state/policy` | **5/5 отвергнуты** | Проверка узкого входного контракта |
| Независимый `Decimal` validator | **30/30 PASS, 2/2 мутации обнаружены** | Оракул формул, **не** повторный нейросетевой training run |
| Максимальное `abs` расхождение скалярных формул | **3.56e−15** | Стандартная погрешность floating-point |

[Machine verifier](../../data/results/decision-geometry-harness/2026-11-07-bandit-oracle.json) хранит SHA первичного результата и отдельные negative controls. Авторский код исполнялся в Python 3.12 с NumPy 2.5.1 в локальной доступной исследовательской среде; ни production-процессы, ни личные данные не читались. Не запускались GPU trainer, Terminal-Bench Lite, кодовые агенты, policy gradient и реальная перестановка prompts у LLM.

Таким образом, подтверждено **математическое существование** reversal в условиях статьи. **Не подтверждено**, что реальный prompt/tool schema change в наших репозиториях вызовет похожую деградацию, что новая обучаемая модель улучшит качество, или что возможно контролируемое онлайн-дообучение на коммерческом API. Слова «15 случаев» описывают искусственно выбранную сетку `u,tau`, а не распределение потерь на пользовательских задачах.

## Совет и достоверность независимой контрпроверки

Две роли ZCode (`methods`, `falsifier`) проверяют только публичные краткие выдержки Sections 4–5/Appendix D.5 и агрегированные результаты. [Скрипт](../../experiments/decision-geometry-harness/2026-11-07-council.py) • [протокол каждой роли](../../data/results/decision-geometry-harness/2026-11-07-council.json). Согласие моделей **не** признаётся подтверждением истинности. **Результат двух последовательных запросов: 0/2 COMPLETE, 2/2 BLOCKED_PROVIDER**: роль `methods` вернула `TIMEOUT`, `falsifier` — `NONZERO_EXIT`. Повторных бесконечных попыток нет. Никакого модельного scientific/implementation ACCEPT не получено; независимый численный вердикт ограничен реальным авторским solver и `Decimal`-оракулом. Эти ошибки провайдера не доказывают некорректность статьи или теста.

## Матрица применимости к портфелю

Актуальный [`project-registry@fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6`](https://github.com/Artemedi/project-registry/tree/fc15adabccfcf1e41cb2625f7ecb8d74a9ffc8a6) содержит 45 карточек. Выбраны три наиболее предметные; backlinks на это исследование **уже существуют** в registry, новые не требуются. Публичные ссылки не содержат частных профилей или секретов.

| Исследование | Target project ID | Проверенная граница и профиль | Риски, минимальный offline A/B | Статус |
| --- | --- | --- | --- | --- |
| Decision Geometry | `dsh-runtime` | Исходник [@3feed5d](https://github.com/Artemedi/dsh-runtime/tree/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc); [`packages/core/tools/src/schema.ts:11–21,64–72`](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/core/tools/src/schema.ts#L11-L21) задаёт tool description/annotations/object-property shape. Это реальный контракт подготовки схемы, **не** подтверждённый causal prompt-order эффект. | 60–100 фиксированных synthetics с разным `property` order, annotations, status/tool output formatting, одинаковой model/policy/tools; сериализация, decision equivalence, task correctness, malformed calls, p50/p95, tokens/cost, cold/warm cache, CPU/RAM. Отдельный regression-gate. | `VERIFIED_SOURCE_SEAM / EXPERIMENT_PENDING / NO_FIT_UPGRADE` |
| Decision Geometry | `agent-config` | [@489e074](https://github.com/Artemedi/agent-config/tree/489e074ab0daaadb732673c193047172a3744862), [`claude_templates/harness.CLAUDE.md:6–13`](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/claude_templates/harness.CLAUDE.md#L6-L13) управляет инструкциями и ограничениями; это документированный prompt surface. | Изолированный A/B на 30–50 permission-gated сценариях до/после перестановки *допустимых* секций, где золотой oracle проверяет сохранение запретов и команд. Не устанавливать hooks; не менять реальные профили без approval. | `VERIFIED_DOCUMENTED_PROMPT_SURFACE / EFFECT_UNMEASURED` |
| Decision Geometry | `HermesAgent` | Профиль registry описывает agent orchestration, но конкретный model-facing serializer/tool-schema seam в актуальном checkout **не исследован** этим этапом. | Сначала pinned `repo@SHA:lines`, затем идентичные synthetic tasks с изменением representation, фиксированные ограничения и независимая test harness. До этого не приписывать эффект paper. | `PROFILE_ONLY / NEEDS_SOURCE_SEAM` |

Другие 42 карточки рассмотрены на уровне профиля. Для проекта коллеги `.NET` исходный implementation seam и одинаково проверяемые harness variants не предоставлены; `AUTHOR_STATED/NEEDS_SOURCE_CODE`, **не** выдавать FIT без дополнительных материалов. Для иных reference/DBA/catalog проектов общего слова «AI» недостаточно.

## Трейдоффы и решение

- **Стабильность и качество:** при изменении tool schema/observation order полезно удерживать даже те метаданные, от которых кажется возможным избавиться. Сравнение «старый prompt vs новый prompt на той же LLM» измеряет только *текущую* пригодность; оно **не измеряет ceiling после адаптации**.
- **CPU/RAM/IO/latency:** сам независимый bandit solver лёгкий. Настоящий A/B с LLM inference и особенно с teacher/adaptation потребует намного больше токенов, latency и GPU/RAM; стоимость/эффект на наших проектах **MEASUREMENT_MISSING**.
- **Сложность:** не внедрять теоретический KL estimator или новый общий слой harness в `dsh-runtime`. Начать с regression-fixtures текущих observation schemas и фиксированной проверяемой семантики; YAGNI.
- **Безопасность:** изменение presentation может менять не только качество, но и частоту неверных tool calls. В независимом oracle добавить hard negative controls на permission escalation и unexpected execution.

**Вердикт:** `FULL_SOURCE_AND_AUTHOR_SOLVER_VERIFIED / ACCEPT_BOUNDED_EXACT_BANDIT_THEORY`; `REWORK_REAL_HARNESS_PRESENTATION_AB`; `NO_NEW_PROJECT_FIT`; `NO_PRODUCTION_APPROVAL`. Никакие target project files не изменены. Следующий meaningful gate — сквозной held-out A/B на одном зафиксированном model+tool runtime **без права автономного внедрения** и с измеренными task success, ошибки tool execution, p50/p95 и полными затратами; математическая подстановка сама по себе не делает инструмент готовым.
