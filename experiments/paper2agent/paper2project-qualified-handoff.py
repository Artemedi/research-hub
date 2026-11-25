"""Replay a document-only Paper2Agent handoff and its revision lifecycle."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

REVISION = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
PAPER = "fixture"
LIMIT = "The supplementary material is pending."


def review(p2a, work, limited):
    p2a.write(work / "verification.json", {
        "status": "reviewed_with_limitations" if limited else "reviewed",
        "mechanical_ok": True, "all_sources_agent_reviewed": True,
        "limitations": [LIMIT] if limited else [],
    })


def attest(p2a, work):
    path = work / "independent-review.json"
    p2a.write(path, {"decision": "PASS", "reviewer": "fixture-reader",
                     "fingerprint": p2a.review_fingerprint(PAPER)})
    return p2a.attest(PAPER, path)["fingerprint"]


def rejected(p2a, workspace):
    try:
        p2a.handoff(PAPER, workspace)
    except ValueError as error:
        if "requires current qualified evidence" not in str(error):
            raise
    else:
        raise AssertionError("The handoff should have refused this package")


def check_report(app, job, source, original_bytes, stale, path):
    report = app.report(job)
    if (report["json"]["snapshots"]["research"] != source
            or bool(report["json"]["stale"]) != stale
            or app.context(job)["research_source"] != source):
        raise AssertionError("Historical source or job freshness was lost")
    app.export(job, path, include_memory=True)
    with ZipFile(path) as archive:
        stored = json.loads(archive.read("report.json"))["snapshots"]["research"]
        if stored != source:
            raise AssertionError("Export lost the source record")
        for name in archive.namelist():
            payload = archive.read(name)
            if any(original in payload for original in original_bytes):
                raise AssertionError("Report export included original document bytes")


def scenario(p2a, App, seed):
    with TemporaryDirectory() as directory, patch.object(p2a, "ROOT", Path(directory)):
        root = Path(directory)
        papers = root / "sources/papers" / PAPER
        papers.mkdir(parents=True)
        main = f"%PDF-fixture-main-{seed}".encode()
        (papers / "main.pdf").write_bytes(main)
        originals = [{"file": "main.pdf", "role": "main", "sha256": hashlib.sha256(main).hexdigest()}]
        p2a.write(root / "papers.json", {"papers": [{"id": PAPER, "title": "Fixture arithmetic notes"}]})
        manifest = papers / "manifest.json"
        # The package can be structurally complete even when source acquisition is unfinished.
        p2a.write(manifest, {"full_text_status": "INCOMPLETE", "sources": originals})
        package = root / f"outputs/{PAPER}/run/{PAPER}-paper"
        text = package / "references/paper.md"
        text.parent.mkdir(parents=True)
        text.write_text(f"# Arithmetic\n\nThe fixture sum is {seed}.\n", encoding="utf-8")
        work = root / "review" / PAPER
        p2a.write(work / "bundle.json", {})
        p2a.write(work / "build.json", {"output": f"/work/outputs/{PAPER}/run/{PAPER}-paper",
                  "files": {"references/paper.md": p2a.digest(text)}})
        review(p2a, work, limited=True)
        workspace = root / "workspace"
        app = App(workspace)

        attest(p2a, work)
        rejected(p2a, workspace)
        if app.research():
            raise AssertionError("Incomplete source was registered")
        p2a.write(manifest, {"full_text_status": "COMPLETE", "sources": originals})
        rejected(p2a, workspace)
        first_fingerprint = attest(p2a, work)
        first = p2a.handoff(PAPER, workspace)
        prior, = app.research()
        qualification = prior["qualification"]
        if (prior["coverage"] != "PAPER2AGENT_REVIEW_RECORDED" or prior["limitations"] != [LIMIT]
                or qualification["fingerprint"] != first_fingerprint
                or qualification["source_artifacts"] != [{"role": "main", "sha256": originals[0]["sha256"]}]):
            raise AssertionError("Qualified limitations or main source were lost")
        project_path = root / "project.md"
        project_path.write_text("Synthetic project checks arithmetic.", encoding="utf-8")
        project, = app.import_projects(project_path)
        job = app.create_job(PAPER, [project["id"]])["id"]

        supplement = f"%PDF-fixture-supplement-{seed}".encode()
        (papers / "supplement.pdf").write_bytes(supplement)
        originals.append({"file": "supplement.pdf", "role": "supplement",
                          "sha256": hashlib.sha256(supplement).hexdigest()})
        p2a.write(manifest, {"full_text_status": "COMPLETE", "sources": originals})
        review(p2a, work, limited=False)
        rejected(p2a, workspace)
        if app.research() != [prior] or app.status(job)["stale"]:
            raise AssertionError("Unaccepted package revision changed project state")
        check_report(app, job, prior, (main, supplement), False, root / "before.zip")

        second_fingerprint = attest(p2a, work)
        second = p2a.handoff(PAPER, workspace)
        current, = app.research()
        references = [{"role": row["role"], "sha256": row["sha256"]} for row in originals]
        if (first["snapshot"] == second["snapshot"] or first_fingerprint == second_fingerprint
                or current["qualification"]["fingerprint"] != second_fingerprint
                or current["qualification"]["source_artifacts"] != references or current["limitations"]
                or app.status(job)["stale"] != [f"research:{PAPER}"]):
            raise AssertionError("Qualified update or stale-job detection did not work")
        if [app.store.blob(row["sha256"]) for row in references] != [main, supplement]:
            raise AssertionError("Stored originals differ from fixture bytes")
        job2 = app.create_job(PAPER, [project["id"]])["id"]
        check_report(app, job, prior, (main, supplement), True, root / "historical.zip")
        check_report(app, job2, current, (main, supplement), False, root / "current.zip")
        return {"fixture": seed, "incomplete_rejected": True, "changed_fingerprint_rejected": True,
                "prior_review_unchanged_before_acceptance": True, "historical_job_stale_after_acceptance": True,
                "before_roles": ["main"], "after_roles": ["main", "supplement"],
                "historical_limitation_preserved": True, "reports_exported_without_originals": 3}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("checkout", type=Path)
    source = cli.parse_args().checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        cli.error(f"Expected clean dsh-paper2agent checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(source / "tools"), str(source / "src")]
    import p2a
    from paper2project.core import App

    fixtures = (4, 12, 23, 57)
    result = [scenario(p2a, App, seed) for seed in fixtures]
    if result != [scenario(p2a, App, seed) for seed in fixtures]:
        raise AssertionError("Repeat diverged")
    print(json.dumps({"revision": REVISION, "repeat_count": 2, "status": "PASS", "fixtures": result}, indent=2))


if __name__ == "__main__":
    main()
