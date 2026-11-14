#!/usr/bin/env python3
"""Drift Inspector step A: recompute counts and paper-level prevalence from the published CSV.

Offline and deterministic. Input is the author's published cluster labels
(Hamyrappy/drift-inspector @6c643d6, artifacts/baseline/acc_clusters_emnlp.csv).
It does NOT rerun LLM extraction, embeddings, UMAP or HDBSCAN, so it checks the
arithmetic of the published table, not the scientific pipeline.

Usage: 2026-11-14-step-a-prevalence.py --csv PATH [--out PATH]
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "data/results/drift-inspector/2026-11-14-step-a-prevalence.json"
SOURCE = "https://github.com/Hamyrappy/drift-inspector/blob/6c643d6ebfaa771d01c743d921dac839dd771c40/artifacts/baseline/acc_clusters_emnlp.csv"
PINNED_SHA256 = "e0854f1df2f3dca198d105417df70cb8832cb97230a39a0f6abad7789059b47e"
# Numbers stated in reviews/drift-inspector/2026-11-13.md (confirmed there by reading this CSV).
EXPECTED = {"papers": 4488, "claims": 16576, "clusters": 80, "noise_claims": 5980,
            "noise_share_percent": 36.08, "papers_per_year": 748, "years": [2020, 2021, 2022, 2023, 2024, 2025]}


def analyse(path):
    raw = Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    claims = len(rows)
    paper_year, year_papers = {}, defaultdict(set)
    cluster_names, cluster_claims = {}, defaultdict(int)
    cluster_year_papers = defaultdict(lambda: defaultdict(set))
    ids = set()
    for r in rows:
        cid, pid, year, cl = r["claim_id"], r["paper_id"], int(r["year"]), int(r["cluster"])
        assert cid not in ids, f"duplicate claim_id {cid}"
        ids.add(cid)
        assert paper_year.setdefault(pid, year) == year, f"paper {pid} has two years"
        year_papers[year].add(pid)
        cluster_claims[cl] += 1
        cluster_names.setdefault(cl, r["cluster_name"])
        cluster_year_papers[cl][year].add(pid)
    noise = cluster_claims.get(-1, 0)
    clusters = sorted(c for c in cluster_claims if c != -1)
    per_year = {y: len(year_papers[y]) for y in sorted(year_papers)}
    prevalence = {}
    for c in clusters:
        prevalence[str(c)] = {
            "name": cluster_names[c], "claims": cluster_claims[c],
            "paper_prevalence_by_year": {str(y): round(len(cluster_year_papers[c].get(y, ())) / per_year[y], 6) for y in per_year},
            "papers_by_year": {str(y): len(cluster_year_papers[c].get(y, ())) for y in per_year},
        }
    measured = {"papers": len(paper_year), "claims": claims, "clusters": len(clusters), "noise_claims": noise,
                "noise_share_percent": round(100 * noise / claims, 2), "papers_per_year": sorted(set(per_year.values())),
                "years": sorted(per_year)}
    checks = {
        "csv_sha256_matches_pinned": sha == PINNED_SHA256,
        "papers": measured["papers"] == EXPECTED["papers"],
        "claims": measured["claims"] == EXPECTED["claims"],
        "clusters": measured["clusters"] == EXPECTED["clusters"],
        "noise_claims": measured["noise_claims"] == EXPECTED["noise_claims"],
        "noise_share_percent": measured["noise_share_percent"] == EXPECTED["noise_share_percent"],
        "papers_per_year_each_748": measured["papers_per_year"] == [EXPECTED["papers_per_year"]],
        "years": measured["years"] == EXPECTED["years"],
    }
    # Paper-level vs claim-level share for the largest clusters shows why the unit matters.
    top = sorted(clusters, key=lambda c: -cluster_claims[c])[:5]
    unit_contrast = {str(c): {"name": cluster_names[c], "claim_share_percent": round(100 * cluster_claims[c] / claims, 2),
                              "distinct_papers": len({p for y in cluster_year_papers[c] for p in cluster_year_papers[c][y]})} for c in top}
    return {
        "scope": "step-A-published-csv-arithmetic",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "limitations": ["Recomputes counts and paper-level prevalence from the author's published labels only.",
                        "LLM extraction, SPECTER2 embeddings, UMAP and HDBSCAN were NOT re-executed.",
                        "Prevalence is descriptive, not causal; conference composition and clustering settings affect trends.",
                        "Says nothing about project benefit; ACC labels are faithful-to-abstract, not verified science."],
        "source": {"url": SOURCE, "sha256": sha},
        "expected_from_review": EXPECTED, "measured": measured, "checks": checks,
        "largest_clusters_claim_vs_paper_unit": unit_contrast,
        "clusters": prevalence,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    result = analyse(args.csv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"], json.dumps(result["measured"], ensure_ascii=False))
    print("checks:", {k: v for k, v in result["checks"].items() if not v} or "all true")
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
