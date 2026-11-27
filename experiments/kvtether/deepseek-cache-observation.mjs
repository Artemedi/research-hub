import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const revision = 'b6a1635b1200071754e2871b9d9453368e6daf23';
const checkout = resolve(process.argv[2]);
const dependency = resolve(process.argv[3]);
const git = (...args) => execFileSync('git', ['-C', checkout, ...args], { encoding: 'utf8' }).trim();
assert.equal(git('rev-parse', 'HEAD'), revision);
assert.equal(git('status', '--porcelain', '-uno'), '');
const url = (path) => pathToFileURL(resolve(checkout, path)).href;
const source = 'packages/llm/llm-deepseek/src';
const hashes = {
  'serialize.ts': '36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162',
  'translate.ts': '66e8b1f96a90404d4e5ca67fc85b9e37a96bbee78ed52521e7b8fdc3f336ba32',
  'sse.ts': '621f53b6641a9fb5c652a755f477045f0616f42d5a559b9bea4754836552d705',
  'adapter.ts': 'bd97f822363f45fae28e4aa1b7a4412305865979e22889c6c771989dcee87a32',
};
for (const [file, hash] of Object.entries(hashes)) {
  assert.equal(createHash('sha256').update(readFileSync(resolve(checkout, source, file))).digest('hex'), hash);
}

const manifest = JSON.parse(readFileSync(resolve(dependency, 'package.json'), 'utf8'));
assert.equal(manifest.name, 'eventsource-parser');
assert.equal(manifest.version, '3.1.0');
const parserUrl = pathToFileURL(resolve(dependency, manifest.exports['./stream'].import)).href;
const llmBridge = [
  `export { contentHasImage, offloadedImageText, offloadRequestImagesWithPolicy, requestImageHandleText } from ${JSON.stringify(url('packages/llm/llm/src/content.ts'))};`,
  `export { EMPTY_RESPONSE_CODE } from ${JSON.stringify(url('packages/llm/llm/src/error.ts'))};`,
  'export class LlmError extends Error { constructor(message, code) { super(message); this.code = code; } }',
].join('\n');
const routes = new Map([
  ['eventsource-parser/stream', parserUrl],
  ['@deepseek-ai/dsh-llm', 'data:text/javascript,' + encodeURIComponent(llmBridge)],
  ['@deepseek-ai/dsh-util-values', url('packages/util/values/src/index.ts')],
  ['@deepseek-ai/dsh-brand', url('packages/util/brand/src/index.ts')],
]);
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(routes.get(specifier) ?? specifier, context);
} });
const { serializeRequest } = await import(url(`${source}/serialize.ts`));
const { parseSse } = await import(url(`${source}/sse.ts`));
const { translate } = await import(url(`${source}/translate.ts`));
hook.deregister();

async function observe(usage, placement) {
  const completion = { choices: [{ index: 0, delta: { content: 'Fixture answer.' }, finish_reason: 'stop' }] };
  const counters = { choices: [], usage: { ...usage, fixture_placement: placement } };
  const raw = `data: ${JSON.stringify(completion)}\n\ndata: ${JSON.stringify(counters)}\n\ndata: [DONE]\n\n`;
  const observed = [];
  for await (const event of translate(parseSse(new Response(raw).body))) observed.push(event);
  return { raw, observed };
}

function usageFrom(form, prompt, output, hit) {
  const counters = { prompt_tokens: prompt, completion_tokens: output, total_tokens: prompt + output };
  if (form === 'native') {
    return { ...counters, prompt_cache_hit_tokens: hit, prompt_cache_miss_tokens: prompt - hit };
  }
  if (form === 'compatible') return { ...counters, prompt_tokens_details: { cached_tokens: hit } };
  return { ...counters, prompt_tokens_details: { cached_tokens: hit }, prompt_cache_hit_tokens: hit - 1 };
}

const forms = ['native', 'compatible', 'both'];
const casesPerForm = 16;
async function replay(repeat) {
  const result = {};
  for (const form of forms) {
    const counts = { pairs: 0, identical_requests: 0, identical_events: 0, counter_controls: 0, text_controls: 0 };
    for (let i = 0; i < casesPerForm; i++) {
      const sequence = i + repeat * casesPerForm;
      const placementA = { id: `fixture-${sequence}`, tier: 'device', retained_after_request: true };
      const placementB = { ...placementA, tier: 'host', retained_after_request: false };
      const options = {
        model: 'fixture-model',
        system: 'Return the authored fixture answer.',
        messages: [{ role: 'user', content: [{ type: 'text', text: `Fixture ${sequence}` }] }],
      };
      const wire = serializeRequest(options);
      const requestA = serializeRequest({ ...options, fixturePlacementIntent: placementA });
      const requestB = serializeRequest({ ...options, fixturePlacementIntent: placementB });
      assert.equal(JSON.stringify(requestA), JSON.stringify(wire));
      assert.equal(JSON.stringify(requestB), JSON.stringify(wire));
      assert.deepEqual(wire.stream_options, { include_usage: true });
      assert.notDeepEqual(serializeRequest({ ...options, system: 'Different fixture text.' }), wire);

      const prompt = 128 + sequence;
      const output = 5 + i % 3;
      const hit = 32 + i;
      const usage = usageFrom(form, prompt, output, hit);
      const left = await observe(usage, placementA);
      const right = await observe(usage, placementB);
      assert.notEqual(left.raw, right.raw);
      assert.deepEqual(left.observed, right.observed);
      assert.equal(left.observed.at(-1).reason.kind, 'stop');
      const baselineUsage = left.observed.find((event) => event.type === 'usage').usage;
      assert.deepEqual(baselineUsage, {
        inputTokens: prompt - hit, outputTokens: output, totalTokens: prompt + output, cacheReadTokens: hit,
      });
      const changed = await observe(usageFrom(form, prompt, output, hit + 1), placementA);
      assert.deepEqual(changed.observed.find((event) => event.type === 'usage').usage, {
        ...baselineUsage, inputTokens: prompt - hit - 1, cacheReadTokens: hit + 1,
      });
      counts.pairs++;
      counts.identical_requests++;
      counts.identical_events++;
      counts.counter_controls++;
      counts.text_controls++;
    }
    result[form] = counts;
  }
  return result;
}

const counts = await replay(0);
assert.deepEqual(await replay(1), counts);
assert.deepEqual(await replay(2), counts);
console.log(JSON.stringify({ revision, source_sha256: hashes, eventsource_parser: manifest.version,
  cases_per_form: casesPerForm, repeats: 3, provider_or_model_calls: 0, counts }, null, 2));
