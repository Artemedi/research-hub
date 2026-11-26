"""Check citation extraction and review routing against authored reports."""

import argparse
import ast
from collections import Counter
from contextlib import closing
import hashlib
import importlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace


UPSTREAM = "8f192b88bf777e2ad6da5e07e4b2ad7af40e2d7c"
TARGET = "c3bbe09bddf54b0efdcc0da1f17e1446dd35a4fd"
CORE_HASHES = {
    "citecheck": "53405db780de66866e8b3131f7a99edc1341832095fcc7b0888eaae69684a465",
    "patterns": "e7dbe6b0b804cc784dde71e9d10fff3946258e5e91c806443096ba825efdbadc",
    "fetcher": "7baa0fa70003e778c79d6fcc0de76995f1bc99b451f8b77a73009676c3711486",
    "scholar": "42bd51802d950ca89a219828f790d083cea31847b8a3c6595a25edaf0acf487d",
}
TARGET_HASH = "fd37058e63efb578c7f3fc6864ba658b0e2c53722f454d32e6efa03d85d39a2b"
ACTORS = ("Alder", "Birch", "Cedar", "Dogwood", "Elm", "Fir", "Ginkgo", "Hazel",
          "Juniper", "Larch", "Maple", "Oak")


def verify(root, sha):
    def git(*args):
        return subprocess.check_output(["git", "-C", root, *args], text=True).strip()

    if git("rev-parse", "HEAD") != sha or git("status", "--porcelain", "-uno"):
        raise ValueError(f"Expected clean tracked files at {sha}")


def pinned_bytes(path, digest):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Source digest mismatch: {path.name}")
    return data


def load_upstream(root):
    verify(root, UPSTREAM)
    src = root / "src" / "hyperresearch"
    for module, digest in CORE_HASHES.items():
        pinned_bytes(src / "core" / f"{module}.py", digest)
    # Only import the core modules, without initializing the parent application.
    for name, path in (("hyperresearch", src), ("hyperresearch.core", src / "core")):
        module = ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    return importlib.import_module("hyperresearch.core.citecheck")


def load_advisory(root):
    verify(root, TARGET)
    data = pinned_bytes(root / "src/paper2project/core.py", TARGET_HASH)
    symbols = {"CONDITION", "NEGATION", "QUANTITY"}
    tree = ast.parse(data)
    nodes = [
        node for node in tree.body if (
            isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in symbols for target in node.targets
            )
        ) or (isinstance(node, ast.FunctionDef) and node.name == "citation_signals")
    ]
    assert len(nodes) == 4
    scope = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<pinned advisory>", "exec"), scope)
    return scope["citation_signals"]


def corpus(db, style):
    lines = ["# Fixture report", "```text", "[999] [[missing-code-note]]", "```", ""]
    sources = []
    labels = {}
    for number, actor in enumerate(ACTORS, 1):
        note = f"fixture-{actor.lower()}"
        url = f"https://source.invalid/{note}"
        db.execute("INSERT INTO notes VALUES(?, ?, ?, NULL)", (note, actor, url))
        db.execute("INSERT INTO sources VALUES(?, ?)", (url, note))
        subject = f"The {actor} scheduler stores maintenance summaries"
        base = f"{subject} before reconciliation only for internal queues"
        quantity = f"The {actor} processor records a median duration of 20 ms"
        db.executemany("INSERT INTO claims VALUES(?, ?, '', '')", ((note, base), (note, quantity)))
        cases = (
            ("exact", base, base, True),
            ("paraphrase", f"Only internal queues receive {actor} maintenance summaries ahead of reconciliation", base, True),
            ("reversal", f"{subject} after reconciliation only for internal queues", base, False),
            ("missing_condition", f"{subject} before reconciliation", base, False),
            ("negation", f"It is not true that the {base.removeprefix('The ')}", base, False),
            ("changed_number", quantity.replace("20 ms", "30 ms"), quantity, False),
            ("changed_unit", quantity.replace("20 ms", "20 s"), quantity, False),
            ("unrelated", f"Rain fell near the fictional {actor} station", base, False),
        )
        marker = f"[{number}]" if style == "numbered" else f"[[{note}]]"
        for category, claim, quote, supported in cases:
            sentence = f"{claim} {marker}."
            lines.append(sentence)
            labels[sentence] = (category, claim, quote, supported, note)
        sources.append(f"[{number}] {actor} {url}")
    marker = "[999]" if style == "numbered" else "[[missing-note]]"
    dangling = f"A citation has no matching note {marker}."
    lines.append(dangling)
    if style == "numbered":
        lines.extend(("", "## Sources", *sources))
    return "\n".join(lines) + "\n", labels, dangling


def normalize(text):
    return " ".join(text.casefold().split()).strip(" .")


