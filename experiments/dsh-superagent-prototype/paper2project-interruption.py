"""Exercise Paper2Project recovery and decision history with a real local writer lock."""

import argparse
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import selectors
import subprocess
import sys
from tempfile import TemporaryDirectory


FIXTURE = Path(__file__).resolve().parents[1] / "benchshield/paper2project-report-replay.py"
LOCKER = """
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
from paper2project.store import Store
with Store(sys.argv[2]).writer():
    print("READY", flush=True)
    sys.stdin.read()
"""


def trial(root, checkout, fixture, app_class, execution, workspace_busy, seed, terminate, partial):
    workspace = root / "workspace"
    app = app_class(workspace)
    jid, experiment, expected = fixture.prepare(app, root, seed)
    run = {key: experiment[key] for key in ("job_id", "plan", "source_tree", "input_tree")}
    run.update(id="run-lab-first", experiment_id=experiment["id"], status="RUNNING", arms={})
    if partial:
        result = app.store.put_json({"total": expected})
        run["arms"]["baseline"] = {"result": result, "result_sha256": result, "exit_code": 0}
    app.store.save("run", run["id"], run)

    worker = subprocess.Popen([sys.executable, "-B", "-c", LOCKER, str(checkout), str(workspace)],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        with selectors.DefaultSelector() as watcher:
            watcher.register(worker.stdout, selectors.EVENT_READ)
            if not watcher.select(15) or worker.stdout.readline().strip() != "READY":
                raise AssertionError("The disposable lock owner did not start")
        project, = app.report(jid)["json"]["projects"]
        if project["experiments"][0]["status"] != "RUNNING" or worker.poll() is not None:
            raise AssertionError("Report lost the live attempt")
        try:
            app.record_decisions(jid)
        except workspace_busy:
            pass
        else:
            raise AssertionError("Decision writer did not respect the live workspace lock")
        if app.decisions(jid) or app.store.get("run", run["id"]) != run:
            raise AssertionError("Inspection or failed write changed the live attempt")
        if terminate:
            worker.kill()
        else:
            worker.stdin.close()
        exit_status = worker.wait(timeout=10)
        if (terminate and exit_status >= 0) or (not terminate and exit_status != 0):
            raise AssertionError("Unexpected lock-holder exit")
    finally:
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=10)
        worker.stdin.close()
        worker.stdout.close()

    app = app_class(workspace)
    project, = app.report(jid)["json"]["projects"]
    if (project["experiments"][0]["status"] != "INTERRUPTED"
            or project["decision"] != "EXPERIMENT_INCOMPLETE"
            or app.store.get("run", run["id"]) != run):
        raise AssertionError("Idle report did not project interruption without writing")
    first, = app.record_decisions(jid)
    again, = app.record_decisions(jid)
    recovered = app.store.get("run", run["id"])
    if (first["decision"] != "EXPERIMENT_INCOMPLETE" or first["object"] != again["object"]
            or len(app.decisions(jid)) != 1 or not recovered.get("recovered_at")
            or recovered["status"] != "INTERRUPTED" or recovered["arms"] != run["arms"]):
        raise AssertionError("Durable recovery discarded evidence or duplicated the decision")

    fixture.record(app, execution, experiment, "match", expected, seed)
    project, = app.report(jid)["json"]["projects"]
    second, = app.record_decisions(jid)
    last, = app.record_decisions(jid)
    if (project["decision"] != "MIXED_EVIDENCE"
            or project["experiments"][0]["run_statuses"] != ["INTERRUPTED", "PASS"]
            or second["decision"] != "MIXED_EVIDENCE" or second["previous"] != first["object"]
            or last["object"] != second["object"] or len(app.decisions(jid)) != 2
            or app.store.get("run", run["id"]) != recovered):
        raise AssertionError("A later passing attempt rewrote or hid the interruption")


def main(checkout):
    spec = spec_from_file_location("report_fixture", FIXTURE)
    fixture = module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(fixture)
    git = ["git", "-C", str(checkout)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != fixture.TARGET
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        raise ValueError("Use the clean, pinned dsh-paper2agent checkout")
    sys.path.insert(0, str(checkout / "src"))
    from paper2project import execution
    from paper2project.core import App
    from paper2project.store import WorkspaceBusy

    exits, records = Counter(), Counter()
    for seed in (1, 4):
        for terminate in (False, True):
            for partial in (False, True):
                with TemporaryDirectory(prefix="paper2project-interruption-") as directory:
                    trial(Path(directory), checkout, fixture, App, execution, WorkspaceBusy,
                          seed, terminate, partial)
                exits["terminated" if terminate else "released"] += 1
                records["partial" if partial else "empty"] += 1
    total = sum(exits.values())
    print(json.dumps(dict(target_commit=fixture.TARGET, trials=total, exit_modes=exits,
                          first_attempts=records, live_guard_passed=total,
                          read_only_projection_passed=total, durable_recovery_passed=total,
                          mixed_history_passed=total, idempotent_writes_passed=total), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    main(parser.parse_args().checkout.resolve())
