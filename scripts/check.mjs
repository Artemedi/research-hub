import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const exists = p => fs.existsSync(path.join(root, p));
const walk = dir => fs.readdirSync(path.join(root, dir), { withFileTypes: true }).flatMap(e => {
  if (e.name === '.git') return [];
  const p = dir ? `${dir}/${e.name}` : e.name;
  return e.isDirectory() ? walk(p) : [p];
});
const files = walk(''), errors = [];
const config = JSON.parse(read('catalog/structure.json'));
assert.equal(config.schema_version, 1);
const safe = p => typeof p === 'string' && !p.includes('\\') && !p.startsWith('/') && path.posix.normalize(p) === p && !p.startsWith('../');
const targets = config.documents.map(d => d.to);
assert.equal(new Set(targets).size, targets.length, 'duplicate canonical document');
for (const d of config.documents) {
  assert.ok(safe(d.to) && exists(d.to), d.to);
  assert.ok(d.title && d.kind, d.to);
  if (d.from) assert.ok(safe(d.from) && d.from.startsWith('reports/') && exists(d.from), d.from);
  else assert.match(d.date, /^\d{4}-\d{2}-\d{2}$/);
}
assert.equal(new Set(config.studies).size, config.studies.length);
const actualStudies = files.filter(p => p.startsWith('studies/') && p.endsWith('.md') && p !== 'studies/INDEX.md').sort();
assert.deepEqual([...config.studies].sort(), actualStudies, 'uncatalogued study');
for (const folder of ['reviews', 'portfolio']) {
  assert.deepEqual(files.filter(p => p.startsWith(folder + '/') && p.endsWith('.md') && p !== folder + '/README.md').sort(), targets.filter(p => p.startsWith(folder + '/') && p.endsWith('.md')).sort(), 'uncatalogued ' + folder);
}
const aliases = config.documents.filter(d => d.from).map(d => d.from).sort();
assert.equal(new Set(aliases).size, aliases.length, 'duplicate legacy endpoint');
assert.deepEqual(files.filter(p => p.startsWith('reports/') && p !== 'reports/README.md').sort(), aliases, 'unregistered legacy file');

let jsonCount = 0;
for (const p of files.filter(p => p.endsWith('.json'))) { JSON.parse(read(p)); jsonCount++; }
const ledger = JSON.parse(read('collections/telegram/bookmarks.json'));
assert.equal(ledger.entries.length, ledger.source_record_count);
assert.equal(new Set(ledger.entries.map(e => e.id)).size, ledger.entries.length);
for (const [status, n] of Object.entries(ledger.count_by_status)) assert.equal(ledger.entries.filter(e => e.status === status).length, n, status);
for (const e of ledger.entries) for (const key of ['hub_study_card', 'hub_experiment_report']) if (e[key]) assert.ok(exists(e[key]), e[key]);

function slug(s) { return s.trim().toLowerCase().replace(/<[^>]*>/g, '').replace(/[^\p{L}\p{N}\p{M}_\-\s]/gu, '').replace(/ /g, '-'); }
const anchorCache = new Map();
function anchors(p) {
  if (anchorCache.has(p)) return anchorCache.get(p);
  const text = read(p), result = new Set(), used = new Map();
  for (const m of text.matchAll(/^#{1,6} (.+)$/gm)) {
    const base = slug(m[1]), n = used.get(base) ?? 0;
    used.set(base, n + 1); result.add(base + (n ? `-${n}` : ''));
  }
  for (const m of text.matchAll(/<a\s+(?:id|name)="([^"]+)"/g)) result.add(m[1]);
  anchorCache.set(p, result); return result;
}
let links = 0;
const hub = 'https://github.com/Artemedi/research-hub/blob/main/';
for (const p of files.filter(p => p.endsWith('.md') && !p.startsWith('archive/'))) {
  const text = read(p).replace(/```[^\n]*\n[\s\S]*?```/g, '');
  for (const m of text.matchAll(/!?\[[^\]\n]*\]\(([^\s)]+)\)/g)) {
    const url = m[1];
    if (/^[a-z]+:/i.test(url) && !url.startsWith(hub)) continue;
    if (url.startsWith('//')) continue;
    const [base, rawAnchor] = url.split('#');
    const dest = url.startsWith(hub) ? base.slice(hub.length) : base ? path.posix.normalize(path.posix.join(path.posix.dirname(p), decodeURIComponent(base))) : p;
    if (!safe(dest) || !exists(dest)) errors.push(`${p}: missing ${url}`);
    else if (rawAnchor && dest.endsWith('.md') && !anchors(dest).has(decodeURIComponent(rawAnchor))) errors.push(`${p}: missing anchor ${url}`);
    links++;
  }
}
let preserved = 0;
for (const m of read('archive/dsh/ARCHIVE_MANIFEST.md').matchAll(/\| \[knowledge\/research\/([^\]]+)\]\([^)]*\) \| [a-f0-9]{40} \| ([a-f0-9]{64}) \|/g)) {
  const file = 'archive/dsh/knowledge/research/' + m[1];
  assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex'), m[2], file);
  preserved++;
}
assert.ok(preserved > 0, 'archive manifest parsed no rows');
const generated = spawnSync(process.execPath, [path.join(root, 'scripts/build-catalog.mjs'), '--check'], { encoding: 'utf8' });
if (generated.status !== 0) errors.push(generated.stderr || generated.error?.message || 'catalog check failed');
if (errors.length) { console.error(errors.join('\n')); process.exitCode = 1; }
else console.log(JSON.stringify({ studies: config.studies.length, canonical_documents: targets.length, legacy_endpoints: aliases.length, json_files: jsonCount, links, preserved_archive_files: preserved, ledger: ledger.count_by_status }));
