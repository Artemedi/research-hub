#!/usr/bin/env python3
"""Independent audit of published paired ablation table and synthetic DAG safety.
No model, private data, original implementation, or external network is used.
"""
import itertools
import json
import math
import random
from pathlib import Path

N = 200
PAIRED = {
    'upfront_decomposition': (176, 8, 5, 11),
    'single_agent_leaf': (172, 12, 7, 9),
    'no_rebuilding': (175, 9, 4, 12),
}


def exact_p(b, c):
    m = b + c
    return min(1.0, 2.0 * sum(math.comb(m, k) for k in range(min(b, c) + 1)) / (2 ** m))


def audit_pair(both, better, worse, neither):
    assert both + better + worse + neither == N
    assert both + better == 184
    return {
        'both_correct': both, 'htn_only_correct': better,
        'ablation_only_correct': worse, 'both_incorrect': neither,
        'difference_percentage_points': 100 * (better - worse) / N,
        'two_sided_exact_mcnemar_p': exact_p(better, worse),
        'n_discordant': better + worse,
        'paper_full_correct': both + better,
        'paper_variant_correct': both + worse,
        'is_p_less_0_05': exact_p(better, worse) < 0.05,
    }


def valid_topological_order(nodes, deps):
    """Brute-force oracle independent from the scheduler's Kahn traversal."""
    for perm in itertools.permutations(nodes):
        pos = {node: i for i, node in enumerate(perm)}
        if all(pos[dep] < pos[node] for node in nodes for dep in deps[node]):
            return True
    return False


def scheduler(nodes, deps, supported, completed=()):
    done = list(completed)
    assert len(set(done)) == len(done)
    assert set(done) <= set(nodes)
    order = []
    while len(done) < len(nodes):
        ready = [n for n in nodes if n not in done and set(deps[n]) <= set(done)]
        if not ready:
            return {'status': 'BLOCKED_CYCLE_OR_DEPENDENCY', 'order': order, 'completed': done}
        node = ready[0]
        if not supported[node]:
            return {'status': 'NEEDS_EVIDENCE', 'order': order, 'completed': done}
        order.append(node)
        done.append(node)
    return {'status': 'PASS', 'order': order, 'completed': done}


def cases():
    rng = random.Random(20261107)
    for i in range(20):
        n = 2 + (i % 3)
        nodes = tuple(range(n))
        deps = {j: tuple(k for k in range(j) if rng.random() < 0.4) for j in nodes}
        yield f'valid_{i}', nodes, deps, {j: True for j in nodes}, 'PASS'
    for i in range(5):
        nodes = (0, 1, 2)
        yield f'cycle_{i}', nodes, {0: (2,), 1: (0,), 2: (1,)}, {0: True, 1: True, 2: True}, 'BLOCKED_CYCLE_OR_DEPENDENCY'
    for i in range(5):
        nodes = (0, 1, 2)
        yield f'missing_{i}', nodes, {0: (), 1: (0,), 2: (1,)}, {0: True, 1: False, 2: True}, 'NEEDS_EVIDENCE'


def main():
    results = {name: audit_pair(*counts) for name, counts in PAIRED.items()}
    trials = []
    recovery_pass = 0
    for name, nodes, deps, supported, expected in cases():
        r = scheduler(nodes, deps, supported)
        oracle_can_complete = valid_topological_order(nodes, deps) and all(supported.values())
        assert (r['status'] == 'PASS') == oracle_can_complete
        assert r['status'] == expected, (name, r)
        assert len(r['order']) == len(set(r['order']))
        done = set()
        for step in r['order']:
            assert set(deps[step]) <= done
            done.add(step)
        if expected == 'PASS':
            first = r['order'][0]
            resumed = scheduler(nodes, deps, supported, (first,))
            assert resumed['status'] == 'PASS'
            assert first not in resumed['order']
            assert len(resumed['completed']) == len(nodes)
            recovery_pass += 1
        trials.append({'case': name, 'expected': expected, 'observed': r['status'], 'passed': True})
    report = {
        'study_id': 'htn-orchestrate',
        'date': '2026-11-07',
        'paper_source': 'https://arxiv.org/abs/2610.22195',
        'prior_pdf_v1_hash_from_hub': '781ff3cd5f16673d7f7b9f8a2cb6a8381d6eb5e1332c6e55bed2dcbbd300b452',
        'upstream_source': {
            'repo': 'ycdeng-ntu/htn-orchestrate',
            'sha': '0bccf18d813298e5c2a33961dbf56b907bd8b133',
            'inspected': [
                'workflows/dynamic_htn_informed_research/htn/task_tree.py:68-90',
                'workflows/dynamic_htn_informed_research/htn/task_tree.py:142-158',
                'workflows/dynamic_htn_informed_research/htn/task_node.py:15-55',
                'workflows/dynamic_htn_informed_research/htn/epoch.py:1-150',
                'tests/workflows/dynamic_htn_informed_research/test_epoch_recovery.py:59-150',
                'tests/workflows/dynamic_htn_informed_research/test_result_informed_planning.py:1-150',
            ],
            'upstream_tests_run': False,
            'boundary': 'Static code/test inspection; not upstream test execution, not runtime coverage or performance benchmark',
        },
        'project_fit': {
            'project_registry_sha': '838b86a28fcaa3440eeddbe147b6188e0d177963',
            'shortlist_from_prior_45_profile_matrix': ['dsh-runtime', 'hermes-akuz-agents'],
            'status': 'PROFILE_MATCH_NEEDS_CURRENT_SOURCE_SEAM_AND_HELD_OUT_AB',
            'new_backlinks': 0,
        },
        'table_basis': 'Appendix C.3 Table 11, 200 paired BrowseComp tasks, one run per variant',
        'method': 'exact conditional McNemar (two-sided binomial on discordant tasks); independent brute-force topological oracle',
        'paired_results': results,
        'synthetic_dag': {
            'cases': len(trials), 'passes': sum(x['passed'] for x in trials),
            'valid': 20, 'cycles': 5, 'missing_evidence': 5,
            'resume_idempotence_cases': 20, 'resume_idempotence_pass': recovery_pass,
            'scope': 'Independent static-DAG surrogate only; NOT HTN-Orchestrate source code, LLM, or paper benchmark',
            'case_results': trials,
        },
        'verdict': 'NO_SIGNIFICANT_PAIRED_ABLATION_GAIN_AT_0_05_IN_PUBLISHED_200_SUBSET; HTN_TARGET_BENEFIT_NOT_REPRODUCED',
        'limitations': [
            'Statistical test reuses author-reported paired counts; does not independently reproduce outcomes',
            'No multiple-testing correction required for the negative nominal p<0.05 finding; no claim of equality',
            '200-question ablation subset not full 1266-question benchmark',
            'Synthetic cases test a simpler dependency-gated DAG only; do not imply HTN is ineffective in dynamic research',
            'No local target repository benchmark, model calls, latency, tokens or cost measured',
        ],
    }
    out = Path(__file__).resolve().parents[2] / 'data/results/htn-orchestrate/2026-11-07-paired-audit.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'paired_results': results, 'synthetic_pass': len(trials), 'recovery_pass': recovery_pass, 'evidence': str(out)}, indent=2))


if __name__ == '__main__':
    main()
