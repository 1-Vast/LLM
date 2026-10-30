#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-B design arithmetic only: dual compute/experiment budget decision design.

NO prediction fitting, NO response-value reading, NO effect experiment.
Reads no data file; all constants are design inputs from prior frozen/qualification
reports (cited in design_B.json inputs). Writes design_B.json (deterministic).
"""
from __future__ import annotations

import hashlib
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'D:\MAESTRO'

# ---- design constants (documented in DESIGN_B.md; no response values) ----
Z80 = 2.8015852181          # MDE80 coefficient (two-sided alpha=0.05, power=0.80)
DELTA_MIN = 0.10            # provisional minimal decision benefit on the declared scale
K_TOPK = 5                  # untested-decision menu: top-k
ALPHA = 0.05
POWER = 0.80

ON2EX = {'sigma_e': 0.1422665081, 'se_unit': 0.0251494031, 'mde80_mean_delta': 0.0287644381,
         'n_eff': 6, 'scope': 'full 4x4 grid, complete-case all batches/cells (qualification; mean-delta scale)'}
D3 = {'rank_mde_n6': 2.2875, 'rank_mde_n30': 0.7625, 'cells_needed_rank_010': 1573,
      'note': 'D3 single-anchor rank MDE; D3 stopped precision_insufficient'}
ON3 = {'wall_s_run1': 1272.0627641678, 'wall_s_run2': 1130.6128668785,
       'b6_perms_total': 5000, 'bootstrap_B': 5000, 'n_eff': 6,
       'note': 'ON3 v1.2 execution wall, development-only, non-blind/peeked'}
A5 = {'anchored_key_cu_central': 363.6, 'anchored_key_wells_low': 34, 'anchored_key_wells_high': 68,
      'cell_setup_wells': 2880, 'c136_keys_80pct': 1600, 'c136_power': 0.80,
      'example_budget_cu': 100000, 'unit': 'planning CU (not currency); wells physical',
      'note': 'A5 cost model is planning-only, coefficients uncalibrated to quotes/LOI'}
C187 = {'pair_level_al_delta': -0.0040, 'ci': [-0.0127, 0.0054], 'mde80': 0.0142,
        'verdict': 'no pair-level AL advantage; estimation saturated; not proof of absence'}
C190 = {'cellstate_line': 'unqualified', 'clustered_mde80': 0.240, 'delta_min': 0.05,
        'note': 'iid MDE 0.0295 rejected; clustered MDE used; line D stopped'}
D1 = {'status': 'stop', 'reason': 'precision_insufficient; MDE 0.0941>delta 0.05 (conservative); no optimistic planning'}
A1 = {'status': 'data_unavailable', 'reason': 'R199 A1 relations_check: R=2<20, coverage=1.17%<86'}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def mde_rank(n):
    """Conservative rank-difference MDE (Fisher-z; D3 formula), n independent units."""
    if n <= 3:
        return float('inf')
    return Z80 * math.sqrt(2.0 / (n - 3.0))


def mde_decision_accuracy(n):
    """Conservative paired-binary decision accuracy MDE: worst-case SE_diff=sqrt(2*0.25/n)."""
    if n <= 0:
        return float('inf')
    return Z80 * math.sqrt(0.5 / n)


def n_for_mde(metric, target):
    if target <= 0:
        raise ValueError
    if metric == 'rank':
        return int(math.ceil(2.0 * (Z80 / target) ** 2 + 3.0))
    if metric == 'decision_accuracy':
        return int(math.ceil(0.5 * (Z80 / target) ** 2))
    raise ValueError(metric)


def main():
    # ---- MDE table: local O'Neil vs synthetic vs required ----
    n_values = [6, 30, 100, 200, 393, 500, 1573]
    mde_table = []
    for n in n_values:
        mde_table.append({'n_independent_units': n,
                          'mde80_rank_delta_rho': round(mde_rank(n), 6) if n > 3 else None,
                          'mde80_decision_accuracy': round(mde_decision_accuracy(n), 6)})
    n_rank = n_for_mde('rank', DELTA_MIN)
    n_dec = n_for_mde('decision_accuracy', DELTA_MIN)

    # ---- experiment budget arithmetic (A5 planning CU; no currency) ----
    budget_levels = [0, 4, 16, 64, 256]
    experiment_budget = []
    for keys in budget_levels:
        cu = keys * A5['anchored_key_cu_central']
        wells_low = keys * A5['anchored_key_wells_low']
        wells_high = keys * A5['anchored_key_wells_high']
        experiment_budget.append({'anchored_keys': keys, 'central_CU': round(cu, 1),
                                  'wells_low': wells_low, 'wells_high': wells_high,
                                  'vs_A5_100k_example': round(cu / A5['example_budget_cu'], 4),
                                  'share_of_C136_1600key_gate': round(keys / A5['c136_keys_80pct'], 4)})
    need_393_keys = {'anchored_keys': n_dec, 'central_CU': round(n_dec * A5['anchored_key_cu_central'], 1),
                     'wells_low': n_dec * A5['anchored_key_wells_low'],
                     'wells_high': n_dec * A5['anchored_key_wells_high'],
                     'vs_A5_100k_example': round(n_dec * A5['anchored_key_cu_central'] / A5['example_budget_cu'], 4)}

    # ---- compute budget arithmetic (measured ON3 v1.2; seconds only) ----
    compute_levels = [300, 600, 1200, 2400, 3600]
    compute_budget = []
    for sec in compute_levels:
        compute_budget.append({'compute_budget_s': sec,
                               'runs_of_on3_v12_wall_run1': round(sec / ON3['wall_s_run1'], 3),
                               'runs_of_on3_v12_wall_run2': round(sec / ON3['wall_s_run2'], 3),
                               'share_of_15min_frozen_budget': round(sec / 900.0, 3),
                               'b6_perm_equiv_at_raw_306_722s_per_5000': round(sec / 306.722, 3)})

    # ---- decision-state / criterion arithmetic (definitions only) ----
    criteria = {
        'compute_insufficiency': {
            'definition': 'certified decision-set under declared approximation family changes, or certified gap > decision margin, when solver tolerance/iterations are tightened at fixed data',
            'operational_test': 'run two certified solves at increasing compute (same data, same seed family); if top-k set / best-plan choice changes OR h_out(d)-h_in(d) > delta_decision, classify compute-limited',
            'gap_formula': 'g_C = (h_out(d) - h_in(d)) / delta_decision',
            'compute_trigger': 'g_C > 1 and compute budget remains',
            'do_not_buy_experiment_when': 'g_C > 1 (compute ambiguity unresolved; buying data cannot certify decision)',
        },
        'evidence_insufficiency': {
            'definition': 'after compute convergence (g_C <= 1), different worlds within the declared compatible set still change decision, and the experiment can distinguish them at pre-registered power/MDE',
            'operational_test': 'MDE_decision(B_E) <= delta_min <= headroom; decision flip probability under compatible set > 0; experiment selector has positive expected decision value per CU',
            'evidence_trigger': 'g_C <= 1 AND ambiguity remains AND MDE_decision(B_E) <= delta_min AND power>=0.80',
            'stop_when': 'ambiguity cannot be reduced by any affordable experiment (MDE>delta_min or headroom<=0)',
        },
        'budget_rule': {
            'order': '1) certify-compute; 2) if compute-limited -> buy compute; 3) if evidence-limited and powered -> buy experiment; 4) else stop (compute_sufficient / evaluation_cannot_distinguish / blocked_by_precision)',
            'experiment_selection': 'select plan/stratum maximizing expected reduction of decision ambiguity per planning CU, subject to same information and same cost',
            'no_free_teacher': 'all solver time, certification, refit, experiment selection, controls/replicates/failed plates are charged',
            'compute_unit': 'measured CPU-second (no GPU); experiment unit: wells/plates/keys and planning CU from A5 (not currency)',
        },
    }

    # ---- gate arithmetic ----
    local_n = 30  # O'Neil target30 cells; per-fold n_eff=6
    gates = {
        'delta_min': DELTA_MIN,
        'local_oneil': {
            'n_independent_cells': local_n,
            'per_fold_n_eff': 6,
            'mde80_decision_accuracy_pooled30': round(mde_decision_accuracy(local_n), 6),
            'mde80_decision_accuracy_fold6': round(mde_decision_accuracy(6), 6),
            'mde80_rank_delta_rho_fold6': round(mde_rank(6), 6),
            'mde80_rank_delta_rho_pooled30': round(mde_rank(30), 6),
            'pass_delta_min': False,
            'verdict': 'evaluation_cannot_distinguish (precision_insufficient for decision benefit at delta_min=0.10)',
            'reason': 'decision/rank MDE >> delta_min on 30 cells (6/fold); adding technical wells/replicates does not increase independent-cell n',
        },
        'synthetic_simulator': {
            'proposed_replications': 500,
            'mde80_decision_accuracy': round(mde_decision_accuracy(500), 6),
            'pass_delta_min': mde_decision_accuracy(500) <= DELTA_MIN,
            'verdict': 'computational-evidence only; not biological decision benefit',
        },
        'prospective_wet': {
            'required_keys_for_decision_accuracy_mde_0_10': n_dec,
            'central_CU_required_at_A5_anchored_rate': round(n_dec * A5['anchored_key_cu_central'], 1),
            'A5_100k_CU_affordable_keys': int(A5['example_budget_cu'] // A5['anchored_key_cu_central']),
            'verdict': 'data_unavailable / cost_uncalibrated (no quotes/LOI, no wet budget, no independent culture)',
        },
        'required_n': {'rank_0_10': n_rank, 'decision_accuracy_0_10': n_dec},
    }

    out = {
        'task': 'R201-B',
        'status': 'design_only_not_run',
        'no_prediction_fitting': True,
        'no_response_value_read': True,
        'no_effect_experiment': True,
        'inputs_cited': {
            'BRIEF_R201': {'path': 'research/2026-10-27-innovation-round-r201/BRIEF.md',
                           'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-innovation-round-r201/BRIEF.md'))},
            'colearning_report': {'path': 'research/2026-10-27-agent-cell-colearning/report.md',
                                  'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-agent-cell-colearning/report.md'))},
            'ON2EX_report_calib': {'path': 'research/2026-10-27-core-module-design/oneil_dev/exec_calibration/report_calib.md',
                                   'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-core-module-design/oneil_dev/exec_calibration/report_calib.md'))},
            'ON3_v12_report': {'path': 'research/2026-10-27-core-module-design/oneil_dev/report_on3_exec.md',
                               'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-core-module-design/oneil_dev/report_on3_exec.md'))},
            'PEEK_DISCLOSURE_ON3': {'path': 'research/2026-10-27-core-module-design/oneil_dev/PEEK_DISCLOSURE_ON3.md',
                                    'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-core-module-design/oneil_dev/PEEK_DISCLOSURE_ON3.md'))},
            'A5_cost_model': {'path': 'research/2026-10-27-innovation-scouting/acquisition_stage3/cost_model.md',
                              'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-innovation-scouting/acquisition_stage3/cost_model.md'))},
            'D3_report': {'path': 'research/2026-10-27-direction-mechanism-expansion/d3_feedback/report_d3_v0_2.md',
                          'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-direction-mechanism-expansion/d3_feedback/report_d3_v0_2.md'))},
            'D1_decision': {'path': 'research/2026-10-27-direction-mechanism-expansion/d1_information/DECISION_D1_STOP.md',
                            'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-direction-mechanism-expansion/d1_information/DECISION_D1_STOP.md'))},
            'C187_report': {'path': 'research/2026-10-27-agent-cell-identifiability-r187/report.md',
                            'sha256': sha(os.path.join(ROOT, 'research/2026-10-27-agent-cell-identifiability-r187/report.md'))},
        },
        'constants': {'Z80': Z80, 'DELTA_MIN': DELTA_MIN, 'K_TOPK': K_TOPK, 'ALPHA': ALPHA, 'POWER': POWER,
                      'ON2EX': ON2EX, 'D3': D3, 'ON3': ON3, 'A5': A5, 'C187': C187, 'C190': C190, 'D1': D1, 'A1': A1},
        'mde_table': mde_table,
        'required_n': {'rank_delta_rho_0_10': n_rank, 'decision_accuracy_0_10': n_dec},
        'experiment_budget_arithmetic': {'budget_levels': experiment_budget, 'required_for_decision_accuracy': need_393_keys,
                                         'unit': 'A5 planning CU; NOT currency; actual quotes/LOI required before freeze'},
        'compute_budget_arithmetic': compute_budget,
        'criteria': criteria,
        'gates': gates,
        'design_verdict': {
            'local_oneil_primary_decision_benefit': 'not_identifiable (evaluation_cannot_distinguish; MDE>delta_min)',
            'synthetic_simulator': 'feasible for algorithmic falsification only (computational evidence; not biological/decision benefit)',
            'prospective_wet': 'data_unavailable / cost_uncalibrated (no wet budget, quotes, independent culture)',
            'main_claim_allowed': 'none; only design and computable arithmetic',
        },
        'attestation': {
            'no_response_reads': True,
            'no_model_fitting': True,
            'no_effect_run': True,
            'no_wet_spend': True,
            'no_novelty_claim': True,
            'no_decision_benefit_claim': True,
            'no_blind_or_independent_confirmation_claim': True,
        },
    }
    p = os.path.join(BASE, 'design_B.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write('\n')
    print('wrote', p, 'sha', sha(p))
    print('local decision MDE pooled30', gates['local_oneil']['mde80_decision_accuracy_pooled30'],
          'fold6', gates['local_oneil']['mde80_decision_accuracy_fold6'])
    print('required n rank/decision', n_rank, n_dec)
    print('synthetic pass', gates['synthetic_simulator']['pass_delta_min'],
          'wet keys', n_dec, 'CU', gates['prospective_wet']['central_CU_required_at_A5_anchored_rate'])


if __name__ == '__main__':
    main()
