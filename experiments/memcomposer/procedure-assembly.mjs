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
const promptSource = 'packages/core/system-prompt/src/index.ts';
const promptHash = '2cd5cc40c006e70b8fb5f50ad459213623f9f7f86e12ad3fc402cefca0ece577';
assert.equal(createHash('sha256').update(readFileSync(resolve(checkout, promptSource))).digest('hex'), promptHash);

const url = path => pathToFileURL(resolve(checkout, path)).href;
const cordis = 'vendor/cordis/src/index.ts';
const routes = new Map(Object.entries({
  '@deepseek-ai/cordis': cordis,
  '@deepseek-ai/cosmokit': 'vendor/cosmokit/src/index.ts',
  '@deepseek-ai/schemastery': 'vendor/schemastery/src/index.ts',
  '@deepseek-ai/dsh-scope': 'packages/core/scope/src/index.ts',
}));
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(routes.has(specifier) ? url(routes.get(specifier)) : specifier, context);
} });
const { Context } = await import(url(cordis));
const { default: SystemPrompt, renderContextSections, joinContextSections, renderPrompt } = await import(url(promptSource));
hook.deregister();

const steps = ['prepare', 'decorate', 'pack'];
const outputByStep = { prepare: 'blank', decorate: 'decorated', pack: 'packed' };
const scenarios = {
  single: { target: 'blank', length: 1 },
  pair: { target: 'decorated', length: 2 },
  triple: { target: 'packed', length: 3 },
  absent: { target: null, length: 0 },
};
const variants = ['no_memory', 'fixed_top3', 'filtered_rank', 'filtered_dependencies'];

function fixture(seed, scenario) {
  const { length, target } = scenarios[scenario];
  const request = { family: `craft-${String(seed).padStart(2, '0')}`, edition: 2, target };
  const memory = (id, step, family = request.family, edition = request.edition) => ({
    id, family, edition, step, note: `Archived example: apply ${step} to a paper model.`,
  });
  const usable = steps.slice(0, length).map(step => memory(step, step));
  if (seed % 2 === 0) usable.reverse();
  const candidates = [memory('old', 'prepare', request.family, 1)];
  if (usable[0]) candidates.push(usable[0]);
  candidates.push(memory('foreign', 'decorate', 'another-craft'));
  candidates.push(...usable.slice(1), memory('foreign-pack', 'pack', 'another-craft'));
  return { request, candidates };
}

function select(mode, request, candidates) {
  if (mode === 'no_memory') return [];
  if (mode === 'fixed_top3') return candidates.slice(0, 3);
  const matching = candidates.filter(item => item.family === request.family && item.edition === request.edition);
  if (mode === 'filtered_dependencies') matching.sort((a, b) => steps.indexOf(a.step) - steps.indexOf(b.step));
  return matching;
}

function runProcedure(request, supplied) {
  let stage = 0;
  for (const memory of supplied) {
    if (memory.family !== request.family || memory.edition !== request.edition) continue;
    if (stage === 0 && memory.step === 'prepare') stage = 1;
    else if (stage === 1 && memory.step === 'decorate') stage = 2;
    else if (stage === 2 && memory.step === 'pack') stage = 3;
  }
  return outputByStep[steps[stage - 1]] ?? null;
}

function expectedOutput(mode, target, length, reversed) {
  if (length === 0 || mode === 'no_memory') return null;
  if (mode === 'fixed_top3') return reversed && length > 1 ? null : 'blank';
  if (mode === 'filtered_rank' && reversed && length > 1) return 'blank';
  return target;
}

const ctx = new Context();
const plugin = await ctx.plugin(SystemPrompt);
const baseline = renderPrompt(await ctx.systemPrompt.assemble());
async function render(selected) {
  // Register in reverse so the test exercises DSH's explicit numeric order.
  const disposers = selected.map((item, index) => ({ item, index })).reverse().map(({ item, index }) =>
    ctx.systemPrompt.context({ name: `memory:${item.id}`, order: 100 + index, text: JSON.stringify(item) }));
  try {
    const assembly = await ctx.systemPrompt.assemble();
    assert.equal(renderPrompt(assembly), baseline);
    const sections = renderContextSections(assembly);
    assert.deepEqual(sections.map(section => section.name), selected.map(item => `memory:${item.id}`));
    const supplied = sections.map(section => JSON.parse(section.text));
    assert.deepEqual(supplied, selected);
    return { supplied, bytes: Buffer.byteLength(joinContextSections(sections), 'utf8') };
  } finally {
    for (const dispose of disposers) dispose();
  }
}

const repeats = [];
try {
  for (let repeat = 0; repeat < 3; repeat++) {
    const outcomes = {};
    for (const [scenario, { target, length }] of Object.entries(scenarios)) {
      outcomes[scenario] = {};
      for (const mode of variants) {
        const counts = { cases: 0, completed: 0, empty_when_absent: 0, delivered_items: 0, irrelevant_items: 0, context_utf8_bytes: 0 };
        for (let seed = repeat * 12 + 1; seed <= (repeat + 1) * 12; seed++) {
          const { request, candidates } = fixture(seed, scenario);
          const { supplied, bytes } = await render(select(mode, request, candidates));
          const expectedCount = mode === 'fixed_top3' ? 3 : mode === 'no_memory' ? 0 : length;
          assert.equal(supplied.length, expectedCount);
          const result = runProcedure(request, supplied);
          assert.equal(result, expectedOutput(mode, target, length, seed % 2 === 0));
          const irrelevant = supplied.filter(item => item.family !== request.family || item.edition !== request.edition).length;
          assert.equal(irrelevant, mode === 'fixed_top3' ? 3 - Number(length > 0) : 0);
          counts.cases += 1;
          counts.completed += Number(result !== null && result === target);
          counts.empty_when_absent += Number(target === null && supplied.length === 0);
          counts.delivered_items += supplied.length;
          counts.irrelevant_items += irrelevant;
          counts.context_utf8_bytes += bytes;
        }
        outcomes[scenario][mode] = counts;
      }
    }
    assert.deepEqual(renderContextSections(await ctx.systemPrompt.assemble()), []);
    if (repeat > 0) assert.deepEqual(outcomes, repeats[0]);
    repeats.push(outcomes);
  }
} finally {
  await plugin.dispose();
}

console.log(JSON.stringify({
  date: '2026-11-27',
  target_revision: revision,
  source_sha256: promptHash,
  node_version: process.versions.node,
  cases_per_repeat: 48,
  repeats,
}, null, 2));
