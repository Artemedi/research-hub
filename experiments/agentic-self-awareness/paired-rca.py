"""Compare refusal, attribution and evidence on authored paired RCA cases."""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

COMMIT = "13fa0c910c75d9e3b79c758bcba473a6406e008c"
CAUSE = "open_transaction_blocking"
NEEDED = ("blocking_chain_verified", "head_transaction_open", "affected_workload_matches")
MISSING = {
    "not_captured": "Collect the blocking chain for the affected workload.",
    "transaction_unknown": "Collect the head transaction state in the same time window.",
    "scope_unmatched": "Collect a blocking chain matched to the affected workload.",
}


def evidence(ident, facts):
    return dict(id=ident, captured_at="2026-01-01T00:00:00Z",
                source="authored fixture", scope="synthetic workload", facts=facts)


def make_case(index, variant):
    observed = {key: True for key in NEEDED}
    observed["sample_number"] = index
    if variant == "not_captured":
        response = "NOT_CAPTURED"
    else:
        if variant == "transaction_unknown":
            observed.pop("head_transaction_open")
        if variant == "scope_unmatched":
            observed["affected_workload_matches"] = False
        response = [evidence("e2", observed)]
    return dict(
        schema_version=1, id=f"fixture-{index:02d}-{variant}",
        engine="postgresql" if index % 2 else "mssql", engine_version="synthetic",
        brief="Identify the cause of this synthetic workload delay if the captured facts support it.",
        cutoff="2026-01-01T00:01:00Z",
        initial=[evidence("e1", {"latency_ms": 101 + index, "sample_number": index})],
        actions=[dict(id="blocking", description="Read the recorded blocking observation",
                      risk="low", cost=1, response=response)],
        metadata=dict(kind="synthetic", family=f"fixture-{index:02d}", split="test",
                      provenance="authored positive and blocked twins"),
    )


def diagnosed(evidence_id):
    return dict(status="DIAGNOSED",
                root_causes=[dict(mechanism=CAUSE, summary="An open transaction blocks this workload.",
                                  evidence_ids=[evidence_id])],
                contributing_factors=[], alternatives=[], confidence="medium",
                limits=["The trigger of the open transaction remains unknown."],
                recommendations=[])


