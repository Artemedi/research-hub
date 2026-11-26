"""Read snapshots from the original CLI on this lab's authored windows."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
EXPECTED = {"Fixture Query": "textfield", "Fixture Run": "button"}


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def cli(binary, *args):
    run = subprocess.run(
        [binary, "--session", "research-toolkit", *args],
        capture_output=True, text=True, timeout=12, check=False,
    )
    try:
        payload = json.loads(run.stdout)
    except ValueError:
        raise RuntimeError(f"CLI failed to emit JSON: {run.stderr[-1000:]}") from None
    return run.returncode, payload


def observe(binary, process):
    deadline = time.monotonic() + 22
    last = {"status": "app_not_listed"}
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Fixture exited prematurely with code {process.returncode}")
        code, apps = cli(binary, "list-apps")
        if code == 0:
            matches = [item for item in nodes(apps)
                       if item.get("pid") == process.pid and isinstance(item.get("name"), str)]
            if len(matches) == 1:
                name = matches[0]["name"]
                same_name = [item for item in nodes(apps)
                             if item.get("name") == name and "pid" in item]
                if len(same_name) != 1:
                    raise RuntimeError("Fixture app name is ambiguous on the private bus.")
                code, snapshot = cli(binary, "snapshot", "--app", name, "-i", "--timeout-ms", "5000")
                if code != 0:
                    last = {"status": "snapshot_error",
                            "code": snapshot.get("error", {}).get("code")}
                else:
                    body = snapshot.get("data", snapshot)
                    entries = list(nodes(body.get("tree")))
                    observations = {
                        label: [{"role": entry.get("role"), "has_ref": bool(entry.get("ref_id"))}
                                for entry in entries if entry.get("name") == label]
                        for label in EXPECTED
                    }
                    absent = not any(entry.get("name") == "Fixture Absent" for entry in entries)
                    complete = body.get("complete") is True
                    identity_unproven = body.get("identity_unproven") is True
                    last = {"status": "observed", "controls": observations, "absent_control": absent,
                            "complete": complete, "identity_unproven": identity_unproven}
                    if complete and not identity_unproven and absent and all(
                        observations[label] == [{"role": role, "has_ref": True}]
                        for label, role in EXPECTED.items()
                    ):
                        last["status"] = "all_controls_matched"
                        return last
        time.sleep(0.5)
    return last


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary")
    parser.add_argument("toolkit", choices=["qt", "electron"])
    args = parser.parse_args()
    if args.toolkit == "qt":
        command = [sys.executable, str(ROOT / "qt-fixture.py")]
    else:
        command = ["/electron/electron", "--disable-dev-shm-usage", "--no-sandbox",
                   str(ROOT / "electron-fixture.cjs")]
    with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=sys.stderr) as fixture:
        try:
            outcome = observe(args.binary, fixture)
        finally:
            if fixture.poll() is None:
                fixture.terminate()
    print(json.dumps({"toolkit": args.toolkit, **outcome}, ensure_ascii=False))


if __name__ == "__main__":
    main()
