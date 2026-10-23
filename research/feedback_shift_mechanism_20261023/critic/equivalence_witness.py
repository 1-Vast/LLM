"""Fixed algebra witnesses; no biological data, predictor, search or randomness."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np

start = time.perf_counter()
# Prespecified action features, known batch indicator and observed toy labels.
X = np.array([[0., 1.], [1., 0.], [2., 1.], [0., 2.], [1., 2.], [3., 0.]])
Z = np.array([[1., 0.], [1., 0.], [1., 0.], [0., 1.], [0., 1.], [0., 1.]])
y = np.array([2., 1., 4., 3., 5., 2.])
prior = np.array([0.3, -0.2])
strength = 1.3
joint_system = np.block([[X.T @ X + strength*np.eye(2), X.T @ Z],
                         [Z.T @ X, Z.T @ Z]])
joint_rhs = np.r_[X.T @ y + strength*prior, Z.T @ y]
joint = np.linalg.solve(joint_system, joint_rhs)
M = np.eye(len(y)) - Z @ np.linalg.solve(Z.T @ Z, Z.T)
profiled = np.linalg.solve(X.T @ M @ X + strength*np.eye(2),
                           X.T @ M @ y + strength*prior)
assert np.allclose(joint[:2], profiled, atol=1e-13, rtol=0)
# Fully confounded design: known nuisance space spans all mechanism features.
confounded_X = Z.copy()
confounded = np.linalg.solve(confounded_X.T @ M @ confounded_X + strength*np.eye(2),
                             confounded_X.T @ M @ y + strength*prior)
assert np.allclose(confounded, prior, atol=1e-13, rtol=0)
# One untreated control, one treated action: identical full observed values.
source_biology = np.array([1., 2.])
target_observed = np.array([1., 3.])
measurement_world = 2*source_biology - 1
biology_world = np.array([1., 3.])
assert np.array_equal(measurement_world, target_observed)
assert np.array_equal(biology_world, target_observed)
# Distinct invariant standards with known values identify a shared affine channel.
known_standards = np.array([1., 2.])
observed_standards = np.array([1., 3.])
gain, offset = np.linalg.solve(np.c_[known_standards, np.ones(2)], observed_standards)
assert gain == 2 and offset == -1
out = Path(__file__).resolve().parents[3] / 'log/20261023/feedback_shift_mechanism/critic'
result = dict(status='PASS', purely_synthetic_algebra=True,
              joint_theta=joint[:2].tolist(), profiled_theta=profiled.tolist(),
              maximum_difference=float(np.max(abs(joint[:2]-profiled))),
              full_confounding_returns_prior=confounded.tolist(),
              identical_observation_measurement_world=measurement_world.tolist(),
              identical_observation_biology_world=biology_world.tolist(),
              affine_two_standard_gain=float(gain), affine_two_standard_offset=float(offset),
              limitations='Known invariant distinct standards and shared affine channel are assumptions, not authenticated MAESTRO assets. No method novelty or biological performance established.',
              wall_seconds=time.perf_counter()-start, numpy=np.__version__,
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out / 'EQUIVALENCE_WITNESS.json').write_text(json.dumps(result, indent=2, allow_nan=False))
print(json.dumps(result, indent=2))
