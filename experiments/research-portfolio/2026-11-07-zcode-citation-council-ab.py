#!/usr/bin/env python3
"""Offline, two-role ZCode citation A/B against a clean pinned Paper2Project App.

Synthetic evidence only.  One physical remote worker, checkpoint per model call,
no tools offered to ZCode, no target changes, no private project descriptions.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

TARGET = Path(os.environ["P2P_SOURCE"]).resolve()
WRAPPER = Path(os.environ["ZCODE_WRAPPER"]).resolve()
OUT = Path(os.environ.get("OUTPUT", "zcode-citation-council-ab.json"))
CHECKPOINT = Path(os.environ["SWARM_CHECKPOINT"]).resolve()
PIN = "6d82a42175a71d3327b773df88f1da0707efe43c"
ROLES = ("grounded_reviewer", "adversarial_falsifier")
FACTS = [
    ("Alpha completes snapshot restore in exactly 12 minutes.",
     "Alpha's snapshot restoration lasts precisely twelve minutes.",
     "Alpha does not restore snapshots in twelve minutes.",
     "Alpha completes snapshot restore in exactly 9 minutes.",
     "Beta completes snapshot restore in exactly 12 minutes.",
     "Alpha uses an external alerting service."),
    ("Beta retains audit events for exactly 30 days.",
     "Beta keeps audit log entries for precisely thirty days.",
     "Beta never retains audit events.",
     "Beta retains audit events for exactly 7 days.",
     "Gamma retains audit events for exactly 30 days.",
     "Beta exports incident archives in JSON format."),
    ("Gamma allows at most 3 concurrent workers.",
     "Gamma caps simultaneous workers at three.",
     "Gamma permits an unlimited number of concurrent workers.",
     "Gamma allows at most 8 concurrent workers.",
     "Delta allows at most 3 concurrent workers.",
     "Gamma transmits task progress by email."),
    ("Delta encrypts exported archives with AES-256.",
     "Delta uses 256-bit AES encryption for archive exports.",
     "Delta leaves exported archives unencrypted.",
     "Delta encrypts exported archives with AES-128.",
     "Omega encrypts exported archives with AES-256.",
     "Delta rotates certificates every week."),
    ("Omega retries each failed task exactly 2 times.",
     "A failed task in Omega receives precisely two retry attempts.",
     "Omega does not retry failed tasks.",
     "Omega retries each failed task exactly 5 times.",
     "Kappa retries each failed task exactly 2 times.",
     "Omega keeps every project file in cold storage."),
    ("Kappa limits individual uploads to 5 MiB.",
     "One Kappa upload cannot exceed five mebibytes.",
     "Kappa imposes no upload size restriction.",
     "Kappa limits individual uploads to 8 MiB.",
     "Alpha limits individual uploads to 5 MiB.",
     "Kappa archives request logs for three years."),
]
CLASSES = ("exact", "paraphrase", "contradiction", "wrong_number",
           "wrong_entity", "unrelated")
assert len(FACTS) == 6 and all(len(x) == len(CLASSES) for x in FACTS)

def sha(payload):
    return hashlib.sha256(payload).hexdigest()

def run(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, **kw)

def provider_response(text):
    envelope = json.loads(text)
    if envelope.get("stop_reason") != "end_turn":
        raise ValueError("provider did not complete end_turn")
    blocks = [x.get("text", "") for x in envelope.get("content", [])
              if x.get("type") == "text"]
    if not blocks:
        raise ValueError("provider produced no text response")
    payload = "\n".join(blocks).strip()
    if payload.startswith("```"):
        payload = re.sub(r"^\`\`\`(?:json)?\s*|\s*\`\`\`$", "", payload).strip()
    try:
        judgments = json.loads(payload)
    except json.JSONDecodeError:
        judgments = json.loads(payload[payload.index("{"):payload.rindex("}") + 1])
    if not isinstance(judgments, dict) or not isinstance(judgments.get("judgments"), list):
        raise ValueError("invalid JSON judgments")
    return envelope, judgments["judgments"]

def one_role(batch, role, checkpoint):
    key = f"batch-{batch[0]['batch']:02d}-{role}"
    dest = checkpoint / (key + ".json")
    if dest.exists():
        record = json.loads(dest.read_text(encoding="utf-8"))
        if record.get("prompt_sha256") and record.get("status") == "COMPLETE":
            return record
    instructions = (
        "You are a citation reviewer. Label SUPPORTED only if the source sentence "
        "directly entails the entire claim. For a contradiction, a different subject, "
        "wrong number or unrelated subject, use NOT_SUPPORTED. Where genuinely ambiguous, "
        "use UNCERTAIN. No tools; do not infer unstated facts. "
        if role == "grounded_reviewer" else
        "You are an independent adversarial citation falsifier. Work blind to any "
        "other reviewer. Check quantifiers, numbers, negation and attribution. "
        "Never count topical similarity as proof. Mark SUPPORTED only on explicit "
        "entailment; NOT_SUPPORTED on absent/contradictory facts; UNCERTAIN on ambiguity. "
        "No tools."
    )
    cases = [{"id": x["id"], "source": x["source"], "claim": x["claim"]}
             for x in batch]
    prompt = instructions + (
        ' Return ONLY JSON {"judgments":[{"id":"...","decision":"SUPPORTED|NOT_SUPPORTED|UNCERTAIN"}]}. '
        "Include every ID exactly once, with no commentary. CASES: "
    ) + json.dumps(cases, ensure_ascii=False, separators=(",", ":"))
    record = {"key": key, "role": role, "batch": batch[0]["batch"],
              "prompt_sha256": sha(prompt.encode()), "status": "BLOCKED_PROVIDER"}
    started = time.perf_counter()
    try:
        p = run(["node", str(WRAPPER), "--json", prompt], cwd=str(WRAPPER.parent),
                timeout=50)
        record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
        record["exit_code"] = p.returncode
        record["response_sha256"] = sha(p.stdout.encode())
        record["stderr_sha256"] = sha(p.stderr.encode())
        if p.returncode != 0:
            record["failure"] = "NONZERO_EXIT"
        else:
            response, judgments = provider_response(p.stdout)
            assert {x.get("id") for x in judgments} == {x["id"] for x in batch}
            assert len(judgments) == len(batch)
            assert all(x.get("decision") in
                       {"SUPPORTED", "NOT_SUPPORTED", "UNCERTAIN"} for x in judgments)
            record.update(status="COMPLETE",
                          model=response.get("model"),
                          usage=response.get("usage", {}),
                          judgments=sorted(judgments, key=lambda x: x["id"]))
    except subprocess.TimeoutExpired:
        record.update(elapsed_ms=round((time.perf_counter()-started)*1000, 1),
                      failure="TIMEOUT")
    except (ValueError, AssertionError, KeyError, json.JSONDecodeError) as exc:
        record.update(failure="MALFORMED_RESPONSE",
                      failure_type=type(exc).__name__)
    dest.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print("ROLE", key, record["status"], record.get("failure", ""),
          record.get("elapsed_ms"), flush=True)
    return record

def main():
    assert WRAPPER.is_file()
    head = run(["git", "-C", str(TARGET), "rev-parse", "origin/main"])
    assert head.returncode == 0 and head.stdout.strip() == PIN
    cases = []
    for i, fixture in enumerate(FACTS):
        for j, category in enumerate(CLASSES):
            cases.append({"id": f"{i}-{category}", "batch": i,
                          "source": fixture[0], "claim": fixture[j],
                          "expected_supported": j in (0, 1), "category": category})
    assert len(cases) == 36
    # Build a clean, pinned source snapshot; no target worktree or .git metadata changed.
    with tempfile.TemporaryDirectory(prefix="p2p-clean-snapshot-") as temp:
        source = Path(temp) / "checkout"
        source.mkdir()
        a = subprocess.Popen(["git", "-C", str(TARGET), "archive", "--format=tar",
                              PIN, "src/paper2project"], stdout=subprocess.PIPE)
        assert a.stdout is not None
        b = subprocess.run(["tar", "-xf", "-", "-C", str(source)], stdin=a.stdout,
                           capture_output=True)
        a.stdout.close()
        assert a.wait() == 0 and b.returncode == 0, b.stderr[-500:]
        sys.path.insert(0, str(source / "src"))
        from paper2project.core import App
        project = Path(temp) / "project.md"
        research = Path(temp) / "study.txt"
        project.write_text("The synthetic target requires audited research evidence.\n",
                           encoding="utf-8")
        research.write_text("\n".join(x[0] for x in FACTS)+"\n", encoding="utf-8")
        app = App(Path(temp) / "workspace", allowed_roots=[Path(temp)])
        app.import_projects(project, layout="single", name="Synthetic target",
                            project_id="synthetic-target")
        app.import_research(research, research_id="synthetic-study")
        job = app.create_job("synthetic-study", ["synthetic-target"])["id"]
        docs = list(app.docs(job).values())
        rd = next(x for x in docs if x["owner_kind"] == "research")
        pd = next(x for x in docs if x["owner_kind"] == "project")
        p_cite = {"document_id": pd["id"], "start": 1, "end": 1,
                  "quote": "The synthetic target requires audited research evidence."}
        for item in cases:
            r_cite = {"document_id": rd["id"], "start": item["batch"] + 1,
                      "end": item["batch"] + 1, "quote": item["source"]}
            analysis = {"summary": "Synthetic citation pipeline test",
                        "assessments": [{"project_id": "synthetic-target",
                                         "relevance": "candidate",
                                         "rationale": item["claim"],
                                         "citations": [r_cite, p_cite]}]}
            app.submit_analysis(job, analysis)
            item["target_structure_accepted"] = True
            normalize = lambda s: re.sub(r"\s+", " ", s.casefold()).strip(" .,:;")
            item["exact_gate_auto_pass"] = normalize(item["claim"]) == normalize(item["source"])
        core_hash = sha((source / "src/paper2project/core.py").read_bytes())
    CHECKPOINT.mkdir(parents=True, exist_ok=True)
    assert not CHECKPOINT.is_symlink()
    roles = {}
    for i in range(len(FACTS)):
        batch = [c for c in cases if c["batch"] == i]
        for role in ROLES:
            roles[f"{i}-{role}"] = one_role(batch, role, CHECKPOINT)
    metrics = {}
    for role in ROLES:
        ballots = {x["id"]: x["decision"]
                   for record in roles.values()
                   if record["role"] == role and record["status"] == "COMPLETE"
                   for x in record["judgments"]}
        evaluated = [c for c in cases if c["id"] in ballots]
        metrics[role] = {
            "evaluated": len(evaluated),
            "supported_oracle": sum(x["expected_supported"] for x in evaluated),
            "auto_supported": sum(ballots[x["id"]] == "SUPPORTED" for x in evaluated),
            "false_auto_support": sum(ballots[x["id"]] == "SUPPORTED" and
                                      not x["expected_supported"] for x in evaluated),
            "true_auto_support": sum(ballots[x["id"]] == "SUPPORTED" and
                                     x["expected_supported"] for x in evaluated),
            "abstained": sum(ballots[x["id"]] == "UNCERTAIN" for x in evaluated)
        }
    complete = [c for c in cases
                if all(roles[f"{c['batch']}-{r}"]["status"] == "COMPLETE"
                       for r in ROLES)]
    joined = {}
    for c in complete:
        votes = {r: next(x["decision"] for x in roles[f"{c['batch']}-{r}"]["judgments"]
                         if x["id"] == c["id"]) for r in ROLES}
        joined[c["id"]] = votes
    council_supported = {id for id,votes in joined.items()
                         if all(v == "SUPPORTED" for v in votes.values())}
    result = {
        "date": "2026-11-07", "target": "dsh-paper2agent",
        "target_clean_pin": PIN, "target_core_sha256": core_hash,
        "synthetic_cases": len(cases), "oracle_supported": 12, "oracle_unsupported": 24,
        "baseline_structural_accepts": sum(c["target_structure_accepted"] for c in cases),
        "baseline_not_semantic_approval": True,
        "exact_only_auto_supported": sum(c["exact_gate_auto_pass"] for c in cases),
        "exact_only_false_auto_support": 0,
        "roles": ROLES, "physical_workers": 1,
        "role_runs": len(roles),
        "provider_completions": sum(r["status"] == "COMPLETE" for r in roles.values()),
        "provider_blocked": sum(r["status"] != "COMPLETE" for r in roles.values()),
        "council_evaluated": len(complete),
        "council_auto_supported": len(council_supported),
        "council_false_auto_support": sum(not c["expected_supported"] and
                                         c["id"] in council_supported for c in complete),
        "council_true_auto_support": sum(c["expected_supported"] and
                                        c["id"] in council_supported for c in complete),
        "role_metrics": metrics,
        "provider_usage": {r: {
            "status": record["status"], "model": record.get("model"),
            "usage": record.get("usage"), "elapsed_ms": record.get("elapsed_ms"),
            "prompt_sha256": record["prompt_sha256"],
            "response_sha256": record.get("response_sha256"),
            "failure": record.get("failure")
        } for r,record in sorted(roles.items())},
        "case_verdicts": [{
            "id": c["id"], "category": c["category"],
            "expected_supported": c["expected_supported"],
            "exact_gate_auto_pass": c["exact_gate_auto_pass"],
            "reviewer": joined.get(c["id"],{}).get(ROLES[0]),
            "critic": joined.get(c["id"],{}).get(ROLES[1]),
            "council_auto_supported": c["id"] in council_supported
        } for c in cases],
        "limits": [
            "All labels and source lines are deliberately authored synthetic oracle examples",
            "Inputs to ZCode are only public synthetic facts and claims; no tools or private documents",
            "No blinded natural-science held-out annotations or replication of source article",
            "Target is a clean local git-archive of a pinned remote commit, not uncommitted worktree",
            "Submission accepts structural citation scope; it is not a semantic support verdict",
            "Council auto-supported requires both votes; missing role calls remain BLOCKED",
            "No model integration into project, production changes, patient data or project approvals"
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("RESULT", json.dumps({k:result[k] for k in
          ("synthetic_cases","provider_completions","provider_blocked",
           "council_evaluated","council_false_auto_support","council_true_auto_support")}),
          flush=True)

if __name__ == "__main__":
    main()
