"""Nested conventional baselines for a scoped shared-ancestor composition forecast."""
import hashlib
import json
import os
from pathlib import Path
import time

os.environ['OPENBLAS_NUM_THREADS'] = '2'
os.environ['OMP_NUM_THREADS'] = '2'
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cdk_middle_feedback'
GRIDS = {
    'condition': [0], 'early': [0], 'middle': [0],
    'early_shrink': [0, .25, .5, .75, 1],
    'middle_shrink': [0, .25, .5, .75, 1],
    'early_kernel': [.5, 1, 2], 'middle_kernel': [.5, 1, 2],
    'early_ridge': [.01, .1, 1], 'middle_ridge': [.01, .1, 1],
    'stage': [0, .5, 1],
}
EARLY = ['condition', 'early', 'early_shrink', 'early_kernel', 'early_ridge']
MIDDLE = EARLY + ['middle', 'middle_shrink', 'middle_kernel', 'middle_ridge', 'stage']


def normalize(values, fallback):
    values = np.maximum(values, 0)
    return values / values.sum() if values.sum() > 0 else fallback.copy()


def losses(p, q):
    return {'hellinger2': float(max(0, 1 - np.sqrt(p * q).sum())),
            'tv': float(np.abs(p - q).sum() / 2)}


def predict(name, parameter, train, target, data, context):
    same = [j for j in train if context[j] == context[target]]
    centroid = data[same if same else train, 2].mean(axis=0)
    if name == 'condition':
        return centroid
    if name == 'stage':
        return normalize(data[target, 1] + parameter * (data[target, 1] - data[target, 0]), centroid)
    stage = 1 if name.startswith('middle') else 0
    if name in ('early', 'middle'):
        return data[target, stage]
    if name.endswith('shrink'):
        return (1 - parameter) * centroid + parameter * data[target, stage]
    indices = list(train) + [target]
    features = np.sqrt(data[indices, 0])
    if stage:
        features = np.concatenate((features, np.sqrt(data[indices, 1])), axis=1) / np.sqrt(2)
    distance = np.maximum(0, (features * features).sum(1)[:, None] + (features * features).sum(1)[None, :] - 2 * features @ features.T)
    labels = np.array([context[i] for i in indices])
    distance += (labels[:, None] != labels[None, :])
    source = distance[:-1, :-1]
    positive = source[np.triu_indices(len(train), 1)]
    positive = positive[positive > 1e-12]
    scale = float(np.median(positive)) if len(positive) else 1.0
    bandwidth = parameter if name.endswith('kernel') else 1.0
    kernel = np.exp(-distance / (2 * scale * bandwidth ** 2))
    if name.endswith('kernel'):
        weights = kernel[-1, :-1]
        return weights @ data[train, 2] / weights.sum()
    weights = np.linalg.solve(kernel[:-1, :-1] + parameter * np.eye(len(train)), kernel[:-1, -1])
    roots = np.maximum(weights @ np.sqrt(data[train, 2]), 0)
    return normalize(roots ** 2, centroid)


def select(train, data, context):
    selected = {}
    for name, grid in GRIDS.items():
        candidates = []
        for parameter in grid:
            scores = []
            for target in train:
                inner = [j for j in train if j != target]
                q = predict(name, parameter, inner, target, data, context)
                scores.append(losses(data[target, 2], q)['hellinger2'])
            candidates.append((float(np.mean(scores)), parameter))
        selected[name] = min(candidates, key=lambda item: item[0])
    return selected


def run_scheme(scheme, folds, data, tasks):
    context = [f'{t[0]}_{t[1]}' for t in tasks]
    rows = []
    for fold, test in enumerate(folds):
        train = [i for i in range(12) if i not in test]
        chosen = select(train, data, context)
        early_best = min(EARLY, key=lambda name: chosen[name][0])
        middle_best = min(MIDDLE, key=lambda name: chosen[name][0])
        for target in test:
            for report_name, actual in [(n, n) for n in GRIDS] + [('early_selected', early_best), ('middle_selected', middle_best)]:
                score, parameter = chosen[actual]
                q = predict(actual, parameter, train, target, data, context)
                assert np.all(np.isfinite(q)) and np.all(q >= 0) and np.isclose(q.sum(), 1)
                rows.append({'fold': fold, 'task': tasks[target], 'method': report_name,
                             'selected_method': actual, 'parameter': parameter, 'inner_loss': score,
                             **losses(data[target, 2], q)})
        print(f'{scheme} fold {fold + 1}/{len(folds)} complete', flush=True)
    means = {name: {metric: float(np.mean([r[metric] for r in rows if r['method'] == name]))
                    for metric in ('hellinger2', 'tv')} for name in list(GRIDS) + ['early_selected', 'middle_selected']}
    pairs = []
    for i, task in enumerate(tasks):
        e = next(r for r in rows if r['task'] == task and r['method'] == 'early_selected')
        m = next(r for r in rows if r['task'] == task and r['method'] == 'middle_selected')
        pairs.append({'task': task, 'hellinger_gain': e['hellinger2'] - m['hellinger2'], 'tv_gain': e['tv'] - m['tv']})
    return {'means': means, 'paired_selected': pairs, 'rows': rows}


def main():
    started = time.perf_counter()
    assert not (OUT / 'RESULT.json').exists(), 'No silent reruns'
    metadata = json.loads((OUT / 'PREPARATION.json').read_text())
    assert hashlib.sha256((OUT / 'prepared.npz').read_bytes()).hexdigest() == metadata['prepared_sha256']
    data = np.load(OUT / 'prepared.npz')['compositions']
    tasks = metadata['tasks']
    results = {'loo': run_scheme('loo', [[i] for i in range(12)], data, tasks),
               'index_blocked': run_scheme('index_blocked', [[i for i, t in enumerate(tasks) if t[2] == r] for r in (1, 2, 3)], data, tasks)}
    results['wall_seconds'] = time.perf_counter() - started
    results['scope'] = 'Exploratory shared-ancestor relative-composition forecast; no functional, agent, inheritance or RSI gain claim'
    (OUT / 'RESULT.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps({s: results[s]['means'] for s in ('loo', 'index_blocked')}, indent=2))


if __name__ == '__main__':
    main()
