# Repository maintenance

Read `RESEARCH_POLICY.md` and `docs/architecture.md` before adding research material. Preserve evidence qualifications, pinned source revisions and the distinction between author claims, local tests and project benefit.

New sources must also follow `docs/data-model.md` and register explicit entities in `catalog/entities.json`. The `legacy_studies` list marks existing unconverted cards; do not put newly added sources there. Project and structured study pages are generated from the same assessments, never edited independently. Preserve supersession and explicit current pointers.

- One canonical source card: `studies/<source>.md`.
- Dated source reviews: `reviews/<source>/YYYY-MM-DD[-scope].md`.
- Multi-source reviews and project-fit: `portfolio/<period>/`.
- Machine results: `data/results/<source>/`; project-fit: `data/project-fit/<source>/`.
- Collection provenance: `collections/<collection>/`. BK identifiers belong here and in provenance, not as the main source taxonomy.
- New scripts: `experiments/<source>/`. Do not run experiments as part of documentation checks.
- Keep `archive/dsh/` byte-identical. Keep existing experiment code unchanged during documentation-only work.

`reports/` contains generated compatibility endpoints. Do not add new reports there or edit compatibility JSON directly. Edit canonical files and `catalog/structure.json`; new documents use `from: null` and an explicit `date`.

Do not append changelog-style lists to the root README. It links stable section indexes. Generated files begin with a comment naming `scripts/build-catalog.mjs` and must not receive manual additions.

After edits:

```sh
node scripts/build-catalog.mjs
node scripts/check.mjs
node --test scripts/check.test.mjs scripts/entity-model.test.mjs
git diff --check
```

Tests must remain offline and use temporary synthetic fixtures. Do not execute user agents, desktop tools, database labs or network experiments to validate repository navigation. Do not change research statuses during structural cleanup.
