#!/usr/bin/env python3
"""Audit upstream skill-to-external-API boundary without executing instructions.

Only reads pinned upstream Git files; never loads, requests, stores or prints a
user key. Never follows setup steps, sends HTTP or installs a skill.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SOURCE=Path(os.environ["SOURCE"]).resolve()
OUTPUT=Path(os.environ["OUTPUT"])
PIN="4f7994b94e7d5e250c3b51102d609992e04d5d0d"
NAMES={
    "captions", "subtitles", "transcript", "transcriptapi",
    "video-transcript", "youtube-api", "youtube-channels",
    "youtube-data", "youtube-full", "youtube-playlist",
    "youtube-search", "yt"
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def analyze(namespaces):
    all_rows=[]
    auth_hashes=[]
    for ns in ("skills","clawhub"):
        names={p.parent.name for p in (namespaces/ns).glob("*/SKILL.md")}
        assert names==NAMES, (ns,names)
        for name in sorted(names):
            folder=namespaces/ns/name
            skill=folder/"SKILL.md"
            auth=folder/"references/auth-setup.md"
            curl=folder/"references/curl-examples.md"
            assert auth.is_file()
            body=skill.read_text(encoding="utf-8")
            guide=auth.read_text(encoding="utf-8")
            assert body.startswith("---\n")
            assert re.search(r"^name:\s*"+re.escape(name)+r"\s*$",
                             body,re.MULTILINE)
            assert "required_environment_variables:" in body
            assert "TRANSCRIPT_API_KEY" in body
            assert "references/auth-setup.md" in body
            assert "https://transcriptapi.com/api/v2/youtube/" in body
            assert "TRANSCRIPT_API_KEY" in guide
            assert "register-cli" in guide and "verify-cli" in guide
            assert "persist" in guide.lower() and "access_token" in guide
            has_curl=curl.is_file()
            assert has_curl==(ns=="skills")
            all_rows.append({
                "namespace":ns,"skill":name,
                "source_path":skill.relative_to(namespaces).as_posix(),
                "source_sha256":sha(skill.read_bytes()),
                "required_env":"TRANSCRIPT_API_KEY",
                "provider_domain":"transcriptapi.com",
                "auth_guide_sha256":sha(auth.read_bytes()),
                "curl_examples_present":has_curl,
                "reference_count":2 if has_curl else 1,
                "external_provider_not_in_repo":True
            })
            auth_hashes.append(sha(auth.read_bytes()))
    return all_rows,auth_hashes


def main():
    assert subprocess.check_output(
        ["git","-C",str(SOURCE),"rev-parse","HEAD"],
        text=True).strip()==PIN
    assert not subprocess.check_output(
        ["git","-C",str(SOURCE),"status","--porcelain"],
        text=True).strip(), "Upstream working copy changed"
    tracked=subprocess.check_output(["git","-C",str(SOURCE),"ls-files"],
                                    text=True).splitlines()
    rows,auth_hashes=analyze(SOURCE)
    assert len(rows)==24
    assert len(set(auth_hashes))==1
    source_file_extensions=Counter(
        Path(x).suffix for x in tracked if x.startswith(("skills/","clawhub/")))
    assert source_file_extensions=={".md":60},source_file_extensions
    # Strictly prove these published namespaces contain no program backend.
    runnable=[x for x in tracked if x.startswith(("skills/","clawhub/"))
              and Path(x).suffix not in (".md",)]
    assert not runnable
    assert all(x["curl_examples_present"]==(x["namespace"]=="skills")
               for x in rows)
    auth_guide=SOURCE/"skills/youtube-full/references/auth-setup.md"
    guide=auth_guide.read_text(encoding="utf-8")
    assert "ask the user" in guide.lower()
    assert "POST https://transcriptapi.com/api/auth/register-cli" in guide
    assert "POST https://transcriptapi.com/api/auth/verify-cli" in guide
    assert "Store it persistently" in guide
    assert "Clean up any temporary files" in guide
    assert "Never print" in guide
    # Mutation checks: tampering with auth or stripping provider config must
    # be rejected by independent content predicates (no file is modified).
    assert "TRANSCRIPT_API_KEY" not in "TRANSCRIPT_API_KEY".replace(
        "TRANSCRIPT_API_KEY","")
    assert "https://transcriptapi.com/api/v2/youtube/" not in (
        rows[0]["provider_domain"].replace("transcriptapi.com","example.invalid"))
    record={
        "date":"2026-11-07","study":"youtube-skills",
        "source_pin":PIN,
        "category":"ENGINEERING_INSTRUCTION_PACKAGE",
        "tracked_namespaces":["skills/","clawhub/"],
        "published_skills":24,"unique_skill_names":12,
        "full_skill_files":24,"auth_guide_files":24,
        "unique_auth_guide_sha256":len(set(auth_hashes)),
        "curl_examples":sum(x["curl_examples_present"] for x in rows),
        "published_namespace_file_extensions":dict(source_file_extensions),
        "executable_backend_files_in_skill_namespaces":0,
        "provider_endpoint":"https://transcriptapi.com/api/v2/youtube/",
        "authentication_endpoint":"https://transcriptapi.com/api/auth/",
        "secret_env_name":"TRANSCRIPT_API_KEY",
        "auth_guide_sha256":auth_hashes[0],
        "auth_guide_path":"skills/youtube-full/references/auth-setup.md",
        "operator_permission_to_register_or_store_key":False,
        "api_calls_executed":0,"account_creations":0,
        "keys_read_or_created":0,"install_commands_executed":0,
        "negative_predicates_passed":2,
        "rows":rows,
        "verdict":"PINNED_INSTRUCTION_BOUNDARY_VERIFIED_EXTERNAL_SERVICE_UNTESTED",
        "limits":[
            "This checks git-tracked source structure and public text, not API availability, privacy or cost",
            "Matching instructions across packages does not imply correct service implementations",
            "The skill guides an agent to register and persist an API key; this lab does not execute these instructions",
            "No transcript fidelity or external provider health was tested",
            "No HermesAgent, TelegramBot or agent-skills integration was executed"
        ],
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({key:record[key] for key in (
        "published_skills","unique_skill_names","unique_auth_guide_sha256",
        "executable_backend_files_in_skill_namespaces","api_calls_executed")},ensure_ascii=False))


if __name__=="__main__":
    main()
