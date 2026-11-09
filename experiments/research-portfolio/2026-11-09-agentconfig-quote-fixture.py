#!/usr/bin/env python3
"""Execute only exact pinned check_findings() with entirely synthetic input."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

COMMIT="489e074ab0daaadb732673c193047172a3744862"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    raw=args.source.read_bytes()
    tree=ast.parse(raw.decode("utf-8"))
    names=[f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name=="check_findings"]
    assert len(names)==1
    code=compile(ast.fix_missing_locations(ast.Module(body=names,type_ignores=[])),str(args.source),"exec")
    environment={}
    exec(code,environment)
    check=environment["check_findings"]
    files=[("reviewed.py","allowed_action = True\ninjection_target = 'PAUSE'\n")]
    examples=[
        {"file":"reviewed.py","line":1,"evidence":"allowed_action = True"},
        {"file":"reviewed.py","line":1,"evidence":"injection_target = 'PAUSE'"},
        {"file":"reviewed.py","line":2,"evidence":"missing evidence"},
        {"file":"missing.py","line":1,"evidence":"allowed_action = True"},
    ]
    results=check([v.copy() for v in examples],files)
    expected=[True,False,False,False]
    for item,expected_same in zip(results,expected):
        actual_same=bool(item["location_ok"] and item["evidence_found"])
        if item is results[1]:
            assert actual_same, "Expected pinned original cross-line false acceptance"
        else:
            assert actual_same==expected_same
    oracle=[]
    for item in results:
        current=dict(files).get(item["file"])
        lines=current.splitlines() if current else []
        exact=bool(current and 1<=item["line"]<=len(lines) and
                   " ".join(item["evidence"].split()) in " ".join(lines[item["line"]-1].split()))
        oracle.append(exact)
    assert oracle==expected
    payload={
        "status":"PINNED_ORIGINAL_SOURCE_FALSE_LINE_BINDING_REPRODUCED",
        "source_repo":"Artemedi/agent-config",
        "source_git_sha":COMMIT,
        "source_file":"tools/review.py",
        "source_file_sha256":hashlib.sha256(raw).hexdigest(),
        "scope":"AST-extracted check_findings only, four synthetic claims; external false-line oracle, network-denied sandbox",
        "records":[{
            "case_index":i,
            "location_ok":r["location_ok"],
            "source_evidence_found_anywhere":r["evidence_found"],
            "quoted_evidence_found_at_claimed_line":oracle[i],
            "false_line_binding_if_fields_anded":bool(r["location_ok"] and r["evidence_found"] and not oracle[i])
        } for i,r in enumerate(results)],
        "false_line_binding_cases":1,
        "limits":[
            "check_findings returns diagnostic flags; no proof downstream consumers auto-approve a finding.",
            "The candidate strict line-bound validator has not been implemented or compared across held-out real traces.",
            "No project files, secrets, network or service were modified.",
        ]
    }
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOURCE_QUOTE_LINE_ORACLE",payload["false_line_binding_cases"],"false-line case")
if __name__=="__main__":
    main()
