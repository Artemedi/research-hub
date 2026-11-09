#!/usr/bin/env python3
"""Independent structural evidence audit; does NOT adjudicate semantic science.

Checks every status and every cited source-byte SHA from a separately written
implementation, with negative mutation controls. Primary scientific validity
must remain supported by the source and human methodology review itself.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "data/results/research-portfolio/2026-11-09-closure-ledger.json"
EXPECTED_STATUSES = {
    "ACCEPT_BOUNDED": 40,
    "ACCEPT_RESEARCH_ONLY": 39,
    "BLOCKED": 2,
    "NO_FIT": 2,
}
EXPECTED_BLOCKED = {"claude-swarm", "hyperresearch"}
EXPECTED_NO_FIT = {"kvtether", "random-attention"}
HISTORIC_WITHOUT_RAW = {"mcp-toolbox-postgres", "pgbot"}

def hashbytes(data):
    return hashlib.sha256(data).hexdigest()

def verify(obj):
    source = json.loads((ROOT / "catalog/entities.json").read_text())
    expected = {s["id"]: s["card"] for s in source["studies"]}
    assert len(expected) == 83
    rows = obj["studies"]
    ids = [r["study_id"] for r in rows]
    assert len(rows) == len(ids) == len(set(ids)) == 83
    assert set(ids) == set(expected)
    counts = Counter(r["closure_status"] for r in rows)
    assert dict(counts) == EXPECTED_STATUSES
    assert obj["summary"]["by_status"] == dict(sorted(counts.items()))
    assert obj["summary"]["total"] == obj["summary"]["terminal"] == 83
    assert obj["summary"]["open"] == 0
    assert obj["summary"]["explicit_project_pairs"] == 506
    assert obj["summary"]["unassessed_project_pairs"] == 3229
    assert obj["summary"]["explicit_project_pairs"] + obj["summary"]["unassessed_project_pairs"] == 83 * 45
    assert obj["basis_entities_sha256"] == hashbytes((ROOT / "catalog/entities.json").read_bytes())
    blocked = set()
    no_fit = set()
    evidence_checked = 0
    research_full = 0
    bounded_rechecks = 0
    for r in rows:
        sid = r["study_id"]
        status = r["closure_status"]
        assert r["card"] == expected[sid]
        assert hashbytes((ROOT / r["card"]).read_bytes()) == r["card_sha256"]
        assert hashbytes((ROOT / r["review_document"]).read_bytes()) == r["review_sha256"]
        assert hashbytes((ROOT / r["current_catalog_review"]).read_bytes()) == r["current_catalog_review_sha256"]
        assert r["author_results_independently_replicated_by_this_ledger"] is False
        assert r["production_approved"] is False
        assert r["primary_url"].startswith("https://")
        evidence = r["evidence"]
        assert evidence and len({e["path"] for e in evidence}) == len(evidence)
        for entry in evidence:
            path = ROOT / entry["path"]
            assert path.is_file(), entry
            assert hashbytes(path.read_bytes()) == entry["sha256"], (sid, entry["path"])
            evidence_checked += 1
        assert len(r["limits"]) >= 60, sid
        if status == "ACCEPT_BOUNDED":
            assert len(r["verified_scope"]) >= 50
            assert "deployment_gate" in r and len(r["deployment_gate"]) >= 40
            assert len(evidence) >= 2
            if sid in HISTORIC_WITHOUT_RAW:
                assert r.get("independently_reexecuted_this_pass") is False
                assert r.get("evidence_tier") == "HISTORIC_ORIGINAL_LAB_DOCUMENTED_ONLY_WITHOUT_RETAINED_RAW_RECEIPTS"
                assert "not retained" in r["limits"] or "not included" in r["limits"]
            if r.get("evidence_tier") == "TWO_PINNED_PUBLIC_SOURCE_REPLAYS_WITH_INDEPENDENT_ORIGINAL_FIXTURE_SHA":
                assert r["independently_reexecuted_this_pass"] is True
                assert len(evidence) == 3
                bounded_rechecks += 1
        elif status == "ACCEPT_RESEARCH_ONLY":
            assert r["author_results"] == "AUTHOR_REPORTED / NOT_REPRODUCED"
            assert r["rechecked_source_bytes_in_this_pass"] is False
            assert len(r["methodological_reference"]) >= 50
            assert r["verified_scope"].startswith("CRITICALLY_REVIEWED_PRIMARY_SOURCE_METHOD")
            assert len(r["deployment_gate"]) >= 50
            if sid not in ("self-replicating-prompt-injections", "unsloth-decision-model"):
                assert r["primary_source_full_text_prior_review"] is True
                assert r["previous_full_primary_review_documents"]
                research_full += 1
        elif status == "BLOCKED":
            blocked.add(sid)
            assert len(r["blocker"]) >= 80 and len(r["attempted_alternative"]) >= 75
            assert len(r["unblock_condition"]) >= 110
            assert len(evidence) >= 2
            assert r["verified_scope"]
        elif status == "NO_FIT":
            no_fit.add(sid)
            assert r["verified_scope"] == "CURRENT_REGISTERED_PROJECT_PORTFOLIO_ONLY"
            assert len(r["decision"]) >= 90 and len(r["reopen_condition"]) >= 90
            assert len(evidence) >= 2
        else:
            raise AssertionError(f"Nonterminal or unknown status for {sid}")
    assert blocked == EXPECTED_BLOCKED
    assert no_fit == EXPECTED_NO_FIT
    assert bounded_rechecks == 6
    assert research_full == 37
    return {"studies": len(rows), "evidence_refs_sha_verified": evidence_checked,
            "full_primary_source_method_reviews_prior": research_full,
            "original_pinned_source_helper_rechecks": bounded_rechecks,
            "status_counts": dict(sorted(counts.items()))}

def main():
    obj=json.loads(LEDGER.read_text())
    result=verify(obj)
    mutations = [
        lambda d: d["studies"][0]["evidence"][0].update(sha256="0"*64),
        lambda d: d["studies"][0].update(closure_status="ACCEPT"),
        lambda d: next(r for r in d["studies"] if r["study_id"] == "hyperresearch").update(unblock_condition=""),
        lambda d: next(r for r in d["studies"] if r["study_id"] == "pgbot").update(independently_reexecuted_this_pass=True),
        lambda d: next(r for r in d["studies"] if r["study_id"] == "paper2agent").update(author_results="INDEPENDENTLY_REPLICATED"),
        lambda d: d["summary"].update(terminal=82),
    ]
    for mutate in mutations:
        changed = deepcopy(obj)
        mutate(changed)
        try:
            verify(changed)
        except AssertionError:
            continue
        raise AssertionError("FAIL_OPEN: structural mutant was wrongly accepted")
    result.update({
        "status": "PASS_STRUCTURAL_EVIDENCE_ONLY",
        "input_sha256": hashbytes(LEDGER.read_bytes()),
        "mutations_injected": len(mutations),
        "mutations_rejected": len(mutations),
        "scope": "Independent file-hash and disposition contract verification, NOT independent re-analysis of paper outcomes, author-reported statistics or medical truth.",
        "limitations": [
            "Source-level experiments remain bounded and are supported by their original dated reviews and original-source fixtures.",
            "Scientific content of research-only reviews was previously read by the reviewing agents, not re-downloaded and empirically replicated here.",
            "Two original PostgreSQL/MCP lab reports lack retained raw JSON receipts; they are explicitly distinguished and cannot be treated as freshly reproduced.",
            "The 45-profile NO_FIT is current registered portfolio only and not a source audit of every implementation.",
            "Project integration needs separate user permission, held-out tests and privacy review."
        ]
    })
    out = ROOT / "data/results/research-portfolio/2026-11-09-ledger-independent-check.json"
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv[1:]:
        assert out.read_text() == output, "Stale independent ledger receipt"
    else:
        out.write_text(output)
    print("LEDGER_INDEPENDENT_CHECK",result["status"],result["studies"],
          "evidence SHA",result["evidence_refs_sha_verified"],
          "mutations",result["mutations_rejected"])

if __name__=="__main__":
    main()
