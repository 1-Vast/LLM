"""Exact predeclared null calibration and nuisance tests, not a biological fit."""
from fractions import Fraction as F
import itertools
import json
from math import comb, factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_rule_renewal'


def sign(x):
    return (x > 0) - (x < 0)


def tail(m, k):
    return sum((F(comb(m, j), 2 ** m) for j in range(k, m + 1)), F(0))


def run():
    assert not (OUT / 'EXACT_ESG.json').exists()
    results = {}
    for ordered in (False, True):
        edges = list(itertools.permutations(range(6), 2) if ordered else itertools.combinations(range(6), 2))
        accepted, histogram = 0, {}
        for y in itertools.permutations(range(6)):
            k = sum(sign(y[i] - y[j]) == sign(i - j) for i, j in edges)
            histogram[k] = histogram.get(k, 0) + 1
            accepted += int(F(k, len(edges)) >= F(3, 5) and tail(len(edges), k) <= F(1, 20))
        rate = F(accepted, factorial(6))
        assert rate > F(1, 20)
        results['ordered' if ordered else 'unique_unordered'] = {
            'vertices': 6, 'edges': len(edges), 'equally_likely_null_orderings': factorial(6),
            'gate_acceptance': str(rate), 'acceptance_decimal': float(rate),
            'nominal_alpha': '1/20', 'histogram_k': histogram,
            'marginal_edge_probability': '1/2', 'iid_continuous_vertex_null': True}

    nuisance = {}
    for ordered in (False, True):
        edges = list(itertools.permutations(range(4), 2) if ordered else itertools.combinations(range(4), 2))
        rho = [F(i - j) for i, j in edges]
        a = [F(i - j) for i, j in edges]
        k = sum(sign(r) == sign(v) for r, v in zip(rho, a))
        p = tail(len(edges), k)
        statistic = sum(sign(r) * v for r, v in zip(rho, a))
        h = F(1, 100)
        def loss(t):
            return sum(abs(r - t * v) for r, v in zip(rho, a))
        derivative = (loss(h) - loss(-h)) / (2 * h)
        assert derivative == -statistic and p <= F(1, 20) and statistic > 0
        nuisance['ordered' if ordered else 'unique_unordered'] = {
            'true_effect': 0, 'state_main_effect_y_s': 's', 'frozen_base': 0,
            'model_effect': 'phi*s', 'initial_phi': 0, 'gate_p': str(p),
            'accepted': True, 'update_sign': sign(statistic),
            'pairwise_L1_directional_derivative': str(derivative), 'negative_gradient_statistic': str(statistic)}

    payload = {'status': 'EXACT_CHECKS_PASS_LITERAL_JUSTIFICATIONS_FAIL',
               'null_calibration': results, 'state_main_effect_counterexample': nuisance,
               'scope': 'Synthetic exchangeable vertex-noise null and scalar nuisance witness; no biological performance/novelty proof'}
    (OUT / 'EXACT_ESG.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    run()
