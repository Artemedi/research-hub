import assert from 'node:assert/strict';
import { scanStructuredPii } from '/source/common/sensitive.ts';
const cases = [
  ['synthetic_email', 'patient@example.invalid', ['email']],
  ['synthetic_medical', 'Пациент Тестовый Иван: диагноз вымышленный, запись учебная.', []],
  ['clean', 'General technical note.', []],
];
for (const [name, text, expected] of cases) {
  const categories = scanStructuredPii(text).map(match => match.category);
  assert.deepEqual(categories, expected);
  console.log(name, JSON.stringify(categories));
}
