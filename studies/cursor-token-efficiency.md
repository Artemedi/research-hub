# Cursor — Improved Token Efficiency

[Структурированная запись и связи](../catalog/studies/cursor-token-efficiency.md)

**Primary source:** https://cursor.com/blog/improved-token-efficiency

**Topic:** `INFERENCE_EFFICIENCY`. **Previously recorded evidence:** `FULL_ENGINEERING_ARTICLE_REVIEW_RECORDED`.

**Source review:** [DSH historical decision record](../archive/dsh/knowledge/research/2026-09-28-research-review-proposal.md) | [pinned original](https://github.com/Artemedi/dsh/blob/343dc077e3a4f1de0e441116d66a57c9fecff022/knowledge/research/2026-09-28-research-review-proposal.md).

**Verification boundary:** The cited DSH review records examination of its source, not a fresh reread or independent reproduction here. The earlier DSH disposition is historical and applies to DSH research only; it does not authorize adoption in other projects.

## Review evidence preserved from DSH

### Historical full-source basis
Complete first-party engineering article, not a peer-reviewed paper, 23 Sep 2026

### Reported results and limitations
Cursor reports 7% total token-cost reduction on its traffic; reduced static tool definitions, dynamic MCP tool loading, cache-stable prefixes and sparse file numbering. 46.9% reduction refers to tokens in **sessions calling an MCP tool**, not all traffic; 20% cold-cache miss reduction is another distinct metric. Proprietary A/B data are not independently reproducible.

### DSH-specific research disposition
**NEEDS_EVIDENCE / P2 PERFORMANCE BASELINE**. First measure DSH prompt/tool definition tokens, prompt cache hit/miss, tool selection failures, downstream task success and total cost, including extra dynamic discovery calls. Only then test safe on-demand presentation; tool visibility must never alter tool **authorization**. Avoid speculative framework.

## Further cross-project evaluation

- Candidate applicability beyond DSH (2026-11-03): [dsh-runtime](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/dsh-runtime/PROJECT.md), [HermesAgent](https://github.com/Artemedi/project-registry/blob/f1342414ecca7f5b2f708e91e54bc086c879b63d/projects/02-agents-dsh/HermesAgent/PROJECT.md). Причина: Издержки tool schemas, MCP discovery и prompt-prefix cache stability. [Cross-project matrix](../portfolio/historical/project-fit.md). **Profile-only match, not a verified code integration.**
- Actual integration point: `NEEDS_EVIDENCE` pending current target repository @ SHA and precise source lines.
- Recheck full-source version and methods before a fresh cross-project recommendation; separate paper reported results from measured local benefit.
- Approval: `RESEARCH_ONLY`; no production, runtime or permission changes are authorized.

## 2026-11-07 — независимая проверка GPT-6 и ZCode-совет

[Полный отчёт BK-021](../reviews/cursor-token-efficiency/2026-11-07-council-vs-single.md) · [исполняемый синтетический benchmark](../experiments/2026-11-07-bk021-tool-context-proxy.py) · [машинный результат](../data/results/cursor-token-efficiency/2026-11-07-council-vs-single.json).

На полном первоисточнике Cursor и отдельном локальном симуляторе 12 tools/52 шаблона ×5 перестановок static сохраняет 260/260 доступных нужных инструментов, ideal-oracle dynamic — 260/260 с −50,37% символов контекста, наивный keyword dynamic — 220/260 с −50,97% символов. Негативный контроль обнаружил **20 случаев лишнего раскрытия редкого инструмента на отрицательных формулировках**. Это **символы, не реальные модельные токены**, и 5 seeds повторяют одни шаблоны. Авторский production −7% не воспроизведён.

Три GLM-5.3-Flash эксперта ZCode выполнили разрешённые tool calls и подготовили независимые заключения; первый председатель не прошёл лимит инструментов, второй подтвердил основные числа одним независимым аудитом и вынес решение **NO_PRODUCTION_APPROVAL**. GPT-6 нашёл ошибку совета: из усечённого preview он счёл лишь 6 отрицательных примеров вместо 20. Совокупный бюджет 14 ZCode model calls: **41 825 input / 16 778 output токенов, 438,99 сек** включая переделку. Время/токены самого GPT-6 не измерены, поэтому **не доказано**, что рой эффективнее одного агента. Для `dsh-runtime` и `HermesAgent` оставлен только исследовательский кандидат с требованием shadow A/B на реальных инструментах, без правок проектов.
