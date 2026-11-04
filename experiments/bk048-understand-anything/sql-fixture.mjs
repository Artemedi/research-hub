// Synthetic SQL strings only; imports the pinned original parser, never executes SQL.
import assert from 'node:assert/strict';
import { SQLParser } from '/source/sql-parser.ts';
const parser = new SQLParser();
const examples = [
  ['CREATE TABLE dbo.users (id INT);', ['dbo']],
  ['CREATE TABLE [dbo].[users] (id INT);', []],
  ['-- CREATE TABLE fake (id INT);\nCREATE TABLE real (id INT);', ['fake', 'real']],
  ['CREATE TABLE users (id INT);', ['users']],
];
for (const [sql, expected] of examples) {
  const actual = parser.analyzeFile('fixture.sql', sql).definitions.map(d => d.name);
  assert.deepEqual(actual, expected);
  console.log(JSON.stringify({sql, definitions: actual}));
}
