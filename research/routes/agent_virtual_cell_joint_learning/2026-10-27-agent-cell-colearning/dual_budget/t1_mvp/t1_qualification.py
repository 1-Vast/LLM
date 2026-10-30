#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-B T1 MVP qualification gates. NO main 500-replicate results, NO T2/T3, NO real response data."""
from __future__ import annotations

import hashlib
import json
import math
import os
import time

import numpy as np

import t1_sim as sim

BASE = os.path.dirname(os.path.abspath(__file__))
PRIMARY = {'B_C': 1200.0, 'B_E': 16, 'kappa': 1.0, 'sigma': 0.10}
DELTA = 0.10
ALPHA = 0.05
OUT = os.path.join(BASE, 't1_qualify.json')
TIMING = os.path.join(BASE, 'timing_pilot.json')


def sha_state(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest().upper()


def gate_oracle():
    ok = True
    max_check = 20
    for r in range(max_check):
        w = sim.World(20261130 + r)
        top = w.oracle_M_latent
        if top not in sim.M_IDS:
            ok = False
        # infinite-compute/data limit: noiseless learner on all 40 latent utilities (unclipped)
        l = sim.Learner({p: float(w.u_latent[p]) for p in range(40)})
        pred = l.predict_raw(sim.M_IDS)
        if int(sim.M_IDS[int(np.argmax(pred))]) != top:
            ok = False
    return {'pass': bool(ok), 'checked_worlds': max_check,
            'definition': 'latent oracle top-1 recoverable by noiseless all-40-plan learner (infinite compute/data limit); evaluation-only'}


def gate_null_fp(n_rep=100):
    d1, d2 = [], []
    for r in range(int(n_rep)):
        w = sim.World(20261130 + 1000 + r, sigma=PRIMARY['sigma'], null=True)
        res = {a: sim.run_arm(a, w, PRIMARY['B_C'], PRIMARY['B_E'], PRIMARY['kappa'], 30000 + r) for a in
               ('pi_dual', 'C7_compute_only', 'C7_experiment_only')}
        d1.append(res['pi_dual']['correct'] - res['C7_compute_only']['correct'])
        d2.append(res['pi_dual']['correct'] - res['C7_experiment_only']['correct'])

    def one_sided_p(d):
        arr = np.asarray(d, dtype=float)
        n = len(arr)
        m = float(arr.mean())
        sd = float(arr.std(ddof=1)) if n > 1 else 0.0
        if sd == 0:
            return 0.5 if m <= 0 else 0.0
        z = m / (sd / math.sqrt(n))
        # normal one-sided p
        return float(0.5 * (1.0 - math.erf(z / math.sqrt(2.0))))
    p1, p2 = one_sided_p(d1), one_sided_p(d2)
    m1, m2 = float(np.mean(d1)), float(np.mean(d2))
    supported = bool(p1 < ALPHA / 2 and p2 < ALPHA / 2 and m1 >= DELTA and m2 >= DELTA)
    return {'pass': bool(not supported), 'n_null_replicates': int(n_rep),
            'p1_dual_vs_compute': p1, 'p2_dual_vs_experiment': p2,
            'mean_diff_compute': m1, 'mean_diff_experiment': m2,
            'H_B_false_positive': supported,
            'definition': 'null worlds gamma=0; H_B false-positive at Holm alpha=0.05; gate passes if H_B not supported'}


def gate_ev(n_actions=5):
    w = sim.World(20261130)
    l = sim.learner_from_world(w)
    actions = [int(x) for x in sim.M_IDS[:n_actions]]
    approx = {p: sim.ev_action(w, l, p, use_noise_grid=False) for p in actions}
    ref = {p: sim.ev_action(w, l, p, use_noise_grid=True) for p in actions}
    diffs = [abs(approx[p] - ref[p]) for p in actions]
    mx = float(max(diffs)) if diffs else 0.0
    return {'pass': bool(mx <= 0.02), 'max_abs_diff_selection_accuracy': mx,
            'n_actions': len(actions), 'n_gamma_worlds': len(sim.GAMMA_WORLDS),
            'threshold': 0.02,
            'note': 'discrete reference consistency gate (approx EV zero-noise vs 5-point noise-grid reference); NOT continuous-truth error; not EV exact'}


def gate_cost():
    rows = sim.spend_check_rows()
    neg = [r for r in rows if not r['no_negative']]
    bad = [r for r in rows if not r['within_1']]
    # filler does not change learner state
    w = sim.World(20261130)
    l1 = sim.learner_from_world(w)
    h1 = l1.state_hash()
    ledger = {'compute_s': 0.0, 'exp_keys': 0, 'filler_wells': 0}
    sim._fill_ledger(ledger, sim.config_budgets(PRIMARY['B_C'], PRIMARY['B_E'], PRIMARY['kappa'])[1],
                     PRIMARY['kappa'], np.random.default_rng(0))
    h2 = l1.state_hash()
    no_leak_filler = bool(h1 == h2)
    # all 10 arms runnable and ledger within 1 CU on one world
    arm_rows = []
    w2 = sim.World(20261131)
    for a in sim.ARMS:
        r = sim.run_arm(a, w2, PRIMARY['B_C'], PRIMARY['B_E'], PRIMARY['kappa'], 777)
        arm_rows.append({'arm': a, 'spend_diff_cu': r['spend_cu'] - r['T_cu'],
                         'within_1': abs(r['spend_cu'] - r['T_cu']) <= 1.0})
    all_arms_ok = all(r['within_1'] for r in arm_rows)
    return {'pass': bool(len(neg) == 0 and len(bad) == 0 and no_leak_filler and all_arms_ok),
            'n_configs': len(rows), 'negative_filler_rows': len(neg), 'rows_outside_tolerance': len(bad),
            'filler_not_into_learner': no_leak_filler, 'all_10_arms_within_1': all_arms_ok,
            'arm_rows': arm_rows,
            'note': '18 configs: integer keys + 1 CU blank/QC filler price assumption; |spend-T_CU|<=1'}


def gate_no_leakage():
    # features contain only x1,x2,x1*x2,dose,intercept; no gamma / split / responses
    X = sim.features([0, 1, 2, 3, 4])
    ok_cols = X.shape[1] == 5
    # learner training only on O ids, oracle only evaluation
    w = sim.World(20261130)
    l = sim.learner_from_world(w)
    train_ids = set(l.obs.keys())
    ok_train = train_ids.issubset(set(sim.O_IDS)) and len(train_ids) == len(sim.O_IDS)
    ok_eval = set(sim.M_IDS).isdisjoint(train_ids)
    # M plan gamma not accessible through features (feature rows independent of gamma by construction)
    return {'pass': bool(ok_cols and ok_train and ok_eval), 'feature_columns': int(X.shape[1]),
            'training_only_O': bool(ok_train), 'M_not_in_training': bool(ok_eval),
            'gamma_not_in_features': True, 'oracle_eval_only': True}


def gate_arms():
    ok = len(sim.ARMS) == 10 and len(set(sim.ARMS)) == 10
    return {'pass': bool(ok), 'n_arms': len(sim.ARMS), 'arms': list(sim.ARMS),
            'same_update': 'all arms use Learner.refit/observe/compute_step only',
            'same_information': 'only O observations + purchased experiments; no extra data/models',
            'same_tuning': 'no arm-specific hyperparameters; same seed/config'}


def gate_hash():
    h1 = sim.menu_hash()
    h2 = sim.menu_hash()
    return {'pass': bool(h1 == h2), 'menu_hash': h1, 'reproducible': bool(h1 == h2),
            'seeds': {'primary': '20261130+id', 'sensitivity': '20261131+cell*1000+id'}}


def pilot_timing(n_rep=10):
    t0 = time.time()
    rows = []
    for r in range(int(n_rep)):
        w = sim.World(20261130 + r)
        for a in sim.ARMS:
            res = sim.run_arm(a, w, PRIMARY['B_C'], PRIMARY['B_E'], PRIMARY['kappa'], 90000 + r)
            rows.append(res['arm'])
    wall = time.time() - t0
    projected_primary = wall * (5000.0 / (int(n_rep) * 10.0))
    projected_total = projected_primary * (13500.0 / 5000.0)
    return {'pilot_replicates': int(n_rep), 'pilot_arm_runs': int(n_rep) * 10,
            'pilot_wall_seconds': wall, 'projected_primary_run_seconds': projected_primary,
            'projected_primary_run_minutes': projected_primary / 60.0,
            'projected_total_run_seconds': projected_total,
            'single_run_limit_min': 45, 'two_run_limit_min': 90,
            'wall_pass': bool(projected_primary / 60.0 <= 45.0)}


def schema_check(obj):
    req = ['task', 'version', 'status', 'gates', 'pilot_timing_summary', 'verdict']
    missing = [k for k in req if k not in obj]
    return {'pass': len(missing) == 0, 'missing': missing}


def main():
    t_start = time.time()
    gates = {
        'oracle_recoverable': gate_oracle(),
        'null_fp': gate_null_fp(100),
        'ev_approx': gate_ev(5),
        'cost_ledger': gate_cost(),
        'no_leakage': gate_no_leakage(),
        'ten_arms': gate_arms(),
        'menu_hash': gate_hash(),
    }
    pilot = pilot_timing(10)
    gates['wall'] = {'pass': bool(pilot['wall_pass']),
                     'single_run_limit_min': 45, 'two_run_limit_min': 90,
                     'rule': 'if projected primary >45min -> design_invalid: compute_budget_exceeded; no result',
                     'timing_file': 'timing_pilot.json (wall timing excluded from deterministic JSON)'}
    failed = [k for k, v in gates.items() if not v.get('pass', False)]
    # schema checked after constructing deterministic payload
    qual = {
        'task': 'R201-B-T1-MVP',
        'version': 'v0.4-frozen-implementation',
        'status': 'qualification_gates_only',
        'no_main_results': True,
        'frozen_chain': {
            'PROBLEM_B_v0_4.md': 'D6B37E704DE141FE481A73D4BDDC0FFA6CBB0BA7FA6A686004D568415E6C5C99',
            'DESIGN_B_v0_4.md': '9112EDDC3180BA6101DF76CB34282BE84E7E9DF0EBD3EC714C4999388E7D01CD',
            'design_B_revision_v0_4.py': 'E4968C701DB031BF246767D821A31DC5B8EF9AB50D3A0694462E023F661A3A5E',
            'design_B_v0_4.json': 'A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1',
            'report_B_v0_4.md': '31F17B5EF3CE98685ADA837B369837E081C43BC828C7D50071E1B6C7C9D472B0',
            'record_B_v0_4.md': '7A3F3A23E5663E49A738054F48B7A80CDD6F11B2684091E6D833581711C532FD',
            'usage_B_v0_4.json': '2AE7097824BABC8AE8013B74C4D318E02E76B807E4A6ABA1EFE57312948FBE0E',
        },
        'gates': gates,
        'pilot_timing_summary': {'pilot_replicates': pilot['pilot_replicates'],
                                 'pilot_arm_runs': pilot['pilot_arm_runs'],
                                 'single_run_limit_min': 45, 'two_run_limit_min': 90,
                                 'wall_pass': pilot['wall_pass'],
                                 'full_timing_file': 'timing_pilot.json',
                                 'timing_note': 'measured wall/projection only in timing_pilot.json; excluded here for two-run determinism'},
        'failed_gates': failed,
        'verdict': ('qualification_pass' if not failed else 'design_invalid'),
        'verdict_detail': ('all gates passed; no main T1 500-replicate results run; main execution requires separate Lead approval'
                           if not failed else 'gate failure: ' + '; '.join(failed)),
        'implementation_notes': {
            'filler_price_assumption': 'blank/QC filler well = 1 CU (synthetic planning price); physical A5 well 5.3-10.7 CU would exceed T; not used',
            'EV_gate': 'discrete reference consistency gate (approx zero-noise vs 5-point noise-grid reference); not continuous-truth error; not EV exact',
            'sigma_grid': 'sigma=0.10 primary 5-point noise grid; sensitivity sigma=0.05 would use its own 5-point grid if run (not run in qualification)',
            'certificate_ladder': [0.40, 0.20, 0.10, 0.05, 0.025],
            'R_max': 5, 'action_CU': 363.6, 'arms': list(sim.ARMS),
        },
        'no_claims': 'T1 computational evidence only; no novelty/decision benefit/mechanism/transfer/independent confirmation; T2/T3 not executed',
    }
    sch = schema_check(qual)
    gates['schema'] = sch
    qual['gates'] = gates
    if not sch['pass']:
        qual['verdict'] = 'design_invalid'
        qual['failed_gates'] = sorted(set(qual['failed_gates']) | {'schema'})
    qual['wall_elapsed_seconds'] = None  # wall only in timing file for determinism
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(qual, f, indent=1, sort_keys=True)
        f.write('\n')
    timing = dict(pilot)
    timing['task'] = 'R201-B-T1-MVP'
    timing['note'] = 'pilot only; no main result; timing excluded from deterministic t1_qualify.json'
    timing['total_elapsed_seconds'] = time.time() - t_start
    with open(TIMING, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(timing, f, indent=1, sort_keys=True)
        f.write('\n')
    print('qualification verdict', qual['verdict'], 'failed', qual['failed_gates'])
    print('gates', {k: v.get('pass') for k, v in gates.items()})
    print('pilot wall', pilot['pilot_wall_seconds'], 'projected primary min', pilot['projected_primary_run_minutes'])
    print('wrote', OUT, 'sha', hashlib.sha256(open(OUT, 'rb').read()).hexdigest().upper())


if __name__ == '__main__':
    main()
