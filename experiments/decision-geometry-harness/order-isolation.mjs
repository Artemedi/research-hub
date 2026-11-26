import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const commit = 'b6a1635b1200071754e2871b9d9453368e6daf23';
const source = resolve(process.argv[2]);
const git = (...args) => execFileSync('git', ['-C', source, ...args], { encoding: 'utf8' }).trim();
assert.equal(git('rev-parse', 'HEAD'), commit);
assert.equal(git('status', '--porcelain', '--untracked-files=no'), '');
const url = (path) => pathToFileURL(resolve(source, path)).href;
const digest = (value) => createHash('sha256').update(value).digest('hex');
const serializerPath = 'packages/llm/llm-deepseek/src/serialize.ts';
const headerPath = 'packages/core/session/src/request-header.ts';
assert.equal(digest(readFileSync(resolve(source, serializerPath))),
  '36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162');
assert.equal(digest(readFileSync(resolve(source, headerPath))),
  'abd8ef57c34ad6ddbc21ba83398092f6aff64ac5c0f38efb353cebb04f654ad4');

const bridge = [
  `export { contentHasImage, offloadedImageText, offloadRequestImagesWithPolicy, requestImageHandleText } from ${JSON.stringify(url('packages/llm/llm/src/content.ts'))};`,
  `export { callConfigEquals } from ${JSON.stringify(url('packages/llm/llm/src/call-config.ts'))};`,
  "export class LlmError extends Error { constructor(message) { throw new Error('Text-only test encountered a provider-error path', { cause: message }); } }",
].join('\n');
const routes = new Map([
  ['@deepseek-ai/dsh-llm', 'data:text/javascript,' + encodeURIComponent(bridge)],
  ['@deepseek-ai/dsh-util-values', url('packages/util/values/src/index.ts')],
]);
registerHooks({ resolve(specifier, context, next) {
  return next(routes.get(specifier) ?? specifier, context);
} });
const { serializeRequest } = await import(url(serializerPath));
const { canonicalHeader, headerEquals, foldRequestHeader } = await import(url(headerPath));

const fields = () => ({ period: { type: 'string' }, limit: { type: 'integer' } });
const names = ['fixture_lookup', 'fixture_summary', 'fixture_count'];
const schemas = names.map((name) => ({
  name, description: 'A synthetic data lookup.',
  parameters: { type: 'object', properties: fields(), required: ['period'], additionalProperties: false },
}));
const config = { provider: 'fixture', model: 'fixture-model' };
const header = (tools) => canonicalHeader({ config, tools });
const variants = {
  tools_reversed: [...schemas].reverse(),
  properties_reversed: schemas.map(({ parameters, ...tool }) => ({
    ...tool, parameters: { ...parameters, properties: Object.fromEntries(
      Object.entries(parameters.properties).reverse(),
    ) },
  })),
  changed_required: schemas.map((tool, index) => index === 0 ? {
    ...tool, parameters: { ...tool.parameters, required: ['period', 'limit'] },
  } : tool),
};

function normalizedSchemas(wire) {
  return wire.tools.map(({ function: { name, description, parameters } }) => ({
    name, description,
    properties: Object.entries(parameters.properties).sort(([a], [b]) => a.localeCompare(b)),
    required: [...parameters.required].sort(),
    type: parameters.type,
    additionalProperties: parameters.additionalProperties,
  })).sort((a, b) => a.name.localeCompare(b.name));
}

function linked(messages) {
  const ids = messages.flatMap((message) => message.tool_calls?.map(({ id }) => id) ?? []);
  const results = messages.filter(({ role }) => role === 'tool').map(({ tool_call_id }) => tool_call_id);
  return ids.length === 2 && new Set(ids).size === 2
    && results.length === 2 && ids.every((id, i) => id === results[i]);
}

function run() {
  const records = [];
  for (let index = 0; index < 60; index++) {
    const calls = [index % 3, (index + 1) % 3].map((slot, order) => ({
      type: 'tool-call', id: `fixture-${index}-${order}`, name: names[slot],
      arguments: JSON.stringify({ period: `sampling-${index}`, limit: order + 1 }),
    }));
    const toolResults = calls.map(({ id }, order) => ({
      type: 'tool-result', toolCallId: id,
      content: [{ type: 'text', text: `Test observation ${index}.${order}` }],
    }));
    const messages = [
      { role: 'user', content: [{ type: 'text', text: `Synthetic task ${index}` }] },
      { role: 'assistant', content: calls },
      { role: 'user', content: toolResults },
    ];
    const wire = (tools, history = messages) => serializeRequest({
      model: config.model, system: 'Use the fixture observations.', tools, messages: history,
    });
    const control = wire(schemas);
    assert.ok(linked(control.messages));
    assert.equal(headerEquals(header(schemas), header(structuredClone(schemas))), true);
    const results = {};
    for (const [name, tools] of Object.entries(variants)) {
      const changed = wire(tools);
      assert.deepEqual(changed.messages, control.messages);
      assert.notEqual(JSON.stringify(changed), JSON.stringify(control));
      assert.equal(headerEquals(header(schemas), header(tools)), false);
      const restored = foldRequestHeader([
        { type: 'request/header', data: { header: header(schemas) } },
        { type: 'request/header', data: { header: header(tools) } },
      ]);
      assert.equal(headerEquals(restored, header(tools)), true);
      assert.equal(headerEquals(restored, header(schemas)), false);
      if (name === 'changed_required') {
        assert.notDeepEqual(normalizedSchemas(control), normalizedSchemas(changed));
      } else {
        assert.deepEqual(normalizedSchemas(control), normalizedSchemas(changed));
      }
      results[name] = digest(JSON.stringify(changed));
    }
    const bad = structuredClone(messages);
    bad[2].content[0].toolCallId = 'unrelated-fixture-id';
    const badWire = wire(schemas, bad);
    assert.equal(linked(badWire.messages), false);
    records.push({ case: index, baseline: digest(JSON.stringify(control)),
      permutations: results, bad_link_detected_by_oracle: true });
  }
  return records;
}

const records = run();
assert.deepEqual(run(), records);
assert.deepEqual(run(), records);
console.log(JSON.stringify({
  commit, node: process.version, cases_per_repeat: records.length, repeats: 3,
  provider_requests: 0, records,
}, null, 2));
