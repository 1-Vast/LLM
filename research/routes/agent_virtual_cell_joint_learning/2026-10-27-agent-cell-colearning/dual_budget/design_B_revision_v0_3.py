#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-B.2 (v0.3) T1 pre-registration arithmetic only.

NO effect run, NO fitting, NO response-value reading. Writes design_B_v0_3.json.
All constants are design inputs cited from v0.2/challenge; no data file reads.
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

# Fixed design grids (v0.3: DESIGN/JSON consistency)
BUDGET_PAIRS = [(300, 4), (1200, 16), (3600, 64)]  # (compute seconds, integer keys)
KAPPA_GRID = [0.1, 1.0, 10.0]         # synthetic compute-seconds per CU
SIGMA_GRID = [0.05, 0.10]
PRIMARY_CONFIG = {'B_C_s': 1200, 'B_E_keys': 16, 'kappa_s_per_CU': 1.0, 'sigma': 0.10}
PRIMARY_REPLICATES = 500
SENS_REPLICATES = 50
R_PRIMARY = 5
R_SENS = [1, 10]
ON3 = {'wall_s_run1': 1272.0627641678, 'wall_s_run2': 1130.6128668785,
       'b6_perms_total': 5000, 'bootstrap_B': 5000, 'raw_b6_306_722_s': 306.722}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def mde(n):
    return Z80 * math.sqrt(0.5 / n)


def equal_cost_rows():
    rows = []
    for bc, be in BUDGET_PAIRS:
        cu_e = be * A5_KEY_CU
        for kappa in KAPPA_GRID:
                total = bc + kappa * cu_e
                # experiment-only: integer keys + blank/QC filler
                n_keys_eff = be + int(math.floor((bc / kappa) / A5_KEY_CU))
                cu_keys = n_keys_eff * A5_KEY_CU
                filler_cu = total - cu_keys
                rows.append({
                    'config': {'B_C_s': bc, 'B_E_keys': be, 'kappa_s_per_CU': kappa},
                    'total_cost_synthetic_s': round(total, 3),
                    'dual_nominal': {'compute_s': bc, 'experiment_keys': be, 'experiment_CU': round(cu_e, 1)},
                    'compute_only': {'B_C_eff_s': round(total, 3), 'experiment_keys': 0,
                                     'filler': 'none (compute continuous)'},
                    'experiment_only': {'integer_keys': n_keys_eff, 'keys_CU': round(cu_keys, 1),
                                        'blank_QC_filler_CU': round(filler_cu, 3),
                                        'compute_s': 0,
                                        'filler_rule': 'blank/QC/known-standard wells only; not into learner'},
                    'tolerance': 'blank/QC filler absorbs residual; |spend-T| <= 1 well-equivalent; keys are integers',
                    'primary_config': (bc == PRIMARY_CONFIG['B_C_s'] and be == PRIMARY_CONFIG['B_E_keys']
                                       and kappa == PRIMARY_CONFIG['kappa_s_per_CU']),
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
                                  'seed_rule': ('20261130 + replicate_id (0..499)' if is_primary
                                                else '20261131 + cell_index*1000 + replicate_id (0..49)'),
                                  'used_for_main_H_B': is_primary,
                                  'used_for_sensitivity_only': not is_primary})
                    idx += 1
    return cells


