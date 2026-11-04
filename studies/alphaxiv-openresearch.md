# BK-014 — alphaXiv OpenResearch (local-first research agent harness)

**Type:** full open-source engineering implementation, not a peer-reviewed paper.
**Telegram bookmark:** `BK-014`, 2026-09-16.
**Official primary source:** [alphaXiv/OpenResearch](https://github.com/alphaXiv/OpenResearch), [architecture](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/arc/experiments.md), [storage/egress](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/arc/storage.md).
**Pinned revision:** `23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d` (2026-11-04 UTC), `Cargo.toml` version `0.2.24`, MIT.
**Detailed independent source review:** [2026-11-04-bk014-openresearch-review.md](../reports/2026-11-04-bk014-openresearch-review.md).

## Engineering claim and evidence

OpenResearch creates independent Git-based experiment branches, archives the exact commit by SHA256 and links local SQLite WAL records, run status, logs and artifacts to the source state. The actual implementation in [`src/compute.rs:24–75`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/compute.rs#L24-L75) and [`src/local/experiments.rs`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/local/experiments.rs) was read; no benchmark or end-to-end execution performed.

**Critical source limitation:** [`orx paper --full` does NOT extract full text for PubMed, OpenAlex or bioRxiv](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/commands/paper.rs#L1-L17); alphaXiv extracted text is not independently validated for figures, methodology and supplementary materials. **Never grant `FULL_TEXT_VERIFIED` from article metadata or abstract alone.**

**Trust boundary:** [`src/local/localrun.rs`](https://github.com/alphaXiv/OpenResearch/blob/23a4d67bb5ce3cf9051f8d62b2cd52e93116e16d/src/local/localrun.rs#L50-L127) executes arbitrary committed project run commands using the host's own execution environment. Local-first does not mean outbound-free: alphaXiv/OpenAlex queries, user-chosen model providers, remote compute and official-release opt-out telemetry may generate network traffic. Remote dashboard is not application-authenticated for other local users. No live-agent or host installer was run during review.

## Project mapping and verdict

**Strongest verified profile fit:** `dsh-paper2agent` (standalone Python research-to-project tool with Podman experimental execution and source/input hashing). Source pin: [`Artemedi/dsh-paper2agent@6d82a421`](https://github.com/Artemedi/dsh-paper2agent/tree/6d82a42175a71d3327b773df88f1da0707efe43c), [`src/paper2project/execution.py:308–318`](https://github.com/Artemedi/dsh-paper2agent/blob/6d82a42175a71d3327b773df88f1da0707efe43c/src/paper2project/execution.py#L308-L318). Existing sandbox is **stricter** than ordinary orx local run. Only consider provenance/tree ideas, not wholesale executor replacement.

`paper2agent-index` is a derived Stage-3 index, **not** a runner; `research-hub` is the archive of this review, not an additional project ID. All 45 project profiles were screened; no other backlinks.

**State:** `SOURCE_REVIEWED / PROJECT_PROFILE_MATCH / VERIFIED_SOURCE_SEAM / NEEDS_EVIDENCE / LAB_NOT_RUN / NO_PRODUCTION_APPROVAL`. **Value 6/10, complexity 7/10.** Next gate: owner-approved isolated offline A/B comparing existing Python Podman runner against a content-addressed Git snapshot variant with deterministic independent oracle, resource/IO/cost measurements and explicit full-text coverage guards.

**No project source changes, installs, external code execution or experiment runs.**
