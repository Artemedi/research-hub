// Only classify strings; never execute the represented commands.
import assert from 'node:assert/strict';
import { destructiveReason } from '/source/core/safety.mjs';
const cases = [['git reset --hard', false], ['kubectl delete deployment example', false], ['git push --force', true]];
for (const [command, expected] of cases) {
  const reason = destructiveReason(command);
  assert.equal(Boolean(reason), expected);
  console.log(JSON.stringify({ command, reason }));
}
