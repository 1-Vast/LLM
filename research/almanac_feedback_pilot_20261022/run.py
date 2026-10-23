"""Source-only finite selection, refit, development evaluation and study diagnostic."""
import json
import math
import platform
import time
from collections import Counter
import numpy as np
from models import MENU, predict_catalog, select
from prepare import OUT, verify_freeze


def metrics(pred, truth):
    error = pred - truth[..., :8]
    actual = truth[..., :8].mean(axis=-1)
    scores = pred.mean(axis=-1)
    k = math.ceil(.1 * actual.shape[1])
    regrets = []
    for a, s in zip(actual, scores):
        picked = np.argsort(s, kind='stable')[:k]
        oracle = np.argsort(a, kind='stable')[:k]
        regrets.append(float(a[picked].mean() - a[oracle].mean()))
    return {'mse': float(np.mean(error ** 2)), 'mae': float(np.mean(abs(error))),
            'cell_mse': np.mean(error ** 2, axis=(1, 2)).tolist(),
            'cell_mae': np.mean(abs(error), axis=(1, 2)).tolist(),
            'dose_mse': np.mean(error ** 2, axis=(0, 1)).tolist(),
            'cell_top10pct_regret': regrets, 'mean_top10pct_regret': float(np.mean(regrets))}


def main():
    verify_freeze()
    assert not (OUT / 'RESULTS.json').exists()
    start = time.perf_counter()
    values = np.load(OUT / 'VALUES.npz')
    solo, y = values['solo'], values['y']
    predictions, tune_predictions, tune_risks, choices = {}, {}, {}, {}
    for budget in (0, 1):
        candidates = {}
        for name in MENU:
            candidates[name], _ = predict_catalog(name, budget, solo[:20], y[:20], solo[20:30], y[20:30, :, 8] if budget else None)
        if budget:
            candidates['B0-fallback'] = tune_predictions['B0-selected']
        selected, risks = select(candidates, y[20:30])
        choices[str(budget)], tune_risks[str(budget)] = selected, risks
        for name, pred in candidates.items():
            tune_predictions[f'B{budget}:{name}'] = pred
        tune_predictions[f'B{budget}-selected'] = candidates[selected]
        for name in MENU:
            predictions[f'B{budget}:{name}'], _ = predict_catalog(name, budget, solo[:30], y[:30], solo[30:40], y[30:40, :, 8] if budget else None)
        if budget:
            predictions['B1:B0-fallback'] = predictions['B0-selected']
        predictions[f'B{budget}-selected'] = predictions[f'B{budget}:{selected}']
    split = json.loads((OUT / 'SPLIT.json').read_text())
    tasks = json.loads((OUT / 'DESIGN_TASKS.json').read_text())
    study = np.array([[tasks[i]['study'] for i in row] for row in split['task_indices_by_cell_pair']])
    study_counts = {}
    for budget in (0, 1):
        selected = choices[str(budget)]
        if selected == 'B0-fallback':
            name, actual_budget = choices['0'], 0
        else:
            name, actual_budget = selected, budget
        pred, counts = predict_catalog(name, actual_budget, solo[:30], y[:30], solo[30:40],
                                       y[30:40, :, 8] if actual_budget else None, study[:30], study[30:40])
        predictions[f'B{budget}-study-exclusion'] = pred
        study_counts[str(budget)] = dict(Counter(counts))
    result_metrics = {name: metrics(pred, y[30:40]) for name, pred in predictions.items()}
    a, b = (np.array(result_metrics[f'B{budget}-selected']['cell_mse']) for budget in (0, 1))
    gain = a - b
    rng = np.random.default_rng(20261022)
    boot = gain[rng.integers(0, len(gain), size=(10000, len(gain)))].mean(axis=1)
    interval = np.quantile(boot, [.025, .975]).tolist()
    study_gain = result_metrics['B0-study-exclusion']['mse'] - result_metrics['B1-study-exclusion']['mse']
    gates = {'positive_mean': bool(gain.mean() > 0), 'cell_bootstrap_lower_positive': bool(interval[0] > 0),
             'at_least_seven_cells_improve': bool(np.sum(gain > 0) >= 7),
             'all_delete_one_cell_positive': bool(np.all((gain.sum() - gain) / (len(gain) - 1) > 0)),
             'study_exclusion_gain_positive': bool(study_gain > 0)}
    result = {'choices': choices, 'tune_risks': tune_risks, 'development_metrics': result_metrics,
              'selected_gain': float(gain.mean()), 'cell_gains': gain.tolist(), 'bootstrap95_fixed_predictions': interval,
              'study_exclusion_gain': study_gain, 'study_exclusion_source_n_histogram': study_counts,
              'gates': gates, 'advance_to_error_diagnosis': all(gates.values()),
              'wall_s': time.perf_counter() - start, 'numpy': np.__version__, 'python': platform.python_version(),
              'seed': 20261022, 'deepseek_calls': 0, 'new_wet_experiments': 0,
              'native_agent_cost': 'not exposed', 'scope': 'ordinary functional feedback pilot, not WM/agent/inheritance/RSI'}
    np.savez_compressed(OUT / 'PREDICTIONS.npz', **predictions)
    np.savez_compressed(OUT / 'TUNE_PREDICTIONS.npz', **tune_predictions)
    (OUT / 'RESULTS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('choices', 'selected_gain', 'bootstrap95_fixed_predictions', 'study_exclusion_gain', 'gates', 'wall_s')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
