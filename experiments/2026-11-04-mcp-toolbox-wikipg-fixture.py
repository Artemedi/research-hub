#!/usr/bin/env python3
"""Build a synthetic Wiki_PG snapshot from the actual disposable PostgreSQL lab."""
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--container", default="trin-toolbox-lab-20261104")
args = parser.parse_args()
root = args.root.resolve()
q = """
SELECT name,setting,COALESCE(unit,'')
FROM pg_catalog.pg_settings
WHERE name IN ('max_connections','work_mem','random_page_cost','wal_level')
ORDER BY name
"""
r = subprocess.run(["podman", "exec", args.container, "psql",
                    "-U", "postgres", "-d", "lab", "-X", "-At", "-F", "|", "-c", q],
                   check=True, capture_output=True, text=True)
rows = {}
for line in r.stdout.strip().splitlines():
    name, setting, unit = line.split("|")
    rows[name] = {"name": name, "setting": setting, "unit": unit}

fixture = root / "fake-wiki" / "Wiki_PG"
registry = fixture / "operations" / "clusters" / "registry.yaml"
registry.parent.mkdir(parents=True, exist_ok=True)
registry.write_text("clusters:\n  LAB_001: lab\n", encoding="utf-8")

def write_report(day, hour, values):
    report = fixture / "raw" / "sysconfig-report" / "Lab" / "LAB_001" / "2026" / "11" / \
        f"LAB_001_sysconfig_report_{day}_{hour}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({
        "postgres_settings": {"instances": [{
            "port": "5432",
            "settings": [
                {**row, "setting": values.get(row["name"], row["setting"])}
                for row in rows.values()
            ],
        }]}
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return report

new = write_report("2026-11-04", "07-00-00", {})
old = write_report("2026-11-03", "07-00-00", {"work_mem": "8192"})
(root / "oracle-settings.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps({"settings": rows, "latest": str(new.relative_to(fixture)),
                  "historical": str(old.relative_to(fixture))}, indent=2))
