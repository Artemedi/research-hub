"""Compare fixed and adaptive routes through Wiki_PG's real lexical search."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory


TARGET = "d55721bb99bff25fae352341cfd630c048693d6b"
PORTS = ("5432", "5433")
REGION = "lab-zone"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture(root):
    cases = []
    for seed in range(6):
        host = f"lab-{seed}"
        folder = root / "raw/deep-report" / REGION / host
        folder.mkdir(parents=True)
        sequence = iter(range(60))

        def report(port, text):
            second = next(sequence)
            stamp = f"2026-11-25T00:00:{second:02}Z"
            path = folder / f"report_2026-11-25_00-00-{second:02}.md"
            path.write_text(f"**Date:** {stamp}\n## PostgreSQL test\n### Инстанс на порту {port}\n"
                            f"#### Observation\n{text}\n", encoding="utf-8")
            return path.relative_to(root).as_posix()

        for family, width, available in (("one", 1, 1), ("two", 2, 2), ("crowded", 2, 2),
                                         ("partial", 2, 1), ("absent", 1, 0)):
            facets = tuple((f"{family}{seed}{index}", PORTS[index]) for index in range(width))
            paths = [report(port, f"{token} confirmed observation detail long enough for a rich section.")
                     for token, port in facets[:available]]
            if family == "crowded":
                for _ in range(5):
                    report("5439", " ".join([token for token, _ in facets] * 8))
            cases.append((host, family, facets, tuple(paths) + (None,) * (width - available)))
    return cases


def match(chunks, token, port):
    return next((row for row in chunks if str(row.get("pg_port")) == port
                 and token in re.findall(r"[a-z0-9]+", row["text"].lower())), None)


def route(search, root, host, facets, strategy):
    calls, candidates = 0, 0

    def get(terms, port=None):
        nonlocal calls, candidates
        calls += 1
        chunks = search(root, terms, host=host, region=REGION, category="deep-report",
                        port=port, semantic=False, limit=8 if strategy == "single_default" else 3)["chunks"]
        candidates += len(chunks)
        return chunks

    if strategy == "split":
        rows = [match(get(token, port), token, port) for token, port in facets]
    else:
        chunks = get(" ".join(token for token, _ in facets))
        rows = [match(chunks, token, port) for token, port in facets]
        if strategy == "adaptive" and len(facets) > 1:
            for index, (token, port) in enumerate(facets):
                if rows[index] is None:
                    rows[index] = match(get(token, port), token, port)
    return rows, calls, candidates


def check_source(root, row, expected, token, port):
    if row["source_file"] != expected or str(row["pg_port"]) != port:
        return False
    raw = (root / expected).read_bytes()
    location = re.fullmatch(r"lines:(\d+)-(\d+)", row["location"])
    if not location or sha(raw) != row["sha256"]:
        return False
    start, end = map(int, location.groups())
    lines = raw.decode("utf-8").splitlines()
    return 1 <= start <= end <= len(lines) and token in "\n".join(lines[start - 1:end])


def run(search, build, root):
    cases = fixture(root)
    build(root)
    database = root / "System_Database/system.sqlite3"
    before = sha(database.read_bytes())
    modes = {}
    for strategy in ("single", "split", "adaptive", "single_default"):
        summary, families = Counter(), {}
        for host, family, facets, expected in cases:
            rows, calls, candidates = route(search, root, host, facets, strategy)
            complete = all(row is not None for row in rows)
            verified = set()
            selected = set()
            exact = 0
            for (token, port), path, row in zip(facets, expected, rows):
                if row is not None:
                    reference = (row["source_file"], row["location"])
                    selected.add(reference)
                    if path and check_source(root, row, path, token, port):
                        verified.add(reference)
                        exact += 1
            summary["sources_returned"] += len(selected)
            stats = families.setdefault(family, Counter())
            stats["calls"] += calls
            stats["cases"] += 1
            stats["verified_sources"] += len(verified)
            stats["complete_positive"] += int(all(expected) and complete and exact == len(facets))
            stats["incomplete_negative"] += int(not all(expected) and not complete)
            summary["calls"] += calls
            summary["candidates_returned"] += candidates
            summary["verified_sources"] += len(verified)
            summary["complete_positive"] += int(all(expected) and complete and exact == len(facets))
            summary["false_complete"] += int(complete and (not all(expected) or exact != len(facets)))
        modes[strategy] = dict(summary=summary, families=families)
    if before != sha(database.read_bytes()):
        raise AssertionError("Search changed the SQLite checkpoint")
    return dict(target_commit=TARGET, cases=len(cases), positive_cases=18, incomplete_cases=12,
                checkpoint_unchanged=True, modes=modes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    checkout = parser.parse_args().checkout.resolve()
    git = ["git", "-C", str(checkout)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != TARGET
            or subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()):
        raise ValueError("Use the clean, pinned Wiki_PG checkout")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(checkout / "Wiki_PG/ingestion"))
    from build_system_store import build
    from evidence_search import search

    with TemporaryDirectory(prefix="wiki-pg-drag-") as directory:
        print(json.dumps(run(search, build, Path(directory)), indent=2))
