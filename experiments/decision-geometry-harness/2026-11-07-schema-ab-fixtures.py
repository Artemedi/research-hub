#!/usr/bin/env python3
"""Pre-registered 24 synthetic tool-routing cases and independent gold labels.

Writes public, non-executable tasks before any model inference. No secret,
project source, patient data or production records. Never pass gold to ZCode.
"""
import hashlib
import json
import os
from pathlib import Path
import random

OUT = Path(os.environ["OUTPUT"])
PIN = "3feed5d0d9a8a0f8e75c0a63f37b530d6eebc5dc"
SERIALIZER_SHA = "36ff023acb53f11af7eb7550e533907489e928a81037f8b4e447804a16910162"


def task(key, text, tool, args):
    return {"id": key, "instruction": text, "expected_tool": tool, "expected_arguments": args}


def main():
    rows = [
        task("sql-1", "Inspect SQL execution plan query_id=771 in database AuditLab.", "inspect_sql_plan", {"database": "AuditLab", "query_id": "771"}),
        task("sql-2", "Покажи план SQL для query_id=772 в базе TestWarehouse.", "inspect_sql_plan", {"database": "TestWarehouse", "query_id": "772"}),
        task("sql-3", "Retrieve SQL plan for query_id=42 in database DemoDb.", "inspect_sql_plan", {"database": "DemoDb", "query_id": "42"}),
        task("pg-1", "Get PostgreSQL relation statistics for schema=public, relation=events.", "inspect_pg_relation", {"schema": "public", "relation": "events"}),
        task("pg-2", "Получи статистику таблицы в PostgreSQL: schema=metrics, relation=samples.", "inspect_pg_relation", {"schema": "metrics", "relation": "samples"}),
        task("pg-3", "Inspect PostgreSQL relation named audit_log in schema demo.", "inspect_pg_relation", {"schema": "demo", "relation": "audit_log"}),
        task("job-1", "Find status for background job with job_id=job-104.", "get_job_status", {"job_id": "job-104"}),
        task("job-2", "Проверь состояние задачи job_id=job-211.", "get_job_status", {"job_id": "job-211"}),
        task("job-3", "Get execution status for job_id=job-007.", "get_job_status", {"job_id": "job-007"}),
        task("artifact-1", "List report artifacts for study=agent-sandbox.", "list_experiment_artifacts", {"study": "agent-sandbox", "kind": "report"}),
        task("artifact-2", "Список данных для исследования study=schema-drift, kind=data.", "list_experiment_artifacts", {"study": "schema-drift", "kind": "data"}),
        task("artifact-3", "List experiment artifacts associated with study=kv-order.", "list_experiment_artifacts", {"study": "kv-order", "kind": "experiment"}),
        task("file-1", "Read docs/notes.md lines 10 through 14, inclusive.", "read_file_range", {"path": "docs/notes.md", "start_line": 10, "end_line": 14}),
        task("file-2", "Прочитай строки 35–42 файла src/agent.ts.", "read_file_range", {"path": "src/agent.ts", "start_line": 35, "end_line": 42}),
        task("file-3", "Read README.md lines 1 to 5 inclusive.", "read_file_range", {"path": "README.md", "start_line": 1, "end_line": 5}),
        task("runbook-1", "Find runbook for topic=backup-check, revision=v1.", "find_runbook", {"topic": "backup-check", "revision": "v1"}),
        task("runbook-2", "Найди инструкцию по topic=replica-delay, revision=v2.", "find_runbook", {"topic": "replica-delay", "revision": "v2"}),
        task("runbook-3", "Look up runbook revision v3 for topic=vacuum-stall.", "find_runbook", {"topic": "vacuum-stall", "revision": "v3"}),
        task("sum-1", "Use the sum tool on the numbers [4, 9, -2].", "sum_numbers", {"numbers": [4, 9, -2]}),
        task("sum-2", "Сложи инструментом числа [10, -3, 8].", "sum_numbers", {"numbers": [10, -3, 8]}),
        task("sum-3", "Select the sum tool with integer inputs [0, 100, 5].", "sum_numbers", {"numbers": [0, 100, 5]}),
        task("none-1", "Do not select or call any tool. This is only an acknowledgement.", "NONE", {}),
        task("none-2", "Не вызывай инструменты. Просто отметь, что инструмент не нужен.", "NONE", {}),
        task("none-3", "This is not a request to inspect SQL or files: select NONE.", "NONE", {}),
    ]
    assert len(rows) == 24
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == 24
    rng = random.Random(20261107)
    rng.shuffle(rows)
    for i in range(0, len(rows), 8):
        assert len(rows[i:i+8]) == 8
    output = {
        "date": "2026-11-07",
        "study": "decision-geometry-harness",
        "target": "dsh-runtime wire schema + ZCode text-only choice surrogate",
        "source_pin": PIN,
        "serializer_source_sha256": SERIALIZER_SHA,
        "seed": 20261107,
        "cases": rows,
        "case_count": len(rows),
        "batch_size": 8,
        "batches": 3,
        "variants": ["A", "B"],
        "replicates": 2,
        "oracle": "pre-registered authored exact tool name and JSON arguments; independent of model output",
        "limitations": ["One manually authored gold per scenario, not blinded expert adjudication",
                        "Synthetic, semantically disjoint tasks; not real agent tool executions"]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(rows), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
