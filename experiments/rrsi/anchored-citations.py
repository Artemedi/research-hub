"""Evaluate citation locations separately from behavior using pinned source."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

RRSI_SHA = "be50316e1db05914068a973f322770ef08ed7ba1"
AGENT_CONFIG_SHA = "489e074ab0daaadb732673c193047172a3744862"
ARMS = ("baseline", "exact_anchor", "neighbor_anchor")
FOLDS = (
    (("sum", "scale"), ("square", "clamp"), ("bit", "residue")),
    (("square", "clamp"), ("bit", "residue"), ("sum", "scale")),
    (("bit", "residue"), ("sum", "scale"), ("square", "clamp")),
)
# Independent expected outputs for inputs -2 and 3.
FIXTURES = {
    "sum": ("value + 4", (0, 7)),
    "scale": ("value * 5", (0, 15)),
    "square": ("value ** 2", (0, 9)),
    "clamp": ("min(value, 2)", (0, 2)),
    "bit": ("value & 1", (0, 1)),
    "residue": ("value % 3", (0, 0)),
}


def verify(root, commit):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    if git("rev-parse", "HEAD") != commit or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError(f"Expected clean tracked files at {commit}: {root}")


def anchored(source, finding, radius):
    """Match normalized quote text whose first character falls near its line."""
    rows = [" ".join(line.split()) for line in source.splitlines()]
    quote = " ".join(finding["evidence"].split())
    line = finding["line"]
    if not quote or not 1 <= line <= len(rows):
        return False
    for start in range(max(0, line - 1 - radius), min(len(rows), line + radius)):
        index = " ".join(row for row in rows[start:] if row).find(quote)
        if 0 <= index < len(rows[start]):
            return True
    return False


def samples(families, check_findings):
    rows = []
    for name in families:
        expr, (negative_output, positive_output) = FIXTURES[name]
        lines = [
            "def transform(value):", "    return (", f"        {expr}",
            "        if value >= 0", "        else 0", "    )", "",
            "def passthrough(value):", "    return value", "",
            "def duplicate(value):", "    return value", "", "# end of fixture",
        ]
        source = "\n".join(lines) + "\n"
        namespace = {}
        exec(compile(source, "<authored fixture>", "exec"), namespace)
        assert namespace["transform"](-2) == negative_output
        assert namespace["transform"](3) == positive_output
        assert namespace["passthrough"](3) == namespace["duplicate"](3) == 3

        # name, line, quote, expected anchor, function, input, claimed output
        cases = (
            ("exact", 3, expr, True, "transform", 3, positive_output),
            ("one_line_early", 2, expr, True, "transform", 3, positive_output),
            ("one_line_late", 4, expr, True, "transform", 3, positive_output),
            ("distant", 14, expr, False, "transform", 3, positive_output),
            ("fabricated", 3, "value * 901", False, "transform", 3, positive_output),
            ("unsupported_behavior", 3, expr, True, "transform", 3, positive_output + 1),
            ("multiline", 2, "\n".join(lines[1:6]), True, "transform", -2, negative_output),
            ("multiline_neighbor", 1, "\n".join(lines[1:6]), True, "transform", 3, positive_output),
            ("distant_duplicate", 5, "return value", False, "passthrough", 3, 3),
            ("local_duplicate", 12, "return value", True, "duplicate", 3, 3),
            ("blank_line", 7, "return value", False, "passthrough", 3, 3),
            ("out_of_range", 15, expr, False, "transform", 3, positive_output),
            ("missing_file", 3, expr, False, "transform", 3, positive_output),
        )
        filename = name + ".py"
        for kind, line, quote, expected_anchor, function, value, claimed in cases:
            finding = {
                "file": "absent.py" if kind == "missing_file" else filename,
                "line": line,
                "evidence": quote,
            }
            checked = check_findings([finding.copy()], [(filename, source)])[0]
            location = checked["location_ok"]
            rows.append({
                "id": f"{name}/{kind}",
                "citation": expected_anchor,
                "behavior": namespace[function](value) == claimed,
                "baseline": location and checked["evidence_found"],
                "exact_anchor": location and anchored(source, finding, 0),
                "neighbor_anchor": location and anchored(source, finding, 1),
                "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            })
    return rows


def scores(rows, arm):
    return {
        "cases": len(rows),
        "citation_correct": sum(row[arm] == row["citation"] for row in rows),
        "citation_false_accept": sum(row[arm] and not row["citation"] for row in rows),
        "citation_false_reject": sum(not row[arm] and row["citation"] for row in rows),
        "supported_but_wrong_behavior_accepted": sum(
            row[arm] and row["citation"] and not row["behavior"] for row in rows
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rrsi", required=True, type=Path)
    parser.add_argument("--agent-config", required=True, type=Path)
    args = parser.parse_args()
    verify(args.rrsi, RRSI_SHA)
    verify(args.agent_config, AGENT_CONFIG_SHA)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(args.rrsi.resolve()), str(args.agent_config.resolve() / "tools")]
    checker = importlib.import_module("review").check_findings
    from rrsi.config import RRSIConfig
    from rrsi.evaluate import TaskResult, aggregate
    from rrsi.selection import Candidate, select_round

    receipt = []
    for train_families, validation_families, holdout_families in FOLDS:
        train = samples(train_families, checker)
        validation = samples(validation_families, checker)
        assert set(train_families).isdisjoint(validation_families + holdout_families)
        assert set(validation_families).isdisjoint(holdout_families)

        def evaluate(arm):
            return aggregate(arm, 1, {
                row["id"]: TaskResult(rewards=[float(row[arm] == row["citation"])])
                for row in train
            })

        validation_scores = {arm: scores(validation, arm) for arm in ARMS}

        def validation_guard(incumbent, proposal):
            baseline = validation_scores[incumbent.job]
            candidate = validation_scores[proposal.job]
            return [] if (
                candidate["citation_false_reject"] <= baseline["citation_false_reject"]
                and candidate["citation_false_accept"] < baseline["citation_false_accept"]
            ) else ["Validation requires fewer false anchors with no loss of supported citations."]

        base = evaluate("baseline")
        candidates = [
            Candidate(arm, [{"component": "prompt", "hypothesis": arm}], ev=evaluate(arm))
            for arm in ARMS[1:]
        ]
        selected, _ = select_round(
            candidates, base, base.S, 0.02, RRSIConfig(),
            incumbent_counts={}, guard_fn=validation_guard,
        )
        assert selected and selected.variant == "neighbor_anchor", selected
        assert base.C is None  # No provider cost observed.
        holdout = samples(holdout_families, checker)
        holdout_scores = {arm: scores(holdout, arm) for arm in ARMS}
        assert holdout_scores[selected.variant]["citation_correct"] == len(holdout)
        assert holdout_scores[selected.variant]["supported_but_wrong_behavior_accepted"] > 0
        receipt.append({
            "families": {"train": train_families, "validation": validation_families,
                         "holdout": holdout_families},
            "selected": selected.variant,
            "train": {arm: scores(train, arm) for arm in ARMS},
            "validation": validation_scores,
            "holdout": holdout_scores,
            "holdout_cases": holdout,
        })

    print(json.dumps({
        "rrsi": RRSI_SHA,
        "agent_config": AGENT_CONFIG_SHA,
        "python": sys.version.split()[0],
        "provider_tokens": None,
        "folds": receipt,
    }, indent=2))


if __name__ == "__main__":
    main()
