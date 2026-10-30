#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-B T1 MAIN execution (frozen v0.4; synthetic only).

NO real response data, NO T2/T3, NO wet experiment, NO frozen-knob changes.
Writes t1_main.json (deterministic, no timestamps/wall), t1_main_rows.csv, timing_main.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
T1MVP = os.path.abspath(os.path.join(BASE, '..', 't1_mvp'))
sys.path.insert(0, T1MVP)

import t1_sim as sim  # noqa: E402
import t1_qualification as qual  # noqa: E402

PRIMARY = {'B_C': 1200.0, 'B_E': 16, 'kappa': 1.0, 'sigma': 0.10}
DELTA = 0.10
ALPHA = 0.05
N_REP = 500
N_SENS_REP = 50
BOOT_B = 5000
BOOT_SEED = 20261130
OUT = os.path.join(BASE, 't1_main.json')
CSV = os.path.join(BASE, 't1_main_rows.csv')
TIMING = os.path.join(BASE, 'timing_main.json')

FROZEN = {
    'PROBLEM_B_v0_4.md': 'D6B37E704DE141FE481A73D4BDDC0FFA6CBB0BA7FA6A686004D568415E6C5C99',
    'DESIGN_B_v0_4.md': '9112EDDC3180BA6101DF76CB34282BE84E7E9DF0EBD3EC714C4999388E7D01CD',
    'design_B_revision_v0_4.py': 'E4968C701DB031BF246767D821A31DC5B8EF9AB50D3A0694462E023F661A3A5E',
    'design_B_v0_4.json': 'A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1',
    'DECISION_R201_T1_MAIN.md': '19719E25774EDA298E354018EA786DDE5FC17F9BFC75E234CDFF5B81D9E1820B',
}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def frozen_check():
    root = os.path.abspath(os.path.join(BASE, '..'))
    ok = True
    got = {}
    for name, expected in FROZEN.items():
        path = os.path.join(root, name)
        actual = sha_file(path) if os.path.exists(path) else None
        got[name] = actual
        if actual != expected:
            ok = False
    if not ok:
        raise SystemExit('FROZEN_CHAIN_MISMATCH: ' + json.dumps({k: v for k, v in got.items() if v != FROZEN.get(k)}))
    return {'pass': True, 'checked': got}


def quick_gates():
    gates = {
        'oracle_recoverable': qual.gate_oracle(),
        'null_fp': qual.gate_null_fp(100),
        'ev_approx': qual.gate_ev(5),
        'cost_ledger': qual.gate_cost(),
        'no_leakage': qual.gate_no_leakage(),
        'ten_arms': qual.gate_arms(),
        'menu_hash': qual.gate_hash(),
    }
    failed = [k for k, v in gates.items() if not v.get('pass', False)]
    return gates, failed


def row_for(world, arm, replicate, seed):
    res = sim.run_arm(arm, world, PRIMARY['B_C'], PRIMARY['B_E'], PRIMARY['kappa'], seed)
    true_u = [float(world.u_true[p]) for p in sim.M_IDS]
    oracle = int(world.oracle_M)
    selected = int(res['selected'])
    u_or = world.u_true[oracle]
    u_sel = world.u_true[selected]
    topk = sorted(sim.M_IDS, key=lambda p: -world.u_true[p])[:sim.K_TOPK] if hasattr(sim, 'K_TOPK') else sorted(sim.M_IDS, key=lambda p: -world.u_true[p])[:5]
    topk_hit = int(selected in topk)
    denom = u_or - float(np.mean(true_u))
    regret = float((u_or - u_sel) / denom) if denom > 1e-12 else 0.0
    regret = max(0.0, min(1.0, regret))
    ledger = res['ledger']
    return {
        'replicate_id': int(replicate), 'arm': arm,
        'selection_accuracy': int(res['correct']),
        'topk_hit': topk_hit,
        'normalized_regret': regret,
        'chosen_plan': selected, 'oracle_plan': oracle,
        'cost_ledger': {'compute_s': ledger['compute_s'], 'exp_keys': ledger['exp_keys'],
                        'filler_wells': ledger['filler_wells'], 'spend_cu': res['spend_cu'], 'T_cu': res['T_cu']},
        'compute_steps': int(round(ledger['compute_s'] / sim.STEP_COST_S)),
        'experiments': int(ledger['exp_keys']), 'filler': int(ledger['filler_wells']),
        'failure_class': 'none',
    }


