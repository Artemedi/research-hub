"""Synthetic offline checks against pinned SIMURG; no network or model calls."""
import json
from simurg.data.evaluate import _auroc
from simurg.detection.fusion import ConformalEnsemble
from simurg.detection.sentinel import Simurg

scores = [0.5, 0.5, 0.5, 0.5]
labels = [0, 1, 0, 1]
pos = [s for s, label in zip(scores, labels) if label == 1]
neg = [s for s, label in zip(scores, labels) if label == 0]
oracle = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))
actual = _auroc(scores, labels)
print(f"tie AUROC upstream={actual:.2f} oracle={oracle:.2f}")
assert actual == 1.0 and oracle == 0.5
ensemble = ConformalEnsemble().calibrate([0.99] * 50, alpha=0.02)
print(f"clean calibration score=0.99 threshold={ensemble.corrupt_at:.2f} verdict={ensemble.decide(0.99)}")
assert ensemble.corrupt_at == 0.95 and ensemble.decide(0.99) == 'corrupt'
examples = {
    'repeated_ru': 'Анализ показал, что показатель улучшился. Это подтверждено измерениями на тестовом стенде. ' * 12,
    'repeated_sql': 'SELECT customer_id, sum(amount) FROM orders WHERE year=2026 GROUP BY customer_id ORDER BY customer_id;\n' * 12,
    'json': json.dumps({'records': [{'id': i, 'value': 100000 + i, 'active': True} for i in range(40)]}),
    'loop': 'повторяющаяся фраза снова и снова ' * 70,
}
for name, text in examples.items():
    detector = Simurg()
    emitted = 0
    for i in range(0, len(text), 40):
        verdict = detector.feed(text[i:i + 40])
        emitted += len(verdict.released)
        if verdict.state == 'corrupt':
            break
    verdict = detector.finish()
    print(f'{name}: state={verdict.state} emitted={emitted}')
