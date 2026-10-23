"""Symmetric pair kernel must preserve PSD and orientation equivalence."""
import numpy as np
from experiment import pair_kernel

gene = np.array([[1., .5, -.2], [.5, 1., .1], [-.2, .1, 1.]])
a, b = np.array([0, 0, 1]), np.array([1, 2, 2])
k = pair_kernel(gene, a, b, a, b)
assert np.allclose(np.diag(k), 1)
assert np.allclose(k, k.T)
assert np.linalg.eigvalsh(k).min() > -1e-12
assert np.allclose(k, pair_kernel(gene, b, a, a, b))
print('PASS pair kernel PSD/unit diagonal/order invariance')
