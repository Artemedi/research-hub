import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [sourcePath, fixturePath] = process.argv.slice(2);
const source = resolve(sourcePath);
const fixtures = resolve(fixturePath);

registerHooks({
  resolve(specifier, context, next) {
    if (specifier.startsWith('.') && specifier.endsWith('.js')) {
      return next(specifier.slice(0, -3) + '.ts', context);
    }
    return next(specifier, context);
  },
});

const load = (name) => import(pathToFileURL(join(source, 'src/dotnet', name + '.ts')));
const { readManagedPeLayout } = await load('ManagedPeReader');
const { readManagedMetadataLayout } = await load('ManagedMetadataLayout');
const {
  readManagedMetadataInventory,
  readManagedResourceDirectory,
  managedTableRowCounts,
} = await load('ManagedMetadataInventory');
const { readTypeMemberListFacts } = await load('ManagedTypeMemberLists');

function inspect(bytes) {
  const pe = readManagedPeLayout(bytes);
  assert.ok(pe.cli);
  const { rva, size } = pe.cli.metadata;
  const layout = readManagedMetadataLayout(bytes, pe.rvaToOffset(rva, size, 'cli.metadata'), size);
  const issues = [];
  const resourceDirectory = readManagedResourceDirectory(pe, issues);
  const memberLists = readTypeMemberListFacts(bytes, layout);
  const inventory = readManagedMetadataInventory(bytes, layout, resourceDirectory, memberLists);
  assert.deepEqual([...issues, ...inventory.issues], []);
  return { ...inventory, row_counts: managedTableRowCounts(layout) };
}

function select(actual, expected) {
  return Object.fromEntries(Object.keys(expected).map((key) => [key, actual[key]]));
}

const results = [];
for (const [variant, expectedMethodCount] of [['baseline', 1], ['second-method', 2]]) {
  const bytes = readFileSync(join(fixtures, variant, 'out', 'ReaSynthetic.dll'));
  const oracle = JSON.parse(readFileSync(join(fixtures, variant + '.json'), 'utf8'));
  assert.equal(oracle.assembly.name, 'ReaSynthetic');
  assert.equal(oracle.assembly.version, '2.3.4.5');
  assert.equal(oracle.module.name, 'ReaSynthetic.dll');
  assert.equal(oracle.row_counts.TypeDef, 2);
  assert.equal(oracle.row_counts.MethodDef, expectedMethodCount);
  assert.ok(oracle.references.some(({ name }) => name === 'System.Runtime'));
  const checks = [
    'module identity, token and file offset',
    'assembly identity, token and file offset',
    'reference identities, tokens and file offsets',
    'TypeDef and MethodDef row counts',
  ];
  const runs = [];
  for (let repeat = 1; repeat <= 3; repeat++) {
    const actual = inspect(bytes);
    assert.deepEqual(select(actual.module, oracle.module), oracle.module);
    assert.deepEqual(select(actual.assembly, oracle.assembly), oracle.assembly);
    assert.equal(actual.references.length, oracle.references.length);
    assert.deepEqual(actual.references.map((row, i) => select(row, oracle.references[i])), oracle.references);
    assert.deepEqual(select(actual.row_counts, oracle.row_counts), oracle.row_counts);
    runs.push({ repeat, passed: checks.length });
  }
  results.push({
    variant,
    sha256: createHash('sha256').update(bytes).digest('hex'),
    oracle,
    checks,
    runs,
  });
}

console.log(JSON.stringify({
  source_commit: '92f332652d352e60b550567adf2399d83d8ebe78',
  node: process.version,
  platform: process.platform,
  sdk: process.env.REA_FIXTURE_SDK,
  results,
}, null, 2));