def measure(pairs, queued, labels):
    counts = Counter(dict.fromkeys(("support_auto", "unsupported_auto", "support_queued",
                                   "unsupported_queued", "support_omitted", "unsupported_omitted"), 0))
    for pair in pairs:
        sentence = pair["sentence"]
        if sentence not in labels:
            continue
        support = "support" if labels[sentence][3] else "unsupported"
        state = "auto" if pair["verdict"] == "supported-mechanical" else (
            "queued" if sentence in queued else "omitted"
        )
        counts[f"{support}_{state}"] += 1
    return dict(counts)


def replay(core, advisory, style, temp):
    with closing(sqlite3.connect(":memory:")) as db:
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE notes(id TEXT PRIMARY KEY, title TEXT, source TEXT, doi TEXT);
            CREATE TABLE sources(url TEXT PRIMARY KEY, note_id TEXT);
            CREATE TABLE claims(note_id TEXT, claim TEXT, quoted_support TEXT, numbers TEXT);
        """)
        report, labels, dangling = corpus(db, style)
        path = temp / f"{style}.md"
        path.write_text(report, encoding="utf-8")
        vault = SimpleNamespace(db=db, run_dir=lambda tag: temp / tag)
        saved = {}
        for name, rate in (("stock_default", 0.6), ("stock_full_sampling", 1.0)):
            result = core.write_pairs_file(vault, name, path, rate)
            receipt = json.loads((temp / name / "cite-check-pairs.json").read_text(encoding="utf-8"))
            assert receipt == result
            assert [pair["sentence"] for pair in receipt["dangling"]] == [dangling]
            assert receipt["summary"]["total"] == len(labels) + 1
            saved[name] = {pair["sentence"] for pair in receipt["sampled_for_llm"]}

        pairs = core.extract_pairs(report, db)
        assert len(pairs) == len(labels) + 1
        assert {pair["sentence"] for pair in pairs} == labels.keys() | {dangling}
        assert all(pair["note_id"] == labels[pair["sentence"]][4]
                   for pair in pairs if pair["sentence"] in labels)
        triaged = core.triage_pairs(pairs, db)["pairs"]
        auto_by_category = Counter(
            labels[pair["sentence"]][0] for pair in triaged if pair["verdict"] == "supported-mechanical"
        )
        assert auto_by_category == dict.fromkeys(("exact", "reversal", "missing_condition", "negation"), len(ACTORS))
        for name, rate in (("stock_default", 0.6), ("stock_full_sampling", 1.0)):
            assert {pair["sentence"] for pair in core.sample_needs_llm(triaged, rate)} == saved[name]
        result = {name: measure(triaged, queued, labels) for name, queued in saved.items()}

        exact_pairs = []
        for pair in triaged:
            if pair["sentence"] not in labels:
                continue
            _, _, _, _, note = labels[pair["sentence"]]
            assert pair["note_id"] == note
            text = normalize(pair["sentence"].replace(pair["marker"], ""))
            stored = db.execute("SELECT claim FROM claims WHERE note_id = ?", (note,)).fetchall()
            verdict = "supported-mechanical" if any(text == normalize(row["claim"]) for row in stored) else "needs-llm"
            exact_pairs.append({**pair, "verdict": verdict})
        exact_queue = {pair["sentence"] for pair in exact_pairs if pair["verdict"] == "needs-llm"}
        result["exact_all_other_pairs"] = measure(exact_pairs, exact_queue, labels)

        signals = Counter()
        for category, claim, quote, _, _ in labels.values():
            if advisory(quote, claim):
                signals[category] += 1
        assert signals == dict.fromkeys(("missing_condition", "negation", "changed_unit", "unrelated"), len(ACTORS))
        assert result["exact_all_other_pairs"]["unsupported_auto"] == 0
        assert result["exact_all_other_pairs"]["unsupported_queued"] == len(ACTORS) * 6
        result["stock_auto_by_category"] = dict(auto_by_category)
        result["target_advisory_by_category"] = dict(signals)
        result["parsed_pairs"] = len(pairs)
        result["dangling_findings"] = 1
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    core = load_upstream(args.upstream.resolve())
    advisory = load_advisory(args.target.resolve())
    with TemporaryDirectory() as directory:
        results = {style: replay(core, advisory, style, Path(directory)) for style in ("numbered", "wiki")}
        for _ in range(2):
            assert results == {style: replay(core, advisory, style, Path(directory)) for style in results}
    print(json.dumps({
        "upstream": UPSTREAM, "target": TARGET, "core_sha256": CORE_HASHES, "target_sha256": TARGET_HASH,
        "repeats": 3, "model_calls": 0, "results": results,
    }, indent=2))


if __name__ == "__main__":
    main()
