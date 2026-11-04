// Only synthetic numeric strings; exercise pinned original parsing and normalization.
import assert from 'node:assert/strict';
import { parseChartInput, normalizeData } from '/source/src/utils/normalize.ts';
const exponential = parseChartInput('1e3\n2e3');
assert.deepEqual(exponential.headers, ['1e3']);
assert.deepEqual(exponential.rows, [[2000]]);
const ragged = normalizeData(parseChartInput('1 2\n3').rows);
assert.deepEqual(ragged.min, [1, 0]);
const malformed = normalizeData(parseChartInput('1 2\n3 nope').rows);
assert.equal(Number.isNaN(malformed.min[1]), true);
const control = normalizeData(parseChartInput('1\n2').rows);
assert.deepEqual(control.data, [[0], [1]]);
console.log(JSON.stringify({exponential, ragged_min: ragged.min, malformed_min_is_nan: Number.isNaN(malformed.min[1]), control: control.data}));
