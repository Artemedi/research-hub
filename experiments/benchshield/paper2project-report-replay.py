"""Replay Paper2Project report decisions from benign synthetic run records."""

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


TARGET = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
CASES = {
    "match": ("PASS", "REPRODUCED_BENEFIT_UNPROVEN"),
    "mismatch": ("FAIL", "EXPERIMENT_FAILED"),
    "missing_facts": ("FAIL", "EXPERIMENT_FAILED"),
    "interrupted": ("INTERRUPTED", "EXPERIMENT_INCOMPLETE"),
    "blocked": ("BLOCKED", "EXPERIMENT_BLOCKED"),
    "legacy": ("STALE", "STALE_EVIDENCE"),
    "not_run": ("NOT_RUN", "EXPERIMENT_NOT_RUN"),
}


def prepare(app, root, seed):
    project_file = root / "project.md"
    project_file.write_text("# Lab project\n\nCompare the sum of three integers.\n", encoding="utf-8")
    paper_file = root / "paper.md"
    paper_file.write_text("# Lab study\n\nRecord the input and the calculated sum.\n", encoding="utf-8")
    source = root / "source"
    source.mkdir()
    (source / "description.txt").write_text("Synthetic replay fixture. No runnable program.\n", encoding="utf-8")
    inputs = root / "inputs"
    inputs.mkdir()
    input_file = inputs / "numbers.json"
    input_file.write_text(json.dumps([seed, -2 * seed, 2 * seed + 7]), encoding="utf-8")
    expected = sum(json.loads(input_file.read_text(encoding="utf-8")))
    project, = app.import_projects(project_file, name="Lab project")
    research = app.import_research(paper_file, title="Lab study")
    pid = project["id"]
    jid = app.create_job(research["id"], [pid])["id"]
    app.submit_analysis(jid, {"summary": "Synthetic replay", "assessments": [
        {"project_id": pid, "relevance": "candidate", "rationale": "Compare arithmetic on artificial data.",
         "missing_evidence": [], "citations": [
             {"document_id": f"project:{pid}:project.md", "start": 3, "end": 3, "quote": "sum of three integers"},
             {"document_id": "research:lab-study:paper.md", "start": 3, "end": 3, "quote": "calculated sum"},
         ]}
    ]})
    plan = {
        "kind": "reproduction", "project_id": pid, "image": "test/image",
        "source": {"path": str(source), "revision": "a" * 40, "license": "MIT"},
        "input": {"path": str(inputs)}, "arms": {"baseline": ["false"], "candidate": ["false"]},
        "metrics": [{"name": "total", "path": "total", "comparison": "exact",
                     "expected": {"baseline": expected, "candidate": expected}}],
    }
    return jid, app.add_experiment(jid, plan), expected


def record(app, execution, experiment, case, expected, seed):
    if case == "not_run":
        return
    row = {key: experiment[key] for key in ("job_id", "plan", "source_tree", "input_tree")}
    row.update(id=f"run-lab-{seed}", experiment_id=experiment["id"], arms={})
    if case in ("interrupted", "blocked"):
        row.update(status=case.upper(), reason=f"Synthetic {case} record")
    else:
        candidate = expected - 1 if case == "mismatch" else expected
        for arm, value in (("baseline", expected), ("candidate", candidate)):
            result = app.store.put_json({"total": value})
            row["arms"][arm] = dict(exit_code=0, timed_out=False, error=None,
                                    result=result, result_sha256=result)
        row["status"] = "PASS" if case == "match" else "FAIL"
        if case != "missing_facts":
            seal = {"schema": 1 if case == "legacy" else 2,
                    "run": execution.run_identity(row), "arms": row["arms"]}
            row["sealed"] = app.store.put_json(seal)
    app.store.save("run", row["id"], row)


def run(checkout):
    git = ["git", "-C", str(checkout)]
    actual = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    if actual != TARGET or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip():
        raise ValueError("Use the clean, pinned dsh-paper2agent checkout")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(checkout / "src"))
    from paper2project import execution
    from paper2project.core import App

    counts, decisions, reporting, explanations = Counter(), Counter(), {}, {}
    for case, (status, decision) in CASES.items():
        for seed in (1, 4, 9, 12):
            with TemporaryDirectory(prefix="paper2project-report-replay-") as folder:
                root = Path(folder)
                app = App(root / "workspace")
                jid, experiment, expected = prepare(app, root, seed)
                record(app, execution, experiment, case, expected, seed)
                report = app.report(jid)
                project, = report["json"]["projects"]
                entry, = project["experiments"]
                if (entry["status"], project["decision"]) != (status, decision):
                    raise AssertionError(f"{case}: unexpected JSON report")
                if (f"Decision: **{decision}**" not in report["markdown"]
                        or f"Experiment `{experiment['id']}`: {status}" not in report["markdown"]):
                    raise AssertionError(f"{case}: unexpected Markdown report")
                if case in ("match", "mismatch"):
                    evaluated, = execution.runs(app, experiment["id"])
                    expected_candidate = expected - (case == "mismatch")
                    if [check["actual"] for check in evaluated["checks"]] != [expected, expected_candidate]:
                        raise AssertionError(f"{case}: unexpected evaluated values")
                    if [check["passed"] for check in evaluated["checks"]] != [True, case == "match"]:
                        raise AssertionError(f"{case}: unexpected comparison flags")
                reason = entry["reason"]
                display = {"has_experiment_reason_in_json": bool(reason),
                           "includes_same_reason_in_markdown": bool(reason and reason in report["markdown"])}
                if reporting.setdefault(case, display) != display:
                    raise AssertionError(f"{case}: inconsistent reporting across input variants")
                if explanations.setdefault(case, project["explanation"]) != project["explanation"]:
                    raise AssertionError(f"{case}: inconsistent explanation across input variants")
                counts[case] += 1
                decisions[decision] += 1
    return dict(target_commit=TARGET, checked=sum(counts.values()), case_counts=counts,
                decision_counts=decisions, reporting=reporting,
                missing_facts_shares_mismatch_explanation=explanations["missing_facts"] == explanations["mismatch"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    options = parser.parse_args()
    print(json.dumps(run(options.checkout.resolve()), indent=2))