def one_sided_p(d):
    arr = np.asarray(d, dtype=float)
    n = len(arr)
    m = float(arr.mean())
    sd = float(arr.std(ddof=1)) if n > 1 else 0.0
    if sd <= 0:
        return 0.5 if m <= 0 else 0.0
    z = m / (sd / math.sqrt(n))
    return float(0.5 * (1.0 - math.erf(z / math.sqrt(2.0))))


def bootstrap_ci(d):
    arr = np.asarray(d, dtype=float)
    rng = np.random.default_rng(BOOT_SEED)
    n = len(arr)
    vals = np.empty(BOOT_B)
    for b in range(BOOT_B):
        idx = rng.integers(0, n, size=n)
        vals[b] = arr[idx].mean()
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def hb_stats(primary_rows):
    by = {}
    for r in primary_rows:
        by.setdefault(r['replicate_id'], {})[r['arm']] = r['selection_accuracy']
    d1 = [by[i]['pi_dual'] - by[i]['C7_compute_only'] for i in sorted(by)]
    d2 = [by[i]['pi_dual'] - by[i]['C7_experiment_only'] for i in sorted(by)]
    c = []
    raw = [one_sided_p(d1), one_sided_p(d2)]
    means = [float(np.mean(d1)), float(np.mean(d2))]
    cis = [bootstrap_ci(d1), bootstrap_ci(d2)]
    # Holm adjusted p for two one-sided tests
    order = sorted(range(2), key=lambda i: raw[i])
    adj = [0.0, 0.0]
    adj[order[0]] = min(1.0, 2.0 * raw[order[0]])
    adj[order[1]] = min(1.0, max(adj[order[0]], raw[order[1]]))
    names = ['dual_vs_C7_compute_only', 'dual_vs_C7_experiment_only']
    for i in range(2):
        c.append({'name': names[i], 'n': len(d1), 'mean_diff': means[i],
                  'ci95': cis[i], 'p_raw_one_sided': raw[i], 'p_holm': adj[i],
                  'positive': bool(means[i] > 0), 'holm_significant': bool(adj[i] < ALPHA and means[i] > 0),
                  'meets_delta': bool(means[i] >= DELTA)})
    both_sig_pos = all(x['holm_significant'] for x in c)
    both_meet = all(x['meets_delta'] for x in c)
    if both_sig_pos and both_meet:
        verdict = 'H_B_supported'
    elif both_sig_pos and not both_meet:
        verdict = 'below_delta'
    elif sum(1 for x in c if x['holm_significant']) == 1:
        verdict = 'partial_decision_benefit'
    else:
        verdict = 'no_decision_benefit'
    return {'delta_min': DELTA, 'alpha': ALPHA, 'holm': 'two one-sided contrasts, Holm alpha=0.05',
            'contrasts': c, 'both_significant_positive': bool(both_sig_pos),
            'both_meet_delta': bool(both_meet), 'verdict': verdict,
            'rule': 'H_B iff both Holm-significant positive AND both point>=delta; one only=partial; none=no_decision_benefit; both sig but below delta=below_delta'}


def config_table():
    pairs = [(300, 4), (1200, 16), (3600, 64)]
    kappas = [0.1, 1.0, 10.0]
    sigmas = [0.05, 0.10]
    cells = []
    idx = 0
    for bc, be in pairs:
        for kappa in kappas:
            for sigma in sigmas:
                is_primary = (bc == 1200 and be == 16 and kappa == 1.0 and sigma == 0.10)
                cells.append({'cell_index': idx, 'B_C': bc, 'B_E': be, 'kappa': kappa, 'sigma': sigma,
                              'role': 'primary' if is_primary else 'sensitivity'})
                idx += 1
    return cells


