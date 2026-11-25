import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
function runCheck(temp) {
  return spawnSync(process.execPath, [path.join(temp, 'scripts/check.mjs')], { encoding: 'utf8', timeout: 15000 });
}

function fixture(change, run = runCheck) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'research-hub-check-'));
  try {
    fs.cpSync(root, temp, { recursive: true, filter: src => path.basename(src) !== '.git' });
    change(temp);
    return run(temp);
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
for (const gate of ['2026-11-09-ledger-independent-check.py', '2026-11-09-targeted-fit.py']) {
  const runGate = dir => spawnSync('python3', ['-B', path.join(dir, 'experiments/research-portfolio', gate), '--check'],
    { encoding: 'utf8', timeout: 15000 });
  test(`${gate} accepts a new review and a changed current pointer`, () => {
    const result = fixture(dir => {
      const file = path.join(dir, 'catalog/entities.json');
      const entities = JSON.parse(fs.readFileSync(file, 'utf8'));
      const study = entities.studies.find(row => row.id === 'silent-cue-loss');
      const old = entities.reviews.find(row => row.id === study.current_review_id);
      entities.reviews.push({ ...old, id: 'fixture-new-review', supersedes: old.id });
      study.current_review_id = 'fixture-new-review';
      fs.writeFileSync(file, JSON.stringify(entities));
    }, runGate);
    assert.equal(result.status, 0, result.stderr);
  });
  test(`${gate} rejects a change to the frozen copy or an original review`, () => {
    const frozen = fixture(dir => {
      fs.appendFileSync(path.join(dir, 'data/results/research-portfolio/2026-11-09-basis-entities.json'), ' ');
    }, runGate);
    assert.equal(frozen.status, 1);
    assert.match(frozen.stderr, /Frozen entities file hash mismatch/);
    const live = fixture(dir => {
      const file = path.join(dir, 'catalog/entities.json');
      const entities = JSON.parse(fs.readFileSync(file, 'utf8'));
      entities.reviews.find(row => row.id === 'silent-cue-loss-review').limitations += ' changed';
      fs.writeFileSync(file, JSON.stringify(entities));
    }, runGate);
    assert.equal(live.status, 1);
    assert.match(live.stderr, /Historical reviews record changed/);
  });
}
test('applicability matrix cannot promote an untested project pair to production', () => {
  const result = fixture(dir => {
    const file = path.join(dir, 'data/project-fit/portfolio/2026-11-09-targeted-fit.json');
    const matrix = JSON.parse(fs.readFileSync(file, 'utf8'));
    matrix.pairs[0].production_approved = true;
    fs.writeFileSync(file, JSON.stringify(matrix, null, 2) + '\n');
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Targeted applicability matrix integrity failed/);
});
test('P0 unmeasured pair cannot silently become production approved', () => {
  const result = fixture(dir => {
    const file = path.join(dir, 'data/results/research-portfolio/2026-11-10-p0-outcomes.json');
    const outcomes = JSON.parse(fs.readFileSync(file, 'utf8'));
    outcomes.rows[0].production_approved = true;
    fs.writeFileSync(file, JSON.stringify(outcomes, null, 2) + '\n');
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /P0 offline experimental integrity failed/);
});
test('changed archive bytes are rejected', () => {
  const result = fixture(dir => fs.appendFileSync(path.join(dir, 'archive/dsh/knowledge/research/2026-09-15-research-review-decisions.md'), '\nChanged\n'));
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /archive\/dsh\/knowledge\/research/);
});

for (const removeFile of [false, true]) {
  test(`archive omission is rejected when the corresponding file is ${removeFile ? 'also removed' : 'still present'}`, () => {
    const result = fixture(dir => {
      const target = '2026-09-15-research-review-decisions.md';
      const manifest = path.join(dir, 'archive/dsh/ARCHIVE_MANIFEST.md');
      const lines = fs.readFileSync(manifest, 'utf8').split('\n');
      fs.writeFileSync(manifest, lines.filter(line => !line.startsWith(`| [knowledge/research/${target}]`)).join('\n'));
      if (removeFile) fs.unlinkSync(path.join(dir, 'archive/dsh/knowledge/research', target));
    });
    assert.equal(result.status, 1);
    assert.match(result.stderr, removeFile ? /original archive manifest entries changed/ : /archive inventory differs from manifest/);
  });
}

test('unexpected archive file is rejected', () => {
  const result = fixture(dir => fs.writeFileSync(path.join(dir, 'archive/dsh/knowledge/research/extra.md'), '# Extra\n'));
  assert.equal(result.status, 1);
  assert.match(result.stderr, /archive inventory differs from manifest/);
});

for (const fence of ['````', '~~~~']) {
  test(`fenced pseudo-heading is rejected as an anchor (${fence[0]})`, () => {
    const result = fixture(dir => fs.appendFileSync(path.join(dir, 'README.md'),
      `\n[Missing](#phantom-heading)\n\n${fence}text\n## Phantom heading\n${fence}\n`));
    assert.equal(result.status, 1);
    assert.match(result.stderr, /missing anchor #phantom-heading/);
  });
  test(`real anchors remain visible and fenced links are ignored (${fence[0]})`, () => {
    const result = fixture(dir => fs.appendFileSync(path.join(dir, 'README.md'),
      `\n[Real](#real-heading)\n\n${fence}text\n${fence.slice(1)}\n[Ignored](bogus.md)\n${fence}\n\n## Real heading\n`));
    assert.equal(result.status, 0, result.stderr);
  });
}

test('unexpected generated study and project files are reported', () => {
  const result = fixture(dir => {
    for (const folder of ['catalog/studies', 'projects']) {
      fs.writeFileSync(path.join(dir, folder, 'extra.md'),
        '<!-- Generated by scripts/build-catalog.mjs. Edit catalog/structure.json or canonical source files. -->\n');
    }
  });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /unexpected catalog\/studies\/extra.md, unexpected projects\/extra.md/);
});

test('compatibility alias preserves the historic anchor and links to its containing section', () => {
  const body = fs.readFileSync(path.join(root, 'reports/2026-11-04-benchshield-reward-integrity-offline.md'), 'utf8');
  assert.match(body, /<a id="скрипт-печатает-json-statuspass-выход-с-ошибкой-при-ложных-контрольных-ожиданиях"><\/a>/);
  assert.match(body, /Скрипт печатает[^\n]+\.md#[^\s)]+\)/);
  assert.doesNotMatch(body, /\.md#скрипт-печатает-json-statuspass/);
});
