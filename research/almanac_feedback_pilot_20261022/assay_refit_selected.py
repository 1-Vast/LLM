"""Independent selected RBF fits only; no root imports, reserve access or selection."""
import hashlib
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[2]
phase = root / 'log/20261022/almanac_feedback_pilot'
out = phase / 'assay/SELECTED_RBF_REFIT.json'
assert not out.exists()
values = np.load(phase / 'root/VALUES.npz')
solo, y = values['solo'], values['y']
saved = np.load(phase / 'root/PREDICTIONS.npz')


def expected(v):
    left, right = v[:, :3, None], v[:, None, 3:]
    return np.where((left < 0) | (right < 0), np.minimum(left, right),
                    np.minimum(left, 1) * np.minimum(right, 1)).reshape(len(v), 9)


stats = {}
for budget, regularizer in ((0, .1), (1, .01)):
    pred = np.empty((10, 887, 8))
    for pair in range(887):
        source_solo, target_solo = solo[:30, pair], solo[30:40, pair]
        source_base, target_base = expected(source_solo), expected(target_solo)
        residual = y[:30, pair] - source_base
        x, t = source_solo.copy(), target_solo.copy()
        if budget:
            x = np.concatenate((x, residual[:, 8, None]), axis=1)
            t = np.concatenate((t, (y[30:40, pair, 8] - target_base[:, 8])[:, None]), axis=1)
        mu, sigma = x.mean(0), np.maximum(x.std(0), .05)
        x, t = (x - mu) / sigma, (t - mu) / sigma
        xx = np.square(x[:, None, :] - x[None, :, :]).mean(2)
        tx = np.square(t[:, None, :] - x[None, :, :]).mean(2)
        kernel = np.exp(-xx / 8)
        cross = np.exp(-tx / 8)
        mean = residual.mean(0)
        weights = np.linalg.solve(kernel + (30 * regularizer + 1e-8) * np.eye(30), residual - mean)
        pred[:, pair] = (target_base + mean + cross @ weights)[:, :8]
    delta = pred - saved[f'B{budget}-selected']
    np.testing.assert_allclose(pred, saved[f'B{budget}-selected'], rtol=1e-11, atol=1e-12)
    stats[str(budget)] = {'max_abs_difference': float(abs(delta).max()),
                          'numeric_predictions': pred.size,
                          'mse': float(np.square(pred - y[30:40, :, :8]).mean())}
result = {'status': 'PASS', 'scope': 'Independent 30-source to 10-development refit of two selected RBF programs, all887pairs. No menu search, tuning refit or study-exclusion refit.',
          'budgets': stats, 'reserve_accessed': False, 'root_code_imported': False,
          'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
