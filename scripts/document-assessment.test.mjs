import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateEntities, cardBodyHash, isDocumentedTarget } from './entity-model.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
function fixture() {
  const m = JSON.parse(fs.readFileSync(path.join(root, 'catalog/entities.json'), 'utf8'));
  const doc = 'portfolio/2026-09-03--2026-09-15/project-fit.md';
  const lines = fs.readFileSync(path.join(root, doc), 'utf8').replace(/\r\n/g, '\n').split('\n');
  const index = lines.findIndex(l => l.startsWith('| [BenchShield'));
  const row = { id: 'document-test', study_id: 'benchshield', project_id: 'agent-skills', review_id: 'bench-review', date: '2026-11-03', decision: 'DOCUMENTED_CANDIDATE', source_decision: 'P1_EVAL_INTEGRITY_DESIGN', evidence: 'P1_EVAL_INTEGRITY_DESIGN', reason: lines[index], limitations: 'Documented research candidate, not verified integration.', next_test: null, next_test_reason: 'See source plan.', project_revision: null, project_card_sha256: null, unknown_reason: 'Project implementation not inspected in this migration.', source_document: doc, source_line: index + 1, source_excerpt: lines[index], supersedes: null };
  m.assessments = m.assessments.filter(a => !(a.study_id === row.study_id && a.project_id === row.project_id));
  m.current_assessments = m.current_assessments.filter(a => !(a.study_id === row.study_id && a.project_id === row.project_id));
  m.assessments.push(row); m.current_assessments.push({ study_id: row.study_id, project_id: row.project_id, assessment_id: row.id });
  m.studies.find(s => s.id === row.study_id).fit_coverage = 'PARTIAL';
  return { m, row };
}
test('exact documentary research candidate is accepted without project verification claim', () => {
  const { m } = fixture(); validateEntities(root, m);
});
test('fabricated quotation is rejected', () => {
  const { m, row } = fixture(); row.source_excerpt += ' fabricated';
  assert.throws(() => validateEntities(root, m), /quote\/line mismatch/);
});
test('documentary candidate cannot become verified by changing the status', () => {
  const { m, row } = fixture(); row.evidence = 'SOURCE_CODE_VERIFIED';
  assert.throws(() => validateEntities(root, m), /evidence not verbatim/);
});
test('project not named in the source row is rejected', () => {
  const { m, row } = fixture(); row.project_id = 'MyPartyIsGrinding';
  assert.throws(() => validateEntities(root, m), /does not mention project/);
});
test('source row for another study is rejected', () => {
  const { m, row } = fixture(); row.study_id = 'rrsi'; row.review_id = 'selection-review';
  assert.throws(() => validateEntities(root, m), /belongs to another study/);
});
test('schema v2 detects a changed card body even when navigation survives', () => {
  assert.notEqual(cardBodyHash('# Source\n\nOriginal evidence'), cardBodyHash('# Source\n\nDifferent evidence'));
  assert.equal(cardBodyHash('# Source\n\nOriginal evidence'), cardBodyHash('# Source\n\n[Структурированная запись и связи](../catalog/studies/source.md)\n\nOriginal evidence'));
  const { m } = fixture(); m.studies[0].card_body_sha256 = '0'.repeat(64);
  assert.throws(() => validateEntities(root, m), /body hash mismatch/);
});
test('project mentioned only in a limitation is not a target', () => {
  const lines = fs.readFileSync(path.join(root, 'portfolio/2026-10-12--2026-10-19/project-fit.md'), 'utf8').split(/\r?\n/);
  const index = lines.findIndex(line => line.startsWith('| [MemComposer]'));
  assert.ok(index >= 0);
  assert.equal(isDocumentedTarget(lines, index, 'dsh-team-context'), true);
  assert.equal(isDocumentedTarget(lines, index, 'dsh-runtime'), true);
  assert.equal(isDocumentedTarget(lines, index, 'Wiki_PG'), false);
});
