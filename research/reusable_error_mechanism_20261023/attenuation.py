"""One post-result same-parameter ordinary shrinkage control, no feature menu."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/reusable_error_mechanism'
OLD = ROOT / 'log/20261023/mixed_feedback_estimator'


def scalar(g, r):
    norm = np.sum(g * g)
    return float(np.clip(np.sum(g * r) / norm, 0., 1.)) if norm else 0.


def main():
    assert not (OUT / 'ATTENUATION_STARTED.json').exists()
    paths = [Path(__file__), OUT / 'ATTENUATION_PROTOCOL.md', OUT / 'OVERLAP_ARRAYS.npz',
             OUT / 'OVERLAP_RESULT.json', OLD / 'STATE_BY_GEM.npz']
    assert not (OUT / 'ATTENUATION_FREEZE.json').exists()
    freeze = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUT / 'ATTENUATION_FREEZE.json').write_text(json.dumps(dict(files=freeze, utc=datetime.now(timezone.utc).isoformat()), indent=2), encoding='utf-8')
    (OUT / 'ATTENUATION_STARTED.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat())), encoding='utf-8')
    started = time.perf_counter()
    data = np.load(OLD / 'STATE_BY_GEM.npz', allow_pickle=False)
    saved = np.load(OUT / 'OVERLAP_ARRAYS.npz', allow_pickle=False)
    pairs, folds = saved['pairs'].tolist(), saved['folds']
    values = data['mean_log1pCP10K']
    lookup = {(str(n), int(g)): i for i, (n, g) in enumerate(zip(data['group_names'], data['gems']))}
    rows, output = [], dict(pairs=np.array(pairs), folds=folds)
    for direction, gems in [('A_to_B', [1, 2, 3, 4]), ('B_to_A', [5, 6, 7, 8])]:
        features = []
        for pair in pairs:
            a, b = pair.split('|')
            features.append(np.mean([-(values[lookup[(a, g)]] + values[lookup[(b, g)]]
                                       - 2 * values[lookup[('CONTROL', g)]]) for g in gems], axis=0))
        g = np.asarray(features)
        r, overlap = saved[direction + '__truth'], saved[direction + '__prediction']
        assert np.isfinite(g).all() and g.shape == r.shape == (73, 103)
        pred, records = np.full_like(r, np.nan), []
        for fold in range(5):
            train, test = folds != fold, folds == fold
            beta = scalar(g[train], r[train])
            pred[test] = beta * g[test]
            records.append(dict(fold=fold, beta=beta, MSE=float(np.mean((pred[test] - r[test]) ** 2)),
                                overlap_MSE=float(np.mean((overlap[test] - r[test]) ** 2))))
        beta_oracle = scalar(g, r)
        mse, overlap_mse = float(np.mean((pred - r) ** 2)), float(np.mean((overlap - r) ** 2))
        rows.append(dict(direction=direction, attenuation_MSE=mse, overlap_MSE=overlap_mse,
                         direct_MSE=float(np.mean((saved[direction + '__direct'] - r) ** 2)),
                         folds=records, oracle_beta=beta_oracle,
                         in_sample_scalar_oracle_MSE=float(np.mean((beta_oracle * g - r) ** 2)),
                         overlap_strictly_better=bool(overlap_mse < mse)))
        output.update({direction + '__g': g, direction + '__prediction': pred})
    result = dict(status='NECESSARY_CONTROL_SCREEN_ONLY' if all(r['overlap_strictly_better'] for r in rows)
                  else 'STOP_OVERLAP_SPECIFIC_ADVANTAGE_ON_THIS_SOURCE', directions=rows,
                  fit_calls=12, seconds=time.perf_counter() - started,
                  scope='One post-result separately frozen ordinary control on exposed data, not independent confirmation',
                  functional_outcomes_read=0, raw_matrix_reads=0)
    np.savez_compressed(OUT / 'ATTENUATION_ARRAYS.npz', **output)
    (OUT / 'ATTENUATION_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
