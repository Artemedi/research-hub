# Mass research screening (source-grounded ZCode micro-swarm)

This directory contains an experimental **advisory screening** pipeline for
the 31 studies with open source/evidence gaps in the 2026-11-07 portfolio snapshot.
It is deliberately separate from the canonical dated scientific reviews.

The pipeline is designed around **many independent logical source tasks and one
physical ZCode executor**. A central GPT reviewer independently evaluates the
results. Structured completion or agreement between LLM roles is not scientific
replication, validated project fit, nor approval to deploy.

## Source inputs and outputs

1. Run source-packs.py against a locally available research-hub checkout,
   the existing source-audit.json, coverage.json and source-heads.json.
   The script retrieves only public primary source HTML and pinned public
   GitHub README/source/test files, producing local source excerpts and hashes.
   It never sends private project-registry cards to any model.
2. Run micro-swarm.py only with the owner-authorized local ZCode wrapper.
   No tools are exposed to the model. Only short public source excerpts
   and existing public project shortlist identifiers are in prompts.
   The script is single-worker, uses bounded timeouts, bounded retries and
   a circuit breaker, and checkpoints after every study.
3. Run audit-micro.py to check saved excerpt hashes, anchor existence and model output scoping; this is not semantic verification.
4. Run report-micro.py to convert the saved checkpoint into an auditable
   Markdown overview and redacted source-anchor metadata for 31 studies.
5. Optionally run cluster-critics.py after the 31-study checkpoint has finished. The five critic roles are untrusted advisory reviews; failures must be retained.
6. Run publish-cluster.py to write only aggregated critique status and the separate five-group review, without full source text.

Example commands on an **authorized local machine**:

    export RESEARCH_HUB_ROOT=/path/to/research-hub
    export SWARM_WORK=/path/to/private-audit-work
    export ZCODE_WRAPPER=/path/to/authorized-zcode-subagent
    python3 -B experiments/research-portfolio/source-packs.py
    python3 -B experiments/research-portfolio/micro-swarm.py
    python3 -B experiments/research-portfolio/report-micro.py \
      --work "$SWARM_WORK" --repo "$RESEARCH_HUB_ROOT"

Requirements: Python 3, requests, BeautifulSoup/lxml, the official gh
CLI for optional public GitHub tree metadata, Node.js and an already
authenticated *owner-controlled* ZCode wrapper. Never commit session
credentials, hidden authorizations, raw private documents or downloaded full
paper/source excerpts. The model is a third-party service and receives only
public material from source-packs.

## Evidence boundaries

- Machine-readable full HTML/PDF and exact excerpt hashes **do not** imply
  that Methods, Results and Limitations were independently reviewed.
- A pinned source path and excerpt do not mean the repository was built,
  its tests passed, or its present implementation matches the project profile.
- The public registry's existing shortlist is an input, not a newly
  independently approved fit. Unreviewed source-project pairs remain
  NOT_EVALUATED; absence is not proof of NO_FIT.
- Provider HTTP 429, timeouts, invalid/incomplete JSON and schema mismatches
  remain BLOCKED with exact counts. Never treat them as successful reviews.
- Scientific efficacy, code-level acceptance and production deployment
  require separate source reading, independent oracle/A-B and human gates.

The 2026-11-07 output is in portfolio/2026-11-07/mass-swarm-review.md
and data/results/research-portfolio/2026-11-07-mass-swarm.json.
Local source packs and raw provider failures are intentionally not published.

Offline repository verification remains:

    node scripts/build-catalog.mjs
    node scripts/check.mjs
    node --test scripts/check.test.mjs scripts/entity-model.test.mjs scripts/document-assessment.test.mjs
    git diff --check

Do not invoke the ZCode executor from routine repository tests or CI.
