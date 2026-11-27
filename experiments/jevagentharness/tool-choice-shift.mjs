import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const revision = 'b6a1635b1200071754e2871b9d9453368e6daf23';
const authorRevision = 'f2932199e1ef1d9f089b51d39430c87be0f560b5';
const authorRuleSha256 = '11f508b265af89c49ae3a55da2db567b661a5d4386e2164feb2c5834c53069e2';
const root = resolve(process.argv[2]);
const git = (...args) => execFileSync('git', ['-C', root, ...args], { encoding: 'utf8' }).trim();
assert.equal(git('rev-parse', 'HEAD'), revision);
assert.equal(git('status', '--porcelain', '-uno'), '');
const url = (path) => pathToFileURL(resolve(root, path)).href;
const schemaPath = 'packages/core/tools/src/schema.ts';
const hashes = {
  [schemaPath]: 'be6e4b3fa18fe633c6c83ed4f9072da5a2a203f64bf0b70c9066fd58b0e2c897',
  'packages/core/tools/src/json-schema.ts': '13deffdfd34539e23706b0fde235991da45b2f07c5c18dbbf3ca734c1da0c788',
};
for (const [path, hash] of Object.entries(hashes)) {
  assert.equal(createHash('sha256').update(readFileSync(resolve(root, path))).digest('hex'), hash);
}
const routes = new Map([
  ['@deepseek-ai/dsh-llm', url('packages/llm/llm/src/error.ts')],
  ['@deepseek-ai/dsh-util-values', url('packages/util/values/src/index.ts')],
]);
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(routes.get(specifier) ?? specifier, context);
} });
const { validateArgs } = await import(url(schemaPath));
hook.deregister();

const number = { type: 'integer', required: true };
const tools = {
  sum: { schema: { left: number, right: number }, run: (_, { left, right }) => left + right },
  product: { schema: { left: number, right: number }, run: (_, { left, right }) => left * right },
  scale: { schema: { factor: number }, run: (value, { factor }) => value * factor },
  format: {
    schema: { label: { type: 'string', enum: ['receipt', 'preview'], required: true } },
    run: (value, { label }) => `${label}:${value}`,
  },
};
const calibrationProfile = 'fixture-v1';
const candidates = [0, 0.55, 0.72, 0.81, 0.87, 0.91, 0.94, 0.95, 0.97, 0.99, 1];
const fixtureCount = 48;
const folds = ['calibration', 'matched', 'catalog_shift', 'silent_shift'];

function fixtures(fold, repeat) {
  const block = folds.indexOf(fold);
  const shifted = block >= 2;
  return Array.from({ length: fixtureCount }, (_, index) => {
    const identity = repeat * 192 + block * fixtureCount + index;
    const shape = (index + repeat) % 12;
    const left = identity + 11;
    const right = (identity % 7) + 3;
    const factor = identity % 2 + 2;
    const operation = identity % 2 ? 'sum' : 'product';
    const reference = [
      { tool: operation, args: { left, right } },
      { tool: 'scale', args: { factor } },
      { tool: 'format', args: { label: 'receipt' } },
    ];
    const proposals = reference.map((action, i) => ({ ...structuredClone(action), score: [0.94, 0.87, 0.91][i] }));
    if (shape === 0 || (shifted && [1, 2].includes(shape))) {
      proposals[0].tool = operation === 'product' ? 'sum' : 'product';
      proposals[0].score = shape === 0 ? 0.55 : 0.97;
    }
    if (shape === 3) Object.assign(proposals[1], { args: { factor: String(factor) }, score: 0.99 });
    if (shape === 4) Object.assign(proposals[1], { args: { factor: factor + 1 }, score: 0.72 });
    if (shape === 5) Object.assign(proposals[2], { args: { label: 1 }, score: 0.99 });
    if (shape === 6 || (shifted && shape === 7)) {
      Object.assign(proposals[2], { args: { label: 'preview' }, score: shape === 6 ? 0.81 : 0.95 });
    }
    if (shape === 8) Object.assign(proposals[0], { tool: 'unavailable-fixture-tool', score: 0.99 });
    return {
      profile: fold === 'catalog_shift' ? 'fixture-v2' : calibrationProfile,
      reference, proposals,
      expected: `receipt:${factor * (operation === 'sum' ? left + right : left * right)}`,
    };
  });
}

function run(tasks, threshold, requireProfile = false) {
  const counts = {
    tasks: tasks.length, decisions: 0, tasks_solved: 0, delegated: 0, fallback: 0,
    schema_or_registry_rejections: 0, profile_deferrals: 0, wrong_delegated: 0,
  };
  for (const task of tasks) {
    let result;
    for (const [index, proposal] of task.proposals.entries()) {
      const reference = task.reference[index];
      let action = reference;
      counts.decisions++;
      if (proposal.score >= threshold) {
        if (requireProfile && task.profile !== calibrationProfile) {
          counts.profile_deferrals++;
        } else if (!Object.hasOwn(tools, proposal.tool)
          || validateArgs(tools[proposal.tool].schema, proposal.args).length) {
          counts.schema_or_registry_rejections++;
        } else {
          action = proposal;
          counts.delegated++;
          counts.wrong_delegated += action.tool !== reference.tool
            || JSON.stringify(action.args) !== JSON.stringify(reference.args);
        }
      }
      if (action === reference) counts.fallback++;
      assert.deepEqual(validateArgs(tools[action.tool].schema, action.args), []);
      result = tools[action.tool].run(result, action.args);
    }
    counts.tasks_solved += result === task.expected;
  }
  return counts;
}

function fit(tasks) {
  const scored = candidates.map((threshold) => ({ threshold, ...run(tasks, threshold) }));
  return scored.filter((row) => row.tasks_solved === row.tasks)
    .reduce((best, row) => row.delegated > best.delegated ? row : best);
}

function experiment(repeat) {
  const calibration = fit(fixtures('calibration', repeat));
  assert.equal(calibration.threshold, 0.87);
  assert.equal(calibration.tasks_solved, fixtureCount);
  const holdouts = {};
  for (const fold of folds.slice(1)) {
    const tasks = fixtures(fold, repeat);
    const reference = run(tasks, Infinity);
    const noThreshold = run(tasks, 0);
    const fitted = run(tasks, calibration.threshold);
    const knownProfile = run(tasks, calibration.threshold, true);
    assert.equal(reference.tasks_solved, fixtureCount);
    assert.equal(noThreshold.tasks_solved, fold === 'matched' ? 36 : 24);
    assert.equal(fitted.tasks_solved, fold === 'matched' ? 48 : 36);
    assert.equal(fitted.schema_or_registry_rejections, 12);
    assert.equal(knownProfile.tasks_solved, fold === 'silent_shift' ? 36 : 48);
    assert.equal(knownProfile.delegated, fold === 'catalog_shift' ? 0 : fitted.delegated);
    holdouts[fold] = { reference, no_threshold: noThreshold, fitted, known_profile_only: knownProfile };
  }
  return { calibration, holdouts };
}

const result = experiment(0);
assert.deepEqual(experiment(1), result);
assert.deepEqual(experiment(2), result);
console.log(JSON.stringify({ author_revision: authorRevision, author_rule_sha256: authorRuleSha256,
  target_revision: revision, target_source_sha256: hashes, model_calls: 0, repeats: 3, ...result }, null, 2));
