#!/usr/bin/env python3
"""Execute pinned SIMURG hash/sketch/SimHash in isolated seeded processes."""
import json
from pathlib import Path
import sys

source = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(source / "src"))
from simurg.core import stable_hash  # noqa: E402
from simurg.signals.sketch import CountMinSketch  # noqa: E402
from simurg.signals.simhash import RollingSimHash  # noqa: E402

TOKENS = ("postgresql", "SQL Server", "повторение", "audit", "alpha",
          "beta", "123456", "🙂", "schema", "schema", "schema", "cache")
SHINGLE = ["schema", "cache", "query", "schema", "cache", "schema",
           "query", "cache", "schema", "vacuum", "schema", "cache"]


def main():
    sketch = CountMinSketch(depth=4, width=256)
    additions = [sketch.add(token) for token in SHINGLE]
    fingerprint = RollingSimHash(window_tokens=8)
    snapshots = []
    for position, token in enumerate(TOKENS):
        fingerprint.push(token)
        if position == 7:
            fingerprint.set_baseline()
        snapshots.append({
            "value": fingerprint.value(), "drift": fingerprint.drift(),
            "baseline": fingerprint.baseline
        })
    result = {
        "stable": {token: {
            "unseeded": stable_hash(token),
            "seeded_1": stable_hash(token, 1),
            "seeded_12345": stable_hash(token, 12345)
        } for token in TOKENS},
        "sketch_cols": {token: sketch._cols(token) for token in set(SHINGLE)},
        "sketch_additions": additions,
        "sketch_estimates": {token: sketch.estimate(token) for token in set(SHINGLE)},
        "simhash_snapshots": snapshots,
        "builtin_hash_control": hash("postgresql"),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
