"""Compare reference shape and native snapshot binding on synthetic artifacts."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REVISION = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
NAME = "measurement.txt"
OTHER = "operator-notes.txt"
SCENARIOS = {
    "exact": (True, None),
    "unknown_name": (False, "frozen snapshot"),
    "mismatched_hash": (False, "frozen snapshot"),
    "incorrect_line": (False, "precise line range"),
    "next_snapshot_same_name": (False, "frozen snapshot"),
    "wrong_role_with_valid_binding": (False, None),
}


def link(name, text, line, quote):
    return {
        "name": name, "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "start": line, "end": line, "quote": quote,
    }


def shape_accepts(ref):
    return (bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", ref["name"]))
            and bool(re.fullmatch(r"[a-f0-9]{64}", ref["sha256"]))
            and type(ref["start"]) is int and type(ref["end"]) is int
            and 1 <= ref["start"] <= ref["end"] and bool(ref["quote"].strip()))


def case(App, fixture, scenario):
    expected_correct, expected_error = SCENARIOS[scenario]
    with TemporaryDirectory() as temp:
        root = Path(temp)
        project = root / "project.md"
        paper = root / "paper.md"
        project_quote = "The local catalog records a synthetic measurement."
        paper_quote = "A named measurement is required by the downstream stage."
        project.write_bytes(f"{project_quote}\n".encode())
        paper.write_bytes(f"{paper_quote}\n".encode())
        app = App(root / "workspace")
        pid = app.import_projects(project, name=f"Fixture {fixture}")[0]["id"]
        rid = app.import_research(paper, title="Synthetic contract excerpt")["id"]

        first = f"Measurement points: {fixture}"
        second = f"Revised measurement points: {fixture + 10}"
        note = f"Operator notes count: {fixture}"
        first_text = f"{first}\nSynthetic footer.\n"
        second_text, note_text = f"{second}\n", f"{note}\n"
        artifact, other = root / NAME, root / OTHER
        artifact.write_bytes(first_text.encode())
        other.write_bytes(note_text.encode())
        app.attach_asset(pid, artifact)
        app.attach_asset(pid, other)
        jid = app.create_job(rid, [pid])["id"]
        if scenario == "next_snapshot_same_name":
            artifact.write_bytes(second_text.encode())
            app.attach_asset(pid, artifact)

        ref = link(NAME, first_text, 1, first)
        if scenario == "unknown_name":
            ref["name"] = "absent.txt"
        if scenario == "mismatched_hash":
            ref["sha256"] = link(OTHER, note_text, 1, note)["sha256"]
        if scenario == "incorrect_line":
            ref.update(start=2, end=2)
        if scenario == "next_snapshot_same_name":
            ref = link(NAME, second_text, 1, second)
        if scenario == "wrong_role_with_valid_binding":
            ref = link(OTHER, note_text, 1, note)

        research_citation = {
            "document_id": f"research:{rid}:paper.md", "start": 1, "end": 1, "quote": paper_quote,
        }
        analysis = {"summary": "Synthetic observation", "assessments": [{
            "project_id": pid, "finding_schema": 1, "rationale": "Synthetic control",
            "citations": [
                {"document_id": f"project:{pid}:project.md", "start": 1, "end": 1, "quote": project_quote},
                research_citation,
            ],
            "missing_evidence": [],
            "findings": [{
                "id": "measurement", "target": "Local catalog",
                "claim": "The input contains a synthetic measurement.",
                "premise": "The measurement belongs to the selected snapshot.",
                "falsifier": "The cited input is absent from that snapshot.",
                "proposed": "candidate", "research_citations": [research_citation],
                "project_artifacts": [ref], "missing_evidence": [],
            }],
        }]}
        error, status = None, None
        try:
            app.submit_analysis(jid, analysis, author="fixture")
        except ValueError as exc:
            error = str(exc)
        else:
            packet = app.review_packet(jid)
            if packet["assessment"]["findings"][0]["project_artifacts"] != [ref]:
                raise AssertionError("Captured reference differs from submitted reference")
            status = app.report(jid)["json"]["projects"][0]["findings"][0]["status"]

        native = error is None
        if (native != (expected_error is None)
                or (expected_error and expected_error not in error)
                or (native and status != "PENDING_SEMANTIC_REVIEW") or not shape_accepts(ref)):
            raise AssertionError((fixture, scenario, error, status))
        return {"fixture": fixture, "scenario": scenario, "correct_input": expected_correct,
                "shape_accepted": True, "native_accepted": native, "error": error, "status": status}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("paper2project_checkout", type=Path)
    args = cli.parse_args()
    source = args.paper2project_checkout.resolve()
    revision = subprocess.check_output(["git", "-C", source, "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", source, "status", "--porcelain"], text=True)
    if revision != REVISION or dirty:
        cli.error(f"Expected clean Paper2Project checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    from paper2project.core import App

    first = [case(App, i, scenario) for i in range(1, 6) for scenario in SCENARIOS]
    second = [case(App, i, scenario) for i in range(1, 6) for scenario in SCENARIOS]
    if first != second:
        raise AssertionError("Repeat did not reproduce the first run")
    print(json.dumps({"revision": REVISION, "repeat_count": 2, "status": "PASS",
                      "cases": first}, indent=2))


if __name__ == "__main__":
    main()
