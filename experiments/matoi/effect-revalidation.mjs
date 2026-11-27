import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

assert.equal(process.argv.length, 3, 'Supply the pinned DSH checkout');
const checkout = resolve(process.argv[2]);
const revision = 'b6a1635b1200071754e2871b9d9453368e6daf23';
const git = (...args) => execFileSync('git', ['-C', checkout, ...args], { encoding: 'utf8' }).trim();
assert.equal(git('rev-parse', 'HEAD'), revision);
assert.equal(git('status', '--porcelain', '-uno'), '');
const approvalSource = 'packages/interaction/user-approval/src/index.ts';
const approvalHash = '632d819c0e1d0b0f489a17264a1e3bd9f88ae537746be768bbb0775d842e4a24';
assert.equal(createHash('sha256').update(readFileSync(resolve(checkout, approvalSource))).digest('hex'), approvalHash);

const url = path => pathToFileURL(resolve(checkout, path)).href;
const cordis = 'vendor/cordis/src/index.ts';
const routes = new Map(Object.entries({
  '@deepseek-ai/cordis': cordis,
  '@deepseek-ai/cosmokit': 'vendor/cosmokit/src/index.ts',
  '@deepseek-ai/schemastery': 'vendor/schemastery/src/index.ts',
  '@deepseek-ai/dsh-llm': 'packages/llm/llm/src/message.ts',
  '@deepseek-ai/dsh-scope': 'packages/core/scope/src/index.ts',
  '@deepseek-ai/dsh-session': 'packages/core/session/src/types.ts',
  '@deepseek-ai/dsh-brand': 'packages/util/brand/src/index.ts',
  '@deepseek-ai/dsh-util-crypto': 'packages/util/crypto/src/index.ts',
  '@deepseek-ai/dsh-util-values': 'packages/util/values/src/index.ts',
}));
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(routes.has(specifier) ? url(routes.get(specifier)) : specifier, context);
} });
const { Context } = await import(url(cordis));
const { default: ApprovalService, setApprovalPolicy } = await import(url(approvalSource));
hook.deregister();

const scenarios = {
  stable: 'confirmed',
  unrelated_change: 'confirmed',
  relevant_change: 'confirmed',
  revoked: 'rejected',
  unavailable: 'unavailable',
  unknown_retry: 'held-unknown',
};

async function exercise(mode, scenario, seed) {
  const events = [{ type: 'turn/start' }];
  const session = {
    get seq() { return events.length; },
    eventAt: index => events[index],
    append: (type, data) => events.push({ type, data }),
  };
  const agent = { session };
  const counts = { analyses: 0, approval_requests: 0, answerer_calls: 0, dispatches: 0 };
  const ctx = new Context();
  const approval = await ctx.plugin(ApprovalService);
  const answerer = ctx.on('approval/request', () => {
    counts.answerer_calls += 1;
    return 'allowed-once';
  });
  const attempts = new Map();
  const authorizedValues = [];
  let analyzed;
  let input = { amount: seed, label: 'initial' };

  async function attempt(id, loseReceipt = false) {
    if (attempts.get(id) === 'unknown') return 'held-unknown';
    if (mode === 'fresh' || analyzed?.amount !== input.amount) {
      counts.analyses += 1;
      analyzed = { amount: input.amount, effect: input.amount * 2 };
    }
    counts.approval_requests += 1;
    const decision = await ctx.approval.request({ agent, toolName: 'fixture-write', callId: id });
    if (decision !== 'allowed-once') return decision;
    counts.dispatches += 1;
    authorizedValues.push(analyzed.effect);
    const result = loseReceipt ? 'unknown' : 'confirmed';
    attempts.set(id, result);
    return result;
  }

  try {
    const first = await attempt('first', scenario === 'unknown_retry');
    assert.equal(first, scenario === 'unknown_retry' ? 'unknown' : 'confirmed');
    if (scenario === 'unrelated_change') input = { ...input, label: 'updated' };
    if (scenario === 'relevant_change') input = { ...input, amount: seed + 1 };
    if (scenario === 'revoked') setApprovalPolicy(session, 'never');
    if (scenario === 'unavailable') answerer();
    const secondId = scenario === 'unknown_retry' ? 'first' : 'second';
    const second = await attempt(secondId);
    assert.equal(second, scenarios[scenario]);
    const audit = events.filter(event => ['approval/asked', 'approval/decided'].includes(event.type));
    const decisions = ['allowed-once'];
    if (second !== 'held-unknown') decisions.push(second === 'confirmed' ? 'allowed-once' : second);
    assert.equal(audit.length, decisions.length * 2);
    for (const [index, decision] of decisions.entries()) {
      const [asked, decided] = audit.slice(index * 2, index * 2 + 2);
      assert.equal(asked.type, 'approval/asked');
      assert.equal(asked.data.callId, index === 0 ? 'first' : secondId);
      assert.deepEqual(decided, { type: 'approval/decided', data: { id: asked.data.id, outcome: decision } });
    }
    if (decisions.length === 2) assert.notEqual(audit[0].data.id, audit[2].data.id);
    const expectedValues = [seed * 2];
    if (second === 'confirmed') expectedValues.push((seed + Number(scenario === 'relevant_change')) * 2);
    assert.deepEqual(authorizedValues, expectedValues);
    assert.equal(counts.dispatches, expectedValues.length);
    assert.equal(counts.approval_requests, decisions.length);
    assert.equal(counts.answerer_calls, second === 'confirmed' ? 2 : 1);
    assert.equal(attempts.has('second'), second === 'confirmed');
    assert.equal(attempts.get('first'), first);
    return { first, second, ...counts };
  } finally {
    answerer();
    await approval.dispose();
  }
}

const repeats = [];
for (let repeat = 0; repeat < 3; repeat++) {
  const outcomes = {};
  const totals = {};
  for (const mode of ['fresh', 'selective']) {
    totals[mode] = { schedules: 0, analyses: 0, approval_requests: 0, answerer_calls: 0, dispatches: 0 };
    outcomes[mode] = {};
    for (const scenario of Object.keys(scenarios)) {
      for (let seed = 1 + repeat * 4; seed <= (repeat + 1) * 4; seed++) {
        const { first, second, ...counts } = await exercise(mode, scenario, seed);
        const expectedAnalyses = scenario === 'unknown_retry' ? 1 : mode === 'fresh' || scenario === 'relevant_change' ? 2 : 1;
        assert.equal(counts.analyses, expectedAnalyses);
        outcomes[mode][scenario] ??= { first, second, schedules: 0 };
        outcomes[mode][scenario].schedules += 1;
        totals[mode].schedules += 1;
        for (const [name, value] of Object.entries(counts)) totals[mode][name] += value;
      }
    }
  }
  assert.deepEqual(outcomes.fresh, outcomes.selective);
  const results = { scenarios: outcomes.fresh, totals };
  if (repeat > 0) assert.deepEqual(results, repeats[0]);
  repeats.push(results);
}

console.log(JSON.stringify({
  date: '2026-11-27',
  target_revision: revision,
  approval_source_sha256: approvalHash,
  node_version: process.versions.node,
  repeats,
}, null, 2));
