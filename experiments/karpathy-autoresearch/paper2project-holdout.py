"""Replay a primary metric and an independently declared guard through Paper2Project."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REVISION = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
CASES = {
    # Primary gain, declared guard loss, recorded guard loss, reference, expected run, expected benefit.
    "confirmed": (2, 0, 0, True, "PASS", True),
    "missing_reference": (2, 0, 0, False, "PASS", True),
    "reproduced_regression": (2, 1, 1, True, "PASS", False),
    "unexpected_regression": (2, 0, 1, True, "FAIL", False),
    "missing_guard": (2, 0, None, True, "FAIL", False),
    "below_threshold": (1, 0, 0, True, "PASS", False),
}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def setup(app, execution, root, base, gain, loss, reference):
    source, inputs = root / "source", root / "inputs"
    source.mkdir()
    inputs.mkdir()
    (source / "README.md").write_bytes(b"Synthetic evidence only.\n")
    git(source, "init", "-q")
    git(source, "add", "README.md")
    git(source, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
        "commit", "-qm", "Create disposable source")
    (inputs / "target.json").write_text(json.dumps({"primary": base, "holdout": 10}), encoding="utf-8")
    project_file, paper_file = root / "project.md", root / "paper.md"
    project_quote = "Synthetic target has a second quality measure."
    paper_quote = "The baseline and candidate are measured separately."
    project_file.write_text(project_quote + "\n", encoding="utf-8")
    paper_file.write_text(paper_quote + "\n", encoding="utf-8")
    project, = app.import_projects(project_file, name="Target")
    pid = project["id"]
    metrics = [
        {"name": "primary", "path": "primary", "comparison": "exact",
         "expected": {"baseline": base, "candidate": base + gain}},
        {"name": "holdout", "path": "holdout", "comparison": "exact",
         "expected": {"baseline": 10, "candidate": 10 - loss}},
    ]
    plan = {"kind": "project_benefit", "project_id": pid, "image": "test/image",
            "source": {"path": str(source), "revision": git(source, "rev-parse", "HEAD"), "license": "MIT"},
            "input": {"path": str(inputs)}, "arms": {"baseline": ["false", "base"], "candidate": ["false", "trial"]},
            "metrics": metrics, "benefit": {"metric": "primary", "direction": "increase", "min_delta": 2,
                                           "guards": [{"metric": "holdout", "op": "ge", "value": 10}]}}
    if reference:
        receipt = root / "expected.json"
        receipt.write_text(json.dumps({
            "schema": 1, "method": "Expected integers from the fixed scenario table",
            "source_tree": execution.tree_hash(source)["sha256"],
            "input_tree": execution.tree_hash(inputs)["sha256"],
            "expected": {metric["name"]: metric["expected"] for metric in metrics},
        }), encoding="utf-8")
        app.attach_asset(pid, receipt)
        plan["reference"] = receipt.name
    rid = app.import_research(paper_file, title="Study")["id"]
    jid = app.create_job(rid, [pid])["id"]
    app.submit_analysis(jid, {"summary": "Synthetic replay", "assessments": [{
        "project_id": pid, "relevance": "candidate", "rationale": "Compare two declared outcomes.",
        "missing_evidence": [], "citations": [
            {"document_id": f"project:{pid}:project.md", "start": 1, "end": 1, "quote": project_quote},
            {"document_id": f"research:{rid}:paper.md", "start": 1, "end": 1, "quote": paper_quote},
        ],
    }]}, author="fixture-author")
    return jid, app.add_experiment(jid, plan)


def record(app, execution, entry, base, gain, observed_loss):
    run = {key: entry[key] for key in ("job_id", "plan", "source_tree", "input_tree")}
    run.update(id="run-fixture", experiment_id=entry["id"], status="PASS", arms={})
    candidate = {"primary": base + gain}
    if observed_loss is not None:
        candidate["holdout"] = 10 - observed_loss
    for key, value in (("baseline", {"primary": base, "holdout": 10}), ("candidate", candidate)):
        digest = app.store.put_json(value)
        run["arms"][key] = dict(exit_code=0, timed_out=False, error=None, result=digest, result_sha256=digest)
    run["sealed"] = app.store.put_json({"schema": 2, "run": execution.run_identity(run), "arms": run["arms"]})
    app.store.save("run", run["id"], run)


def replay(App, execution):
    rows = []
    for case, (gain, expected_loss, observed_loss, reference, run_status, benefit) in CASES.items():
        for base in (4, 10, 19, 28):
            with TemporaryDirectory() as temp:
                root = Path(temp)
                app = App(root / "workspace")
                jid, entry = setup(app, execution, root, base, gain, expected_loss, reference)
                record(app, execution, entry, base, gain, observed_loss)
                evaluated, = execution.runs(app, entry["id"])
                pending = app.report(jid)["json"]["projects"][0]["decision"]
                packet = app.review_packet(jid)
                review = dict(evidence=packet["evidence"])
                app.review_analysis(jid, "pass", "Synthetic fixture review.", "fixture-reviewer", packet["analysis"], **review)
                reviewed = app.report(jid)["json"]["projects"][0]["decision"]
                try:
                    app.review_analysis(jid, "pass", "Synthetic reference check.", "fixture-reviewer",
                                        packet["analysis"], verified_experiments=[entry["id"]], **review)
                except ValueError as error:
                    if "passing experiments with frozen references" not in str(error):
                        raise
                    attested = False
                else:
                    attested = True
                final = app.report(jid)["json"]["projects"][0]["decision"]
                blocked = "EXPERIMENT_FAILED" if run_status == "FAIL" else "REPRODUCED_BENEFIT_UNPROVEN"
                expected = (run_status, benefit, "BENEFIT_PENDING_REVIEW" if benefit else blocked,
                            "BENEFIT_CRITERIA_MET" if benefit else blocked, benefit and reference,
                            "BENEFIT_DEMONSTRATED" if benefit and reference else
                            "BENEFIT_CRITERIA_MET" if benefit else blocked)
                actual = evaluated["status"], evaluated["benefit"]["met"], pending, reviewed, attested, final
                if actual != expected:
                    raise AssertionError((case, base, actual, expected))
                rows.append({"case": case, "baseline_primary": base, "primary_gain": gain,
                             "primary_only_accepts": evaluated["benefit"]["delta"] >= 2,
                             "run": run_status, "benefit_criteria_met": benefit, "initial": pending,
                             "ordinary_review": reviewed, "attestation_accepted": attested, "final": final})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    source = parser.parse_args().checkout.resolve()
    if git(source, "rev-parse", "HEAD") != REVISION or git(source, "status", "--porcelain"):
        parser.error(f"Expected clean Paper2Project checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    from paper2project import execution
    from paper2project.core import App

    result = replay(App, execution)
    if result != replay(App, execution):
        raise AssertionError("Repeat diverged")
    print(json.dumps({"revision": REVISION, "repeat_count": 2, "status": "PASS", "cases": result}, indent=2))


if __name__ == "__main__":
    main()
