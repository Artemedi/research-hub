"""Measure Pyright's warnings on authored calls to the pinned Paper2Project API."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

from paper2project.core import App

TARGET = "57991e6681ad683a5be8111b7d470fed5d53625b"
CALLS = {
    "status": "job",
    "docs": "job",
    "read": "job, doc",
    "context": "job",
    "report": "job",
    "import_projects": "project",
    "import_research": "source",
    "create_job": "'source', ['project']",
}


def cases():
    for method, args in CALLS.items():
        invented = "imagined_" + method
        yield method, "valid_direct", f"app.{method}({args})", None, None
        yield method, "valid_dynamic", f"getattr(app, {method!r})({args})", None, None
        yield method, "missing_method", f"app.{invented}({args})", AttributeError, invented
        yield method, "unknown_keyword", f"app.{method}({args}, extra_api_kw=True)", TypeError, "extra_api_kw"
        yield method, "missing_dynamic", f"getattr(app, {invented!r})({args})", AttributeError, invented


def setup(root):
    app = App(root / "store")
    project, source = root / "project.md", root / "source.md"
    project.write_text("A test project imports research documents.\n", encoding="utf-8")
    source.write_text("A test source records a bounded claim.\n", encoding="utf-8")
    app.import_projects(project)
    app.import_research(source)
    job = app.create_job("source", ["project"])["id"]
    doc = "research:source:source.md"
    return app, job, doc, project, source


def run(repository, node, pyright):
    def git(*args):
        return subprocess.check_output(["git", "-C", repository, *args], text=True).strip()

    if git("rev-parse", "HEAD") != TARGET or git("status", "--porcelain"):
        raise ValueError("Use a clean copy of the pinned target.")
    if subprocess.check_output([node, pyright, "--version"], text=True).strip() != "pyright 1.1.407":
        raise ValueError("Use Pyright 1.1.407.")

    header = (
        "from pathlib import Path\n"
        "from paper2project.core import App\n\n"
        "def adapter(app: App, job: str, doc: str, project: Path, source: Path):\n"
    )
    with TemporaryDirectory(prefix="p2p-api-lab-") as folder:
        root = Path(folder)
        inputs = root / "cases"
        inputs.mkdir()
        fixtures = list(cases())
        digest = hashlib.sha256()
        for method, variant, expr, _, _ in fixtures:
            name = f"{method}-{variant}.py"
            text = header + f"    return {expr}\n"
            (inputs / name).write_text(text, encoding="utf-8")
            digest.update((name + "\n" + text).encode("utf-8"))
        config = root / "pyrightconfig.json"
        config.write_text(json.dumps({
            "include": ["cases"],
            "extraPaths": [str(Path(repository).resolve() / "src")],
            "typeCheckingMode": "basic",
            "pythonVersion": "3.14",
        }), encoding="utf-8")

        runs = []
        for repetition in range(3):
            if repetition % 2:
                batch = fixtures[::-1]
            else:
                batch = fixtures
            started = perf_counter()
            codes = {}
            for method, variant, _, _, _ in batch:
                name = f"{method}-{variant}.py"
                codes[name] = compile((inputs / name).read_text(encoding="utf-8"), name, "exec")
            compile_ms = 1000 * (perf_counter() - started)

            started = perf_counter()
            checked = subprocess.run(
                [node, pyright, "--project", config, "--outputjson"],
                capture_output=True, text=True, timeout=60, check=False,
            )
            pyright_ms = 1000 * (perf_counter() - started)
            if checked.returncode not in (0, 1):
                raise RuntimeError(checked.stderr)
            diagnostics = json.loads(checked.stdout)["generalDiagnostics"]
            by_file = {name: [] for name in codes}
            other = []
            for warning in diagnostics:
                name = Path(warning["file"]).name
                if name in by_file and warning["range"]["start"]["line"] == 4:
                    by_file[name].append(warning)
                else:
                    other.append(warning)

            started = perf_counter()
            run_root = root / f"r{repetition}"
            run_root.mkdir()
            app_args = setup(run_root)
            rows = []
            for method, variant, _, expected, token in batch:
                name = f"{method}-{variant}.py"
                namespace = {}
                exec(codes[name], namespace)
                actual = None
                try:
                    result = namespace["adapter"](*app_args)
                    if result is None:
                        raise ValueError("Empty adapter result")
                except (AttributeError, TypeError) as error:
                    actual = type(error).__name__
                    if expected is None or type(error) is not expected or token not in str(error):
                        raise
                if expected and actual is None:
                    raise AssertionError(f"Expected {expected.__name__} in {name}")
                rules = [warning.get("rule") for warning in by_file[name]]
                checking_rule = "reportCallIssue" if variant == "unknown_keyword" else "reportAttributeAccessIssue"
                correct_reason = any(
                    token and token in warning["message"] and warning.get("rule") == checking_rule
                    for warning in by_file[name]
                )
                rows.append({"method": method, "variant": variant, "runtime_error": actual,
                             "rules": rules, "correct_reason": correct_reason})
            runtime_ms = 1000 * (perf_counter() - started)
            recognized = Counter(row["variant"] for row in rows if row["correct_reason"])
            valid_warnings = sum(bool(row["rules"]) and row["runtime_error"] is None for row in rows)
            passed = sum(recognized[key] for key in ("missing_method", "unknown_keyword")) >= 12 and not valid_warnings and not other
            runs.append({
                "known_reason_per_variant": dict(recognized), "valid_calls_warned": valid_warnings,
                "other_diagnostics": [warning.get("rule") for warning in other],
                "timing_ms": {"compile": round(compile_ms, 2), "pyright": round(pyright_ms, 2), "runtime": round(runtime_ms, 2)},
                "passed": passed, "cases": sorted(rows, key=lambda row: (row["method"], row["variant"])),
            })
        print(json.dumps({"target": TARGET, "python": platform.python_version(),
                          "pyright": "1.1.407", "cases_sha256": digest.hexdigest(), "runs": runs}, indent=2))
    return 0 if all(row["passed"] for row in runs) else 1


if __name__ == "__main__":
    sys.exit(run(*sys.argv[1:]))
