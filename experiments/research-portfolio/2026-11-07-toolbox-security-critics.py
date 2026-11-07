#!/usr/bin/env python3
"""Two bounded ZCode advisory critics for the published synthetic MCP lab.

Not a scientific/security oracle. No tools are exposed, no real credentials or
private project material is sent. Each call is sequential and separately saved.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

EVIDENCE = Path(os.environ["MCP_EVIDENCE"])
WRAPPER = Path(os.environ["ZCODE_WRAPPER"])
OUT = Path(os.environ["OUTPUT"])
CHECKPOINT = Path(os.environ["SWARM_CHECKPOINT"])
ROLES = (
    ("security_falsifier", "Look for unsupported security guarantees and adversarial escapes."),
    ("methodology_critic", "Look for missing independent controls, confounding and external validity."),
)

def sha(data):
    return hashlib.sha256(data).hexdigest()

evidence = json.loads(EVIDENCE.read_text())
facts = {
    "toolbox_sha256": evidence["toolbox_sha256"],
    "checks_total": evidence["checks_total"],
    "checks_passed": evidence["checks_passed"],
    "tool_allowlist": evidence["tool_allowlist"],
    "network": evidence["network"],
    "published_ports": evidence["published_ports"],
    "production_database_touched": evidence["production_database_touched"],
    "tested_controls": [x["name"] for x in evidence["checks"]],
    "limits": evidence["limits"],
}
CHECKPOINT.mkdir(parents=True, exist_ok=True)
results = []
for role, guidance in ROLES:
    prompt = (
        "You are an independent skeptical reviewer of a *synthetic* PostgreSQL MCP "
        "security experiment, not a penetration test. " + guidance +
        " Derive only from these recorded claims; do not imply full tool safety. "
        'Return ONLY {"decision":"ACCEPT_BOUNDED|REWORK|BLOCKED",'
        '"largest_remaining_gap":"...", "next_independent_oracle":"..."}. '
        "Be specific and short. Evidence: " +
        json.dumps(facts, ensure_ascii=False, separators=(",", ":"))
    )
    record = {"role": role, "prompt_sha256": sha(prompt.encode()),
              "status": "BLOCKED_PROVIDER"}
    started = time.perf_counter()
    try:
        p = subprocess.run(["node", str(WRAPPER), "--json", prompt],
                           cwd=WRAPPER.parent, capture_output=True, text=True,
                           timeout=50)
        record.update(exit_code=p.returncode,
                      elapsed_ms=round((time.perf_counter()-started)*1000, 2),
                      response_sha256=sha(p.stdout.encode()))
        if p.returncode != 0:
            record["failure"] = "NONZERO_EXIT"
        else:
            payload = json.loads(p.stdout)
            if payload.get("stop_reason") != "end_turn":
                raise ValueError("incomplete provider output")
            texts = [x.get("text", "") for x in payload.get("content", [])
                     if x.get("type") == "text"]
            if not texts:
                raise ValueError("empty content")
            raw = "\n".join(texts)
            if raw.strip().startswith("```"):
                raw = raw.strip().split("\n", 1)[1].rsplit("```", 1)[0]
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                obj = json.loads(raw[raw.index("{"):raw.rindex("}")+1])
            if obj.get("decision") not in {"ACCEPT_BOUNDED", "REWORK", "BLOCKED"}:
                raise ValueError("invalid decision")
            if not all(isinstance(obj.get(key), str) and obj[key].strip()
                       for key in ("largest_remaining_gap", "next_independent_oracle")):
                raise ValueError("missing rationale")
            record.update(status="COMPLETE", model=payload.get("model"),
                          usage=payload.get("usage", {}), advisory=obj)
    except subprocess.TimeoutExpired:
        record.update(failure="TIMEOUT", elapsed_ms=round((time.perf_counter()-started)*1000, 2))
    except (ValueError, KeyError, TypeError) as exc:
        record.update(failure="INVALID_RESPONSE", failure_type=type(exc).__name__)
    results.append(record)
    (CHECKPOINT / (role+".json")).write_text(
        json.dumps(record, ensure_ascii=False, indent=2)+"\n")
    print("ZCODE_SECURITY_ROLE", role, record["status"], record.get("elapsed_ms"), flush=True)
report = {
    "date": "2026-11-07",
    "scope": "advisory two-role scrutiny of bounded synthetic MCP Toolbox results",
    "source_json_sha256": sha(EVIDENCE.read_bytes()),
    "physical_workers": 1,
    "roles_completed": sum(x["status"] == "COMPLETE" for x in results),
    "roles_blocked": sum(x["status"] != "COMPLETE" for x in results),
    "roles": results,
    "interpretation": "Model roles are advisory, not independent security test or oracle",
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
