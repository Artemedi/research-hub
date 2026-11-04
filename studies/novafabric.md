# NovaFabric — tamper-evident agent run evidence

**Original paper:** https://arxiv.org/abs/2609.12582; [complete PDF](https://arxiv.org/pdf/2609.12582v1).
**Primary version:** arXiv v1; 44 pages. **SHA-256:** `b5a81659602175218aba04bb936c8d689bfd5e021ba94a1ffb3b13bfa1548ca9` (checked 2026-11-03; PDF binary not redistributed).
**Source type:** `AUTHOR_PREPRINT`. **Evidence:** `FULL_TEXT_REVIEWED_2026-11-03 / NOT_INDEPENDENTLY_REPRODUCED`.
**Historical first watch:** [15 Sep 2026](../archive/dsh/knowledge/research/2026-09-15-deepseek-harness-research-watch.md); [non-normative operator dispositions](../archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md). For Random Attention the earlier source is the [chronological archive index](../archive/dsh/knowledge/research/README.md).
**Historical closure:** [scientific review](../reports/2026-11-03-historical-gap-closure-2026-09-03-to-15.md); [research-to-project matrix](../reports/2026-11-03-project-mapping-september-gaps.md).
**Editorial value / disposition:** 7/10; `P2_MINIMAL_REPLAY_BUNDLE_ONLY` (research only, no production authorization).

## Methodology and sample

Self-contained Run Capsules, content hashes, DSSE/in-toto signatures, manifests, evidence bundles and replay modes. Оценка 10 single-machine release-decision scenarios, отдельно 100M-edge lineage queries и 314 Azure VM → one ingest host, но это разные экспериментальные tiers; measured end-to-end event stream в cloud отсутствует.

## Authors results (not local measurements)

Mocked replay не делал новых model calls в 10/10 scenarios, но **полностью завершились только 2/10 tool-using workloads**: tool responses не подменялись, внешние вызовы оставались live. After fixes captured event completeness mean 0,652 ± 0,064 по десяти сценариям, не 100%. Агентная capture overhead CI [−10,5%, +16,9%] включает ноль. На ingest-plane >41k accepted requests все проверенные preserved, но metadata backend schema была пуста в одном эксперименте и это вскрыло непроверенный контракт.

## Limitations / transfer confounders

Author-led preprint, прототипное состояние и несогласованные paths provenance: в полном v1 отозван ранее заявленный запрос parent-child «20/20» из-за отсутствующих данных в capsule. Replay до mock tools нельзя считать deterministic offline workflow; capture completeness неполная; ingest throughput не является throughput event pipeline.

## Smallest discriminating experiment

До криптографии: 20 disposable sessions с captured response streams, immutable evidence manifest и mock tool/LLM providers. Требовать byte-stable derived trace, full completion, coverage=100% для declared event types, искусственную порчу и обнаружение miss; измерить IO, RAM, diff size.

## Project-fit decision

Идентичность и доказательная полнота session replay, RCA evidence, multi-agent transitions. Не создавать новый crypto framework до верификации простого bundle.

**Gate:** `PROJECT_PROFILE_MATCH / NEEDS_CURRENT_SOURCE_CODE`. Owner gate and independent outcome oracle required before any code changes.


## 2026-11-04 — реальная авторская реализация v0.108.0: лабораторная проверка

[**Полный новый протокол**](../reports/2026-11-04-novafabric-real-capsules-replay.md), [исходный лабораторный скрипт](../experiments/2026-11-04-novafabric-real-capsule-lab.py), [отдельный независимый verifier Evidence Bundle](../experiments/2026-11-04-novafabric-independent-bundle-verify.py).

**Обновлённая доступность:** авторский [MSKazemi/novafabric@v0.108.0](https://github.com/MSKazemi/novafabric/tree/v0.108.0) (commit `cc1d71b64b4d1b4c9aa6e4a16a804686514fe667`, Apache-2.0) теперь доступен и **запущен как реальный CLI**. Прочитано и техническое продолжение [arXiv:2610.34594](https://arxiv.org/html/2610.34594): оно не заменяет исторические количественные результаты original paper v1. Эта запись дополняет первоначальную оценку `NEEDS_CURRENT_SOURCE_CODE`.

**Собственные измерения на Python 3.12:** прошли **83 upstream tests, 2 skipped**. Созданы 20 sealed Run Capsules одного synthetic Python-агента; **40/40 `@record.tool` ответов** восстановлены из журнала, 20/20 выходов совпали побайтно; все 20 получили `nova validate` + `nova verify` + pinned-local-CA PASS. Исходные данные были изменены перед replay, новые побочные вызовы tool bodies не произошли.

**Криптография на копиях:** `nova verify` отклоняет 6/6 изменений **подписанного содержимого**, но принимает добавленный файл, **не входящий** в подписанный manifest inventory. Переносимый **Evidence Bundle** (49 files) независимо проверен скриптом без импортов NovaFabric: 48/48 SHA, 4/4 Ed25519 DSSE подписи, Merkle root, member-allowlist, 5/5 негативных контролей.

**Fail-closed имеет узкую границу:** лишний `@record.tool` вызов отвергнут, но простая `Path.write_text` **вне инструментированного инструмента действительно выполняется** во время `mocked replay`. Из авторского исходного протокола нельзя вывести «полный offline replay произвольных действий». Модельные вызовы = 0, реальные DSH trace и MCP/network tools = `NOT_TESTED`. `nova seal init` использует только self-asserted identity без trusted TSA. При экспорте Evidence Bundle было предупреждение **OPA unavailable → NoopEngine**, policy gates не выполнены.

**Решение:** `AUTHOR_IMPLEMENTATION_LAB_VERIFIED / RESEARCH_PRINCIPLE_ONLY_FOR_DSH / NO_PRODUCTION_APPROVAL`. Допустим следующий *узкий* эксперимент с подписанным manifest и независимой проверкой только уже имеющихся test-run evidence. Не создавать новый криптографический framework, не внедрять all-in-one NovaFabric, не объявлять replay sandbox. Требуются подтверждённые capture completeness, target-specific trust anchor, redaction policy и реальные trace-oracle замеры.
