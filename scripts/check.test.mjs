import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
function fixture(change) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'research-hub-check-'));
  try {
    fs.cpSync(root, temp, { recursive: true, filter: src => path.basename(src) !== '.git' });
    change(temp);
    return spawnSync(process.execPath, [path.join(temp, 'scripts/check.mjs')], { encoding: 'utf8', timeout: 15000 });
  } finally {
    assert.equal(path.dirname(temp), path.resolve(os.tmpdir()));
    assert.ok(path.basename(temp).startsWith('research-hub-check-'));
    fs.rmSync(temp, { recursive: true, force: true });
  }
}
test('valid repository passes without executing experiments', () => {
  const result = fixture(() => {});
  assert.equal(result.status, 0, result.stderr);
});
test('broken document link is rejected', () => {
  const result = fixture(dir => fs.appendFileSync(path.join(dir, 'README.md'), '\n[Broken](reviews/missing.md)\n'));
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /missing reviews\/missing.md/);
});
test('stale machine-readable compatibility copy is rejected', () => {
  const result = fixture(dir => fs.writeFileSync(path.join(dir, 'reports/2026-11-04-telegram-bookmarks-reconciliation.json'), '{}\n'));
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Generated catalog differs/);
});
test('unindexed study is rejected', () => {
  const result = fixture(dir => fs.writeFileSync(path.join(dir, 'studies/unindexed.md'), '# Unindexed\n'));
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /uncatalogued study/);
});
test('terminal study disposition cannot silently change in the independent ledger', () => {
  const result = fixture(dir => {
    const file = path.join(dir, 'data/results/research-portfolio/2026-11-09-closure-ledger.json');
    const ledger = JSON.parse(fs.readFileSync(file, 'utf8'));
    const study = ledger.studies.find(item => item.study_id === 'hyperresearch');
    assert.equal(study.closure_status, 'BLOCKED');
    study.closure_status = 'ACCEPT_BOUNDED';
    fs.writeFileSync(file, JSON.stringify(ledger, null, 2) + '\n');
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Closure ledger integrity failed/);
});
test('changed archive bytes are rejected', () => {
  const result = fixture(dir => fs.appendFileSync(path.join(dir, 'archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md'), '\nChanged\n'));
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /archive\/dsh\/knowledge\/research/);
});
