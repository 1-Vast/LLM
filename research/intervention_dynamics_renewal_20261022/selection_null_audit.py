"""Exhaustive finite selection witnesses. No measured data or model fitting."""
from fractions import Fraction
from itertools import combinations, product
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/intervention_dynamics_renewal/mechanism_round2'


def binary_audit(n=4, histories=3):
    masks = range(1 << n)
    feasible = set()
    for types in product((0, 1), repeat=n):
        views = set()
        for mask in masks:
            kept = [i for i in range(n) if (mask >> i) & 1]
            views.add((len(kept), sum(types[i] for i in kept)))
        feasible.update(product(views, repeat=histories))
    views = [(live, response) for live in range(n+1) for response in range(live+1)]
    accepted = set()
    constructive = 0
    for record in product(views, repeat=histories):
        lower = max(z for live, z in record)
        upper = min(z+n-live for live, z in record)
        if lower <= upper:
            accepted.add(record)
            # Choose first K responsive founders; retain Z of these and L-Z others.
            k = lower
            assert all(z <= k and live-z <= n-k for live, z in record)
            constructive += 1
        assert (lower <= upper) == (
            max(z for live, z in record)+max(live-z for live, z in record) <= n)
    assert accepted == feasible
    return {'n': n, 'histories': histories, 'candidate_summaries': len(views)**histories,
            'enumerated_realizable': len(feasible), 'interval_accepted': len(accepted),
            'constructive_checks': constructive, 'exact_set_equality': True,
            'binary_state_constraint_equivalent': True}


def categorical_audit(n=3, categories=3, histories=3):
    feasible = set()
    for types in product(range(categories), repeat=n):
        views = set()
        for mask in range(1 << n):
            views.add(tuple(sum(((mask >> i) & 1) and types[i] == k for i in range(n))
                            for k in range(categories)))
        feasible.update(product(views, repeat=histories))
    views = [q for q in product(range(n+1), repeat=categories) if sum(q) <= n]
    accepted = {record for record in product(views, repeat=histories)
                if sum(max(q[k] for q in record) for k in range(categories)) <= n}
    assert accepted == feasible
    return {'n': n, 'categories': categories, 'histories': histories,
            'candidate_summaries': len(views)**histories,
            'enumerated_realizable': len(feasible), 'summax_accepted': len(accepted),
            'exact_set_equality': True}


def witnesses():
    initial = Fraction(1, 2)
    raw = Fraction(8, 9)
    weighted = 8 * Fraction(1, 8) / 2
    assert weighted == initial and raw != initial
    responder = (1, 1, 0, 0)
    assignments = []
    for arm in combinations(range(4), 2):
        z1 = Fraction(sum(responder[i] for i in arm), 2)
        z0 = Fraction(sum(responder[i] for i in range(4) if i not in arm), 2)
        assignments.append({'treated_founders': arm, 'z1': str(z1), 'z0': str(z0),
                            'raw_interval_disjoint': z1 != z0})
    false_violations = sum(a['raw_interval_disjoint'] for a in assignments)
    assert false_violations == 2 and len(assignments) == 6
    q = [(Fraction(1, 2), 0, 0), (0, Fraction(1, 2), 0), (0, 0, Fraction(1, 2))]
    delta = Fraction(1, 2)
    binary_intersections = [max(v[k] for v in q) <= min(v[k]+delta for v in q)
                            for k in range(3)]
    maxima_sum = sum(max(v[k] for v in q) for k in range(3))
    assert all(binary_intersections) and maxima_sum == Fraction(3, 2)
    return {'birth_bias': {'initial_raw_fraction': str(initial), 'expanded_raw_fraction': str(raw),
                          'both_weighted_masses': str(weighted)},
            'randomized_no_attrition': {'assignments': assignments,
                'raw_point_gate_false_violations': false_violations,
                'total_assignments': len(assignments), 'fraction': str(Fraction(false_violations, 6))},
            'multicategory': {'individual_binary_intersections': binary_intersections,
                'sum_of_category_maxima': str(maxima_sum), 'global_common_distribution': False}}


def main():
    result = {'status': 'PASS_EXACT_LOGIC_ONLY', 'binary': binary_audit(),
        'categorical': categorical_audit(), 'witnesses': witnesses(),
        'biological_evidence': False, 'performance_evidence': False,
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol_sha256': hashlib.sha256((OUT/'LOGIC_PROTOCOL.md').read_bytes()).hexdigest()}
    with (OUT/'LOGIC_RESULT.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'witnesses'}))


if __name__ == '__main__':
    main()
