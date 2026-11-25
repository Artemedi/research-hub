"""Measure what registration and export retain on synthetic Paper2Project experiments."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile


COMMIT = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
SEEDS = (3, 7, 11, 19)


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], stderr=subprocess.PIPE).decode().strip()


def trial(root, app_class, execution, seed):
    origin = root / "origin"
    origin.mkdir()
    git(origin, "init", "-q", "-b", "lab")
    filename = "case.txt"
    path = origin / filename
    committed = f"Committed synthetic case {seed}.\n"
    worktree = f"Changed synthetic case {seed}.\n"
    path.write_text(committed, encoding="ascii")
    git(origin, "add", "--", filename)
    git(origin, "-c", "user.name=Lab", "-c", "user.email=lab@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", "Synthetic case")
    revision = git(origin, "rev-parse", "HEAD")
    path.write_text(worktree, encoding="ascii")
    profile, paper = root / "project.md", root / "paper.md"
    profile.write_text("# Lab project\n\nKeep experiment source available.\n", encoding="ascii")
    paper.write_text("# Lab study\n\nRecord an experiment source revision.\n", encoding="ascii")
    app = app_class(root / "workspace")
    project, = app.import_projects(profile, name="Lab project")
    research = app.import_research(paper, title="Lab study")
    pid = project["id"]
    jid = app.create_job(research["id"], [pid])["id"]
    app.submit_analysis(jid, {"summary": "Synthetic portability control", "assessments": [{
        "project_id": pid, "relevance": "candidate", "rationale": "Inspect source retention.",
        "missing_evidence": [], "citations": [
            {"document_id": f"project:{pid}:project.md", "start": 3, "end": 3,
             "quote": "Keep experiment source available."},
            {"document_id": "research:lab-study:paper.md", "start": 3, "end": 3,
             "quote": "Record an experiment source revision."},
        ],
    }]})
    plan = {"kind": "reproduction", "project_id": pid, "image": "test/image",
            "source": {"path": str(origin), "revision": revision, "license": "MIT"},
            "arms": {"baseline": ["false"], "candidate": ["false"]},
            "metrics": [{"name": "value", "path": "value", "expected": {"baseline": 1, "candidate": 1}}]}
    experiment = app.add_experiment(jid, plan)
    if not experiment["head_matches"]:
        raise AssertionError("Git source revision was not verified at registration")
    origin.rename(root / "offline-original")
    snapshot = Path(experiment["source_path"])
    if (execution.tree_hash(snapshot) != experiment["source_tree"]
            or execution.stale_reason(experiment, experiment)
            or (snapshot / filename).read_text(encoding="ascii") != worktree
            or git(snapshot, "show", "HEAD:case.txt") != committed.strip()):
        raise AssertionError("Registered source snapshot did not retain the original workspace")
    bundle = root / "export.zip"
    app.export(jid, bundle)
    with ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if set(archive.namelist()) != {*manifest["files"], "manifest.json"}:
            raise AssertionError("Export manifest does not cover the payload")
        for name, expected in manifest["files"].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise AssertionError("Export member digest differs")
            if worktree.encode("ascii") in archive.read(name) or committed.encode("ascii") in archive.read(name):
                raise AssertionError("Export unexpectedly contains the source payload")
        serialized = json.loads(archive.read(f"experiments/{experiment['id']}.json"))
        marker = "artifact:source:" + experiment["source_tree"]["sha256"][:16]
        if (serialized["plan"]["source"]["path"] != marker
                or serialized["experiment"]["source_tree"] != experiment["source_tree"]):
            raise AssertionError("Export source reference differs from registration")
    (snapshot / filename).write_text("Synthetic local edit.\n", encoding="ascii")
    if execution.stale_reason(experiment, experiment) != "source changed after the run":
        raise AssertionError("Changing the saved source did not invalidate the snapshot")


def main(checkout):
    if git(checkout, "rev-parse", "HEAD") != COMMIT or git(checkout, "status", "--porcelain"):
        raise ValueError("Use the clean, pinned dsh-paper2agent checkout")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(checkout / "src"))
    from paper2project import execution
    from paper2project.core import App

    for seed in SEEDS:
        with TemporaryDirectory(prefix="paper2project-snapshot-") as folder:
            trial(Path(folder), App, execution, seed)
    total = len(SEEDS)
    print(json.dumps(dict(target_commit=COMMIT, cases=total, local_snapshot_retained=total,
                          dirty_bytes_retained=total, export_manifest_verified=total,
                          exports_with_source_bytes=0, altered_snapshot_detected=total), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    main(parser.parse_args().checkout.resolve())
