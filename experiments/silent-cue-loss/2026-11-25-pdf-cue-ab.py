"""Exercise Paper2Project's import and citable-read path on generated PDFs."""
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from paper2project.core import App

TARGET = "57991e6681ad683a5be8111b7d470fed5d53625b"
RED = [1, 0, 0]


def case(number):
    # Assign the red label before constructing a PDF or invoking an extractor.
    names = [
        f"Inspect tray {number}.",
        f"Record batch {number}.",
        f"[COLOR:#FF0000] Label box {number}.",
        f"Close bin {number}.",
    ]
    red_index = number % 2
    return names, names[red_index]


def write_fixture(path, names, number):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    name = NameObject
    page[name("/Resources")] = DictionaryObject({
        name("/Font"): DictionaryObject({name("/F1"): DictionaryObject({
            name("/Type"): name("/Font"), name("/Subtype"): name("/Type1"),
            name("/BaseFont"): name("/Helvetica"),
        })}),
    })
    controls = ["q\n1 0 0 rg\n", "0 0 0 rg\n", "", "0 0 1 rg\n"]
    endings = ["Q\n", "", "", ""]
    if number % 2:
        controls[0], controls[1] = controls[1], controls[0]
        endings[0], endings[1] = endings[1], endings[0]
    instructions = []
    for index, (line, before, after) in enumerate(zip(names, controls, endings)):
        instructions.append(
            f"{before}BT /F1 12 Tf 50 {750-index*24} Td ({line}) Tj ET\n{after}"
        )
    stream = DecodedStreamObject()
    stream.set_data("".join(instructions).encode("ascii"))
    page[name("/Contents")] = writer._add_object(stream)
    writer.write(path)


def annotate_fixture(pdf_path, annotated_path):
    # This is deliberately limited to the generated content-stream grammar.
    page, = PdfReader(pdf_path).pages
    contents = page.get_contents()
    color, stack, records = [0, 0, 0], [], []
    for operands, operator in contents.operations:
        match operator:
            case b"rg":
                color = list(operands)
            case b"q":
                stack.append(color)
            case b"Q":
                color = stack.pop()
            case b"Tj":
                records.append({"text": str(operands[0]), "rgb": color})
            case b"BT" | b"ET" | b"Tf" | b"Td":
                continue
            case _:
                raise ValueError(f"Unexpected fixture operator: {operator!r}")
    if stack:
        raise ValueError("Unbalanced fixture graphics state")
    annotated_path.write_text(
        "\n".join(json.dumps(record, separators=(",", ":")) for record in records) + "\n",
        encoding="utf-8",
    )


def read_case(root, fixture, number, arm, project):
    started = perf_counter()
    app = App(root)
    if arm == "annotated":
        text_path = root / f"case-{number}.txt"
        annotate_fixture(fixture, text_path)
        fixture = text_path
    project_ref, = app.import_projects(project)
    research = app.import_research(fixture)
    job = app.create_job(research["id"], [project_ref["id"]])
    research_doc = next(key for key in app.docs(job["id"]) if key.startswith("research:"))
    readable = app.read(job["id"], research_doc)
    duration_ms = (perf_counter() - started) * 1000
    lines, red, mutant, size = measure_read(readable, arm)
    return lines, red, mutant, size, duration_ms


def measure_read(readable, arm):
    expected_fields = {"document", "start", "end", "text"}
    document_fields = {"id", "path", "sha256", "text", "lines", "kind", "owner", "owner_kind", "snapshot"}
    # The pinned API exposes a plain-text snapshot and document identity metadata.
    if (set(readable) != expected_fields or not isinstance(readable["document"], dict)
            or set(readable["document"]) != document_fields):
        raise ValueError(f"Paper2Project read contract changed; response fields: {sorted(readable)}, "
                         f"document fields: {sorted(readable.get('document', {}))}")
    lines = [line.split(": ", 1)[1] for line in readable["text"].splitlines()]
    size = len("\n".join(lines).encode("utf-8"))
    if arm == "baseline":
        lines = [line for line in lines if line and line != "# PDF page 1"]
        return lines, None, None, size

    records = [json.loads(line) for line in lines]
    red = {record["text"] for record in records if record["rgb"] == RED}
    mutant = {record["text"] for record in records if any(record["rgb"])}
    return [record["text"] for record in records], red, mutant, size


