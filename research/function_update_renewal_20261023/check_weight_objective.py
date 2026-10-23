"""Exact finite Bayesian check; no empirical TDAL replication or new algorithm."""
from fractions import Fraction as F
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/function_update_renewal'
atoms = [(dict(A=a, B=b, C=b), (F(9, 10) if a else F(1, 10)) * F(1, 2))
         for a, b in itertools.product([0, 1], repeat=2)]
assert sum(p for _, p in atoms) == 1
names = ['A', 'B', 'C']
prior = {x: sum(p * z[x] for z, p in atoms) for x in names}
rows = []
for action in names:
    remaining = [x for x in names if x != action]
    immediate = prior[action]
    continuation, weighted_continuation = F(0), 0.
    branches = []
    for outcome in [0, 1]:
        mass = sum(p for z, p in atoms if z[action] == outcome)
        posterior = {x: sum(p * z[x] for z, p in atoms if z[action] == outcome) / mass for x in remaining}
        next_action = max(remaining, key=lambda x: posterior[x])
        next_value = posterior[next_action]
        h2 = [1 - math.sqrt(float(prior[x] * posterior[x])) - math.sqrt(float((1-prior[x])*(1-posterior[x]))) for x in remaining]
        assert min(h2) >= -1e-14
        weight = math.sqrt(max(sum(h2)/len(h2), 0.))
        continuation += mass * next_value
        weighted_continuation += float(mass * next_value) * weight
        branches.append({'outcome': outcome, 'probability': float(mass), 'next_action': next_action,
                         'next_hit_probability': float(next_value), 'weight': weight})
    rows.append({'first_action': action, 'expected_hits': float(immediate + continuation),
                 'weighted_objective': float(immediate) + weighted_continuation, 'branches': branches})
best_true = max(rows, key=lambda r: r['expected_hits'])
best_weighted = max(rows, key=lambda r: r['weighted_objective'])
gap = best_true['expected_hits'] - best_weighted['expected_hits']
assert best_true['first_action'] in ['B', 'C'] and best_weighted['first_action'] == 'A'
assert abs(gap - .05) < 1e-12
assert abs(best_true['expected_hits'] - 1.45) < 1e-12
assert abs(best_weighted['expected_hits'] - 1.4) < 1e-12
result = {'status': 'EXACT_SURROGATE_OBJECTIVE_DIVERGENCE', 'finite_prior_atoms': len(atoms),
          'rows': rows, 'true_optimal_first': best_true['first_action'], 'weighted_optimal_first': best_weighted['first_action'],
          'true_expected_hit_gap': gap, 'biological_experiments': 0,
          'scope': 'Exact stated prior; not an empirical TDAL failure, universal result, novelty or RSI evidence'}
(OUT / 'WEIGHT_CHECK.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
