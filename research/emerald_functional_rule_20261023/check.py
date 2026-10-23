"""Synthetic scientific invariants; no biological response access."""
import json
from pathlib import Path
import numpy as np
from run import canonical, identities, predict, evaluate, pair_mse, pair_regret, OUT
from export_worker import permitted

rng = np.random.default_rng(5023)
assert canonical("[('B', 1., 'uM'), ('A', .10, 'uM')]") == canonical(
    "[('A', .1, 'uM'), ('B', 1, 'uM')]")
plan = identities()
assert len(plan['conditions']) == 60 and len(set(plan['conditions'])) == 60
assert not permitted([dict(cell_line=plan['reserve'][0], condition=plan['conditions'][0])], plan)
assert not permitted([dict(cell_line=plan['development'][0], condition='unallowed')], plan)
groups = np.array([0, 0, 1])
t = np.array([[0., 2., 6.]])
p = np.zeros_like(t)
assert np.allclose(pair_mse(t, p, groups), [[2., 36.]])
assert pair_mse(t, p, groups).mean() == 19.
assert np.allclose(pair_regret(np.array([[2., 0., 6.]]), p, groups), [[2., 0.]])
x, y, z = rng.normal(size=(12, 5)), rng.normal(size=(12, 3)), rng.normal(size=(2, 5))
assert np.allclose(predict(x, y, z, ('mean', 0)), y.mean(0)[None, :])
# Independent primal solve checks dual implementation, including dimension scaling.
sd = x.std(0)
a, b = (x-x.mean(0))/sd, (z-x.mean(0))/sd
primal = y.mean(0) + b @ np.linalg.solve(a.T@a + .1*5*np.eye(5), a.T@(y-y.mean(0)))
assert np.allclose(predict(x, y, z, ('linear', .1)), primal, atol=1e-12)
# Poison held context's query labels: its selected program and prediction cannot change.
mini = dict(development=[str(i) for i in range(8)], query_groups=plan['query_groups'])
matrix = rng.normal(size=(8, 60))
first, predictions, trials = evaluate(matrix, mini)
matrix[0, 45:] += 10000
second, poisoned_predictions, poisoned_trials = evaluate(matrix, mini)
for name in predictions:
    assert np.allclose(predictions[name][0], poisoned_predictions[name][0], atol=1e-10)
for arm in ['single_only', 'single_plus_anchor']:
    old = next(t for t in trials if t['arm'] == arm and t['held_context'] == '0')
    new = next(t for t in poisoned_trials if t['arm'] == arm and t['held_context'] == '0')
    assert old == new
receipt = dict(status='PASS', checks=['identity_and_scope_guard', 'pair_weighting_and_ties',
    'source_mean_fallback', 'dual_primal_equivalence', 'held_query_poisoning'],
    biological_response_access=False)
(OUT / 'PRELABEL_CHECKS.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
