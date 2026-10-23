"""Synthetic counterexamples to overbroad interpretations, before real gate."""
import json
from pathlib import Path
import numpy as np
from reciprocity import examine, TOL

# Exact quadratic potential with positive conjugate-force amplitudes.
susceptibility = np.array([[2., .4, .2], [.4, 3., .5], [.2, .5, 4.]])
assert np.linalg.eigvalsh(susceptibility).min() > 0
result, _ = examine(susceptibility @ np.diag([.3, 2., 5.]))
assert result['opposite_sign_pairs'] == 0 and result['positive_diagonal'] == 3
assert max(result['triangle_normalized_defect_quantiles']) < TOL
assert result['same_sign_graph_max_log_ratio_cycle_defect'] < TOL

# Numerical near-zero does not imply exact support/diagonal failure.
tiny = np.array([[2., .1], [.1, 1.]]) @ np.diag([1e-13, 1.])
result, _ = examine(tiny)
assert result['one_sided_numerical_zero_pairs'] == 1
assert result['exact_one_sided_zero_pairs'] == 0
assert result['exact_nonpositive_diagonal'] == 0
assert result['exact_opposite_sign_pairs'] == 0

# Nonconjugate dense forcing can violate reciprocity with an SPD susceptibility.
forcing = np.eye(3)
forcing[0, 1] = -1
result, _ = examine(susceptibility @ forcing)
assert result['opposite_sign_pairs'] > 0

# A sparse chordless 4-cycle can fail despite having no full triangles.
sparse = np.eye(4)
for i, j in [(0, 1), (1, 2), (2, 3), (0, 3)]:
    sparse[i, j] = sparse[j, i] = .2
sparse[0, 3] = .4
result, _ = examine(sparse)
assert result['fully_nonzero_triangles'] == 0
assert result['same_sign_graph_max_log_ratio_cycle_defect'] > .5

# Nonlinear potential V=.5(x²+y²)+eps*x²*y/2 has symmetric local Hessian,
# yet finite x/y conjugate forces yield nonreciprocal endpoint cross responses.
eps, amplitude = .2, .5
x = amplitude
for _ in range(10):
    x -= (x - .5*eps**2*x**3 - amplitude) / (1 - 1.5*eps**2*x**2)
y = -.5*eps*x*x
assert abs(x + eps*x*y - amplitude) < 1e-12 and abs(y + .5*eps*x*x) < 1e-12
hessian = np.array([[1+eps*y, eps*x], [eps*x, 1.]])
assert np.linalg.eigvalsh(hessian).min() > 0
finite = np.array([[x, 0.], [y, amplitude]])
result, _ = examine(finite)
assert result['one_sided_numerical_zero_pairs'] == 1

out = Path(__file__).resolve().parents[2] / 'log/20261023/intervention_constraint'
(out / 'RECIPROCITY_TEST.json').write_text(json.dumps({'status': 'PASS_SYNTHETIC',
    'cases': ['quadratic_SPD_positive_amplitudes', 'tiny_positive_amplitude', 'dense_force_mapping', 'chordless_cycle', 'nonlinear_finite_force'],
    'biological_values_loaded': 0}, indent=2))
print('PASS synthetic necessary conditions and scope counterexamples')
