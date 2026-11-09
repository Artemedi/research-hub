# P0 research integration: isolated experiment execution and independent gates

**Date:** 2026-11-09. **Source:** 16 P0 pairs in the [targeted matrix](../../data/project-fit/portfolio/2026-11-09-targeted-fit.json).

**Result:** 5 isolated source-level synthetic A/B; 11 blocked by missing target adapter, runtime or oracle. 2 candidates for further review, 2 prototypes rejected, 1 redundant/no measured incremental change. **0 production approvals.**

Source snapshots were Git-archived at pinned commits and original referenced blobs checked byte-for-byte. No private project descriptions, clinical patient data, messages, production databases or target project code changed.

## Every P0 pair: observed effect and decision

| Study | Target | Execution / deployment decision | Measured effect or blocker | Follow-up |
| --- | --- | --- | --- | --- |
| agent-mosaic | dsh-team-context | PILOT_FAIL_COST / **REJECT_CURRENT_PROTOTYPE** | On 60 constructed source-manifest cases, incorrect retrieved source hits 300 -> 0, but 95th-percentile per-call time rose >1.25x; toy manifest not established in runtime. | Optimize source manifest verification and run a real frozen retrieval corpus with independent relevance/authorization oracle and p95. |
| agent-risk | agent-config | PILOT_PASS_CONDITIONAL / **RESEARCH_CANDIDATE_NOT_APPROVED** | Current quote guard: 18/50 false positives; candidate: 0/50; both preserved 30/30 valid claims. Synthetic p95 meets declared 1.25x rule. 10 isolated patched unit tests pass. | Review and test minimal 5-line patch on a separate, truly held-out project review corpus; owner-approved PR only after independent gate. |
| exactly-once-limbo | TelegramBot | PILOT_FAIL_LIVENESS / **REJECT_CURRENT_PROTOTYPE** | On 120 mock sends, duplicate remote effects 60 -> 0, but 90/120 candidate outcomes quarantined as UNKNOWN; no server-side reconciliation. Candidate p95 increased. | Do not deploy until server-side idempotency/reconciliation or human resolution protocol exists, with measured delivery completeness and bounded UNKNOWN recovery. |
| mcp-toolbox-postgres | Wiki_PG | PILOT_NO_INCREMENTAL_GAIN / **NO_CHANGE** | Direct existing GUC reader and existing MCP wrapper both reproduce all 40 valid snapshot values and reject 8 malformed cases; duplicate wrapper showed no accuracy gain and higher p95. | Retain the existing get_postgres_setting contract; revisit only if controlled real-use benchmark proves a missing field/contract. |
| paper2agent | dsh-paper2agent | PILOT_PASS_CONDITIONAL / **RESEARCH_CANDIDATE_NOT_APPROVED** | Original source accepted 3/3 prohibited same-root symlink imports; isolated minimal pre-resolve guard rejected 3/3, preserving 30/30 legitimate source imports and 9 other negative checks. Patched suite 65 pass, 15 skip. | Submit minimal symlink fix with regression test from clean origin/main worktree; independent source review and CI before merge; review ancestor symlink edge cases separately. |
| agent-mosaic | dsh-runtime | BLOCKED_ADAPTER / **BLOCKED** | No outbound claim-source authority guard wired at SessionCommandController.prompt; only source symbol exists. | Build a read-only evidence admission seam, freeze 80 cited claims and an independent source/permission oracle. |
| agent-risk | dsh-runtime | BLOCKED_REPLAY_ORACLE / **BLOCKED** | No immutable per-step tool-effect log with a restorable session and independent replay oracle was established in the pinned source. | Provide 40 deterministic episodes +12 tamper/partial controls and recoverable state before A/B. |
| drag | Wiki_PG | BLOCKED_ENV_AND_ORACLE / **BLOCKED** | Original retrieve() depends on missing isolated chromadb/embedding runtime; no frozen relevant/OOD 60-query quality gold. | Freeze 60 source-labeled retrieval queries, approved embedding/index version and isolated no-network retrieval consumer. |
| harnesssecurity-bench | dsh-runtime | BLOCKED_EFFECT_ORACLE / **BLOCKED** | No actual permission-enforced effect boundary and held-out 80 attack/legitimate trace pairs in the isolated session code. | Pin exact allowed-operation oracle and run 80 malicious/legitimate trace pairs with negative controls. |
| htn-orchestrate | dsh-runtime | BLOCKED_ADAPTER / **BLOCKED** | Session prompt is not an HTN planner, and no project-bound scheduler/dependency result adapter was identified. | Implement narrow dependency-checked planner seam in isolated runner and replay 48 DAG +8 invalid graphs. |
| novafabric | dsh-runtime | BLOCKED_ADAPTER / **BLOCKED** | No own tool-side-effect capsule emitter or restorable replay boundary verified; a prompt symbol is insufficient. | Pin 40 episodes and 12 corrupted capsules, side-effect ledger and independent state-hash oracle. |
| novafabric | sequential-rca | BLOCKED_ADAPTER / **BLOCKED** | score_review has 14 passing archived tests; no NovaFabric capsule intake, independently checked hash chain or 40 matched traces integrated. | Add isolated receipt-consumer adapter and compare 40 real schema traces +12 tampered artifacts. |
| poisoned-skills | agent-skills | BLOCKED_RUNTIME_SEAM / **BLOCKED** | Static skill contract suite is not a runtime tool execution authorization boundary. | Identify real skill-ingest/effect consumer and run 80 attacks without executing untrusted code or network. |
| sequential-diagnosis-language-models | TrinMedicalBot | BLOCKED_CLINICAL_ORACLE / **BLOCKED** | 17 offline tests cover blind-review plumbing, not an expert-adjudicated 60-vignette model comparison; qualified specialist and sealed clinical gold unavailable. | Require independent qualified clinical adjudicators, synthetic no-PHI 60-case gold, critical-risk rule and explicit medical deployment review. |
| veriharness | agent-skills | BLOCKED_ADAPTER / **BLOCKED** | Three static skill tests pass, but no dynamic reviewer/citation admission consumer exists in this repository. | Define exact input/output contract and 80 independently labeled source-span claims; keep plugin execution disabled. |
| veriharness | dsh-paper2agent | BLOCKED_SEMANTIC_ORACLE / **BLOCKED** | Original App.citation validates source-bound line range but not semantic sufficiency; no qualified independent claim-to-context oracle or candidate added. | Supply sealed 80 supported/unsupported claims and an isolated App.review_analysis consumer with independent semantic labels. |

