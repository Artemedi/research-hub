import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const revision = 'b6a1635b1200071754e2871b9d9453368e6daf23';
const checkout = resolve(process.argv[2]);
const git = (...args) => execFileSync('git', ['-C', checkout, ...args], { encoding: 'utf8' }).trim();
assert.equal(git('rev-parse', 'HEAD'), revision);
assert.equal(git('status', '--porcelain', '--untracked-files=no'), '');
const url = (path) => pathToFileURL(resolve(checkout, path)).href;
const approvalPath = 'packages/interaction/user-approval/src/index.ts';
const hashes = {
  [approvalPath]: '632d819c0e1d0b0f489a17264a1e3bd9f88ae537746be768bbb0775d842e4a24',
  'packages/interaction/user-approval/src/types.ts': '46548447cf6aab4283d5473a99014b2b6075724982b99cc3dc77b9ae8274200c',
};
for (const [path, hash] of Object.entries(hashes)) {
  assert.equal(createHash('sha256').update(readFileSync(resolve(checkout, path))).digest('hex'), hash);
}

const fixtureModule = (code) => 'data:text/javascript,' + encodeURIComponent(code);
const routes = new Map([
  ['@deepseek-ai/cordis', fixtureModule('export class Context {} export class Service { constructor(ctx) { this.ctx = ctx; } }')],
  ['@deepseek-ai/schemastery', fixtureModule('export default { object: (shape) => shape, union: () => ({ default: (value) => value }) };')],
  ['@deepseek-ai/dsh-llm', fixtureModule('export function createUserMessage() { throw new Error("No messages in this fixture"); }')],
  ['@deepseek-ai/dsh-scope', url('packages/core/scope/src/index.ts')],
  ['@deepseek-ai/dsh-session', url('packages/core/session/src/types.ts')],
  ['@deepseek-ai/dsh-brand', url('packages/util/brand/src/index.ts')],
]);
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(routes.get(specifier) ?? specifier, context);
} });
const { ApprovalService } = await import(url(approvalPath));
const { carrierKeyOf } = await import(routes.get('@deepseek-ai/dsh-scope'));
hook.deregister();

const casesPerScenario = 10;
// Outcome, answerer invocations, number of audit records, permitted changes.
const expectations = {
  allowed: ['allowed-once', 1, 2, 1],
  rejected: ['rejected', 1, 2, 0],
  no_answerer: ['unavailable', 0, 2, 0],
  answerer_error: ['unavailable', 1, 2, 0],
  already_cancelled: ['cancelled', 0, 2, 0],
  cancelled_then_allowed: ['cancelled', 1, 2, 0],
  never_policy: ['rejected', 0, 2, 0],
  audit_write_failure: ['error', 1, 1, 0],
  closed_turn: ['error', 0, 0, 0],
};

async function replay(scenario, index) {
  const events = [{ type: 'turn/start' }];
  if (scenario === 'closed_turn') events.push({ type: 'turn/end' });
  const auditStart = events.length;
  const dispatches = [];
  let answererCalls = 0;
  const effects = [];
  const auditFailure = new Error('Synthetic audit append failure');
  const session = {
    get seq() { return events.length; },
    eventAt: (seq) => events[seq],
    append(type, data) {
      if (scenario === 'audit_write_failure' && type === 'approval/decided') throw auditFailure;
      events.push({ type, data: structuredClone(data) });
    },
  };
  const agent = { session };
  const controller = new AbortController();
  const proposed = { label: `counter-${index}`, delta: index + 1 };
  const request = {
    agent, toolName: 'increment-fixture-counter', callId: `increment-${index}`,
    reason: 'Record the approved fixture increment.', signal: controller.signal,
  };
  let markDispatched;
  const dispatched = new Promise((resolve) => { markDispatched = resolve; });
  let releaseAnswerer;
  const delayedAnswer = new Promise((resolve) => { releaseAnswerer = resolve; });
  const context = {
    inject: () => {},
    waterfall(target, event, actualRequest, fallback) {
      dispatches.push({ target, event, actualRequest });
      if (scenario === 'no_answerer') return fallback();
      answererCalls++;
      if (scenario === 'answerer_error') throw new Error('Synthetic answerer failure');
      if (scenario === 'cancelled_then_allowed') {
        markDispatched();
        return delayedAnswer;
      }
      return scenario === 'rejected' ? 'rejected' : 'allowed-once';
    },
  };
  const service = new ApprovalService(context, { policy: scenario === 'never_policy' ? 'never' : 'ask' });
  const counters = new Map([[proposed.label, 0]]);
  const perform = () => {
    const before = counters.get(proposed.label);
    counters.set(proposed.label, before + proposed.delta);
    effects.push({ call: request.callId, finalizedRecords: events.length - auditStart });
  };
  const run = async () => {
    const outcome = await service.request(request);
    if (outcome === 'allowed-once') perform();
    return outcome;
  };
  if (scenario === 'already_cancelled') controller.abort();
  const response = run();
  if (scenario === 'cancelled_then_allowed') {
    // A premature response also releases this wait so it fails the expectations below.
    await Promise.race([dispatched, response]);
    controller.abort();
  }
  let outcome;
  if (scenario === 'audit_write_failure' || scenario === 'closed_turn') {
    await assert.rejects(response, scenario === 'audit_write_failure'
      ? (error) => error === auditFailure
      : /outside an open turn/);
    outcome = 'error';
  } else {
    outcome = await response;
  }
  releaseAnswerer('allowed-once');
  await new Promise(setImmediate);

  assert.equal(dispatches.length, scenario === 'no_answerer' ? 1 : expectations[scenario][1]);
  for (const { target, event, actualRequest } of dispatches) {
    assert.equal(carrierKeyOf(target), agent);
    assert.equal(event, 'approval/request');
    assert.equal(actualRequest, request);
  }
  const audit = events.slice(auditStart);
  if (audit.length) {
    const [asked, decided] = audit;
    assert.equal(asked.type, 'approval/asked');
    assert.equal(asked.data.callId, request.callId);
    assert.equal(asked.data.toolName, request.toolName);
    assert.equal(asked.data.reason, request.reason);
    assert.ok(asked.data.id);
    if (decided) {
      assert.equal(decided.type, 'approval/decided');
      assert.deepEqual(decided.data, { id: asked.data.id, outcome });
    }
  }
  const effectCount = expectations[scenario][3];
  assert.equal(counters.get(proposed.label), effectCount * proposed.delta);
  assert.deepEqual(effects, effectCount ? [{ call: request.callId, finalizedRecords: 2 }] : []);
  return [outcome, answererCalls, audit.length, effects.length];
}

async function run() {
  const counts = {};
  for (const [scenario, expected] of Object.entries(expectations)) {
    const observed = { cases: 0, outcomes: {}, answerer_calls: 0, audit_records: 0, effects: 0 };
    for (let index = 0; index < casesPerScenario; index++) {
      const actual = await replay(scenario, index);
      assert.deepEqual(actual, expected, scenario);
      const [outcome, calls, records, effects] = actual;
      observed.cases++;
      observed.outcomes[outcome] = (observed.outcomes[outcome] ?? 0) + 1;
      observed.answerer_calls += calls;
      observed.audit_records += records;
      observed.effects += effects;
    }
    counts[scenario] = observed;
  }
  return counts;
}

const results = await run();
assert.deepEqual(await run(), results);
assert.deepEqual(await run(), results);
console.log(JSON.stringify({ revision, source_sha256: hashes, cases_per_scenario: casesPerScenario,
  repeats: 3, shell_or_provider_calls: 0, results }, null, 2));
