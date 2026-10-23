"""Common source-pair OOF comparison of two explicitly different functional estimands."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_matched_guide'
INP = ROOT / 'log/20261022/norman_numeric_qualification'
spec = importlib.util.spec_from_file_location('completion', ROOT / 'research/norman_baseline_calibration_20261022/calibrate.py')
completion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(completion)


def main():
    start = time.perf_counter()
    assert json.loads((OUT / 'QUALIFICATION.json').read_text())['status'] == 'LOCAL_SOURCE_NUMERICAL_EQUIVALENCE_SUPPORTED'
    data = pd.read_csv(OUT / 'SOURCE_MATCHED_ENDPOINT.csv')
    assert len(data) == data.pair.nunique() == 3107 and data.both_orientations_finite.all()
    assert data.gene_a.lt(data.gene_b).all() and (data.pair == data.gene_a + '|' + data.gene_b).all()
    membership = pd.read_csv(ROOT / 'log/20261022/norman_functional_contract/PAIR_SPLITS.csv').set_index('pair')
    assert membership.loc[data.pair, 'split'].eq('source').all()
    order = data.pair.map(membership.source_order).to_numpy()
    folds = np.array([int.from_bytes(hashlib.sha256(('MAESTRO_NORMAN_RELIABILITY_V1|' + p).encode()).digest()[:8], 'big') % 5 for p in data.pair])
    genes = sorted(set(data.gene_a) | set(data.gene_b))
    assert len(genes) == 102
    lookup = {g: i for i, g in enumerate(genes)}
    a, b = data.gene_a.map(lookup).to_numpy(), data.gene_b.map(lookup).to_numpy()
    raw = np.load(INP / 'SINGLE_RNA_FEATURES.npz')
    feature_map = {g: f for g, f in zip(raw['genes'].tolist(), raw['features'])}
    features = np.stack([feature_map[g] for g in genes])
    assert np.isfinite(features).all()
    u, singular, _ = np.linalg.svd(features - features.mean(axis=0), full_matrices=False)
    embedding = u[:, :32] * singular[:32]
    direct = np.concatenate([embedding[a] + embedding[b], np.abs(embedding[a] - embedding[b]), embedding[a] * embedding[b]], axis=1)
    identity = np.eye(len(genes))[a] + np.eye(len(genes))[b]
    xs = {'direct_RNA_ridge': direct, 'fusion_ridge': np.concatenate([direct, identity], axis=1)}
    corr = np.corrcoef(features)
    eig, vec = np.linalg.eigh(corr)
    sides = {'identity_nuclear': np.eye(len(genes)), 'RNA_nuclear': (vec * np.sqrt(np.maximum(eig, 0))) @ vec.T}
    average_priors = pd.read_csv(INP / 'SINGLE_GROWTH_PRIORS.csv').set_index('gene').average_fitness
    chosen_priors = pd.read_csv(OUT / 'CHOSEN_SINGLE_PRIORS.csv').set_index('gene').candidate_chosen_prior
    assert chosen_priors.index.is_unique
    costs, selections, summaries, fold_scores = [], [], [], []
    output = data[['pair', 'gene_a', 'gene_b']].copy()
    output['fold'] = folds
    for endpoint, target, priors in [('average', 'original_gene_average_growth', average_priors),
                                     ('chosen', 'chosen_processed_growth', chosen_priors)]:
        y = data[target].to_numpy()
        fa, fb = data.gene_a.map(priors).to_numpy(), data.gene_b.map(priors).to_numpy()
        assert np.isfinite(np.concatenate([y, fa, fb])).all()
        q = np.column_stack([np.ones(len(data)), fa + fb, fa * fb, fa ** 2 + fb ** 2])
        predictions = {name: np.full(len(data), np.nan) for name in ['quadratic', *xs, *sides]}

        def base(train):
            started = time.perf_counter()
            pred = q @ np.linalg.lstsq(q[train], y[train], rcond=None)[0]
            costs.append({'endpoint': endpoint, 'kind': 'quadratic', 'train_n': len(train), 'seconds': time.perf_counter() - started})
            return pred

        def fit(name, parameter, train, assess, baseline):
            started = time.perf_counter()
            residual = y[train] - baseline[train]
            info = {}
            if name in xs:
                scaler = StandardScaler().fit(xs[name][train])
                model = Ridge(alpha=parameter).fit(scaler.transform(xs[name][train]), residual)
                pred = baseline[assess] + model.predict(scaler.transform(xs[name][assess]))
            else:
                matrix, info = completion.complete(residual, a[train], b[train], sides[name], parameter, len(genes))
                pred = baseline[assess] + matrix[a[assess], b[assess]]
            costs.append({'endpoint': endpoint, 'kind': name, 'parameter': parameter, 'train_n': len(train), 'seconds': time.perf_counter() - started, **info})
            return pred, info

        for fold in range(5):
            assess, train = np.flatnonzero(folds == fold), np.flatnonzero(folds != fold)
            train = train[np.argsort(order[train])]
            boundary = 3 * len(train) // 4
            inner, validation = train[:boundary], train[boundary:]
            assert not set(train) & set(assess) and not set(inner) & set(validation)
            inner_base, final_base = base(inner), base(train)
            predictions['quadratic'][assess] = final_base[assess]
            for name in [*xs, *sides]:
                menu = [.1, 10., 1000.] if name in xs else [.0005, .05, 5.]
                candidates = []
                for parameter in menu:
                    pred, info = fit(name, parameter, inner, validation, inner_base)
                    candidates.append({'parameter': parameter, 'mse': float(np.mean((pred - y[validation]) ** 2)), **info})
                best = min(candidates, key=lambda c: c['mse'])
                pred, info = fit(name, best['parameter'], train, assess, final_base)
                predictions[name][assess] = pred
                selections.append({'endpoint': endpoint, 'fold': fold, 'model': name,
                    'inner_pairs': data.loc[inner, 'pair'].tolist(), 'validation_pairs': data.loc[validation, 'pair'].tolist(),
                    'candidates': candidates, 'selected_parameter': best['parameter'], 'outer_refit': info})
            for name, pred in predictions.items():
                fold_scores.append({'endpoint': endpoint, 'fold': fold, 'model': name, 'pairs': len(assess),
                                    'mse': float(np.mean((pred[assess] - y[assess]) ** 2))})
            print(json.dumps({'endpoint': endpoint, 'fold': fold, 'completed': True}), flush=True)
        q_mse = np.mean((predictions['quadratic'] - y) ** 2)
        output['truth_' + endpoint] = y
        for name, pred in predictions.items():
            assert np.isfinite(pred).all()
            output[f'prediction_{endpoint}_{name}'] = pred
            mse = np.mean((pred - y) ** 2)
            summaries.append({'endpoint': endpoint, 'model': name, 'mse': float(mse),
                              'endpoint_variance': float(np.var(y)), 'mse_over_quadratic_mse': float(mse / q_mse)})
    output.to_csv(OUT / 'OOF_COMMON_PANEL.csv', index=False)
    summary = pd.DataFrame(summaries)
    summary.to_csv(OUT / 'COMMON_PANEL_SCORES.csv', index=False)
    pd.DataFrame(fold_scores).to_csv(OUT / 'COMMON_PANEL_FOLDS.csv', index=False)
    (OUT / 'SELECTIONS.json').write_text(json.dumps(selections))
    (OUT / 'COSTS.json').write_text(json.dumps(costs, indent=2))
    gains = {}
    for endpoint in ['average', 'chosen']:
        sub = summary[summary.endpoint.eq(endpoint)].set_index('model')
        no_rna, rna = sub.loc['identity_nuclear', 'mse'], sub.loc['RNA_nuclear', 'mse']
        gains[endpoint] = {'relative_RNA_gain': float(1 - rna / no_rna), 'absolute_RNA_gain': float(no_rna - rna)}
    delta = gains['chosen']['relative_RNA_gain'] - gains['average']['relative_RNA_gain']
    result = {'status': 'EXECUTED_SOURCE_ENDPOINT_COMPARISON', 'utc': datetime.now(timezone.utc).isoformat(),
              'wall_seconds': time.perf_counter() - start, 'fit_count': len(costs),
              'fit_counts': dict(Counter(c['kind'] for c in costs)), 'genes': len(genes), 'source_pairs': len(data),
              'gains': gains, 'chosen_minus_average_relative_gain': delta,
              'fixed_prediction_hypothesis': 'DESCRIPTIVE_DIRECTION_SUPPORTED' if delta > 0 else 'STOP_FIXED_ALIGNMENT_BENEFIT_PREDICTION',
              'selected_nuclear_stop_heuristic_unmet': sum(not s['outer_refit'].get('converged', True) for s in selections),
              'development_values_loaded': 0, 'protected_values_loaded': 0,
              'scope': 'Joint estimand+prior comparison, not causal guide-alignment, method superiority or noise correction'}
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
