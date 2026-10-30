#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-B.3 (v0.4) T1 pre-registration arithmetic only.

NO effect run, NO fitting, NO response-value reading. Writes design_B_v0_4.json.
All constants are design inputs cited from v0.3/challenge; no data file reads.
"""
from __future__ import annotations

import hashlib
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))

Z80 = 2.8015852181
DELTA_MIN = 0.10
DELTA_UTILITY = 0.10
K_TOPK = 5
ALPHA = 0.05
POWER = 0.80
A5_KEY_CU = 363.6
A5_WELLS_LOW = 34
A5_WELLS_HIGH = 68

BUDGET_PAIRS = [(300, 4), (1200, 16), (3600, 64)]
KAPPA_GRID = [0.1, 1.0, 10.0]
SIGMA_GRID = [0.05, 0.10]
PRIMARY_CONFIG = {'B_C_s': 1200, 'B_E_keys': 16, 'kappa_s_per_CU': 1.0, 'sigma': 0.10}
PRIMARY_REPLICATES = 500
SENS_REPLICATES = 50
R_PRIMARY = 5
R_SENS = [1, 10]
ON3 = {'wall_s_run1': 1272.0627641678, 'wall_s_run2': 1130.6128668785,
       'b6_perms_total': 5000, 'bootstrap_B': 5000, 'raw_b6_306_722_s': 306.722}

# 10 T1 arms: pi_dual + C0..C6 (7) + C7 compute-only + C7 experiment-only
T1_ARMS = ['pi_dual', 'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
           'C7_compute_only', 'C7_experiment_only']
N_ARMS = len(T1_ARMS)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def mde(n):
    return Z80 * math.sqrt(0.5 / n)


def normal5_weights():
    """5-point standard-normal grid weights, normalized (z=-2..2)."""
    z = [-2.0, -1.0, 0.0, 1.0, 2.0]
    w = [math.exp(-0.5 * zi * zi) for zi in z]
    tot = sum(w)
    return z, [x / tot for x in w]


def equal_cost_rows():
    rows = []
    for bc, be in BUDGET_PAIRS:
        cu_e = be * A5_KEY_CU
        for kappa in KAPPA_GRID:
            for sigma in SIGMA_GRID:
                # synthetic total in seconds and in experiment-side CU-equivalent
                T_seconds = bc + kappa * cu_e
                T_cu_equivalent = cu_e + bc / kappa
                n0 = be + int(math.floor((bc / kappa) / A5_KEY_CU))
                keys_cu = n0 * A5_KEY_CU
                residual_cu = T_cu_equivalent - keys_cu
                filler_wells = int(math.ceil(residual_cu))
                spend_cu = keys_cu + filler_wells
                diff_cu = spend_cu - T_cu_equivalent
                rows.append({
                    'config': {'B_C_s': bc, 'B_E_keys': be, 'kappa_s_per_CU': kappa, 'sigma': sigma},
                    'primary_config': (bc == PRIMARY_CONFIG['B_C_s'] and be == PRIMARY_CONFIG['B_E_keys']
                                       and kappa == PRIMARY_CONFIG['kappa_s_per_CU'] and sigma == PRIMARY_CONFIG['sigma']),
                    'T_seconds': round(T_seconds, 6),
                    'T_CU_equivalent': round(T_cu_equivalent, 6),
                    'compute_only': {'spend_seconds': round(T_seconds, 6), 'filler': 'none (continuous compute)'},
                    'experiment_only': {
                        'n0_integer_keys': n0,
                        'keys_CU': round(keys_cu, 3),
                        'residual_CU': round(residual_cu, 6),
                        'blank_QC_filler_wells': filler_wells,
                        'blank_QC_filler_CU': filler_wells,
                        'spend_CU': round(spend_cu, 3),
                        'spend_diff_CU': round(diff_cu, 6),
                        'within_1_well': bool(0 <= residual_cu < A5_KEY_CU and abs(diff_cu) <= 1.0),
                    },
                    'dual': {'nominal_compute_s': bc, 'nominal_experiment_CU': round(cu_e, 3),
                             'residual_filler_rule': 'blank/QC for experiments; no-info compute steps for compute; spend to T within <=1 well-equivalent'},
                })
    return rows


def config_table():
    cells = []
    idx = 0
    for bc, be in BUDGET_PAIRS:
        for kappa in KAPPA_GRID:
            for sigma in SIGMA_GRID:
                is_primary = (bc == PRIMARY_CONFIG['B_C_s'] and be == PRIMARY_CONFIG['B_E_keys']
                              and kappa == PRIMARY_CONFIG['kappa_s_per_CU'] and sigma == PRIMARY_CONFIG['sigma'])
                cells.append({'cell_index': idx, 'B_C_s': bc, 'B_E_keys': be, 'kappa_s_per_CU': kappa,
                              'sigma': sigma, 'role': 'primary' if is_primary else 'sensitivity',
                              'replicates': PRIMARY_REPLICATES if is_primary else SENS_REPLICATES,
                              'arm_runs_per_replicate': N_ARMS,
                              'seed_rule': ('20261130 + replicate_id (0..499)' if is_primary
                                            else '20261131 + cell_index*1000 + replicate_id (0..49)'),
                              'used_for_main_H_B': is_primary,
                              'used_for_sensitivity_only': not is_primary})
                idx += 1
    return cells


def plan_features():
    """40-plan universe: 4 cells x 10 contexts; x1/x2/dose frozen by formula."""
    rows = []
    for p in range(40):
        u = p // 10
        j = p % 10
        x1 = (j % 3) - 1
        x2 = ((j // 3) % 3) - 1
        dose = 0.5 if j < 5 else 1.0
        split = 'O' if p < 20 else ('M' if p < 30 else 'reserve')
        rows.append({'plan_id': p, 'cell_u': u, 'context_j': j, 'x1': x1, 'x2': x2,
                     'dose': dose, 'split': split})
    return rows


def main():
    z, w = normal5_weights()
    cells = config_table()
    primary = [c for c in cells if c['role'] == 'primary'][0]
    rows = equal_cost_rows()

    # validation: no negative filler; all 18 rows within 1 well
    neg = [r for r in rows if r['experiment_only']['residual_CU'] < 0]
    bad = [r for r in rows if not r['experiment_only']['within_1_well']]
    primary_row = [r for r in rows if r['primary_config']][0]

    # wall with 10 arms
    primary_arm_runs = PRIMARY_REPLICATES * N_ARMS
    sens_arm_runs = (len(cells) - 1) * SENS_REPLICATES * N_ARMS
    total_arm_runs = primary_arm_runs + sens_arm_runs

    out = {
        'task': 'R201-B.3',
        'version': 'v0.4',
        'status': 't1_prereg_freeze_candidate_not_run',
        'challenge_input': {'file': 'challenge_B_v0_3.md', 'sha256': sha(os.path.join(BASE, 'challenge_B_v0_3.md'))},
        'v0_3_inputs': {
            'PROBLEM_B_v0_3.md': sha(os.path.join(BASE, 'PROBLEM_B_v0_3.md')),
            'DESIGN_B_v0_3.md': sha(os.path.join(BASE, 'DESIGN_B_v0_3.md')),
            'design_B_v0_3.json': sha(os.path.join(BASE, 'design_B_v0_3.json')),
            'report_B_v0_3.md': sha(os.path.join(BASE, 'report_B_v0_3.md')),
            'record_B_v0_3.md': sha(os.path.join(BASE, 'record_B_v0_3.md')),
        },
        'changes_5_must_fix': {
            '1_filler_formula': 'blank_QC_filler_CU=(B_E_CU+B_C/kappa)-n0*363.6 (not T_seconds-keys_CU); all 18 rows recomputed; no negative filler; primary 109.2 maintained; integer filler wells=ceil(residual)',
            '2_arm_runs': 'T1 arms = pi_dual + C0..C6 (7) + C7_compute_only + C7_experiment_only = 10; primary 500x10=5,000; sensitivity 17x50x10=8,500; total 13,500; wall/pilot/fallback recomputed',
            '3_x_EV_grid': 'x1/x2/dose formula + explicit 40-plan table frozen; theta fixed; EV uses 125 gamma worlds (3 gamma groups x 5-point normal grid) x noise approximation with pre-registered error gate (max EV error <=0.02)',
            '4_spend_validation': 'all 18 configs: experiment-only integer keys + blank/QC filler; residual CU in [0,363.6); |spend-T_CU|<=1; compute-only exact; dual filler rule; table/assertions',
            '5_boundaries_sync': 'wall_budget reports 10-arm counts; report/JSON sync; T2 PEEK; T3 data_unavailable/cost_uncalibrated; r primary=5; T1 implementation+qualification only',
        },
        'primary_config': primary,
        'primary_replicates': PRIMARY_REPLICATES,
        'primary_mde80': round(mde(PRIMARY_REPLICATES), 6),
        'delta_min': DELTA_MIN,
        'mde_pass': bool(mde(PRIMARY_REPLICATES) <= DELTA_MIN),
        't1_arms': T1_ARMS,
        'n_arms_per_replicate': N_ARMS,
        'config_table': cells,
        'sensitivity': {'n_cells': len(cells) - 1, 'replicates_per_cell': SENS_REPLICATES,
                        'total_replicates': (len(cells) - 1) * SENS_REPLICATES,
                        'arm_runs': sens_arm_runs,
                        'rule': 'descriptive/cost_sensitive only; never used for main H_B; Holm only on primary'},
        'equal_cost': {
            'definition': 'T_seconds=B_C+kappa*B_E_CU; T_CU_equivalent=B_E_CU+B_C/kappa; experiment-only integer keys n0=B_E+floor((B_C/kappa)/363.6) + blank/QC filler; all arms spend to T within <=1 well-equivalent',
            'corrected_filler_formula': 'blank_QC_filler_CU = (B_E_CU + B_C/kappa) - n0*363.6',
            'rows': rows,
            'primary_example': primary_row,
            'no_negative_filler': len(neg) == 0,
            'all_18_within_1_well': len(bad) == 0,
        },
        'spend_validation': {
            'n_rows': len(rows),
            'negative_filler_rows': len(neg),
            'rows_outside_tolerance': len(bad),
            'all_pass': len(neg) == 0 and len(bad) == 0,
            'rule': '|spend_CU - T_CU_equivalent| <= 1 well-equivalent for all 18 configs and all arms; dual residual filler to T; compute-only exact in seconds',
        },
        'H_B_rule': {
            'main_test_only_in_primary_config': True,
            'primary_contrasts': ['dual vs C7_compute_only (+filler)', 'dual vs C7_experiment_only (+filler)'],
            'multiplicity': 'Holm alpha=0.05 (two contrasts)',
            'supported_condition': 'BOTH contrasts positive AND Holm-significant AND both point estimates >= delta_min=0.10',
            'if_one_only': 'partial_decision_benefit (not H_B)',
            'if_none': 'no_decision_benefit',
            'if_both_significant_but_below_delta': 'below_delta (not H_B)',
            'best_single': 'inner validation only; test-set max forbidden; max descriptive with simultaneous CI',
            'sensitivity_configs': 'descriptive/cost_sensitive only; cannot claim H_B',
        },
        'x_mapping': {
            'plan_universe': 40, 'observed_O': 20, 'heldout_menu_M': 10, 'reserve_unused': 10,
            'formula': 'for plan p: cell_u=p//10; context_j=p%10; x1=(j%3)-1; x2=((j//3)%3)-1; dose=0.5 if j<5 else 1.0; split: p<20 O, 20<=p<30 M, else reserve',
            'plan_table': plan_features(),
            'menu_hash': 'SHA256(canonical sorted JSON of plan_id,x1,x2,dose,split for M plans); frozen before run',
        },
        'theta_f': {
            'f': 'f=theta0+theta1*x1+theta2*x2+theta3*x1*x2+theta4*dose',
            'theta_fixed': [0.5, 0.3, 0.2, 0.1, -0.1],
            'gamma_distribution': 'gamma_g ~ Normal(0, tau^2), per x2 group g in {-1,0,1}; tau=0.20',
            'noise': 'epsilon ~ Normal(0, sigma^2) on observed plan utilities',
        },
        'EV_grid': {
            'method': 'finite-discrete-world approximation, not continuous exact enumeration',
            'gamma_grid': {'tau': 0.20, 'z_points': z, 'values': [round(0.20 * zi, 6) for zi in z],
                           'weights': [round(x, 9) for x in w], 'groups': 3, 'n_gamma_worlds': 125},
            'noise_grid_for_observation': {'sigma': 0.10, 'z_points': z,
                                           'values': [round(0.10 * zi, 6) for zi in z],
                                           'weights': [round(x, 9) for x in w]},
            'EV_definition': 'EV computed over 125 gamma worlds with discrete weights; noise integrated by zero-mean expected utility for action ranking; observed utilities add Gaussian noise',
            'approximation_error_gate': 'compare EV_approx against 5-point noise-grid EV on calibration replicates; max selection-accuracy difference <=0.02; else design_invalid: EV_approximation_error; no result reported',
            'no_exact_claim': True,
        },
        'frozen_t1_knobs': {
            'plan_universe': 40, 'observed_O': 20, 'heldout_menu_M': 10, 'reserve_unused': 10,
            'sigma_primary': 0.10, 'sigma_sensitivity': 0.05,
            'tau': 0.20, 'theta_fixed': [0.5, 0.3, 0.2, 0.1, -0.1],
            'certificate_ladder': {'initial_width': 0.40, 'widths': [0.40, 0.20, 0.10, 0.05, 0.025],
                                   'step_cost_s': 120, 'min_compute_unit_s': 120},
            'experiment_action_library': {'action': 'one anchored key per plan', 'CU': A5_KEY_CU,
                                          'wells_low': A5_WELLS_LOW, 'wells_high': A5_WELLS_HIGH},
            'EV_grid_ref': 'EV_grid above', 'R_max': 5,
            'seeds': {'primary': '20261130+replicate_id(0..499)',
                      'sensitivity': '20261131+cell_index*1000+replicate_id(0..49)'},
            'two_run': 'byte-identical JSON; sorted keys; no timestamps',
            'schema': ['replicate_id', 'cell_index', 'arm', 'selection_accuracy', 'topk_hit', 'normalized_regret',
                       'chosen_plan', 'oracle_plan', 'cost_ledger', 'compute_steps', 'experiments', 'filler',
                       'failure_class'],
        },
        'wall_budget': {
            'n_arms_per_replicate': N_ARMS,
            'primary_arm_runs': primary_arm_runs,
            'sensitivity_arm_runs': sens_arm_runs,
            'total_arm_runs': total_arm_runs,
            'pilot': '10 primary replicates x 10 arms = 100 arm-runs before full; only wall timing, no result read',
            'single_run_limit_min': 45,
            'two_run_limit_min': 90,
            'fallback_rule': 'if pilot projects primary >45min -> design_invalid: compute_budget_exceeded, no results; if total >45min but primary <=45min -> run primary only, skip sensitivity (no sensitivity claims); never reduce primary 500 or 10 arms',
            'compute_anchor': ON3,
        },
        'qualification_gates': ['oracle recoverable with infinite compute', 'null false-positive <= alpha',
                                 'EV approximation error <=0.02', 'cost ledger exact/equal (integer keys + filler)',
                                 'no leakage unit tests (filler not into learner)', 'all 10 arms implementable and share update',
                                 'two-run byte-identical', 'schema valid', 'wall within budget', 'menu hash/seed reproducible'],
        'qualification_rule': 'gates checked before ANY T1 result is read/reported; gate failure -> design_invalid only; no selection_accuracy/topk/regret reported; no algorithm valid/invalid claim',
        'r_mapping': {'primary_r_keys_per_decision_unit': R_PRIMARY, 'sensitivity_r': R_SENS,
                      'T3_decision_units': 393,
                      'T3_cost_CU': {str(r): round(393 * r * A5_KEY_CU, 1) for r in [R_PRIMARY] + R_SENS},
                      'note': 'T3 remains data_unavailable/cost_uncalibrated; r primary=5 pre-registered'},
        't2_t3_boundaries': {
            'T2': 'descriptive only; no main test; attach PEEK_DISCLOSURE_ON3.md B4CAD955...; n=6/30 not main',
            'T3': 'data_unavailable/cost_uncalibrated; no quotes/LOI/wet budget/independent culture; no execution',
            'approval_scope': 'T1 simulator implementation + qualification gates only; no results/T2/T3 execution',
            'claims': 'T1 computational evidence only; no decision benefit/transfer/mechanism/novelty/resource-sufficient/independent confirmation claims',
        },
        'attestation': {'no_effect_run': True, 'no_fitting': True, 'no_response_read': True, 'no_wet_experiment': True,
                        'no_novelty_claim': True, 'no_decision_benefit_claim': True, 'T1_computational_evidence_only': True,
                        'v0_1_v0_2_v0_3_unmodified': True},
    }
    p = os.path.join(BASE, 'design_B_v0_4.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write('\n')
    print('wrote', p, 'sha', sha(p))
    print('primary MDE', round(mde(PRIMARY_REPLICATES), 6))
    print('arms', N_ARMS, 'primary arm runs', primary_arm_runs, 'sens', sens_arm_runs, 'total', total_arm_runs)
    print('neg filler rows', len(neg), 'bad rows', len(bad))
    print('primary filler', primary_row['experiment_only'])


if __name__ == '__main__':
    main()