def main():
    t_start = time.time()
    timings = {}
    frozen = frozen_check()
    t_q = time.time()
    gates, failed = quick_gates()
    timings['qualification_quick_s'] = time.time() - t_q
    if failed:
        result = {'task': 'R201-B-T1-MAIN', 'status': 'design_invalid',
                  'reason': 'qualification_quick_gates_failed: ' + ','.join(failed),
                  'no_main_results': True}
        with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(result, f, indent=1, sort_keys=True)
            f.write('\n')
        raise SystemExit(0)

    # ---- primary 500 x 10 ----
    t_p = time.time()
    primary_rows = []
    for r in range(N_REP):
        world = sim.World(20261130 + r)
        for a in sim.ARMS:
            primary_rows.append(row_for(world, a, r, 20261130 + r))
    timings['primary_s'] = time.time() - t_p
    primary_agg = {}
    for a in sim.ARMS:
        vals = [x['selection_accuracy'] for x in primary_rows if x['arm'] == a]
        primary_agg[a] = {'n': len(vals), 'mean_selection_accuracy': float(np.mean(vals))}

    hb = hb_stats(primary_rows)

    # ---- sensitivity 17 x 50 (descriptive only; wall allows per T1-MVP pilot projection) ----
    t_s = time.time()
    sens_cells = []
    for cell in [c for c in config_table() if c['role'] == 'sensitivity']:
        acc = {a: [] for a in sim.ARMS}
        for r in range(N_SENS_REP):
            w = sim.World(20261131 + cell['cell_index'] * 1000 + r, sigma=cell['sigma'])
            for a in sim.ARMS:
                res = sim.run_arm(a, w, float(cell['B_C']), int(cell['B_E']), float(cell['kappa']),
                                  seed=20261131 + cell['cell_index'] * 1000 + r)
                acc[a].append(res['correct'])
        cell_out = {'cell_index': cell['cell_index'], 'B_C': cell['B_C'], 'B_E': cell['B_E'],
                    'kappa': cell['kappa'], 'sigma': cell['sigma'], 'replicates': N_SENS_REP,
                    'mean_selection_accuracy': {a: float(np.mean(acc[a])) for a in sim.ARMS},
                    'dual_minus_C7_compute': float(np.mean(acc['pi_dual']) - np.mean(acc['C7_compute_only'])),
                    'dual_minus_C7_experiment': float(np.mean(acc['pi_dual']) - np.mean(acc['C7_experiment_only'])),
                    'role': 'descriptive/cost_sensitive only; not H_B'}
        sens_cells.append(cell_out)
    timings['sensitivity_s'] = time.time() - t_s

    # deterministic result JSON (no wall/timestamps)
    result = {
        'task': 'R201-B-T1-MAIN',
        'status': 'completed_synthetic_only',
        'primary_config': {'B_C_s': 1200, 'B_E_keys': 16, 'kappa_s_per_CU': 1.0, 'sigma': 0.10},
        'n_replicates': N_REP, 'n_arms': len(sim.ARMS), 'arms': list(sim.ARMS),
        'primary_arm_runs': N_REP * len(sim.ARMS),
        'primary_rows': primary_rows,
        'primary_agg': primary_agg,
        'H_B': hb,
        'sensitivity': {'n_cells': len(sens_cells), 'replicates_per_cell': N_SENS_REP,
                        'cells': sens_cells,
                        'rule': 'descriptive/cost_sensitive only; not used for H_B; no main inference'},
        'qualification_quick': {'frozen_chain': frozen, 'gates': gates, 'failed_gates': failed},
        'frozen_knobs_unchanged': True,
        'no_claims': 'synthetic computational evidence only; no biological/drug decision benefit, novelty, mechanism, transfer, independent confirmation',
        'no_real_response': True, 'no_t2_t3': True,
    }
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1, sort_keys=True)
        f.write('\n')
    with open(CSV, 'w', encoding='utf-8', newline='') as f:
        f.write('replicate_id,arm,selection_accuracy,topk_hit,normalized_regret,chosen_plan,oracle_plan,compute_steps,experiments,filler,spend_cu,T_cu,failure_class\n')
        for r in primary_rows:
            f.write(','.join(str(r[k]) for k in ['replicate_id', 'arm', 'selection_accuracy', 'topk_hit',
                                                 'normalized_regret', 'chosen_plan', 'oracle_plan', 'compute_steps',
                                                 'experiments', 'filler']) + f",{r['cost_ledger']['spend_cu']},{r['cost_ledger']['T_cu']},{r['failure_class']}\n")
    timings['total_s'] = time.time() - t_start
    timings['task'] = 'R201-B-T1-MAIN'
    timings['note'] = 'main synthetic execution wall; result JSON excludes wall/timestamps for two-run determinism'
    with open(TIMING, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(timings, f, indent=1, sort_keys=True)
        f.write('\n')
    print('verdict', hb['verdict'])
    print('contrasts', [(c['name'], c['mean_diff'], c['p_holm'], c['ci95']) for c in hb['contrasts']])
    print('wall', timings)
    print('wrote', OUT, 'sha', sha_file(OUT))


if __name__ == '__main__':
    main()
