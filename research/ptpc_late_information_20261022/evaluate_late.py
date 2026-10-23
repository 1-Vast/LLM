"""Fixed development information screen; no causal, updating or RSI claims."""
import hashlib
import json
import os
from pathlib import Path
import time
import warnings

os.environ['OMP_NUM_THREADS'] = '2'
os.environ['OPENBLAS_NUM_THREADS'] = '2'
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_late_information'
PANELS = {'C': ['chem'], 'Craw': ['raw'],
          'E': ['chem', 'early', 'emask'],
          'M': ['chem', 'early', 'emask', 'lmask'],
          'V': ['chem', 'early', 'emask', 'lmask', 'late']}
GRID = [.1, 1., 10.]


def assigned(key, salt, count):
    return int(hashlib.sha256((salt + '|' + key).encode()).hexdigest(), 16) % count


def normalized_block(train, test, kind):
    a, b = train.astype(float), test.astype(float)
    if kind == 'protein':
        keep = np.isfinite(a).any(axis=0)
        a, b = a[:, keep], b[:, keep]
        if a.shape[1] == 0:
            return np.zeros((len(a), 1)), np.zeros((len(b), 1))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            medians = np.nanmedian(a, axis=0)
        a, b = np.where(np.isfinite(a), a, medians), np.where(np.isfinite(b), b, medians)
    if kind == 'chem':
        mean = a.mean(axis=0)
        a, b = a - mean, b - mean
    else:
        scaler = StandardScaler().fit(a)
        a, b = scaler.transform(a), scaler.transform(b)
    energy = np.sqrt(np.mean(np.sum(a * a, axis=1)))
    if energy == 0:
        return np.zeros_like(a), np.zeros_like(b)
    return a / energy, b / energy


def blocks(train, test, arrays):
    result = {'raw': (arrays['chemistry'][train].astype(float), arrays['chemistry'][test].astype(float))}
    result['chem'] = normalized_block(*result['raw'], 'chem')
    for key, source in [('early', 'early'), ('late', 'late')]:
        a, b = arrays[source][train], arrays[source][test]
        result[key] = normalized_block(a, b, 'protein')
        result['emask' if key == 'early' else 'lmask'] = normalized_block(
            (~np.isfinite(a)).astype(float), (~np.isfinite(b)).astype(float), 'mask')
    return result


def panel_features(prepared, panel):
    names = PANELS[panel]
    return tuple(np.concatenate([prepared[name][side] for name in names], axis=1) / np.sqrt(len(names))
                 for side in (0, 1))


def kernels(a, b):
    variance = float(a.var())
    gamma = 1. / (a.shape[1] * variance) if variance > 0 else 1.
    return rbf_kernel(a, a, gamma=gamma), rbf_kernel(b, a, gamma=gamma)


def fit_score(family, c, a, b, y, kernel_pair=None):
    if len(np.unique(y)) < 2:
        return np.full(len(b), float(y.mean())), [], 'source_prevalence_fallback'
    if family == 'logistic':
        model = LogisticRegression(C=c, solver='liblinear', class_weight='balanced',
                                   max_iter=3000, random_state=0)
    else:
        model = SVC(C=c, kernel='precomputed', class_weight='balanced')
        a, b = kernel_pair if kernel_pair is not None else kernels(a, b)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model.fit(a, y)
    return model.decision_function(b), [str(w.message) for w in caught], 'classifier'


def metrics(y, score, ids):
    varied = len(np.unique(y)) == 2
    order = sorted(range(len(y)), key=lambda i: (-float(score[i]), ids[i]))
    return {'n': len(y), 'positive': int(y.sum()),
            'AP': float(average_precision_score(y, score)) if varied else None,
            'AUROC': float(roc_auc_score(y, score)) if varied else None,
            'P_at_5': float(y[order[:min(5, len(y))]].mean())}


def bootstrap(y, predictions, groups):
    rng = np.random.default_rng(20261022)
    unique = sorted(set(groups))
    indices = [np.where(np.array(groups) == group)[0] for group in unique]
    differences = {name: [] for name in ('E', 'M')}
    for _ in range(2000):
        chosen = np.concatenate([indices[i] for i in rng.integers(len(indices), size=len(indices))])
        if len(np.unique(y[chosen])) < 2:
            continue
        value = average_precision_score(y[chosen], predictions['V'][chosen])
        for name in differences:
            differences[name].append(float(value - average_precision_score(y[chosen], predictions[name][chosen])))
    return {name: {'valid_draws': len(values), 'percentile_95': np.quantile(values, [.025, .975]).tolist()}
            for name, values in differences.items()}


