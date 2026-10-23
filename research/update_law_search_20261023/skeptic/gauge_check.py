import json
from pathlib import Path
import numpy as np

out = Path('log/20261023/update_law_search/skeptic')
J = np.diag([10., 1.])
Q = np.array([[1., -1.], [1., 1.]]) / np.sqrt(2.)
theta = np.array([2., -3.])
eta = Q.T @ theta
F = J.T @ J
Fr = Q.T @ F @ Q

def summary(matrix):
    inverse = np.linalg.inv(matrix)
    return {
        'fisher': matrix.tolist(),
        'pure_decoupling_ratio': (1. / (np.diag(matrix) * np.diag(inverse))).tolist(),
        'a_optimal_trace': float(np.trace(inverse)),
        'd_optimal_determinant': float(np.linalg.det(matrix)),
        'eigenvalues': np.linalg.eigvalsh(matrix).tolist(),
    }

result = {'original': summary(F), 'rotated': summary(Fr), 'prediction_max_error': float(np.max(np.abs(J @ theta - J @ Q @ eta))), 'rng': None, 'biological_outcome_reads': 0, 'claim': 'pure parameter decoupling is not invariant under latent coordinate rotation'}
assert result['prediction_max_error'] < 1e-12
assert np.allclose(result['original']['eigenvalues'], result['rotated']['eigenvalues'])
assert np.allclose(result['original']['a_optimal_trace'], result['rotated']['a_optimal_trace'])
assert np.allclose(result['original']['d_optimal_determinant'], result['rotated']['d_optimal_determinant'])
assert min(result['original']['pure_decoupling_ratio']) > .99
assert max(result['rotated']['pure_decoupling_ratio']) < .04
(out / 'GAUGE_CHECK.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
