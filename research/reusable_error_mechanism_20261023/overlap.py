"""Fixed overlap residual-law falsifier on already exposed saved aggregates."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/reusable_error_mechanism'
OLD = ROOT / 'log/20261023/mixed_feedback_estimator'


def feature(a, b):
    return np.where(a * b > 0, -np.sign(a) * np.minimum(np.abs(a), np.abs(b)), 0.)


def coefficient(h, r):
    denominator = float(np.sum(h * h))
    return float(np.clip(np.sum(h * r) / denominator, 0., 1.)) if denominator else 0.


def self_check():
    a, b = np.array([2., -3., 2., 0.]), np.array([1., -1., -1., 2.])
    h = feature(a, b)
    np.testing.assert_array_equal(h, [-1., 1., 0., 0.])
    np.testing.assert_array_equal(feature(b, a), h)
    np.testing.assert_array_equal(feature(3 * a, 3 * b), 3 * h)
    assert np.all(np.abs(h) <= np.minimum(np.abs(a), np.abs(b)))
    assert coefficient(np.array([1., 2.]), np.array([.5, 1.])) == .5
    assert coefficient(np.array([1., 2.]), np.array([-1., -2.])) == 0.
    assert coefficient(np.array([1., 2.]), np.array([2., 4.])) == 1.
    r, hh, train = np.array([.2, .4, 100.]), np.ones(3), np.array([0, 1])
    original = coefficient(hh[train], r[train])
    r[2] = -1e100
    assert original == coefficient(hh[train], r[train])
    return dict(status='PASS', checks=['sign/support', 'swap', 'positive_homogeneity',
                'weaker_parent_bound', 'constrained_optimum_interior_and_boundaries', 'heldout_target_isolation'])


def arrays(data, pairs, inputs, targets):
    lookup = {(str(n), int(g)): i for i, (n, g) in enumerate(zip(data['group_names'], data['gems']))}
    values = data['mean_log1pCP10K']

    def centered(name, gem):
        return values[lookup[(name, gem)]] - values[lookup[('CONTROL', gem)]]

    hh, rr = [], []
    for pair in pairs:
        a, b = pair.split('|')
        hh.append(np.mean([feature(centered(a, g), centered(b, g)) for g in inputs], axis=0))
        rr.append(np.mean([centered(pair, g) - centered(a, g) - centered(b, g) for g in targets], axis=0))
    return np.asarray(hh), np.asarray(rr)


def main():
    assert not (OUT / 'OVERLAP_STARTED.json').exists(), 'Inspect existing execution, never silently rerun'
    freeze = json.loads((OUT / 'OVERLAP_FREEZE.json').read_text(encoding='utf-8'))
    for path, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    checks = self_check()
    (OUT / 'OVERLAP_SELFCHECK.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    (OUT / 'OVERLAP_STARTED.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat())), encoding='utf-8')
    started = time.perf_counter()
    data = np.load(OLD / 'STATE_BY_GEM.npz', allow_pickle=False)
    previous = np.load(OLD / 'OOF_STATE.npz', allow_pickle=False)
    meta = pd.read_csv(OLD / 'support/SOURCE_PAIR_METADATA.csv')
    pairs = sorted(meta.loc[meta.identity_qc_cells > 0, 'pair'].tolist())
    assert len(pairs) == len(set(pairs)) == 73
    folds = np.array([int.from_bytes(hashlib.sha256(('MAESTRO_MIXED_DIAGONAL_V1|' + p).encode()).digest()[:8], 'big') % 5 for p in pairs])
    np.testing.assert_array_equal(previous['pairs'], pairs)
    np.testing.assert_array_equal(previous['folds'], folds)
    saved, reports = dict(pairs=np.array(pairs), folds=folds), []
    for direction, inputs, targets in [('A_to_B', [1, 2, 3, 4], [5, 6, 7, 8]),
                                        ('B_to_A', [5, 6, 7, 8], [1, 2, 3, 4])]:
        h, r = arrays(data, pairs, inputs, targets)
        key = 'mean_log1pCP10K__' + direction
        np.testing.assert_allclose(r, previous[key + '__truth'], rtol=0., atol=1e-15)
        assert h.shape == r.shape == (73, 103) and np.isfinite(h).all() and np.isfinite(r).all()
        pred, records = np.full_like(r, np.nan), []
        for fold in range(5):
            train, test = folds != fold, folds == fold
            theta = coefficient(h[train], r[train])
            pred[test] = theta * h[test]
            records.append(dict(fold=fold, theta=theta, train_pairs=int(train.sum()), test_pairs=int(test.sum()),
                                MSE=float(np.mean((pred[test] - r[test]) ** 2)),
                                direct_MSE=float(np.mean((previous[key + '__linear_ridge'][test] - r[test]) ** 2))))
        theta_oracle = coefficient(h, r)
        scores = {name: float(np.mean((previous[key + '__' + name] - r) ** 2))
                  for name in ['additive', 'linear_ridge', 'q_ridge', 'bilinear_ridge', 'mean']}
        scores['bounded_overlap'] = float(np.mean((pred - r) ** 2))
        scores['in_sample_global_scalar_oracle'] = float(np.mean((theta_oracle * h - r) ** 2))
        reports.append(dict(direction=direction, scores=scores, folds=records, theta_oracle=theta_oracle,
                            pooled_h_dot_r=float(np.sum(h * r)), pooled_h_norm2=float(np.sum(h * h)),
                            feature_nonzero_fraction=float(np.mean(h != 0)),
                            strict_direct_and_additive_pass=bool(scores['bounded_overlap'] < min(scores['linear_ridge'], scores['additive']))))
        saved.update({direction + '__h': h, direction + '__truth': r, direction + '__prediction': pred,
                      direction + '__direct': previous[key + '__linear_ridge']})
    passes = all(r['strict_direct_and_additive_pass'] for r in reports)
    result = dict(status='NECESSARY_SOURCE_SCREEN_ONLY' if passes else 'STOP_FIXED_BOUNDED_OVERLAP_LAW',
                  directions=reports, fit_calls=12, seconds=time.perf_counter() - started,
                  functional_labels_read=0, raw_matrix_reads=0, python=sys.version,
                  scope='New fixed post-history hypothesis on exposed source; oracle is not OOF performance')
    np.savez_compressed(OUT / 'OVERLAP_ARRAYS.npz', **saved)
    (OUT / 'OVERLAP_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
