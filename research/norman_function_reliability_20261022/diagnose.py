"""Nested source-only OOF functional residual and replicate moment diagnostic."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_function_reliability'
INP = ROOT / 'log/20261022/norman_numeric_qualification'
spec = importlib.util.spec_from_file_location('completion', ROOT / 'research/norman_baseline_calibration_20261022/calibrate.py')
completion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(completion)


def fold_id(pair):
    return int.from_bytes(hashlib.sha256(('MAESTRO_NORMAN_RELIABILITY_V1|' + pair).encode()).digest()[:8], 'big') % 5


def main():
    start = time.perf_counter()
    qualification = json.loads((OUT / 'QUALIFICATION.json').read_text())
    assert qualification['status'] == 'PASS_ENDPOINT_IDENTITY'
    assert qualification['max_separately_averaged_replicates_difference'] <= 1e-10
    data = pd.read_csv(OUT / 'SOURCE_REPLICATES.csv')
    assert len(data) == data.pair.nunique() == 3160 and data.gene_a.lt(data.gene_b).all()
    memberships = pd.read_csv(ROOT / 'log/20261022/norman_functional_contract/PAIR_SPLITS.csv').set_index('pair')
    assert memberships.loc[data.pair, 'split'].eq('source').all()
    order = data.pair.map(memberships.source_order).to_numpy()
    folds = data.pair.map(fold_id).to_numpy()
    rna = np.load(INP / 'SINGLE_RNA_FEATURES.npz')
    genes, features = rna['genes'].tolist(), rna['features']
    n = len(genes)
    lookup = {g: i for i, g in enumerate(genes)}
    a, b = data.gene_a.map(lookup).to_numpy(), data.gene_b.map(lookup).to_numpy()
    assert n == 103 and np.isfinite(a).all() and np.isfinite(b).all()
    y = data.growth.to_numpy()
    rep1, rep2 = data.replicate1.to_numpy(), data.replicate2.to_numpy()
    assert np.isfinite(np.concatenate([y, rep1, rep2])).all()
    priors = pd.read_csv(INP / 'SINGLE_GROWTH_PRIORS.csv').set_index('gene').average_fitness
    fa, fb = data.gene_a.map(priors).to_numpy(), data.gene_b.map(priors).to_numpy()
    q = np.column_stack([np.ones(len(data)), fa + fb, fa * fb, fa ** 2 + fb ** 2])
    u, singular, _ = np.linalg.svd(features - features.mean(axis=0), full_matrices=False)
    embedding = u[:, :32] * singular[:32]
    pair_rna = np.concatenate([embedding[a] + embedding[b], np.abs(embedding[a] - embedding[b]), embedding[a] * embedding[b]], axis=1)
    identity = np.eye(n)[a] + np.eye(n)[b]
    inputs = {'direct_RNA_ridge': pair_rna, 'fusion_ridge': np.concatenate([pair_rna, identity], axis=1)}
    corr = np.corrcoef(features)
    eig, vec = np.linalg.eigh(corr)
    sides = {'identity_nuclear': np.eye(n), 'RNA_nuclear': (vec * np.sqrt(np.maximum(eig, 0))) @ vec.T}
    predictions = {name: np.full(len(data), np.nan) for name in ['quadratic', *inputs, *sides]}
    costs, selections, fold_rows = [], [], []

    def baseline(train):
        started = time.perf_counter()
        base = q @ np.linalg.lstsq(q[train], y[train], rcond=None)[0]
        costs.append({'kind': 'quadratic', 'train_n': len(train), 'seconds': time.perf_counter() - started})
        return base

    def fit(name, parameter, train, assess, base):
        started = time.perf_counter()
        residual = y[train] - base[train]
        info = {}
        if name in inputs:
            scaler = StandardScaler().fit(inputs[name][train])
            xtrain = scaler.transform(inputs[name][train])
            model = Ridge(alpha=parameter).fit(xtrain, residual)
            pred = base[assess] + model.predict(scaler.transform(inputs[name][assess]))
        else:
            matrix, info = completion.complete(residual, a[train], b[train], sides[name], parameter, n)
            pred = base[assess] + matrix[a[assess], b[assess]]
        costs.append({'kind': name, 'parameter': parameter, 'train_n': len(train), 'seconds': time.perf_counter() - started, **info})
        return pred, info

    for fold in range(5):
        assess = np.flatnonzero(folds == fold)
        train = np.flatnonzero(folds != fold)
        train = train[np.argsort(order[train])]
        boundary = 3 * len(train) // 4
        inner_train, validation = train[:boundary], train[boundary:]
        assert not set(inner_train) & set(validation) and not set(train) & set(assess)
        base_inner, base_full = baseline(inner_train), baseline(train)
        predictions['quadratic'][assess] = base_full[assess]
        for name in [*inputs, *sides]:
            menu = [.1, 10., 1000.] if name in inputs else [.0005, .05, 5.]
            candidates = []
            for parameter in menu:
                pred, info = fit(name, parameter, inner_train, validation, base_inner)
                candidates.append({'parameter': parameter, 'mse': float(np.mean((pred - y[validation]) ** 2)), **info})
            best = min(candidates, key=lambda row: row['mse'])
            pred, info = fit(name, best['parameter'], train, assess, base_full)
            assert np.isfinite(pred).all()
            predictions[name][assess] = pred
            selections.append({'fold': fold, 'model': name, 'inner_train_pairs': data.loc[inner_train, 'pair'].tolist(),
                               'inner_validation_pairs': data.loc[validation, 'pair'].tolist(), 'candidates': candidates,
                               'selected_parameter': best['parameter'], 'outer_refit': info})
        for name, pred in predictions.items():
            row = {'fold': fold, 'model': name, 'assessed_pairs': len(assess), 'train_pairs': len(train),
                   'heldout_growth_mse': float(np.mean((pred[assess] - y[assess]) ** 2))}
            fold_rows.append(row)
            print(json.dumps(row), flush=True)
    result = data.copy()
    result['fold'] = folds
    disagreement = rep1 - rep2
    reference = np.mean(disagreement ** 2) / 4
    moments = []
    quartile_rows = []
    quartiles = pd.qcut(np.abs(disagreement), 4, labels=False, duplicates='drop')
    for name, pred in predictions.items():
        assert np.isfinite(pred).all()
        result['prediction_' + name] = pred
        e1, e2 = rep1 - pred, rep2 - pred
        cross = np.mean(e1 * e2)
        average_mse = np.mean(((rep1 + rep2) / 2 - pred) ** 2)
        assert abs(average_mse - cross - reference) < 1e-14
        moments.append({'model': name, 'growth_mse': float(np.mean((y - pred) ** 2)),
                        'replicate_mean_mse': float(average_mse), 'residual_cross_product': float(cross),
                        'replicate_difference_moment_div4': float(reference),
                        'replicate1_residual_mean': float(e1.mean()), 'replicate2_residual_mean': float(e2.mean()),
                        'centered_residual_correlation': float(np.corrcoef(e1, e2)[0, 1]),
                        'absolute_error_vs_absolute_disagreement_spearman': float(spearmanr(np.abs(y - pred), np.abs(disagreement)).statistic)})
        for quartile in np.unique(quartiles):
            mask = quartiles == quartile
            quartile_rows.append({'model': name, 'disagreement_quartile': int(quartile), 'pairs': int(mask.sum()),
                                  'growth_mse': float(np.mean((y[mask] - pred[mask]) ** 2)),
                                  'mean_absolute_replicate_difference': float(np.mean(np.abs(disagreement[mask])))})
    result.to_csv(OUT / 'OOF_SOURCE.csv', index=False)
    pd.DataFrame(moments).to_csv(OUT / 'MOMENTS.csv', index=False)
    pd.DataFrame(fold_rows).to_csv(OUT / 'FOLD_SCORES.csv', index=False)
    pd.DataFrame(quartile_rows).to_csv(OUT / 'DISAGREEMENT_QUARTILES.csv', index=False)
    (OUT / 'SELECTIONS.json').write_text(json.dumps(selections))
    (OUT / 'COSTS.json').write_text(json.dumps(costs, indent=2))
    summary = {'status': 'EXECUTED_SOURCE_DIAGNOSTIC', 'utc': datetime.now(timezone.utc).isoformat(),
               'wall_seconds': time.perf_counter() - start, 'source_pairs': len(data),
               'fold_sizes': {int(f): int(np.sum(folds == f)) for f in range(5)},
               'fit_counts': dict(Counter(c['kind'] for c in costs)), 'fit_count': len(costs),
               'selected_nuclear_objective_stop_unmet': sum(not s['outer_refit'].get('converged', True) for s in selections),
               'replicate1_mean': float(rep1.mean()), 'replicate2_mean': float(rep2.mean()),
               'mean_screen_offset': float(disagreement.mean()),
               'replicate_difference_moment_div4': float(reference),
               'pair_weighted_guide_replicate_mse': float(data.within_pair_guide_replicate_mse.mean()),
               'mean_within_pair_guide_sd_rep1': float(data.within_pair_guide_sd_rep1.mean()),
               'mean_within_pair_guide_sd_rep2': float(data.within_pair_guide_sd_rep2.mean()),
               'development_values_loaded': 0, 'protected_values_loaded': 0,
               'scope': 'Descriptive algebraic moments, not noise variance/oracle ceiling/biological structure or predictive headroom'}
    (OUT / 'RESULT.json').write_text(json.dumps(summary, indent=2))
    print(pd.DataFrame(moments).to_string(index=False), flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
