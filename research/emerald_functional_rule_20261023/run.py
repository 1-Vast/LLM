"""Predeclared ordinary functional-feedback diagnostic on development contexts."""
import ast
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import time

os.environ['OPENBLAS_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'
import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/emerald_functional_rule'
SOURCE = ROOT / 'log/20261023/dose_update_qualification/summary_statistics.parquet'
LAMBDAS = [.01, .1, 1., 10., 100.]
PROGRAMS = [('mean', 0.)] + [('offset', a) for a in [.25, .5, .75, 1.]] + [
    (kind, lam) for kind in ['linear', 'rbf'] for lam in LAMBDAS]


def canonical(condition):
    return tuple(sorted((str(d), str(Decimal(str(v)).normalize()), str(u))
                        for d, v, u in ast.literal_eval(condition)))


def key(cell):
    return hashlib.sha256(('emerald-functional-rule-v1|' + cell).encode()).hexdigest(), cell


def identities():
    rows = pq.read_table(SOURCE, columns=['cell_line', 'condition']).to_pylist()
    cells = sorted({r['cell_line'] for r in rows}, key=key)
    by_canonical = defaultdict(list)
    for condition in sorted({r['condition'] for r in rows}):
        by_canonical[canonical(condition)].append(condition)
    assert all(len(v) == 1 for v in by_canonical.values()), 'Canonical aliases require a separate protocol'
    singles = sorted(c for c in by_canonical if len(c) == 1 and not c[0][0].startswith('DMSO'))
    single_parts = {c[0] for c in singles}
    anchor = canonical("[('Adagrasib', 0.005, 'uM'), ('Galunisertib', 0.1, 'uM')]")
    assert anchor in by_canonical
    anchor_pair = tuple(p[0] for p in anchor)
    queries = sorted(c for c in by_canonical if len(c) == 2 and all(p in single_parts for p in c)
                     and tuple(p[0] for p in c) != anchor_pair)
    pairs = sorted({tuple(p[0] for p in c) for c in queries})
    assert len(cells) == 52 and len(singles) == 44 and len(queries) == 15 and len(pairs) == 7
    conditions = [by_canonical[c][0] for c in singles + [anchor] + queries]
    groups = [pairs.index(tuple(p[0] for p in c)) for c in queries]
    return dict(development=cells[:36], reserve=cells[36:], conditions=conditions,
                support_count=44, query_groups=groups, query_pairs=pairs,
                query_conditions=[by_canonical[c][0] for c in queries],
                programs=[list(p) for p in PROGRAMS], query_tie_order='sorted canonical component tuples',
                query_pairs_order=[list(p) for p in pairs])


def predict(x, y, z, program):
    kind, amount = program
    ym = y.mean(axis=0)
    if kind == 'mean':
        return np.tile(ym, (len(z), 1))
    xm = x.mean(axis=0)
    if kind == 'offset':
        return ym + amount * (z - xm).mean(axis=1, keepdims=True)
    sd = x.std(axis=0)
    sd = np.where(sd > 0, sd, 1.)
    a, b = (x-xm)/sd, (z-xm)/sd
    if kind == 'linear':
        kernel, cross = a @ a.T / a.shape[1], b @ a.T / a.shape[1]
    else:
        def rbf(left, right):
            distance = ((left*left).sum(1)[:, None] + (right*right).sum(1)[None, :]
                        - 2*left@right.T) / left.shape[1]
            return np.exp(-np.maximum(distance, 0)/2)
        kernel, cross = rbf(a, a), rbf(b, a)
    weights = np.linalg.solve(kernel + amount*np.eye(len(a)), y-ym)
    return ym + cross @ weights


def pair_mse(truth, predicted, groups):
    return np.array([((truth[:, groups == g] - predicted[:, groups == g])**2).mean(axis=1)
                     for g in sorted(set(groups))]).T


def pair_regret(truth, predicted, groups):
    result = []
    for g in sorted(set(groups)):
        indices = np.flatnonzero(groups == g)
        chosen = np.argmin(predicted[:, indices], axis=1)
        values = truth[:, indices]
        result.append(values[np.arange(len(values)), chosen] - values.min(axis=1))
    return np.array(result).T


def evaluate(matrix, plan):
    groups = np.asarray(plan['query_groups'])
    y = matrix[:, 45:]
    all_predictions, trials, counters = {}, [], dict(inner_program_fits=0, outer_fits=0)
    for arm, width in [('single_only', 44), ('single_plus_anchor', 45)]:
        x = matrix[:, :width]
        predictions = np.empty_like(y)
        for held in range(len(x)):
            source = np.array([i for i in range(len(x)) if i != held])
            scores = np.zeros(len(PROGRAMS))
            for fold in range(3):
                val = source[np.arange(len(source)) % 3 == fold]
                train = source[np.arange(len(source)) % 3 != fold]
                for j, program in enumerate(PROGRAMS):
                    p = predict(x[train], y[train], x[val], program)
                    scores[j] += pair_mse(y[val], p, groups).sum() / (len(source)*7)
                    counters['inner_program_fits'] += 1
            selected = int(np.argmin(scores))
            predictions[held] = predict(x[source], y[source], x[[held]], PROGRAMS[selected])[0]
            counters['outer_fits'] += 1
            trials.append(dict(arm=arm, held_context=plan['development'][held],
                               scores=scores.tolist(), selected=selected))
        all_predictions[arm] = predictions
    baseline = (y.sum(axis=0)[None, :] - y) / (len(y)-1)
    all_predictions['source_mean'] = baseline
    metrics = {}
    for name, prediction in all_predictions.items():
        m, r = pair_mse(y, prediction, groups), pair_regret(y, prediction, groups)
        metrics[name] = dict(mse=float(m.mean()), regret=float(r.mean()),
                            per_pair_mse=m.mean(0).tolist(), per_pair_regret=r.mean(0).tolist(),
                            per_context_mse=m.mean(1).tolist(), per_context_regret=r.mean(1).tolist())
    a, b = metrics['single_only'], metrics['single_plus_anchor']
    wins = sum(v < u for u, v in zip(a['per_pair_mse'], b['per_pair_mse']))
    passed = b['mse'] < a['mse'] and b['regret'] < a['regret'] and wins >= 4
    return dict(metrics=metrics, pair_wins=wins, gate=passed, counters=counters,
                decision='ORDINARY_INFORMATION_SIGNAL' if passed else 'STOP_FIXED_SINGLE_PLUS_ONE_ANCHOR'), all_predictions, trials


if __name__ == '__main__':
    assert not (OUT / 'RESULT.json').exists() and not (OUT / 'STARTED.json').exists()
    freeze = json.loads((OUT / 'FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    plan = identities()
    assert json.loads(json.dumps(plan)) == json.loads((OUT / 'IDENTITY_PLAN.json').read_text())
    start = time.perf_counter()
    (OUT / 'STARTED.json').write_text(json.dumps(dict(stage='permitted-response-access', clock=start)))
    subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('export_worker.py'))], check=True)
    rows = json.loads((OUT / 'DEVELOPMENT_ROWS.json').read_text())
    bucket = defaultdict(list)
    for row in rows:
        assert row['cell_line'] in plan['development'] and row['condition'] in plan['conditions']
        bucket[row['cell_line'], row['condition']].append(row['growth_rate'])
    matrix = np.empty((36, len(plan['conditions'])))
    for i, cell in enumerate(plan['development']):
        for j, condition in enumerate(plan['conditions']):
            values = bucket.get((cell, condition), [])
            if not values or any(v is None or not np.isfinite(v) for v in values) or len(set(values)) != 1:
                result = dict(decision='STOP_RESPONSE_COVERAGE', stage='before_fit',
                              allowed_rows=len(rows), failed_context=cell, failed_condition=condition,
                              count=len(values), reserve_exported=False)
                (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2))
                print(json.dumps(result))
                raise SystemExit(0)
            matrix[i, j] = values[0]
    result, predictions, trials = evaluate(matrix, plan)
    result.update(wall_seconds=time.perf_counter()-start, allowed_rows=len(rows),
                  development_contexts=36, reserve_contexts_not_exported=16, logical_support_conditions=[44,45],
                  scope='exploratory relative pooled-score reconstruction; no independent biological or method claim')
    np.savez_compressed(OUT / 'DEVELOPMENT.npz', matrix=matrix, **predictions)
    (OUT / 'TRIALS.json').write_text(json.dumps(trials, indent=2), encoding='utf-8')
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