## Exact bounded A/B numeric summary

| Pair | Original baseline | Candidate | p95 ratio | Decision |
| --- | --- | --- | --- | --- |
| agent-mosaic/dsh-team-context | {'cases': 60, 'correct_or_abstain': 0, 'wrong_source_count': 300, 'ood_abstained': 0} | {'cases': 60, 'correct_or_abstain': 60, 'wrong_source_count': 0, 'ood_abstained': 15} | 4.5866× | REJECT_CURRENT_PROTOTYPE |
| agent-risk/agent-config | {'true_positive': 30, 'false_positive': 18, 'false_negative': 0, 'true_negative': 32} | {'true_positive': 30, 'false_positive': 0, 'false_negative': 0, 'true_negative': 50} | 1.0× | RESEARCH_CANDIDATE_NOT_APPROVED |
| exactly-once-limbo/TelegramBot | {'total': 120, 'duplicate_remote_effects': 60, 'remote_commits': 180, 'recorded_success': 120, 'unknown_pending': 0, 'false_recorded_success': 0} | {'total': 120, 'duplicate_remote_effects': 0, 'remote_commits': 90, 'recorded_success': 30, 'unknown_pending': 90, 'false_recorded_success': 0} | 3.2285× | REJECT_CURRENT_PROTOTYPE |
| mcp-toolbox-postgres/Wiki_PG | {'valid_correct': 40, 'invalid_non_ok': 8} | {'valid_correct': 40, 'invalid_non_ok': 8} | 1.6974× | NO_CHANGE |
| paper2agent/dsh-paper2agent | {'valid_accepted': 30, 'invalid_rejected': 9, 'invalid_accepted': 3, 'symlink_accepted': 3, 'snapshots_stable_after_external_edit': 30} | {'valid_accepted': 30, 'invalid_rejected': 12, 'invalid_accepted': 0, 'symlink_accepted': 0, 'snapshots_stable_after_external_edit': 30} | 0.8184× | RESEARCH_CANDIDATE_NOT_APPROVED |

## Evidence receipts and source-level patch proposals

### agent-mosaic/dsh-team-context

