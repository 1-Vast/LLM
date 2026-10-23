"""Grouped nested development baselines; no model update or RSI claim."""
import hashlib
import json
import os
from pathlib import Path
import time
import warnings

os.environ['OMP_NUM_THREADS'] = '2'
os.environ['OPENBLAS_NUM_THREADS'] = '2'
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_update_opportunity'
GRID = [.01, .1, 1.]
MODELS = ['prior', 'chemistry', 'chemistry_raw', 'proteins', 'joint', 'missingness', 'protein_masked', 'joint_masked']


def assigned(key, salt, number):
    return int(hashlib.sha256((salt + '|' + key).encode()).hexdigest(), 16) % number


def features(name, train, test, chemical, protein):
    blocks_train, blocks_test = [], []
    if name in ('chemistry', 'chemistry_raw', 'joint', 'joint_masked'):
        divisor = 1. if name == 'chemistry_raw' else np.sqrt(chemical.shape[1])
        blocks_train.append(chemical[train] / divisor)
        blocks_test.append(chemical[test] / divisor)
    if name in ('proteins', 'joint', 'protein_masked', 'joint_masked'):
        a, b = protein[train], protein[test]
        keep = np.isfinite(a).any(axis=0)
        assert keep.any(), 'No train-observed protein features'
        a, b = a[:, keep], b[:, keep]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            medians = np.nanmedian(a, axis=0)
        a = np.where(np.isfinite(a), a, medians)
        b = np.where(np.isfinite(b), b, medians)
        scaler = StandardScaler().fit(a)
        blocks_train.append(scaler.transform(a) / np.sqrt(a.shape[1]))
        blocks_test.append(scaler.transform(b) / np.sqrt(a.shape[1]))
    if name in ('missingness', 'protein_masked', 'joint_masked'):
        a, b = (~np.isfinite(protein[train])).astype(float), (~np.isfinite(protein[test])).astype(float)
        scaler = StandardScaler().fit(a)
        blocks_train.append(scaler.transform(a) / np.sqrt(a.shape[1]))
        blocks_test.append(scaler.transform(b) / np.sqrt(a.shape[1]))
    return np.concatenate(blocks_train, axis=1), np.concatenate(blocks_test, axis=1)


def fit_predict(name, c, train, test, chemical, protein, labels):
    if name == 'prior' or len(np.unique(labels[train])) < 2:
        return np.full(len(test), labels[train].mean()), []
    a, b = features(name, train, test, chemical, protein)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', ConvergenceWarning)
        model = LogisticRegression(C=c, class_weight='balanced', solver='liblinear', max_iter=1000, random_state=0).fit(a, labels[train])
    return model.predict_proba(b)[:, 1], [str(w.message) for w in caught]


def metrics(y, score, identifiers):
    varied = len(np.unique(y)) == 2
    order = sorted(range(len(y)), key=lambda i: (-float(score[i]), identifiers[i]))
    return {'n': len(y), 'positive': int(y.sum()), 'prevalence': float(y.mean()),
            'average_precision': float(average_precision_score(y, score)) if varied else None,
            'auroc': float(roc_auc_score(y, score)) if varied else None,
            'brier': float(brier_score_loss(y, score)),
            'precision_at_5': float(y[order[:min(5, len(y))]].mean())}


def select(name, train, inner, chemical, protein, labels):
    if name == 'prior':
        return None, [], []
    candidates, messages = [], []
    for c in GRID:
        scores = []
        for fold in range(3):
            validation = [i for i in train if inner[i] == fold]
            fit = [i for i in train if inner[i] != fold]
            if not validation or not fit or len(np.unique(labels[validation])) < 2:
                continue
            prediction, notes = fit_predict(name, c, fit, validation, chemical, protein, labels)
            messages.extend(notes)
            scores.append(float(average_precision_score(labels[validation], prediction)))
        candidates.append({'C': c, 'source_fold_AP': scores, 'mean_AP': float(np.mean(scores)) if scores else None})
    valid = [r for r in candidates if r['mean_AP'] is not None]
    chosen = max(valid, key=lambda r: r['mean_AP'])['C'] if valid else GRID[0]
    return chosen, candidates, messages


def main():
    started = time.perf_counter()
    target = OUT / 'BASELINE_RESULT.json'
    assert not target.exists(), 'No silent rerun or overwriting'
    prep = json.loads((OUT / 'BASELINE_PREPARATION.json').read_text())
    path = OUT / 'BASELINE_PREPARED.npz'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == prep['prepared_sha256']
    with np.load(path) as data:
        chemical, protein, labels = data['chemistry'], data['proteins'], data['labels']
    tasks = prep['tasks']
    outer = np.array([assigned(t['chemical_group'], 'PTPC_HCT116_DEV_V1', 5) for t in tasks])
    inner = np.array([assigned(t['chemical_group'], 'INNER', 3) for t in tasks])
    predictions = {name: np.full(len(labels), np.nan) for name in MODELS}
    rows, model_folds, notes = [], [], []
    for fold in range(5):
        train, test = np.where(outer != fold)[0].tolist(), np.where(outer == fold)[0].tolist()
        assert train and test
        assert set(tasks[i]['chemical_group'] for i in train).isdisjoint(tasks[i]['chemical_group'] for i in test)
        for name in MODELS:
            c, tuning, messages = select(name, train, inner, chemical, protein, labels)
            prediction, warning_messages = fit_predict(name, c, train, test, chemical, protein, labels)
            assert np.all(np.isfinite(prediction)) and np.all((prediction >= 0) & (prediction <= 1))
            predictions[name][test] = prediction
            notes.extend(messages + warning_messages)
            model_folds.append({'fold': fold, 'model': name, 'C': c, 'tuning': tuning,
                                'source_n': len(train), 'source_positive': int(labels[train].sum()),
                                'training_mode': 'prior' if name == 'prior' else ('single_class_prevalence_fallback' if len(np.unique(labels[train])) < 2 else 'logistic'),
                                **metrics(labels[test], prediction, [tasks[i]['pert_id'] for i in test])})
        print(f'fold {fold + 1}/5 complete', flush=True)
    pooled = {name: metrics(labels, score, [t['pert_id'] for t in tasks]) for name, score in predictions.items()}
    for i, task in enumerate(tasks):
        rows.append({'pert_id': task['pert_id'], 'chemical_group': task['chemical_group'], 'fold': int(outer[i]),
                     'label': int(labels[i]), 'prediction': {name: float(values[i]) for name, values in predictions.items()}})
    result = {'scope': 'Exploratory HCT116-only six-hour measured-state annotation baselines; no cell-background confirmation or novel rule',
              'pooled': pooled, 'model_folds': model_folds, 'predictions': rows,
              'warnings': notes, 'wall_seconds': time.perf_counter() - started}
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'pooled': pooled, 'warning_count': len(notes), 'wall_seconds': result['wall_seconds']}, indent=2))


if __name__ == '__main__':
    main()
