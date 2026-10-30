#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-S2-EXEC-PREREG planning: frozen-chain verification, independent execution seeds,
Stage2 one-step DR synthetic environment / six allocation arms / G1-G6 / failure / budget / schema.
PLANNING ONLY: no training, no effect comparison, no real data.
"""
import sys
import os
import json
import math
import hashlib
import time

sys.dont_write_bytecode = True
import numpy as np

ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m3-stage2-exec-prereg')
M3P = os.path.join(ROOT, 'research', '2026-10-28-m3-decision-credit-prereg')
M3S1 = os.path.join(ROOT, 'research', '2026-10-28-m3-stage1')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'exec_plan_m3_s2.json')
SCHEMA = os.path.join(OUTDIR, 'schema_m3_s2_exec.json')

CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}

EXPECTED_CHAIN = {
    'research/2026-10-28-m3-decision-credit-prereg/PROBLEM_M3_v0_2.md': '15DFE82CDECA4429B1A7153A142909B41A570842D2E2E8CBFBAB757BC756ABAE',
    'research/2026-10-28-m3-decision-credit-prereg/DESIGN_M3_v0_2.md': '033D67CB63158A323DE03AA0A42C5750E14358D417743FE35269256E897EA8A0',
    'research/2026-10-28-m3-decision-credit-prereg/formalism_M3_v0_2.py': '3E709B8193AFA3814D821B46E9D541957B1864308D9DF98E2A60F118A25997B3',
    'research/2026-10-28-m3-decision-credit-prereg/formalism_M3_v0_2.json': '299E5B03E916BFB0FA36C02FE8446EA6170FAD89E6DF4BC039A92B0E36DD7E39',
    'research/2026-10-28-m3-decision-credit-prereg/schema_M3_v0_2.json': 'E2E641BCC4A65666382CAFCBDB1D1A496566F312F6560F9F9781E2BB92925F7E',
    'research/2026-10-28-m3-decision-credit-prereg/timing_M3_pilot_v0_2.json': 'BA261FA71AE957D38CA76BB4EB6A43B1E1FC230F5290088469425A63A3963C36',
    'research/2026-10-28-m3-decision-credit-prereg/report_M3_v0_2.md': '039B1A9821A48298E9F3E4F735E34837645400EBD3B2C2590CD6F3929571E4CF',
    'research/2026-10-28-m3-decision-credit-prereg/record_M3_v0_2.md': '47042AD6678912C7B8CBC2909A45D90546A411849330DE0AFE84345E3D1A47EE',
    'research/2026-10-28-m3-decision-credit-prereg/DECISION_R204_M3_STAGE1.md': '9743CF2ECD2F37FF4A2885DCE4BE468F9E895C357204ACC89BF9DD8A61FFC856',
    'research/2026-10-28-m3-stage1/m3_stage1.json': '60845EFA66215F31FE18A8159943DC1F90EA38B86FB9C19203F3AF98D84F052D',
    'research/2026-10-28-m3-stage1/m3_stage1_diagnostics.json': 'D0816802A6A9E9F95A51E14A41A4F1811BDE650D07E27891B40E9276A4C4DFD8',
    'research/2026-10-28-m3-stage1/m3_stage1_checks.csv': '2E6E3C8FFA91083386B14A96BC5B8415D95D58F43F327F01E5501F8433FFDFBE',
    'research/2026-10-28-m3-stage1/schema_m3_stage1.json': 'B0DC56A84797CF5E08B6139A2164F3264B9A8FCAFA793BCED206D620A489D1BC',
    'research/2026-10-28-m3-stage1/timing_m3_stage1.json': '7432135D6968B02ACBCBED371B90AF2D0B1F33CA622E041592BDEAE0ECEF0F87',
    'research/2026-10-28-m3-stage1/report_m3_stage1.md': '3FCAC8275D9BE6E25407D3B34484F5530F56289AEBEA784E5B21FC6A88996A68',
    'research/2026-10-28-m3-stage1/record_m3_stage1.md': 'EDB0AC3841A8DD65476B655185236B38DB40E2AFAB154C1EC7A4BA529BF6A6A6',
    'research/2026-10-28-m3-stage1/usage_m3_stage1.json': '7F8E2E6AEFA1A36382DB1A7783D700EFFFDE6B5C84705C9A56C9F7A18CED248D',
}

EXEC_DATA_SEED = 20261401
ARM_SEED_BASE = 20261410
REP_SEED_BASE = 20261420
N_REPS = 10
FORBIDDEN_SEEDS = {
    'M3_stage1_arithmetic_seed': [20261200],
    'M1_stage1_gen_eval': [20261112, 20261113],
    'M1_v0_2_param_train_eval': [20261201, 20261202, 20261203],
    'M1_stage2_exec_range': list(range(20261301, 20261350)),
    'M2_stage2_prep_range': list(range(20261200, 20261240)),
    'M2_stage3_range': list(range(20262100, 20262140)),
    'N1_gate_dev_seeds': [20261030, 20261061, 20261062, 20261063],
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest().upper()


def rq(x, nd=8):
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        if not math.isfinite(v):
            return None
        return float(round(v, nd))
    return x


def sanitize(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return rq(float(obj))
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float):
        return rq(obj)
    return obj


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sanitize(obj), fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)

    say('[1/7] verify M3 v0.2 + Stage1 + Lead decision chain ...')
    chain, mismatches = {}, {}
    for rel, expected in EXPECTED_CHAIN.items():
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            mismatches[rel] = 'missing'
            continue
        actual = sha256_file(path)
        chain[rel] = actual
        if actual != expected.upper():
            mismatches[rel] = {'expected': expected.upper(), 'actual': actual}
    chain_pass = len(mismatches) == 0
    s1 = json.load(open(os.path.join(M3S1, 'm3_stage1.json'), encoding='utf-8'))
    stage1_pass = bool(s1.get('failed_checks') == [] and s1.get('all_checks_pass') is True and
                       s1.get('check19_pass') is True and s1.get('no_effect_results') is True)
    say('    chain files=%d mismatches=%d pass=%s; Stage1 PASS=%s; check19=%s' % (
        len(chain), len(mismatches), chain_pass, stage1_pass, s1.get('check19_pass')))

    say('[2/7] independent execution seeds ...')
    arm_seeds = [ARM_SEED_BASE + i for i in range(6)]
    rep_seeds = [REP_SEED_BASE + i for i in range(N_REPS)]
    all_exec = [EXEC_DATA_SEED] + arm_seeds + rep_seeds
    forbidden_flat = []
    for v in FORBIDDEN_SEEDS.values():
        forbidden_flat.extend(v)
    overlap = sorted(set(all_exec) & set(forbidden_flat))
    seeds = {
        'data_seed': EXEC_DATA_SEED, 'arm_seeds': arm_seeds, 'replicate_seeds': rep_seeds,
        'two_runs': 'same seeds, separate processes; result JSON byte-identical; telemetry separate',
        'forbidden_seed_sets': FORBIDDEN_SEEDS, 'overlap_with_forbidden': overlap,
        'unique': len(set(all_exec)) == len(all_exec),
        'note': 'all execution seeds are 20261401+ and disjoint from M3 Stage1/M1 Stage2/M2/N1 seeds; no changes at execution',
    }
    say('    seeds=%d unique; overlap=%s' % (len(all_exec), overlap))

    say('[3/7] Stage2 synthetic DR environment / six allocation arms freeze ...')
    # frozen one-step DR environment (from M3 v0.2); arithmetic only
    p_h = np.array([0.3, 0.4, 0.3])
    mu = np.array([[0.20, 0.50, 0.80], [0.40, 0.60, 0.30], [0.10, 0.70, 0.50]])
    b = np.array([[0.20, 0.30, 0.50], [0.40, 0.40, 0.20], [0.25, 0.35, 0.40]])
    pi1 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    pi2 = np.array([[0.6, 0.4, 0.0], [0.3, 0.7, 0.0], [0.2, 0.2, 0.6]])
    m_true = mu.copy()
    m_wrong = np.full_like(mu, 0.5)
    H = {'pi1': pi1 / b, 'pi2': pi2 / b}
    env = {
        'H_contexts': 3, 'A_actions': 3, 'Y': 'binary in [0,1]', 'p_h': [rq(v) for v in p_h],
        'mu': [[rq(v) for v in row] for row in mu],
        'behavior_b': [[rq(v) for v in row] for row in b],
        'pi_1_deterministic_permutation': [[int(v) for v in row] for row in pi1],
        'pi_2_frozen_mixture': [[rq(v) for v in row] for row in pi2],
        'm_true': 'mu', 'm_wrong': 'all 0.5', 'C_H_truncation': 20.0,
        'known_truth_cases': ['m_true', 'm_wrong', 'positive support', 'zero support diagnostic',
                              'truncation C_H=20', 'collinearity diagnostic', 'separation diagnostic'],
        'formulas': {'H_k': 'pi_k(a|h)/b(a|h)', 'delta_k': 'E_{h,a~b}[H_k (Y-m_theta)]',
                     'V_k': 'E_h[sum_a pi_k m_theta] + delta_k',
                     'score_tilt': 'logit m_{theta,eps}=logit m_theta + sum_k eps_k H_k',
                     'allocation_Q': 'sum_h p(h) sum_a pi_k(a|h)^2 [Var(Y|h,a)+(E[Y|h,a]-m_theta(h,a))^2]/b(a|h)'},
        'zero_support_diagnostic': 'b=0 where pi mass=1 -> policy value not identified (support/positivity)',
        'collinearity_diagnostic': 'H columns rank<2 -> nonunique finite solution (nonidentifiable)',
        'separation_diagnostic': 'all Y=0 with positive H -> score root at -inf; nonidentifiable',
        'truncation_rule': 'weights clipped at predetermined C_H=20; clipped estimate is not exact policy value; report bias/bound',
        'pi_equals_b_degeneracy': 'H=1 -> one-step linear score-tilt degenerates to weighted residual; no novelty claim',
    }
    arms = [
        {'id': 'S_shared_score', 'role': 'candidate', 'allocation_rule': 'shared-score Q_k(b) allocation using H/delta/m_theta',
         'same': 'same updater/feedback/features/tuning<=20/caps/legal experiment package'},
        {'id': 'S_random', 'role': 'baseline', 'allocation_rule': 'random legal behavior allocation',
         'same': 'same budget/caps/legal package'},
        {'id': 'S_gp_uncertainty', 'role': 'baseline', 'allocation_rule': 'GP/uncertainty allocation',
         'same': 'same budget/caps/legal package'},
        {'id': 'S_decision_AL', 'role': 'explicit equal-budget strong baseline', 'allocation_rule': 'decision active learning',
         'same': 'same info/feedback/tuning<=20/caps/legal package'},
        {'id': 'S_optimal_experimental_design', 'role': 'explicit equal-budget strong baseline',
         'allocation_rule': 'optimal experimental design', 'same': 'same info/feedback/tuning<=20/caps/legal package'},
        {'id': 'S_DR_MLE_allocation', 'role': 'standard baseline', 'allocation_rule': 'DR+MLE optimal allocation',
         'same': 'same budget/caps/legal package'},
    ]
    stage2 = {
        'name': 'fixed-updater allocation comparison (synthetic one-step DR)', 'arms': arms,
        'same_learner_updater': True, 'only_allocation_changes': True,
        'common_budget': 'same data/information/physical feedback/tuning<=20 configs/caps 1800s/2h/8GB/0 wells/legal experiment package',
        'no_effect_outputs': ['no decision utility', 'no regret', 'no top-k', 'no learning-effect comparison'],
        'standard_equivalence': 'standard DR/TMLE + optimal allocation equal-budget replication/exceed -> no_increment/withdraw; '
                                'this judgment is left to later Stage3; current round registers spec/reproducibility only',
        'status': 'planned_not_run',
    }
    say('    six arms frozen: shared-score vs random/GP/decision_AL/optimal design/DR+MLE')

    say('[4/7] DR arithmetic/unit checks (no training) ...')
    # DR identity on frozen true/wrong m
    def policy_value(pi, m):
        V = []
        for h in range(3):
            base = float(np.sum(pi[h] * m[h]))
            delta = 0.0
            for a in range(3):
                Hk = pi[h, a] / b[h, a]
                delta += b[h, a] * Hk * (mu[h, a] - m[h, a])
            V.append(float(p_h[h] * (base + delta)))
        return float(np.sum(V))
    dr_gap = 0.0
    for pi in (pi1, pi2):
        for m in (m_true, m_wrong):
            direct = 0.0
            for h in range(3):
                for a in range(3):
                    Hk = pi[h, a] / b[h, a]
                    direct += p_h[h] * b[h, a] * Hk * mu[h, a]
            dr_gap = max(dr_gap, abs(policy_value(pi, m) - direct))
    # clipping bias from Stage1 JSON
    _diag = s1.get('S1_diagnostics', {})
    clip = _diag.get('S1_b_clipping') if isinstance(_diag, dict) else None
    # collinearity / pi=b / allocation ratios from loaded formalism
    fj = json.load(open(os.path.join(M3P, 'formalism_M3_v0_2.json'), encoding='utf-8'))
    collinear_rank = fj['score_tilt_update']['collinear_scores_rank']
    pi_b_H1 = fj['standard_baselines']['max_abs_H_minus_1']
    ratios = [fj['allocation_second_order']['rows_frozen_m'][k]['ratio_full_over_noise'] for k in ('pi_1', 'pi_2')]
    checks = {
        'dr_identity_gap_max': rq(float(dr_gap), 12), 'dr_identity_ok': bool(dr_gap <= 1e-12),
        'clipping_bias_value_loaded': (clip.get('bias') if isinstance(clip, dict) else None),
        'clipping_detected': bool(isinstance(clip, dict) and clip.get('n_weights_clipped', 0) >= 1 and clip.get('pass') is True),
        'collinear_rank': int(collinear_rank), 'collinear_rank_ok': bool(collinear_rank == 1),
        'pi_equals_b_H1_max_diff': pi_b_H1, 'pi_equals_b_ok': bool(abs(float(pi_b_H1)) < 1e-12),
        'allocation_ratios': [rq(float(v)) for v in ratios],
        'allocation_full_ge_noise': bool(all(float(v) >= 1.0 for v in ratios)),
        'score_root': fj['score_tilt_update']['epsilon_root'],
        'arms': [a['id'] for a in arms],
        'arms_include_decision_AL': any(a['id'] == 'S_decision_AL' for a in arms),
        'arms_include_optimal_design': any(a['id'] == 'S_optimal_experimental_design' for a in arms),
        'no_training_executed': True,
    }
    checks['all_pass'] = bool(checks['dr_identity_ok'] and checks['clipping_detected'] and
                              checks['collinear_rank_ok'] and checks['pi_equals_b_ok'] and
                              checks['allocation_full_ge_noise'] and checks['arms_include_decision_AL'] and
                              checks['arms_include_optimal_design'])
    say('    DR gap=%.2g; clip detected=%s; ratios=%s; all_pass=%s' % (
        dr_gap, checks['clipping_detected'], checks['allocation_ratios'], checks['all_pass']))

    say('[5/7] gates G1-G6 / failure / budget ...')
    gates = {
        'G1_support_program': 'b>0 on pi support, b>=b_min, action support, randomization recorded; failure support/positivity',
        'G2_truncation': 'predetermined C_H=20 clipping; clipped estimate != exact policy value; report bias/bound; failure calibration',
        'G3_allocation_second_order': 'Q full >= Q noise-only; misspecification bias-square nonzero/unknown; allocation not noise-only; failure calibration',
        'G4_no_leakage': 'evaluation sample independent of m_theta fit/policy selection; target samples not labels; allocation does not reuse evaluation; failure leakage',
        'G5_two_run': 'result JSON byte-identical; telemetry separate; failure two_run_mismatch',
        'G6_schema_budget': 'schema first-written; caps 1800s/2h/8GB/0 wells; failure compute_budget_exceeded',
        'failure_map': {'G1': ['support', 'positivity'], 'G2': ['calibration'], 'G3': ['calibration'],
                        'G4': ['leakage'], 'G5': ['two_run_mismatch'], 'G6': ['compute_budget_exceeded']},
    }
    failures = ['design_invalid: support', 'design_invalid: positivity', 'design_invalid: propensity',
                'design_invalid: leakage', 'design_invalid: calibration',
                'design_invalid: compute_budget_exceeded', 'design_invalid: nonidentifiable',
                'design_invalid: two_run_mismatch', 'unreachable_gate', 'precision_insufficient',
                'no_increment', 'inconclusive']
    timing_ref = json.load(open(os.path.join(M3S1, 'timing_m3_stage1.json'), encoding='utf-8'))
    budget = {
        'caps': CAPS, 'compute_only': True, 'new_wells': 0,
        'pilot_policy': 'execution must rerun final-implementation pilot and freeze canonical timing BEFORE main runs; '
                        'documented canonical timing and JSON use same snapshot; no telemetry in result JSON',
        'stage1_pilot_reference': {'file': 'timing_m3_stage1.json',
                                   'per_rep_seconds': timing_ref['mean_per_rep_seconds'],
                                   'projected_seconds': timing_ref['projected_seconds'],
                                   'full_stage1_wall_seconds': timing_ref['full_stage1_wall_seconds'],
                                   'sha': EXPECTED_CHAIN['research/2026-10-28-m3-stage1/timing_m3_stage1.json'],
                                   'note': 'Stage1 pilot only; execution pilot must re-time final implementation'},
    }
    say('    gates/failure/budget frozen; pilot ref per-rep=%.8f' % timing_ref['mean_per_rep_seconds'])

    say('[6/7] schema/failure template first written ...')
    schema = {
        'schema': 'R204-M3-S2-EXEC',
        'version': 'v1',
        'top_keys': ['task', 'status', 'chain', 'seeds', 'environment', 'arms', 'G1_G6', 'budget',
                     'run_shas', 'failure_category', 'verdict'],
        'arm_fields': ['arm_id', 'role', 'allocation_rule', 'same_budget_audit'],
        'checks_fields': ['dr_identity_gap', 'clipping_detected', 'collinear_rank', 'pi_equals_b_H1',
                          'allocation_ratios', 'two_run', 'budget'],
        'forbidden_fields': ['decision_utility', 'regret', 'topk', 'method_comparison', 'learning_effect',
                             'gain_claim', 'pharmacology_claim', 'real_decision_claim', 'transfer_claim',
                             'mechanism_claim', 'novelty_claim', 'real_data_result', 'sequential_DR_claim'],
        'no_effect_results': True,
        'no_training_in_prereg': True,
        'two_run_rule': 'result JSON byte-identical; telemetry only separate file',
    }
    write_json(schema, SCHEMA)
    say('    schema written')

    say('[7/7] write exec_plan_m3_s2.json ...')
    out = {
        'task': 'R204-M3-S2-EXEC-PREREG',
        'status': 'preregistration_only_not_executed; no training/effect/real data',
        'chain': {'files': chain, 'mismatches': mismatches, 'pass': chain_pass, 'stage1_pass': stage1_pass},
        'seeds': seeds,
        'environment_stage2': env,
        'stage2': stage2,
        'G1_G6': gates,
        'unit_checks': checks,
        'failure_categories': failures,
        'budget': budget,
        'schema_file': 'schema_m3_s2_exec.json',
        'scope': {'stage2_allocation_diagnostics_only': True, 'no_effect': True, 'no_method_comparison': True,
                  'no_learning_effect': True, 'no_training_executed': True, 'no_real_data': True,
                  'stage3_not_executed': True, 'mechanism_account_only': True, 'new_wells': 0, 'compute_only': True},
        'stop_boundaries': [
            'pi=b -> H=1 degeneracy; preserve equivalence; no novelty claim',
            'collinearity/separation/no support -> design_invalid: nonidentifiable',
            'zero support/extreme weights -> design_invalid: support/positivity',
            'truncation bias -> design_invalid: calibration; clipped estimate is not exact policy value',
            'evaluation reused for policy selection -> design_invalid: leakage',
            'two-run mismatch -> design_invalid: two_run_mismatch; chain mismatch -> design_invalid: chain_mismatch',
            'budget exceed -> design_invalid: compute_budget_exceeded',
            'functional-mean-only update != compatible cell-dynamics update',
            'no complete sequential history/propensity/censoring -> do not claim sequential DR/TMLE',
            'no old judgment/threshold/endpoint changes; no result-driven relaxation',
        ],
        'boundaries': ['mechanism account only (supporting research); synthetic compute-only; 0 wells',
                       'no Stage2 training/effect execution; no Stage3/real data/wet lab',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'no modification of old gates/judgments; no revival of stopped experiments',
                       'M3 not mixed with M1/M2; N1 not used as M3 evidence; data readiness open (C203/C205/C210)',
                       'Stage2 execution requires separate pre-registration + independent challenge + Lead approval'],
        'frozen_inputs': EXPECTED_CHAIN,
        'no_effect_results': True,
        'no_training_or_comparison_executed': True,
        'log_milestones': ['chain + Lead decision verified', 'independent execution seeds allocated',
                           'Stage2 environment/six arms frozen', 'G1-G6/failure/budget frozen',
                           'schema first-written', 'DR arithmetic/unit checks only'],
    }
    write_json(out, OUTJSON)
    print('exec_plan_m3_s2.json sha256:', sha256_file(OUTJSON))
    print('schema_m3_s2_exec.json sha256:', sha256_file(SCHEMA))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
