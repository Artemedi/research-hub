import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateEntities, entityPages } from './entity-model.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const original = JSON.parse(fs.readFileSync(path.join(root, 'catalog/entities.json'), 'utf8'));
function rejects(name, change, pattern) {
  test(name, () => { const m = structuredClone(original); change(m); assert.throws(() => validateEntities(root, m), pattern); });
}
test('pilot data passes with original evidence matrices', () => { assert.equal(validateEntities(root, original), original); });
rejects('primary source cannot disappear', m => { m.studies[0].primary_url = null; }, /primary_url/);
rejects('unknown project ID is rejected', m => { m.assessments[0].project_id = 'missing-project'; }, /unknown projects/);
rejects('duplicate study identity is rejected', m => { m.studies.push(m.studies[0]); }, /duplicate id/);
rejects('current assessment cannot point to history', m => { m.current_assessments[0].assessment_id = 'rea-initial-' + m.current_assessments[0].project_id; }, /superseded/);
rejects('supersession cannot cross projects', m => { m.assessments[45].supersedes = m.assessments[1].id; }, /incompatible supersession/);
rejects('changing imported evidence is rejected', m => { m.assessments[0].evidence = 'VERIFIED'; }, /differs from original/);
rejects('unknown version needs an explanation', m => { const v = m.versions.find(v => v.ref === null); v.unknown_reason = null; }, /unknown reason/);
rejects('unavailable review cannot borrow another study version', m => { m.reviews.find(r => r.id === 'unreal-access').version_ids = ['bench-v1']; }, /missing source version/);
rejects('current pointer cannot be omitted', m => { m.current_assessments.pop(); }, /current pointer missing/);
rejects('removing a complete project history cannot conceal partial import', m => {
  m.assessments = m.assessments.filter(a => a.project_id !== 'AKUZ');
  m.current_assessments = m.current_assessments.filter(a => a.project_id !== 'AKUZ');
}, /incomplete\/duplicate matrix import/);
rejects('project URL cannot identify a different project', m => { m.projects[0].registry_card_url = m.projects[1].registry_card_url; }, /project card identity mismatch/);
test('generated pages display terminal bounded findings distinct from scientific current review', () => {
  const ledger = JSON.parse(fs.readFileSync(path.join(root, 'data/results/research-portfolio/2026-11-09-closure-ledger.json'), 'utf8'));
  const pages = entityPages(original, new Map(ledger.studies.map(row => [row.study_id, row])));
  const blocked = pages.get('catalog/studies/claude-swarm.md');
  assert.ok(blocked.includes('BLOCKED'));
  assert.ok(blocked.includes('WORKTREE_DATA_LOSS_AND_FALSE_COMPLETION'));
  assert.ok(blocked.includes('2026-11-07-claude-swarm-failure-e2e.json'));
  assert.ok(blocked.includes('claude-swarm-review'));
  const unrelated = pages.get('catalog/studies/memscope.md');
  assert.ok(unrelated.includes('ACCEPT_RESEARCH_ONLY'));
  assert.ok(unrelated.includes('memscope-review'));
  const noFit = pages.get('catalog/studies/kvtether.md');
  assert.ok(noFit.includes('OPEN_EVIDENCE_ADJUDICATION'));
  assert.ok(noFit.includes('NO_FIT_RETRACTED_INSUFFICIENT_PROFILE_ORACLE') === false);
  assert.ok(noFit.includes('Obtain independent source-level verification'));
});
test('shared review belongs to both sources without folder-name inference', () => {
  const pages = entityPages(original);
  for (const id of ['rrsi', 'harness2']) assert.ok(pages.get(`catalog/studies/${id}.md`).includes('reviews/rrsi-harness2/2026-11-04.md'));
});
test('typed relation is visible from both ends', () => {
  const pages = entityPages(original);
  assert.ok(pages.get('catalog/studies/rrsi.md').includes('[harness2](harness2.md)'));
  assert.ok(pages.get('catalog/studies/harness2.md').includes('[rrsi](rrsi.md)'));
});
test('project and study views expose the same current decision and limits', () => {
  const a = original.assessments.find(a => a.id === 'rea-current-MyPartyIsGrinding');
  const pages = entityPages(original);
  for (const file of ['catalog/studies/rea.md', 'projects/MyPartyIsGrinding.md']) {
    assert.ok(pages.get(file).includes(a.decision)); assert.ok(pages.get(file).includes(a.evidence));
  }
  assert.ok(pages.get('catalog/studies/unreal-agent.md').includes('NOT_MIGRATED') === false);
  const unreal = original.assessments.find(a => a.id === 'unreal-bk025-20261106-dsh-runtime');
  for (const file of ['catalog/studies/unreal-agent.md', 'projects/dsh-runtime.md']) {
    assert.ok(pages.get(file).includes(unreal.decision)); assert.ok(pages.get(file).includes(unreal.evidence));
  }
});
test('Hyra article hash and coverage are not presented as source-code verification', () => {
  const r = original.reviews.find(r => r.id === 'hyra-2-primary');
  const v = original.versions.find(v => v.id === r.version_ids[0]);
  const matrix = JSON.parse(fs.readFileSync(path.join(root, 'data/project-fit/hyra-2/2026-11-05.json'), 'utf8'));
  assert.equal(r.source_coverage, 'FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED');
  assert.equal(v.ref, 'sha256:' + matrix.source_content_sha256);
  assert.equal(matrix.source_code_sha, null);
});
test('Desktop GUI PASS retains narrow scope and whole-suite limitations', () => {
  const e = original.experiments.find(e => e.id === 'vercel-agent-desktop-wayland-toy-ui');
  const evidence = JSON.parse(fs.readFileSync(path.join(root, 'data/results/vercel-agent-desktop/2026-11-05.json'), 'utf8'));
  assert.equal(e.result, 'PASS');
  assert.equal(evidence.all_gui_runs_passed, true);
  assert.ok(e.scope.includes(`${evidence.gui_cases_passed}/${evidence.gui_cases_passed}`));
  assert.match(e.limitations, /one failure and 233 ignored/);
});
