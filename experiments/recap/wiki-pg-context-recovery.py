"""Test scope- and source-bound recovery of omitted Wiki_PG context."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
BUDGET = 960
HOST = "FixtureHost"
PORT = "5432"
KEYS = ("source_file", "sha256", "location", "text", "pg_port")
CASES = {
    "linked_recovery": (False, False, True, "restored"),
    "direct_recovery": (False, True, True, "baseline"),
    "missing_link": (False, False, False, "no_link"),
    "another_port": (False, False, False, "wrong_scope"),
    "source_changed": (False, False, False, "stale_source"),
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def excerpt(chunk):
    return {key: chunk[key] for key in KEYS}


def context(records):
    result = []
    for row in records:
        if len(json.dumps(result + [row], ensure_ascii=False).encode()) <= BUDGET:
            result.append(row)
    return result


def reference(record):
    return {key: record[key] for key in KEYS if key != "text"}


def restore(root, record, port):
    if record["pg_port"] != port:
        return None, "wrong_scope"
    payload = (root / record["source_file"]).read_bytes()
    if sha256(payload).hexdigest() != record["sha256"]:
        return None, "stale_source"
    start, end = map(int, record["location"].removeprefix("lines:").split("-"))
    text = "\n".join(payload.decode("utf-8").splitlines()[start - 1:end])
    return {**record, "text": text}, "restored"


def trial(build, search, seed):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        registry = root / "operations/clusters/registry.yaml"
        registry.parent.mkdir(parents=True)
        registry.write_text(f"clusters:\n  {HOST}: fixture\n", encoding="utf-8")
        reports = root / "raw/deep-report/fixture" / HOST
        reports.mkdir(parents=True)
        early, current, decoy = (reports / name for name in ("early.md", "current.md", "decoy.md"))

        def write(path, port, stamp, line):
            path.write_text(f"**Date:** {stamp}\n## PostgreSQL\n### Инстанс на порту {port}\n"
                            f"#### Observation\n{line}\n", encoding="utf-8")

        old_term, new_term, other_term = (f"{term}{seed}" for term in ("initialmarker", "recentmarker", "othermarker"))
        write(early, PORT, "2026-11-23T00:00:00Z", f"{old_term} exact recovery condition {seed}.")
        write(current, PORT, "2026-11-25T00:00:00Z", f"{new_term} current observation {seed}.")
        write(decoy, "5433", "2026-11-23T00:00:00Z", f"{other_term} unrelated instance {seed}.")
        build(root)

        def lookup(term, port=PORT):
            return [excerpt(chunk) for chunk in search(root, term, host=HOST, port=port, semantic=False)["chunks"]]

        old, = lookup(old_term)
        latest, = lookup(new_term)
        unrelated, = lookup(other_term, "5433")
        if restore(root, reference(old), PORT) != (old, "restored") or lookup(other_term):
            raise AssertionError("The baseline did not enforce exact scope")
        # Simulate compaction. The separate graph stores coordinates, not the omitted text.
        node = tuple(reference(latest).values())
        results = []
        for case, expected in CASES.items():
            if case == "source_changed":
                write(early, PORT, "2026-11-23T00:00:00Z", f"{old_term} revised recovery condition {seed + 1}.")
            before = {path: digest(path) for path in (early, current, decoy)}
            query = f"{new_term} {old_term}" if case == "direct_recovery" else new_term
            static, lexical = context([latest]), context(lookup(query))
            graph = {} if case == "missing_link" else {node: reference(unrelated if case == "another_port" else old)}
            link = next((graph[tuple(reference(row).values())] for row in lexical
                         if tuple(reference(row).values()) in graph), None)
            restored, reason = None, "no_link"
            if old in lexical:
                reason = "baseline"
            elif link:
                restored, reason = restore(root, link, PORT)
            derived = context(lexical + [restored]) if restored else lexical
            hits = old in static, old in lexical, old in derived, reason
            if hits != expected or (case == "another_port" and unrelated in derived):
                raise AssertionError((seed, case, hits))
            if context(lookup(query)) != lexical or {path: digest(path) for path in before} != before:
                raise AssertionError("Source or baseline changed during recovery")
            results.append({"case": case, "retained_only_hit": hits[0], "lexical_hit": hits[1],
                            "linked_hit": hits[2], "link_decision": reason, "sources_unchanged": True})
        return {"fixture": seed, "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_checkout", type=Path)
    source = parser.parse_args().wiki_checkout.resolve()
    git = ["git", "-C", str(source)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != REVISION
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        parser.error(f"Expected clean Wiki_PG checkout at {REVISION}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "Wiki_PG/ingestion"))
    from build_system_store import build
    from evidence_search import search

    seeds = (2, 11, 19, 23, 39, 47)
    rows = [trial(build, search, seed) for seed in seeds]
    if rows != [trial(build, search, seed) for seed in seeds]:
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "repeat_count": 2, "context_budget_bytes": BUDGET,
                      "status": "PASS", "fixtures": rows}, indent=2))


if __name__ == "__main__":
    main()
