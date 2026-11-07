#!/usr/bin/env python3
"""Two sequential ZCode critics on bounded, synthetic Claude Swarm E2E results."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

evidence = json.loads(Path(os.environ["EVIDENCE"]).read_text())
out = Path(os.environ["OUTPUT"])
wrapper = Path(os.environ["ZCODE_WRAPPER"])
checkpoint = Path(os.environ["CHECKPOINT"])
checkpoint.mkdir(parents=True, exist_ok=True)
facts = {
    "upstream_pin": evidence["upstream_pin"],
    "tests_total": evidence["tests_total"],
    "matched_oracle": evidence["matched_oracle"],
    "tests": [{"id": x["id"], "observed": x["observed"],
               "interpretation": x["interpretation"]} for x in evidence["tests"]],
    "environment": evidence["environment"],
    "limitations": evidence["limitations"],
}
roles = [
    ("safety_critic", "Audit claim scope and any false security guarantee."),
    ("failure_critic", "Audit crash/retry oracle and identify confounding or missing controls."),
]
results = []
for role, guide in roles:
    prompt = (
        "You are an independent technical critic. " + guide +
        " No tools. This is a *mock* worker and real upstream orchestration-code test; "
        "the source repository and production were not edited. "
        'Return only JSON {"verdict":"ACCEPT_BOUNDED|REWORK|BLOCKED",'
        '"critical_risk":"one sentence","next_oracle":"one sentence"}. '
        "Never invent evidence beyond this data: " +
        json.dumps(facts, ensure_ascii=False, separators=(",", ":"))
    )
    record = {"role": role, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
              "status": "BLOCKED_PROVIDER"}
    start = time.monotonic()
    try:
        process = subprocess.run(
            ["node", str(wrapper), "--json", prompt],
            cwd=wrapper.parent, capture_output=True, text=True, timeout=50)
        record.update(elapsed_ms=round((time.monotonic()-start)*1000, 1),
                      exit_code=process.returncode,
                      response_sha256=hashlib.sha256(process.stdout.encode()).hexdigest())
        if process.returncode:
            record["failure"] = "NONZERO_EXIT"
        else:
            response = json.loads(process.stdout)
            if response.get("stop_reason") != "end_turn":
                raise ValueError("Not a completed provider turn")
            body = "\n".join(item.get("text", "") for item in response.get("content", [])
                             if item.get("type") == "text").strip()
            if body.startswith("```"):
                body = body.split("\n", 1)[-1].rsplit("```", 1)[0]
            try:
                claim = json.loads(body)
            except json.JSONDecodeError:
                claim = json.loads(body[body.index("{"):body.rindex("}")+1])
            if claim.get("verdict") not in ("ACCEPT_BOUNDED", "REWORK", "BLOCKED"):
                raise ValueError("Unsupported verdict")
            if not all(isinstance(claim.get(x), str) and claim[x].strip()
                       for x in ("critical_risk", "next_oracle")):
                raise ValueError("Missing critic explanation")
            record.update(status="COMPLETE", model=response.get("model"),
                          usage=response.get("usage"), advisory=claim)
    except subprocess.TimeoutExpired:
        record["failure"] = "TIMEOUT"
        record["elapsed_ms"] = round((time.monotonic()-start)*1000, 1)
    except (KeyError, ValueError, TypeError) as e:
        record.update(failure="INVALID_RESPONSE", failure_class=type(e).__name__)
    (checkpoint/(role+".json")).write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
    results.append(record)
    print("CRITIC", role, record["status"], record.get("elapsed_ms"), flush=True)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "date": "2026-11-07", "study": "claude-swarm", "evidence_sha256":
    hashlib.sha256(Path(os.environ["EVIDENCE"]).read_bytes()).hexdigest(),
    "physical_workers": 1, "roles": results,
    "completed": sum(x["status"] == "COMPLETE" for x in results),
    "blocked": sum(x["status"] != "COMPLETE" for x in results),
    "limitation": "ZCode is advisory model criticism; deterministic Git/tmux oracles are independent"
}, ensure_ascii=False, indent=2)+"\n")
