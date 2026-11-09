# P0: frozen-source independent offline trials and remaining evidence gates

Date: **2026-11-10**. Prior [P0 shortlist](2026-11-09/targeted-fit.md): exact 16 pairs, all anchored to original project Git objects. No repo code, deployments, network services, actual databases or personal/clinical data were changed or accessed.

**Decision:** 0 full-integrated A/B accepted; 16 remain BLOCKED_FULL_AB. Three source-function subsystem A/B experiments were actually executed: two passed their limited synthetic safety/recall gate and one treatment was rejected. The rest have a verified source symbol and an explicit missing full-experiment prerequisite, not a fictional PASS or NO_FIT.

## Measured offline comparisons

| Study / target | Frozen data | Baseline | Candidate | Bounded result / full decision |
| --- | --- | --- | --- | --- |
| exactly-once-limbo / TelegramBot | 120 mocked sends (40×3) | 40 duplicates, 0 missing | 0 duplicates, 40 missing | **REJECT** quarantine: missing delivery; BLOCKED_FULL_AB |
| agent-risk / agent-config | 80 exact-line synthetic claims | 20/80 false accept | 0/80 false accept; 30 true positives | **PASS subsystem** citation quality and micro p95; BLOCKED_FULL_AB |
| drag / Wiki_PG | 60 artificial fused ranking queries | Recall@5 270/300, 30 forbidden docs | Recall@5 300/300, 0 forbidden docs | **PASS subsystem** on pure RRF only; BLOCKED_FULL_AB |

Source excerpts were run by AST extraction from pinned Git archives under bubblewrap with the network namespace disabled. All numerics above are synthetic in-process counts, not study-author gains, complete target end-to-end results, observed production incidents or clinical efficacy. Existing Wiki_PG retrieval already has host/curated filtering; adversarial RRF lists do not imply those invalid documents could reach the current full pipeline.

## In-process timing (microseconds, synthetic only)

| Study / target | Baseline p50/p95 | Candidate p50/p95 | p95 ratio |
| --- | --- | --- | --- |
| exactly-once-limbo / TelegramBot | 94.922 / 110.462 | 71.401 / 77.212 | 0.70x |
| agent-risk / agent-config | 0.97 / 1.24 | 0.61 / 0.8 | 0.65x |
| drag / Wiki_PG | 1.996 / 2.85 | 2.15 / 3.0 | 1.05x |

These are one-process synthetic microbenchmarks without model or network latency, not a production SLA or confidence interval across hosts.

## Baseline target tests (no new treatment)

| Repo | Source pin | Offline tests |
| --- | --- | --- |
| agent-config | 489e074ab0da | 33 passed, 0 skipped; PASS_EXISTING_TESTS |
| agent-skills | 163d92846024 | 11 passed, 0 skipped; PASS_EXISTING_TESTS |
| dsh-paper2agent | cbcb1c089b27 | 99 passed, 16 skipped; PASS_EXISTING_TESTS |
| sequential-rca | 13fa0c910c75 | 14 passed, 0 skipped; PASS_EXISTING_TESTS |
| dsh-team-context | b7268d12581b | 3 passed, 0 skipped; source scope isolation already tested |

**Baseline total:** 160 passed, 16 skipped. These are not 160 comparative scientific successes and do not imply any P0 gain.

## Decision per all 16 P0 pairs

