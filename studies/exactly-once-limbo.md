# Where Does Exactly-Once Live? / LIMBO

**Primary source:** https://arxiv.org/abs/2609.29095

**Topic:** `RELIABILITY`. **Previously recorded evidence:** `FULL_TEXT_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-28-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-28-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
Complete 23-page arXiv PDF, including setup, theorems, Tables 3–6 and limitations

### Reported results and limitations
25,930 **synthetic fault-injection** episodes with nine models/three harnesses. Client-side read-back cannot solve in-flight/late commit or redelivery with a key-less non-idempotent write. Keys-everywhere cut duplicate write rate 28% → 4% in studied conditions; a wrapper can help only when the actual service contract supports idempotency.

### DSH-specific research disposition
**ACCEPT REQUIREMENT / P1 COVERAGE AUDIT**. Inventory per-tool effect identity, logical operation correlation, key support and ambiguous-outcome retry. Confirm in actual pinned code and tests; propose a disposable service-level fault fixture before code changes. Durable session evidence is NOT exactly-once external execution. No generic new transaction framework.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [TelegramBot](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/03-automations/TelegramBot/PROJECT.md), [HermesAgent](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/HermesAgent/PROJECT.md). Причина: Неопределённость результата внешней записи и дубли после retry, не SQL atomicity. [Cross-project matrix](../portfolio/historical/project-fit.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.


## 2026-11-04 — cross-project experiment: LIMBO × TelegramBot

**Целевой проект вне DSH/Wiki_PG:** [Artemedi/TelegramBot@b47c527](https://github.com/Artemedi/TelegramBot/tree/b47c527d40d0e7b0aa5311677eca9e8a14fd1b9e). [**Полный lab report**](../reviews/exactly-once-limbo/2026-11-04.md), [исполняемый воспроизводимый replay](../experiments/2026-11-04-limbo-telegrambot-send-retry.py), [JSON results](../data/results/exactly-once-limbo/2026-11-04.json). Авторский [jaxblack/limbo-bench@2db09fb](https://github.com/jaxblack/limbo-bench/tree/2db09fba22a0572a70639162a808906409f612a8) был непосредственно исполнен.

**Почему этот target:** реальный `main.py:187-204` делает HTTP POST `sendMessage`, а `main.main` помечает `seen_videos.txt` и `post_state.json` **только после** возврата `send_telegram`; отдельный GitHub Actions `Save state` коммитит результат после исполнения. Сервис Telegram не декларирует контракт `idempotency_key`, поэтому надежность не исправить одной добавленной строкой со случайным ключом.

**Собственный эксперимент:** 9 классов сбоя × 20 независимых fake video IDs = **180 вызовов двух последовательных запусков настоящего TelegramBot.main**, с полностью подменённым `urllib.request.urlopen` и fake ledger. **120/180** synthetic scenarios с дублем из-за заданных commit-after-timeout/500, delayed commit, redelivery, abrupt process crash или непереданного state. Это **не** измеренная частота ошибок в реальном Telegram. `timeout_pre` и `timeout_post` имели одинаковую локальную картину ошибки и файлов, но скрытый ledger отличался: 0 против 1 совершённого эффекта.

**Подтверждение авторским кодом:** `limbo.World`/`ToolRuntime` исполнены для 20 семян × 3 fault types × 2 contracts: 60/60 дублей для model platform `x` **без ключей**, 0/60 для `mastodon` **со стабильным поддерживаемым ключом**. Это две *симулированные* сети из LIMBO, **не** эквивалент Telegram API. Upstream original tests **65/65 PASS**, Python compile/Ruff, альтернативный объём теста 63 cases и oracle mutation control — PASS.

**Решение:** `AMBIGUOUS_EFFECT_REAL_CODE_REPRODUCED / NO_SERVER_KEYS / NO_PRODUCTION_APPROVAL`. Кандидат: долговременный outbox с логическим ключом, `READY | SENDING | SENT(message_id) | UNCERTAIN`; при неизвестном исходе *не* выполнять немедленный повторный POST, а передавать в manual reconciliation. Это at-most-once на клиенте и может **пропустить** сообщение после `timeout_pre`, то есть нельзя заявлять exactly-once. Любая правка исходников TelegramBot — отдельный approval/branch после согласования судьбы `UNCERTAIN`.
