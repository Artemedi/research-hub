#!/usr/bin/env python3
"""Bounded Wiki_PG SQLite FTS5 source-recall experiment; no index writes."""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--wiki-root", required=True, type=Path)
parser.add_argument("--database", required=True, type=Path)
args = parser.parse_args()

wiki_root = args.wiki_root.resolve()
database = args.database.resolve()
sys.path.insert(0, str(wiki_root / "ingestion"))
from source_recall_benchmark import CASES, evaluate
from search_document_store import Filters, search as production_search

connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
sections = connection.execute("SELECT count(*) FROM sections").fetchone()[0]
documents = connection.execute("SELECT count(DISTINCT source_file) FROM sections").fetchone()[0]
missing = [source for source in {case[3] for case in CASES}
           if not connection.execute("SELECT 1 FROM sections WHERE source_file=? LIMIT 1", (source,)).fetchone()]
if missing:
    raise SystemExit("expected sources not in index: " + ", ".join(sorted(missing)))

results = []
for query_mode in ("question", "keywords"):
    for strategy in ("and", "or", "or_dedup", "or_dedup_host"):
        def lookup(query, host, limit):
            if strategy == "and":
                return [item["source_file"] for item in production_search(
                    "sqlite", database, query, Filters(), limit)]
            tokens = re.findall(r"\w+", query, flags=re.UNICODE)
            expression = " OR ".join(chr(34) + token + chr(34) for token in tokens)
            constrain_host = strategy == "or_dedup_host"
            sql = (
                "SELECT s.source_file FROM sections_fts "
                "JOIN sections s ON s.rowid=sections_fts.rowid "
                "WHERE sections_fts MATCH ?"
                + (" AND s.host=?" if constrain_host else "")
                + " ORDER BY bm25(sections_fts), s.section_id LIMIT ?"
            )
            parameters = [expression] + ([host] if constrain_host else []) + [
                sections if "dedup" in strategy else limit]
            found = [row[0] for row in connection.execute(sql, parameters)]
            if "dedup" in strategy:
                found = list(dict.fromkeys(found))
            return found[:limit]

        result = evaluate(lookup, query_mode=query_mode, limit=8)
        results.append({
            "query_mode": query_mode, "strategy": strategy,
            "source_recall_at_8": result["source_recall"],
            "mrr_at_8": round(result["mrr"], 4),
            "ranks": [row["rank"] for row in result["cases"]],
        })

print(json.dumps({"documents": documents, "sections": sections,
                  "labelled_cases": len(CASES), "results": results},
                 ensure_ascii=False, indent=2))
