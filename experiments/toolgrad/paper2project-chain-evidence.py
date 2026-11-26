"""Check benign synthetic chain outcomes using Paper2Project's native comparator."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
CRITERIA = {
    "success_flag": ("ok",),
    "terminal_state": ("ok", "state"),
    "state_and_trace": ("ok", "state", "steps"),
}
EXPECT = {
    "exact": (True, True, True),
    "omitted_publish": (True, False, False),
    "reordered": (True, False, False),
    "wrong_scope": (True, False, False),
    "redundant_publish": (True, True, False),
}


def fixture(app, root):
    project_file, paper_file = root / "project.md", root / "paper.md"
    project_file.write_text("# Project\n\nThe job records its final counter and scope.\n", encoding="utf-8")
    paper_file.write_text("# Study\n\nThe witness records the order of steps.\n", encoding="utf-8")
    project, = app.import_projects(project_file, name="Chain fixture")
    rid = app.import_research(paper_file, title="Chain study")["id"]
    pid = project["id"]
    jid = app.create_job(rid, [pid])["id"]
    app.submit_analysis(jid, {"summary": "Synthetic chain evidence", "assessments": [{
        "project_id": pid, "relevance": "candidate", "rationale": "Compare expected state and step order.",
        "missing_evidence": [], "citations": [
            {"document_id": f"project:{pid}:project.md", "start": 3, "end": 3,
             "quote": "final counter and scope"},
            {"document_id": f"research:{rid}:paper.md", "start": 3, "end": 3,
             "quote": "order of steps"},
        ],
    }]})
    source, inputs = root / "source", root / "input"
    source.mkdir()
    inputs.mkdir()
    (source / "fixture.txt").write_bytes(b"Synthetic local counter.\n")
    (inputs / "fixture.json").write_text(json.dumps({"first": 1, "last": 100}), encoding="utf-8")
    return pid, jid, source, inputs


def execute(steps, initial, offset):
    counter, published, scope = initial, None, "primary"
    for step in steps:
        if step == "add":
            counter += offset
        elif step == "scale":
            counter *= 2
        elif step == "publish":
            published = counter
        elif step == "publish_peer":
            published, scope = counter, "peer"
        else:
            raise ValueError(step)
    return {"ok": True, "state": {"draft": counter, "published": published, "scope": scope},
            "steps": steps}


def variants(gold):
    return {
        "exact": gold, "omitted_publish": gold[:-1],
        "reordered": ["scale", "add", *gold[2:]],
        "wrong_scope": [*gold[:-1], "publish_peer"],
        "redundant_publish": [*gold, "publish"],
    }


def register(app, pid, jid, source, inputs, expected, fields):
    return app.add_experiment(jid, {
        "kind": "reproduction", "project_id": pid, "image": "test/image",
        "source": {"path": str(source), "revision": "a" * 40, "license": "MIT"},
        "input": {"path": str(inputs)}, "arms": {"baseline": ["false"], "candidate": ["false"]},
        "metrics": [{"name": field, "path": field, "comparison": "exact",
                     "expected": {"baseline": expected[field], "candidate": expected[field]}}
                    for field in fields],
    })


def passes(app, native, entry, run_id, expected, actual):
    row = {key: entry[key] for key in ("job_id", "plan", "source_tree", "input_tree")}
    row.update(id=run_id, experiment_id=entry["id"], status="PASS", arms={})
    for name, value in (("baseline", expected), ("candidate", actual)):
        digest = app.store.put_json(value)
        row["arms"][name] = dict(exit_code=0, timed_out=False, error=None, result=digest, result_sha256=digest)
    row["sealed"] = app.store.put_json({"schema": 2, "run": native.run_identity(row), "arms": row["arms"]})
    return native.evaluate(app, row)["status"] == "PASS"


def replay(App, native):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        app = App(root / "workspace")
        pid, jid, source, inputs = fixture(app, root)
        counts = {name: Counter() for name in CRITERIA}
        for seed in range(1, 101):
            scales = 1 + seed % 4
            gold = ["add", *["scale"] * scales, "publish"]
            # Independent closed-form oracle: the interpreter above is not used to set expectations.
            terminal = (seed + 3) * 2**scales
            expected = {"ok": True, "state": {"draft": terminal, "published": terminal, "scope": "primary"},
                        "steps": gold}
            plans = {name: register(app, pid, jid, source, inputs, expected, fields)
                     for name, fields in CRITERIA.items()}
            for case, steps in variants(gold).items():
                actual = execute(steps, seed, 3)
                verdicts = tuple(passes(app, native, entry, f"run-{seed}-{case}-{name}", expected, actual)
                                 for name, entry in plans.items())
                if verdicts != EXPECT[case]:
                    raise AssertionError((seed, case, verdicts))
                for name, accepted in zip(CRITERIA, verdicts):
                    counts[name][case] += int(accepted)
        return {name: dict(cases) for name, cases in counts.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    source = parser.parse_args().checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        parser.error(f"Expected clean Paper2Project checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    from paper2project import execution
    from paper2project.core import App

    first = replay(App, execution)
    if first != replay(App, execution):
        raise AssertionError("Repeat diverged")
    print(json.dumps({"revision": REVISION, "repeat_count": 2, "chains_per_repeat": 100,
                      "cases_per_repeat": 500, "status": "PASS", "accepted_per_repeat": first}, indent=2))


if __name__ == "__main__":
    main()
