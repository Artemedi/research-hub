#!/usr/bin/env python3
"""Evidence boundary for no currently documented controllable KV backend.

Checks all 45 private project profiles as a CURRENT SNAPSHOT and emits only
aggregate evidence. A negative documentation scan is not a proof of no source
implementation, nor an authorization to inspect user machines.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--registry",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    registry=args.registry.resolve()
    rev=subprocess.check_output(["git","-C",str(registry),"rev-parse","HEAD"],text=True).strip()
    project_paths=sorted((registry/"projects").rglob("PROJECT.md"))
    assert len(project_paths)==45, "Do not assign NO_FIT for an incomplete registry"
    dig=hashlib.sha256()
    alltexts=[]
    for p in project_paths:
        s=p.read_text(encoding="utf-8")
        assert len(s.strip())>=100, "Empty/partial project description"
        rel=str(p.relative_to(registry))
        dig.update(f"{rel}:{hashlib.sha256(s.encode()).hexdigest()}\n".encode())
        alltexts.append(s)
    # A candidate requires an EXPLICITLY documented serving implementation and
    # an eviction/lifecycle control seam, not incidental 'KV', 'cache', 'routing',
    # 'GPU', 'memory' or 'LLM' vocabulary.
    serving=re.compile(r"(?i)\b(vllm|sglang|lmcache|mooncake|inference server|serving backend)\b")
    control=re.compile(r"(?i)(KV.{0,12}(evict|cache|manag|hook)|evict.{0,30}(cache|KV)|cache.{0,30}(evict|hook)|pin.{0,10}unpin)")
    candidates=[s for s in alltexts if serving.search(s) and control.search(s)]
    assert not candidates, "Relevant capability profile found: manually adjudicate before NO_FIT"
    result={
        "date":"2026-11-09",
        "private_registry_commit":rev,
        "profiles_read":len(project_paths),
        "aggregate_profile_set_sha256":dig.hexdigest(),
        "documented_controllable_kv_backend_candidates":0,
        "scope":"Current PROJECT.md descriptions only, checked all 45; no private profile bodies or per-file digests published.",
        "decision":"NO_CURRENT_VERIFIED_FIT_FOR_PHYSICAL_KV_CACHE_CONTROL",
        "evaluated_studies":["kvtether","random-attention"],
        "independent_prior_technical_reviews":[
            "reviews/kvtether/2026-11-05-full-text.md",
            "studies/random-attention.md"
        ],
        "limits":[
            "This negative capability gate is restricted to the registered current project portfolio; it does not disprove unregistered machines or future/new source-level implementations.",
            "Lexical scan independently confirms absence of explicit full serving plus KV policy-control contract; it is not a complete per-repository source audit.",
            "No model weights, GPU runtime, LLM calls or private project source were accessed.",
            "Reopen this current-portfolio NO_FIT only on documented controllable KV backend + owner-approved offline measurement."
        ]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PROFILE_GATE_PASS count={len(project_paths)} commit={rev[:10]} candidates=0")

if __name__=="__main__":
    main()
