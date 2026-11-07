#!/usr/bin/env python3
"""Eight pinned public full-text excerpts for independent advisory roles.

Full source HTML stays in temporary local cache. Only SHA/section metadata and
limited model-output receipts are committed. Models see only public excerpts.
"""
from bs4 import BeautifulSoup
import hashlib
import json
import os
from pathlib import Path

DOCS = {
    "agent-risk": ("2610.16280v1", "00efdbf5d47fa0fd5895c1bed6211302a477c2183f066959496f02ca7bc45d72"),
    "agentic-self-awareness": ("2610.19226v1", "2b4273b6c050456134604714bbc091b6242193ab47e58b1d18e31814673ff913"),
    "memscope": ("2610.21170v1", "b0401a1ed64e01aa0ecfe68b2ec035037434ceaf2723ad98324dd2329742bdc6"),
    "harnesssecurity-bench": ("2610.07639v1", "c1dd3f5e0445f7f19aec877c4e529a854df17b0ea71488e45c4f9a8fc2ec2812"),
    "matoi": ("2610.21394v1", "1077ad83aa736627e0a5dd7a8d46ef97591cf4d0862aa5b78a9d05e4cf533a4c"),
    "poisoned-skills": ("2610.37738v1", "ed0857f1d2c1a920ab884533fb95bf18157f4495464dd86472b6e29b7236a989"),
    "trust-region-injection": ("2610.38867v1", "2968b28363d1928a91f448bca8c9b0e52a36a52efa52c9693b5c66a31177117c"),
    "red-teaming-auto-mode": ("2609.19587v2", "32c529e7df37b9a411758da8edb962d640f9182df6251dfd602db7caeaa444b0"),
}
SOURCES = Path(os.environ["SOURCE_DIR"])
PACKETS = Path(os.environ["PACKET_DIR"])
OUTPUT = Path(os.environ["OUTPUT"])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def squish(text):
    return " ".join(text.split())


def excerpts(html):
    soup = BeautifulSoup(html, "html.parser")
    headings = [x for x in soup.select("h2,h3") if x.parent is not None]
    patterns = {
        "method": ("method", "approach", "evaluation", "problem formulation"),
        "results": ("results", "experiment", "applying the framework", "findings"),
        "limits": ("limitations", "discussion", "threats to validity"),
    }
    blocks = {}
    for key, terms in patterns.items():
        chosen = None
        for heading in headings:
            title = squish(heading.get_text(" ",strip=True))
            if any(term in title.lower() for term in terms):
                if key == "limits" and "limitation" not in title.lower():
                    continue
                chosen = heading
                break
        if chosen is None and key == "limits":
            for heading in headings:
                if "discussion" in heading.get_text(" ",strip=True).lower():
                    chosen = heading
                    break
        if chosen is None:
            blocks[key] = {"heading": None, "text": ""}
            continue
        title = squish(chosen.get_text(" ",strip=True))
        siblings = []
        for sibling in chosen.next_siblings:
            if getattr(sibling, "name", None) in ("h2","h3"):
                break
            if getattr(sibling, "name", None) is None:
                continue
            value = squish(sibling.get_text(" ",strip=True))
            if value and len(value)>38:
                siblings.append(value)
            if len(" ".join(siblings))>=900:
                break
        passage = " ".join(siblings)[:1100]
        if not passage:
            passage=squish(chosen.parent.get_text(" ",strip=True))[:900]
        blocks[key] = {"heading": title, "text": passage}
    return blocks


def main():
    PACKETS.mkdir(parents=True,exist_ok=True)
    records = []
    model_inputs = []
    for key,(version,expected) in DOCS.items():
        raw = (SOURCES/(key+".html")).read_bytes()
        assert sha(raw)==expected, key
        source = excerpts(raw.decode("utf-8","replace"))
        assert source["method"]["text"] and source["results"]["text"], key
        model_inputs.append({
            "id":key,
            "source_url":"https://arxiv.org/html/"+version,
            "passages":source,
        })
        records.append({
            "id":key, "source_url":"https://arxiv.org/html/"+version,
            "full_html_sha256":expected,"full_html_bytes":len(raw),
            "passages":{name:{
                "heading":body["heading"],
                "passage_sha256":sha(body["text"].encode()),
                "character_count":len(body["text"]),
                "present":bool(body["text"])
            } for name,body in source.items()},
            "full_text_read_for_extraction":True,
            "author_claims_not_experimentally_reproduced":True,
        })
    assert len(records)==8
    batches = [model_inputs[i:i+2] for i in range(0,8,2)]
    for idx,batch in enumerate(batches):
        (PACKETS/f"batch-{idx}.json").write_text(
            json.dumps(batch,ensure_ascii=False,indent=2)+"\n")
    result={
        "date":"2026-11-07",
        "status":"EIGHT_PINNED_FULL_HTML_SOURCE_PACKETS_PREPARED",
        "full_legal_html_available":8,
        "batch_count":len(batches),"items_per_batch":2,
        "sources":records,
        "no_article_fulltext_distributed":True,
        "method_note":"Short source excerpts are advisory model inputs; every author claim requires separate external verification before status changes",
        "limitations":[
            "String-excerpt selection does not independently verify all results or appendix limitations",
            "All full public HTML lives only in temporary runtime, not redistributed",
            "This extraction does not itself reproduce scientific experiments",
        ]
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "sources":len(records),"batches":len(batches),
        "empty_limitations":[x["id"] for x in records
                             if not x["passages"]["limits"]["present"]],
        "manifest_sha256":sha(OUTPUT.read_bytes())
    }))


if __name__=="__main__":
    main()
