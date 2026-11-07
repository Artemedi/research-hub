#!/usr/bin/env python3
"""Independently inventory pre-existing 83-card evidence, without promotion.

Provenance report only. Does NOT interpret dated reviews as scientific
replication, project FIT or permission to deploy. Every file SHA is local.
"""
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(os.environ["RESEARCH_HUB_ROOT"]).resolve()
OUTPUT = Path(os.environ["OUTPUT"]).resolve()
EXPECTED_COUNT = 83
DOC_RE = re.compile(r"\]\(([^)]+)\)")
KNOWN_MARKERS = (
    "FULL_TEXT_REVIEWED", "FULL_PUBLIC_DISCLOSURE_REVIEW_RECORDED",
    "PDF_APPENDICES_REVIEWED", "FULL_PRIMARY_TECHNICAL_DISCLOSURE_READ",
    "NOT_REPRODUCED", "NOT_INDEPENDENTLY_REPRODUCED", "LAB_VERIFIED",
    "NO_PRODUCTION_APPROVAL", "NO_CURRENT_TARGET", "NEEDS_EVIDENCE",
    "BLOCKED", "NOT_RUN", "AUTHOR_REPORTED", "NO_FIT"
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def local_links(card):
    body = card.read_text(encoding="utf-8")
    for link in DOC_RE.findall(body):
        path = link.split("#", 1)[0].split("?", 1)[0]
        if not path.startswith("../"):
            continue
        target = (card.parent / path).resolve()
        if not target.is_relative_to(ROOT):
            raise AssertionError("External or unsafe path " + str(target))
        if target.is_file():
            yield target.relative_to(ROOT).as_posix()


def main():
    assert (ROOT / "RESEARCH_POLICY.md").is_file()
    assert (ROOT / "AGENTS.md").is_file()
    items = []
    for card in sorted((ROOT / "studies").glob("*.md")):
        if card.name == "INDEX.md":
            continue
        text = card.read_text(encoding="utf-8")
        refs = sorted(set(local_links(card)))
        dated = sorted(p.relative_to(ROOT).as_posix()
                       for p in (ROOT / "reviews" / card.stem).glob("*.md"))
        portfolio_review = [
            x for x in refs if x.startswith("portfolio/") and x.endswith("/review.md")
        ]
        alias_review = [
            x for x in refs if x.startswith("reviews/") and x.endswith(".md")
            and x not in dated and not x.endswith("/README.md")
        ]
        historical = [
            x for x in refs if x.startswith("archive/dsh/knowledge/research/")
            and x.endswith(".md")
        ]
        if dated:
            path = dated[-1]
            mode = "DATED_SOURCE_REVIEW"
        elif portfolio_review:
            path = sorted(portfolio_review)[-1]
            mode = "WEEKLY_PORTFOLIO_REVIEW"
        elif alias_review:
            path = sorted(alias_review)[-1]
            mode = "DATED_ALIAS_REVIEW"
        elif historical:
            path = historical[-1]
            mode = "HISTORIC_SOURCE_REVIEW"
        else:
            raise AssertionError("Missing independently locatable source review: " + card.stem)
        assert (ROOT / path).is_file()
        refs_to_experiments = [x for x in refs if x.startswith("experiments/")]
        result_links = [x for x in refs if x.startswith("data/results/")]
        fit_links = [x for x in refs if "project-fit" in x]
        label_markers = [token for token in KNOWN_MARKERS if token in text]
        source_urls = re.findall(r"https?://[^\s)\]<>]+", text)
        arxiv_ids = sorted(set(re.findall(
            r"(?:arxiv.org/(?:abs|pdf|html)/)(\d{4}\.\d{4,5})", text)))
        if arxiv_ids:
            source_category = "SCIENTIFIC_PREPRINT_OR_ARTICLE"
        elif "paper.pdf" in text or "DOI" in text:
            source_category = "TECHNICAL_PAPER_OTHER"
        elif "github.com" in text:
            source_category = "ENGINEERING_OR_TECHNICAL_DISCLOSURE"
        else:
            source_category = "OTHER_PRIMARY_SOURCE"
        items.append({
            "id": card.stem,
            "card": "studies/" + card.name,
            "card_sha256": sha(card.read_bytes()),
            "review_provenance": path,
            "review_sha256": sha((ROOT / path).read_bytes()),
            "review_mode": mode,
            "all_dated_card_reviews": dated,
            "source_category_heuristic": source_category,
            "source_arxiv_ids": arxiv_ids,
            "source_url_count": len(source_urls),
            "portfolio_review_links": portfolio_review,
            "experiment_links_in_card": refs_to_experiments,
            "result_links_in_card": result_links,
            "project_fit_links_in_card": fit_links,
            "markers_in_card_not_verdict": label_markers,
            "research_gate": "DOCUMENTARY_EVIDENCE_LOCATED_NOT_SCIENTIFIC_VERIFIED",
            "project_gate": "NO_NEW_PROJECT_FIT_ASSESSED_IN_THIS_INVENTORY",
        })
    assert len(items) == EXPECTED_COUNT
    assert len({x["id"] for x in items}) == EXPECTED_COUNT
    groups = {}
    for item in items:
        groups[item["review_mode"]] = groups.get(item["review_mode"],0)+1
    assert sum(groups.values()) == EXPECTED_COUNT
    assert len([x for x in items if not x["all_dated_card_reviews"]]) == 32
    assert any(x["id"] == "self-replicating-prompt-injections" and
               x["review_mode"] == "HISTORIC_SOURCE_REVIEW" for x in items)
    record = {
        "date": "2026-11-07",
        "source_repository": "Artemedi/research-hub",
        "catalog_scope": "83 canonical studies, excluding generated INDEX.md",
        "research_hub_git_sha": os.environ["SOURCE_SHA"],
        "source_files_hash_enforced": True,
        "card_count": EXPECTED_COUNT,
        "review_provenance_counts": groups,
        "cards_without_individual_dated_reviews": 32,
        "documentary_review_provenance_found": len(items),
        "scientific_replication_verified_by_this_audit": 0,
        "new_project_fits": 0,
        "data_only": True,
        "items": items,
        "limitations": [
            "This audit verifies local review-document provenance, not whether the review accurately read the complete external source",
            "Some reports review multiple sources; a link alone does not independently establish that each paper was experimentally reproduced",
            "Marker words are copied as metadata, not reinterpreted as scientific verdicts",
            "Existing projects, source bodies, original reviews and assessment histories remain unmodified",
        ],
        "status": "ALL_83_DOCUMENTARY_REVIEW_PATHS_LOCATED_REPLICATION_SEPARATE",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({
        "cards":EXPECTED_COUNT, "groups":groups,
        "historical_only":[x["id"] for x in items
                           if x["review_mode"]=="HISTORIC_SOURCE_REVIEW"],
        "checksum":sha(OUTPUT.read_bytes())
    },ensure_ascii=False))


if __name__ == "__main__":
    main()
