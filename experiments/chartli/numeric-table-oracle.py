"""Compare actual Chartli SVG coordinates and labels with authored duration tables."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

COMMIT = "3b39b97aeb564646437b2b7501b60541994d7575"
NAMESPACE = {"svg": "http://www.w3.org/2000/svg"}
SECONDS = "Duration (s)"
TIME = "Offset (s)"


def fixture(id, x, rows, expected, *, x_label=TIME, y_label=SECONDS):
    return dict(id=id, rows=rows, x=x, x_label=x_label, y_label=y_label, expected=expected)


def observe(svg, case):
    root = ET.fromstring(svg)
    lines = root.findall("svg:line", NAMESPACE)
    left = Decimal(lines[0].get("x1"))
    top = Decimal(lines[0].get("y1"))
    bottom = Decimal(lines[0].get("y2"))
    width = Decimal(lines[1].get("x2")) - left
    assert width == 320 and bottom - top == 120
    polylines = root.findall("svg:polyline", NAMESPACE)
    actual = [[tuple(map(Decimal, point.split(","))) for point in line.get("points").split()]
              for line in polylines]
    texts = root.findall("svg:text", NAMESPACE)
    labels = [x.text or "" for x in texts if x.get("font-size") == "10"]
    ticks = [x.text or "" for x in texts if x.get("text-anchor") == "end"]
    displayed_x = [x.text for x in texts if x.get("text-anchor") == "middle"
                   and x.get("font-size") == "11"]
    assert displayed_x == list(map(str, case["x"]))
    assert {case["x_label"], case["y_label"]}.issubset({x.text for x in texts})
    assert len(actual) == len(case["rows"][0]) and all(len(p) == len(case["x"]) for p in actual)

    x = list(map(Decimal, case["x"]))
    x_positions = [left + width * (value - x[0]) / (x[-1] - x[0]) for value in x]
    findings = []
    if any(abs(point[0] - expected) > Decimal("0.5")
           for series in actual for point, expected in zip(series, x_positions, strict=True)):
        findings.append("x_spacing")

    columns = list(zip(*case["rows"], strict=True))
    missing = any(value is None for column in columns for value in column)
    if missing:
        values = [value for column in columns for value in column]
        assert all(label == "0" for label, value in zip(labels, values, strict=True)
                   if value is None)
        findings.append("missing_sample_plotted")
    else:
        raw = [[Decimal(str(value)) for value in column] for column in columns]
        lower = min(min(column) for column in raw)
        upper = max(max(column) for column in raw)
        assert upper > lower
        for observed, expected in zip(actual, raw, strict=True):
            ideal = [bottom - (bottom - top) * (value - lower) / (upper - lower)
                     for value in expected]
            if any(abs(point[1] - y) > Decimal("0.5")
                   for point, y in zip(observed, ideal, strict=True)):
                findings.append("shared_y_geometry")
                break
        if list(map(Decimal, ticks)) != [upper, (lower + upper) / 2, lower]:
            findings.append("numeric_y_ticks")
        if list(map(Decimal, labels)) != [value for column in raw for value in column]:
            findings.append("duration_labels")

    assert findings == case["expected"], (case["id"], findings, case["expected"])
    return {
        "id": case["id"], "input_table": {"x_seconds": case["x"],
                                        "duration_seconds": case.get("source_seconds", case["rows"])},
        "render_input_rows": case["rows"],
        "axes": [case["x_label"], case["y_label"]],
        "points": [[[int(v) for v in point] for point in series] for series in actual],
        "labels": labels, "y_ticks": ticks, "errors": findings,
        "presentation": "chart_and_source_table" if not findings else "source_table_only",
        "svg_sha256": hashlib.sha256(svg.encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--node", default="node")
    args = parser.parse_args()
    source = args.source.resolve()

    def git(*items):
        return subprocess.check_output(["git", "-C", str(source), *items], text=True).strip()

    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Use a clean Chartli checkout at " + COMMIT)
    tiny = [[0.0001], [0.0002], [0.0003]]
    scaled = [[int(Decimal(str(row[0])) * 1_000_000)] for row in tiny]
    assert [Decimal(row[0]) / 1_000_000 for row in scaled] == [
        Decimal(str(row[0])) for row in tiny
    ]
    usual_x = [0, 10, 20]
    cases = [
        fixture("regular_seconds", usual_x, [[1], [3], [5]], []),
        fixture("irregular_seconds", [0, 10, 40], [[1], [3], [5]], ["x_spacing"]),
        fixture("different_series_same_unit", usual_x, [[0, 10], [10, 10], [20, 30]],
                ["shared_y_geometry", "numeric_y_ticks"]),
        fixture("omitted_series_sample", usual_x, [[0, 10], [10, None], [20, 30]],
                ["missing_sample_plotted"]),
        fixture("rounded_seconds", usual_x, tiny, ["numeric_y_ticks", "duration_labels"]),
        fixture("exact_microseconds", usual_x, scaled, [], y_label="Duration (µs)"),
    ]
    cases[-1]["source_seconds"] = tiny
    renderer = Path(__file__).resolve().with_name("render-numeric-fixtures.mjs")

    def run():
        output = subprocess.check_output([args.node, str(renderer), str(source)],
                                         input=json.dumps(cases), text=True, encoding="utf-8")
        receipt = json.loads(output)
        reports = receipt["reports"]
        assert [report["id"] for report in reports] == [case["id"] for case in cases]
        return dict(node=receipt["node"], cases=[
            observe(report["svg"], case)
            for report, case in zip(reports, cases, strict=True)
        ])

    first = run()
    assert run() == run() == first
    print(json.dumps(dict(source_commit=COMMIT, repetitions=3, **first), indent=2))


if __name__ == "__main__":
    main()
