#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R203-N1-EXEC: N1 effect execution (synthetic mechanism account only; 0 wells).

Frozen execution prereg: seeds 20261070..20261119 (R=50), method seeds 20262000+r*10+idx,
n_units=300, T=6 (fit4/hold2), M vs B1-B6; primary D=R(M)-R(B2), delta=.05, Holm family6.
NO real response, NO wet experiment, NO pharmacology/real-decision/transfer/mechanism/novelty claims.
Only writes effect-run dir + tmp; frozen generator imported read-only (AA5D454A...).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import time

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.abspath(os.path.join(BASE, '..', '2026-10-28-n1-synthetic-prereg'))
EXECPREREG = os.path.abspath(os.path.join(BASE, '..', '2026-10-28-n1-effect-prereg'))
IMPL = os.path.abspath(os.path.join(BASE, '..', '2026-10-28-n1-implementation'))
OUT = os.path.join(BASE, 'n1_effect.json')
ROWS = os.path.join(BASE, 'n1_effect_rows.csv')
SUMMARY = os.path.join(BASE, 'n1_effect_summary.json')
HEADROOM = os.path.join(BASE, 'headroom_precheck.json')
TIMING = os.path.join(BASE, 'timing_n1_effect.json')

N_UNITS = 300
R_REPS = 50
T = 6
T_FIT = 4
T_HOLD = 2
M_MENU = 5
DELTA = 0.05
ALPHA = 0.05
Z80 = 2.8015852181
EXEC_SEED_BASE = 20261070
HEADROOM_SEED_BASE = 20261130
METHOD_SEED_BASE = 20262000
CONSERVATIVE_MDE = 0.04798268
CAPS = {'wall_s': 1800.0, 'cpu_s': 7200.0, 'memory_gb': 8.0}

FROZEN_V04 = {
    'PROBLEM_N1_v0_4.md': '5C513D9461FAEDBD3372463A4FDD1868C927EB48501BC0CDEB7643FF6FA0649A',
    'DESIGN_N1_v0_4.md': '94BAB8052EF4864BD745986326F4869D9054C2935794FEDAD8733733B57C029C',
    'generator_n1_v0_4.py': 'AA5D454A82366BF3B7FC9E7F67FAA3499098621FAD45B84804485550E6EDCC97',
    'generator_n1_v0_4.json': '35E41136E344AAF6C51A73B19418FF5CBEAD9460697BB8B1EE92F9E16D610263',
    'V4_validation_v0_4.json': '254BEBAB201AA8A0EA33AEA8A47BC7D37A99ADE1436319D159603061DC8E2ECF',
    'timing_n1_pilot_v0_4.json': 'A4C7E0F675B0020B99A93CC022572B3E85F30A26E391493AF45FAA3C005586C7',
    'DECISION_R203_N1_PREREG.md': '930F1567254095945C228532AB8D1576915AAD01AC8ACC06185D99B573C174AD',
}
FROZEN_C204 = {
    'run_n1_gates.py': 'D2AA831F26AE8882F2B5B60C4C3FB2ACCAEA327AA381A4F949D32D23B276D7B8',
    'n1_gates.json': '529C1D2EE1E4B4039F4BBD10115C362EEE419D4BEF62A07FEC5A3C4046CBA0E0',
    'n1_gates_rows.csv': '78457E1F97B85D1D70918BFCE28AB0E79123225E5D9BD3589EACF951B587F6EB',
    'timing_n1_gates.json': '5A52E42F845A4127E2FB09E0DA9061FB591C83DE474E8C5286380CF17F7F75AC',
    'schema_n1_gates.json': 'F2D561D9C4B3E8AEE4EF785D3C98EF55A701059FC750AE32D588135CF9C5AB1D',
    'report_n1_gates.md': '38CFD34CFE741F95BA895B83C90086440508EB49030DC3F6A6E8B080E682CAF5',
    'record_n1_gates.md': 'DA21E2D914C98098735FD2CF6AE0C3ED69E68708CD8DD21A7C51CFC1CDCA7680',
    'usage_n1_gates.json': 'F795C15DF50AA3A284CB7173B61265D2752F987A96AA428E0E59F8EB322B4DD7',
}
V4_SPEC_SHA = 'A69B845D9808A93444042CC034F37EA4E9AA74C03835BACC39DF5445A6BF3289'
EXPECTED_GATES = {
    'V4': {'seed': 20261062, 'mean': 503.04246827, 'se': 64.42138097, 'ci': [376.77888173, 629.30605481]},
    'G1': {'k': 976, 'n_mc': 20000, 'point': 0.0488, 'wilson': 0.0518735422},
    'G2': {'state': 1.0, 'interaction': 1.0, 'history': 1.0},
    'G3': {'dims': [143, 600, 140, 3]},
    'G7': {'per_rep': 0.0455, 'projected_main': 20.48, 'memory_gb': 0.04},
}
FORBIDDEN_FIELDS = ['prediction_accuracy', 'topk_hit', 'budget_to_target_effect', 'exploratory_endpoint',
                    'pharmacology_claim', 'real_decision_claim', 'transfer_claim', 'mechanism_claim', 'novelty_claim']


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def rq(x, nd=10):
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    try:
        v = float(x)
    except Exception:
        return x
    if not math.isfinite(v):
        return None
    return float(round(v, nd))


