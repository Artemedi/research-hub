"""Compare similarity search and typed directed search on projected RCA graphs."""

import argparse
from collections import Counter
import hashlib
import importlib
import importlib.util
import json
from math import log
from pathlib import Path
import subprocess
import sys

import networkx as nx
import numpy as np


LKG_PIN = "58fce402c7d15a3f5abcc8d0b1e920c1be5071b5"
RCA_PIN = "13fa0c910c75d9e3b79c758bcba473a6406e008c"
LKG_HASH = "a4faedce7752c4f192d7bc06d727e1fe272da90986fc6fc2e9055c865f6f8f75"
RCA_HASHES = {
    "graph.py": "b0a22615ecf4c34d1ecef35da85d76596ea5c7add252d4fbdfe983a6d6b2e171",
    "state.py": "6e20881609494d10391187237befc00d236eeca77556b6957a3127ab5aeb7544",
    "orchestrator.py": "c677e4b79264c1fa5192f4739f4b32aa0267da56b58ffea1a8347705679d100d",
}
SUPPORT_RELATIONS = {"cited_as_support", "proposed_cause", "proposed_contribution"}
SCENARIOS = ("direct", "reverse_only", "contradiction_only", "bridge_only", "bridge_with_alternative")
CASES_PER_SCENARIO = 12


