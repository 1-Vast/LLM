"""A new mathematical identifiability witness, not a biological fit or RSI test."""
import json
from pathlib import Path
import numpy as np

OUT = Path('log/20261023/update_law_search/mechanism')
records = []
single_states = []
for c in [-0.5, 0.0, 0.5]:
    regimes = []
    for u1, u2 in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        x = np.array([u1 / (1 - c * u2), u2], dtype=float)
        f = np.array([-x[0] + u1 + c * x[0] * x[1], -x[1] + u2])
        jac = np.array([[-1 + c * x[1], c * x[0]], [0, -1]])
        assert np.max(np.abs(f)) < 1e-14
        assert np.max(np.linalg.eigvals(jac).real) < 0
        regimes.append({'u': [u1, u2], 'x': x.tolist(), 'function': float(sum(x)),
                        'eigenvalues': np.linalg.eigvals(jac).tolist()})
    single_states.append([r['x'] for r in regimes[:3]])
    records.append({'c': c, 'regimes': regimes})
assert np.array_equal(single_states[0], single_states[1])
assert np.array_equal(single_states[1], single_states[2])
# Arbitrary single-axis amplitudes, not just one measured dose.
for c in [-0.5, 0.0, 0.5]:
    for u in np.linspace(0, 1, 101):
        for x, action in [(np.array([u, 0.0]), [u, 0]), (np.array([0.0, u]), [0, u])]:
            assert np.max(np.abs([-x[0]+action[0]+c*x[0]*x[1], -x[1]+action[1]])) < 1e-14
# Exact low-rank inverse update identity on an independently chosen directed system.
rng = np.random.default_rng(20261023)
jac = -2 * np.eye(5) + rng.normal(size=(5, 5)) * 0.05
left, right = rng.normal(size=5) * .1, rng.normal(size=5) * .1
inv = np.linalg.inv(jac)
woodbury = inv - np.outer(inv @ left, right @ inv) / (1 + right @ inv @ left)
error = float(np.max(np.abs(woodbury - np.linalg.inv(jac + np.outer(left, right)))))
assert error < 1e-14
result = {'status': 'PASS_MATHEMATICAL_WITNESS_ONLY', 'models': records,
          'identical_control_and_single_states': True,
          'identical_all_single_axis_doses_0_to_1': True,
          'control_jacobian_all_models': [[-1, 0], [0, -1]],
          'pair_function_range': [5/3, 3.0], 'woodbury_max_error': error,
          'biological_values_read': 0, 'biological_fits': 0,
          'provider_calls': 0, 'independent_tasks': 0}
(OUT / 'WITNESS.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print(json.dumps(result, indent=2))
