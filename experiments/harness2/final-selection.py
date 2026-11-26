"""Replay Harness² final selection on authored answers without running an agent."""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

COMMIT = "6868817518876de8fd170c6a8354daca273b6191"


@dataclass(frozen=True)
class Case:
    name: str
    reply: str
    chosen: str
    ok: bool
    fallback: bool
    cost: float
    calls: int
    correct: bool | None
    first_delivered: bool = True
    second_delivered: bool = True
    k: int = 2


CASES = (
    Case("supported_final", "answer_5", "c2", True, False, 0.125, 1, True),
    Case("incorrect_but_valid_choice", "answer_4", "c1", True, False, 0.125, 1, False),
    Case("malformed_reply", "malformed", "c1", False, True, 0.125, 1, False),
    Case("unknown_id", "unknown", "c1", False, True, 0.125, 1, False),
    Case("provider_failure", "exception", "c1", False, True, 0.25, 1, False),
    Case("skip_undelivered_first", "malformed", "c2", False, True, 0.125, 1, True,
         first_delivered=False),
    Case("no_deliverable", "unused", "", False, False, 0.0, 0, None,
         first_delivered=False, second_delivered=False),
    Case("single_final", "unused", "c1", True, False, 0.0, 0, True, k=1),
)


def run_case(case, root, selection, proposer, spec):
    work_dir = root / case.name
    work_dir.mkdir()
    evidence = {}
    calls = []

    def rollout(label, answer, delivered):
        path = work_dir / label
        path.mkdir()
        (path / "answer.txt").write_text(f"{answer}\n", encoding="utf-8")
        evidence[label] = answer
        return spec.RunView(label, f"run-{label}", path, True, delivered, cost_usd=4.0)

    base = [rollout("base1", 5, True)]
    finals = {"c1": rollout("c1", 5 if case.k == 1 else 4, case.first_delivered)}
    if case.k == 2:
        finals["c2"] = rollout("c2", 5, case.second_delivered)
    pool = selection.selection_pool("sequential", case.k, finals, base)
    adapter = SimpleNamespace(
        spec=SimpleNamespace(prompts=spec.BenchPrompts(work="Add two numbers."),
                             state_deliverable=False),
        task_prompt=lambda _task: "Return the sum of 2 and 3.",
        deliverable_text=lambda path: (path / "answer.txt").read_text(encoding="utf-8"),
    )

    def fake_call(_mission, context, label):
        calls.append(label)
        files = sorted((context / "candidates").glob("*.md"))
        answers = {path.stem: int(path.read_text(encoding="utf-8").splitlines()[-1])
                   for path in files}
        assert sorted(answers.values()) == sorted(
            evidence[label] for label, view in pool.items() if view.delivered
        )
        assert all(path.stem.isupper() for path in files)
        assert not (context / "selection.json").exists()
        if case.reply == "exception":
            raise proposer.ProposerError("synthetic provider failure", attempts=2, cost_usd=0.25)
        if case.reply == "malformed":
            text = "No choice block."
        else:
            chosen_id = "UNLISTED"
            if case.reply != "unknown":
                answer = int(case.reply.removeprefix("answer_"))
                chosen_id = next(key for key, value in answers.items() if value == answer)
            text = "```choice\n" + chosen_id + "\n```"
        return proposer.Reply(label, text, True, cost_usd=0.125)

    if case.k == 1:
        result = selection.trivial_selection("arithmetic", case.k, "sequential", pool,
                                             adapter=adapter, work_dir=work_dir)
    else:
        result = selection.run_selection(
            "arithmetic", case.k, "sequential", pool, adapter=adapter, work_dir=work_dir,
            prop=SimpleNamespace(call=fake_call), pool_kind="finals",
        )
    record = work_dir / "selection" / f"sequential{case.k}" / "selection.json"
    correct = evidence[result.chosen_label] == 2 + 3 if result.chosen_label else None
    observed = (result.chosen_label, result.ok, result.fallback, result.usd,
                len(calls), correct)
    expected = (case.chosen, case.ok, case.fallback, case.cost, case.calls, case.correct)
    assert observed == expected, (case.name, observed, expected)
    assert not result.chosen_is_base and "base1" not in result.id_map.values()
    assert set(result.dropped) == {label for label, view in pool.items() if not view.delivered}
    assert len(result.id_map) == result.n_candidates
    assert record.exists() == bool(case.chosen)
    if record.exists():
        stored = json.loads(record.read_text(encoding="utf-8"))
        assert Path(stored.pop("chosen_run_dir")) == pool[case.chosen].run_dir
        assert stored == result.to_dict()
    return {
        "case": case.name, "calls": len(calls), "chosen": result.chosen_label or None,
        "ok": result.ok, "fallback": result.fallback, "selection_usd_fixture": result.usd,
        "correct_by_oracle": correct, "persisted": record.exists(),
        "dropped": result.dropped,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()

    def git(*command):
        return subprocess.check_output(["git", "-C", str(source), *command], text=True).strip()

    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Use a clean checkout at " + COMMIT)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    from harness2.core import proposer, selection, spec

    runs = []
    for _ in range(3):
        with tempfile.TemporaryDirectory(prefix="harness2-selection-") as directory:
            runs.append([run_case(case, Path(directory), selection, proposer, spec) for case in CASES])
    assert runs[0] == runs[1] == runs[2]
    print(json.dumps({
        "upstream_commit": COMMIT, "python": sys.version.split()[0], "platform": sys.platform,
        "repeat_count": len(runs), "case_count": len(CASES),
        "provider_requests": 0, "provider_tokens": None, "observed_spend_usd": 0,
        "cases_per_repeat": runs[0],
    }, indent=2))


if __name__ == "__main__":
    main()
