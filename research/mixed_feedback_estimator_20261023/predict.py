"""Frozen source-pair OOF falsifier; never reads functional outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/mixed_feedback_estimator'
GRID = [.001, .01, .1, 1., 10., 100.]
MODELS = ['mean', 'diagonal', 'q_ridge', 'linear_ridge', 'bilinear_ridge']
COSTS = []


def hashed(value, salt):
    return int.from_bytes(hashlib.sha256((salt + value).encode()).digest()[:8], 'big')


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()


def design(a, b):
    # n pairs x four gemgroups x 103 named coordinates.
    outer = np.einsum('ngk,ngl->nkl', a, b) / a.shape[1]
    outer = (outer + outer.transpose(0, 2, 1)) / 2
    q = np.diagonal(outer, axis1=1, axis2=2).copy()
    linear = np.concatenate([(a + b).mean(axis=1), np.abs(a - b).mean(axis=1)], axis=1)
    return {'diagonal': q, 'q_ridge': q, 'linear_ridge': linear,
            'bilinear_ridge': outer.reshape(len(a), -1)}


def _fit(name, features, y, train, assess, penalty):
    if name == 'mean':
        return np.tile(y[train].mean(axis=0), (len(assess), 1))
    x = features[name]
    if name == 'diagonal':
        denominator = (x[train] ** 2).sum(axis=0)
        theta = np.divide((x[train] * y[train]).sum(axis=0), denominator * (1 + penalty),
                          out=np.zeros(y.shape[1]), where=denominator > 0)
        return x[assess] * theta
    mean = x[train].mean(axis=0)
    scale = x[train].std(axis=0)
    scale = np.where(scale > 0, scale, 1.)
    xt, xv = (x[train] - mean) / scale, (x[assess] - mean) / scale
    dimension = x.shape[1]
    kt, kv = xt @ xt.T / dimension, xv @ xt.T / dimension
    target_mean = y[train].mean(axis=0)
    alpha = np.linalg.solve(kt + len(train) * penalty * np.eye(len(train)), y[train] - target_mean)
    return target_mean + kv @ alpha


def fit(name, features, y, train, assess, penalty):
    started = time.perf_counter()
    result = _fit(name, features, y, train, assess, penalty)
    COSTS.append({'model': name, 'penalty': penalty, 'train_pairs': len(train),
                  'assess_pairs': len(assess), 'seconds': time.perf_counter() - started})
    return result


def form_arrays(data, pairs, space, input_gems, target_gems):
    names, gems = data['group_names'].tolist(), data['gems'].tolist()
    lookup = {(name, str(gem)): i for i, (name, gem) in enumerate(zip(names, gems))}
    values = data[space]

    def centered(name, group):
        return values[lookup[(name, str(group))]] - values[lookup[('CONTROL', str(group))]]

    aa, bb, yy = [], [], []
    for pair in pairs:
        a, b = pair.split('|')
        aa.append([centered(a, g) for g in input_gems])
        bb.append([centered(b, g) for g in input_gems])
        yy.append(np.mean([centered(pair, g) - centered(a, g) - centered(b, g)
                           for g in target_gems], axis=0))
    return np.asarray(aa), np.asarray(bb), np.asarray(yy)


def main():
    started = time.perf_counter()
    if (OUT / 'PREDICTION_STARTED.json').exists():
        raise FileExistsError('Already initiated; inspect execution before retry')
    freeze = json.loads((OUT / 'FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        assert digest(ROOT / name) == expected, name
    (OUT / 'PREDICTION_STARTED.json').write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat()}))
    data = np.load(OUT / 'STATE_BY_GEM.npz')
    metadata = pd.read_csv(OUT / 'support/SOURCE_PAIR_METADATA.csv')
    pairs = sorted(metadata.loc[metadata.identity_qc_cells > 0, 'pair'].tolist())
    assert len(pairs) == len(set(pairs)) == 73
    folds = np.asarray([hashed(p, 'MAESTRO_MIXED_DIAGONAL_V1|') % 5 for p in pairs])
    order = np.asarray([hashed(p, 'MAESTRO_MIXED_INNER_V1|') for p in pairs], dtype=np.uint64)
    all_scores, all_folds, choices, output = [], [], [], {'pairs': np.asarray(pairs), 'folds': folds}
    for space in ['mean_log1pCP10K', 'mean_CP10K']:
        for direction, inputs, targets in [('A_to_B', [1, 2, 3, 4], [5, 6, 7, 8]),
                                            ('B_to_A', [5, 6, 7, 8], [1, 2, 3, 4])]:
            a, b, y = form_arrays(data, pairs, space, inputs, targets)
            features = design(a, b)
            assert np.isfinite(y).all() and all(np.isfinite(v).all() for v in features.values())
            predictions = {name: np.full_like(y, np.nan) for name in MODELS}
            predictions['additive'] = np.zeros_like(y)
            for fold in range(5):
                train, assess = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
                ordered = train[np.argsort(order[train])]
                boundary = 3 * len(train) // 4
                inner, validation = ordered[:boundary], ordered[boundary:]
                assert not set(train) & set(assess) and not set(inner) & set(validation)
                for name in MODELS:
                    candidates = []
                    for penalty in ([None] if name == 'mean' else GRID):
                        pred = fit(name, features, y, inner, validation, penalty)
                        candidates.append({'penalty': penalty, 'validation_MSE': float(np.mean((pred - y[validation]) ** 2))})
                    selected = min(range(len(candidates)), key=lambda i: candidates[i]['validation_MSE'])
                    parameter = candidates[selected]['penalty']
                    predictions[name][assess] = fit(name, features, y, train, assess, parameter)
                    choices.append({'space': space, 'direction': direction, 'fold': fold, 'model': name,
                                    'train': train.tolist(), 'inner': inner.tolist(), 'validation': validation.tolist(),
                                    'assess': assess.tolist(), 'candidates': candidates, 'selected': selected})
            predictions['fixed_mixture'] = (predictions['diagonal'] + predictions['q_ridge']) / 2
            key = space + '__' + direction
            output[key + '__truth'] = y
            for name, pred in predictions.items():
                assert np.isfinite(pred).all()
                output[key + '__' + name] = pred
                all_scores.append({'space': space, 'direction': direction, 'model': name,
                                   'MSE': float(np.mean((pred - y) ** 2))})
                for fold in range(5):
                    mask = folds == fold
                    all_folds.append({'space': space, 'direction': direction, 'model': name,
                                      'fold': fold, 'pairs': int(mask.sum()), 'MSE': float(np.mean((pred[mask] - y[mask]) ** 2))})
    np.savez_compressed(OUT / 'OOF_STATE.npz', **output)
    pd.DataFrame(all_scores).to_csv(OUT / 'SCORES.csv', index=False)
    pd.DataFrame(all_folds).to_csv(OUT / 'FOLD_SCORES.csv', index=False)
    (OUT / 'SELECTIONS.json').write_text(json.dumps(choices, indent=2))
    (OUT / 'FIT_COSTS.json').write_text(json.dumps(COSTS, indent=2))
    result = {'status': 'COMPLETED_FIXED_RECIPE', 'pairs': len(pairs), 'readouts': 103, 'scores': all_scores,
              'seconds': time.perf_counter() - started, 'functional_outcomes_read': 0,
              'fit_calls': len(COSTS), 'summed_fit_seconds': sum(r['seconds'] for r in COSTS),
              'scope': 'Exploratory source state-structure falsifier, no biological replication, function, agent or RSI gain'}
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
