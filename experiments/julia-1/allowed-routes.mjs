import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const source = resolve(process.argv[2], 'src/sse/services/routingBoundary.js');
const targetHash = '86749093d2cb38dc0aba4a45ccadf95f1cc5d44e7684a6ff82d6c6759421e638';
assert.equal(createHash('sha256').update(readFileSync(source)).digest('hex'), targetHash);
const fixtureDb = 'data:text/javascript,' + encodeURIComponent(`
  export class RoutingCorrelationConflictError extends Error {}
  function unused() { throw new Error('Storage is outside this fixture'); }
  export { unused as beginRoutingRequest, unused as finishRoutingRequest,
    unused as beginRoutingAttempt, unused as finishRoutingAttempt };
`);
const hook = registerHooks({ resolve(specifier, context, next) {
  return next(specifier === '@/lib/db/index.js' ? fixtureDb : specifier, context);
} });
const { createRoutingBoundary, constrainModelStrings } = await import(pathToFileURL(source));
hook.deregister();

const asIdentity = (name) => {
  const [provider, model] = name.split('/');
  return { provider, model };
};
const rows = JSON.parse(readFileSync(0, 'utf8'));
const output = [];
for (const row of rows) {
  const resolveModel = async (name) => row.available.includes(name) ? asIdentity(name) : null;
  const boundary = await createRoutingBoundary({ allowedCandidates: row.allowed.map(asIdentity) }, resolveModel);
  const filtered = await constrainModelStrings(row.available, boundary, resolveModel);
  assert.deepEqual(filtered, row.allowed);
  if (row.selected !== undefined) {
    assert.ok(filtered.includes(row.selected));
    assert.equal(await boundary.beginAttempt(asIdentity(row.selected)), null);
    await assert.rejects(boundary.beginAttempt(asIdentity(row.excluded)), { code: 'NO_ALLOWED_ROUTE' });
  }
  output.push(filtered);
}
console.log(JSON.stringify(output));
