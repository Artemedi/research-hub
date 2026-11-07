#!/usr/bin/env python3
"""External static oracle: independently recheck the pinned public skill tree.

No import from the manifest generator. This proves source references and
document-level trust boundary only; does not attempt signup/API/tool install.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SOURCE=Path(os.environ["SOURCE"]).resolve()
INPUT=Path(os.environ["INPUT"])
OUTPUT=Path(os.environ["OUTPUT"])
PIN="4f7994b94e7d5e250c3b51102d609992e04d5d0d"


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def validate_document(skill_text, auth_text):
    # Observe source, not a simulated agent or the vendor API.
    front=skill_text.split("---",2)
    if len(front)<3:
        return False
    return (
        "required_environment_variables:" in front[1]
        and "TRANSCRIPT_API_KEY" in front[1]
        and "references/auth-setup.md" in skill_text
        and "/api/v2/youtube/" in skill_text
        and "register-cli" in auth_text
        and "verify-cli" in auth_text
        and "Store it persistently" in auth_text
    )


def main():
    assert subprocess.check_output(
        ["git","-C",str(SOURCE),"rev-parse","HEAD"],
        text=True).strip()==PIN
    original=json.loads(INPUT.read_text())
    assert original["source_pin"]==PIN
    rows=original["rows"]
    assert len(rows)==24
    names={x["skill"] for x in rows}
    assert len(names)==12
    assert set(x["namespace"] for x in rows)=={"skills","clawhub"}
    assert len({(x["namespace"],x["skill"]) for x in rows})==24
    tracked=subprocess.check_output(
        ["git","-C",str(SOURCE),"ls-files"],text=True).splitlines()
    all_docs=[p for p in tracked if p.startswith(("skills/","clawhub/"))]
    assert len(all_docs)==60
    assert all(Path(path).suffix==".md" for path in all_docs)
    independent=[]
    for row in rows:
        file=SOURCE/row["source_path"]
        auth=SOURCE/row["namespace"]/row["skill"]/"references/auth-setup.md"
        assert file.is_file() and auth.is_file()
        assert digest(file.read_bytes())==row["source_sha256"]
        assert digest(auth.read_bytes())==row["auth_guide_sha256"]
        content=file.read_text()
        guide=auth.read_text()
        assert validate_document(content,guide)
        assert row["required_env"]=="TRANSCRIPT_API_KEY"
        assert row["provider_domain"]=="transcriptapi.com"
        independent.append(row["source_path"])
    assert len(independent)==24
    # Two independent mutation controls, never writing to source.
    sample=(SOURCE/rows[0]["source_path"]).read_text()
    guide=(SOURCE/rows[0]["namespace"]/rows[0]["skill"]/
           "references/auth-setup.md").read_text()
    assert not validate_document(
        sample.replace("TRANSCRIPT_API_KEY","INVALID_PLACEHOLDER"),guide)
    assert not validate_document(
        sample, re.sub("Store it persistently","Do not store it",guide))
    result={
        "date":"2026-11-07","study":"youtube-skills","source_pin":PIN,
        "manifest_sha256":digest(INPUT.read_bytes()),
        "tracks_exact_60_markdown_documents":True,
        "provider_source_code_in_skill_folders":0,
        "independently_pinned_skills":24,
        "auth_guide_sha_verified":24,
        "required_key_contract_verified":24,
        "synthetic_mutations_rejected":2,
        "network_actions_run":0,
        "verdict":"SOURCE_BOUNDARY_AND_SECRET_BOOTSTRAP_AUDITED_NO_PROVIDER_TEST",
        "limits":[
            "Independent re-read and SHA check of bundled text, not independent third-party API behavior",
            "No credential collection, registration, API requests, live transcript or user profile changes",
            "No proof of actual security defect or key leakage; guidance only exposes an operational hazard",
            "Cannot infer compatibility, latency, costs or quality for claimed platforms"
        ],
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"docs":60,"skills":24,"mutation_checks":2,
                      "source_pin_verified":True}))


if __name__=="__main__":
    main()
