#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-B.1 (v0.2) design arithmetic only: dual compute/experiment budget decision design.

NO effect run, NO model fitting, NO response-value reading. Writes design_B_v0_2.json.
All constants are design inputs cited from v0.1 reports/challenge; no data file reads.
"""
from __future__ import annotations

import hashlib
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'D:\MAESTRO'

Z80 = 2.8015852181
DELTA_MIN_ACCURACY = 0.10       # primary operational threshold on selection accuracy [0,1]
DELTA_UTILITY = 0.10            # T1 synthetic utility-scale decision margin (separate, defined in simulator)
K_TOPK = 5
ALPHA = 0.05
POWER = 0.80

A5 = {'anchored_key_cu_central': 363.6, 'anchored_key_wells_low': 34, 'anchored_key_wells_high': 68,
      'cell_setup_wells': 2880, 'c136_keys': 1600, 'c136_cu': 1600 * 363.6,
      'example_budget_cu': 100000, 'example_keys': int(100000 // 363.6),
      'unit': 'planning CU (not currency); quotes/LOI missing'}
ON3 = {'wall_s_run1': 1272.0627641678, 'wall_s_run2': 1130.6128668785,
       'b6_perms_total': 5000, 'bootstrap_B': 5000, 'raw_b6_306_722_s': 306.722}
D3 = {'rank_mde_n6': 2.2875, 'rank_mde_n30': 0.7625, 'required_cells_rank_010': 1573}
ON2EX = {'se_unit': 0.0251494031, 'mde80_mean_delta': 0.0287644381, 'n_eff': 6}
C187 = {'delta': -0.0040, 'ci': [-0.0127, 0.0054], 'mde': 0.0142}
C190 = {'clustered_mde80': 0.240, 'delta_min': 0.05}
CLOSED = {'D1': 'stop:precision_insufficient', 'D3': 'design_invalid:precision',
          'A1': 'data_unavailable:relations R=2<20 coverage=1.17%<86',
          'C187': 'pair-level AL saturated (delta -0.0040)'}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def mde_accuracy(n):
    if n <= 0:
        return float('inf')
    return Z80 * math.sqrt(0.5 / n)


def mde_rank(n):
    if n <= 3:
        return float('inf')
    return Z80 * math.sqrt(2.0 / (n - 3.0))


def n_for_accuracy(target):
    return int(math.ceil(0.5 * (Z80 / target) ** 2))


def equal_cost_table():
    """Auditable equal-total-cost conversion table (T1 synthetic conversion)."""
    kappas = [0.1, 1.0, 10.0]  # synthetic compute-seconds per CU (pre-registered scenarios)
    pairs = [{'C_s': 300, 'E_keys': 4}, {'C_s': 1200, 'E_keys': 16}, {'C_s': 3600, 'E_keys': 64}]
    rows = []
    for pair in pairs:
        cu_e = pair['E_keys'] * A5['anchored_key_cu_central']
        for kappa in kappas:
            total_s = pair['C_s'] + kappa * cu_e  # synthetic total cost in compute-second-equivalents
            rows.append({
                'pair': {'B_C_s': pair['C_s'], 'B_E_keys': pair['E_keys'], 'B_E_CU': round(cu_e, 1)},
                'kappa_s_per_CU': kappa,
                'total_cost_synthetic_s': round(total_s, 1),
                'dual_spend': {'compute_s': pair['C_s'], 'experiment_CU': round(cu_e, 1),
                               'total_synthetic_s': round(total_s, 1)},
                'compute_only_redistributed': {'B_C_eff_s': round(pair['C_s'] + kappa * cu_e, 1),
                                               'experiments': 0, 'filler': 'none needed (budget fully converted)'},
                'experiment_only_redistributed': {'B_E_eff_CU': round(cu_e + pair['C_s'] / kappa, 1),
                                                  'B_E_eff_keys': round((cu_e + pair['C_s'] / kappa) / A5['anchored_key_cu_central'], 3),
                                                  'compute_s': 0, 'filler': 'none needed (budget fully converted)'},
                'filler_rule': 'if discretization leaves residual, fill with random no-information actions of the same dimension, counted in cost/ledger',
            })
    return {'kappas_s_per_CU': kappas, 'budget_pairs': pairs, 'table': rows,
            'definition': 'T1 synthetic defines kappa explicitly; T2/T3 without quotes/LOI mark cost_uncalibrated and do not use this table for conclusions',
            'no_test_set_max': 'best single budget selected on validation only; two primary contrasts reported with Holm correction; max only descriptive with simultaneous CI'}


def t3_cost_table():
    units = n_for_accuracy(DELTA_MIN_ACCURACY)  # 393 decision units
    rows = []
    for r in [1, 5, 10]:
        keys = units * r
        cu = keys * A5['anchored_key_cu_central']
        rows.append({'keys_per_decision_unit': r, 'decision_units': units, 'purchased_keys': keys,
                     'central_CU': round(cu, 1), 'wells_low': keys * A5['anchored_key_wells_low'],
                     'wells_high': keys * A5['anchored_key_wells_high'],
                     'vs_A5_100k_example': round(cu / A5['example_budget_cu'], 3),
                     'note': 'r is a pre-registered design sensitivity; r=1 is optimistic (393 keys only if one key resolves a decision unit)'})
    return {'decision_unit_definition': 'one independent held-out cell/fold menu with one selection decision; technical wells/keys are not decision units',
            'primary_mde_target': DELTA_MIN_ACCURACY, 'decision_units_required': units,
            'key_to_CU_mapping': 'purchased keys per decision unit r in {1,5,10}; keys*363.6 CU; setup/replicates/failed plates extra',
            'cost_rows': rows,
            'verdict': 'data_unavailable/cost_uncalibrated (no quotes/LOI, no wet budget, no independent culture)'}


def main():
    n_values = [6, 30, 200, 393, 500, 1573]
    mde_table = [{'n_independent_decision_units': n,
                  'mde80_selection_accuracy': round(mde_accuracy(n), 6),
                  'mde80_rank_delta_rho': round(mde_rank(n), 6)} for n in n_values]
    units = n_for_accuracy(DELTA_MIN_ACCURACY)

    out = {
        'task': 'R201-B.1',
        'version': 'v0.2',
        'status': 'design_revision_only_not_run',
        'challenge_input': {'file': 'challenge_B.md', 'sha256': sha(os.path.join(BASE, 'challenge_B.md'))},
        'v0_1_inputs': {
            'PROBLEM_B.md': sha(os.path.join(BASE, 'PROBLEM_B.md')),
            'DESIGN_B.md': sha(os.path.join(BASE, 'DESIGN_B.md')),
            'design_B.json': sha(os.path.join(BASE, 'design_B.json')),
            'report_B.md': sha(os.path.join(BASE, 'report_B.md')),
        },
        'changes_5_must_fix': {
            '1_equal_total_cost': 'single-budget arms redistribute unused budget via pre-registered kappa (s/CU); filler for residual; no test-set max; nested validation selection + Holm two contrasts + descriptive max CI',
            '2_criteria_operational': 'T1 synthetic certificate h_in/h_out, delta_utility, headroom, EV; unique decision tree; B_C-exhausted=compute_budget_exceeded (no buy); no-certificate models=certificate_unavailable; T2/T3 blocked before utility/certificate freeze',
            '3_primary_unified': 'primary = top-1 selection accuracy [0,1]; MDE=paired-binary formula; delta_min=0.10 operational; top-k/regret secondary only; decision unit=independent held-out cell/menu/fold; key->CU r in {1,5,10}',
            '4_t1_prereg': 'world generation/shared operator/hidden plan differences/noise/cost; 500 independent replicates seeds; oracle/top-k; null calibration; no-leakage tests; C0-C7 equivalents; equal cost; two-run; schema; wall budget; qualification gates',
            '5_t2_t3_boundaries': 'T2 descriptive only + PEEK B4CAD955...; T3 data_unavailable/cost_uncalibrated; n=6/30 not main test; 393 keys != decision units; no novelty/decision claim',
        },
        'constants': {'Z80': Z80, 'DELTA_MIN_ACCURACY': DELTA_MIN_ACCURACY, 'DELTA_UTILITY_T1': DELTA_UTILITY,
                      'K_TOPK': K_TOPK, 'ALPHA': ALPHA, 'POWER': POWER, 'A5': A5, 'ON3': ON3, 'D3': D3,
                      'ON2EX': ON2EX, 'C187': C187, 'C190': C190, 'closed_routes': CLOSED},
        'primary': {
            'metric': 'top-1 selection accuracy on held-out unmeasured menu (single choice per independent decision unit)',
            'scale': '[0,1]; delta_min=0.10 operational (statistical threshold, not business utility)',
            'mde_formula': 'MDE80 = 2.8015852181 * sqrt(0.5/n_independent_decision_units) (paired-binary worst-case)',
            'decision_unit': 'one independent held-out cell/fold menu with one selection decision',
            'n_required_for_delta': units,
            'primary_contrasts': ['dual vs compute-only-filler (Holm)', 'dual vs experiment-only-filler (Holm)'],
            'best_single_rule': 'selected on inner validation only; test reports both arms separately; max only descriptive with simultaneous CI',
            'topk_secondary': 'top-k hit and normalized regret are secondary; T1 simulator-calibrated null/MDE; not primary',
            'blocked_utility_meaning': 'blocked_by_utility_definition applies ONLY to secondary regret/EV/headroom and real-world decision-value claims; primary selection accuracy is operational and not blocked',
        },
        'mde_table': mde_table,
        't3_cost': t3_cost_table(),
        'equal_cost': equal_cost_table(),
        'criteria_decision_tree': {
            'order': [
                '0. if utility/certificate not defined for an arm -> blocked_by_utility_definition / certificate_unavailable (no conclusion; T2/T3 default until frozen)',
                '1. compute stage: if g_C>1 and remaining B_C>=min_compute_unit -> spend one pre-registered compute step; repeat',
                '2. if g_C>1 and B_C<min_compute_unit -> compute_budget_exceeded (unresolved; do NOT buy experiment, do NOT silently stop)',
                '3. if g_C<=1 and all worlds in certified compatible set give same decision -> compute_sufficient -> stop',
                '4. if evidence-limited: if headroom unknown -> oracle_unknown -> stop (T3 fallback; no buy); if MDE_decision(B_E)>delta_min or power<0.80 or headroom<delta_utility -> evaluation_cannot_distinguish -> stop; else buy experiment maximizing expected decision value per CU',
                '5. after experiment: update model, re-certify, next round; rounds exhausted -> unresolved (record)',
            ],
            'fallbacks': {
                'B_C_exhausted_gC_gt_1': 'compute_budget_exceeded (unresolved; no automatic experiment purchase)',
                'headroom_unknown': 'oracle_unknown (no experiment purchase; record required prospective pilot/oracle estimate)',
                'no_certificate_models': 'certificate_unavailable; such arms are comparators only and cannot run the dual splitter; T1 dual uses the certified synthetic family',
                'T2_T3': 'no conclusions before utility/certificate freeze; T2 descriptive-only with PEEK; T3 data_unavailable/cost_uncalibrated',
            },
        },
        't1_preregistration': {
            'scope': 'T1 synthetic simulator only; computational evidence, not biological/decision benefit',
            'world_generation': 'per replicate: draw shared operator theta_shared (plan feature coefficients), hidden plan-difference effects gamma_plan, noise sigma, observed/held-out plan split; utilities normalized to [0,1]',
            'shared_operator': 'plan utility = f_shared(plan features; theta) + gamma_plan + noise; gamma is hidden from learner and never in features',
            'plans_menu': 'fixed pre-registered plan universe/menu sizes; menu construction metadata-only, hash frozen before run',
            'replicates': 500,
            'seeds': 'seed = 20261130 + replicate_id; independent worlds; no reuse of a world across arms',
            'oracle_topk': 'oracle top-1 and top-k computed from true utilities; evaluation-only, never available to policies',
            'null_calibration': 'null world gamma=0 and all utilities equal; random decision; label shuffle; solver-seed shuffle; calibrate selection accuracy/top-k null, false-positive <= alpha',
            'no_leakage_unit_tests': ['hidden gamma not in features', 'unmeasured plans not used in training', 'oracle only evaluation', 'cost ledger includes all compute/experiment/filler', 'no arm-specific extra data/update'],
            'arms_C0_C7': {'C0': 'fixed compute + random experiments', 'C1': 'fixed experiments + more compute', 'C2': 'full-history retrain',
                           'C3': 'ordinary decision AL', 'C4': 'GP/BOED', 'C5': 'generic solver', 'C6': 'random budget allocation',
                           'C7': 'compute-only/experiment-only with unused-budget conversion/filler'},
            'equal_cost': 'same total synthetic cost via kappa; C7 conversion/filler; all arms share unit ledger; filler no information',
            'two_run': 'two full T1 runs must be byte-identical; JSON sorted keys, no timestamps',
            'schema': 'per replicate/arm: selection_accuracy, topk_hit, regret, chosen_plan, budget ledger, compute_steps, experiments, filler, failure_class; summary by arm',
            'wall_budget': 'pilot budget test first; T1 single-run wall <=45 min, two-run <=90 min CPU-only; if exceeded -> design_invalid: compute_budget_exceeded, no result',
            'qualification_gates': ['oracle recoverable with infinite compute', 'null false-positive <= alpha', 'cost ledger exact/equal', 'no leakage unit tests pass',
                                     'all C0-C7 implementable and share update', 'two-run identical', 'schema valid', 'wall within budget'],
            'if_gate_fail': 'simulator qualification fails -> design_invalid; no T1 result; no effect/decision claim',
        },
        't2': {'status': 'descriptive-only', 'n_decision_units': [6, 30],
               'mde_selection_accuracy': {'n6': round(mde_accuracy(6), 6), 'n30': round(mde_accuracy(30), 6)},
               'reason': 'MDE>0.10 -> evaluation_cannot_distinguish; not a main test',
               'peek': 'must attach PEEK_DISCLOSURE_ON3.md B4CAD955...; ON3 non-blind/peeked; no blind/independent claim'},
        't3': {'status': 'data_unavailable/cost_uncalibrated', 'decision_units_required': units,
               'cost': t3_cost_table()['cost_rows'], 'reason': 'no quotes/LOI, no wet budget, no independent culture; 393 keys != 393 decision units'},
        'design_verdict': {'T0': 'completed', 'T1': 'pre-registration-ready after this revision; not run',
                           'T2': 'not a main test; descriptive only', 'T3': 'data_unavailable/cost_uncalibrated',
                           'claim_allowed': 'none; no novelty/decision benefit/mechanism/transfer'},
        'attestation': {'no_effect_run': True, 'no_prediction_fitting': True, 'no_response_read': True,
                        'no_wet_experiment': True, 'no_novelty_claim': True, 'no_decision_benefit_claim': True,
                        'no_blind_confirmation_claim': True, 'T1_computational_evidence_only': True},
    }
    p = os.path.join(BASE, 'design_B_v0_2.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write('\n')
    print('wrote', p, 'sha', sha(p))
    print('primary selection-accuracy MDE n=6/30/393/500:', [round(mde_accuracy(n), 6) for n in (6, 30, 393, 500)])
    print('decision units required', units)
    print('t3 cost r=1/5/10 CU:', [r['central_CU'] for r in out['t3_cost']['cost_rows']])
    print('T1 replicates', out['t1_preregistration']['replicates'])


if __name__ == '__main__':
    main()