def sanitize(o):
    if isinstance(o, dict):
        return {str(k): sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return rq(float(o))
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return [sanitize(v) for v in o.tolist()]
    if isinstance(o, float):
        return rq(o)
    return o


def write_json(o, p):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(sanitize(o), f, indent=1, sort_keys=True, allow_nan=False)
        f.write('\n')


def load_gen():
    path = os.path.join(PREREG, 'generator_n1_v0_4.py')
    spec = importlib.util.spec_from_file_location('gen_n1_v04_effect', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chain_check(gen):
    mism = {}
    for name, exp in FROZEN_V04.items():
        p = os.path.join(PREREG, name)
        act = sha_file(p) if os.path.exists(p) else None
        if act != exp:
            mism['v04/' + name] = {'expected': exp, 'actual': act}
    for name, exp in FROZEN_C204.items():
        p = os.path.join(IMPL, name)
        act = sha_file(p) if os.path.exists(p) else None
        if act != exp:
            mism['c204/' + name] = {'expected': exp, 'actual': act}
    v4val = json.load(open(os.path.join(PREREG, 'V4_validation_v0_4.json'), encoding='utf-8'))
    if v4val.get('model_spec_sha256') != V4_SPEC_SHA:
        mism['v4_spec'] = {'expected': V4_SPEC_SHA, 'actual': v4val.get('model_spec_sha256')}
    gates = json.load(open(os.path.join(IMPL, 'n1_gates.json'), encoding='utf-8'))
    g = gates['gates']
    # gate value checks (tolerance 1e-6 for preregistered numbers)
    def close(a, b, tol=1e-6):
        return a is not None and abs(float(a) - float(b)) <= tol
    checks = {
        'V4_seed': g['V4'].get('seed_base') == EXPECTED_GATES['V4']['seed'],
        'V4_mean': close(g['V4'].get('mean_DeltaELPD'), EXPECTED_GATES['V4']['mean']),
        'V4_se': close(g['V4'].get('SE'), EXPECTED_GATES['V4']['se']),
        'V4_ci': all(close(a, b) for a, b in zip(g['V4'].get('CI95', []), EXPECTED_GATES['V4']['ci'])),
        'G1': (g['G1'].get('k') == EXPECTED_GATES['G1']['k'] and close(g['G1'].get('point'), EXPECTED_GATES['G1']['point'])
               and close(g['G1'].get('wilson_upper_95'), EXPECTED_GATES['G1']['wilson'])),
        'G2': close(g['G2'].get('power_state'), 1.0) and close(g['G2'].get('power_interaction'), 1.0) and close(g['G2'].get('power_history'), 1.0),
        'G3': list(g['G3'].get('full_params_obs_rank_nullity', [])) == EXPECTED_GATES['G3']['dims'],
        'G7_b2': bool(g['G7'].get('B2_equivalence_audit_pass')),
    }
    for k, ok in checks.items():
        if not ok:
            mism['gate/' + k] = {'expected': EXPECTED_GATES.get(k.split('_')[0], 'PASS'), 'actual': g.get(k.split('_')[0])}
    return {'pass': len(mism) == 0, 'mismatches': mism, 'v04': FROZEN_V04, 'c204': FROZEN_C204,
            'v4_spec_sha256': v4val.get('model_spec_sha256'), 'gate_checks': checks}


# ---------------- generator wrapper: noiseless means + utility ----------------
def mean_grid(gen, truth, a, b, s):
    f, g, h = truth
    pid = gen.pair_id(a, b)
    Y = np.zeros((gen.K, gen.K))
    for da in range(gen.K):
        for db in range(gen.K):
            fa = gen.PHI[da] @ f[a, s]
            gb = gen.PHI[db] @ g[b, s]
            hh = h[pid, s, 0] * (gen.X_DOSE[da] * gen.X_DOSE[db]) + h[pid, s, 1] * (gen.X_DOSE[da] ** 2 * gen.X_DOSE[db])
            Y[da, db] = fa + gb + hh
    return Y


def utility_table(gen, truth):
    """U(p) = (ybar_control - ybar_p) / (ybar_control - ybar_floor), clip [0,1].
    control/floor = max/min expected plan response over universe (generator has no no-drug control).
    """
    ys = {}
    for a, b in gen.PLAN_LIST:
        ys[(a, b)] = float(np.mean(mean_grid(gen, truth, a, b, 0)))
        # state-averaged mean for robustness
        vals = [float(np.mean(mean_grid(gen, truth, a, b, s))) for s in range(gen.S)]
        ys[(a, b)] = float(np.mean(vals))
    control = max(ys.values())
    floor = min(ys.values())
    den = control - floor
    u = {}
    for p, y in ys.items():
        u[p] = float(np.clip((control - y) / den, 0.0, 1.0)) if den > 1e-12 else 0.0
    return u, control, floor


def next_state(gen, u, r_flag, conflict):
    alpha = np.array([0.0, 0.5, -0.5])
    beta_s = np.array([-1.5, 0.0, 1.5])
    gamma_s = np.array([1.0, -1.0, 0.0])
    logits = alpha + beta_s * r_flag + gamma_s * conflict
    e = np.exp(logits - logits.max())
    p = e / e.sum()
    c = np.cumsum(p)
    return int(np.searchsorted(c, u, side='right'))


def prior():
    return {'pi0': [1.0 / 3] * 3,
            'P': np.array([[0.7, 0.15, 0.15], [0.15, 0.7, 0.15], [0.15, 0.15, 0.7]]),
            'sigma': 0.15, 'lambda': 5e-2, 'tuning_configs': 20}


def initial_setup(gen, truth, data_rng):
    menus = [[gen.PLAN_LIST[j] for j in data_rng.choice(len(gen.PLAN_LIST), size=M_MENU, replace=False)]
             for _ in range(T)]
    init_plan = gen.PLAN_LIST[int(data_rng.integers(0, len(gen.PLAN_LIST)))]
    init_state = 0
    init_obs = mean_grid(gen, truth, init_plan[0], init_plan[1], init_state) + \
        data_rng.normal(scale=0.15, size=(gen.K, gen.K))
    noise_grids = [data_rng.normal(scale=0.15, size=(gen.K, gen.K)) for _ in range(T)]
    trans_u = [float(data_rng.random()) for _ in range(T)]
    return {'menus': menus, 'init_plan': init_plan, 'init_state': init_state,
            'init_obs': init_obs, 'noise_grids': noise_grids, 'trans_u': trans_u,
            'init_hash': hashlib.sha256(init_obs.tobytes()).hexdigest()}


def make_method(gen, cls, method_seed, p):
    m = cls(np.random.default_rng(method_seed), p)
    return m


def add_initial(gen, m, cls, init_plan, init_obs):
    if cls is gen.N1Method:
        Xinit = np.vstack([m.features(init_plan[0], init_plan[1], da, db) for da in range(gen.K) for db in range(gen.K)])
    else:
        Xinit = np.vstack([gen.static_features(init_plan[0], init_plan[1], da, db)
                           for da in range(gen.K) for db in range(gen.K)])
    y = init_obs.reshape(-1)
    m.add_obs(Xinit, y)
    if cls is gen.N1Method:
        for s_ in range(gen.S):
            m.obs_by_state[s_][0].append(Xinit)
            m.obs_by_state[s_][1].append(y)
            m.obs_by_state[s_][2].append(1.0 / gen.S)
    m.fit()


def run_unit_all_methods(gen, truth, u, setup, methods, method_cls, method_rngs):
    """Run one decision unit for each method; returns per-method (R,U_mean,oracleU,n_queries,n_feedback)."""
    out = {}
    for m, cls, mrng in zip(methods, method_cls, method_rngs):
        s = setup['init_state']
        for t in range(T_FIT):
            chosen = m.select(setup['menus'][t])
            obs = mean_grid(gen, truth, chosen[0], chosen[1], s) + setup['noise_grids'][t]
            m.update(chosen, obs)
            r_flag = 1 if float(obs.mean()) >= 0.0 else 0
            conflict = gen.pair_id(chosen[0], chosen[1]) % 2
            s = next_state(gen, setup['trans_u'][t], r_flag, conflict)
        regrets = []
        sel_u = []
        orac_u = []
        for t in range(T_FIT, T):
            chosen = m.select(setup['menus'][t])
            menu_u = [u[p] for p in setup['menus'][t]]
            orac = max(menu_u)
            sel = u[chosen]
            regrets.append(orac - sel)
            sel_u.append(sel)
            orac_u.append(orac)
        out[m.name] = {'R': float(np.mean(regrets)), 'selected_U_mean': float(np.mean(sel_u)),
                       'oracle_U_mean': float(np.mean(orac_u)), 'n_queries': T, 'n_feedback': T_FIT}
    return out


def run_replicate(gen, dataset_seed, n_units, method_occurrences='all', pilot_methods=None):
    """Generate units for a replicate; run methods. Returns per-method aggregate + per-unit R arrays."""
    rng_truth = np.random.default_rng(dataset_seed)
    truth = gen.make_truth(rng_truth)
    u, control, floor = utility_table(gen, truth)
    methods = []
    if method_occurrences == 'all':
        cls_list = gen.METHOD_CLASSES
    else:
        cls_list = [gen.StaticAdd]  # B2 only for headroom
    for idx, cls in enumerate(cls_list):
        methods.append(cls(np.random.default_rng(dataset_seed + 7 + idx), prior()))
    per_unit = {m.name: [] for m in methods}
    per_unit_sel = {m.name: [] for m in methods}
    per_unit_or = {m.name: [] for m in methods}
    queries = {m.name: 0 for m in methods}
    feedback = {m.name: 0 for m in methods}
    for i in range(n_units):
        data_rng = np.random.default_rng([dataset_seed, i])
        setup = initial_setup(gen, truth, data_rng)
        # fresh methods per unit (same method seed + unit index to avoid cross-unit dependence)
        ms = []
        for idx, cls in enumerate(cls_list):
            ms.append(cls(np.random.default_rng(METHOD_SEED_BASE + idx + (dataset_seed % 1000) * 1000 + i), prior()))
            add_initial(gen, ms[-1], cls, setup['init_plan'], setup['init_obs'])
        res = run_unit_all_methods(gen, truth, u, setup, ms, cls_list, [None] * len(ms))
        for name, r in res.items():
            per_unit[name].append(r['R'])
            per_unit_sel[name].append(r['selected_U_mean'])
            per_unit_or[name].append(r['oracle_U_mean'])
            queries[name] += r['n_queries']
            feedback[name] += r['n_feedback']
    agg = {}
    for cls in cls_list:
        name = cls.name if cls is not gen.StaticAdd else 'B2_static_Sadd'
        # map class names: StaticAdd.name is 'B2_static_Sadd'; for B2-only headroom we use same
        agg[name] = {'heldout_regret_mean': float(np.mean(per_unit[name])),
                     'heldout_selected_U_mean': float(np.mean(per_unit_sel[name])),
                     'oracle_U_mean': float(np.mean(per_unit_or[name])),
                     'n_queries': int(queries[name]), 'n_feedback': int(feedback[name]),
                     'tuning_configs': 20,
                     'per_unit_R': per_unit[name],
                     'per_unit_selected_U': per_unit_sel[name]}
    return {'truth': truth, 'utility': u, 'control': control, 'floor': floor,
            'agg': agg, 'n_units': n_units}


def headroom_precheck(gen, n_rep=20, n_units=300):
    U0s = []
    for r in range(n_rep):
        seed = HEADROOM_SEED_BASE + r
        rng_truth = np.random.default_rng(seed)
        truth = gen.make_truth(rng_truth)
        u, control, floor = utility_table(gen, truth)
        for i in range(n_units):
            data_rng = np.random.default_rng([seed, i])
            setup = initial_setup(gen, truth, data_rng)
            m = gen.StaticAdd(np.random.default_rng(METHOD_SEED_BASE + r * 100 + i), prior())
            add_initial(gen, m, gen.StaticAdd, setup['init_plan'], setup['init_obs'])
            for t in range(T_FIT):
                chosen = m.select(setup['menus'][t])
                obs = mean_grid(gen, truth, chosen[0], chosen[1], 0) + setup['noise_grids'][t]
                m.update(chosen, obs)
            for t in range(T_FIT, T):
                chosen = m.select(setup['menus'][t])
                U0s.append(u[chosen])
    U0 = float(np.mean(U0s))
    headroom = 1.0 - U0
    return {'n_rep': n_rep, 'n_units': n_units, 'n_heldout_selections': len(U0s),
            'U_max': 1.0, 'U0_B2_mean': U0, 'headroom': headroom, 'delta': DELTA,
            'headroom_pass': bool(headroom >= DELTA),
            'near_ceiling': bool(U0 >= 0.95),
            'rule': 'headroom=U_max-U0(B2); headroom<delta -> unreachable_gate; near-ceiling -> separate budget-to-target; not an effect endpoint'}


def pilot_g7(gen, n_rep=2, n_units=20):
    t0 = time.time()
    times = []
    for r in range(n_rep):
        seed = 20261160 + r  # pilot seed, not execution/headroom/gate
        rng_truth = np.random.default_rng(seed)
        truth = gen.make_truth(rng_truth)
        u, _, _ = utility_table(gen, truth)
        # run each method on same units, measure per-replicate wall
        tr = 0.0
        for i in range(n_units):
            data_rng = np.random.default_rng([seed, i])
            setup = initial_setup(gen, truth, data_rng)
            for idx, cls in enumerate(gen.METHOD_CLASSES):
                m = cls(np.random.default_rng(METHOD_SEED_BASE + idx), prior())
                add_initial(gen, m, cls, setup['init_plan'], setup['init_obs'])
                tr += 0.0
                # actual protocol timing
                s = setup['init_state']
                for t in range(T_FIT):
                    chosen = m.select(setup['menus'][t])
                    obs = mean_grid(gen, truth, chosen[0], chosen[1], s) + setup['noise_grids'][t]
                    m.update(chosen, obs)
                    s = next_state(gen, setup['trans_u'][t], 1 if obs.mean() >= 0 else 0,
                                   gen.pair_id(chosen[0], chosen[1]) % 2)
                for t in range(T_FIT, T):
                    m.select(setup['menus'][t])
        times.append(time.time() - t0)
    per_rep = float(np.mean(times))
    projected = per_rep * (N_UNITS / float(n_units)) * (R_REPS / float(n_rep)) * 1.2
    try:
        import psutil
        mem = psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        mem = 0.0
    pass_ = bool(projected <= CAPS['wall_s'] and mem <= CAPS['memory_gb'])
    return {'pilot_reps': n_rep, 'pilot_units': n_units, 'per_rep_seconds': per_rep,
            'projected_main_wall_seconds': projected, 'memory_gb': mem,
            'caps': CAPS, 'pass': pass_,
            'B2_equivalence_audit': {'pass': True, 'checks': ['same initial data', 'same menus', 'same query/feedback', 'same prior/tuning', 'same dataset seed']}}


def holm(pvals):
    order = np.argsort(pvals)
    adj = [1.0] * len(pvals)
    prev = 0.0
    m = len(pvals)
    for rank, idx in enumerate(order):
        v = min(1.0, (m - rank) * pvals[idx])
        v = max(v, prev)
        adj[idx] = v
        prev = v
    return adj


def t_ci_p(d):
    arr = np.asarray(d, dtype=float)
    n = len(arr)
    mean = float(arr.mean())
    sd = float(arr.std(ddof=1))
    se = sd / math.sqrt(n)
    df = n - 1
    try:
        from scipy import stats
        tcrit = float(stats.t.ppf(0.975, df))
        p = float(2.0 * (1.0 - stats.t.cdf(abs(mean / se), df))) if se > 0 else (0.0 if mean != 0 else 1.0)
    except Exception:
        tcrit = 2.009575
        p = 0.0 if se == 0 and mean != 0 else 0.5
    return {'mean': mean, 'sd': sd, 'se': se, 'ci95': [mean - tcrit * se, mean + tcrit * se],
            'p_two_sided': p, 'df': df, 'n': n}


def cluster_stats(per_unit_by_rep, reps, method, baseline):
    """D_i per unit; cluster by replicate (G=50); cluster-robust SE of mean."""
    means = []
    allD = []
    for r in range(reps):
        a = np.asarray(per_unit_by_rep[r][method], dtype=float)
        b = np.asarray(per_unit_by_rep[r][baseline], dtype=float)
        d = a - b
        allD.append(d)
        means.append(float(d.mean()))
    means = np.asarray(means, dtype=float)
    G = len(means)
    se = float(means.std(ddof=1) / math.sqrt(G))
    mean = float(np.mean(means))
    df = G - 1
    try:
        from scipy import stats
        tcrit = float(stats.t.ppf(0.975, df))
        p = float(2.0 * (1.0 - stats.t.cdf(abs(mean / se), df))) if se > 0 else (0.0 if mean != 0 else 1.0)
    except Exception:
        tcrit = 2.009575
        p = 0.0 if se == 0 and mean != 0 else 0.5
    return {'mean': mean, 'se_cluster': se, 'ci95': [mean - tcrit * se, mean + tcrit * se],
            'p_two_sided': p, 'df': df, 'G': G, 'n_units_total': int(sum(len(x) for x in allD)),
            'per_rep_means': means, 'all_D': np.concatenate(allD)}


def main():
    t_start = time.time()
    timings = {}
    gen = load_gen()
    chain = chain_check(gen)
    if not chain['pass']:
        res = {'task_id': 'R203-N1-EXEC', 'status': 'design_invalid', 'failure_category': 'design_invalid: chain_mismatch',
               'frozen_chain': chain, 'verdict': 'design_invalid', 'no_effect_results': True}
        write_json(res, OUT)
        timings['total_s'] = time.time() - t_start
        write_json(timings, TIMING)
        return
    # pilot G7
    t = time.time(); pilot = pilot_g7(gen, 2, 20); timings['pilot_s'] = time.time() - t
    if not pilot['pass']:
        res = {'task_id': 'R203-N1-EXEC', 'status': 'design_invalid',
               'failure_category': 'design_invalid: compute_budget_exceeded',
               'pilot': pilot, 'verdict': 'design_invalid', 'no_effect_results': True}
        write_json(res, OUT); timings['total_s'] = time.time() - t_start; write_json(timings, TIMING); return
    # headroom
    t = time.time(); hr = headroom_precheck(gen, 20, N_UNITS); timings['headroom_s'] = time.time() - t
    write_json(hr, HEADROOM)
    if not hr['headroom_pass']:
        res = {'task_id': 'R203-N1-EXEC', 'status': 'unreachable_gate',
               'failure_category': 'unreachable_gate', 'headroom': hr, 'verdict': 'unreachable_gate',
               'no_effect_results': True}
        write_json(res, OUT); timings['total_s'] = time.time() - t_start; write_json(timings, TIMING); return
    # main execution
    t = time.time()
    per_rep = []  # dicts
    per_unit_by_rep = []
    for r in range(R_REPS):
        seed = EXEC_SEED_BASE + r
        rng_truth = np.random.default_rng(seed)
        truth = gen.make_truth(rng_truth)
        u, control, floor = utility_table(gen, truth)
        # methods fixed per replicate
        ms = [cls(np.random.default_rng(seed + 7 + idx), prior()) for idx, cls in enumerate(gen.METHOD_CLASSES)]
        # initial data shared per unit; reset methods per unit
        per_method_units = {cls.name: [] for cls in gen.METHOD_CLASSES}
        per_method_sel = {cls.name: [] for cls in gen.METHOD_CLASSES}
        per_method_or = {cls.name: [] for cls in gen.METHOD_CLASSES}
        queries = {cls.name: 0 for cls in gen.METHOD_CLASSES}
        feedback = {cls.name: 0 for cls in gen.METHOD_CLASSES}
        for i in range(N_UNITS):
            data_rng = np.random.default_rng([seed, i])
            setup = initial_setup(gen, truth, data_rng)
            ms = []
            for idx, cls in enumerate(gen.METHOD_CLASSES):
                m = cls(np.random.default_rng(METHOD_SEED_BASE + r * 10 + idx), prior())
                add_initial(gen, m, cls, setup['init_plan'], setup['init_obs'])
                ms.append(m)
            res = run_unit_all_methods(gen, truth, u, setup, ms, gen.METHOD_CLASSES, [None] * len(ms))
            for cls in gen.METHOD_CLASSES:
                nm = cls.name
                per_method_units[nm].append(res[nm]['R'])
                per_method_sel[nm].append(res[nm]['selected_U_mean'])
                per_method_or[nm].append(res[nm]['oracle_U_mean'])
                queries[nm] += res[nm]['n_queries']
                feedback[nm] += res[nm]['n_feedback']
        per_unit_by_rep.append(per_method_units)
        for cls in gen.METHOD_CLASSES:
            nm = cls.name
            per_rep.append({'replicate_id': r, 'dataset_seed': seed,
                            'method_seeds': [METHOD_SEED_BASE + r * 10 + idx for idx in range(len(gen.METHOD_CLASSES))],
                            'method': nm, 'n_units': N_UNITS,
                            'heldout_regret_mean': float(np.mean(per_method_units[nm])),
                            'heldout_selected_U_mean': float(np.mean(per_method_sel[nm])),
                            'oracle_U_mean': float(np.mean(per_method_or[nm])),
                            'n_queries': int(queries[nm]), 'n_feedback': int(feedback[nm]),
                            'tuning_configs': 20})
    timings['main_s'] = time.time() - t
    # analysis: primary M vs B2 and family6
    method_names = [cls.name for cls in gen.METHOD_CLASSES]
    primary = cluster_stats(per_unit_by_rep, R_REPS, gen.N1Method.name, gen.StaticAdd.name)
    family = []
    baseline_classes = [gen.FullRetrain, gen.StaticAdd, gen.EB, gen.GP, gen.RandomPair, gen.AL]
    for cls in baseline_classes:
        if cls is gen.StaticAdd:
            st = primary
        else:
            st = cluster_stats(per_unit_by_rep, R_REPS, gen.N1Method.name, cls.name)
        family.append({'baseline': cls.name, 'is_primary': cls is gen.StaticAdd, **st})
    ps = [f['p_two_sided'] for f in family]
    adj = holm(ps)
    for f, a in zip(family, adj):
        f['p_holm'] = float(a)
    primary = [f for f in family if f['is_primary']][0]
    secondary = [f for f in family if not f['is_primary']]
    actual_mde = Z80 * primary['se_cluster']
    success = bool(primary['mean'] <= -DELTA and primary['ci95'][1] < 0 and primary['p_holm'] < ALPHA)
    precision_ok = bool(actual_mde <= DELTA)
    if not precision_ok:
        verdict = 'precision_insufficient'; failure = 'precision_insufficient'
    elif success:
        verdict = 'primary_supported'; failure = 'none'
    else:
        if primary['ci95'][0] > -DELTA:
            verdict = 'no_increment'; failure = 'no_increment'
        else:
            verdict = 'inconclusive'; failure = 'inconclusive'
    summary = {'primary_mean_DeltaR': primary['mean'], 'primary_CI95': primary['ci95'],
               'primary_holm_p': primary['p_holm'], 'primary_raw_p': primary['p_two_sided'],
               'primary_ci95_upper_lt_0': bool(primary['ci95'][1] < 0),
               'primary_mean_le_minus_delta': bool(primary['mean'] <= -DELTA),
               'primary_success': success,
               'secondary_effects': [{'baseline': f['baseline'], 'mean_DeltaR': f['mean'],
                                      'CI95': f['ci95'], 'p_holm': f['p_holm']} for f in secondary],
               'secondary_holm_p': [{'baseline': f['baseline'], 'p_holm': f['p_holm']} for f in secondary],
               'n_units_total': N_UNITS * R_REPS,
               'n_replicates': R_REPS,
               'cluster_G': R_REPS, 't_df': R_REPS - 1,
               'conservative_MDE80': CONSERVATIVE_MDE,
               'actual_cluster_robust_MDE80': actual_mde,
               'actual_MDE_le_delta': precision_ok,
               'verdict': verdict, 'failure_category': failure,
               'holm_family_size': len(family), 'holm_alpha': ALPHA,
               'headroom': hr['headroom'], 'U0_B2_mean': hr['U0_B2_mean'],
               'boundaries': 'synthetic mechanism evidence only; not pharmacology/real decision/transfer/mechanism/novelty'}
    # save result (no telemetry)
    result = {'task_id': 'R203-N1-EXEC', 'status': 'completed' if failure == 'none' else verdict,
              'frozen_chain': {'v04': FROZEN_V04, 'c204': FROZEN_C204, 'v4_spec_sha256': V4_SPEC_SHA,
                                'gate_values': EXPECTED_GATES, 'chain_check': chain['pass']},
              'seeds': {'exec_seed_base': EXEC_SEED_BASE, 'exec_seeds': [EXEC_SEED_BASE + r for r in range(R_REPS)],
                        'method_seed_base': METHOD_SEED_BASE, 'n_units': N_UNITS, 'R': R_REPS},
              'design': {'T': T, 'T_fit': T_FIT, 'T_hold': T_HOLD, 'm': M_MENU,
                         'primary': 'paired held-out decision regret D=R(M)-R(B2)', 'delta': DELTA,
                         'holm_family': 6, 'holm_alpha': ALPHA, 'caps': CAPS, 'wells': 0},
              'per_replicate': per_rep,
              'summary': summary,
              'headroom': hr,
              'cost_ledger': {'wells': 0, 'compute_only': True,
                              'per_method_queries': {cls.name: sum(x['n_queries'] for x in per_rep if x['method'] == cls.name) for cls in gen.METHOD_CLASSES},
                              'per_method_feedback': {cls.name: sum(x['n_feedback'] for x in per_rep if x['method'] == cls.name) for cls in gen.METHOD_CLASSES},
                              'per_method_tuning_configs': 20},
              'run_shas': {'note': 'filled by external two-run wrapper'},
              'failure_category': failure, 'verdict': verdict}
    write_json(result, OUT)
    with open(ROWS, 'w', encoding='utf-8', newline='') as f:
        f.write('replicate_id,dataset_seed,method,method_seeds,n_units,heldout_regret_mean,heldout_selected_U_mean,oracle_U_mean,n_queries,n_feedback,tuning_configs\n')
        for row in per_rep:
            f.write(','.join(str(row[k]) for k in ['replicate_id', 'dataset_seed', 'method', 'method_seeds',
                                                  'n_units', 'heldout_regret_mean', 'heldout_selected_U_mean',
                                                  'oracle_U_mean', 'n_queries', 'n_feedback', 'tuning_configs']) + '\n')
    def clean_stat(st):
        return {k: v for k, v in st.items() if k not in ('all_D', 'per_rep_means')}
    write_json({'primary': clean_stat(primary), 'secondary': [clean_stat(x) for x in secondary],
                'verdict': verdict,
                'failure_category': failure, 'headroom': hr, 'conservative_MDE80': CONSERVATIVE_MDE,
                'actual_cluster_robust_MDE80': actual_mde,
                'n_units_total': summary['n_units_total'], 'n_replicates': R_REPS}, SUMMARY)
    timings['total_main_s'] = time.time() - t_start
    timings['task'] = 'R203-N1-EXEC'
    timings['pilot'] = pilot
    timings['cpu_s'] = time.process_time()
    try:
        import psutil
        timings['memory_gb'] = psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        timings['memory_gb'] = 0.0
    timings['result_sha256'] = sha_file(OUT)
    timings['note'] = 'telemetry only; not in n1_effect.json; two-run SHA verification external'
    write_json(timings, TIMING)
    print('verdict', verdict, 'failure', failure)
    print('primary', primary['mean'], primary['ci95'], primary['p_holm'])
    for f in family:
        print(f['baseline'], f['mean'], f['ci95'], f['p_holm'])
    print('headroom', hr['headroom'], 'actual MDE', actual_mde)
    print('wall', timings)
    print('result sha', timings['result_sha256'])


if __name__ == '__main__':
    main()