def run_suite(evaluate, verify_report, Runner, Budget, Case, ValidationError, Reply, ModelError):
    class AuthoredReplies:
        def __init__(self, arm):
            self.identity = "authored-" + arm
            self.arm = arm

        def call(self, role, context, timeout):
            assert role == "planner"
            if self.arm == "model_error":
                raise ModelError("Fixture model unavailable")
            if self.arm == "always_abstain":
                output = self.pause("Collect more evidence.")
            elif self.arm == "premature_diagnose":
                output = dict(action_id=None, reason="Premature model claim", final=diagnosed("e1"))
            elif not context["attempts"]:
                output = dict(action_id="blocking", reason="Read the discriminating probe", final=None)
            elif self.arm == "turn_budget":
                raise AssertionError("The budget control must stop before a decision")
            else:
                items = [row for row in context["evidence"] if row["id"] == "e2"]
                if items and all(items[0]["facts"].get(key) is True for key in NEEDED):
                    output = dict(action_id=None, reason="Confirmed by recorded evidence",
                                  final=diagnosed("e2"))
                elif not items:
                    output = self.pause(MISSING["not_captured"])
                elif "head_transaction_open" not in items[0]["facts"]:
                    output = self.pause(MISSING["transaction_unknown"])
                else:
                    output = self.pause(MISSING["scope_unmatched"])
            return Reply(output, spend_basis="not-applicable")

        @staticmethod
        def pause(request):
            final = dict(status="INSUFFICIENT_EVIDENCE", root_causes=[], contributing_factors=[],
                         alternatives=[], confidence="low", limits=["Required fact missing."],
                         recommendations=[request])
            return dict(action_id=None, reason="Pause for evidence", final=final)

    aggregates = {}
    reasons = Counter()
    cases = []
    mutation_rejections = 0
    for index in range(1, 21):
        blocked_variant = tuple(MISSING)[(index - 1) % len(MISSING)]
        feasible_input = make_case(index, "feasible")
        blocked_input = make_case(index, blocked_variant)
        positive, blocked = [Case.parse(raw) for raw in (feasible_input, blocked_input)]
        assert positive.snapshot_hash != blocked.snapshot_hash
        assert {k: v for k, v in positive.brief_context().items() if k != "id"} == {
            k: v for k, v in blocked.brief_context().items() if k != "id"
        }
        reasons[blocked_variant] += 1
        for case, feasible in ((positive, True), (blocked, False)):
            group = "feasible" if feasible else "blocked"
            expected = dict(
                schema_version=1, case_id=case.id, snapshot_hash=case.snapshot_hash,
                expected_status="DIAGNOSED" if feasible else "INSUFFICIENT_EVIDENCE",
                root_causes=[CAUSE] if feasible else [], contributing_factors=[],
                adjudication=dict(status="unreviewed", reviewer="authored synthetic oracle"),
                notes="Independent expected labels for the authored twin only.",
            )
            row = dict(case_id=case.id, group=group, snapshot_hash=case.snapshot_hash, arms={})
            for arm in ("evidence_first", "always_abstain", "premature_diagnose",
                        "turn_budget", "model_error"):
                budget = Budget(max_turns=1 if arm == "turn_budget" else 3)
                report = Runner(case, AuthoredReplies(arm), budget=budget, strategy="A2").run()
                score = evaluate(case, report, expected)
                assert score["quality_eligible"] is False
                final = report["final"]
                by_model = report["stop_reason"] == "MODEL_STOP" and any(
                    event["kind"] == "model"
                    and event["payload"]["output"].get("final") == final
                    for event in report["events"]
                )
                if feasible:
                    strict = by_model and score["status_match"] and score["root_label_match"] and (
                        final["root_causes"][0]["evidence_ids"] == ["e2"]
                    )
                else:
                    strict = by_model and score["status_match"] and bool(report["attempts"]) and (
                        final["recommendations"] == [MISSING[blocked_variant]]
                    )
                facts = dict(
                    status_match=score["status_match"], root_label_match=score["root_label_match"],
                    abstained=score["abstained"], model_authored=by_model, strict_match=bool(strict),
                    stop_reason=report["stop_reason"], calls=score["metrics"]["calls"],
                )
                row["arms"][arm] = facts
                counts = aggregates.setdefault(arm, {}).setdefault(group, Counter())
                counts["cases"] += 1
                for flag in ("status_match", "root_label_match", "abstained",
                             "model_authored", "strict_match"):
                    counts[flag] += int(facts[flag])
                if arm == "evidence_first":
                    altered = deepcopy(report)
                    altered["evidence"].append({"id": "fabricated"})
                    try:
                        verify_report(case, altered)
                    except ValidationError:
                        mutation_rejections += 1
                    else:
                        raise AssertionError("Replay accepted an undeclared observation.")
            cases.append(row)

    assert mutation_rejections == 40
    assert all(aggregates["evidence_first"][group]["strict_match"] == 20
               for group in ("feasible", "blocked"))
    assert aggregates["always_abstain"]["feasible"]["abstained"] == 20
    assert aggregates["premature_diagnose"]["feasible"]["root_label_match"] == 20
    assert aggregates["premature_diagnose"]["feasible"]["strict_match"] == 0
    assert aggregates["turn_budget"]["blocked"]["status_match"] == 20
    assert aggregates["turn_budget"]["blocked"]["model_authored"] == 0
    assert aggregates["model_error"]["blocked"]["status_match"] == 0
    return dict(pair_count=20, blocked_variants=dict(reasons), aggregates=aggregates,
                fabricated_observations_rejected=mutation_rejections, cases=cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()

    def git(*items):
        return subprocess.check_output(["git", "-C", str(source), *items], text=True).strip()

    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Use a clean sequential-rca checkout at " + COMMIT)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    from sequential_rca.evaluate import evaluate, verify_report
    from sequential_rca.models import ModelError, Reply
    from sequential_rca.orchestrator import Runner
    from sequential_rca.state import Budget, Case, ValidationError

    functions = (evaluate, verify_report, Runner, Budget, Case, ValidationError, Reply, ModelError)
    first = run_suite(*functions)
    assert run_suite(*functions) == first
    print(json.dumps(dict(target_commit=COMMIT, python=sys.version.split()[0],
                          repeats=2, model_requests=0, **first), indent=2))


if __name__ == "__main__":
    main()