| Study | Target | Source-pinned symbol | Subsystem | Full A/B | Unmet prerequisite |
| --- | --- | --- | --- | --- | --- |
| agent-mosaic | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | No output-admission or citation provenance consumer implemented at session-to-response boundary; frozen effect/citation trace and independent full-agent oracle absent. |
| agent-mosaic | dsh-team-context | [src/core/scoped-recall.ts:73](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/scoped-recall.ts#L73) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Original recallScoped already isolates project scope by default (3/3 network-denied baseline tests); no separate Agent Mosaic evidence-propagation treatment or full retrieval/output evaluation is implemented. |
| agent-risk | agent-config | [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103) | PASS_OFFLINE_LINE_BINDING_GUARD | BLOCKED_FULL_AB | Function-level citation oracle improved, but no integrated review-to-policy approval boundary or held-out actual policy-change dataset; line-bound checks alone do not replay risk. |
| agent-risk | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Session prompt symbol does not provide a restorable full agent state, deterministic effect journal or pre-change risk replay; no candidate adapter. |
| drag | Wiki_PG | [Wiki_PG/ingestion/retrieval_service.py:402](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/retrieval_service.py#L402) | PASS_OFFLINE_RANK_SOURCE_GUARD | BLOCKED_FULL_AB | Pure _rrf_fuse rank-source safety probe succeeded, but current retrieve()/select_retrieval_ids already apply host and curated-source policy; no DRAG implementation or frozen Chroma dense/BM25 retrieval corpus was run. |
| exactly-once-limbo | TelegramBot | [main.py:187](https://github.com/Artemedi/TelegramBot/blob/a838ca6671cada5307825d3b5c433ce7083e1e76/main.py#L187) | REJECT_TREATMENT_DELIVERY_REGRESSION | BLOCKED_FULL_AB | One proposed quarantine variant failed joint safety+delivery: zero duplicate messages but 40/120 lost deliveries; Telegram Bot API authoritative UNKNOWN-effect reconciliation/idempotency is not established. |
| harnesssecurity-bench | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | No bounded effect-authorization simulator or adversarial tool-execution oracle at the pinned session prompt; source-symbol pin is not proof of a security gate. |
| htn-orchestrate | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Session prompt entry exists but no integrated hierarchical planner, dependency-checked ticket executor, frozen task DAG or worker-failure oracle. |
| mcp-toolbox-postgres | Wiki_PG | [Wiki_PG/ingestion/mcp_wiki_server.py:391](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/mcp_wiki_server.py#L391) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Current code already exposes get_postgres_setting() with read-only snapshot semantics; no distinct Google MCP Toolbox adapter and no paired numeric fixture comparison against it. |
| novafabric | dsh-runtime | [packages/api/session-controller/src/commands.ts:302](https://github.com/Artemedi/dsh-runtime/blob/3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc/packages/api/session-controller/src/commands.ts#L302) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | No NovaFabric capsule capture/restore integration, immutable side-effect journal or rebooted-session replay oracle is attached to session controller. |
| novafabric | sequential-rca | [src/sequential_rca/review.py:81](https://github.com/Artemedi/sequential-rca/blob/13fa0c910c75d9e3b79c758bcba473a6406e008c/src/sequential_rca/review.py#L81) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Existing 14/14 review tests verify report hashes/attribution but do not exercise a NovaFabric capsule importer or a distinct variant; independent DBA causal judgment is absent. |
| paper2agent | dsh-paper2agent | [src/paper2project/core.py:39](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L39) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Original Paper2Project already implements source import, exact citations and review, and 99 offline tests passed with 16 skips; no new paper-to-tool treatment, held-out benefit evaluation or distinct adapter. |
| poisoned-skills | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Static 11/11 skills tests establish structure only, not behavior when a model interprets malicious SKILL.md; no contained tool consumer or attack oracle. |
| sequential-diagnosis-language-models | TrinMedicalBot | [eval/clinical_review.py:151](https://github.com/Artemedi/TrinMedicalBot/blob/5c32b51e007cf6486482b2aa96c6bce39f5412ac/eval/clinical_review.py#L151) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | No independent qualified clinical reviewers or sealed, approved vignette gold; existing score() is not an expert oracle. No real patient data or unsupervised medical model test authorized. |
| veriharness | agent-skills | [tests/test_skill_contract.py:9](https://github.com/Artemedi/agent-skills/blob/163d928460247d3d40a936504fda8d5d82ae7cc2/tests/test_skill_contract.py#L9) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | 11/11 static skill contract tests pass but they do not execute a reviewer, tool result or VeriHarness evidence verifier; no paired variant. |
| veriharness | dsh-paper2agent | [src/paper2project/core.py:137](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L137) | NOT_EXECUTED_NO_PAIRED_TREATMENT | BLOCKED_FULL_AB | Published clean Paper2Project offline suite passed 99 tests with 16 explicit skips; core citation() already checks owner/document/range/quote, but no distinct VeriHarness treatment or author benefit A/B. |

## Exact next gates

- **agent-mosaic / dsh-runtime:** Build a read-only output-admission probe over pinned session outputs and test 80 bounded prompts with exact independent source spans.
- **agent-mosaic / dsh-team-context:** Design source-span propagation beyond existing recall scope, then freeze project/user knowledge corpus and output-citation oracle.
- **agent-risk / agent-config:** Patch only the pinned review adapter in isolated copy, run 80 blinded policy-change cases, track downstream allow/deny and nonzero false allow.
- **agent-risk / dsh-runtime:** Pin a replayable event-state capsule and a held-out risk-policy oracle for 40 isolated agent trajectories.
- **drag / Wiki_PG:** Compare unchanged retrieval pipeline against a distinct DRAG-style adapter on a frozen authorized 60-query corpus, measure recall, wrong source and p95.
- **exactly-once-limbo / TelegramBot:** Reject blind-retry and naive quarantine as complete solutions; prove server-supported deduplication or an owner-approved reconciliation protocol before any new live delivery.
- **harnesssecurity-bench / dsh-runtime:** Use an isolated effect ledger and 80 authorized/forbidden task pairs; measure actual unauthorized effects under treatment.
- **htn-orchestrate / dsh-runtime:** Implement an isolated non-effecting HTN-vs-fixed-DAG harness for 48 held-out tasks with dependency and resource accounting.
- **mcp-toolbox-postgres / Wiki_PG:** Compare 40 frozen GUC fixtures for the existing Wiki_PG MCP tool and a pinned Toolbox adapter without connecting to production PostgreSQL.
- **novafabric / dsh-runtime:** Build isolated trace/capsule capture with 40 deterministic episodes and 12 tamper/crash controls.
- **novafabric / sequential-rca:** Connect a read-only capsule input to score_review on synthetic traces; compare original report binding against mutated evidence.
- **paper2agent / dsh-paper2agent:** Compare original import/review workflow with an independently justified new method on pinned synthetic papers and code fixtures.
- **poisoned-skills / agent-skills:** Construct an isolated fake tool/effect runner and independently scored poisoned-versus-clean skill corpus before considering enforcement.
- **sequential-diagnosis-language-models / TrinMedicalBot:** Prepare consent-free synthetic vignettes with independent qualified specialist adjudication and clinical safety governance before supervised A/B.
- **veriharness / agent-skills:** Instrument an isolated skill-review consumer and evaluate forged quotes and independent line-level gold across 80 claims.
- **veriharness / dsh-paper2agent:** Run a pinned source-hash and citation false-allow benchmark on a separate proposed verifier; ensure it adds value beyond existing citation().

## Traceability, trade-offs and adoption decision

- [Full 16-row JSON receipt](../data/results/research-portfolio/2026-11-10-p0-outcomes.json).
- [Executed source-level A/B results](../data/results/research-portfolio/2026-11-10-p0-boundary-ab.json); [existing offline suites](../data/results/research-portfolio/2026-11-10-p0-baseline-suites.json); [team-context baseline](../data/results/research-portfolio/2026-11-10-p0-team-scope-baseline.json).
- Repro: offline source archive + SHA → read-only bwrap sandbox → source function + isolated candidate → frozen, prelabelled independent synthetic oracle → all negative controls → receipt. Use scripts in experiments/research-portfolio/p0-20261110/.
- A strict evidence guard and rank filter add code and some latency but prevent local false accepts. This trade-off is not measured at deployment scale; p95 in microseconds from synthetic calls is not a service SLA.
- Candidate quarantine reduces duplicate effects but increases losses. Real external exactly-once delivery requires a validated provider-side idempotency/reconciliation boundary, not a clever local retry loop.
- Source symbol existence (including a prompt() method) is not an implemented adapter. The final verdict intentionally stays BLOCKED; no production or project change was approved.
