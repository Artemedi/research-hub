"""Compare fixed, lexical and reusable span ranking on artificial Wiki_PG sources."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "d55721bb99bff25fae352341cfd630c048693d6b"
KNOWN = "operations/known.md"
UNSEEN = "operations/unseen.md"
LIMIT = 1
EXPECTED = {
    "frequent": (False, False, True, "prior_scores"),
    "rare_with_common": (False, True, False, "prior_scores"),
    "rare_only": (True, True, True, "lexical_fallback"),
    "unscored_source": (False, True, True, "lexical_fallback"),
    "revised_source": (False, True, True, "lexical_fallback"),
}


def key(row):
    return row["source_file"], row["sha256"], row["location"]


def start(row):
    return int(row["location"].removeprefix("lines:").split("-")[0])


def checked(root, row):
    payload = (root / row["source_file"]).read_bytes()
    lines = payload.decode("utf-8").splitlines()
    first, last = map(int, row["location"].removeprefix("lines:").split("-"))
    if sha256(payload).hexdigest() != row["sha256"] or "\n".join(lines[first - 1:last]) != row["text"]:
        raise AssertionError("Selected evidence does not match its cited source range")
    return row


def materialize(candidates, scores):
    scored = [row for row in candidates if scores[key(row)]]
    if not scored:
        return candidates[:LIMIT], "lexical_fallback"
    return sorted(candidates, key=lambda row: -scores[key(row)])[:LIMIT], "prior_scores"


def trial(build, search, seed):
    with TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "raw").mkdir()
        (root / "operations").mkdir()
        shared, rare, prior = f"common{seed}", f"rare{seed}", f"prior{seed}"
        text = (f"# Common summary\n{' '.join([shared] * 8)} overview.\n"
                f"## Exception\n{' '.join([rare] * 8)} exact exception.\n"
                f"## Routine\n{shared} {prior} expected routine.\n")
        for path in (KNOWN, UNSEEN):
            (root / path).write_text(text, encoding="utf-8")
        build(root)

        def candidates(question, path):
            return search(root, question, source_file=path, semantic=False)["chunks"]

        scores = Counter()
        # Fixed training requests are distinct from all held-out queries.
        for question in (prior, f"recall {prior}", f"explain {prior}"):
            cited, = candidates(question, KNOWN)
            scores[key(checked(root, cited))] += 1
        original_key, = scores
        rows = []
        for case, expected in EXPECTED.items():
            source, question, heading = KNOWN, f"{shared} {rare}", "## Exception"
            if case == "frequent":
                question, heading = shared, "## Routine"
            if case == "rare_only":
                question = rare
            if case == "unscored_source":
                source = UNSEEN
            if case == "revised_source":
                (root / KNOWN).write_text(text.replace("expected routine", "revised routine details"),
                                          encoding="utf-8")
                if build(root)["state"] != "complete":
                    raise AssertionError("Fixture revision was not indexed")
            result = candidates(question, source)
            prefix = sorted(result, key=start)[:LIMIT]
            lexical = result[:LIMIT]
            reused, reason = materialize(result, scores)
            hits = tuple(any(checked(root, row)["text"].startswith(heading) for row in view)
                         for view in (prefix, lexical, reused))
            if (*hits, reason) != expected:
                raise AssertionError((case, seed, hits, reason))
            rows.append({"case": case, "first_span_hit": hits[0], "lexical_hit": hits[1],
                         "reused_scores_hit": hits[2], "policy": reason,
                         "selected_views_verified": True})
        if scores != {original_key: 3}:
            raise AssertionError("Held-out questions changed the score store")
        return {"fixture": seed, "cases": rows}


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

    seeds = (2, 4, 11, 14, 19, 23, 39, 47, 53, 87)
    rows = [trial(build, search, seed) for seed in seeds]
    if rows != [trial(build, search, seed) for seed in seeds]:
        raise AssertionError("Repeat diverged")
    print(json.dumps({"wiki_revision": REVISION, "repeat_count": 2, "view_spans": LIMIT,
                      "status": "OBSERVED", "fixtures": rows}, indent=2))


if __name__ == "__main__":
    main()
