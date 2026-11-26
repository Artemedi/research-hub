"""Exercise the pinned Daedalus pool with authored rules and held-out state checks."""
import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

COMMIT = "2f78c7f9343926e2088a88907d61571079ec411e"
TASKS = (
    ("ready", True, "staged"),
    ("ready", False, "waiting"),
    ("blocked", True, "escalated"),
    ("complete", True, "kept"),
)
RULES = {
    "ready_always": ("ready", None, "stage"),
    "ready_checked": ("ready", True, "stage"),
    "blocked_escalate": ("blocked", None, "escalate"),
    "complete_keep": ("complete", None, "keep"),
    "complete_reopen": ("complete", None, "escalate"),
}


@dataclass(frozen=True)
class Exercise:
    ident: str
    status: str
    checklist: bool
    expected: str


def load(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Use a clean Daedalus checkout at " + COMMIT)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(
        "pinned_daedalus_pool", root / "daedalus/core/memory/pool.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.MemoryPool, module.MemoryItem


def solve(task, rule_ids):
    """Apply the first matching authored rule, else use the cautious baseline."""
    for ident in rule_ids:
        status, checklist, action = RULES[ident]
        if task.status == status and (checklist is None or checklist == task.checklist):
            return action
    return "stage" if task.status == "ready" and task.checklist else "wait"


def evaluate(task, rules):
    state = {task.ident: "initial"}
    action = solve(task, rules)
    outcomes = {"stage": "staged", "escalate": "escalated", "keep": "kept", "wait": "waiting"}
    state[task.ident] = outcomes[action]
    return {"exercise": task.ident, "expected": task.expected, "observed": state[task.ident],
            "correct": state[task.ident] == task.expected}


def run(pool_type, item_type, root):
    selected = []
    training = []
    candidate_inputs = {
        "ready_always": TASKS[0],
        "blocked_escalate": TASKS[2],
        "complete_keep": TASKS[3],
        "complete_reopen": TASKS[3],
    }
    for ident, features in candidate_inputs.items():
        attempts = []
        for i in range(3):
            result = evaluate(Exercise(f"warmup-{ident}-{i}", *features), [ident])
            attempts.append(result["correct"])
        training.append({"candidate": ident, "results": attempts})
        if all(attempts):
            selected.append(ident)

    heldout = [Exercise(f"heldout-{f}-{i}", *features)
               for f, features in enumerate(TASKS) for i in range(5)]
    assert len({task.ident for task in heldout}) == 20
    results = {}
    for arm, rule_ids in {
        "no_memory": [],
        "three_success_bank": selected,
        "reviewed_bank": ["ready_checked", "blocked_escalate", "complete_keep"],
    }.items():
        if not rule_ids:
            rules, bank_hash, byte_count = [], None, 0
        else:
            items = [item_type(memory_id=ident, type="workflow",
                               text=f"Authored fixture rule {ident}", tags={"lab_rule_id": ident})
                     for ident in rule_ids]
            path = root / f"{arm}.json"
            bank = pool_type(items)
            assert bank.save(path) == path
            before = path.read_bytes()
            copy = bank.save(path)
            assert copy != path and copy.read_bytes() == before
            frozen = pool_type.load_for_solver(path, "synthetic")
            rules = [frozen.get(ident).tags["lab_rule_id"] for ident in frozen.ids()]
            assert rules == rule_ids
            bank_hash, byte_count = hashlib.sha256(before).hexdigest(), len(before)
        observed = [evaluate(task, rules) for task in heldout]
        if rule_ids:
            assert path.read_bytes() == before
        results[arm] = {"correct": sum(row["correct"] for row in observed),
                        "unwarranted_stages": sum(row["observed"] == "staged"
                                                  and row["expected"] == "waiting"
                                                  for row in observed),
                        "bank_sha256": bank_hash, "bank_bytes": byte_count,
                        "rules": rules, "heldout": observed}

    admission = {}
    for case in ("missing", "empty"):
        path = root / f"{case}.json"
        if case == "empty":
            pool_type().save(path)
        try:
            pool_type.load_for_solver(path, "synthetic")
        except (FileNotFoundError, ValueError) as exc:
            admission[case] = type(exc).__name__
        else:
            raise AssertionError(f"Solver accepted {case} bank")

    assert admission == {"missing": "FileNotFoundError", "empty": "ValueError"}
    assert [results[arm]["correct"] for arm in results] == [10, 15, 20]
    assert results["three_success_bank"]["unwarranted_stages"] == 5
    assert results["reviewed_bank"]["unwarranted_stages"] == 0
    return dict(heldout_count=len(heldout), bank_admission=admission,
                selection_trials=training, results=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    pool_type, item_type = load(args.source.resolve())
    runs = []
    for _ in range(3):
        with TemporaryDirectory(prefix="daedalus-frozen-") as directory:
            runs.append(run(pool_type, item_type, Path(directory)))
    assert runs[0] == runs[1] == runs[2]
    print(json.dumps(dict(source_commit=COMMIT, repeats=len(runs), provider_requests=0,
                          **runs[0]), indent=2))


if __name__ == "__main__":
    main()
