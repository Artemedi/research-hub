"""Replay an archived fireperf receipt through the sequential-rca evidence contract."""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys


REVISION = "13fa0c910c75d9e3b79c758bcba473a6406e008c"
RECEIPT = Path(__file__).resolve().parents[2] / "data/results/ipfire-fireperf/2026-11-04.json"
RECEIPT_SHA256 = "e8c0456e058ae0fcb1e989b5615665c5fa0927a8c1288a80ebced2cb7e093359"
SOURCE_HASHES = {
    "state.py": "6e20881609494d10391187237befc00d236eeca77556b6957a3127ab5aeb7544",
    "graph.py": "b0a22615ecf4c34d1ecef35da85d76596ea5c7add252d4fbdfe983a6d6b2e171",
    "orchestrator.py": "c677e4b79264c1fa5192f4739f4b32aa0267da56b58ffea1a8347705679d100d",
}
SCOPE = "isolated-loopback"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_target(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", root, *args], text=True).strip()

    if git("rev-parse", "HEAD") != REVISION or git("status", "--porcelain", "-uno"):
        raise ValueError("Expected a clean checkout at the pinned sequential-rca revision")
    package = root / "src/sequential_rca"
    for file, digest in SOURCE_HASHES.items():
        if sha256((package / file).read_bytes()) != digest:
            raise ValueError(f"Source digest mismatch: {file}")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(package.parent))
    return tuple(importlib.import_module(f"sequential_rca.{name}")
                 for name in ("state", "orchestrator", "graph"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expect_integer(value, expected):
    require(type(value) is int and value == expected, "Invalid or inconsistent counter")


def evidence_rows(receipt):
    require(receipt["version"] == "fireperf 0.3.0" and receipt["status"] == "PASS", "Unexpected receipt")
    require(receipt["isolation_guard"] == {"loopback": "127.0.0.1", "no_default_ipv4_route": True}
            and receipt["isolation_guard"]["no_default_ipv4_route"] is True
            and receipt["network"] == "rootless podman --network=none, 127.0.0.1 only", "Unverified scope")
    require(isinstance(receipt["limitations"], list) and receipt["limitations"]
            and all(isinstance(item, str) and item.strip() for item in receipt["limitations"]), "Missing limitations")
    runs = receipt["runs"]
    expect_integer(receipt["cases"], 12)
    expect_integer(len(runs), receipt["cases"])
    expect_integer(receipt["connections_per_case"], 20)
    expect_integer(receipt["asserted_total_connections"], len(runs) * 20)
    seen = set()
    rows = []

    def observation(identity, fields):
        return {
            "id": identity, "captured_at": None,
            "source": f"archived-fireperf-0.3.0 sha256:{RECEIPT_SHA256}", "scope": SCOPE,
            "facts": {**fields, "limitations": receipt["limitations"]},
        }

    for run in runs:
        backend = run["backend_requested"]
        mode = run["mode"]
        trial = run["trial"]
        require(backend in ("epoll", "auto") and run["backend_used"] == "epoll"
                and mode in ("close", "exchange") and type(trial) is int and trial in range(3), "Unexpected trial")
        identity = (backend, mode, trial)
        require(identity not in seen, "Duplicate trial")
        seen.add(identity)
        for counter in ("attempted", "new", "total"):
            expect_integer(run["connections"][counter], 20)
        for counter in ("failed", "lost", "resets"):
            expect_integer(run["connections"][counter], 0)
        expect_integer(run["schedule"]["skipped"], 0)
        expect_integer(run["handshake"]["count"], 20)
        if mode == "exchange":
            expect_integer(run["exchanges"], 20)
            expect_integer(run["exchange"]["count"], 20)
            expect_integer(run["sent_bytes"], 20 * 64)
            expect_integer(run["received_bytes"], 20 * 256)
        else:
            require(run["exchanges"] is None and run["exchange"] is None, "Unexpected exchange in close mode")
            expect_integer(run["sent_bytes"], 0)
            expect_integer(run["received_bytes"], 0)
        rows.append(observation(f"run-{backend}-{mode}-{trial}", {
            "record_kind": "trial", "backend_requested": backend, "backend_used": run["backend_used"],
            "mode": mode, "attempted": run["connections"]["attempted"], "new": run["connections"]["new"],
            "failed": run["connections"]["failed"], "sent_bytes": run["sent_bytes"],
            "received_bytes": run["received_bytes"],
        }))

    refusal = receipt["refused_port_negative_control"]
    expect_integer(refusal["attempted"], 1)
    expect_integer(refusal["failed"], 1)
    expect_integer(refusal["returncode"], 1)
    for reason in ("incomplete", "local", "rejected", "timeout"):
        expect_integer(refusal["failure_reasons"][reason], int(reason == "rejected"))
    require(refusal["got_summary"] is True, "Missing refusal summary")
    rows.append(observation("refused-control", {
        "record_kind": "refusal-control", "attempted": refusal["attempted"],
        "failed": refusal["failed"], "rejected": refusal["failure_reasons"]["rejected"],
    }))
    return rows


def parse_case(state, rows):
    return state.Case.parse({
        "schema_version": 2, "temporal_basis": "retrospective_unordered",
        "id": "fireperf-archived-handoff", "engine": "postgresql", "engine_version": "not measured",
        "brief": "Offline fixture for evidence intake. No PostgreSQL server was measured.", "cutoff": None,
        "initial": rows, "actions": [],
        "metadata": {"kind": "historical", "family": "isolated-network-observation",
                     "split": "train", "provenance": RECEIPT_SHA256},
    })


def observation_summary(evidence):
    facts = evidence.facts
    return f"Archived isolated loopback: {facts['new']} of {facts['attempted']} connections opened."


def draft(summary, ids):
    return {
        "status": "DIAGNOSED", "root_causes": [{
            "mechanism": "synthetic observation routing", "summary": summary, "evidence_ids": ids,
        }],
        "contributing_factors": [], "alternatives": [], "confidence": "low",
        "limits": ["The archived measurements cover isolated loopback only."], "recommendations": [],
    }


def abstention():
    return {
        "status": "INSUFFICIENT_EVIDENCE", "root_causes": [], "contributing_factors": [],
        "alternatives": [], "confidence": "low", "recommendations": [],
        "limits": ["The archived measurements do not describe the incident path."],
    }


def guarded_handoff(report, requested_scope, state, target):
    target.validate_final(report, state)
    result = {"final": target.validate_final(abstention(), state), "observation": None}
    claim, = report["root_causes"]
    if requested_scope != SCOPE or len(claim["evidence_ids"]) != 1:
        return result
    item = next(evidence for evidence in state.evidence if evidence.id == claim["evidence_ids"][0])
    if (item.scope == SCOPE and item.facts["record_kind"] == "trial"
            and claim["summary"] == observation_summary(item)):
        # A verified lab observation is an attachment, not a root cause for an incident.
        result["observation"] = item.public()
    return result


def replay(receipt, state, target, graph):
    case = parse_case(state, evidence_rows(receipt))
    current = state.State(list(case.initial))
    assert current.context(case)["evidence"] == [row.public() for row in case.initial]
    assert len(case.initial) == 13 and not case.actions and case.cutoff is None
    assert all(row.captured_at is None and row.scope == SCOPE for row in case.initial)
    assert all(entry["captured_at"] is None for entry in graph.timeline(current))
    assert case.initial[-1].facts["rejected"] == 1
    counts = Counter()
    for item in case.initial[:-1]:
        local = observation_summary(item)
        invented = "The routed incident path and firewall are healthy."
        for label, scope, report in (
            ("local_observation", SCOPE, draft(local, [item.id])),
            ("routed_claim", "routed-incident", draft(invented, [item.id])),
            ("relabeled_routed_claim", SCOPE, draft(invented, [item.id])),
            ("unknown_evidence", SCOPE, draft(local, ["not-in-archive"])),
            ("duplicate_evidence", SCOPE, draft(local, [item.id, item.id])),
        ):
            if label in ("unknown_evidence", "duplicate_evidence"):
                for validate in (lambda: target.validate_final(report, current),
                                 lambda: guarded_handoff(report, scope, current, target)):
                    try:
                        validate()
                    except state.ValidationError:
                        pass
                    else:
                        raise AssertionError(f"{label} was accepted")
                counts[label + "_rejected_by_stock_and_guard"] += 1
                continue

            current.final = target.validate_final(report, current)
            linked = graph.evidence_graph(case, current, [])
            assert {"source": "evidence:" + item.id, "target": "root:0",
                    "relation": "cited_as_support"} in linked["edges"]
            counts[label + "_schema_accepted"] += 1
            handoff = guarded_handoff(report, scope, current, target)
            assert handoff["final"]["status"] == "INSUFFICIENT_EVIDENCE"
            expected = item.public() if label == "local_observation" else None
            assert handoff["observation"] == expected
            counts[label + ("_attached" if expected else "_withheld")] += 1
    return case.snapshot_hash, dict(counts)


def mutated_receipts(receipt):
    for name in ("scope", "missing_limits", "byte_count", "boolean_counter", "duplicate_trial", "refusal_label"):
        changed = deepcopy(receipt)
        if name == "scope":
            changed["isolation_guard"]["no_default_ipv4_route"] = False
        elif name == "missing_limits":
            changed["limitations"] = []
        elif name == "byte_count":
            next(run for run in changed["runs"] if run["mode"] == "exchange")["sent_bytes"] += 1
        elif name == "boolean_counter":
            changed["runs"][0]["connections"]["failed"] = False
        elif name == "duplicate_trial":
            changed["runs"][1]["trial"] = changed["runs"][0]["trial"]
        else:
            changed["refused_port_negative_control"]["failure_reasons"]["rejected"] = 0
        yield name, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    state, target, graph = load_target(parser.parse_args().checkout.resolve())
    data = RECEIPT.read_bytes()
    require(sha256(data) == RECEIPT_SHA256, "Historical receipt digest mismatch")
    receipt = state.parse_json(data.decode("utf-8"))
    rejected = []
    for label, changed in mutated_receipts(receipt):
        try:
            evidence_rows(changed)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError(f"Importer accepted {label}")
    snapshot_hash, counts = replay(receipt, state, target, graph)
    assert replay(receipt, state, target, graph) == (snapshot_hash, counts)
    assert replay(receipt, state, target, graph) == (snapshot_hash, counts)
    print(json.dumps({
        "revision": REVISION, "source_sha256": SOURCE_HASHES, "receipt_sha256": RECEIPT_SHA256,
        "case_snapshot_sha256": snapshot_hash, "imported_trials": len(receipt["runs"]),
        "connections_opened": receipt["asserted_total_connections"], "imported_refusal_controls": 1,
        "retrospective_scope": SCOPE, "capture_time": None, "model_or_network_calls": 0,
        "repeats": 3, "rejected_receipt_mutations": rejected, "counts": counts,
    }, indent=2))


if __name__ == "__main__":
    main()
