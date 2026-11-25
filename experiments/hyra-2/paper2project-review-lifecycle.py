"""Check Paper2Project's evidence-first review and persisted decisions on synthetic inputs."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


TARGET = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
CASES = (
    ("support", "Observed transition: retry -> done.", "supported", "REVIEWED_PREMISE_SUPPORTED"),
    ("contradict", "Observed transition: retry -> stopped.", "contradicted", "REVIEWED_PREMISE_CONTRADICTED"),
    ("missing", None, "unknown", "PENDING_SEMANTIC_REVIEW"),
    ("unrelated", "Observed transition: queued -> cancelled.", "unknown", "PENDING_SEMANTIC_REVIEW"),
)


def attachment(app, pid, path, line):
    payload = (line + "\n").encode("utf-8")
    path.write_bytes(payload)
    app.attach_asset(pid, path)
    return {"name": path.name, "sha256": hashlib.sha256(payload).hexdigest(),
            "start": 1, "end": 1, "quote": line}


def scenario(app_class, root, case, observation, premise, expected, proposal):
    workspace = root / "workspace"
    app = app_class(workspace)
    project = root / "project.md"
    original = "# Lab project\n\nRetry can reach a terminal state.\n"
    project.write_text(original, encoding="utf-8")
    paper = root / "paper.md"
    quote = "A separate reviewer checks observations."
    paper.write_text(f"# Lab study\n\n{quote}\n", encoding="utf-8")
    project_row, = app.import_projects(project, name="Lab project")
    pid = project_row["id"]
    research = app.import_research(paper, title="Lab study")
    cited = attachment(app, pid, root / "design.txt", "Declared transition: retry -> done.")
    control = attachment(app, pid, root / "observation.txt", observation) if observation else None
    jid = app.create_job(research["id"], [pid])["id"]
    citation = {"document_id": "research:lab-study:paper.md", "start": 3, "end": 3, "quote": quote}
    project_citation = {"document_id": f"project:{pid}:project.md", "start": 3, "end": 3,
                        "quote": "Retry can reach a terminal state."}
    app.submit_analysis(jid, {"summary": "Check a design statement using an observation.",
                              "assessments": [{
        "project_id": pid, "rationale": "A reported transition needs separate evidence.",
        "finding_schema": 1, "missing_evidence": [], "citations": [project_citation, citation],
        "findings": [{"id": "transition", "target": "retry", "claim": "Retry can reach done.",
                      "premise": "The test event reaches done from retry.",
                      "falsifier": "The recorded retry event reaches another terminal state.",
                      "proposed": proposal, "research_citations": [citation],
                      "project_artifacts": [cited], "missing_evidence": []}],
    }]}, author="lab-author")
    ordinary = app.review_packet(jid)
    blind = app.review_packet(jid, blind=True)
    if (ordinary["assessment"]["findings"][0]["proposed"] != proposal
            or "proposed" in blind["findings"][0] or "analysis_author" in blind
            or ordinary["citation_context"] != blind["citation_context"]
            or not blind["citation_context"]):
        raise AssertionError(f"{case}: unexpected review packet projection")
    reviewed = app.review_finding(jid, pid, {"finding_id": "transition",
        "evidence": blind["finding_evidence"]["transition"], "reviewer": "lab-reviewer",
        "premise": premise, "test_link": "unknown", "notes": "Predetermined test judgment.",
        "second_observation": control, "independence_basis": "The observed target can differ from the design."})
    if reviewed["status"] != expected:
        raise AssertionError(f"{case}: unexpected finding status")
    first, = app.record_decisions(jid)
    expected_decision = "FINDINGS_REVIEWED" if expected.startswith("REVIEWED_") else "FINDINGS_PENDING_REVIEW"
    app = app_class(workspace)
    report = app.report(jid)
    row, = report["json"]["projects"]
    finding, = row["findings"]
    if (finding["status"], row["decision"]) != (expected, expected_decision) or f"**{expected}**" not in report["markdown"]:
        raise AssertionError(f"{case}: finding changed after reopening")
    repeated, = app.record_decisions(jid)
    if first["object"] != repeated["object"] or len(app.decisions(jid)) != 1:
        raise AssertionError(f"{case}: same decision was recorded twice")

    project.write_text(original + "\nThe target snapshot is now revised.\n", encoding="utf-8")
    app.import_projects(project, name="Lab project")
    stale, = app.record_decisions(jid)
    history = app.decisions(jid)
    if (stale["decision"] != "STALE" or stale["findings"][0]["status"] != "STALE"
            or stale["previous"] != first["object"] or len(history) != 2
            or history[0]["findings"][0]["status"] != expected):
        raise AssertionError(f"{case}: stale decision or history disagrees")


def main(checkout):
    git = ["git", "-C", str(checkout)]
    actual = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    if actual != TARGET or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip():
        raise ValueError("Use the clean, pinned dsh-paper2agent checkout")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(checkout / "src"))
    from paper2project.core import App

    outcomes = Counter()
    for case, observation, premise, expected in CASES:
        for proposal in ("candidate", "not_applicable"):
            with TemporaryDirectory(prefix="hyra-review-") as folder:
                scenario(App, Path(folder), case, observation, premise, expected, proposal)
            outcomes[expected] += 1
    total = sum(outcomes.values())
    print(json.dumps({"target_commit": TARGET, "dossiers": total, "finding_status_counts": outcomes,
                      "packet_pairs_matched": total, "reopen_and_idempotence_passed": total,
                      "stale_history_passed": total}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    main(parser.parse_args().checkout.resolve())
