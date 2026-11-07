# Repository maintenance

Read `RESEARCH_POLICY.md` and `docs/architecture.md` before adding research material. Preserve evidence qualifications, pinned source revisions and the distinction between author claims, local tests and project benefit.

New sources must also follow `docs/data-model.md` and register explicit entities in `catalog/entities.json`. All 81 existing cards are normalized under schema v2; `legacy_studies` is empty and must not receive newly added sources. Project and structured study pages are generated from the same assessments, never edited independently. Preserve supersession and explicit current pointers. Document-backed links require exact source quotes and target-column proof; do not infer FIT from incidental mentions. Preserve source card body hashes; updating scientific analysis requires a reviewed, dated correction rather than silently regenerating its hash.

- One canonical source card: `studies/<source>.md`.
- Dated source reviews: `reviews/<source>/YYYY-MM-DD[-scope].md`.
- Multi-source reviews and project-fit: `portfolio/<period>/`.
- Machine results: `data/results/<source>/`; project-fit: `data/project-fit/<source>/`.
- Collection provenance: `collections/<collection>/`. BK identifiers belong here and in provenance, not as the main source taxonomy.
- New scripts: `experiments/<source>/`. Do not run experiments as part of documentation checks.
- Keep `archive/dsh/` byte-identical. Keep existing experiment code unchanged during documentation-only work.

`reports/` contains generated compatibility endpoints. Do not add new reports there or edit compatibility JSON directly. Edit canonical files and `catalog/structure.json`; new documents use `from: null` and an explicit `date`.

Do not append changelog-style lists to the root README. It links stable section indexes. Generated files begin with a comment naming `scripts/build-catalog.mjs` and must not receive manual additions.

For evidence-gated portfolio swarms and the experimental Claude Swarm → ZCode bridge, use the repository-local skill in `.agents/skills/research-swarm-orchestrator/SKILL.md`. It is a bounded lab workflow, not authorization for unattended or production execution.

After edits:

```sh
node scripts/build-catalog.mjs
node scripts/check.mjs
node --test scripts/check.test.mjs scripts/entity-model.test.mjs scripts/document-assessment.test.mjs
git diff --check
```

Tests must remain offline and use temporary synthetic fixtures. Do not execute user agents, desktop tools, database labs or network experiments to validate repository navigation. Do not change research statuses during structural cleanup.
