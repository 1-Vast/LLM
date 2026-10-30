#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-S3-EXEC-PREREG planning: frozen-chain verification, independent seeds, Stage3 fixed-feedback
learning-comparison protocol, primary/secondary endpoints + Holm, headroom/MDE, closed-loop cost,
G1-G6 / 13 failure categories, schema and budget.
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
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m3-stage3-exec-prereg')
M3P = os.path.join(ROOT, 'research', '2026-10-28-m3-decision-credit-prereg')
M3S1 = os.path.join(ROOT, 'research', '2026-10-28-m3-stage1')
M3S2 = os.path.join(ROOT, 'research', '2026-10-28-m3-stage2-exec-prereg')
M3R2 = os.path.join(ROOT, 'research', '2026-10-28-m3-stage2-run')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'exec_plan_m3_s3_v0_2.json')
SCHEMA = os.path.join(OUTDIR, 'schema_m3_s3_exec_v0_2.json')

CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}
DELTA = 0.05
ALPHA = 0.05
Z80 = 2.801585
ICC = 0.30
M_CLUSTER = 5
DEFF = 1.0 + (M_CLUSTER - 1) * ICC
N_UNITS = 300
N_REPS = 10
N_FEEDBACK = 300
N_EVAL = 300
N_ARMS = 7
ENV_SEED = 20261601
REP_SEED_BASE = 20261601
ARM_SEED_BASE = 20261611
ARM_SEED_STRIDE = 10
HEADROOM_SEED_BASE = 20261681
R_HEADROOM = 10

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
    'research/2026-10-28-m3-stage2-exec-prereg/PROBLEM_M3_S2_EXEC_v0_2.md': 'FE9180FA4A82A71ABA77F7080A848BEBD7C6CA24482DD3BE397F6B5138398F32',
    'research/2026-10-28-m3-stage2-exec-prereg/DESIGN_M3_S2_EXEC_v0_2.md': '2569079C63320EC0518D913B26A65A2CCA7E35D6DB47D178B48AE904AF7ED89F',
    'research/2026-10-28-m3-stage2-exec-prereg/exec_plan_m3_s2_v0_2.py': 'C85C1AEA651E844D4D9B26EC793D10037960B3B516BC97FA6F48C5942B1192C4',
    'research/2026-10-28-m3-stage2-exec-prereg/exec_plan_m3_s2_v0_2.json': 'F16D1C04F5E63ECDA082F10FD5EB4AEC486B902829DA1FCAD027CA92BF0184C8',
    'research/2026-10-28-m3-stage2-exec-prereg/schema_m3_s2_exec_v0_2.json': '987089F84330DF97338513163570DDA47E91ABA3B26E73981DF44E0FC188B3B1',
    'research/2026-10-28-m3-stage2-exec-prereg/report_m3_s2_exec_v0_2.md': '0B473A506D89ABCFEBAEC52A0E6E5D3039AF9C3FFA6A05729760BBFE3C98F782',
    'research/2026-10-28-m3-stage2-exec-prereg/record_m3_s2_exec_v0_2.md': '9E934D800EDDA9A4A8AC4E477E5F6F1FF1775B06EA21C492AC38D8E01323D301',
    'research/2026-10-28-m3-stage2-exec-prereg/usage_m3_s2_exec_v0_2.json': 'CA8F6C4A82CEED6786652394451B1DFABE7217E821159A53F4D37E48C22264F9',
    'research/2026-10-28-m3-stage2-exec-prereg/DECISION_R204_M3_S2_EXEC.md': 'A29CBF7B19F82EC649A0A7F746C2ECFDD16EC4A7372AC2D508E137E618B03A51',
    'research/2026-10-28-m3-stage2-run/run_m3_stage2.py': '1AFA5CBD1BD0D134F75755D5ADE1CEE592CD61F30817C6556757C88FA1EDEF6F',
    'research/2026-10-28-m3-stage2-run/m3_stage2.json': '36C4DF1291EEB17D5FE31D3E3DC32509A1A366254396EFE9F9F08A0C146CE7FE',
    'research/2026-10-28-m3-stage2-run/m3_stage2_per_arm.csv': 'ACAF46352CB4FB8AB86375EBA57B0D3CB51C5E06D125A30DB42C193EA228E5A1',
    'research/2026-10-28-m3-stage2-run/m3_stage2_diagnostics.json': '4A742BA087E1F3807C278B4EBFF762A7FE98657CC4C9C993A9370688D7BD8176',
    'research/2026-10-28-m3-stage2-run/schema_m3_stage2_run.json': '0E46DEC026DB42E8887296E7365C22466132ADC40DCF675C5FF543CDD4A2F499',
    'research/2026-10-28-m3-stage2-run/timing_m3_stage2_run.json': '6B02BCD44ECD76666126EFD5660DC651E2974792076C6E1B33B35E9F28BC8136',
    'research/2026-10-28-m3-stage2-run/report_m3_stage2_run.md': 'FFD24ED55D3B185F71466FC7580EB9B31376C4517B8F711D0E0E8B2A609057B7',
    'research/2026-10-28-m3-stage2-run/record_m3_stage2_run.md': '0C818AC971CB5839FB5EE39B804AEED97E0FC0EBF4275D5E6A15D40D1FB1D32F',
    'research/2026-10-28-m3-stage2-run/usage_m3_stage2_run.json': 'C0F9BD33B000C2A6A3B302759EB8FDC9466ADE9E55DB2FB175AEC3C2A57F321A',
}
FORBIDDEN_SEEDS = {
    'M3_stage1_arithmetic_seed': [20261200],
    'M3_stage1_gen_eval': [20261112, 20261113],
    'M1_stage1_gen_eval': [20261112, 20261113],
    'M1_v0_2_param_train_eval': [20261201, 20261202, 20261203],
    'M1_stage2_exec_range': list(range(20261301, 20261350)),
    'M3_stage2_seed_range': list(range(20261401, 20261471)),
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

    say('[1/8] verify M3 v0.2 + Stage1 + Stage2 exec/run + Lead decisions chain ...')
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
    s2 = json.load(open(os.path.join(M3R2, 'm3_stage2.json'), encoding='utf-8'))
    stage1_pass = bool(s1.get('failed_checks') == [] and s1.get('all_checks_pass') is True and
                       s1.get('check19_pass') is True and s1.get('no_effect_results') is True)
    stage2_pass = bool(s2.get('status') == 'completed_allocation_diagnostics' and
                       s2.get('failure_category') is None and
                       isinstance(s2.get('per_arm'), list) and len(s2.get('per_arm')) == 60 and
                       s2.get('no_effect_results') is True)
    say('    chain=%d files mismatches=%d pass=%s; Stage1=%s; Stage2 C213=%s' % (
        len(chain), len(mismatches), chain_pass, stage1_pass, stage2_pass))

    say('[2/8] independent Stage3 seeds ...')
    replicate_seeds = [REP_SEED_BASE + r for r in range(N_REPS)]
    arm_seeds = [[ARM_SEED_BASE + ARM_SEED_STRIDE * a + r for r in range(N_REPS)] for a in range(N_ARMS)]
    headroom_seeds = [HEADROOM_SEED_BASE + r for r in range(R_HEADROOM)]
    all_exec = replicate_seeds + [v for row in arm_seeds for v in row] + headroom_seeds
    forbidden_flat = [v for vals in FORBIDDEN_SEEDS.values() for v in vals]
    overlap = sorted(set(all_exec) & set(forbidden_flat))
    seeds = {
        'env_seed': ENV_SEED, 'replicate_seeds': replicate_seeds, 'replicate_seed_rule': '20261601..20261610',
        'arm_seeds': arm_seeds, 'arm_seed_rule': 'arm a,r = 20261611 + 10*a + r (a=0..6, r=0..9)',
        'headroom_seeds': headroom_seeds, 'headroom_rule': '20261681..20261690',
        'two_runs': 'same seeds, separate processes; result JSON byte-identical; telemetry separate',
        'forbidden_seed_sets': FORBIDDEN_SEEDS, 'overlap_with_forbidden': overlap,
        'unique': len(set(all_exec)) == len(all_exec),
        'note': 'Stage3 seeds 20261601+; disjoint from M3 Stage1/Stage2, M1 Stage2, M2, N1; no changes at execution',
    }
    say('    seeds=%d unique; overlap=%s' % (len(all_exec), overlap))

    say('[3/8] Stage3 fixed-feedback learning comparison + closed-loop cost ...')
    sample = {
        'R_replicates': N_REPS, 'n_units_per_replicate': N_UNITS,
        'n_feedback_shared_per_replicate': N_FEEDBACK, 'n_eval_shared_per_replicate': N_EVAL,
        'n_units_total': N_REPS * N_UNITS, 'n_feedback_total': N_REPS * N_FEEDBACK,
        'n_arms': N_ARMS,
        'fixed_feedback_rule': 'all arms see the SAME recorded (h,a,Y) feedback stream of 300 records/replicate; '
                               'same evaluation sample of 300 units/replicate; no arm chooses allocation',
        'evaluation_independence': 'evaluation sample independent of fitting/update/policy selection',
        'closed_loop_ledger': {'feedback_per_arm': N_FEEDBACK, 'evaluation_units': N_EVAL,
                               'tuning_configs_max': 20, 'caps': CAPS,
                               'cost_units': 'feedback records + evaluation units + compute; counted for every arm'},
    }
    arms = [
        {'id': 'A_candidate_score_tilt', 'role': 'candidate',
         'update_rule': 'one-step score-tilt update on shared score H/delta',
         'allocation_policy': 'shared_score_fixed_same_feedback_stream'},
        {'id': 'A_full_history_retrain', 'role': 'baseline', 'update_rule': 'refit from all history each round',
         'allocation_policy': 'shared_score_fixed_same_feedback_stream'},
        {'id': 'A_importance_weighting', 'role': 'baseline', 'update_rule': 'importance-weighted update',
         'allocation_policy': 'shared_score_fixed_same_feedback_stream'},
        {'id': 'A_DR_targeting', 'role': 'baseline', 'update_rule': 'DR targeting update',
         'allocation_policy': 'shared_score_fixed_same_feedback_stream'},
        {'id': 'A_TMLE_targeting', 'role': 'baseline', 'update_rule': 'TMLE targeting update',
         'allocation_policy': 'shared_score_fixed_same_feedback_stream'},
        {'id': 'A_value_aware', 'role': 'baseline', 'update_rule': 'value-aware model learning',
         'allocation_policy': 'shared_score_fixed_same_feedback_stream'},
        {'id': 'A_standard_DR_TMLE', 'role': 'standard equal-budget learner baseline (fixed allocation)',
         'update_rule': 'standard DR/TMLE learner (no optimal allocation; fixed shared-score allocation)',
         'allocation_policy': 'shared_score_fixed_same_feedback_stream',
         'equivalence_note': 'standard DR/TMLE learner (fixed allocation); equal-budget replication/exceed -> no_increment/withdraw'},

    ]
    stage3 = {
        'name': 'fixed-feedback learning comparison + closed-loop cost',
        'arms': arms,
        'same_feedback': True, 'same_evaluation_sample': True,
        'allocation_comparison': False,
        'allocation_fixed_shared_score': True,
        'all_arms_same_feedback_stream': True,
        'no_arm_changes_feedback': True,
        'feedback_stream_frozen': True,
        'no_optimal_allocation_arm': True,
        'same_information_budget_tuning_caps': True,
        'standard_equivalence_rule': 'standard DR/TMLE learner (fixed allocation) equal-budget replication/exceed -> no_increment/withdraw; no optimal-allocation arm or feedback advantage allowed',
        'no_learning_effect_claim_here': True,
        'status': 'planned_not_run',
    }
    say('    7 arms frozen (candidate + 5 learning baselines + standard DR/TMLE learner baseline; all fixed shared-score feedback)')

    say('[4/8] primary/secondary endpoints + Holm + precision/headroom ...')
    endpoints = {
        'primary_comparison': 'A_candidate_score_tilt vs A_standard_DR_TMLE',
        'primary_endpoint': 'independent functional decision utility/regret (normalized), delta=.05',
        'primary_success': 'mean DeltaR <= -delta AND 95% CI upper < 0 AND Holm-adjusted p < .05',
        'family': ['A_candidate_score_tilt vs A_standard_DR_TMLE (primary)',
                   'A_candidate_score_tilt vs A_full_history_retrain',
                   'A_candidate_score_tilt vs A_importance_weighting',
                   'A_candidate_score_tilt vs A_DR_targeting',
                   'A_candidate_score_tilt vs A_TMLE_targeting',
                   'A_candidate_score_tilt vs A_value_aware'],
        'multiplicity': 'Holm, alpha=.05, family size=6',
        'secondary_endpoints': ['prediction calibration', 'DR score error', 'RNA error (secondary only)'],
        'no_endpoint_switch': 'primary fixed; no post-hoc switching to prediction/top-k/budget endpoint',
        'delta': DELTA,
    }
    n_eff = N_UNITS / DEFF
    mde = Z80 * 0.20 / math.sqrt(n_eff)
    n_req = int(math.ceil((Z80 * 0.20 / DELTA) ** 2))
    n_req_cluster = int(math.ceil(n_req * DEFF))
    precision = {
        'delta': DELTA, 'n_units_per_replicate': N_UNITS, 'R_replicates': N_REPS,
        'cluster_m': M_CLUSTER, 'ICC': ICC, 'design_effect': DEFF, 'n_eff_conservative': rq(n_eff),
        'conservative_SD_D': 0.20, 'MDE80_conservative': rq(mde), 'MDE80_le_delta': bool(mde <= DELTA),
        'n_req_independent': n_req, 'n_req_cluster': n_req_cluster, 'n_req_le_n_units': bool(n_req_cluster <= N_UNITS),
        'analysis': 'paired unit-level DeltaR with cluster-robust SE by replicate; conservative precision from '
                    'n_units=300/deff=2.2; actual R=10 replicates reported',
        'headroom': {'U_max': 1.0, 'U0_standard': 'estimated in pre-effect headroom precheck',
                     'headroom_required_ge_delta': True,
                     'rule': 'headroom=U_max-U0; <delta -> unreachable_gate; near-ceiling -> separate budget-to-target; no endpoint switch'},
        'fisher_z_only': {'delta_0.05': 6282.10378742114, 'delta_0.10': 1572.775946855285,
                          'non_integer': True, 'not_a_gate': True, 'not_paired_DR_formula': True,
                          'decision_use': 'MDE80=.047982685 / n_req_cluster=278 / headroom / cluster'},
    }
    say('    primary vs standard DR/TMLE learner (fixed allocation); family=6 Holm; MDE=%.5f n_req=%d' % (mde, n_req_cluster))

    say('[5/8] G1-G6 / 13 failure categories ...')
    failures = ['design_invalid: support', 'design_invalid: positivity', 'design_invalid: propensity',
                'design_invalid: leakage', 'design_invalid: calibration',
                'design_invalid: compute_budget_exceeded', 'design_invalid: nonidentifiable',
                'design_invalid: two_run_mismatch', 'design_invalid: chain_mismatch',
                'unreachable_gate', 'precision_insufficient', 'no_increment', 'inconclusive']
    gates = {
        'G1_support_program': 'b>0 on pi support, b>=b_min, action support, randomization recorded; failure support/positivity',
        'G2_truncation': 'C_H=20; clipped estimate != exact policy value; report bias/bound; failure calibration',
        'G3_projection_approx': 'score-tilt/DR/TMLE fitting diagnostics; failure calibration/nonidentifiable',
        'G4_no_leakage': 'evaluation sample independent of fitting/update/selection; target samples not labels; failure leakage',
        'G5_two_run': 'result JSON byte-identical; telemetry separate; failure two_run_mismatch',
        'G6_schema_budget': 'schema first-written; caps 1800s/2h/8GB/0 wells; failure compute_budget_exceeded',
        'failure_map': {'G1': ['support', 'positivity'], 'G2': ['calibration'], 'G3': ['calibration', 'nonidentifiable'],
                        'G4': ['leakage'], 'G5': ['two_run_mismatch'], 'G6': ['compute_budget_exceeded']},
    }
    say('    failure_categories=%d includes chain_mismatch=%s' % (len(failures), 'design_invalid: chain_mismatch' in failures))

    say('[6/8] budget / pilot policy / schema ...')
    timing_ref = json.load(open(os.path.join(M3R2, 'timing_m3_stage2_run.json'), encoding='utf-8'))
    budget = {
        'caps': CAPS, 'compute_only': True, 'new_wells': 0,
        'closed_loop': sample['closed_loop_ledger'],
        'pilot_policy': 'execution must run a FINAL-IMPLEMENTATION Stage3 pilot (2 replicates x 7 arms x 300 units) '
                        'and measure wall/CPU/memory; freeze canonical timing before main; Stage2 pilot numbers are '
                        'historical reference only and must not be cited as Stage3 execution pilot',
        'stage2_pilot_reference_only': {'pilot_wall_s': timing_ref['pilot']['wall_s'],
                                        'pilot_cpu_s': timing_ref['pilot']['cpu_s'],
                                        'pilot_memory_gb': timing_ref['pilot']['memory_gb'],
                                        'sha': EXPECTED_CHAIN['research/2026-10-28-m3-stage2-run/timing_m3_stage2_run.json']},
        'main_projection_rule': 'main = R=10 x 7 arms x 300 units feedback/eval; projected wall must be measured by '
                                'pilot and verified <=1800 s; otherwise design_invalid: compute_budget_exceeded',
    }
    schema = {
        'schema': 'R204-M3-S3-EXEC', 'version': 'v1',
        'top_keys': ['task', 'status', 'chain', 'seeds', 'sample_semantics', 'stage3_arms', 'endpoints',
                     'headroom_mde', 'closed_loop_cost', 'G1_G6', 'failure_categories', 'budget',
                     'run_shas', 'failure_category', 'verdict'],
        'arm_fields': ['arm_id', 'role', 'update_rule', 'allocation_policy', 'n_feedback', 'n_eval', 'tuning_configs',
                       'cost_ledger', 'per_replicate_regret', 'mean_DeltaR', 'CI95', 'holm_p', 'pass'],
        'forbidden_fields': ['topk', 'method_comparison_as_effect', 'gain_claim', 'pharmacology_claim',
                             'real_decision_claim', 'transfer_claim', 'mechanism_claim', 'novelty_claim',
                             'real_data_result', 'sequential_DR_claim', 'allocation_comparison'],
        'failure_categories': failures,
        'no_effect_results': True, 'no_training_in_prereg': True,
        'two_run_rule': 'result JSON byte-identical; telemetry only separate file',
    }
    write_json(schema, SCHEMA)
    say('    schema written (endpoints/arms/closed-loop/failure categories)')

    say('[7/8] arithmetic/unit checks (no training) ...')
    checks = {
        'chain_files': len(chain), 'chain_pass': chain_pass,
        'stage1_pass': stage1_pass, 'stage2_c213_pass': stage2_pass,
        'failure_categories_count': len(failures),
        'chain_mismatch_present': 'design_invalid: chain_mismatch' in failures,
        'family_size': len(endpoints['family']),
        'primary_plus_five_secondary': bool(len(endpoints['family']) == 6),
        'arms_count': len(arms),
        'arms_include_standard_DR_TMLE': any(a['id'] == 'A_standard_DR_TMLE' for a in arms),
        'no_optimal_allocation_arm': not any('optimal_allocation' in a['id'] for a in arms),
        'all_arms_same_feedback_stream': True,
        'all_arms_same_allocation_policy': len({a['allocation_policy'] for a in arms}) == 1,
        'seeds_overlap': overlap, 'seeds_unique': seeds['unique'],
        'sample_units_total': sample['n_units_total'],
        'sample_feedback_total': sample['n_feedback_total'],
        'sample_matches': bool(sample['n_units_total'] == N_REPS * N_UNITS and sample['n_feedback_total'] == N_REPS * N_FEEDBACK),
        'MDE80': rq(mde), 'MDE80_le_delta': bool(mde <= DELTA), 'n_req_cluster': n_req_cluster,
        'no_training_executed': True,
    }
    checks['all_pass'] = bool(chain_pass and stage1_pass and stage2_pass and len(failures) == 13 and
                              checks['chain_mismatch_present'] and len(endpoints['family']) == 6 and
                              len(arms) == 7 and checks['arms_include_standard_DR_TMLE'] and checks['no_optimal_allocation_arm'] and checks['all_arms_same_feedback_stream'] and checks['all_arms_same_allocation_policy'] and
                              len(overlap) == 0 and seeds['unique'] and checks['sample_matches'] and
                              checks['MDE80_le_delta'])
    say('    chain=%s C213=%s family=%d arms=%d MDE=%.5f all_pass=%s' % (
        chain_pass, stage2_pass, len(endpoints['family']), len(arms), mde, checks['all_pass']))

    say('[8/8] write exec_plan_m3_s3.json ...')
    out = {
        'task': 'R204-M3-S3.1',
        'status': 'preregistration_only_not_executed; no training/effect/real data',
        'chain': {'files': chain, 'mismatches': mismatches, 'pass': chain_pass,
                  'stage1_pass': stage1_pass, 'stage2_c213_pass': stage2_pass},
        'seeds': seeds,
        'sample_semantics': sample,
        'stage3': stage3,
        'endpoints': endpoints,
        'precision_headroom': precision,
        'G1_G6': gates,
        'failure_categories': failures,
        'budget': budget,
        'unit_checks': checks,
        'schema_file': 'schema_m3_s3_exec.json',
        'scope': {'stage3_learning_comparison_only': True, 'no_effect_claim_here': True,
                  'no_allocation_comparison': True, 'no_training_executed': True, 'no_real_data': True,
                  'mechanism_account_only': True, 'new_wells': 0, 'compute_only': True},
        'stop_boundaries': [
            'standard DR/TMLE + optimal allocation equal-budget replication/exceed -> no_increment/withdraw',
            'pi=b -> H=1 degeneracy; collinearity/separation/no support -> nonidentifiable',
            'zero support/extreme weights -> support/positivity; truncation -> calibration',
            'evaluation reuse -> leakage; two-run/chain/budget -> corresponding design_invalid',
            'functional-mean-only update != cell dynamics; no sequential history/propensity/censoring -> no sequential DR claim',
            'no endpoint switch/relaxation; no old judgment/threshold changes',
        ],
        'boundaries': ['supporting mechanism account only; synthetic compute-only; 0 wells',
                       'no Stage3 execution in this task; no real data/wet lab; no Stage2/Stage1 changes',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'no modification of old gates/judgments; no revival of stopped experiments',
                       'M3 not mixed with M1/M2; N1 not used as M3 evidence; data readiness open (C203/C205/C210/C214)',
                       'Stage3 execution requires separate pre-registration + independent challenge + Lead approval'],
        'frozen_inputs': EXPECTED_CHAIN,
        'no_effect_results': True,
        'no_training_or_comparison_executed': True,
        'log_milestones': ['35-file chain + Stage1/C209 + Stage2/C213 verified', 'independent Stage3 seeds',
                           'fixed-feedback sample/arms frozen', 'primary/secondary/Holm/headroom/MDE frozen',
                           'closed-loop cost + 13 failure categories', 'schema first-written', 'arithmetic only'],
    }
    write_json(out, OUTJSON)
    print('exec_plan_m3_s3_v0_2.json sha256:', sha256_file(OUTJSON))
    print('schema_m3_s3_exec_v0_2.json sha256:', sha256_file(SCHEMA))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
