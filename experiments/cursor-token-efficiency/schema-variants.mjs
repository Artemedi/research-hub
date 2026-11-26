import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const source = resolve(process.argv[2], 'packages/llm/token-meter/src/estimate.ts');
const { estimateToolsTokens } = await import(pathToFileURL(source));
const input = JSON.parse(readFileSync(0, 'utf8'));
const documents = input.map(({ id, tools, messages }) => {
  return {
    id,
    estimate_schema_tokens: estimateToolsTokens({ tools }),
    schemas: JSON.stringify(tools),
    request: JSON.stringify({ tools, messages }),
  };
});
console.log(JSON.stringify({ node: process.version, documents }));