def verify_file(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Source digest mismatch: {path.name}")


def load_sources(lkg, rca):
    def git(*args):
        return subprocess.check_output(["git", "-C", rca, *args], text=True).strip()

    if git("rev-parse", "HEAD") != RCA_PIN or git("status", "--porcelain", "-uno"):
        raise ValueError("Expected a clean checkout at the pinned sequential-rca revision")
    for path, expected in RCA_HASHES.items():
        verify_file(rca / "src/sequential_rca" / path, expected)
    verify_file(lkg, LKG_HASH)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("pinned_lkg_graph", lkg)
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    sys.path.insert(0, str(rca / "src"))
    state = importlib.import_module("sequential_rca.state")
    validator = importlib.import_module("sequential_rca.orchestrator")
    graph = importlib.import_module("sequential_rca.graph")
    return upstream.strongest_path, state, validator, graph


def projected_case(state, validator, graph, scenario, seed):
    source_id, other_id = f"fixture-{seed}-primary", f"fixture-{seed}-secondary"
    source, other = f"evidence:{source_id}", f"evidence:{other_id}"
    payload = {
        "schema_version": 1, "id": f"graph-fixture-{seed}", "engine": "postgresql",
        "engine_version": "fixture", "brief": "Synthetic evidence attribution.",
        "cutoff": "2026-01-01T00:01:00Z", "actions": [],
        "metadata": {"kind": "synthetic", "family": "edge-direction", "split": "test", "provenance": "authored"},
        "initial": [
            {"id": evidence, "captured_at": "2026-01-01T00:00:00Z",
             "source": "authored", "scope": "fixture", "facts": {"observation": index}}
            for index, evidence in enumerate((source_id, other_id))
        ],
    }
    case = state.Case.parse(payload)
    current = state.State(list(case.initial))
    hypotheses = [
        {"id": "candidate", "mechanism": "Hypothesis", "rationale": "Authored scenario.",
         "support": [], "contradictions": []},
        {"id": "control", "mechanism": "Alternative", "rationale": "Unused control.",
         "support": [], "contradictions": []},
    ]
    if scenario == "contradiction_only":
        hypotheses[0]["contradictions"] = [source_id]
    elif scenario.startswith("bridge"):
        hypotheses[0]["support"] = [source_id, other_id]
    events = [{"kind": "hypotheses", "seq": 1, "payload": {
        "hypotheses": validator.validate_hypotheses({"hypotheses": hypotheses}, current),
    }}]
    roots = [source_id]
    if scenario == "bridge_only":
        roots = [other_id]
    elif scenario == "bridge_with_alternative":
        roots = [source_id, other_id]
    elif scenario == "contradiction_only":
        roots = []
    current.final = validator.validate_final({
        "status": "DIAGNOSED" if roots else "INSUFFICIENT_EVIDENCE",
        "root_causes": [{"mechanism": "Fixture cause", "summary": "Authored claim.", "evidence_ids": [identity]}
                        for identity in roots],
        "contributing_factors": [], "alternatives": [], "recommendations": [],
        "limits": ["Synthetic attribution only."], "confidence": "low",
    }, current)
    view = graph.evidence_graph(case, current, events)
    assert view["interpretation"] == "UNVERIFIED_ATTRIBUTIONS_REQUIRE_DBA_REVIEW"
    return view, source, other


def directed_path(weighted, start, end, typed):
    graph = nx.DiGraph()
    graph.add_nodes_from(node["id"] for node in weighted["nodes"])
    for edge in weighted["edges"]:
        if not typed or edge["relation"] in SUPPORT_RELATIONS:
            graph.add_edge(edge["from"], edge["to"], cost=-log(edge["value"]))
    try:
        return nx.dijkstra_path(graph, start, end, weight="cost")
    except nx.NetworkXNoPath:
        return None


def replay(strongest, state, validator, graph, repeat):
    results = {}
    for scenario in SCENARIOS:
        counts = Counter(dict.fromkeys(
            ("cases", "stock_matches_oracle", "stock_reverse_edges", "stock_contradiction_paths",
             "directed_matches_oracle", "typed_matches_oracle", "typed_no_path"), 0,
        ))
        for index in range(CASES_PER_SCENARIO):
            view, source, other = projected_case(state, validator, graph, scenario, repeat * 12 + index)
            weighted = {
                "nodes": view["nodes"],
                "edges": [
                    {"from": edge["source"], "to": edge["target"], "relation": edge["relation"],
                     "value": 0.64 if scenario == "bridge_with_alternative"
                     and "root:0" in (edge["source"], edge["target"]) else 0.96}
                    for edge in view["edges"]
                ],
            }
            hypothesis = "hypothesis:1:candidate"
            endpoints = {
                "reverse_only": ("root:0", source),
                "contradiction_only": (source, hypothesis),
            }
            start, end = endpoints.get(scenario, (source, "incident"))
            oracle = [source, "root:0", "incident"] if scenario in ("direct", "bridge_with_alternative") else None
            expected_stock = {
                "direct": oracle, "reverse_only": ["root:0", source],
                "contradiction_only": [source, hypothesis],
                "bridge_only": [source, hypothesis, other, "root:0", "incident"],
                "bridge_with_alternative": [source, hypothesis, other, "root:1", "incident"],
            }[scenario]
            stock, _, _ = strongest(weighted, start, end)
            directional = directed_path(weighted, start, end, typed=False)
            filtered = directed_path(weighted, start, end, typed=True)
            assert stock == expected_stock
            assert directional == ([source, hypothesis] if scenario == "contradiction_only" else oracle)
            assert filtered == oracle
            actual_edges = {(edge["from"], edge["to"]): edge["relation"] for edge in weighted["edges"]}
            pairs = list(zip(stock, stock[1:]))
            counts["cases"] += 1
            counts["stock_matches_oracle"] += stock == oracle
            counts["stock_reverse_edges"] += any(pair not in actual_edges for pair in pairs)
            counts["stock_contradiction_paths"] += any(actual_edges.get(pair) == "cited_as_contradiction" for pair in pairs)
            counts["directed_matches_oracle"] += directional == oracle
            counts["typed_matches_oracle"] += filtered == oracle
            counts["typed_no_path"] += filtered is None
        results[scenario] = dict(counts)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lkg_graph", type=Path)
    parser.add_argument("rca_checkout", type=Path)
    args = parser.parse_args()
    sources = load_sources(args.lkg_graph.resolve(), args.rca_checkout.resolve())
    counts = replay(*sources, 0)
    assert replay(*sources, 1) == counts
    assert replay(*sources, 2) == counts
    print(json.dumps({
        "lkg_revision": LKG_PIN, "lkg_source_sha256": LKG_HASH,
        "rca_revision": RCA_PIN, "rca_source_sha256": RCA_HASHES,
        "networkx": nx.__version__, "numpy": np.__version__,
        "cases_per_scenario": CASES_PER_SCENARIO, "repeats": 3, "model_calls": 0, "counts": counts,
    }, indent=2))


if __name__ == "__main__":
    main()
