import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const source = resolve(process.argv[2]);
const hashes = {
  'svg.ts': '81b05c1000e389b80e11a87f09e74e889a899462e14cd322e9f259acb431db7e',
  'normalize.ts': '98adfcf1ebb0aa7793c194b1eb5e8e484004c52288fad0a692bee6c21503a438',
};
for (const [name, expected] of Object.entries(hashes)) {
  const bytes = readFileSync(join(source, 'src', 'utils', name));
  assert.equal(createHash('sha256').update(bytes).digest('hex'), expected, name);
}
registerHooks({
  resolve(specifier, context, next) {
    const local = specifier === './chart-annotations.js' || specifier === './normalize.js';
    return next(local ? specifier.slice(0, -3) + '.ts' : specifier, context);
  },
});
const utility = (name) => import(pathToFileURL(join(source, 'src', 'utils', name)));
const { normalizeData } = await utility('normalize.ts');
const { renderSvg } = await utility('svg.ts');
const cases = JSON.parse(readFileSync(0, 'utf8'));
const reports = cases.map(({ id, rows, x, x_label, y_label }) => {
  const svg = renderSvg({
    normalized: normalizeData(rows),
    options: {
      mode: 'lines', width: 320, height: 120, showDataLabels: true,
      xLabels: x.map(String), xAxisLabel: x_label, yAxisLabel: y_label,
      seriesLabels: ['First series', 'Second series'],
    },
  });
  return { id, svg };
});
console.log(JSON.stringify({ node: process.version, reports }));
