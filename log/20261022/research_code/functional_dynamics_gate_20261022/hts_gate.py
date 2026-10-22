"""Frozen grouped drug forecast gate. Test targets open only after model freeze."""
import csv
import hashlib
import json
import pickle
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/functional_dynamics_gate'
OUT = LOG/'hts_gate'
DATA = LOG/'root_scout/hts001.body'
CELL_LINES = ['BR1', 'DS3', 'DS7', 'DS8', 'DS9', 'MGH', 'PC9']
ALPHAS = np.linspace(0, 1, 11)


def save(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def drug_split(drugs):
    ordered = sorted(drugs, key=lambda d: hashlib.sha256(
        ('HTS001-functional-gate-v1|'+d).encode()).hexdigest())
    if len(ordered) != 14:
        raise ValueError('expected_14_drugs')
    return {'train': ordered[:8], 'validation': ordered[8:11], 'test': ordered[11:]}


def slope(t, s):
    dt = t-np.mean(t)
    return float(dt @ (s-np.mean(s)) / (dt @ dt))


def structure(rows):
    groups = defaultdict(list)
    for row in rows:
        if row['drug1'] == 'control':
            continue
        key = tuple(row[c] for c in ['drug1', 'cell.line', 'drug1.conc', 'upid', 'well'])
        groups[key].append(row)
    eligible, excluded = [], []
    for key, rr in sorted(groups.items()):
        rr = sorted(rr, key=lambda r: float(r['time']))
        t = np.array([float(r['time']) for r in rr])
        if len(set(t)) != len(t):
            raise ValueError('duplicate_time_key')
        initial = np.flatnonzero(t <= 24)
        new = np.flatnonzero((t > 24) & (t <= 34))
        targets = np.flatnonzero((t >= 56) & (t <= 62))
        if len(initial) < 3 or len(new) < 2 or len(targets) == 0:
            excluded.append({'key': key, 'initial': len(initial), 'feedback': len(new),
                             'targets': len(targets)})
            continue
        eligible.append({'key': key, 'rows': rr, 'initial': initial,
                         'new': new, 'target': int(targets[-1])})
    return eligible, excluded


def count(row):
    n = float(row['cell.count'])
    if not np.isfinite(n) or n < 0:
        raise ValueError('invalid_count')
    return n


def prefix_features(g):
    """The only count accesses here are at t<=34; future counts are opaque."""
    initial, new, rr = g['initial'], g['new'], g['rows']
    ix = np.concatenate([initial, new])
    t = np.array([float(rr[i]['time']) for i in ix])
    s = np.log2([count(rr[i])+1 for i in ix])
    n0 = len(initial)
    r0 = slope(t[:n0], s[:n0])
    r1 = slope(t[n0-1:], s[n0-1:])
    target_t = float(rr[g['target']]['time'])
    h = target_t-t[-1]
    anchor = float(s[-1])
    key = g['key']
    dose = float(key[2])
    if dose <= 0 or key[1] not in CELL_LINES:
        raise ValueError('unexpected_identity')
    interpolated = np.interp([4, 8, 12, 20, 24, 28, 32], t, s)-anchor
    x = np.r_[interpolated, s[0], anchor, r0, r1, r1-r0,
              t[0], t[n0-1], t[-1], h, np.log10(dose),
              [int(key[1] == c) for c in CELL_LINES]]
    return {'x': x, 'r0': r0, 'r1': r1, 'rfull': slope(t, s), 'anchor': anchor,
            'h': h, 'frozen': float(s[n0-1]+r0*(target_t-t[n0-1]))}


def targets(groups, allowed_drugs):
    values = []
    for g in groups:
        if g['key'][0] not in allowed_drugs:
            raise ValueError('target_access_outside_authorized_partition')
        values.append(np.log2(count(g['rows'][g['target']])+1))
    return np.array(values)


def macro_losses(keys, pred, y):
    # Equal drug -> background -> dose -> well. Plate stays in key.
    dose_losses = defaultdict(list)
    for k, e in zip(keys, np.abs(np.asarray(pred)-y)):
        dose_losses[k[:3]].append(float(e))
    cells = defaultdict(list)
    for k, ee in dose_losses.items():
        cells[k[:2]].append(float(np.mean(ee)))
    drugs = defaultdict(list)
    for k, ee in cells.items():
        drugs[k[0]].append(float(np.mean(ee)))
    per_drug = {k: float(np.mean(v)) for k, v in sorted(drugs.items())}
    return {'macro_mae': float(np.mean(list(per_drug.values()))), 'per_drug': per_drug}


def updater(f, alpha):
    return f['anchor']+f['h']*((1-alpha)*f['r0']+alpha*f['r1'])


def search_alpha(features, keys, y):
    trials = []
    for alpha in ALPHAS:
        score = macro_losses(keys, [updater(f, alpha) for f in features], y)
        trials.append({'alpha': float(alpha), **score})
    best = min(trials, key=lambda q: (q['macro_mae'], q['alpha']))
    return best['alpha'], trials


def direct_configs():
    out = [('ridge_'+str(a), make_pipeline(StandardScaler(), Ridge(alpha=a)))
           for a in [.01, .1, 1, 10, 100, 1000]]
    for leaves in [7, 15]:
        for l2 in [0, 10]:
            out.append((f'hgb_{leaves}_{l2}', HistGradientBoostingRegressor(
                max_iter=200, learning_rate=.05, max_leaf_nodes=leaves,
                l2_regularization=l2, min_samples_leaf=10, random_state=20261022)))
    for depth in [8, None]:
        for leaf in [3, 10]:
            out.append((f'extratrees_{depth}_{leaf}', ExtraTreesRegressor(
                n_estimators=200, max_depth=depth, min_samples_leaf=leaf,
                random_state=20261022, n_jobs=1)))
    return out


def training_weights(keys):
    # Exact equal drug/background/dose/well weighting, also used for fitting.
    n_wells, n_doses, n_cells = defaultdict(int), defaultdict(set), defaultdict(set)
    for k in keys:
        n_wells[k[:3]] += 1
        n_doses[k[:2]].add(k[2])
        n_cells[k[0]].add(k[1])
    w = np.array([1/(len(n_cells[k[0]])*len(n_doses[k[:2]])*n_wells[k[:3]]) for k in keys])
    return w/np.mean(w)


def fit_direct(model, x, y, keys):
    w = training_weights(keys)
    if hasattr(model, 'named_steps'):
        return model.fit(x, y, ridge__sample_weight=w)
    return model.fit(x, y, sample_weight=w)


def contrast(scores, a, b):
    aa, bb = scores[a], scores[b]
    drugs = sorted(aa['per_drug'])
    gains = np.array([bb['per_drug'][d]-aa['per_drug'][d] for d in drugs])
    rng = np.random.default_rng(20261022)
    means = np.mean(rng.choice(gains, (10000, len(gains))), axis=1)
    gain = bb['macro_mae']-aa['macro_mae']
    return {'candidate': a, 'comparator': b, 'mae_reduction': float(gain),
            'relative_reduction': float(gain/bb['macro_mae']),
            'per_drug_gain': dict(zip(drugs, gains.tolist())),
            'conditional_3drug_bootstrap_95': np.quantile(means, [.025, .975]).tolist(),
            'useful_gain_pass': bool(gain >= .10 and gain >= .10*bb['macro_mae'])}


def main():
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        raise FileExistsError('gate_output_not_empty')
    if hashlib.md5(DATA.read_bytes()).hexdigest() != 'a5959a38166685707e840369ce34d74d':
        raise ValueError('data_integrity')
    with DATA.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    split = drug_split({r['drug1'] for r in rows if r['drug1'] != 'control'})
    groups, excluded = structure(rows)
    save(OUT/'IDENTITY_SPLIT_BEFORE_RESPONSES.json', {'split': split, 'excluded': excluded,
         'eligible': len(groups), 'response_values_converted_at_this_point': False,
         'counts': {s: sum(g['key'][0] in ds for g in groups) for s, ds in split.items()}})
    features = [prefix_features(g) for g in groups]
    keys = [g['key'] for g in groups]
    mask = {s: np.array([k[0] in ds for k in keys]) for s, ds in split.items()}
    part = {s: [g for g, keep in zip(groups, m) if keep] for s, m in mask.items()}
    kk = {s: [k for k, keep in zip(keys, m) if keep] for s, m in mask.items()}
    ff = {s: [f for f, keep in zip(features, m) if keep] for s, m in mask.items()}
    y = {s: targets(part[s], split[s]) for s in ['train', 'validation']}
    alpha, alpha_trials = search_alpha(ff['train'], kk['train'], y['train'])
    # Conventional search computes the same programs independently, vectorized.
    candidate_matrix = np.array([[updater(f, a) for f in ff['train']] for a in ALPHAS])
    search_scores = [macro_losses(kk['train'], p, y['train'])['macro_mae'] for p in candidate_matrix]
    ordinary_alpha = float(ALPHAS[int(np.argmin(search_scores))])
    if alpha != ordinary_alpha:
        raise AssertionError('same_program_search_disagrees')
    prior = {c: float(np.median([f['r1'] for k, f in zip(kk['train'], ff['train']) if k[1] == c]))
             for c in CELL_LINES}
    x = {s: np.array([f['x'] for f in fs]) for s, fs in ff.items()}
    anchors = {s: np.array([f['anchor'] for f in fs]) for s, fs in ff.items()}
    direct_trials, models = [], {}
    for name, model in direct_configs():
        fit_direct(model, x['train'], y['train']-anchors['train'], kk['train'])
        score = macro_losses(kk['validation'], anchors['validation']+model.predict(x['validation']),
                             y['validation'])
        direct_trials.append({'name': name, **score})
        models[name] = model
    selected = min(direct_trials, key=lambda q: (q['macro_mae'], q['name']))['name']
    selected_model = models[selected]
    fit_direct(selected_model, np.concatenate([x['train'], x['validation']]),
               np.concatenate([y['train']-anchors['train'], y['validation']-anchors['validation']]),
               kk['train']+kk['validation'])
    testf, testkeys = ff['test'], kk['test']
    preds = {
        'persistence': np.array([f['anchor'] for f in testf]),
        'frozen_initial': np.array([f['frozen'] for f in testf]),
        'readout_only': np.array([updater(f, 0) for f in testf]),
        'ordinary_full_refit': np.array([f['anchor']+f['h']*f['rfull'] for f in testf]),
        'ordinary_local_psi0': np.array([updater(f, 1) for f in testf]),
        'inherited_psi1': np.array([updater(f, alpha) for f in testf]),
        'equal_budget_search': np.array([updater(f, ordinary_alpha) for f in testf]),
        'simple_half_mixture': np.array([updater(f, .5) for f in testf]),
        'shared_rate_prior': np.array([f['anchor']+f['h']*prior[k[1]] for k, f in zip(testkeys, testf)]),
        'warm_start_half': np.array([f['anchor']+f['h']*(.5*prior[k[1]]+.5*f['r1'])
                                     for k, f in zip(testkeys, testf)]),
        'prior_and_psi': np.array([f['anchor']+f['h']*((1-alpha)*prior[k[1]]+alpha*f['r1'])
                                  for k, f in zip(testkeys, testf)]),
        'selected_direct': anchors['test']+selected_model.predict(x['test'])}
    preds['direct_world_half_blend'] = .5*(preds['selected_direct']+preds['inherited_psi1'])
    if not np.array_equal(preds['inherited_psi1'], preds['equal_budget_search']):
        raise AssertionError('search_prediction_disagrees')
    with (OUT/'selected_direct.pkl').open('xb') as f:
        pickle.dump(selected_model, f)
    save(OUT/'MODEL_FREEZE_BEFORE_TEST_TARGETS.json', {
        'alpha': alpha, 'ordinary_search_alpha': ordinary_alpha, 'alpha_trials': alpha_trials,
        'direct_trials': direct_trials, 'selected_direct': selected, 'rate_prior': prior,
        'test_keys': testkeys, 'test_predictions': {k: v.tolist() for k, v in preds.items()},
        'test_target_values_accessed': False,
        'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [Path(__file__), LOG/'HTS001_GATE_PROTOCOL.md', DATA]}})
    yt = targets(part['test'], split['test'])
    scores = {name: macro_losses(testkeys, p, yt) for name, p in preds.items()}
    contrasts = [contrast(scores, 'inherited_psi1', b)
                 for b in ['selected_direct', 'ordinary_local_psi0', 'ordinary_full_refit']]
    save(OUT/'RESULT.json', {'split': split, 'test_n_drugs': 3, 'test_n_wells': len(yt),
        'target': 'log2(cell.count+1)', 'scores': scores, 'contrasts': contrasts,
        'advance_signal': all(c['useful_gain_pass'] for c in contrasts[:2]),
        'algorithm_novelty': 'NONE_EXACT_SAME_PROGRAM_SEARCH',
        'scope': 'within_screen_exploratory_only_no_independent_run_validation',
        'test_targets': yt.tolist(), 'elapsed_seconds': time.time()-started})
    print(json.dumps({'alpha': alpha, 'selected_direct': selected,
        'scores': {k: v['macro_mae'] for k, v in scores.items()},
        'contrasts': contrasts, 'advance_signal': all(c['useful_gain_pass'] for c in contrasts[:2])}))


if __name__ == '__main__':
    main()
