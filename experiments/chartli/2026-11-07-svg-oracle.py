#!/usr/bin/env python3
"""Independent GNU xmllint + Python ElementTree and finite-geometry oracle.

Checks rendered Chartli XML from original pinned TypeScript sources, not
authors' substring tests. Invalid XML and nonfinite geometry are distinct.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

INPUT = Path(os.environ["INPUT"])
SVG_DIR = Path(os.environ["SVG_DIR"])
OUTPUT = Path(os.environ["OUTPUT"])
PIN = "3b39b97aeb564646437b2b7501b60541994d7575"
INVALID_XML = {"bad_control_series", "bad_control_x"}
NONFINITE_GEOMETRY = {"nonfinite_nan", "nonfinite_inf", "large_exponent"}
XMLNS = "{http://www.w3.org/2000/svg}"


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def finite_geometry(root):
    attributes = {
        "svg": ("width", "height"),
        "circle": ("cx", "cy", "r"),
        "line": ("x1", "x2", "y1", "y2"),
        "text": ("x", "y"),
    }
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1]
        for attr in attributes.get(name, ()):
            if attr in element.attrib:
                try:
                    if not math.isfinite(float(element.attrib[attr])):
                        return False
                except ValueError:
                    return False
        if name == "polyline":
            for pair in element.attrib.get("points", "").split():
                try:
                    coordinates = [float(x) for x in pair.split(",")]
                    if len(coordinates) != 2 or not all(map(math.isfinite, coordinates)):
                        return False
                except ValueError:
                    return False
    return True


def verify():
    report = json.loads(INPUT.read_text())
    assert report["source_pin"] == PIN
    assert report["case_count"] == 16
    assert len({x["id"] for x in report["testcases"]}) == 16
    measurements = []
    for row in report["testcases"]:
        label = row["id"]
        assert row["file"] == label + ".svg"
        data = (SVG_DIR / row["file"]).read_bytes()
        assert sha(data) == row["raw_svg_sha256"]
        assert len(data) == row["bytes"]
        result = subprocess.run(
            ["xmllint", "--nonet", "--noout", str(SVG_DIR / row["file"])],
            capture_output=True, text=True)
        valid_xmllint = result.returncode == 0
        try:
            root = ET.fromstring(data)
            valid_et = True
        except ET.ParseError:
            valid_et = False
            root = None
        assert valid_et == valid_xmllint, label
        assert valid_xmllint == (label not in INVALID_XML), label
        is_finite = finite_geometry(root) if root is not None else False
        assert is_finite == (label not in INVALID_XML | NONFINITE_GEOMETRY), label
        if root is not None:
            assert root.tag == XMLNS + "svg"
            assert not any(node.tag.rsplit("}", 1)[-1] == "script" for node in root.iter())
        circles = len(root.findall(".//" + XMLNS + "circle")) if root is not None else None
        polylines = len(root.findall(".//" + XMLNS + "polyline")) if root is not None else None
        if label == "single_circles":
            assert (circles, polylines) == (3, 0)
        if label == "single_lines":
            assert (circles, polylines) == (0, 1)
        if label == "multi_circles_legend":
            assert (circles, polylines) == (8, 0)
        if label == "multi_lines_legend":
            assert (circles, polylines) == (2, 2)
        if label == "escaped_legend":
            text_nodes = [t.text or "" for t in root.findall(".//" + XMLNS + "text")]
            assert any("<script>alert(1)</script>" in t for t in text_nodes)
        if label == "escaped_x_y_labels":
            text_nodes = [t.text or "" for t in root.findall(".//" + XMLNS + "text")]
            assert any("<script>&" in t for t in text_nodes)
        measurements.append({
            "id": label,
            "xml_well_formed": valid_xmllint,
            "finite_numeric_geometry": is_finite,
            "circle_elements": circles,
            "polyline_elements": polylines,
            "svg_sha256": sha(data),
        })
    baseline = (SVG_DIR / "single_circles.svg").read_bytes()
    malformed = baseline.replace(b"<svg ", b"<not-svg ", 1)
    try:
        ET.fromstring(malformed)
    except ET.ParseError:
        markup_mutation_rejected = True
    else:
        markup_mutation_rejected = False
    assert markup_mutation_rejected
    tree = ET.fromstring(baseline)
    circle = next(iter(tree.findall(".//" + XMLNS + "circle")))
    circle.set("cx", "NaN")
    coordinate_mutation_rejected = not finite_geometry(tree)
    assert coordinate_mutation_rejected
    out = {
        "date": "2026-11-07", "study": "chartli",
        "source_pin": PIN,
        "fixture_manifest_sha256": sha(INPUT.read_bytes()),
        "total": len(measurements),
        "well_formed_xml": sum(x["xml_well_formed"] for x in measurements),
        "finite_numeric_svg": sum(x["finite_numeric_geometry"] for x in measurements),
        "invalid_xml_cases": sorted(INVALID_XML),
        "invalid_numeric_geometry_cases": sorted(NONFINITE_GEOMETRY),
        "mutation_checks": {
            "mismatched_svg_close_tag_rejected": markup_mutation_rejected,
            "nonfinite_coordinate_rejected": coordinate_mutation_rejected
        },
        "cases": measurements,
        "status": "BOUNDED_SVG_XML_AND_NUMERIC_ORACLE",
        "limits": [
            "XML well-formedness and finite geometry are necessary but not sufficient for browser SVG rendering",
            "Source renderer called via tsx, not built CLI or Rust renderer",
            "Sixteen constructed cases, not natural numeric datasets or a statistical rendering benchmark",
            "No model-generated code or user data inspected"
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({
        "cases":len(measurements),
        "xml":out["well_formed_xml"],
        "numeric":out["finite_numeric_svg"],
        "mutations":out["mutation_checks"]
    }))


if __name__=="__main__":
    verify()
