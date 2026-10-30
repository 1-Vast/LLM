#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-S2.1 (v0.2) planning: frozen-chain verification, independent seeds, frozen Stage2 replicate/sample
semantics, six-arm allocation diagnostics (per-arm fields/criteria), 13 failure categories, schema/budget.
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
OUTJSON = os.path.join(OUTDIR, 'exec_plan_m3_s2_v0_2.json')
SCHEMA = os.path.join(OUTDIR, 'schema_m3_s2_exec_v0_2.json')

CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}
ENV_SEED = 20261401
REP_SEED_BASE = 20261401
R_REPS = 10
N_INITIAL = 300
N_ALLOC = 300
ARM_SEED_BASE = 20261411
ARM_SEED_STRIDE = 10
N_ARMS = 6

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

    say('[1/8] verify M3 v0.2 + Stage1 + Lead decision chain ...')
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
    say('    chain=%d files mismatches=%d pass=%s; Stage1=%s' % (len(chain), len(mismatches), chain_pass, stage1_pass))

    say('[2/8] frozen Stage2 replicate/sample semantics + independent seeds ...')
    replicate_seeds = [REP_SEED_BASE + r for r in range(R_REPS)]
    arm_seeds = [[ARM_SEED_BASE + ARM_SEED_STRIDE * a + r for r in range(R_REPS)] for a in range(N_ARMS)]
    all_exec = replicate_seeds + [s for row in arm_seeds for s in row]
    forbidden_flat = [v for vals in FORBIDDEN_SEEDS.values() for v in vals]
    overlap = sorted(set(all_exec) & set(forbidden_flat))
    sample = {
        'R_replicates': R_REPS,
        'H_contexts': 3, 'A_actions': 3, 'Y': 'binary in [0,1]',
        'data_seed_base': ENV_SEED,
        'replicate_seed_rule': 'replicate r = data_seed_base + r (r=0..9) -> 20261401..20261410',
        'replicate_seeds': replicate_seeds,
        'n_initial_behavior_units_per_replicate': N_INITIAL,
        'n_alloc_units_per_arm_per_replicate': N_ALLOC,
        'n_arms': N_ARMS,
        'per_replicate_total_units': N_INITIAL + N_ARMS * N_ALLOC,
        'total_units_all_replicates': R_REPS * (N_INITIAL + N_ARMS * N_ALLOC),
        'total_allocation_feedback_units': R_REPS * N_ARMS * N_ALLOC,
        'arm_seed_rule': 'arm a, replicate r = 20261411 + 10*a + r (a=0..5, r=0..9)',
        'arm_seeds': arm_seeds,
        'equal_budget_ledger_per_arm': {'n_allocations': N_ALLOC, 'feedback': N_ALLOC,
                                        'tuning_configs_max': 20, 'caps': CAPS,
                                        'legal_experiment_package': 'H=3 contexts/A=3 actions/Y binary; same package for all arms'},
        'two_runs': 'same seeds, separate processes; result JSON byte-identical; telemetry separate',
        'note': 'data seed 20261401 defines the frozen environment; replicate/arm seeds are explicit; no seed changes at execution',
    }
    seeds = {'sample_semantics': sample, 'overlap_with_forbidden': overlap,
             'unique': len(set(all_exec)) == len(all_exec),
             'forbidden_seed_sets': FORBIDDEN_SEEDS}
    say('    R=%d; per-rep units=%d; total=%d; overlap=%s; unique=%s' % (
        R_REPS, sample['per_replicate_total_units'], sample['total_units_all_replicates'], overlap, seeds['unique']))

    say('[3/8] Stage2 environment + six allocation arms ...')
    p_h = np.array([0.3, 0.4, 0.3])
    mu = np.array([[0.20, 0.50, 0.80], [0.40, 0.60, 0.30], [0.10, 0.70, 0.50]])
    b = np.array([[0.20, 0.30, 0.50], [0.40, 0.40, 0.20], [0.25, 0.35, 0.40]])
    pi1 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    pi2 = np.array([[0.6, 0.4, 0.0], [0.3, 0.7, 0.0], [0.2, 0.2, 0.6]])
    env = {
        'H_contexts': 3, 'A_actions': 3, 'Y': 'binary in [0,1]', 'p_h': [rq(v) for v in p_h],
        'mu': [[rq(v) for v in row] for row in mu], 'behavior_b': [[rq(v) for v in row] for row in b],
        'pi_1': 'deterministic permutation', 'pi_2': 'frozen mixture', 'm_true': 'mu', 'm_wrong': 'all 0.5',
        'C_H_truncation': 20.0,
        'known_truth_cases': ['m_true', 'm_wrong', 'positive support', 'zero support diagnostic',
                              'truncation C_H=20', 'collinearity diagnostic', 'separation diagnostic'],
        'formulas': {'H': 'pi/b', 'delta': 'E_b[H(Y-m_theta)]', 'V': 'E_h[sum pi m_theta]+delta',
                     'score_tilt': 'logit m_eps=logit m_theta + sum eps_k H_k',
                     'allocation_Q': 'sum_h p(h) sum_a pi^2[Var+(E-m)^2]/b'},
        'zero_support': 'b=0 where pi mass=1 -> not identified',
        'collinearity': 'H rank<2 -> nonunique (nonidentifiable)',
        'separation': 'all Y=0 positive H -> root at -inf',
        'pi_equals_b': 'H=1 -> weighted residual; no novelty claim',
    }
    arms = [
        {'id': 'S_shared_score', 'role': 'candidate', 'rule': 'shared-score Q_k(b) allocation'},
        {'id': 'S_random', 'role': 'baseline', 'rule': 'random legal allocation'},
        {'id': 'S_gp_uncertainty', 'role': 'baseline', 'rule': 'GP/uncertainty allocation'},
        {'id': 'S_decision_AL', 'role': 'explicit equal-budget strong baseline', 'rule': 'decision active learning'},
        {'id': 'S_optimal_experimental_design', 'role': 'explicit equal-budget strong baseline',
         'rule': 'optimal experimental design'},
        {'id': 'S_DR_MLE_allocation', 'role': 'standard baseline', 'rule': 'DR+MLE optimal allocation'},
    ]
    arm_result_fields = ['arm_id', 'replicate_id', 'allocation_weights', 'realized_allocation_frequency',
                         'H_summary', 'delta_summary', 'allocation_Q', 'variance_term', 'clipping',
                         'equal_budget_audit', 'two_run_sha', 'pass', 'failure_category']
    arm_pass_criteria = {
        'allocation_valid_simplex_support': 'weights on probability simplex, b>=b_min, support on legal actions',
        'H_delta_finite': 'H/delta summaries finite (no NaN/inf); clipping count/bias bound reported',
        'allocation_Q_reported': 'full/noise/bias-square terms reported; no effect interpretation',
        'equal_budget_audit_pass': 'same n_alloc=300/feedback=300/tuning<=20/caps/legal package for every arm',
        'two_run_sha_match': 'per-arm two-run result SHA match',
        'no_forbidden_outputs': 'no decision utility/regret/top-k/learning-effect comparison',
    }
    arm_failure_map = {
        'allocation_valid_simplex_support': ['design_invalid: support', 'design_invalid: positivity'],
        'H_delta_finite': ['design_invalid: nonidentifiable'],
        'allocation_Q_reported': ['design_invalid: calibration'],
        'equal_budget_audit_pass': ['design_invalid: compute_budget_exceeded'],
        'two_run_sha_match': ['design_invalid: two_run_mismatch'],
        'no_forbidden_outputs': ['design_invalid: leakage'],
    }
    stage2 = {
        'name': 'fixed-updater allocation diagnostics (synthetic one-step DR)',
        'arms': arms, 'same_learner_updater': True, 'only_allocation_changes': True,
        'allocation_diagnostics_only': True,
        'no_effect_outputs': ['no decision utility', 'no regret', 'no top-k', 'no learning-effect comparison'],
        'per_arm_result_fields': arm_result_fields,
        'per_arm_pass_criteria': arm_pass_criteria,
        'per_arm_failure_map': arm_failure_map,
        'equal_budget_rule': 'every arm: n_alloc=300, feedback=300, tuning<=20 configs, caps 1800s/2h/8GB/0 wells, same legal package',
        'standard_equivalence_deferred': 'standard DR/TMLE + optimal allocation equal-budget copy/exceed -> no_increment/withdraw; deferred to Stage3',
        'status': 'planned_not_run',
    }
    say('    six arms + per-arm diagnostic fields/criteria frozen')

    say('[4/8] failure categories (13) / gates ...')
    failures = ['design_invalid: support', 'design_invalid: positivity', 'design_invalid: propensity',
                'design_invalid: leakage', 'design_invalid: calibration',
                'design_invalid: compute_budget_exceeded', 'design_invalid: nonidentifiable',
                'design_invalid: two_run_mismatch', 'design_invalid: chain_mismatch',
                'unreachable_gate', 'precision_insufficient', 'no_increment', 'inconclusive']
    gates = {
        'G1_support_program': 'b>0 on pi support, b>=b_min, action support, randomization recorded; failure support/positivity',
        'G2_truncation': 'C_H=20; clipped estimate != exact policy value; report bias/bound; failure calibration',
        'G3_allocation_second_order': 'Q full>=noise; misspecification bias-square nonzero/unknown; failure calibration',
        'G4_no_leakage': 'evaluation independent of fit/policy selection; target samples not labels; failure leakage',
        'G5_two_run': 'result JSON byte-identical; telemetry separate; failure two_run_mismatch',
        'G6_schema_budget': 'schema first-written; caps 1800s/2h/8GB/0 wells; failure compute_budget_exceeded',
        'failure_map': {'G1': ['support', 'positivity'], 'G2': ['calibration'], 'G3': ['calibration'],
                        'G4': ['leakage'], 'G5': ['two_run_mismatch'], 'G6': ['compute_budget_exceeded']},
    }
    say('    failure_categories=%d includes chain_mismatch=%s' % (
        len(failures), 'design_invalid: chain_mismatch' in failures))

    say('[5/8] DR arithmetic/unit checks + sample semantics checks ...')
    def policy_value(pi, m):
        V = 0.0
        for h in range(3):
            base = float(np.sum(pi[h] * m[h]))
            delta = 0.0
            for a in range(3):
                Hk = pi[h, a] / b[h, a]
                delta += b[h, a] * Hk * (mu[h, a] - m[h, a])
            V += float(p_h[h] * (base + delta))
        return float(V)
    dr_gap = 0.0
    for pi in (pi1, pi2):
        for m in (mu, np.full_like(mu, 0.5)):
            direct = 0.0
            for h in range(3):
                for a in range(3):
                    Hk = pi[h, a] / b[h, a]
                    direct += p_h[h] * b[h, a] * Hk * mu[h, a]
            dr_gap = max(dr_gap, abs(policy_value(pi, m) - direct))
    fj = json.load(open(os.path.join(M3P, 'formalism_M3_v0_2.json'), encoding='utf-8'))
    ratios = [fj['allocation_second_order']['rows_frozen_m'][k]['ratio_full_over_noise'] for k in ('pi_1', 'pi_2')]
    clip = s1['S1_diagnostics']['S1_b_clipping']
    checks = {
        'dr_identity_gap_max': rq(float(dr_gap), 12),
        'clipping_detected': bool(clip.get('n_weights_clipped', 0) >= 1 and clip.get('pass') is True),
        'clipping_bias': clip.get('bias'), 'collinear_rank': int(fj['score_tilt_update']['collinear_scores_rank']),
        'pi_equals_b_H1_max_diff': fj['standard_baselines']['max_abs_H_minus_1'],
        'allocation_ratios': [rq(float(v)) for v in ratios],
        'failure_categories_count': len(failures),
        'chain_mismatch_present': 'design_invalid: chain_mismatch' in failures,
        'per_arm_fields_count': len(arm_result_fields),
        'per_arm_fields': arm_result_fields,
        'sample_total_units': sample['total_units_all_replicates'],
        'sample_total_allocations': sample['total_allocation_feedback_units'],
        'sample_equal_budget_ok': bool(N_ALLOC == sample['equal_budget_ledger_per_arm']['n_allocations'] and
                                       N_ALLOC == sample['equal_budget_ledger_per_arm']['feedback']),
        'no_training_executed': True,
    }
    checks['all_pass'] = bool(checks['dr_identity_gap_max'] <= 1e-12 and checks['clipping_detected'] and
                              checks['collinear_rank'] == 1 and abs(float(checks['pi_equals_b_H1_max_diff'])) < 1e-12 and
                              all(float(v) >= 1.0 for v in checks['allocation_ratios']) and
                              checks['failure_categories_count'] == 13 and checks['chain_mismatch_present'] and
                              checks['per_arm_fields_count'] >= 10 and checks['sample_equal_budget_ok'])
    say('    DR gap=%.2g; failures=%d; per-arm fields=%d; all_pass=%s' % (
        dr_gap, len(failures), len(arm_result_fields), checks['all_pass']))

    say('[6/8] budget / pilot policy / schema ...')
    budget = {
        'caps': CAPS, 'compute_only': True, 'new_wells': 0,
        'pilot_policy': 'execution must run a FINAL-IMPLEMENTATION pilot (2 replicates x 6 arms x 300 alloc units) '
                        'and measure wall/CPU/memory; freeze canonical timing BEFORE main runs; Stage1 pilot numbers '
                        'are historical reference only and must not be cited as execution pilot',
        'stage1_pilot_reference_only': {'per_rep_seconds': 0.00016347, 'projected_seconds': 0.001635,
                                        'full_stage1_wall_seconds': 0.007137,
                                        'sha': EXPECTED_CHAIN['research/2026-10-28-m3-stage1/timing_m3_stage1.json']},
        'main_projection_rule': 'main = R=10 x (300 initial + 6*300 alloc) draws; projected wall must be measured '
                                'by pilot and verified <=1800 s; otherwise compute_budget_exceeded',
    }
    schema = {
        'schema': 'R204-M3-S2-EXEC-v0.2', 'version': 'v0.2',
        'top_keys': ['task', 'status', 'chain', 'seeds', 'sample_semantics', 'environment', 'arms', 'per_arm',
                     'G1_G6', 'failure_categories', 'budget', 'run_shas', 'failure_category', 'verdict'],
        'per_arm_fields': arm_result_fields,
        'arm_pass_criteria': arm_pass_criteria,
        'arm_failure_map': arm_failure_map,
        'failure_categories': failures,
        'forbidden_fields': ['decision_utility', 'regret', 'topk', 'method_comparison', 'learning_effect',
                             'gain_claim', 'pharmacology_claim', 'real_decision_claim', 'transfer_claim',
                             'mechanism_claim', 'novelty_claim', 'real_data_result', 'sequential_DR_claim'],
        'no_effect_results': True, 'no_training_in_prereg': True,
        'two_run_rule': 'result JSON byte-identical; telemetry only separate file',
    }
    write_json(schema, SCHEMA)
    say('    schema v0.2 written (per_arm + 13 failure categories)')

    say('[7/8] write exec_plan_m3_s2_v0_2.json ...')
    out = {
        'task': 'R204-M3-S2.1',
        'status': 'preregistration_only_not_executed; no training/effect/real data',
        'chain': {'files': chain, 'mismatches': mismatches, 'pass': chain_pass, 'stage1_pass': stage1_pass},
        'seeds': seeds,
        'sample_semantics': sample,
        'environment_stage2': env,
        'stage2': stage2,
        'G1_G6': gates,
        'failure_categories': failures,
        'budget': budget,
        'unit_checks': checks,
        'schema_file': 'schema_m3_s2_exec_v0_2.json',
        'scope': {'stage2_allocation_diagnostics_only': True, 'no_effect': True, 'no_method_comparison': True,
                  'no_learning_effect': True, 'no_training_executed': True, 'no_real_data': True,
                  'stage3_not_executed': True, 'mechanism_account_only': True, 'new_wells': 0, 'compute_only': True},
        'stop_boundaries': ['pi=b -> H=1 degeneracy', 'collinearity/separation/no support -> nonidentifiable',
                            'zero support/extreme weights -> support/positivity',
                            'truncation bias -> calibration', 'evaluation reuse -> leakage',
                            'two-run/chain/budget -> corresponding design_invalid',
                            'functional-mean-only update != cell dynamics',
                            'no sequential history/propensity/censoring -> no sequential DR/TMLE claim',
                            'no old judgment/threshold changes'],
        'boundaries': ['supporting mechanism account only; synthetic compute-only; 0 wells',
                       'no Stage2 training/effect execution; no Stage3/real data/wet lab',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'no modification of old gates/judgments; no revival of stopped experiments',
                       'M3 not mixed with M1/M2; N1 not used as M3 evidence; data readiness open (C203/C205/C210)',
                       'Stage2 execution requires separate pre-registration + independent challenge + Lead approval'],
        'frozen_inputs': EXPECTED_CHAIN,
        'no_effect_results': True,
        'no_training_or_comparison_executed': True,
        'log_milestones': ['chain verified', 'sample semantics frozen (R=10; 300 initial + 6x300 alloc)',
                           'per-arm fields/criteria frozen', '13 failure categories frozen',
                           'schema v0.2 first-written', 'arithmetic/unit checks only'],
    }
    write_json(out, OUTJSON)
    print('exec_plan_m3_s2_v0_2.json sha256:', sha256_file(OUTJSON))
    print('schema_m3_s2_exec_v0_2.json sha256:', sha256_file(SCHEMA))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
