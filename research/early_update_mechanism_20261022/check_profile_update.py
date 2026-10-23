"""Compare the proposed profile update with ordinary joint WLS/MAP."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/early_update_mechanism'
target = OUT / 'ROOT_MATH_RESULT.json'
assert not target.exists()
cases = []
for seed in range(801, 806):
    rng = np.random.default_rng(seed)
    nuisance = rng.normal(size=(7, 2))
    factor = rng.normal(size=(7, 7))
    precision = factor.T @ factor + np.eye(7)
    j, residual = rng.normal(size=7), rng.normal(size=7)
    projection = np.eye(7) - nuisance @ np.linalg.solve(nuisance.T @ precision @ nuisance, nuisance.T @ precision)
    information = float(j @ precision @ projection @ j)
    assert information > 0
    design = np.column_stack((-j, nuisance))
    for regularization in (0., .25):
        proposed = -float(j @ precision @ projection @ residual) / (information + regularization)
        penalty = np.diag([regularization, 0., 0.])
        ordinary = np.linalg.solve(design.T @ precision @ design + penalty, design.T @ precision @ residual)[0]
        error = float(abs(proposed - ordinary))
        assert error < 1e-10
        cases.append({'seed': seed, 'lambda': regularization, 'profile_delta': proposed,
                      'ordinary_joint_MAP_delta': float(ordinary), 'absolute_error': error})
    confounded = nuisance[:, 0]
    degenerate_information = float(confounded @ precision @ projection @ confounded)
    assert abs(degenerate_information) < 1e-10
    cases[-1]['confounded_information'] = degenerate_information
true_delta = Fraction(1)
information = Fraction(1)
regularization = Fraction(1)
shrunk = information * true_delta / (information + regularization)
assert shrunk == Fraction(1, 2) and shrunk != true_delta
candidate_s, candidate_a, noise, observation = Fraction(0), Fraction(1, 10), Fraction(1, 10), Fraction(1, 20)
assert abs(observation - candidate_s) <= noise and abs(observation - candidate_a) <= noise
record = {'scope': 'Mathematical only; no biological values or fits',
          'protocol_sha256': hashlib.sha256((OUT / 'ROOT_MATH_PROTOCOL.md').read_bytes()).hexdigest(),
          'ordinary_profile_equivalence_cases': cases,
          'max_equivalence_error': max(row['absolute_error'] for row in cases),
          'noiseless_regularization_counterexample': {'true_delta': str(true_delta), 'lambda': str(regularization),
                                                      'estimate': str(shrunk)},
          'overlapping_noise_intervals': {'S': str(candidate_s), 'A': str(candidate_a),
                                         'noise_bound': str(noise), 'compatible_observation': str(observation)},
          'decision_scope': 'Exact profile operation ordinary; positive lambda biases; rejection needs distinguishability'}
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'equivalence_cases': len(cases), 'max_error': record['max_equivalence_error'],
                  'confounding_cases': 5, 'exact_counterexamples': 2, 'status': 'PASS'}, indent=2))