def main():
    cells = config_table()
    primary = [c for c in cells if c['role'] == 'primary'][0]
    n_primary = primary['replicates']
    out = {
        'task': 'R201-B.2',
        'version': 'v0.3',
        'status': 't1_prereg_freeze_candidate_not_run',
        'challenge_input': {'file': 'challenge_B_v0_2.md', 'sha256': sha(os.path.join(BASE, 'challenge_B_v0_2.md'))},
        'v0_2_inputs': {
            'PROBLEM_B_v0_2.md': sha(os.path.join(BASE, 'PROBLEM_B_v0_2.md')),
            'DESIGN_B_v0_2.md': sha(os.path.join(BASE, 'DESIGN_B_v0_2.md')),
            'design_B_v0_2.json': sha(os.path.join(BASE, 'design_B_v0_2.json')),
            'report_B_v0_2.md': sha(os.path.join(BASE, 'report_B_v0_2.md')),
            'record_B_v0_2.md': sha(os.path.join(BASE, 'record_B_v0_2.md')),
        },
        'changes_5_must_fix': {
            '1_primary_config_500': 'primary = (B_C=1200s, B_E=16 keys, kappa=1, sigma=0.10); 500 independent replicates = 500 decision units; other 17 configs sensitivity-only (50 replicates each); no main H_B from sensitivity',
            '2_integer_keys_filler': 'integer keys + blank/QC/known-standard filler (no information; not into learner) or compute filler no-info steps; |spend-T|<=1 well-equivalent; no fractional keys',
            '3_H_B_AND': 'H_B supported iff BOTH Holm-corrected primary contrasts positive & significant AND both point estimates >= delta_min=0.10; one only -> partial_decision_benefit; none -> no_decision_benefit; below delta -> below_delta',
            '4_frozen_knobs': 'O=20/M=10/universe=40/hash; sigma primary 0.10; gamma~N(0,tau^2) tau=0.20; f linear+dose interaction; theta fixed; certificate ladder; experiment action; EV enumeration; R_max=5; wall/pilot rules',
            '5_boundaries': 'T1 approval = simulator implementation+qualification gates only; no T2/T3 execution; T2 descriptive+PEEK; T3 data_unavailable/cost_uncalibrated; r primary=5; no novelty/decision claim',
        },
        'primary_config': primary,
        'primary_replicates': n_primary,
        'primary_mde80': round(mde(n_primary), 6),
        'delta_min': DELTA_MIN,
        'mde_pass': bool(mde(n_primary) <= DELTA_MIN),
        'config_table': cells,
        'sensitivity': {'n_cells': len(cells) - 1, 'replicates_per_cell': SENS_REPLICATES,
                        'total_replicates': (len(cells) - 1) * SENS_REPLICATES,
                        'rule': 'descriptive/cost_sensitive only; never used for main H_B; Holm only on primary',
                        'configs': '3 fixed budget pairs x 3 kappa x 2 sigma = 18 cells; primary one; other 17 sensitivity'},
        'fixed_grids': {'budget_pairs_(B_C_s,B_E_keys)': BUDGET_PAIRS, 'kappa_s_per_CU': KAPPA_GRID, 'sigma': SIGMA_GRID},
        'equal_cost': {
            'definition': 'T = B_C + kappa*B_E_CU; compute-only B_C_eff=T; experiment-only integer keys n0=B_E+floor((B_C/kappa)/363.6) + blank/QC filler to T; dual nominal within pair + filler to T',
            'integer_keys_rule': 'n_keys integer; residual CU absorbed by blank/QC/known-standard filler; filler no information and not into learner; |spend-T| <= 1 well-equivalent',
            'compute_filler_rule': 'no-information random compute steps; no certificate update/model change; counted',
            'rows': equal_cost_rows(),
            'no_fractional_keys': True,
            'primary_example': None,
        },
        'H_B_rule': {
            'main_test_only_in_primary_config': True,
            'primary_contrasts': ['dual vs compute-only-filler', 'dual vs experiment-only-filler'],
            'multiplicity': 'Holm alpha=0.05 (two contrasts)',
            'supported_condition': 'BOTH contrasts positive AND Holm-significant AND both point estimates >= delta_min=0.10',
            'if_one_only': 'partial_decision_benefit (not H_B)',
            'if_none': 'no_decision_benefit',
            'if_both_significant_but_below_delta': 'below_delta (not H_B; no decision-benefit claim)',
            'best_single': 'chosen on inner validation only; max descriptive with simultaneous CI; never test-set max',
            'sensitivity_configs': 'descriptive/cost_sensitive only; cannot claim H_B',
        },
        'frozen_t1_knobs': {
            'plan_universe': 40, 'observed_O': 20, 'heldout_menu_M': 10,
            'menu_hash': 'SHA256 of canonical JSON metadata (sorted plan ids/features); frozen before run',
            'sigma_primary': 0.10, 'sigma_sensitivity': 0.05,
            'gamma_distribution': 'Normal(0, tau^2)', 'tau': 0.20,
            'f': 'linear + dose interaction: f = theta0 + theta1*x1 + theta2*x2 + theta3*x1*x2 + theta4*dose',
            'theta_prior': 'fixed vector [0.5, 0.3, 0.2, 0.1, -0.1]; no random theta',
            'certificate_ladder': {'initial_width': 0.40, 'widths': [0.40, 0.20, 0.10, 0.05, 0.025],
                                   'step_cost_s': 120, 'min_compute_unit_s': 120,
                                   'rule': 'each compute step shrinks interval width to next ladder value; charged'},
            'experiment_action_library': {'action': 'one anchored key per plan', 'CU': A5_KEY_CU,
                                          'wells_low': A5_WELLS_LOW, 'wells_high': A5_WELLS_HIGH,
                                          'information': 'measure one plan response/utility; no extra plan labels'},
            'EV_enumeration': 'exact enumeration over fixed discrete world grid (theta/gamma/noise grid frozen); no sampling approximation',
            'R_max': 5,
            'rounds': 'per replicate at most R_max experiment rounds',
            'seeds': {'primary': '20261130 + replicate_id (0..499)',
                      'sensitivity': '20261131 + cell_index*1000 + replicate_id (0..49)'},
            'two_run': 'byte-identical JSON; sorted keys; no timestamps',
            'schema': ['replicate_id', 'cell_index', 'arm', 'selection_accuracy', 'topk_hit', 'normalized_regret',
                       'chosen_plan', 'oracle_plan', 'cost_ledger', 'compute_steps', 'experiments', 'filler',
                       'failure_class'],
        },
        'wall_budget': {
            'primary_arm_runs': n_primary * 8,
            'sensitivity_arm_runs': (len(cells) - 1) * SENS_REPLICATES * 8,
            'total_arm_runs': n_primary * 8 + (len(cells) - 1) * SENS_REPLICATES * 8,
            'pilot': '10 primary replicates before full; extrapolate wall; no result read',
            'single_run_limit_min': 45,
            'two_run_limit_min': 90,
            'fallback_rule': 'if pilot projects primary-only >45min -> design_invalid: compute_budget_exceeded, no results; if total >45min but primary <=45min -> run primary only, skip sensitivity (no sensitivity claims); never reduce primary 500 or change configs after seeing results',
            'compute_anchor': ON3,
        },
        'qualification_gates': ['oracle recoverable with infinite compute', 'null false-positive <= alpha',
                                 'cost ledger exact/equal (integer keys + filler)', 'no leakage unit tests (filler not into learner)',
                                 'all C0-C7 implementable and share update', 'two-run byte-identical', 'schema valid',
                                 'wall within budget', 'menu hash/seed reproducible'],
        'qualification_rule': 'gates are checked before ANY T1 result is read/reported; gate failure -> design_invalid only; no selection_accuracy/topk/regret reported; no algorithm valid/invalid claim',
        'r_mapping': {'primary_r_keys_per_decision_unit': R_PRIMARY, 'sensitivity_r': R_SENS,
                      'T3_decision_units': 393, 'T3_cost_CU': {str(r): round(393 * r * A5_KEY_CU, 1) for r in [R_PRIMARY] + R_SENS},
                      'note': 'T3 remains data_unavailable/cost_uncalibrated; r primary pre-registered = 5; no post-hoc selection'},
        't2_t3_boundaries': {
            'T2': 'descriptive only; no main test; must attach PEEK_DISCLOSURE_ON3.md B4CAD955...; n=6/30 decision units not main',
            'T3': 'data_unavailable/cost_uncalibrated; no wet budget/quotes/LOI/independent culture; no execution',
            'claims': 'T1 computational evidence only; no decision benefit/transfer/mechanism/novelty/resource-sufficient/independent confirmation claims',
        },
        'attestation': {'no_effect_run': True, 'no_fitting': True, 'no_response_read': True, 'no_wet_experiment': True,
                        'no_novelty_claim': True, 'no_decision_benefit_claim': True, 'T1_computational_evidence_only': True,
                        'v0_1_v0_2_unmodified': True},
    }
    # primary equal-cost example
    for row in out['equal_cost']['rows']:
        if row['primary_config']:
            out['equal_cost']['primary_example'] = row
            break
    p = os.path.join(BASE, 'design_B_v0_3.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write('\n')
    print('wrote', p, 'sha', sha(p))
    print('primary', primary)
    print('primary MDE', round(mde(n_primary), 6), 'pass', mde(n_primary) <= DELTA_MIN)
    print('sensitivity cells', len(cells) - 1, 'reps/cell', SENS_REPLICATES)
    print('primary equal-cost row', json.dumps(out['equal_cost']['primary_example'], sort_keys=True))
    print('T3 cost r5', out['r_mapping']['T3_cost_CU'])


if __name__ == '__main__':
    main()
