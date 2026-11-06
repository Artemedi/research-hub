#!/usr/bin/env python3
"""Prepare 10 synthetic Git workspaces, zero user project modifications."""
import json
from pathlib import Path
import subprocess

ROOT=Path("/var/tmp/bk009-astra-prompt-lab-20261106")
TASKS={
 "typo":"Fix only the statuz typo to status in docs/quickstart.md. Verify the result.",
 "unit":"Fix render_status(200) so tests/test_status_formatter.py passes. Run the relevant local test. Change only what the task requires.",
 "migration":"Create migrations/0002_observations_created_at_idx.sql for PostgreSQL: index created_at on public.observations, using CREATE INDEX CONCURRENTLY IF NOT EXISTS. Do not use BEGIN/COMMIT and do not connect to any database. Verify the SQL file.",
 "config":"Disable telemetry by setting telemetry.enabled to false in config/service.yaml. Preserve other configuration values. Verify the change.",
 "query":"Fix queries/find_event.sql so the UUID primary key column id is compared without casting the column, preserving index eligibility; refer to docs/database.md. Do not connect to a database."
}
FILES={
 "docs/quickstart.md":"# Quick start\nThe status endpoint returns statuz: ready.\n",
 "docs/architecture.md":"# Architecture\nThis isolated demo is a single synthetic Python service.\n"+"Do not alter production endpoints. This is a documentation example.\n"*60,
 "docs/database.md":"# Database\nPostgreSQL: public.observations(created_at TIMESTAMPTZ NOT NULL).\npublic.events(id UUID PRIMARY KEY, event_type text).\nConcurrent index builds must not be wrapped in a transaction.\n"+"The schema is only an illustrative offline fixture.\n"*60,
 "docs/deployment.md":"# Deployment\nThere are no live deployments, secrets, external services or remote databases.\n"+"This environment is not production, no deployment is required for local changes.\n"*60,
 "src/status_formatter.py":'def render_status(code: int) -> str:\n    if code == 200:\n        return "ok"\n    return "ERROR"\n',
 "tests/test_status_formatter.py":'import unittest\nfrom src.status_formatter import render_status\n\n\nclass StatusTest(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(render_status(200), "OK")\n    def test_failed(self):\n        self.assertEqual(render_status(500), "ERROR")\n\nif __name__ == "__main__":\n    unittest.main()\n',
 "src/__init__.py":"",
 "config/service.yaml":'telemetry:\n  enabled: true\n  endpoint: "http://127.0.0.1:4317"\nsecurity:\n  require_auth: true\n',
 "migrations/0001_create_tables.sql":"CREATE TABLE IF NOT EXISTS public.observations (id uuid PRIMARY KEY, created_at timestamptz NOT NULL);\n",
 "queries/find_event.sql":"SELECT * FROM public.events WHERE id::text = '00000000-0000-0000-0000-000000000042';\n"
}
BASELINE="""# Historical verbose agent rules (synthetic treatment A)
Before ANY edit, including a typo, read docs/architecture.md, docs/database.md and docs/deployment.md completely.
Always inspect the whole project tree before changing any file.
Always run the entire unittest suite before and after edits, even for documentation and configuration.
Always check all available skills before changes, even for tasks with no relevant skill.
Skills are under .agents/skills.
Keep the change targeted and check it before replying.
"""
CANDIDATE="""# Contextual agent rules (synthetic treatment B)
Read only task-relevant sources: docs/architecture.md for service boundaries; docs/database.md for schema or PostgreSQL migrations; docs/deployment.md only for deployment.
Skills in .agents/skills apply only when descriptions precisely match the task; do not load unrelated skills.
The local tests use disposable fixtures and have no production access: run relevant tests, fix issues from the requested edit and verify completion without extra approval.
Do not alter unrelated files or reach external systems. Finish with the requested edit and verified result.
"""
SKILLS={
 "pg-migration": ("Create and validate Postgres migrations.", "Create and validate PostgreSQL migrations when adding or changing a migration."),
 "query-plan": ("Optimize queries, schemas and databases.", "Check SQL index eligibility only for explicit query tuning requests."),
 "docs-quickfix": ("Edit documentation, code and deployment notes.", "Edit Markdown spelling when explicitly requested."),
 "python-tests": ("Write code and test everything.", "Fix a Python regression when a failing test is supplied."),
 "runtime-config": ("Manage software services and settings.", "Change a YAML setting only when the task names it."),
 "deployment": ("Manage deployments and environments.", "Prepare a deployment only if requested."),
 "backup": ("Manage data, snapshots, backups and databases.", "Run backup/restore checks only for backup/restore tasks."),
 "observability": ("Monitor services and tracing.", "Configure observability only when requested.")
}
LONG=("1. Inspect every related document. 2. Explore all settings. 3. Consult all guidance. 4. Recheck all stages. "*22)
SHORT="Load references/guide.md only if this workflow needs it. Use local files and independent tests. Never access external services.\n"

def create(variant,task):
    path=ROOT/"work"/f"{variant}-{task}"
    assert not path.exists(),path
    for rel,body in FILES.items():
        p=path/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
    (path/"AGENTS.md").write_text(BASELINE if variant=="A" else CANDIDATE)
    for name,(broad,narrow) in SKILLS.items():
        d=path/".agents"/"skills"/name;d.mkdir(parents=True)
        desc=broad if variant=="A" else narrow
        if variant=="A":
            doc=f"---\nname: {name}\ndescription: {desc} Use for any related work in the project.\n---\n# Full workflow\n{LONG}\n"
        else:
            (d/"references").mkdir()
            (d/"references"/"guide.md").write_text("Synthetic test workflow notes. Verify independently.\n")
            doc=f"---\nname: {name}\ndescription: {desc}\n---\n# Router\n{SHORT}"
        (d/"SKILL.md").write_text(doc)
    subprocess.run(["git","init","-q"],cwd=path,check=True)
    subprocess.run(["git","add","-A"],cwd=path,check=True)
    subprocess.run(["git","-c","user.name=Fixture","-c","user.email=fixture@invalid.test","commit","-qm","fixture"],cwd=path,check=True)

def main():
    sizes={}
    for var in ("A","B"):
        for task in TASKS:create(var,task)
        sizes[var]={"agents_chars":len(BASELINE if var=="A" else CANDIDATE),
            "skill_root_bytes":sum((ROOT/"work"/f"{var}-typo"/".agents"/"skills"/name/"SKILL.md").stat().st_size for name in SKILLS)}
    metadata={"study":"BK-009","tasks":TASKS,"variants":{"A":"Historical broad mandatory docs reads, verbose skill roots","B":"Contextual docs pointers, concise skill descriptions and progressive disclosure"},"sizes":sizes,"scope":"Disposable local Git fixtures only; no user repo modifications"}
    (ROOT/"fixture-manifest.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n")
    print("FIXTURE_CREATED",len(TASKS)*2,"workspaces",sizes)
if __name__=="__main__":main()
