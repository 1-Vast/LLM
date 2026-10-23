"""Fixed saved-prediction accounting; no fits, candidate search or raw-data read."""
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'log/20261022/almanac_feedback_pilot/root'
OUT = ROOT / 'log/20261022/functional_error_structure'


def components(error):
    pair = error.mean(axis=2)
    global_error = pair.mean(axis=1, keepdims=True)
    terms = np.stack((global_error[:, 0] ** 2,
                      ((pair - global_error) ** 2).mean(axis=1),
                      ((error - pair[:, :, None]) ** 2).mean(axis=(1, 2))), axis=1)
    np.testing.assert_allclose(terms.sum(axis=1), (error ** 2).mean(axis=(1, 2)), atol=1e-12, rtol=0)
    return terms


def main():
    assert not (OUT / 'RESULT.json').exists()
    start = time.perf_counter()
    inputs = [OLD / name for name in ('PREDICTIONS.npz', 'VALUES.npz', 'RESULTS.json')]
    inputs += [Path(__file__), OUT / 'PROTOCOL.md']
    bindings = {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (OUT / 'PRECOMPUTE_BINDINGS.json').write_text(json.dumps(bindings, indent=2), encoding='utf-8')
    # NPZ access materializes first40 previously exposed cells; there are no reserve cells in this cache.
    truth = np.load(OLD / 'VALUES.npz')['y'][30:40, :, :8]
    assert truth.shape == (10, 887, 8)
    predictions = np.load(OLD / 'PREDICTIONS.npz')
    saved = json.loads((OLD / 'RESULTS.json').read_text(encoding='utf-8'))['development_metrics']
    actual = truth.mean(axis=2)
    count = 89
    oracle = np.argsort(actual, axis=1, kind='stable')[:, :count]
    oracle_mean = np.take_along_axis(actual, oracle, axis=1).mean(axis=1)
    report = {'scope': 'Post-selection descriptive accounting of exposed development predictions; not a new model or biological validation',
              'term_order': ['global_mean_error', 'centered_pair_mean_error', 'within_pair_dose_error'], 'variants': {}}
    for variant, suffix in (('all_source', 'selected'), ('study_exclusion', 'study-exclusion')):
        records, terms, selections = {}, {}, {}
        for budget in (0, 1):
            name = f'B{budget}-{suffix}'
            pred = predictions[name]
            assert pred.shape == truth.shape and np.isfinite(pred).all()
            error = pred - truth
            terms[budget] = components(error)
            picks = np.argsort(pred.mean(axis=2), axis=1, kind='stable')[:, :count]
            selections[budget] = picks
            regret = np.take_along_axis(actual, picks, axis=1).mean(axis=1) - oracle_mean
            np.testing.assert_allclose(terms[budget].sum(axis=1), saved[name]['cell_mse'], atol=1e-12, rtol=0)
            np.testing.assert_allclose(regret, saved[name]['cell_top10pct_regret'], atol=1e-12, rtol=0)
            records[name] = {'cell_terms': terms[budget].tolist(), 'mean_terms': terms[budget].mean(axis=0).tolist(),
                             'mse': float(np.mean(error ** 2)), 'cell_regret': regret.tolist(), 'mean_regret': float(regret.mean())}
        swaps = []
        for cell in range(10):
            entrants = np.setdiff1d(selections[1][cell], selections[0][cell])
            exits = np.setdiff1d(selections[0][cell], selections[1][cell])
            assert len(entrants) == len(exits)
            entrant_sum = float(actual[cell, entrants].sum())
            exit_sum = float(actual[cell, exits].sum())
            delta = (entrant_sum - exit_sum) / count
            difference = records[f'B1-{suffix}']['cell_regret'][cell] - records[f'B0-{suffix}']['cell_regret'][cell]
            np.testing.assert_allclose(delta, difference, atol=1e-12, rtol=0)
            swaps.append({'cell_index': cell, 'entrants': entrants.tolist(), 'exits': exits.tolist(),
                          'count_each': len(entrants), 'sum_truth_entered': entrant_sum, 'sum_truth_exited': exit_sum,
                          'regret_change_B1_minus_B0': delta, 'observed_regret_change_B1_minus_B0': difference})
        gain = terms[0] - terms[1]
        report['variants'][variant] = {'models': records, 'cell_component_gain_B0_minus_B1': gain.tolist(),
                                       'mean_component_gain_B0_minus_B1': gain.mean(axis=0).tolist(),
                                       'positive_component_gain_cells': (gain > 0).sum(axis=0).tolist(), 'swaps': swaps}
    report.update(wall_seconds=time.perf_counter() - start, python=platform.python_version(), numpy=np.__version__,
                  new_fits=0, deepseek_calls=0, new_wet_experiments=0, seed='none: deterministic fixed arrays')
    (OUT / 'RESULT.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: {'component_gains': v['mean_component_gain_B0_minus_B1'],
                          'models': {n: {'mse': m['mse'], 'regret': m['mean_regret']} for n, m in v['models'].items()}}
                      for k, v in report['variants'].items()}, indent=2))


if __name__ == '__main__':
    main()
