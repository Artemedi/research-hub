"""Replay pinned issue publishing functions with an in-memory service."""

import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import random
import re
import subprocess
import sys
from types import SimpleNamespace


REVISION = "668689dded92affb16b6a3b3f63d4be43d3d80cd"
SOURCE_HASHES = {
    "entry": "543ea99a660a2402839b87bfea1b1d0f7a3587ecdfe3af5ad0b0b564b055ab90",
    "publisher": "9a110ecd8f9dea963f87dd5ae6d5647895a953bd58f4f9129ff88551b63b95ac",
}
SEEDS = (19, 47, 83)
CASES_PER_SCENARIO = 20


def load_functions(path, digest, names):
    source = Path(path).read_bytes()
    if hashlib.sha256(source).hexdigest() != digest:
        raise ValueError("Source does not match the pinned digest")
    nodes = {
        node.name: node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name in names
    }
    if nodes.keys() != set(names):
        raise ValueError("Pinned function bindings are incomplete")
    return compile(ast.Module(body=list(nodes.values()), type_ignores=[]), "<pinned>", "exec")


def reject_fallback():
    raise AssertionError("Unexpected fallback")


def replay(entry_code, publisher_code, bindings, scenario, arm, index):
    video_id = f"fixture_{index:05}"
    video = {"id": video_id, "title": "Synthetic video", "url": f"https://youtu.be/{video_id}"}
    effects = []
    attempts = []

    def command(args, **options):
        if args[:3] == ["gh", "issue", "list"] and options.get("check") is True:
            visible = [] if scenario == "lost_ack_hidden" else effects
            return SimpleNamespace(stdout=json.dumps([{"body": body} for body in visible]))
        if args[:3] != ["gh", "issue", "create"] or options.get("check") is not True:
            raise AssertionError("Unexpected command")
        body = args[args.index("--body") + 1]
        attempts.append(body)
        if len(attempts) == 1 and scenario != "acknowledged":
            if scenario != "failed_before_create":
                effects.append(body)
            raise subprocess.CalledProcessError(1, args)
        effects.append(body)
        return SimpleNamespace()

    def generate(*_):
        if arm == "fixed_url" or scenario != "lost_ack_without_url":
            return f"Synthetic analysis\n\n{video['url']}"
        return "Synthetic analysis"

    safe_builtins = {
        fn.__name__: fn for fn in (bool, dict, len, list, print, set, str, Exception, RuntimeError)
    }
    transport = SimpleNamespace(run=command)
    publisher = {
        "__builtins__": safe_builtins,
        "subprocess": transport,
        bindings["generate"]: generate,
    }
    exec(publisher_code, publisher)
    entry = {
        "__builtins__": safe_builtins,
        "json": json,
        "re": re,
        "subprocess": transport,
        bindings["videos"]: lambda: [video],
        bindings["fallback"]: reject_fallback,
        bindings["context"]: lambda: "Synthetic context",
        bindings["publish"]: publisher[bindings["publish"]],
    }
    exec(entry_code, entry)

    def run():
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                entry[bindings["entry"]]()
            except RuntimeError:
                return False
        return True

    first_ok = run()
    second_ok = run()
    return first_ok, second_ok, len(attempts), len(effects)


def main(bindings):
    entry = load_functions(
        bindings["entry_path"], SOURCE_HASHES["entry"], [bindings["entry"], bindings["lookup"]]
    )
    publisher = load_functions(
        bindings["publisher_path"], SOURCE_HASHES["publisher"], [bindings["publish"]]
    )
    # Independent expectations: first OK, repeat OK, publication attempts, effects.
    expected = {
        "acknowledged": ((True, True, 1, 1), (True, True, 1, 1)),
        "failed_before_create": ((False, True, 2, 1), (False, True, 2, 1)),
        "lost_ack_visible": ((False, True, 1, 1), (False, True, 1, 1)),
        "lost_ack_without_url": ((False, True, 2, 2), (False, True, 1, 1)),
        "lost_ack_hidden": ((False, True, 2, 2), (False, True, 2, 2)),
    }
    results = {}
    for arm_index, arm in enumerate(("baseline", "fixed_url")):
        arm_results = {}
        for seed in SEEDS:
            cases = list(expected) * CASES_PER_SCENARIO
            random.Random(seed).shuffle(cases)
            counts = {
                scenario: {"cases": 0, "duplicates": 0, "missing": 0, "attempts": 0}
                for scenario in expected
            }
            for index, scenario in enumerate(cases):
                outcome = replay(entry, publisher, bindings, scenario, arm, index)
                if outcome != expected[scenario][arm_index]:
                    raise AssertionError((arm, seed, scenario, outcome))
                _, _, attempts, effects = outcome
                counts[scenario]["cases"] += 1
                counts[scenario]["duplicates"] += effects > 1
                counts[scenario]["missing"] += effects == 0
                counts[scenario]["attempts"] += attempts
            arm_results[str(seed)] = counts
        results[arm] = arm_results
    return {
        "source_revision": REVISION,
        "source_sha256": SOURCE_HASHES,
        "real_provider_requests": 0,
        "cases_per_scenario_per_seed": CASES_PER_SCENARIO,
        "observed_counts": results,
    }


if __name__ == "__main__":
    bindings = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(main(bindings), indent=2))