def main():
    started = time.perf_counter()
    target = OUT / 'RESULT.json'
    assert not target.exists(), 'No silent rerun'
    freeze = json.loads((OUT / 'PREDICTION_FREEZE.json').read_text('utf-8'))
    for name, expected in freeze['bindings'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    prep = json.loads((OUT / 'PREPARATION.json').read_text('utf-8'))
    with np.load(OUT / 'LATE_PREPARED.npz') as data:
        arrays = {key: data[key] for key in data.files}
    tasks = prep['tasks']
    y = arrays['labels']
    ids, groups = [t['pert_id'] for t in tasks], [t['chemical_group'] for t in tasks]
    outer = np.array([assigned(g, 'PTPC_HCT116_DEV_V1', 5) for g in groups])
    inner = np.array([assigned(g, 'INNER', 3) for g in groups])
    scores = {f: {p: np.full(len(y), np.nan) for p in PANELS} for f in ('logistic', 'rbf')}
    ledger, fold_results, warning_records = [], [], []
    for fold in range(5):
        train, test = np.where(outer != fold)[0], np.where(outer == fold)[0]
        assert set(np.array(groups)[train]).isdisjoint(np.array(groups)[test])
        tuning = {(f, p, c): [] for f in scores for p in PANELS for c in GRID}
        for inner_fold in range(3):
            source, validation = train[inner[train] != inner_fold], train[inner[train] == inner_fold]
            if not len(source) or not len(validation) or len(np.unique(y[validation])) < 2:
                ledger.append({'outer': fold, 'inner': inner_fold, 'status': 'unscorable_validation_skipped'})
                continue
            prepared = blocks(source, validation, arrays)
            for panel in PANELS:
                a, b = panel_features(prepared, panel)
                kernel_pair = kernels(a, b)
                for family in scores:
                    for c in GRID:
                        prediction, notes, mode = fit_score(family, c, a, b, y[source], kernel_pair)
                        ap = float(average_precision_score(y[validation], prediction))
                        tuning[family, panel, c].append(ap)
                        ledger.append({'outer': fold, 'inner': inner_fold, 'family': family, 'panel': panel,
                                       'C': c, 'n_train': len(source), 'n_test': len(validation), 'mode': mode,
                                       'features': a.shape[1], 'blocks': len(PANELS[panel]), 'AP': ap})
                        warning_records.extend({'outer': fold, 'inner': inner_fold, 'family': family,
                                                'panel': panel, 'C': c, 'message': note} for note in notes)
        prepared = blocks(train, test, arrays)
        for panel in PANELS:
            a, b = panel_features(prepared, panel)
            kernel_pair = kernels(a, b)
            for family in scores:
                choices = [{'C': c, 'inner_AP': tuning[family, panel, c],
                            'mean_AP': float(np.mean(tuning[family, panel, c])) if tuning[family, panel, c] else None}
                           for c in GRID]
                valid = [row for row in choices if row['mean_AP'] is not None]
                c = max(valid, key=lambda row: row['mean_AP'])['C'] if valid else GRID[0]
                prediction, notes, mode = fit_score(family, c, a, b, y[train], kernel_pair)
                assert np.isfinite(prediction).all()
                scores[family][panel][test] = prediction
                row = {'outer': fold, 'inner': None, 'family': family, 'panel': panel, 'C': c,
                       'n_train': len(train), 'n_test': len(test), 'mode': mode,
                       'features': a.shape[1], 'blocks': len(PANELS[panel])}
                ledger.append(row)
                fold_results.append({**row, 'tuning': choices, **metrics(y[test], prediction, np.array(ids)[test])})
                warning_records.extend({'outer': fold, 'inner': None, 'family': family,
                                        'panel': panel, 'C': c, 'message': note} for note in notes)
        print(f'outer {fold + 1}/5 complete; ledger_entries={len(ledger)}', flush=True)
    pooled = {f: {p: metrics(y, values, ids) for p, values in panels.items()} for f, panels in scores.items()}
    gates = {}
    for family in scores:
        differences = {p: pooled[family]['V']['AP'] - pooled[family][p]['AP'] for p in ('C', 'Craw', 'E', 'M')}
        fold_ap = {(r['panel'], r['outer']): r['AP'] for r in fold_results if r['family'] == family}
        directions = {p: sum(fold_ap['V', k] is not None and fold_ap[p, k] is not None
                             and fold_ap['V', k] > fold_ap[p, k] for k in range(5)) for p in differences}
        gates[family] = {'AP_differences': differences, 'positive_folds': directions,
                         'pass': all(v is not None for v in fold_ap.values())
                         and min(differences.values()) >= .02 and min(directions.values()) >= 4}
    result = {'scope': 'HCT116 paired measured-state development information only; primary logistic, RBF sensitivity',
              'pooled': pooled, 'fold_results': fold_results, 'gates': gates,
              'macro_AP': {f: {p: float(np.mean([r['AP'] for r in fold_results
                                                if r['family'] == f and r['panel'] == p and r['AP'] is not None]))
                                for p in PANELS} for f in scores},
              'bootstrap': {f: bootstrap(y, p, groups) for f, p in scores.items()},
              'predictions': [{'pert_id': ids[i], 'chemical_group': groups[i], 'label': int(y[i]), 'fold': int(outer[i]),
                               'scores': {f: {p: float(v[i]) for p, v in panels.items()} for f, panels in scores.items()}}
                              for i in range(len(y))],
              'fit_ledger': ledger, 'warnings': warning_records,
              'classifier_fit_count': sum(r.get('mode') == 'classifier' for r in ledger),
              'fallback_count': sum(r.get('mode') == 'source_prevalence_fallback' for r in ledger),
              'unscorable_inner_splits': sum(r.get('status') == 'unscorable_validation_skipped' for r in ledger),
              'wall_seconds': time.perf_counter() - started}
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'pooled': pooled, 'gates': gates, 'classifier_fits': result['classifier_fit_count'],
                      'warnings': len(warning_records), 'wall_seconds': result['wall_seconds']}, indent=2))


if __name__ == '__main__':
    with threadpool_limits(limits=2):
        main()
