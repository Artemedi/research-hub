# agent-risk — replay assumptions and targeted continuation

**Дата:** 2026-11-09
**Источник:** [arXiv:2610.16280 v1](https://arxiv.org/pdf/2610.16280v1), 43 страницы.
**SHA-256 PDF:** `2b6b107ed057dbfe7b7133143fe1bd7beef1178700b22bbc7af23caac204d21e` — совпадает с ранее зафиксированным v1.
**Companion code:** [yzhao062/agent-risk@a1ab24aaf3c1e5bfbe47a24eaf4cf411bf0b3f1b](https://github.com/yzhao062/agent-risk/tree/a1ab24aaf3c1e5bfbe47a24eaf4cf411bf0b3f1b), BSD-2-Clause.
**Предыдущий полный разбор:** [full-text review 2026-11-03](../../studies/agent-risk.md). Эта запись — ограниченный follow-up, не замена предыдущего полного обзора.

## Область проверки

Повторно прочитан полный легальный PDF v1, включая Sections 2–4, Limitations, Ethical Considerations и экспериментальные приложения D–H. Проверены формулировки assumptions, denominators и companion implementation для stopping/retry replay. Цель этой итерации — проверить границы переноса targeted replay, а не повторять авторские model runs.

## Метод и авторские результаты

Авторы формализуют изменение агента через execution, loss, logging и admissible changes. Для replay важны:

- **(R)** обе политики детерминированы на объявленных входах, а полный лог содержит входы/seed, нужные для воспроизведения решения до first deviation;
- **(A1) invariance** — не заменённые kernels, serving и environment остаются теми же;
- **(A2) no anticipation** — агент не узнаёт о смене gate до момента, когда она должна повлиять на действие;
- **(A3) stop valuation** — стоимость и post-stop loss задаются явно, но не выводятся из самого лога;
- для продолжающихся ветвей нужны support/logging conditions **(G1–G4)** либо saved-state rerun; **(T)** требует, чтобы восстановленный state, agent context и оставшиеся бюджеты давали live continuation law.

Алгоритм делит траектории на agreement, stop и continue. Первые две ветви могут быть определены логом и объявленной stop valuation при достаточном per-step evidence. Continue после отказа или новой модели не наблюдается в pass-all логе; его нужно покрывать support, bounded uncertainty или targeted execution из snapshot.

**Авторские результаты (не наши измерения):** paper сообщает 16 runs и около 49 000 episodes. В двух-gate демонстрации один pass-all log содержит 7 200 units; два retry gate впервые блокируют соответственно примерно 14% и 41%. Для gate 1 авторский targeted replay дал (P(harm)=0.279) против live (0.288); для gate 2 — (0.158) против (0.165). Авторы сообщают согласие в заранее зарегистрированном margin ±0.015. Log-only outer bounds оставались широкими: [0.244, 0.345] и [0.100, 0.451]. Эти числа относятся к авторским harness, задачам и протоколу; они не переносятся на наши runtime автоматически.

Для stopping gate отсутствие per-step harm ухудшало сертифицируемый harm ceiling: в одном held-out примере 0.159 вместо 0.064. Для model release replay совпал с 0 из 99 logged episodes; авторы оставляют такой случай без оценки loss до получения support/bounds/new runs. Объявление gate изменило abort rate и нарушило no-anticipation assumption.

## Ограничения первоисточника

- Идентификационные результаты относятся к конечным path spaces; sampling guarantees требуют независимых episodes.
- Демонстрации используют honest agents из ограниченного семейства open-weight моделей, bash sandbox и airline-booking environment; это не широкая проверка adversarial или oversight-aware agents.
- Restoration checks подтверждали file-tree/context checks, но не полную эквивалентность всех внешних процессов и скрытого состояния.
- A3 объявляется deployer'ом; авторы отдельно отмечают, что stop valuation не подтверждает harm после остановки.
- Для model release старые логи не помогли, когда новый model не воспроизвёл ни одного из 99 эпизодов.
- При announced gate наблюдалось расхождение; обобщённая оценка поведения агента, распознающего oversight, остаётся открытой.
- Результаты по harm зависят от frozen mechanical checker и заданной loss policy; near-saturated task failure в bash setting ограничивает интерпретацию.

## Code review — companion implementation

Pinned upstream HEAD: `a1ab24aaf3c1e5bfbe47a24eaf4cf411bf0b3f1b`.

Проверены `src/agent_risk/episode.py`, `stopping.py`, `retry.py`, `certify.py`, `tests/test_episode.py`, `tests/test_certify.py` и карта finite checks.

- `Episode` хранит per-step harm как трёхзначное значение `True/False/None`; `harm_before(sigma)` не включает шаг first deviation.
- `replay_stop` останавливает до исполнения первого score строго выше threshold; harm после этой границы не переносится назад. Post-stop harm задаётся отдельной `StopValuation`.
- `retry_harm_bounds` считает harm до первого block нижней границей, а все continuing episodes без достаточного исхода — верхней; его plug-in interval сам по себе не является confidence interval.
- Retry cap не сужает log-only outer interval для cap ≥ 1: continuation после отказа отсутствует в baseline log.

Upstream unit suite (Python 3.14.8): **147 passed, 2 skipped, 0 failed**. Отдельный author finite-check suite: **15/15 PASS** (621.9 s). Эти проверки подтверждают только код и конечные формальные fixtures автора, не реальные agent trajectories.

## Независимый synthetic lab

Скрипт: [2026-11-09-replay-boundary.py](../../experiments/agent-risk/2026-11-09-replay-boundary.py). Результат: [JSON](../../data/results/agent-risk/2026-11-09-replay-boundary.json).

**200** детерминированных synthetic episodes, horizon 6, threshold 0.8:

| Метрика | Результат |
|---|---:|
| Первое отклонение / blocked | 171 |
| Agreement без отклонения | 29 |
| Log-only outer bounds | [0.135, 0.890] |
| Full live oracle harm | 0.665 |
| Targeted replay harm | 0.665 |
| Targeted vs live mismatches | 0 / 171 |
| Live proposal calls | 1 200 |
| Targeted continuation calls (prefix log cost excluded) | 600 |
| Synthetic targeted/live call ratio | 0.50 |

Negative controls намеренно нарушали предпосылки: неполный snapshot state дал 24/171 несовпадений; announced gate — 34/171; изменённый environment kernel — 127/171. Два лога с одинаковым coarse episode-level harm flag, но harm по разные стороны stop, дали разные stopping replay outcomes.

**SYNTHETIC LAB: PASS**

Это конечная проверка контракта с независимым full-from-zero live loop и targeted continuation path. Она не исполняла LLM, shell, database, авторский harness или реальные логи. Call count — число синтетических proposal steps, не tokens/latency/cost. Это не научная репликация авторских 16 runs / 49 000 episodes.

## Применимость к проектам

Матрица 45 профилей на текущем private registry HEAD опубликована отдельно: [project-fit](../../portfolio/2026-11-09/agent-risk-project-fit.md). Кандидаты остаются profile-level; source-level integration seam не подтверждён. Ни один target project repository в этой итерации не изменялся и не проходил source review.

## Вердикт и следующий gate

- **AUTHOR_REPORTED:** результаты paper приняты как авторские, не как наши.
- **SOURCE_REVIEWED:** полный v1 и ограниченный companion code review выполнены.
- **UPSTREAM_TESTS:** 147 passed, 2 skipped; finite checks — отдельный результат в evidence JSON.
- **SYNTHETIC_LAB:** PASS только для указанного deterministic fixture и negative controls.
- **AUTHOR EXPERIMENT REPRODUCTION:** `NOT_REPRODUCED`.
- **PROJECT BENEFIT:** `NEEDS_CURRENT_CODE / NEEDS_EVIDENCE`.
- **PRODUCTION APPROVAL:** отсутствует.

Следующий минимальный проектный gate — только после отдельного разрешения владельца: проверить pinned current source/HEAD выбранного target, наличие durable per-step log и полноценного restorable snapshot, затем сравнить log-only / full rerun / targeted replay на 20–40 новых synthetic trajectories с independent oracle и A1/A2/T negative controls. До этого — никаких runtime изменений.
