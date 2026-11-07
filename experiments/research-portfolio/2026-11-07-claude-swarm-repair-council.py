#!/usr/bin/env python3
"""Two bounded advisory ZCode roles critique a clean-pinned Claude Swarm lab patch.

The actual oracle is the independent Git/tmux fault-injection suite, not model
agreement. No tools or user data; checkpoint every model answer or timeout.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

PATCH = gzip.decompress(Path(os.environ["REPAIR_PATCH"]).read_bytes()).decode()
EVIDENCE = json.loads(Path(os.environ["REPAIR_EVIDENCE"]).read_text())
WRAPPER = Path(os.environ["ZCODE_WRAPPER"])
CHECKPOINT = Path(os.environ["CHECKPOINT"])
OUTPUT = Path(os.environ["OUTPUT"])
CHECKPOINT.mkdir(parents=True, exist_ok=True)
roles = [
    ("lifecycle_skeptic", "Find lifecycle races, persistent stale markers or retry data-loss still possible."),
    ("security_skeptic", "Find trust-boundary flaws of marker and CLI exit-code interpretation."),
]
facts = {
    "pin": EVIDENCE["source_pin"],
    "cases_passed": EVIDENCE["cases_passed"],
    "cases_total": EVIDENCE["cases_total"],
    "risks": EVIDENCE["remaining_risks"],
}
results = []
for role, instruction in roles:
    prompt = (
        "You are a technical adversarial reviewer of an isolated proof-of-concept, "
        "not a production authorization. " + instruction +
        ' Respond ONLY JSON with fields {"decision":"ACCEPT_BOUNDED|REWORK|BLOCKED",'
        '"most_important_gap":"...", "next_deterministic_test":"..."}. '
        "Distinguish reproduced behavior from general security assurances. "
        "Patch and facts:\n" + PATCH + "\n" + json.dumps(facts, separators=(",", ":"))
    )
    key = hashlib.sha256(prompt.encode()).hexdigest()
    path = CHECKPOINT / (role + ".json")
    if path.exists():
        old = json.loads(path.read_text())
        if old.get("status") == "COMPLETE" and old.get("prompt_sha256") == key:
            results.append(old)
            continue
    record = {"role": role, "prompt_sha256": key, "status": "BLOCKED_PROVIDER"}
    start = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="research-zcode-patch-") as temp:
            request = Path(temp) / "request.json"
            request.write_text(json.dumps({"max_tokens": 4096, "messages": [
                {"role": "user", "content": prompt}]}))
            proc = subprocess.run(
                ["node", str(WRAPPER), "--request-json", str(request)],
                cwd=WRAPPER.parent, capture_output=True, text=True, timeout=65)
        record["elapsed_ms"] = round((time.monotonic() - start) * 1000, 1)
        record["exit_code"] = proc.returncode
        record["response_sha256"] = hashlib.sha256(proc.stdout.encode()).hexdigest()
        if proc.returncode != 0:
            record["failure"] = "NONZERO_EXIT"
        else:
            message = json.loads(proc.stdout)
            if message.get("stop_reason") != "end_turn":
                raise ValueError("Model response incomplete")
            raw = "\n".join(x.get("text","") for x in message.get("content", [])
                             if x.get("type") == "text").strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
            try:
                verdict = json.loads(raw)
            except json.JSONDecodeError:
                verdict = json.loads(raw[raw.index("{"):raw.rindex("}")+1])
            if verdict.get("decision") not in ("ACCEPT_BOUNDED", "REWORK", "BLOCKED"):
                raise ValueError("Invalid verdict")
            if not all(isinstance(verdict.get(k), str) and verdict[k].strip()
                       for k in ("most_important_gap", "next_deterministic_test")):
                raise ValueError("Missing argument")
            record.update(status="COMPLETE", model=message.get("model"),
                          usage=message.get("usage"), advisory=verdict)
    except subprocess.TimeoutExpired:
        record.update(elapsed_ms=round((time.monotonic()-start)*1000,1),
                      failure="TIMEOUT")
    except (ValueError, KeyError, TypeError) as exc:
        record.update(failure="INVALID_RESPONSE", error_class=type(exc).__name__)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
    results.append(record)
    print("ZCODE_ROLE", role, record["status"], record.get("elapsed_ms"),flush=True)
summary = {
    "date": "2026-11-07", "study": "claude-swarm",
    "source_evidence_sha256": hashlib.sha256(
        Path(os.environ["REPAIR_EVIDENCE"]).read_bytes()).hexdigest(),
    "patch_sha256": hashlib.sha256(PATCH.encode()).hexdigest(),
    "physical_workers": 1, "roles": results,
    "completed": sum(x["status"] == "COMPLETE" for x in results),
    "blocked": sum(x["status"] != "COMPLETE" for x in results),
    "limits": ["Advisory model review does not override Git/tmux evidence",
               "Both roles use same provider/model family", "No tools executed by agents"]
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
