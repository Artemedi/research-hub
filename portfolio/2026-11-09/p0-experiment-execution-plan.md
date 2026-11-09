# P0 source-snapshot experimental validation plan — 2026-11-09

Scope: all 16 P0 research/project pairs from data/project-fit/portfolio/2026-11-09-targeted-fit.json, across nine declared protocols. Research-hub only; no target project, private registry, deployment, bot, clinical system or database is modified. Run in separate Git worktree; source-only target copies are immutable Git archive extracts, pinned by full SHA. Where target code cannot be executed offline, preserve the missing gate as BLOCKED instead of inventing successful A/B.

1. Freeze 16 pairs, target SHA, hashes of code and independently generated fixtures, and adoption criteria. Check real target API/offline test availability without installing dependencies or contacting external systems.
2. For feasible pairs, run original-source baseline and minimal experimental candidate in sandbox with no network. Use deterministic held-out cases with independent oracle and negative controls; record original-source scope, candidate code hash, inputs, observations, timings and failures separately. No whole-paper replication is inferred.
3. For infeasible cases (live dsh-runtime session, agent models, clinically qualified adjudication, missing telemetry, absent adapter), mark BLOCKED_ENV, BLOCKED_ORACLE or BLOCKED_ADAPTER and record precise prerequisites. Positive unit/mock does not qualify as deployment approval.
4. Independently check numeric evidence, source pins, receipts and deliberately invalid mutations. Publish per-pair machine ledger and human decision matrix. ADOPT requires real project-bound integrated candidate, representative owned workload, independent oracle, and explicit owner approval; otherwise distinguish RESEARCH_CANDIDATE and REJECT.
5. Verify syntax, repository node scripts/check.mjs, unit tests and git diff; publish PR, require green CI and merge.

Trade-offs: isolated synthetic benchmark is fast and low-memory/IO but has limited ecological validity. True agent/clinical experiments are more costly, require human/qualified review and cannot be inferred from toy tests. No needless abstraction or target code changes.