def check_measurement_controls():
    literal = "[COLOR:#FF0000] plain black"
    document = {"id": "fixture", "path": "fixture", "sha256": "", "text": "", "lines": 1,
                "kind": "research", "owner": "fixture", "owner_kind": "research", "snapshot": ""}
    response = {"document": document, "start": 1, "end": 1, "text": f"1: {literal}"}
    lines, red, _, _ = measure_read(response, "baseline")
    if lines != [literal] or red is not None:
        raise AssertionError("Plain text marker counted as observed color")
    records = [{"text": "real red", "rgb": RED}, {"text": literal, "rgb": [0, 0, 0]}]
    response["text"] = "\n".join(f"{n}: {json.dumps(row)}" for n, row in enumerate(records, 1))
    _, red, _, _ = measure_read(response, "annotated")
    if red != {"real red"}:
        raise AssertionError("Structured red control was not distinguished from the literal marker")
    try:
        measure_read({**response, "foreground_rgb": [RED]}, "baseline")
    except ValueError:
        return
    raise AssertionError("Changed read contract was silently accepted")


def run(repository):
    revision = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != TARGET or pypdf.__version__ != "6.18.1":
        raise ValueError("Use the pinned Paper2Project revision and pypdf 6.18.1.")
    if subprocess.check_output(["git", "-C", repository, "status", "--porcelain"]):
        raise ValueError("Use a clean Paper2Project tree.")
    check_measurement_controls()
    results = []
    all_times = {"baseline": [], "annotated": []}
    with TemporaryDirectory(prefix="p2p-cue-lab-") as tmp:
        tmp = Path(tmp)
        gold = {number: case(number) for number in range(30)}
        frozen = json.dumps(gold, sort_keys=True, separators=(",", ":")).encode()
        oracle_sha256 = hashlib.sha256(frozen).hexdigest()
        project = tmp / "fixture-project.md"
        project.write_text("Synthetic PDF evidence import fixture.\n", encoding="utf-8")
        for number, (names, _) in gold.items():
            write_fixture(tmp / f"case-{number}.pdf", names, number)
        for repetition in range(3):
            total = {
                arm: dict(exact_lines=0, exact_documents=0, text_bytes=0)
                for arm in all_times
            }
            total["baseline"]["text_only_responses"] = 0
            total["annotated"].update(true_positive=0, false_positive=0, false_negative=0)
            mutant_false_positives = 0
            for number, (expected_lines, expected_red) in gold.items():
                order = list(all_times)
                if (number + repetition) % 2:
                    order.reverse()
                for arm in order:
                    observed, found, mutant, size, ms = read_case(
                        tmp / f"r{repetition}-{number}-{arm}",
                        tmp / f"case-{number}.pdf", number, arm, project
                    )
                    result = total[arm]
                    red = {expected_red}
                    if found is None:
                        result["text_only_responses"] += 1
                    else:
                        result["true_positive"] += len(found & red)
                        result["false_positive"] += len(found - red)
                        result["false_negative"] += len(red - found)
                        mutant_false_positives += len(mutant - red)
                    result["exact_lines"] += sum(a == b for a, b in zip(observed, expected_lines))
                    result["exact_documents"] += observed == expected_lines
                    result["text_bytes"] += size
                    all_times[arm].append(ms)
            a, b = total["baseline"], total["annotated"]
            passed = (
                all(row["exact_documents"] == 30 and row["exact_lines"] == 120
                    for row in total.values())
                and a["text_only_responses"] == 30
                and (b["true_positive"], b["false_positive"], b["false_negative"]) == (30, 0, 0)
                and b["text_bytes"] <= 4 * a["text_bytes"]
                and mutant_false_positives == 30
            )
            results.append({"arms": total, "mutant_false_positives": mutant_false_positives,
                            "passed": passed})
    report = {
        "target": TARGET, "pypdf": pypdf.__version__, "python": platform.python_version(),
        "documents_per_repetition": 30, "oracle_sha256": oracle_sha256,
        "measurement_controls": ["literal_marker", "structured_red", "changed_read_contract"],
        "runs": results, "timing_ms": {
            arm: {"median": round(statistics.median(times), 2),
                  "p95": round(statistics.quantiles(times, n=100, method="inclusive")[94], 2)}
            for arm, times in all_times.items()
        },
    }
    print(json.dumps(report, indent=2), flush=True)
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1]))
