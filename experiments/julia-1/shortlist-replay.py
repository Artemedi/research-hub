"""Exercise pinned Julia narrowing and a pinned 9router allowlist with synthetic scores."""

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType


JULIA_REVISION = "a85b127321d580d65176c89ced8273f305745d85"
ROUTER_REVISION = "d15f5bf3289e50bddda8263cddd239d7078e4ef0"
SOURCE_HASHES = {
    "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c",
    "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206",
}
TARGET_HASH = "86749093d2cb38dc0aba4a45ccadf95f1cc5d44e7684a6ff82d6c6759421e638"
SCENARIOS = ("direct", "same_group", "separate_groups")
CASES_PER_SCENARIO = 20


class FixtureReducer:
    def __init__(self, library):
        assert library is None

    def argmax(self, scores):
        assert len(set(scores)) == len(scores), "The fixture does not specify tie behavior"
        return max(range(len(scores)), key=scores.__getitem__)


def load_julia(root):
    for path, expected in SOURCE_HASHES.items():
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Source digest mismatch: {path}")
    sys.dont_write_bytecode = True
    for name, suffix in (("julia", "julia"), ("julia.router", "julia/router")):
        module = ModuleType(name)
        module.__path__ = [str(root / suffix)]
        sys.modules[name] = module
    native = ModuleType("julia.router.native")
    native.BendReducer = FixtureReducer
    sys.modules[native.__name__] = native
    return importlib.import_module("julia.router.router").Router


def check_boundary(target, rows):
    helper = Path(__file__).with_name("allowed-routes.mjs")
    return json.loads(subprocess.check_output(
        ["node", helper, target], text=True, input=json.dumps(rows),
    ))


class ScoringFixture:
    def logits(self, rows):
        for row in rows:
            options = row["options"]
            state = row["state"]
            scores = {option: -int(option.rsplit("-", 1)[1]) / 20 for option in options}
            gold = state["gold"]
            distractor = state["distractor"]
            if gold in scores:
                scores[gold] = 8
            if distractor in scores:
                if len(options) == 20 and state["size"] > 20:
                    scores[distractor] = 18
                elif gold not in scores:
                    scores[distractor] = 9
            yield [scores[option] for option in options]


def fixture_rows(repeat):
    for group in SCENARIOS:
        for index in range(CASES_PER_SCENARIO):
            # The two tournament cases share the request and IDs, changing only option order.
            size = 8 if group == "direct" else 24
            family = f"fixture-{repeat}-{index}"
            allowed = [f"{family}/model-{n}" for n in range(size)]
            gold, distractor = allowed[:2]
            offset = (index + repeat) % (size - 2)
            fillers = allowed[2 + offset:] + allowed[2:2 + offset]
            if group == "separate_groups":
                allowed = [distractor, *fillers, gold]
            else:
                allowed = [distractor, gold, *fillers]
            excluded = f"{family}/excluded"
            yield group, gold, distractor, {
                "allowed": allowed, "available": [excluded, *allowed], "excluded": excluded,
            }


def experiment(Router, target, repeat):
    fixtures = list(fixture_rows(repeat))
    lists = check_boundary(target, [row[3] for row in fixtures])
    router = Router(ScoringFixture())
    counts = {}
    selections = []
    for (group, gold, distractor, entry), options in zip(fixtures, lists, strict=True):
        assert options == entry["allowed"]
        decision = router.route({
            "state": {"gold": gold, "distractor": distractor, "size": len(options)},
            "question": "Select the fixture route.", "options": options,
        })
        final = [options[index] for index in decision.candidates]
        chosen = options[decision.index]
        assert chosen in final
        assert decision.probability_scope == ("all_options" if group == "direct" else "final_candidates")
        assert (gold in final) == (group != "same_group")
        assert chosen == (distractor if group == "same_group" else gold)
        confidence = decision.probabilities[final.index(chosen)]
        counts.setdefault(group, Counter()).update({
            "cases": 1, "gold_in_final": int(gold in final), "gold_selected": int(gold == chosen),
            "wrong_displayed_as_one": int(gold != chosen and confidence == 1.0),
            "scoring_rows": decision.model_rows, "rounds": decision.rounds,
        })
        selections.append({**entry, "selected": chosen})
    assert check_boundary(target, selections) == lists
    return {group: dict(count) for group, count in counts.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("julia_sources", type=Path)
    parser.add_argument("routing_sources", type=Path)
    args = parser.parse_args()
    Router = load_julia(args.julia_sources.resolve())
    target = args.routing_sources.resolve()
    counts = experiment(Router, target, 0)
    assert experiment(Router, target, 1) == counts
    assert experiment(Router, target, 2) == counts
    print(json.dumps({
        "julia_revision": JULIA_REVISION, "julia_source_sha256": SOURCE_HASHES,
        "target_revision": ROUTER_REVISION, "target_sha256": TARGET_HASH,
        "model_or_provider_calls": 0, "repeats": 3,
        "excluded_route_denials_per_repeat": len(SCENARIOS) * CASES_PER_SCENARIO, "counts": counts,
    }, indent=2))


if __name__ == "__main__":
    main()