Pinned source: [src/core/scoped-recall.ts:73](https://github.com/Artemedi/dsh-team-context/blob/b7268d12581be2705c5e675991126c25f735701a/src/core/scoped-recall.ts#L73), SHA256 of original code blob: ffec7b3fc6ad69a233342c137002bd17a2c91084cb5335e85d64b7c58b9e9189.
- [Evidence or minimal isolated patch](../../data/results/research-portfolio/2026-11-09-p0-agent-mosaic-team-context.json) · sha256 81ff2b61303c4a20ab7595f303bbb2e7e166a2abfabe4a9cc6a178e2b2583d33

### agent-risk/agent-config

Pinned source: [tools/review.py:103](https://github.com/Artemedi/agent-config/blob/489e074ab0daaadb732673c193047172a3744862/tools/review.py#L103), SHA256 of original code blob: 5aa8032a7c56fc6ff1fe050138343a54d8363d1211aa72e7733c153001cfe505.
- [Evidence or minimal isolated patch](../../data/results/research-portfolio/2026-11-09-p0-agent-risk-agent-config.json) · sha256 0b1619b09e71347bda8c08eaf97ada3213adf8d5fcdc763528913090f4a9236f
- [Evidence or minimal isolated patch](../../experiments/research-portfolio/2026-11-09-p0-agentconfig-candidate.patch) · sha256 dd478dc6db54d91a0875ae7b9b11c28373dea5c522ba7cd6df125798d880d9ee

### exactly-once-limbo/TelegramBot

Pinned source: [main.py:187](https://github.com/Artemedi/TelegramBot/blob/a838ca6671cada5307825d3b5c433ce7083e1e76/main.py#L187), SHA256 of original code blob: 96ef4a27fd26def1254a9c69bfb896cd24e1eb175fe11b54f02db7158e3c9de2.
- [Evidence or minimal isolated patch](../../data/results/research-portfolio/2026-11-09-p0-exactly-once-limbo-telegram.json) · sha256 7f35afa016d0038de7e3981aa55d473f1860a6ac1209ce051cbdbbc75d342575

### mcp-toolbox-postgres/Wiki_PG

Pinned source: [Wiki_PG/ingestion/mcp_wiki_server.py:391](https://github.com/Artemedi/Wiki_PG/blob/d55721bb99bff25fae352341cfd630c048693d6b/Wiki_PG/ingestion/mcp_wiki_server.py#L391), SHA256 of original code blob: b15e231087974856bdfcf37b6e710c91f263d82f231a32a18b540659c05d7e6e.
- [Evidence or minimal isolated patch](../../data/results/research-portfolio/2026-11-09-p0-mcp-toolbox-pg.json) · sha256 998e611101baa4c339249289941c0700278396bf11be59a614b12a69c78686df

### paper2agent/dsh-paper2agent

Pinned source: [src/paper2project/core.py:39](https://github.com/Artemedi/dsh-paper2agent/blob/cbcb1c089b2704af70e89e4fd5bb490642c9efae/src/paper2project/core.py#L39), SHA256 of original code blob: 95ea03c7fabbc586ac29e073f16ab5a6e1b5c10b8388f619afec4d3125e6ee79.
- [Evidence or minimal isolated patch](../../data/results/research-portfolio/2026-11-09-p0-paper2project-symlink.json) · sha256 04b9428465af372c755eaec95b7ea28d70a95447807cf062420d8151be8959e7
- [Evidence or minimal isolated patch](../../experiments/research-portfolio/2026-11-09-p0-paper2project-symlink-candidate.patch) · sha256 50a295f0536237464fcac3f3bf2ca39bae6a8f35a94e0a8bab37ab8d2f39550c

## Baseline unit suites and negative controls

Pinned archived target-suite receipts: [read-only network-disabled tests](../../data/results/research-portfolio/2026-11-09-p0-target-snapshot-tests.json). Candidate patch suites: [separate network-disabled execution](../../data/results/research-portfolio/2026-11-09-p0-candidate-unit-suites.json).

Independent numerical check: p0-independent-check.py verifies all outcome classifications, direct fixture labels, source blob SHA, all 16 pairs, five measured receipts and deliberate mutation negatives. This is NOT human model benchmarking or production acceptance.

## Integration and resource trade-offs

- Strict quote checks and pre-resolve symlink guarding have small code footprints and measurable synthetic false-allow reductions; full representative holdouts and target-repo CI are the next gate.
- Source-manifest filtering can remove toy injected results but requires a trustworthy manifest, increases computation and in this run exceeded the originally declared 1.25x p95 budget.
- Quarantining uncertain Telegram outcomes avoids blind duplicate retries but stalls completion; without remote dedupe/reconciliation it cannot promise exactly-once semantics.
- The Wiki_PG GUC MCP tool already exists and is deterministic on synthetic snapshots. Adding another layer under YAGNI is unjustified without evidence of a missing capability.
- The remaining P0 scenarios require project-bound adapters, a stable execution context, actual model outcomes or qualified clinical experts. They remain explicitly blocked.

**Publication is not deployment:** all original target repositories remain unchanged. Existing historical research/project-fit decisions are preserved. No production authorization granted.
