"""Compare votes, native citation checks, and independent evidence in Paper2Project."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
METHOD = "The fixture total is computed from the item ledger."
CASES = {
    # Candidate adjustments to the independent total, incorrect citation slots, conflicting receipt.
    "unanimous_correct": ((0, 0, 0, 0, 0), (), False, (True, True, "supported")),
    "unanimous_wrong": ((4, 4, 4, 4, 4), (), False, (False, False, "no_supported_candidate")),
    "disputed_correct_minority": ((4, 0, 4, 0, 4), (), False, (False, False, "supported")),
    "majority_wrong_citation": ((4, 4, 4, 0, 0), (0, 1, 2), False, (False, True, "supported")),
    "evidence_conflict": ((0, 0, 0, 0, 0), (), True, (True, True, "conflicting_evidence")),
    "disputed_all_wrong": ((4, 9, 4, 9, 4), (), False, (False, False, "no_supported_candidate")),
}


def read_json(app, jid, label):
    result = app.read(jid, label, start=1, count=1)
    return json.loads(result["text"].partition(": ")[2])


def vote(numbers):
    if not numbers:
        return None
    winner, _ = Counter(numbers).most_common(1)[0]
    return winner


def verify(app, jid, prefix, candidates):
    ledger = read_json(app, jid, prefix + "ledger.txt")
    receipt = read_json(app, jid, prefix + "receipt.txt")
    measured = sum(item["units"] * item["each"] for item in ledger)
    if measured != receipt["approved_total"]:
        return None, "conflicting_evidence"
    if measured not in candidates:
        return None, "no_supported_candidate"
    return measured, "supported"


def fixture(App, seed, case):
    adjustments, bad_lines, corrupt, expected = CASES[case]
    with TemporaryDirectory() as folder:
        root = Path(folder)
        docs = root / "docs"
        docs.mkdir()
        ledger = [{"units": 2, "each": seed + 2}, {"units": 3, "each": seed + 7}]
        total = 5 * seed + 25
        note = f"The forecast is {total + 4} and the booked total is {total}."
        (docs / "summary.md").write_text(f"# Summary\n{note}\nReserved reference line.\n", encoding="utf-8")
        (docs / "ledger.txt").write_text(json.dumps(ledger) + "\n", encoding="utf-8")
        (docs / "receipt.txt").write_text(json.dumps({"approved_total": total + int(corrupt)}) + "\n", encoding="utf-8")
        paper = root / "study.md"
        paper.write_text(METHOD + "\n", encoding="utf-8")
        app = App(root / "workspace")
        project, = app.import_projects(docs, name="Evidence trial")
        pid = project["id"]
        rid = app.import_research(paper, title="Fixture study")["id"]
        jid = app.create_job(rid, [pid])["id"]
        prefix = f"project:{pid}:"
        pool = [total + adjustment for adjustment in adjustments]
        anchored = []
        for slot, value in enumerate(pool):
            line = 3 if slot in bad_lines else 2
            claim = f"The booked total is {value}."
            analysis = {"summary": "Candidate arithmetic claim", "assessments": [{
                "project_id": pid, "relevance": "candidate", "rationale": claim, "missing_evidence": [],
                "citations": [
                    {"document_id": prefix + "summary.md", "start": line, "end": line,
                     "quote": note, "claim": claim},
                    {"document_id": f"research:{rid}:study.md", "start": 1, "end": 1,
                     "quote": METHOD, "claim": METHOD},
                ],
            }]}
            try:
                app.submit_analysis(jid, analysis, author="fixture-author")
            except ValueError as error:
                if slot not in bad_lines or "precise line range" not in str(error):
                    raise
            else:
                if slot in bad_lines or app.report(jid)["json"]["citation_warnings"]:
                    raise AssertionError("Structural citation control did not behave as expected")
                anchored.append(value)
        selected, reason = verify(app, jid, prefix, anchored)
        correct = vote(pool) == total, vote(anchored) == total, reason
        if correct != expected or (selected is not None and selected != total):
            raise AssertionError((case, seed, correct, selected))
        return {"case": case, "fixture": seed, "candidates": len(pool), "citation_admitted": len(anchored),
                "vote_correct": correct[0], "citation_vote_correct": correct[1], "verified": reason}


def replay(App):
    return [fixture(App, seed, case) for case in CASES for seed in range(1, 9)]


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("checkout", type=Path)
    source = cli.parse_args().checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        cli.error(f"Expected clean Paper2Project checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    from paper2project.core import App

    rows = replay(App)
    if any(rows != replay(App) for _ in range(2)):
        raise AssertionError("Repeat diverged")
    print(json.dumps({"revision": REVISION, "repeat_count": 3, "cases_per_repeat": len(rows),
                      "status": "PASS", "cases": rows}, indent=2))


if __name__ == "__main__":
    main()
