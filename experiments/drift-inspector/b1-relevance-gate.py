"""Prepare a blind B1 batch and count independently matched positive articles offline."""

import argparse
import csv
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import random
import re
import sys


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "2026-11-25-b1-protocol.md"
MANIFEST = HERE.parents[1] / "data/results/drift-inspector/2026-11-25-b1-corpus-manifest.json"
SPEC = spec_from_file_location("b1_freeze", HERE / "2026-11-25-b1-freeze.py")
FREEZE = module_from_spec(SPEC)
SPEC.loader.exec_module(FREEZE)
MIN_ARTICLES = 50
LABEL_COLUMNS = ["item", "relevant_queries", "unclear_queries"]


def criteria():
    rows = re.findall(r"^\| (Q\d{2}) \| (.*?) \| (.*?) \|$", PROTOCOL.read_text(encoding="utf-8"), re.M)
    if [row[0] for row in rows] != [f"Q{number:02}" for number in range(1, 37)]:
        raise ValueError("Expected the 36 frozen criteria in protocol order")
    return [dict(id=query, name=name, criterion=criterion) for query, name, criterion in rows]


def prepare(snapshot, output):
    if output.is_relative_to(HERE.parents[1]):
        raise ValueError("Place the blind batch outside the repository")
    manifest = json.loads(MANIFEST.read_bytes())
    protocol_hash = FREEZE.sha(PROTOCOL.read_bytes())
    replay = FREEZE.freeze(snapshot, protocol_hash, replay=True)
    if FREEZE.stable_json(replay) != FREEZE.stable_json(manifest):
        raise ValueError("Snapshot and protocol must reproduce the published B1 manifest")

    test_ids = {row["id"] for row in manifest["records"] if row["split"] == "test"}
    articles = {}
    for request in manifest["requests"]:
        filename = "{stratum}-{year}-{page}.json".format(**request)
        raw = (snapshot / filename).read_bytes()
        if FREEZE.sha(raw) != request["response_sha256"]:
            raise ValueError(f"Snapshot page changed: {filename}")
        for record in json.loads(raw)["results"]:
            work_id = record["id"].removeprefix("https://openalex.org/")
            if work_id in test_ids:
                abstract, _ = FREEZE.abstract_text(record["abstract_inverted_index"])
                articles[work_id] = dict(title=record["title"], abstract=abstract)
    if articles.keys() != test_ids:
        raise ValueError("Blind batch must contain the entire frozen test split")

    order = sorted(test_ids)
    random.SystemRandom().shuffle(order)
    mapping = {f"B{number:04}": work_id for number, work_id in enumerate(order, start=1)}
    batch = dict(criteria=criteria(), items=[dict(item=item, **articles[work_id]) for item, work_id in mapping.items()])
    batch_bytes = (json.dumps(batch, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    batch_hash = FREEZE.sha(batch_bytes)

    output.mkdir(parents=True, exist_ok=False)
    (output / "blind-batch.json").write_bytes(batch_bytes)
    (output / "private-key.json").write_bytes(FREEZE.stable_json(dict(
        batch_sha256=batch_hash, selection_sha256=manifest["selection_sha256"], mapping=mapping,
    )))
    with (output / "labels-template.tsv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target, delimiter="\t", lineterminator="\n")
        writer.writerow(["batch_sha256", batch_hash])
        writer.writerow(LABEL_COLUMNS)
        writer.writerows((item, "", "") for item in mapping)
    print(json.dumps(dict(status="READY_FOR_BLIND_REVIEW", test_articles=len(mapping), batch_sha256=batch_hash)))


def read_labels(path, batch_hash, items, query_ids):
    labels = {}
    seen = set()
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, delimiter="\t")
        if next(reader, None) != ["batch_sha256", batch_hash] or next(reader, None) != LABEL_COLUMNS:
            raise ValueError(f"{path.name}: wrong batch or column headers")
        for line, row in enumerate(reader, start=3):
            if len(row) != len(LABEL_COLUMNS) or row[0] not in items or row[0] in seen:
                raise ValueError(f"{path.name}:{line}: invalid or duplicate item")
            item, relevant, unclear = (value.strip() for value in row)
            seen.add(item)
            if not relevant and not unclear:
                continue
            pair = []
            for field in (relevant, unclear):
                queries = [] if field == "-" else [value.strip() for value in field.split(",")]
                if not set(queries) <= query_ids or len(queries) != len(set(queries)):
                    raise ValueError(f"{path.name}:{line}: invalid or duplicate query ID; use '-' for none")
                pair.append(set(queries))
            if pair[0] & pair[1]:
                raise ValueError(f"{path.name}:{line}: a query cannot be both relevant and unclear")
            labels[item] = pair[0]
    return labels


def count(output, owner_sheet, judge_sheet):
    if owner_sheet.samefile(judge_sheet):
        raise ValueError("Expected two independent label sheets")
    raw = (output / "blind-batch.json").read_bytes()
    batch = json.loads(raw)
    batch_hash = FREEZE.sha(raw)
    key = json.loads((output / "private-key.json").read_bytes())
    manifest = json.loads(MANIFEST.read_bytes())
    if manifest["protocol_sha256"] != FREEZE.sha(PROTOCOL.read_bytes()):
        raise ValueError("Protocol differs from the frozen B1 manifest")
    test = {row["id"]: row["text_sha256"] for row in manifest["records"] if row["split"] == "test"}
    mapping = key["mapping"]
    if key["batch_sha256"] != batch_hash or key["selection_sha256"] != manifest["selection_sha256"]:
        raise ValueError("Batch identity does not match the frozen selection")
    if len(mapping) != len(test) or set(mapping.values()) != test.keys() or batch["criteria"] != criteria():
        raise ValueError("Batch must cover the frozen test split and criteria exactly")
    verified = set()
    for item in batch["items"]:
        article = dict(title=item["title"], abstract=item["abstract"])
        if item["item"] in verified or FREEZE.sha(FREEZE.stable_json(article)) != test.get(mapping.get(item["item"])):
            raise ValueError("Batch has a duplicate item or text differs from the frozen snapshot")
        verified.add(item["item"])
    if verified != mapping.keys():
        raise ValueError("Batch omits test articles")

    query_ids = {row["id"] for row in batch["criteria"]}
    owner, judge = [read_labels(sheet, batch_hash, verified, query_ids) for sheet in (owner_sheet, judge_sheet)]
    reviewed_by_both = owner.keys() & judge.keys()
    confirmed = sum(bool(owner[item] & judge[item]) for item in reviewed_by_both)
    result = dict(test_articles=len(test), owner_reviewed=len(owner), judge_reviewed=len(judge),
                  reviewed_by_both=len(reviewed_by_both), confirmed_articles=confirmed,
                  minimum_articles=MIN_ARTICLES, threshold_met=confirmed >= MIN_ARTICLES)
    print(json.dumps(result))
    return 0 if result["threshold_met"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    export = subcommands.add_parser("prepare")
    export.add_argument("snapshot", type=Path)
    export.add_argument("batch_dir", type=Path)
    audit = subcommands.add_parser("count")
    audit.add_argument("batch_dir", type=Path)
    audit.add_argument("owner_sheet", type=Path)
    audit.add_argument("judge_sheet", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.snapshot.resolve(), args.batch_dir.resolve())
            return 0
        return count(args.batch_dir, args.owner_sheet, args.judge_sheet)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    sys.exit(main())
