"""Check explicit observation mask against an analytically solved two-gene case."""
import numpy as np
from calibrate import complete

prediction, info = complete(np.array([1.]), np.array([0]), np.array([1]), np.eye(2), .1, 2)
assert np.allclose(prediction, [[0, .9], [.9, 0]], atol=1e-6)
zero, _ = complete(np.array([0.]), np.array([0]), np.array([1]), np.eye(2), .1, 2)
assert np.array_equal(zero, np.zeros((2, 2)))
assert info['converged']
print('PASS nuclear completion analytic shrinkage, symmetry and observed-zero case')
