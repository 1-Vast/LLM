"""Common-start conventional kernel updates and strong union-refit controls."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_feedback_transport'
INP = ROOT / 'log/20261022/norman_numeric_qualification'
spec = importlib.util.spec_from_file_location('calibration', ROOT / 'research/norman_baseline_calibration_20261022/calibrate.py')
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)
PARAMS = [(w, p) for w in [0., .5, 1.] for p in [.001, .1, 10.]]


def pair_kernel(gene_kernel, a, b, c, d):
    raw = .5 * (gene_kernel[a[:, None], c] * gene_kernel[b[:, None], d]
                + gene_kernel[a[:, None], d] * gene_kernel[b[:, None], c])
    diag_left = .5 * (gene_kernel[a, a] * gene_kernel[b, b] + gene_kernel[a, b] ** 2)
    diag_right = .5 * (gene_kernel[c, c] * gene_kernel[d, d] + gene_kernel[c, d] ** 2)
    return raw / np.sqrt(diag_left[:, None] * diag_right)


def main():
    start = time.perf_counter()
    data = np.load(INP / 'SINGLE_RNA_FEATURES.npz')
    genes, features = data['genes'].tolist(), data['features']
    n = len(genes)
    assert len(set(genes)) == n and np.isfinite(features).all()
    lookup = {g: i for i, g in enumerate(genes)}
    pairs = pd.read_csv(INP / 'FUNCTION_SOURCE_DEVELOPMENT.csv')
    assert set(pairs['split']) == {'source', 'development'}
    assert pairs.pair.is_unique and pairs.gene_a.lt(pairs.gene_b).all()
    assert (pairs.pair == pairs.gene_a + '|' + pairs.gene_b).all()
    assert pairs.source_order.notna().all() and pairs.source_order.is_unique
    source = pairs.index[pairs.split.eq('source')].to_numpy()
    source = np.array(sorted(source, key=lambda i: pairs.loc[i, 'source_order']))
    dev = pairs.index[pairs.split.eq('development')].to_numpy()
    assert len(source) >= 1536 and len(dev) > 0 and not set(source) & set(dev)
    a, b = pairs.gene_a.map(lookup).to_numpy(), pairs.gene_b.map(lookup).to_numpy()
    y = pairs.growth.to_numpy()
    priors = pd.read_csv(INP / 'SINGLE_GROWTH_PRIORS.csv').set_index('gene').average_fitness
    fa, fb = pairs.gene_a.map(priors).to_numpy(), pairs.gene_b.map(priors).to_numpy()
    assert np.isfinite(fa).all() and np.isfinite(fb).all() and np.isfinite(y).all()
    q = np.column_stack([np.ones(len(pairs)), fa + fb, fa * fb, fa ** 2 + fb ** 2])
    corr = np.corrcoef(features)
    assert np.isfinite(corr).all() and np.linalg.eigvalsh(corr).min() > -1e-10
    kernels = {w: (1 - w) * np.eye(n) + w * corr for w in [0., .5, 1.]}
    eig, vec = np.linalg.eigh(corr)
    rna_side = (vec * np.sqrt(np.maximum(eig, 0))) @ vec.T
    costs, outputs, selections = [], [], []

    def baseline(train):
        started = time.perf_counter()
        result = q @ np.linalg.lstsq(q[train], y[train], rcond=None)[0]
        costs.append({'kind': 'quadratic_fit', 'train_n': len(train), 'seconds': time.perf_counter() - started})
        return result

    def kernel_fit(train, assess, base, w, penalty):
        started = time.perf_counter()
        k = kernels[w]
        gram = pair_kernel(k, a[train], b[train], a[train], b[train])
        gram.flat[::len(train) + 1] += penalty
        coef = np.linalg.solve(gram, y[train] - base[train])
        pred = base[assess] + pair_kernel(k, a[assess], b[assess], a[train], b[train]) @ coef
        costs.append({'kind': 'kernel_fit', 'train_n': len(train), 'weight': w,
                      'penalty': penalty, 'seconds': time.perf_counter() - started})
        return pred

    def select(train, validation, tag):
        base = baseline(train)
        rows = []
        for w, penalty in PARAMS:
            pred = kernel_fit(train, validation, base, w, penalty)
            rows.append({'weight': w, 'penalty': penalty, 'selection_mse': float(np.mean((pred - y[validation]) ** 2))})
        selections.append({'tag': tag, 'train_pairs': pairs.loc[train, 'pair'].tolist(),
                           'validation_pairs': pairs.loc[validation, 'pair'].tolist(), 'scores': rows})
        return min(rows, key=lambda r: r['selection_mse']), min((r for r in rows if r['weight'] == 1), key=lambda r: r['selection_mse'])

    def nuclear(train, assess, base, penalty):
        started = time.perf_counter()
        matrix, info = calibration.complete(y[train] - base[train], a[train], b[train], rna_side, penalty, n)
        costs.append({'kind': 'nuclear_fit', 'train_n': len(train), 'penalty': penalty,
                      'seconds': time.perf_counter() - started, **info})
        return base[assess] + matrix[a[assess], b[assess]], info

    def record(name, later_n, prediction, **extra):
        row = {'model': name, 'later_n': later_n, 'early_n': 512,
               'development_mse': float(np.mean((prediction - y[dev]) ** 2)), **extra}
        outputs.append({**row, 'prediction': prediction.tolist()})
        print(json.dumps(row), flush=True)

    early = source[:512]
    chosen_mix, chosen_fixed = select(early[:384], early[384:], 'early')
    common = baseline(early)
    for later_n in [128, 512, 1024]:
        later = source[512:512 + later_n]
        union = source[:512 + later_n]
        record('common_start', later_n, common[dev])
        for name, chosen in [('fixedRNA_earlyselected', chosen_fixed), ('mixture_earlyselected', chosen_mix)]:
            pred = kernel_fit(later, dev, common, chosen['weight'], chosen['penalty'])
            record('lateronly_' + name, later_n, pred, weight=chosen['weight'], penalty=chosen['penalty'])
        for w, penalty in PARAMS:
            pred = kernel_fit(later, dev, common, w, penalty)
            record('lateronly_paired_grid', later_n, pred, weight=w, penalty=penalty)
        boundary = 3 * len(union) // 4
        mix, fixed = select(union[:boundary], union[boundary:], f'union{len(union)}')
        finalbase = baseline(union)
        for name, chosen in [('earlyselected_mixture', chosen_mix), ('earlyselected_fixedRNA', chosen_fixed),
                             ('unionselected_mixture', mix), ('unionselected_fixedRNA', fixed)]:
            pred = kernel_fit(union, dev, finalbase, chosen['weight'], chosen['penalty'])
            record('unionrefit_' + name, later_n, pred, weight=chosen['weight'], penalty=chosen['penalty'])
        innerbase = baseline(union[:boundary])
        nuclear_scores = []
        for penalty in [.0005, .05, 5.]:
            pred, info = nuclear(union[:boundary], union[boundary:], innerbase, penalty)
            nuclear_scores.append({'penalty': penalty, 'selection_mse': float(np.mean((pred - y[union[boundary:]]) ** 2)), **info})
        nuclear_choice = min(nuclear_scores, key=lambda r: r['selection_mse'])
        selections.append({'tag': f'nuclear_union{len(union)}', 'scores': nuclear_scores})
        pred, info = nuclear(union, dev, finalbase, nuclear_choice['penalty'])
        record('unionrefit_RNA_nuclear', later_n, pred, penalty=nuclear_choice['penalty'], **info)
    (OUT / 'PREDICTIONS.json').write_text(json.dumps({'development_pairs': pairs.loc[dev, 'pair'].tolist(),
        'truth': y[dev].tolist(), 'records': outputs}))
    pd.DataFrame([{k: v for k, v in r.items() if k != 'prediction'} for r in outputs]).to_csv(OUT / 'RESULTS.csv', index=False)
    (OUT / 'SELECTIONS.json').write_text(json.dumps(selections, indent=2))
    (OUT / 'COSTS.json').write_text(json.dumps(costs, indent=2))
    report = {'status': 'EXECUTED_EXPLORATORY_DEVELOPMENT', 'utc': datetime.now(timezone.utc).isoformat(),
              'wall_seconds': time.perf_counter() - start, 'fit_counts': pd.Series([c['kind'] for c in costs]).value_counts().to_dict(),
              'protected_values_loaded': 0, 'early_selection': {'mixture': chosen_mix, 'fixedRNA': chosen_fixed},
              'single_map_not_independent_tasks': True}
    (OUT / 'EXECUTION_SUMMARY.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
