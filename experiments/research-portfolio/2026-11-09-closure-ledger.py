#!/usr/bin/env python3
"""Evidence-gated 83-study closure inventory. Does not infer verdicts from PASS."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

# Each entry: tested proposition, reviewed source, independent machine result, limit.
BOUNDED = {
    "agent-error-dataset": (
        "Checkpoint-bound correction: 90 synthetic paired trials; 270 negative controls.",
        "reviews/agent-error-dataset/2026-11-08-checkpoint-replay-ab.md",
        "data/results/agent-error-dataset/2026-11-08-independent-oracle.json",
        "No live agents, source dataset, causal RCA or real project recovery rate."),
    "agent-risk": (
        "Targeted replay versus live oracle on 200 synthetic finite episodes and assumption-breaking controls.",
        "reviews/agent-risk/2026-11-09-replay-assumptions.md",
        "data/results/agent-risk/2026-11-09-replay-boundary.json",
        "No original authors' model runs or real production gate approval."),
    "cera-moa": (
        "Independent synthetic oracle of cumulative-threshold routing rule over 10,000 scenarios.",
        "reviews/cera-moa/2026-11-08-routing-contract.md",
        "data/results/cera-moa/2026-11-08-independent-oracle.json",
        "No learned router, GPU quality/latency replication; one confidential project profile remains unassessed."),
    "chartli": (
        "Independent XML and finite SVG geometry oracles on 16 original-source fixtures with bad-input controls.",
        "reviews/chartli/2026-11-07-svg-validation.md",
        "data/results/chartli/2026-11-07-svg-oracle.json",
        "Five intentionally invalid fixtures fail; not browser rendering, numeric semantics or target benefit."),
    "htn-orchestrate": (
        "43 pinned upstream targeted tests plus 30 synthetic static DAG checks and 20 surrogate resumes.",
        "reviews/htn-orchestrate/2026-11-08-paired-audit-followup.md",
        "data/results/htn-orchestrate/2026-11-07-paired-audit.json",
        "No end-to-end HTN superiority proof; no held-out target project A/B."),
    "rea": (
        "48 independent synthetic PE32/PE32+ header/layout and rejection cases.",
        "reviews/reverse-engineer-anything/2026-11-05-pe-layout.md",
        "data/results/reverse-engineer-anything/2026-11-05.json",
        "No CLR-loadability, CIL reconstruction, arbitrary binary safety or target benefit."),
    "simurg": (
        "Cross-process source hash/sketch/SimHash stability with 4 process seeds and independent numeric oracles.",
        "reviews/simurg/2026-11-07-hash-stability.md",
        "data/results/simurg/2026-11-07-hash-stability.json",
        "Known AUROC ties and calibration/false-alarm issues remain unresolved for deployment."),
    "youtube-skills": (
        "Pinned Markdown package, external transcript provider boundary and secret bootstrap verified by independent source oracle.",
        "reviews/youtube-skills/2026-11-07-provider-boundary.md",
        "data/results/youtube-skills/2026-11-07-provider-boundary-oracle.json",
        "Provider API, cost, privacy and quality not tested; no keys or network calls."),
}
SPECIAL = {
    "hyperresearch": "Resolve documented false supported-mechanical citations on frozen hostile holdout; 54 upstream passing tests do not answer this failure.",
    "unreal-agent": "Verify primary transcript or full original engineering source; video landing alone is insufficient.",
    "hyra-2": "Check available engineering article versus unavailable backend/model internals; record the precise source boundary.",
    "warp-skill-doctor": "Recover inspectable original implementation or document actual failed attempts and a concrete unblock condition.",
    "sequential-diagnosis-language-models": "Recheck pinned full paper and retained full-text evidence after source-fetch access failure.",
}
TERMINAL = {"ACCEPT_BOUNDED", "ACCEPT_RESEARCH_ONLY", "NO_FIT", "BLOCKED"}

def read(root, p):
    return json.loads((root / p).read_text(encoding="utf-8"))

def sha(root, p):
    return hashlib.sha256((root / p).read_bytes()).hexdigest()

def validate_bounded(sid, x):
    if sid == "agent-error-dataset":
        assert x["independent_verification"] == "PASS" and x["trials_checked"] == 90
        assert x["negative_controls_blocked"] == 270 and x["false_accepts"] == 0
    elif sid == "agent-risk":
        assert x["status"] == "PASS" and x["scenario_count"] == 200
        assert x["counts"]["targeted_vs_live_harm_mismatches"] == 0
    elif sid == "cera-moa":
        assert x["status"] == "PASS" and x["verified_cases"] == 10000
        assert x["matches_experiment_digest"] is True
    elif sid == "chartli":
        assert x["total"] == 16 and x["well_formed_xml"] == 14
        assert x["finite_numeric_svg"] == 11 and all(x["mutation_checks"].values())
    elif sid == "htn-orchestrate":
        assert x["study_id"] == sid and x["upstream_source"]["sha"]
        assert x["synthetic_dag"]["passes"] == x["synthetic_dag"]["cases"] == 30
        assert x["synthetic_dag"]["resume_idempotence_pass"] == 20
    elif sid == "rea":
        assert x["passed"] == 48 and x["repetitions"] == 3
    elif sid == "simurg":
        assert x["status"] == "PASS_BOUNDED_CROSS_PROCESS_STABILITY"
        assert x["cross_process_checks_passed"] == 4 and len(x["pythonhashseed_cases"]) == 4
        assert x["unkeyed_external_b2sum_checks"] == 10
        assert all(x["negative_controls"].values())
    elif sid == "youtube-skills":
        assert x["independently_pinned_skills"] == 24
        assert x["auth_guide_sha_verified"] == 24 and x["synthetic_mutations_rejected"] == 2
        assert x["network_actions_run"] == 0

def next_gate(sid, full, experiments, missing):
    if sid in SPECIAL:
        return SPECIAL[sid]
    if experiments:
        return "Independently adjudicate recorded experiment scope, oracle, controls and author-vs-local distinction before terminal decision."
    if not full:
        return "Inspect complete pinned original article/code, methodological limitations and alternatives before a justified disposition."
    if missing:
        return "Use full review to adjudicate research-only value or bounded test; assess remaining project profiles without treating missing assessments as NO_FIT."
    return "Manually adjudicate review methods, limits and independent checks; choose supported research-only, bounded, or evidenced blocker."

def generate(root):
    x = read(root, "catalog/entities.json")
    old = read(root, "data/results/research-portfolio/2026-11-07-evidence-coverage-83.json")
    assert len(x["studies"]) == old["card_count"] == 83 and len(x["projects"]) == 45
    assert old["documentary_review_provenance_found"] == 83
    studies = {s["id"]: s for s in x["studies"]}
    reviews = {r["id"]: r for r in x["reviews"]}
    by_exp = defaultdict(list)
    for e in x["experiments"]:
        for sid in e["study_ids"]:
            by_exp[sid].append(e)
    assessments = {a["id"]: a for a in x["assessments"]}
    cur = defaultdict(dict)
    for a in x["current_assessments"]:
        assert a["project_id"] not in cur[a["study_id"]]
        cur[a["study_id"]][a["project_id"]] = assessments[a["assessment_id"]]
    provenance = {p["card"]: p for p in old["items"]}
    projects = {p["id"] for p in x["projects"]}
    output = []
    assert set(BOUNDED).issubset(studies)
    for sid, study in sorted(studies.items()):
        p = study["card"]
        assert p in provenance
        document = provenance[p]["review_provenance"]
        current = reviews[study["current_review_id"]]
        assert sid in current["study_ids"]
        previous = [r for r in x["reviews"] if sid in r["study_ids"]]
        full = sorted({r["document"] for r in previous if r["source_coverage"] in (
            "FULL_TEXT_REVIEWED", "FULL_PRIMARY_ENGINEERING_ARTICLE_REVIEWED",
            "FULL_PRIMARY_TECHNICAL_DISCLOSURE_READ")})
        explicit = cur[sid]
        missing = sorted(projects.difference(explicit))
        row = {
            "study_id": sid, "card": p, "card_sha256": sha(root, p),
            "kind": study["kind"], "primary_url": study["primary_url"],
            "review_document": document, "review_sha256": sha(root, document),
            "current_catalog_review": current["document"],
            "current_catalog_review_sha256": sha(root, current["document"]),
            "current_source_coverage_claim": current["source_coverage"],
            "previous_full_primary_review_documents": full,
            "existing_registered_experiments": [
                {"id": e["id"], "result": e["result"], "scope": e["scope"],
                 "artifacts": e["artifacts"]} for e in by_exp[sid]],
            "explicit_project_assessments": len(explicit),
            "project_assessment_decisions": dict(sorted(Counter(
                a["decision"] for a in explicit.values()).items())),
            "unassessed_project_count": len(missing),
            "unassessed_project_ids": missing,
            "author_results_independently_replicated_by_this_ledger": False,
            "production_approved": False,
        }
        if sid in BOUNDED:
            scope, reviewpath, evidencepath, limit = BOUNDED[sid]
            validate_bounded(sid, read(root, evidencepath))
            row.update({
                "closure_status": "ACCEPT_BOUNDED", "verified_scope": scope,
                "limits": limit, "evidence": [
                    {"path": f, "sha256": sha(root, f)}
                    for f in (reviewpath, evidencepath)],
                "deployment_gate": "Separate target-source seam, owned A/B, oracle, latency/cost/safety and explicit human approval.",
            })
        else:
            row.update({
                "closure_status": "OPEN_EVIDENCE_ADJUDICATION", "verified_scope": None,
                "limits": "Document provenance does not prove scientific replication or current project fit.",
                "evidence": [],
                "next_evidence_gate": next_gate(sid, bool(full), by_exp[sid], missing),
            })
        output.append(row)
    c = Counter(row["closure_status"] for row in output)
    summary = {"total": 83, "terminal": sum(c[k] for k in TERMINAL),
               "open": c["OPEN_EVIDENCE_ADJUDICATION"],
               "by_status": dict(sorted(c.items())),
               "explicit_project_pairs": sum(v["explicit_project_assessments"] for v in output),
               "unassessed_project_pairs": sum(v["unassessed_project_count"] for v in output)}
    assert summary["terminal"] + summary["open"] == 83
    assert summary["explicit_project_pairs"] + summary["unassessed_project_pairs"] == 3735
    return {
        "date": "2026-11-09", "basis_repo": "Artemedi/research-hub",
        "basis_entities_sha256": sha(root, "catalog/entities.json"),
        "prior_provenance_sha256": sha(root, "data/results/research-portfolio/2026-11-07-evidence-coverage-83.json"),
        "study_status_note": "Terminal acceptance is manually bounded, never inferred from upstream PASS or the existence of a document.",
        "project_status_note": "Unassessed is not NO_FIT; assessments refer to recorded project snapshots, not automatically current HEAD.",
        "summary": summary, "studies": output}

def report(v):
    summ = v["summary"]
    lines = [
        "# Evidence-based closure ledger — first adjudication pass (83 cards)", "",
        "Date: 2026-11-09. This is a finite evidence register, not 83 new reports.",
        "Only existing source, code, negative controls and oracles were inspected; "
        "no model run, production action or source-card rewrite occurred.", "",
        "Terminal: {}/83. Open: {}/83.".format(summ["terminal"], summ["open"]), "",
        "[Machine-readable 83-card ledger](../../data/results/research-portfolio/2026-11-09-closure-ledger.json) "
        "contains per-card SHA, review, full-source pointers, experiment records, project assessment coverage "
        "and precise unresolved gates. [Reproduction script](../../experiments/research-portfolio/2026-11-09-closure-ledger.py).",
        "", "## Terminal bounded results", "",
        "| Study | Verified property (not paper replication) | Existing dated evidence |",
        "| --- | --- | --- |",
    ]
    for r in v["studies"]:
        if r["closure_status"] != "ACCEPT_BOUNDED":
            continue
        f = r["evidence"][0]["path"]
        lines.append("| {} | {} | [review](../../{}) |".format(r["study_id"], r["verified_scope"], f))
    lines += [
        "", "All eight ACCEPT_BOUNDED records refer only to explicitly measured narrow properties. "
        "They do not endorse author-reported generalization, target-project benefit or deployment.",
        "", "## Unresolved evidence, not false closure", "",
        "{} source cards remain OPEN_EVIDENCE_ADJUDICATION, not REWORK-by-default, "
        "BLOCKED-without-a-real-obstacle or speculative ACCEPT.".format(summ["open"]),
        "Existing canonical current assessments cover {}/3735 research–project pairs; "
        "{} pairs have no explicit decision. They are not inferred NO_FIT.".format(
            summ["explicit_project_pairs"], summ["unassessed_project_pairs"]),
        "The previous 83/83 coverage report established review-document provenance, not "
        "scientific validity; this ledger explicitly preserves that boundary.", "",
        "## Next finite gates", "",
        "1. hyperresearch: independent adverse citation oracle; do not rerun unrelated 54 upstream passing tests.",
        "2. Source availability: warp-skill-doctor, hyra-2, unreal-agent, sequential-diagnosis-language-models. "
        "A BLOCKED result requires failed access attempts and an unblock criterion, not merely no local source.",
        "3. Remaining full-primary cases: decide ACCEPT_RESEARCH_ONLY only after independent methodological "
        "review; otherwise use a bounded oracle or documented obstacle. The linked existing experiments "
        "must be adjudicated before any new execution.",
        "", "No original study cards, generated source bodies, target project repositories, "
        "private registry files or production resources were modified.", "",
    ]
    return "\n".join(lines)

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = a.parse_args()
    root = args.root.resolve()
    res = generate(root)
    out = root / "data/results/research-portfolio/2026-11-09-closure-ledger.json"
    md = root / "portfolio/2026-11-09/closure-ledger.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    md.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md.write_text(report(res), encoding="utf-8")
    print(json.dumps(res["summary"], indent=2))

if __name__ == "__main__":
    main()
