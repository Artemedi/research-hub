"""Compare three planning schedules on the pinned HTN task tree."""

import argparse
import asyncio
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType


REVISION = "0bccf18d813298e5c2a33961dbf56b907bd8b133"
PACKAGE = "workflows.dynamic_htn_informed_research.htn"
SOURCE_HASHES = {
    "task_tree.py": "f4222053ee02541452c229596098bbe8444201e4fc24a597a7d70d5a681e4f01",
    "task_node.py": "66bbce59ae807a534a2e900f5980786ea14e6150bdc3056ce20e3606a3561d4b",
}
CASES_PER_SCENARIO = 12
STRATEGIES = ("early_guess", "fixed_both", "deferred")


def load_tree(checkout):
    def git(*args):
        return subprocess.check_output(["git", "-C", checkout, *args], text=True).strip()

    if git("rev-parse", "HEAD") != REVISION or git("status", "--porcelain", "-uno"):
        raise ValueError("Expected a clean checkout at the pinned revision")
    directory = checkout.joinpath(*PACKAGE.split("."))
    for name, expected in SOURCE_HASHES.items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Source digest mismatch: {name}")
    # Load only the two tree modules. Package initializers mount runtime workflows.
    sys.dont_write_bytecode = True
    for depth in range(1, 4):
        parts = PACKAGE.split(".")[:depth]
        module = ModuleType(".".join(parts))
        module.__path__ = [str(checkout.joinpath(*parts))]
        sys.modules[module.__name__] = module
    return importlib.import_module(f"{PACKAGE}.task_tree")


def setup(htn):
    node = htn.HTNTaskNode

    def collect(root, parent, children):
        outputs = {child.id: child.result_summary for child in children}
        if parent.id == root.id:
            return outputs["calculate"]
        route = tree.get_node("discover").result_summary
        return outputs[route]

    root = node(id="root", needs_decomposition=True)
    tree = htn.HTNTree("root", {"root": root}, summarizer=collect)
    tree.decompose("root", [
        node(id="discover"),
        node(id="calculate", depends_on=["discover"], needs_decomposition=True),
    ])
    return tree


async def replay(htn, strategy, scenario, index):
    tree = setup(htn)
    candidate = ("add",) if strategy == "early_guess" else ("add", "subtract")
    if strategy == "deferred":
        candidate = ()
    counts = Counter(proposals=int(bool(candidate)))
    assert [node.id for node in tree.ready_for_execution()] == ["discover"]
    assert tree.ready_for_planning() == []

    tree.mark_running("discover")
    discovery = tree.get_node("discover")
    if scenario == "failed":
        tree.mark_failed(discovery.id)
    else:
        outcome = htn.HTNCompletionOutcome
        if scenario == "unresolved":
            await tree.mark_completed(discovery.id, "unknown", completion_outcome=outcome.EXHAUSTED_UNRESOLVED)
        else:
            await tree.mark_completed(discovery.id, "add" if scenario == "guess_matches" else "subtract")

    ready = [node.id for node in tree.ready_for_planning()]
    assert ready == ([] if scenario == "failed" else ["calculate"])
    counts["tree_branch_ready"] += bool(ready)
    # The compared schedules share this semantic check before committing a draft.
    if discovery.completion_outcome is not htn.HTNCompletionOutcome.RESOLVED:
        counts["discarded"] += bool(candidate)
        assert not tree.get_node("calculate").children
        assert tree.root().status is htn.HTNTaskStatus.PENDING
        return counts, None

    route = discovery.result_summary
    if route not in candidate:
        counts["discarded"] += bool(candidate)
        counts["replans"] += bool(candidate)
        counts["proposals"] += 1
        candidate = (route,)
    tree.decompose(ready[0], [htn.HTNTaskNode(id=operation) for operation in candidate])
    assert not tree.validate()
    operands = (index * 3 + 31, index + 2)
    operations = {"add": sum, "subtract": lambda pair: pair[0] - pair[1]}
    for leaf in tree.ready_for_execution():
        tree.mark_running(leaf.id)
        await tree.mark_completed(leaf.id, str(operations[leaf.id](operands)))
        counts["calculation_leaves"] += 1

    assert tree.root().status is htn.HTNTaskStatus.COMPLETED
    assert tree.root().completion_outcome is htn.HTNCompletionOutcome.RESOLVED
    return counts, tree.root().result_summary


async def run(htn):
    results = {}
    expected_work = {
        "early_guess": [(1, 0, 0, 1), (2, 1, 1, 1), (1, 1, 0, 0), (1, 1, 0, 0)],
        "fixed_both": [(1, 0, 0, 2), (1, 0, 0, 2), (1, 1, 0, 0), (1, 1, 0, 0)],
        "deferred": [(1, 0, 0, 1), (1, 0, 0, 1), (0, 0, 0, 0), (0, 0, 0, 0)],
    }
    fields = ("proposals", "discarded", "replans", "calculation_leaves")
    scenarios = ("guess_matches", "guess_changes", "failed", "unresolved")
    for strategy in STRATEGIES:
        results[strategy] = {}
        for scenario, expected in zip(scenarios, expected_work[strategy], strict=True):
            aggregate = Counter(dict.fromkeys((*fields, "tree_branch_ready", "roots_resolved"), 0))
            for index in range(CASES_PER_SCENARIO):
                counts, result = await replay(htn, strategy, scenario, index)
                expected_result = {
                    "guess_matches": str(4 * index + 33),
                    "guess_changes": str(2 * index + 29),
                }.get(scenario)
                assert result == expected_result, (strategy, scenario, index, result)
                assert tuple(counts[field] for field in fields) == expected
                aggregate.update(counts)
                aggregate["roots_resolved"] += result is not None
            results[strategy][scenario] = dict(aggregate)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    htn = load_tree(parser.parse_args().checkout.resolve())
    results = asyncio.run(run(htn))
    assert asyncio.run(run(htn)) == results
    assert asyncio.run(run(htn)) == results
    print(json.dumps({
        "revision": REVISION, "source_sha256": SOURCE_HASHES,
        "cases_per_scenario": CASES_PER_SCENARIO, "repeats": 3,
        "model_or_provider_calls": 0, "results": results,
    }, indent=2))


if __name__ == "__main__":
    main()
