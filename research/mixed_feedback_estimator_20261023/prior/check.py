"""Synthetic bounded check: functional low-variance directions and standard baselines."""
import datetime
import hashlib
import json
import platform
from pathlib import Path
import numpy as np

out = Path('log/20261023/mixed_feedback_estimator/prior')
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261023)

# Literal intervention-feature -> named-state linear map; no cell data.
truth = np.diag([20.0, 0.2, 0.0, 0.0])
readout = np.array([0.0, 1.0, 0.0, 0.0])
def lowrank(matrix, rank=1):
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)
    return (u[:, :rank] * s[:rank]) @ vh[:rank]

rows = []
for weight in [0.0, 100.0, 10000.0, 20000.0]:
    # ||W-T||_F^2 + weight ||(W-T) beta||_2^2, rank(W)<=1.
    qhalf = np.diag(np.sqrt(1.0 + weight * readout))
    fitted = lowrank(truth @ qhalf) @ np.linalg.inv(qhalf)
    error = fitted - truth
    transformed_objective = np.linalg.norm(error @ qhalf)**2
    direct_objective = np.linalg.norm(error)**2 + weight * np.linalg.norm(error @ readout)**2
    assert np.isclose(transformed_objective, direct_objective, atol=1e-9)
    rows.append({'function_weight': weight,
                 'state_squared_error': float(np.linalg.norm(error)**2),
                 'function_squared_error': float(np.linalg.norm(error @ readout)**2),
                 'objective_equivalence_error': float(abs(transformed_objective-direct_objective)),
                 'fit': fitted.tolist()})
assert rows[0]['function_squared_error'] > .039999
assert rows[-1]['function_squared_error'] < 1e-20
assert rows[-1]['state_squared_error'] > 399.999

# Fully mixed channels: any observation H_i W^T x_i becomes a row of a
# conventional linear inverse/matrix-sensing design. Every full-state channel
# and function-only channel is included; this is an exact objective identity.
p, d, n = 5, 4, 23
features = rng.normal(size=(n, p))
w = rng.normal(size=(p, d))
beta = rng.normal(size=d)
design, observed, predictions = [], [], []
for i, x in enumerate(features):
    h = np.eye(d) if i % 3 == 0 else beta[None, :]
    target = rng.normal(size=h.shape[0])
    pred = h @ w.T @ x
    for row, y, yhat in zip(h, target, pred):
        design.append(np.kron(row, x))
        observed.append(y)
        predictions.append(yhat)
design = np.asarray(design)
observed = np.asarray(observed)
native_predictions = np.asarray(predictions)
linear_predictions = design @ w.flatten(order='F')
max_error = float(np.max(np.abs(native_predictions-linear_predictions)))
assert max_error < 1e-12
native_loss = float(np.sum((native_predictions-observed)**2))
linear_loss = float(np.sum((linear_predictions-observed)**2))
assert abs(native_loss-linear_loss) < 1e-10
result = {'status': 'PASS_SYNTHETIC_IDENTITIES_NOT_BIOLOGICAL_PERFORMANCE',
          'seed': 20261023, 'numpy': np.__version__, 'python': platform.python_version(),
          'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'rna_variance_vs_function_weighting': rows,
          'mixed_observation_identity': {'measurements': len(observed),
              'parameter_shape': [p, d], 'max_prediction_discrepancy': max_error,
              'native_loss': native_loss, 'linear_sensing_loss': linear_loss},
          'new_biological_values': 0, 'model_fits_on_biological_data': 0,
          'scope': 'Known linear functional readout and linear anchored state map only. '
                   'No universal equivalence for nonlinear/shared-circuit estimators.'}
(out / 'WITNESS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
