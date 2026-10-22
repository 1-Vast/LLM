"""Registered concentration-crossfit operational live/dead information gate."""
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
import traceback

import numpy as np
from scipy.optimize import least_squares
from scipy.special import exprel
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/dead_stock_information_gate'
OUT = LOG/'hct_gate'
DATA = ROOT/'log/20261022/functional_dynamics_gate/root_scout/hct116_dose_response_fresh_object.body'
ARMS = ['live_only', 'dead_initial', 'dead_snapshot', 'dead_history']
CONTEXTS = ['mcer-1e3', 'mcer-3e3', 'mkate-1e3', 'mkate-3e3']
STARTS = [[.03, .01, .03, .01, .1], [.04, .04, .06, .02, .5],
          [.01, .08, .1, .05, .8], [.06, .02, .02, .08, .2]]
QUAD_X, QUAD_W = np.polynomial.legendre.leggauss(32)
QUAD_X, QUAD_W = (QUAD_X+1)/2, QUAD_W/2


def save(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def concentration(s):
    c = float(s)
    if not np.isfinite(c) or c < 0:
        raise ValueError('invalid_concentration')
    return format(c, 'g')


def structure(rows):
    grouped = defaultdict(lambda: defaultdict(dict))
    well_identity = {}
    for r in rows:
        ctx, c, well = r['seed'], concentration(r['concentration']), r['well']
        if ctx not in CONTEXTS:
            raise ValueError('unexpected_context')
        identity = (ctx, c)
        if well in well_identity and well_identity[well] != identity:
            raise ValueError('well_identity_changed')
        well_identity[well] = identity
        key = (c, ctx, well)
        t, img = float(r['Elapsed']), r['img']
        if img in grouped[key][t]:
            raise ValueError('duplicate_well_time_image')
        grouped[key][t][img] = r
    result = []
    for key, frames in sorted(grouped.items()):
        absolute = sorted(frames)
        times = [t-absolute[0] for t in absolute]
        if times != list(range(0, 89, 4)):
            raise ValueError('unexpected_export_time_grid')
        origin = None
        for t, relative in zip(absolute, times):
            panel = frames[t]
            if set(panel) != {'1', '2', '3'}:
                raise ValueError('incomplete_image_panel')
            dates = {datetime.strptime(r['Date Time'], '%m/%d/%Y %I:%M:%S %p') for r in panel.values()}
            if len(dates) != 1:
                raise ValueError('image_timestamp_mismatch')
            date = next(iter(dates))
            if origin is None:
                origin = date
            if abs((date-origin).total_seconds()/3600-relative) > 1e-8:
                raise ValueError('elapsed_timestamp_mismatch')
        result.append({'key': key, 'frames': frames, 'times': times, 'absolute': absolute})
    return result


def mean_field(g, relative_t, field):
    absolute = g['absolute'][g['times'].index(relative_t)]
    values = np.array([float(g['frames'][absolute][img][field]) for img in ['1', '2', '3']])
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError('invalid_observed_readout')
    return float(np.mean(values))


def prefix(g):
    ts = np.arange(0., 25., 4.)
    live = np.array([mean_field(g, t, 'intersect_live_cells') for t in ts])
    dead = np.array([mean_field(g, t, 'intersect_dead_cells') for t in ts])
    total = np.array([mean_field(g, t, 'tot_cells') for t in ts])
    s, z = np.log2(live+1), np.log2(dead+1)
    return {'t': ts, 'L': live, 'D': dead, 's': s, 'z': z,
            'total_identity_maxabs': float(np.max(np.abs(total-live-dead)))}


def slope(t, y):
    dt = t-np.mean(t)
    return float(dt@(y-np.mean(y))/(dt@dt))


def features(g, p, arm):
    s, z, t = p['s'], p['z'], p['t']
    c, ctx, _ = g['key']
    x = np.r_[s-s[-1], s[0], s[-1], slope(t[:4], s[:4]),
              slope(t[3:], s[3:]), slope(t, s), np.log1p(float(c)), float(c == '0'),
              [float(ctx == k) for k in CONTEXTS]]
    if arm == 'dead_initial':
        x = np.r_[x, z[0], p['D'][0]/(p['L'][0]+1)]
    elif arm == 'dead_snapshot':
        x = np.r_[x, z[-1], p['D'][-1]/(p['L'][-1]+1)]
    elif arm == 'dead_history':
        x = np.r_[x, z, p['D'][-1]/(p['L'][-1]+1), slope(t, z)]
    elif arm != 'live_only':
        raise ValueError('unknown_arm')
    return x


def labels(groups, allowed):
    out = []
    for g in groups:
        if g['key'][0] not in allowed:
            raise ValueError('target_outside_training_authorization')
        out.append(np.log2(mean_field(g, 72, 'intersect_live_cells')+1))
    return np.array(out)


def macro(keys, pred, y):
    contexts = defaultdict(list)
    for k, e in zip(keys, np.abs(np.array(pred)-y)):
        contexts[k[:2]].append(float(e))
    doses = defaultdict(list)
    for k, ee in contexts.items():
        doses[k[0]].append(float(np.mean(ee)))
    per_dose = {k: float(np.mean(v)) for k, v in sorted(doses.items(), key=lambda kv: float(kv[0]))}
    return {'macro_mae': float(np.mean(list(per_dose.values()))), 'per_dose': per_dose}


def weights(keys):
    contexts, nw = defaultdict(set), defaultdict(int)
    for k in keys:
        contexts[k[0]].add(k[1])
        nw[k[:2]] += 1
    w = np.array([1/(len(contexts[k[0]])*nw[k[:2]]) for k in keys])
    return w/w.mean()


def inner_split(doses, outer):
    remaining = [c for c in doses if c != outer]
    val = min(remaining, key=lambda c: hashlib.sha256(('HCT116-deadstock-inner-v1|'+c).encode()).hexdigest())
    return [c for c in remaining if c != val], val, remaining


def configs():
    models = [(f'ridge_{a}', make_pipeline(StandardScaler(), Ridge(alpha=a)))
              for a in [.01, .1, 1, 10, 100, 1000]]
    for leaves in [7, 15]:
        for l2 in [0, 10]:
            models.append((f'hgb_{leaves}_{l2}', HistGradientBoostingRegressor(
                max_iter=200, learning_rate=.05, max_leaf_nodes=leaves, l2_regularization=l2,
                min_samples_leaf=5, random_state=20261022)))
    for depth in [8, None]:
        for leaf in [2, 5]:
            models.append((f'extratrees_{depth}_{leaf}', ExtraTreesRegressor(
                n_estimators=200, max_depth=depth, min_samples_leaf=leaf,
                random_state=20261022, n_jobs=1)))
    return models


def fit(model, x, y, keys):
    kw = {'ridge__sample_weight': weights(keys)} if hasattr(model, 'named_steps') else {'sample_weight': weights(keys)}
    model.fit(x, y, **kw)


def divided_exp(a, b, t):
    return np.exp(b*t)*t*exprel((a-b)*t)


def compartments(params, t, l0, d0):
    b, k, d, c, q = params
    r = b-k
    s0, i0 = (1-q)*l0, q*l0
    s = s0*np.exp(r*t)
    ii = i0*np.exp(-d*t)+k*s0*divided_exp(r, -d, t)
    # Positive convolution, stable also at repeated rates; no divided-difference cancellation.
    u = t[:, None]*QUAD_X[None, :]
    iu = i0*np.exp(-d*u)+k*s0*divided_exp(r, -d, u)
    dd = d0*np.exp(-c*t)+d*t*np.sum(QUAD_W[None, :]*np.exp(-c*(t[:, None]-u))*iu, axis=1)
    if np.min(dd) < 0 or np.min(s+ii) < 0:
        raise ValueError('invalid_generator_solution')
    return np.c_[s+ii, dd]


def kinetic_fit(p, dual):
    if p['L'][0] <= 0:
        raise ValueError('nonpositive_initial_live_for_kinetic')
    start_time = time.time()
    d0 = p['D'][0] if dual else 0.
    observed = np.c_[p['s'], p['z']] if dual else p['s'][:, None]

    def expand(v):
        return v if dual else np.array([v[0], v[1], v[2], 0., v[3]])

    def residual(v):
        sim = compartments(expand(v), p['t'], p['L'][0], d0)
        pred = np.log2(sim+1) if dual else np.log2(sim[:, :1]+1)
        return (pred-observed).ravel()

    runs = []
    for start in STARTS:
        x0 = np.array(start) if dual else np.array([start[0], start[1], start[2], start[4]])
        upper = [.2, .2, .2, .2, 1.] if dual else [.2, .2, .2, 1.]
        sol = least_squares(residual, x0, bounds=(np.zeros(len(x0)), upper),
                            loss='soft_l1', f_scale=.2, max_nfev=300)
        prediction = float(np.log2(compartments(expand(sol.x), np.array([72.]), p['L'][0], d0)[0, 0]+1))
        if not np.isfinite(prediction) or not np.isfinite(sol.cost):
            raise ValueError('nonfinite_kinetic_fit')
        runs.append({'parameters': expand(sol.x).tolist(), 'cost': float(sol.cost),
                     'success': bool(sol.success), 'status': int(sol.status), 'nfev': int(sol.nfev),
                     'prediction': prediction, 'active_mask': sol.active_mask.tolist()})
    # Finite capped optimizer results are reported, not silently removed/renamed converged.
    winner = min(range(len(runs)), key=lambda i: (runs[i]['cost'], i))
    return {'prediction': runs[winner]['prediction'], 'winner': winner, 'runs': runs,
            'all_starts_unconverged': not any(r['success'] for r in runs),
            'selected_converged': runs[winner]['success'],
            'mechanism_qualification': ('UNQUALIFIED_FOR_MECHANISM' if not any(r['success'] for r in runs)
                                        else 'NO_LATENT_TRUTH_CLAIM'),
            'seconds': time.time()-start_time}


def contrast(scores, candidate, comparator):
    a, b = scores[candidate], scores[comparator]
    doses = list(a['per_dose'])
    gains = np.array([b['per_dose'][c]-a['per_dose'][c] for c in doses])
    gain = float(gains.mean())
    rng = np.random.default_rng(20261022)
    boot = np.mean(rng.choice(gains, (10000, len(gains))), axis=1)
    return {'candidate': candidate, 'comparator': comparator, 'mae_reduction': gain,
            'relative_reduction': gain/b['macro_mae'],
            'per_dose_gain': dict(zip(doses, gains.tolist())),
            'conditional_dose_bootstrap_95': np.quantile(boot, [.025, .975]).tolist(),
            'useful': bool(gain >= .05 and gain >= .1*b['macro_mae'])}


def main():
    import csv
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        raise FileExistsError('measured_output_directory_not_empty')
    if hashlib.md5(DATA.read_bytes()).hexdigest() != '010489434a9e563f4f23afa304c70aca':
        raise ValueError('manifest_integrity')
    with DATA.open(encoding='utf-8-sig', newline='') as f:
        groups = structure(list(csv.DictReader(f)))
    doses = sorted({g['key'][0] for g in groups}, key=float)
    if len(groups) != 96 or len(doses) != 8:
        raise ValueError('unexpected_identity_population')
    keys = [g['key'] for g in groups]
    save(OUT/'PRE_RESPONSE_FREEZE.json', {
        'hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [Path(__file__), LOG/'HCT116_GATE_PROTOCOL.md', DATA]},
        'keys': keys, 'outer_doses': doses,
        'folds': {c: {'inner_train': inner_split(doses, c)[0], 'inner_validation': inner_split(doses, c)[1],
                      'outer_train': inner_split(doses, c)[2]} for c in doses},
        'response_values_converted': False,
        'scope': 'grouped_crossfit_not_globally_unseen_test'})
    pp = [prefix(g) for g in groups]
    x = {arm: np.array([features(g, p, arm) for g, p in zip(groups, pp)]) for arm in ARMS}
    anchors = np.array([p['s'][-1] for p in pp])
    kinetic = {'live_only': [], 'dead_history': []}
    for i, p in enumerate(pp):
        for arm in kinetic:
            kinetic[arm].append(kinetic_fit(p, arm == 'dead_history'))
        if (i+1) % 24 == 0:
            print(json.dumps({'prefix_only_kinetic_wells_done': i+1}), flush=True)
    ols = np.array([p['s'][-1]+48*slope(p['t'], p['s']) for p in pp])
    kinetic_summary = {arm: {
        'wells': len(rr), 'all_starts_unconverged': sum(r['all_starts_unconverged'] for r in rr),
        'selected_unconverged': sum(not r['selected_converged'] for r in rr),
        'starts_unconverged': sum(not s['success'] for r in rr for s in r['runs']),
        'total_nfev': sum(s['nfev'] for r in rr for s in r['runs']),
        'total_seconds': sum(r['seconds'] for r in rr)} for arm, rr in kinetic.items()}
    save(OUT/'PREFIX_ONLY_KINETIC_CACHE.json', {
        'keys': keys, 'kinetic': kinetic, 'ols_predictions': ols.tolist(),
        'kinetic_summary': kinetic_summary,
        'prefix_total_identity_maxabs': max(p['total_identity_maxabs'] for p in pp),
        'future_target_values_accessed': False})
    predictions = {f'direct_{arm}': np.empty(len(groups)) for arm in ARMS}
    for arm in kinetic:
        for kind in ['selected_kinetic', 'selected_family', 'half_blend', 'two_compartment']:
            predictions[kind+'_'+arm] = np.empty(len(groups))
    predictions['constant_netgrowth'] = ols
    fold_records = []
    for outer in doses:
        train_doses, val_dose, outer_train_doses = inner_split(doses, outer)
        train = np.array([k[0] in train_doses for k in keys])
        val = np.array([k[0] == val_dose for k in keys])
        historical = np.array([k[0] in outer_train_doses for k in keys])
        test = np.array([k[0] == outer for k in keys])
        choose_groups = lambda mask: [g for g, keep in zip(groups, mask) if keep]
        choose_keys = lambda mask: [k for k, keep in zip(keys, mask) if keep]
        ytrain = labels(choose_groups(train), train_doses)
        yval = labels(choose_groups(val), [val_dose])
        yhistorical = labels(choose_groups(historical), outer_train_doses)
        fold = {'outer': outer, 'inner_train': train_doses, 'inner_validation': val_dose,
                'outer_train': outer_train_doses, 'arms': {}}
        for arm in ARMS:
            trials, models = [], {}
            fit_started = time.time()
            for name, model in configs():
                fit(model, x[arm][train], ytrain-anchors[train], choose_keys(train))
                score = macro(choose_keys(val), anchors[val]+model.predict(x[arm][val]), yval)
                trials.append({'name': name, **score})
                models[name] = model
            best = min(trials, key=lambda q: (q['macro_mae'], q['name']))
            model = models[best['name']]
            fit(model, x[arm][historical], yhistorical-anchors[historical], choose_keys(historical))
            testpred = anchors[test]+model.predict(x[arm][test])
            predictions['direct_'+arm][test] = testpred
            record = {'trials': trials, 'selected': best['name'],
                      'direct_seconds': time.time()-fit_started, 'test_predictions': testpred.tolist()}
            if arm in kinetic:
                local = np.array([r['prediction'] for r in kinetic[arm]])
                local_score = macro(choose_keys(val), local[val], yval)['macro_mae']
                ols_score = macro(choose_keys(val), ols[val], yval)['macro_mae']
                # Lexicographic tie rule across named local models.
                chosen = min([('constant_ols', ols_score, ols),
                              ('two_compartment', local_score, local)], key=lambda z: (z[1], z[0]))
                predkinetic = chosen[2][test]
                family = 'direct' if best['macro_mae'] <= chosen[1] else 'kinetic'
                predictions['selected_kinetic_'+arm][test] = predkinetic
                predictions['two_compartment_'+arm][test] = local[test]
                predictions['selected_family_'+arm][test] = testpred if family == 'direct' else predkinetic
                predictions['half_blend_'+arm][test] = .5*(testpred+predkinetic)
                record.update(kinetic_validation={'constant_ols': ols_score, 'two_compartment': local_score},
                              selected_kinetic=chosen[0], selected_family=family)
            fold['arms'][arm] = record
        save(OUT/('FOLD_'+outer+'.json'), fold)
        fold_records.append(fold)
        print(json.dumps({'completed_outer_dose': outer}), flush=True)
    save(OUT/'ALL_OUTER_PREDICTIONS_BEFORE_SCORING.json', {
        'keys': keys, 'predictions': {name: v.tolist() for name, v in predictions.items()},
        'folds': fold_records, 'globally_blind_targets': False,
        'each_outer_fold_target_excluded_from_its_fit_and_selection': True})
    y = labels(groups, doses)
    scores = {name: macro(keys, p, y) for name, p in predictions.items()}
    contrasts = [contrast(scores, 'direct_dead_history', 'direct_live_only'),
                 contrast(scores, 'direct_dead_history', 'direct_dead_initial'),
                 contrast(scores, 'direct_dead_history', 'direct_dead_snapshot'),
                 contrast(scores, 'selected_kinetic_dead_history', 'selected_kinetic_live_only'),
                 contrast(scores, 'selected_family_dead_history', 'selected_family_live_only')]
    primary = contrasts[0]['useful']
    support = any(c['useful'] for c in contrasts[3:])
    status = 'EXPLORATORY_CHANNEL_SIGNAL' if primary else ('MIXED_MODEL_DEPENDENT' if support else 'STOP_THIS_APPLICATION_CONFIGURATION')
    result = {'scores': scores, 'contrasts': contrasts, 'primary_pass': primary,
              'dynamic_history_gate_pass': primary and all(c['useful'] for c in contrasts[1:3]),
              'decision': status, 'target_values': y.tolist(), 'elapsed_seconds': time.time()-started,
              'n_wells': len(groups), 'n_doses': len(doses), 'n_independent_drug_tasks': 1,
              'kinetic_summary': kinetic_summary,
              'scope': 'operational_exported_readout_within_source_concentration_crossfit',
              'new_algorithm_agent_inheritance_RSI': 'NOT_ESTABLISHED'}
    save(OUT/'RESULT.json', result)
    print(json.dumps({'scores': {k: v['macro_mae'] for k, v in scores.items()},
                      'contrasts': contrasts, 'decision': status, 'elapsed_seconds': result['elapsed_seconds']}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists() and not (OUT/'FAILURE.txt').exists():
            (OUT/'FAILURE.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
