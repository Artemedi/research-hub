"""Freeze the public OpenAlex B1 sample without publishing abstracts."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from time import sleep
from urllib.parse import urlencode
from urllib.request import urlopen


STRATA = {
    "core": (192, ("T10317", "T11106", "T10286")),
    "adjacent": (144, ("T10772", "T10743", "T10054")),
    "distant": (144, ("T10007", "T10941", "T10165", "T10140")),
}
YEARS = range(2021, 2026)
SEED = 20261125
FIELDS = "id,title,primary_topic,publication_year,abstract_inverted_index"
ENDPOINT = "https://api.openalex.org/works"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stable_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def abstract_text(index):
    if not isinstance(index, dict) or not index:
        raise ValueError("Expected a nonempty abstract index")
    words = sorted((position, word) for word, positions in index.items() for position in positions)
    positions = [position for position, _ in words]
    if not positions or positions[0] < 0 or len(set(positions)) != len(positions):
        raise ValueError("Abstract index has empty, negative or repeated positions")
    return " ".join(word for _, word in words), positions[-1] + 1 - len(positions)


def split_for(work_id):
    bucket = int(sha(work_id.encode("ascii")), 16) % 100
    return "fit" if bucket < 60 else "dev" if bucket < 80 else "test"


def freeze(folder, protocol_hash, replay):
    rows, requests = [], []
    seen = set()
    when = folder / "retrieved-at.txt"
    if not replay:
        folder.mkdir(parents=True, exist_ok=False)
        when.write_text(datetime.now(timezone.utc).isoformat() + "\n", encoding="ascii")
    for stratum, (size, topics) in STRATA.items():
        for year in YEARS:
            for page in (1, 2):
                filters = f"primary_topic.id:{'|'.join(topics)},publication_year:{year},type:article,has_abstract:true"
                query = dict(filter=filters, sample=size, seed=SEED, select=FIELDS, per_page=100, page=page)
                cache = folder / f"{stratum}-{year}-{page}.json"
                if not replay:
                    with urlopen(f"{ENDPOINT}?{urlencode(query)}", timeout=25) as response:
                        raw = response.read()
                    cache.write_bytes(raw)
                    sleep(0.6)
                raw = cache.read_bytes()
                records = json.loads(raw)["results"]
                expected = 100 if page == 1 else size - 100
                if len(records) != expected:
                    raise ValueError(f"{cache.name}: expected {expected} records, got {len(records)}")
                requests.append({"stratum": stratum, "year": year, "page": page,
                                 "count": len(records), "response_sha256": sha(raw)})
                for record in records:
                    work_id = record["id"].removeprefix("https://openalex.org/")
                    topic = record["primary_topic"]["id"].removeprefix("https://openalex.org/")
                    if not re.fullmatch(r"W[0-9]+", work_id) or work_id in seen:
                        raise ValueError(f"{cache.name}: invalid or duplicate work ID")
                    if topic not in topics or record["publication_year"] != year:
                        raise ValueError(f"{cache.name}: work outside its sampled stratum")
                    seen.add(work_id)
                    abstract, gaps = abstract_text(record["abstract_inverted_index"])
                    payload = {"title": record["title"], "abstract": abstract}
                    if not isinstance(payload["title"], str) or not payload["title"].strip():
                        raise ValueError(f"{cache.name}: missing title")
                    rows.append({"id": work_id, "year": year, "topic": topic, "stratum": stratum,
                                 "split": split_for(work_id), "text_sha256": sha(stable_json(payload)),
                                 "missing_abstract_positions": gaps})
    rows.sort(key=lambda row: row["id"])
    return {
        "schema_version": 1, "status": "B1_CORPUS_FROZEN_UNLABELLED",
        "retrieved_at_utc": when.read_text(encoding="ascii").strip(),
        "protocol_sha256": protocol_hash, "source": ENDPOINT, "seed": SEED,
        "strata": {name: {"per_year": size, "topics": topics} for name, (size, topics) in STRATA.items()},
        "years": list(YEARS), "requests": requests, "record_count": len(rows),
        "split_counts": dict(sorted(Counter(row["split"] for row in rows).items())),
        "abstracts_with_gaps": sum(row["missing_abstract_positions"] > 0 for row in rows),
        "selection_sha256": sha(stable_json(rows)), "records": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_directory", type=Path)
    parser.add_argument("--replay", action="store_true", help="Read only the saved response bytes")
    args = parser.parse_args()
    protocol = Path(__file__).with_name("2026-11-25-b1-protocol.md")
    result = freeze(args.snapshot_directory, sha(protocol.read_bytes()), args.replay)
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=True, indent=2) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
