"""One post-pilot descriptive source/tune diagnostic; no correction fitting."""
import json
from pathlib import Path
import numpy as np
from models import predict_pair

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/almanac_feedback_pilot/root'


def relation(innovation, errors):
    x = innovation - innovation.mean(axis=1, keepdims=True)
    e = errors - errors.mean(axis=1, keepdims=True)
    covariance = np.mean(x[..., None] * e, axis=1)
    xv = np.mean(x * x, axis=1)
    ev = np.mean(e * e, axis=1)
    slope = covariance / np.maximum(xv[:, None], 1e-12)
    corr = covariance / np.sqrt(np.maximum(xv[:, None] * ev, 1e-24))
    return {'cell_slopes': slope.tolist(), 'cell_correlations': corr.tolist(),
            'positive_slope_cells_by_query': np.sum(slope > 0, axis=0).tolist(),
            'mean_cell_slope': slope.mean(axis=0).tolist(),
            'mean_cell_correlation': corr.mean(axis=0).tolist()}


def main():
    assert not (OUT / 'ERROR_DIAGNOSIS.json').exists()
    data = np.load(OUT / 'VALUES.npz')
    # No development truth is selected or used in this diagnostic.
    solo, truth = data['solo'][:30], data['y'][:30]
    results = json.loads((OUT / 'RESULTS.json').read_text())
    assert all(results['choices'][str(b)].startswith('rbf:') for b in (0, 1))
    split = json.loads((OUT / 'SPLIT.json').read_text())
    tasks = json.loads((OUT / 'DESIGN_TASKS.json').read_text())
    study = np.array([[tasks[i]['study'] for i in row] for row in split['task_indices_by_cell_pair'][:30]])
    report = {'scope': 'post-result source20/tune10 descriptive correlations; no correction fitting, no development/reserve truth'}
    for exclude in (False, True):
        forecasts = {b: np.empty((10, 887, 9)) for b in (0, 1)}
        counts = []
        for c in range(10):
            for p in range(887):
                mask = np.ones(20, dtype=bool) if not exclude else study[:20, p] != study[c + 20, p]
                assert mask.sum() >= 2
                counts.append(int(mask.sum()))
                for b in (0, 1):
                    forecasts[b][c:c + 1, p] = predict_pair(results['choices'][str(b)], b,
                        solo[:20, p][mask], truth[:20, p][mask], solo[c + 20:c + 21, p],
                        truth[c + 20:c + 21, p, 8] if b else None)
        innovation = truth[20:30, :, 8] - forecasts[0][..., 8]
        report['study_exclusion' if exclude else 'all_source'] = {
            'source_n_range': [min(counts), max(counts)],
            'B0': relation(innovation, forecasts[0][..., :8] - truth[20:30, :, :8]),
            'B1': relation(innovation, forecasts[1][..., :8] - truth[20:30, :, :8])}
    (OUT / 'ERROR_DIAGNOSIS.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({name: {b: report[name][b]['mean_cell_correlation'] for b in ('B0', 'B1')}
                      for name in ('all_source', 'study_exclusion')}, indent=2))


if __name__ == '__main__':
    main()
