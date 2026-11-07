#!/usr/bin/env python3
"""Independent quote-locality verifier of eight-public-paper ZCode advisory roles.

No model consensus allowed to promote source, science or project status.
All source SHA, excerpt SHA and role input groups independently checked.
"""
import hashlib
import json
import os
from pathlib import Path

SOURCES=Path(os.environ["SOURCE_DIR"])
PACKETS=Path(os.environ["PACKET_DIR"])
MANIFEST=Path(os.environ["MANIFEST"])
MODEL=Path(os.environ["MODEL"])
OUTPUT=Path(os.environ["OUTPUT"])
ROLES={"source_grounder","method_falsifier"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def squish(text):
    return " ".join(text.split())


def is_local_quote(quote, body):
    if not isinstance(quote,str) or not quote:
        return False
    normalized=squish(quote)
    words=normalized.split()
    return (5<=len(words)<=14
            and normalized in squish(body)
            and len(normalized)<=180)


def main():
    manifest=json.loads(MANIFEST.read_text())
    model=json.loads(MODEL.read_text())
    assert len(manifest["sources"])==8
    assert model["source_manifest_sha256"]==sha(MANIFEST.read_bytes())
    assert model["planned_calls"]==8
    assert model["attempted_calls"]==len(model["calls"])<=8
    pinned={s["id"]:s for s in manifest["sources"]}
    for id_,entry in pinned.items():
        assert sha((SOURCES/(id_+".html")).read_bytes())==entry["full_html_sha256"]
    packets={}
    for batch in range(4):
        p=json.loads((PACKETS/f"batch-{batch}.json").read_text())
        assert len(p)==2
        packets[batch]=p
        for x in p:
            pin=pinned[x["id"]]
            assert x["source_url"]==pin["source_url"]
            for name,section in x["passages"].items():
                assert sha(section["text"].encode())==pin["passages"][name]["passage_sha256"]
                assert section["heading"]==pin["passages"][name]["heading"]
    row_index={(entry["batch"],entry["role"]):entry for entry in model["calls"]}
    assert len(row_index)==len(model["calls"])
    evaluations=[]
    for key,call in sorted(row_index.items()):
        batch,role=key
        assert role in ROLES
        inputs=packets[batch]
        assert call["ids"]==[x["id"] for x in inputs]
        if call["status"]!="COMPLETE":
            evaluations.append({
                "batch":batch,"role":role,"status":call["status"],
                "error":call.get("error"),"checked":0,
            })
            continue
        assert call["model"]=="glm-5.3-flash"
        assert len(call["items"])==2
        for x,input_item in zip(call["items"],inputs):
            assert x["id"]==input_item["id"]
            body=" ".join(section["text"] for section in input_item["passages"].values())
            has_quote=is_local_quote(x["source_anchor"],body)
            evaluations.append({
                "batch":batch,"role":role,"id":x["id"],
                "status":"ANCHOR_IN_INPUT" if has_quote else "SOURCE_QUOTE_NOT_GROUNDED",
                "anchor_sha256":sha(x["source_anchor"].encode()),
                "anchor_length_words":len(squish(x["source_anchor"]).split()),
                "advisory_evidence_status":x["evidence_status"],
                "checked":1,
            })
    assert not is_local_quote("five nonexistent sentinel words cannot match", "some real text")
    completed=sum(call["status"]=="COMPLETE" for call in model["calls"])
    grounded=sum(x["status"]=="ANCHOR_IN_INPUT" for x in evaluations)
    invalid=sum(x["status"]=="SOURCE_QUOTE_NOT_GROUNDED" for x in evaluations)
    result={
        "date":"2026-11-07",
        "status":"MODEL_ADVISORY_QUOTE_LOCALITY_ONLY",
        "manifest_sha256":sha(MANIFEST.read_bytes()),
        "model_sha256":sha(MODEL.read_bytes()),
        "completed_model_calls":completed,
        "total_model_calls":len(model["calls"]),
        "grounded_short_quotes":grounded,
        "ungrounded_short_quotes":invalid,
        "failed_model_calls":len(model["calls"])-completed,
        "negative_missing_quote_rejected":True,
        "full_text_sha_verified":8,
        "evaluations":evaluations,
        "scientific_accept_claims":0,
        "independent_model_families":1,
        "limitations":[
            "Verbatim quote locality does not validate interpretation, empirical accuracy or completeness",
            "Source extracted snippets are public and may miss context from the complete paper",
            "Author-reported numerical results are not independently rerun",
            "Two roles use the same ZCode model family; agreement is not independent truth"
        ],
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "calls":completed,"grounded":grounded,
        "ungrounded":invalid,"failed":result["failed_model_calls"]
    }))


if __name__=="__main__":
    main()
