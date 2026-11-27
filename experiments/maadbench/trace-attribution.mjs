import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

assert.equal(process.argv.length, 4, 'Supply the pinned DSH checkout and the zod package directory');
const [checkout, dependency] = process.argv.slice(2).map(path => resolve(path));
const revision = 'b6a1635b1200071754e2871b9d9453368e6daf23';
const git = (...args) => execFileSync('git', ['-C', checkout, ...args], { encoding: 'utf8' }).trim();
assert.equal(git('rev-parse', 'HEAD'), revision);
assert.equal(git('status', '--porcelain', '-uno'), '');
const source = 'packages/experimental/agent-team/src';
const hashes = {
  'projection.ts': 'f960707e326f359bdde63bdfe47fdd485c1489230e2be1fcb701849260f08174',
  'task-graph.ts': 'a726081289a2f7a848f69109a750db3ead0d95b88ab0adfdae0477f749b8f490',
};
for (const [file, hash] of Object.entries(hashes)) {
  assert.equal(createHash('sha256').update(readFileSync(resolve(checkout, source, file))).digest('hex'), hash);
}
const manifest = JSON.parse(readFileSync(resolve(dependency, 'package.json'), 'utf8'));
assert.equal(manifest.name, 'zod');
assert.equal(manifest.version, '4.4.3');
const routes = new Map([
  ['zod', pathToFileURL(resolve(dependency, manifest.exports['.'].import)).href],
  ['@deepseek-ai/dsh-brand', pathToFileURL(resolve(checkout, 'packages/util/brand/src/index.ts')).href],
]);
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(routes.get(specifier) ?? specifier, context);
} });
const projection = (await import(pathToFileURL(resolve(checkout, source, 'projection.ts')).href)).teamProjectionDefinition;
hook.deregister();

const teamId = 'fixture-team';
const parents = { left: [], right: [], join: ['left', 'right'], final: ['join'] };
const expected = {
  clean: { projection: null, origin: [], propagated: [], missing: [], unknown: [] },
  wrong_left: { projection: null, origin: ['left'], propagated: ['join', 'final'], missing: [], unknown: [] },
  wrong_join: { projection: null, origin: ['join'], propagated: ['final'], missing: [], unknown: [] },
  missing_revision: { projection: { task: 'left', revision: 3, sequence: 6 } },
  missing_delivery: { projection: null, origin: [], propagated: [], missing: ['left'], unknown: ['join'] },
};

function fixture(seed, scenario) {
  let sequence = 0;
  const events = [];
  const append = (type, fields, omit = false) => {
    sequence += 1;
    if (!omit) events.push({ type, data: { version: 2, teamId, ...fields }, seq: sequence, time: sequence });
  };
  const task = (id, revision, status, omit) => append('team/task', {
    task: { id, revision, status, subject: id, description: '', blockedBy: parents[id], writeScopes: [] },
  }, omit);
  const left = seed + 2 + (scenario === 'wrong_left' ? 7 : 0);
  const right = seed * 3;
  const join = left + right + (scenario === 'wrong_join' ? 7 : 0);
  for (const id of Object.keys(parents)) task(id, 1, 'pending');
  for (const [id, value] of Object.entries({ left, right, join, final: join * 2 })) {
    task(id, 2, 'in_progress', scenario === 'missing_revision' && id === 'left');
    task(id, 3, 'completed');
    const messageId = `result-${id}`;
    append('team/message/queued', { message: {
      id: messageId, senderId: id, senderName: id, targetId: teamId,
      content: [{ type: 'text', text: JSON.stringify({ id, value }) }],
    } });
    append('team/message/delivered', { messageId, targetId: teamId }, scenario === 'missing_delivery' && id === 'left');
  }
  return events;
}

function assess(state, seed) {
  const receipts = new Map();
  for (const message of state.messages) {
    if (!state.delivered.includes(message.id)) continue;
    const { id, value } = JSON.parse(message.content[0].text);
    assert.equal(message.id, `result-${id}`);
    assert.ok(Number.isSafeInteger(value) && !receipts.has(id));
    receipts.set(id, value);
  }
  const reference = { left: seed + 2, right: seed * 3, join: 4 * seed + 2, final: 8 * seed + 4 };
  const result = { origin: [], propagated: [], missing: [], unknown: [] };
  assert.equal(state.tasks.length, 4);
  for (const task of state.tasks) {
    const { id, blockedBy } = task;
    assert.equal(task.status, 'completed');
    assert.deepEqual(blockedBy, parents[id]);
    const observed = receipts.get(id);
    if (observed === undefined) {
      result.missing.push(id);
      continue;
    }
    const inputs = blockedBy.map(parent => receipts.get(parent));
    if (inputs.includes(undefined)) {
      result.unknown.push(id);
      continue;
    }
    const local = id === 'join' ? inputs[0] + inputs[1] : id === 'final' ? inputs[0] * 2 : reference[id];
    if (observed !== local) result.origin.push(id);
    else if (observed !== reference[id]) result.propagated.push(id);
  }
  return result;
}

const repeats = [];
for (let repeat = 0; repeat < 3; repeat++) {
  const counts = {};
  for (const [scenario, oracle] of Object.entries(expected)) {
    const totals = { traces: 0, projection_rejections: 0, exact_observer_matches: 0, origins: 0, propagated: 0, missing: 0, unknown: 0 };
    for (let seed = repeat * 12 + 1; seed <= (repeat + 1) * 12; seed++) {
      const state = projection.init({ id: teamId });
      let firstFailure = null;
      for (const event of fixture(seed, scenario)) {
        projection.apply(state, event);
        if (state.failure && firstFailure === null) {
          assert.match(state.failure, /revision is not contiguous/);
          firstFailure = { task: event.data.task.id, revision: event.data.task.revision, sequence: event.seq };
        }
      }
      assert.deepEqual(firstFailure, oracle.projection);
      const result = firstFailure ? { projection: firstFailure } : { projection: null, ...assess(state, seed) };
      assert.deepEqual(result, oracle);
      totals.traces += 1;
      totals.projection_rejections += Number(firstFailure !== null);
      totals.exact_observer_matches += 1;
      totals.origins += result.origin?.length ?? 0;
      totals.propagated += result.propagated?.length ?? 0;
      totals.missing += result.missing?.length ?? 0;
      totals.unknown += result.unknown?.length ?? 0;
    }
    counts[scenario] = totals;
  }
  if (repeat > 0) assert.deepEqual(counts, repeats[0]);
  repeats.push(counts);
}

console.log(JSON.stringify({
  date: '2026-11-27',
  target_revision: revision,
  source_sha256: hashes,
  node_version: process.versions.node,
  zod_version: manifest.version,
  cases_per_repeat: 60,
  first_structural_error: expected.missing_revision.projection,
  repeats,
}, null, 2));
