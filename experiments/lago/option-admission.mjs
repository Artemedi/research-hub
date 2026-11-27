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
assert.equal(git('status', '--porcelain', '-uno'), '');
const path = 'packages/skill/skill/src/index.ts';
const registryHash = 'bdec27a0ba5dc4063f7987dd2989e70e077de58a55a4e37d29a897bd690a6eb0';
assert.equal(createHash('sha256').update(readFileSync(resolve(checkout, path))).digest('hex'), registryHash);
const url = (file) => pathToFileURL(resolve(checkout, file)).href;
const moduleText = (source) => 'data:text/javascript,' + encodeURIComponent(source);
const routes = new Map([
  ['@deepseek-ai/cordis', moduleText('export class Context {} export class Service { constructor(ctx) { this.ctx = ctx; } }')],
  ['@deepseek-ai/schemastery', moduleText('export default { object: (shape) => shape, number: () => ({ default: (value) => value }) };')],
  ['@deepseek-ai/dsh-scope', url('packages/core/scope/src/index.ts')],
  ['@deepseek-ai/dsh-util-values', url('packages/util/values/src/index.ts')],
]);
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(routes.get(specifier) ?? specifier, context);
} });
const { SkillRegistry } = await import(url(path));
hook.deregister();

const implementations = {
  preserve: (value) => value,
  magnitude: (value) => Math.abs(value),
  clip: (value) => Math.max(0, value),
  increment: (value) => value + 1,
};
const training = [
  { input: 5, signed: 5, magnitude: 5 },
  { input: -5, signed: -5, magnitude: 5 },
  { input: 0, signed: 0, magnitude: 0 },
];

function fixtureCandidates(repeat) {
  return Array.from({ length: 12 }, (_, index) => {
    const name = `fixture-${repeat}-${index}`;
    const option = (id, contract, implementation, rank) => ({ name, id, contract, implementation, rank });
    return [
      option('primary', 'signed', 'preserve', 20),
      option('alias', 'signed', 'preserve', 10),
      option('narrow', 'signed', 'clip', 5),
      option('specialized', 'magnitude', 'magnitude', 15),
      option('bad', 'signed', 'increment', 1),
    ];
  }).flat();
}

function admit(input, arm) {
  if (arm === 'fixed') return { options: input.filter((option) => option.id === 'primary'), rejected: 0, merged: 0 };
  const cases = arm === 'single-example' ? training.slice(0, 1) : training;
  const options = [];
  const seen = new Set();
  let rejected = 0;
  let merged = 0;
  for (const candidate of input.toSorted((a, b) => a.rank - b.rank)) {
    const outputs = cases.map((item) => implementations[candidate.implementation](item.input));
    if (!outputs.every((value, i) => value === cases[i][candidate.contract])) {
      rejected++;
      continue;
    }
    const signature = JSON.stringify([candidate.name, candidate.contract, outputs]);
    if (arm !== 'single-example' && seen.has(signature)) {
      merged++;
      continue;
    }
    seen.add(signature);
    options.push(candidate);
  }
  return { options, rejected, merged };
}

function mount(options, byContract) {
  const warnings = [];
  const context = {
    logger: { warn: (message) => warnings.push(message) },
    events: { dispatch: () => [] },
    effect(fn) {
      const lifecycle = fn();
      const { value: undo, done } = lifecycle.next();
      assert.equal(done, false);
      assert.equal(lifecycle.next().done, true);
      return undo;
    },
  };
  const registry = new SkillRegistry(context);
  const provider = 'fixture-provider';
  const dispose = registry.registerProvider(() => ({
    name: provider,
    async list(view) {
      return options.filter((item) => !byContract || item.contract === view.cwd).map((item) => ({
        name: item.name, rank: item.rank, description: 'Synthetic arithmetic option.',
        source: provider, provider, locator: item,
      }));
    },
    async get(candidate) {
      return { ...candidate, content: candidate.locator.id };
    },
  }));
  return { registry, dispose, warnings };
}

async function replay(repeat, arm) {
  const input = fixtureCandidates(repeat);
  const { options, rejected, merged } = admit(input, arm);
  const { registry, dispose, warnings } = mount(options, arm === 'verified-contract');
  const count = { proposals: input.length, library_size: options.length, rejected, merged,
    tasks: 0, solved: 0, wrong_contract: 0, selected: {}, duplicate_warnings: 0 };
  for (const contract of ['signed', 'magnitude']) {
    const view = { cwd: contract };
    const visible = await registry.list(view);
    assert.equal(visible.length, 12);
    for (const { name } of visible) {
      const definition = await registry.get(name, view);
      const selected = options.find((item) => item.name === name && item.id === definition.content);
      assert.ok(selected);
      count.selected[selected.id] = (count.selected[selected.id] ?? 0) + 1;
      for (const value of [9 + repeat, -7 - repeat, -2 - repeat]) {
        const expected = contract === 'magnitude' && value < 0 ? -value : value;
        count.tasks++;
        count.solved += implementations[selected.implementation](value) === expected;
        count.wrong_contract += selected.contract !== contract;
      }
    }
  }
  count.duplicate_warnings = warnings.length;
  dispose();
  assert.deepEqual(await registry.list(), []);
  return count;
}

async function experiment(repeat) {
  const arms = {};
  for (const arm of ['fixed', 'single-example', 'verified-name', 'verified-contract']) {
    arms[arm] = await replay(repeat, arm);
  }
  assert.deepEqual(Object.values(arms).map((item) => [item.tasks, item.solved, item.library_size, item.merged]),
    [[72, 48, 12, 0], [72, 24, 48, 0], [72, 48, 24, 12], [72, 72, 24, 12]]);
  return arms;
}

const results = await experiment(0);
assert.deepEqual(await experiment(1), results);
assert.deepEqual(await experiment(2), results);
console.log(JSON.stringify({ revision, registry_sha256: registryHash, repeats: 3, model_calls: 0, results }, null, 2));
