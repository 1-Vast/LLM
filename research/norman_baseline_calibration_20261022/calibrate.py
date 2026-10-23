"""Finite ordinary baseline calibration; protected outcomes not loaded."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
INP = ROOT / 'log/20261022/norman_numeric_qualification'
OUT = ROOT / 'log/20261022/norman_baseline_calibration'


def complete(residual, a, b, side, penalty, n, max_iter=2000):
    """FISTA solves the same nuclear-norm side-information objective as source Maxide."""
    matrix = np.zeros((n, n))
    observed = np.zeros((n, n), dtype=bool)
    matrix[a, b] = matrix[b, a] = residual
    observed[a, b] = observed[b, a] = True
    z = np.zeros((n, n))
    extrapolated = z.copy()
    momentum = 1.0
    lipschitz = max(np.linalg.norm(side, 2) ** 4, 1e-12)
    previous = np.inf
    converged = False
    for iteration in range(1, max_iter + 1):
        prediction = side @ extrapolated @ side.T
        gradient = side.T @ np.where(observed, prediction - matrix, 0) @ side
        u, singular, vt = np.linalg.svd(extrapolated - gradient / lipschitz, full_matrices=False)
        shrunk = np.maximum(singular - penalty / lipschitz, 0)
        updated = (u * shrunk) @ vt
        objective = .5 * np.square((side @ updated @ side.T - matrix)[observed]).sum() + penalty * shrunk.sum()
        if iteration > 20 and abs(previous - objective) < 1e-5 * max(objective, 1e-12):
            z = updated
            converged = True
            break
        next_momentum = (1 + np.sqrt(1 + 4 * momentum * momentum)) / 2
        extrapolated = updated + (momentum - 1) / next_momentum * (updated - z)
        z = updated
        momentum = next_momentum
        previous = objective
    return side @ z @ side.T, {'iterations': iteration, 'converged': converged, 'objective': float(objective)}


def main():
    assert json.loads((INP / 'RNA_QC_REPORT.json').read_text())['status'] == 'PASS'
    data = np.load(INP / 'SINGLE_RNA_FEATURES.npz')
    genes, features = data['genes'].tolist(), data['features']
    n = len(genes)
    lookup = {g: i for i, g in enumerate(genes)}
    pairs = pd.read_csv(INP / 'FUNCTION_SOURCE_DEVELOPMENT.csv')
    assert set(pairs['split']) <= {'source', 'development'}
    pairs = pairs[pairs.gene_a.isin(lookup) & pairs.gene_b.isin(lookup)].reset_index(drop=True)
    source = pairs.index[pairs.split.eq('source')].to_numpy()
    source = np.array(sorted(source, key=lambda k: pairs.loc[k, 'source_order']))
    development = pairs.index[pairs.split.eq('development')].to_numpy()
    a, b = pairs.gene_a.map(lookup).to_numpy(), pairs.gene_b.map(lookup).to_numpy()
    priors = pd.read_csv(INP / 'SINGLE_GROWTH_PRIORS.csv').set_index('gene').average_fitness
    fa = pairs.gene_a.map(priors).to_numpy()
    fb = pairs.gene_b.map(priors).to_numpy()
    quadratic = np.column_stack([np.ones(len(pairs)), fa + fb, fa * fb, fa ** 2 + fb ** 2])
    y = pairs.growth.to_numpy()
    # No double RNA or any functional labels enter these seen-gene transforms.
    centered = features - features.mean(axis=0)
    u, singular, _ = np.linalg.svd(centered, full_matrices=False)
    embedding = u[:, :32] * singular[:32]
    rna = np.concatenate([embedding[a] + embedding[b], np.abs(embedding[a] - embedding[b]),
                          embedding[a] * embedding[b]], axis=1)
    identity = np.eye(n)[a] + np.eye(n)[b]
    corr = np.corrcoef(features)
    assert np.isfinite(corr).all()
    eigenvalues, eigenvectors = np.linalg.eigh(corr)
    rna_side = (eigenvectors * np.sqrt(np.maximum(eigenvalues, 0))) @ eigenvectors.T
    results = []
    predictions = []
    for budget in [128, 512, 2048]:
        train = source[:budget]
        assert len(train) == budget
        base_coefficients = np.linalg.lstsq(quadratic[train], y[train], rcond=None)[0]
        base = quadratic @ base_coefficients
        residual = y[train] - base[train]

        def record(model, parameter, prediction, started, extra=None):
            mse = float(np.mean((prediction[development] - y[development]) ** 2))
            row = {'budget_source_pairs': budget, 'model': model, 'parameter': parameter,
                   'development_mse': mse, 'seconds': time.perf_counter() - started, **(extra or {})}
            results.append(row)
            predictions.append({'budget': budget, 'model': model, 'parameter': parameter,
                                'pred': prediction[development].tolist()})
            print(json.dumps(row), flush=True)

        started = time.perf_counter()
        record('mean', 'none', np.full(len(pairs), y[train].mean()), started)
        record('quadratic_single_growth', 'none', base, started)
        for name, x in [('identity_residual_ridge', identity), ('RNA_direct_residual_ridge', rna),
                        ('identity_RNA_fusion_residual_ridge', np.concatenate([identity, rna], axis=1))]:
            for alpha in [.1, 10., 1000.]:
                started = time.perf_counter()
                scaler = StandardScaler().fit(x[train])
                xx = scaler.transform(x)
                fit = Ridge(alpha=alpha).fit(xx[train], residual)
                record(name, str(alpha), base + fit.predict(xx), started)
        for name, side in [('identity_nuclear_completion', np.eye(n)), ('RNA_side_nuclear_completion', rna_side)]:
            for penalty in [.0005, .05, 5.]:
                started = time.perf_counter()
                recovered, info = complete(residual, a[train], b[train], side, penalty, n)
                record(name, str(penalty), base + recovered[a, b], started, info)
        pd.DataFrame(results).to_csv(OUT / 'ALL_SCORES.csv', index=False)
    best = pd.DataFrame(results).sort_values('development_mse').groupby(['budget_source_pairs', 'model'], sort=False).first().reset_index()
    best.to_csv(OUT / 'DEVELOPMENT_SELECTED.csv', index=False)
    (OUT / 'DEVELOPMENT_PREDICTIONS.json').write_text(json.dumps({'pairs': pairs.loc[development, 'pair'].tolist(),
        'truth': y[development].tolist(), 'predictions': predictions}))
    report = {'status': 'EXECUTED_DEVELOPMENT_ONLY', 'utc': datetime.now(timezone.utc).isoformat(),
              'gene_count': n, 'source_pairs': len(source), 'development_pairs': len(development),
              'protected_pairs_loaded': 0, 'candidate_evaluations': len(results),
              'scope': 'Ordinary calibration; development selection not independent performance validation',
              'selected': best.to_dict(orient='records')}
    (OUT / 'RESULT.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
