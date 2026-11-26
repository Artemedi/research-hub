import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const revision = 'b6a1635b1200071754e2871b9d9453368e6daf23';
const source = resolve(process.argv[2]);
const git = (...args) => execFileSync('git', ['-C', source, ...args], { encoding: 'utf8' }).trim();
assert.equal(git('rev-parse', 'HEAD'), revision);
assert.equal(git('status', '--porcelain', '--untracked-files=no'), '');
const url = (path) => pathToFileURL(resolve(source, path)).href;
const team = 'packages/experimental/agent-team/src';
const boardPath = `${team}/task-board.ts`;
const hashes = {
  [boardPath]: 'fdc554f616ea2b1fd0396d8665a7e116e2e787c075a69e906b22c3b5fd6f1750',
  [`${team}/task-graph.ts`]: 'a726081289a2f7a848f69109a750db3ead0d95b88ab0adfdae0477f749b8f490',
};
for (const [path, hash] of Object.entries(hashes)) {
  assert.equal(createHash('sha256').update(readFileSync(resolve(source, path))).digest('hex'), hash);
}

const rosterStub = 'data:text/javascript,' + encodeURIComponent(
  'export function resolveActiveMember() { throw new Error("Reassignment is outside this fixture"); }',
);
const hook = registerHooks({ resolve(specifier, context, next) {
  if (specifier === './roster.ts' && context.parentURL === url(boardPath)) {
    return next(rosterStub, context);
  }
  if (specifier === '@deepseek-ai/dsh-llm' && context.parentURL === url(`${team}/error.ts`)) {
    return next(url('packages/llm/llm/src/error.ts'), context);
  }
  return next(specifier, context);
} });
const { TeamTaskBoard } = await import(url(boardPath));
hook.deregister();

function setup() {
  const root = { id: 'fixture-lead' };
  const owner = { id: 'fixture-owner' };
  const membership = { root, role: 'member' };
  const tasks = new Map();
  const journal = {
    transact(id, operation) {
      assert.equal(id, root.id);
      return operation();
    },
    state(caller) {
      assert.equal(caller, root);
      return { tasks: [...tasks.values()], members: [], nextTaskNumber: tasks.size + 1 };
    },
    appendAndFlush(caller, type, event) {
      assert.equal(caller, root);
      assert.equal(type, 'team/task');
      assert.equal(event.teamId, root.id);
      assert.equal(event.version, 2);
      assert.equal(event.task.revision, (tasks.get(event.task.id)?.revision ?? 0) + 1);
      tasks.set(event.task.id, structuredClone(event.task));
    },
  };
  const board = new TeamTaskBoard(journal, 4);
  return {
    create: (subject, description, blockedBy = []) => board.create(membership, { subject, description, blockedBy }),
    get: (id) => board.get(membership, id),
    update: (task, action, caller = owner) => board.update(caller, membership, {
      taskId: task.id, expectedRevision: task.revision, action,
    }),
  };
}

// The laboratory verifier consumes results scoped to the expected task and its current revision.
function verified(inputs, receipts) {
  return inputs.every(({ task, terms }) => {
    const receipt = receipts.get(task.id);
    return receipt?.task === task.id && receipt.revision === task.revision
      && receipt.total === terms.reduce((sum, value) => sum + value, 0);
  });
}

async function replay(index, scenario, useVerifier) {
  const board = setup();
  let first = await board.create('First subtotal', 'Sum the first pair of fixture inputs.');
  let second = await board.create('Second subtotal', 'Sum the second pair of fixture inputs.');
  const child = await board.create('Combine subtotals', 'Use both computed subtotals.', [first.id, second.id]);
  const other = await board.create('Unrelated subtotal', 'Independent fixture work.');
  const getReceipt = (task, total) => ({ task: task.id, revision: task.revision, total });

  await assert.rejects(board.update(child, 'claim'), { code: 'TEAM_TASK_BLOCKED' });
  first = await board.update(first, 'claim');
  await assert.rejects(board.update(first, 'complete', { id: 'unrelated-owner' }), { code: 'TEAM_TASK_UNAUTHORIZED' });
  first = await board.update(first, 'complete');
  second = await board.update(second, 'claim');
  if (scenario !== 'parent_in_progress') second = await board.update(second, 'complete');
  const receipts = new Map([
    [first.id, getReceipt(first, index + 2)],
    [second.id, getReceipt(second, index + 5)],
    [other.id, getReceipt(other, index + 5)],
  ]);
  if (scenario === 'missing') receipts.delete(second.id);
  if (scenario === 'wrong_value') receipts.get(second.id).total += 1;
  if (scenario === 'wrong_parent') receipts.set(second.id, receipts.get(other.id));
  if (scenario === 'stale_revision') {
    second = await board.update(second, 'reopen');
    await assert.rejects(board.update(child, 'claim'), { code: 'TEAM_TASK_BLOCKED' });
    second = await board.update(second, 'claim');
    second = await board.update(second, 'complete');
  }

  const canVerify = () => verified([
    { task: board.get(first.id), terms: [index, 2] },
    { task: board.get(second.id), terms: [index, 5] },
  ], receipts);
  const ready = board.get(child.id).ready;
  const passes = canVerify();
  if (!ready) {
    await assert.rejects(board.update(child, 'claim'), { code: 'TEAM_TASK_BLOCKED' });
  } else if (!useVerifier || passes) {
    assert.equal((await board.update(child, 'claim')).status, 'in_progress');
  }
  const claimed = board.get(child.id).status === 'in_progress';

  if (useVerifier && !claimed) {
    if (second.status === 'in_progress') second = await board.update(second, 'complete');
    receipts.set(second.id, getReceipt(second, index + 5));
    assert.equal(board.get(child.id).ready && canVerify(), true);
    assert.equal((await board.update(child, 'claim')).status, 'in_progress');
  }
  return { ready, passes, claimed };
}

const scenarios = new Map([
  ['verified', [true, true]],
  ['missing', [true, false]],
  ['wrong_value', [true, false]],
  ['wrong_parent', [true, false]],
  ['stale_revision', [true, false]],
  ['parent_in_progress', [false, true]],
]);
const casesPerScenario = 8;
async function run() {
  const results = {};
  for (const [scenario, [expectedReady, expectedPass]] of scenarios) {
    const counts = { board_ready: 0, baseline_claims: 0, verified_claims: 0, verified_recoveries: 0 };
    for (let index = 0; index < casesPerScenario; index++) {
      const baseline = await replay(index, scenario, false);
      const guarded = await replay(index, scenario, true);
      assert.deepEqual(baseline, { ready: expectedReady, passes: expectedPass, claimed: expectedReady });
      assert.deepEqual(guarded, { ready: expectedReady, passes: expectedPass, claimed: expectedReady && expectedPass });
      counts.board_ready += baseline.ready;
      counts.baseline_claims += baseline.claimed;
      counts.verified_claims += guarded.claimed;
      counts.verified_recoveries += !guarded.claimed;
    }
    results[scenario] = counts;
  }
  return results;
}

const counts = await run();
assert.deepEqual(await run(), counts);
assert.deepEqual(await run(), counts);
console.log(JSON.stringify({ revision, source_sha256: hashes, cases_per_scenario: casesPerScenario,
  repeats: 3, agent_or_provider_calls: 0, counts }, null, 2));
