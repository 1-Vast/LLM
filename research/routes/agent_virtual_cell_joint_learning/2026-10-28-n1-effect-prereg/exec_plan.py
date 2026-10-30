#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R203-N1-EXEC-PREREG planning arithmetic: frozen-chain verification, execution seed allocation,
precision/headroom/budget planning, analysis/multiplicity freeze, schema and failure tree.
PLANNING ONLY: no method comparison, no regret/effect computation, no O'Neil responses.
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
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-n1-effect-prereg')
PREREG = os.path.join(ROOT, 'research', '2026-10-28-n1-synthetic-prereg')
IMPL = os.path.join(ROOT, 'research', '2026-10-28-n1-implementation')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'exec_plan.json')

DELTA = 0.05
Z_80 = 2.801585
ALPHA = 0.05
N_UNITS = 300
N_REPS = 50
N_METHODS = 7
T_ROUNDS = 6
T_FIT = 4
T_HOLD = 2
M_MENU = 5
ICC = 0.30
M_MENU_EFFECT = 5
DEFF = 1.0 + (M_MENU_EFFECT - 1) * ICC
N_EFF = N_UNITS / DEFF
N_REQ_CLUSTER = 278

GATE_SEEDS = [20261030, 20261061, 20261062, 20261063]
EXEC_SEED_BASE = 20261070
HEADROOM_SEED_BASE = 20261130
METHOD_SEED_BASE = 20262000
HEADROOM_REPS = 20

EXPECTED_CHAIN = {
    'research/2026-10-28-n1-synthetic-prereg/PROBLEM_N1_v0_4.md': '5C513D9461FAEDBD3372463A4FDD1868C927EB48501BC0CDEB7643FF6FA0649A',
    'research/2026-10-28-n1-synthetic-prereg/DESIGN_N1_v0_4.md': '94BAB8052EF4864BD745986326F4869D9054C2935794FEDAD8733733B57C029C',
    'research/2026-10-28-n1-synthetic-prereg/generator_n1_v0_4.py': 'AA5D454A82366BF3B7FC9E7F67FAA3499098621FAD45B84804485550E6EDCC97',
    'research/2026-10-28-n1-synthetic-prereg/generator_n1_v0_4.json': '35E41136E344AAF6C51A73B19418FF5CBEAD9460697BB8B1EE92F9E16D610263',
    'research/2026-10-28-n1-synthetic-prereg/V4_validation_v0_4.json': '254BEBAB201AA8A0EA33AEA8A47BC7D37A99ADE1436319D159603061DC8E2ECF',
    'research/2026-10-28-n1-synthetic-prereg/timing_n1_pilot_v0_4.json': 'A4C7E0F675B0020B99A93CC022572B3E85F30A26E391493AF45FAA3C005586C7',
    'research/2026-10-28-n1-synthetic-prereg/DECISION_R203_N1_PREREG.md': '930F1567254095945C228532AB8D1576915AAD01AC8ACC06185D99B573C174AD',
    'research/2026-10-28-n1-implementation/run_n1_gates.py': 'D2AA831F26AE8882F2B5B60C4C3FB2ACCAEA327AA381A4F949D32D23B276D7B8',
    'research/2026-10-28-n1-implementation/n1_gates.json': '529C1D2EE1E4B4039F4BBD10115C362EEE419D4BEF62A07FEC5A3C4046CBA0E0',
    'research/2026-10-28-n1-implementation/n1_gates_rows.csv': '78457E1F97B85D1D70918BFCE28AB0E79123225E5D9BD3589EACF951B587F6EB',
    'research/2026-10-28-n1-implementation/timing_n1_gates.json': '5A52E42F845A4127E2FB09E0DA9061FB591C83DE474E8C5286380CF17F7F75AC',
    'research/2026-10-28-n1-implementation/schema_n1_gates.json': 'F2D561D9C4B3E8AEE4EF785D3C98EF55A701059FC750AE32D588135CF9C5AB1D',
    'research/2026-10-28-n1-implementation/report_n1_gates.md': '38CFD34CFE741F95BA895B83C90086440508EB49030DC3F6A6E8B080E682CAF5',
    'research/2026-10-28-n1-implementation/record_n1_gates.md': 'DA21E2D914C98098735FD2CF6AE0C3ED69E68708CD8DD21A7C51CFC1CDCA7680',
    'research/2026-10-28-n1-implementation/usage_n1_gates.json': 'F795C15DF50AA3A284CB7173B61265D2752F987A96AA428E0E59F8EB322B4DD7',
}
EXPECTED_V4_SPEC_SHA = 'A69B845D9808A93444042CC034F37EA4E9AA74C03835BACC39DF5445A6BF3289'
EXPECTED_GATES = {
    'V1_delta_f_over_sigma': 11.6553919588,
    'V2_KL': 0.6170250568,
    'V3_E_h': 0.5089123677,
    'V4_mean': 503.04246827, 'V4_SE': 64.42138097,
    'V4_CI': [376.77888173, 629.30605481], 'V4_seed': 20261062,
    'G1_k': 976, 'G1_n': 20000, 'G1_point': 0.0488, 'G1_wilson': 0.0518735422,
    'G2_powers': [1.0, 1.0, 1.0],
    'G3_dims': [143, 600, 140, 3],
    'G7_per_rep_s': 0.0455, 'G7_projected_main_s': 20.48, 'G7_memory_gb': 0.04,
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

    say('[1/7] verify frozen chain (v0.4 + C204 + decision) ...')
    chain = {}
    mismatches = {}
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
    say('    chain files=%d mismatches=%d pass=%s' % (len(chain), len(mismatches), chain_pass))

    # V4 spec SHA and gate numbers
    v4val = json.load(open(os.path.join(PREREG, 'V4_validation_v0_4.json'), encoding='utf-8'))
    gates = json.load(open(os.path.join(IMPL, 'n1_gates.json'), encoding='utf-8'))
    timing = json.load(open(os.path.join(IMPL, 'timing_n1_gates.json'), encoding='utf-8'))
    checks = {}
    checks['V4_spec_sha'] = {'expected': EXPECTED_V4_SPEC_SHA,
                             'actual': v4val.get('model_spec_sha256'),
                             'pass': v4val.get('model_spec_sha256') == EXPECTED_V4_SPEC_SHA}
    checks['V4_gate'] = {
        'mode': v4val.get('gate_decision', {}).get('mode'),
        'mean': gates['gates']['V4']['mean_DeltaELPD'],
        'SE': gates['gates']['V4']['SE'],
        'CI95': gates['gates']['V4']['CI95'],
        'seed': gates['gates']['V4']['seed_base'],
        'pass': bool(gates['gates']['V4']['pass'] and
                     abs(gates['gates']['V4']['mean_DeltaELPD'] - EXPECTED_GATES['V4_mean']) < 1e-6 and
                     abs(gates['gates']['V4']['SE'] - EXPECTED_GATES['V4_SE']) < 1e-6 and
                     gates['gates']['V4']['seed_base'] == EXPECTED_GATES['V4_seed'])}
    checks['G1'] = {'k': gates['gates']['G1']['k'], 'n': gates['gates']['G1']['n_mc'],
                    'point': gates['gates']['G1']['point'], 'wilson': gates['gates']['G1']['wilson_upper_95'],
                    'pass': bool(gates['gates']['G1']['pass'] and
                                 gates['gates']['G1']['k'] == EXPECTED_GATES['G1_k'] and
                                 gates['gates']['G1']['n_mc'] == EXPECTED_GATES['G1_n'])}
    checks['G2'] = {'powers': [gates['gates']['G2']['power_state'],
                               gates['gates']['G2']['power_interaction'],
                               gates['gates']['G2']['power_history']],
                    'pass': bool(gates['gates']['G2']['pass'])}
    checks['G3'] = {'dims': gates['gates']['G3']['full_params_obs_rank_nullity'],
                    'pass': bool(gates['gates']['G3']['pass'] and
                                 gates['gates']['G3']['full_params_obs_rank_nullity'] == EXPECTED_GATES['G3_dims'])}
    checks['G7'] = {'per_rep_s': timing['G7_pilot']['per_replicate_total_seconds'],
                    'projected_main_s': timing['G7_pilot']['projected_main_wall_seconds'],
                    'memory_gb': timing['G7_pilot']['memory_gb_observed'],
                    'B2_audit': timing['G7_pilot']['B2_equivalence_audit_pass'],
                    'pass': bool(timing['G7_pilot']['projected_pass'] and
                                 timing['G7_pilot']['B2_equivalence_audit_pass'])}
    prechain_pass = bool(chain_pass and all(c.get('pass') for c in checks.values()))
    say('    V4spec=%s V4gate=%s G1=%s G2=%s G3=%s G7=%s' % (
        checks['V4_spec_sha']['pass'], checks['V4_gate']['pass'], checks['G1']['pass'],
        checks['G2']['pass'], checks['G3']['pass'], checks['G7']['pass']))

    say('[2/7] execution seed allocation (independent of gate seeds) ...')
    exec_seeds = [EXEC_SEED_BASE + r for r in range(N_REPS)]
    headroom_seeds = [HEADROOM_SEED_BASE + r for r in range(HEADROOM_REPS)]
    method_seeds = [[METHOD_SEED_BASE + r * 10 + m for m in range(N_METHODS)] for r in range(N_REPS)]
    all_exec = exec_seeds + headroom_seeds + [s for row in method_seeds for s in row]
    overlap = sorted(set(all_exec) & set(GATE_SEEDS))
    unique_ok = len(set(all_exec)) == len(all_exec)
    # dry seed allocation: first RNG draw per execution seed (deterministic; not an effect)
    first_draws = []
    for s in exec_seeds:
        rng = np.random.default_rng(s)
        first_draws.append(float(rng.random()))
    seed_table = {'exec_seed_base': EXEC_SEED_BASE, 'n_reps': N_REPS,
                  'exec_seeds': exec_seeds,
                  'headroom_seed_base': HEADROOM_SEED_BASE, 'headroom_reps': HEADROOM_REPS,
                  'headroom_seeds': headroom_seeds,
                  'method_seed_base': METHOD_SEED_BASE, 'method_seeds': method_seeds,
                  'gate_seeds_forbidden': GATE_SEEDS,
                  'overlap_with_gate_seeds': overlap,
                  'unique': bool(unique_ok),
                  'dry_first_draw_sha256': hashlib.sha256(
                      json.dumps(first_draws).encode('utf-8')).hexdigest().upper(),
                  'seed_table_sha256': hashlib.sha256(
                      json.dumps({'exec': exec_seeds, 'head': headroom_seeds, 'meth': method_seeds},
                                 sort_keys=True).encode('utf-8')).hexdigest().upper()}
    say('    exec seeds=%d..%d; overlap=%s; unique=%s' % (
        exec_seeds[0], exec_seeds[-1], overlap, unique_ok))

    say('[3/7] precision / headroom planning ...')
    mde = Z_80 * 0.20 / math.sqrt(N_EFF)
    deff = DEFF
    n_req = int(math.ceil((Z_80 * 0.20 / DELTA) ** 2))
    n_req_cluster = int(math.ceil(n_req * deff))
    precision = {
        'delta': DELTA, 'n_units_per_rep': N_UNITS, 'n_reps': N_REPS,
        'menu_m': 5, 'ICC': ICC, 'design_effect': deff, 'n_eff_conservative': rq(N_EFF),
        'conservative_SD_D': 0.20, 'MDE80_conservative': rq(mde), 'MDE80_formula':
            '2.801585*SD(D)/sqrt(n_eff); n_eff=n_units/deff',
        'MDE80_le_delta': bool(mde <= DELTA),
        'n_req_independent': n_req, 'n_req_cluster': n_req_cluster, 'n_req_le_n_units': bool(n_req_cluster <= N_UNITS),
        'primary_analysis_note': 'primary analysis uses all R*n_units paired unit differences with cluster-robust '
                                 'SE clustered by replicate (G=50); the conservative MDE above uses only one '
                                 'replicate worth of independent units (n_units=300), so actual precision is '
                                 'at least this good; report both conservative and cluster-robust SE',
        'headroom_preflight': {
            'rule': 'headroom = U_max - U0(B2) on pre-effect headroom calibration (headroom seeds, 20 reps x 300 '
                    'units, independent of execution/gate seeds); if headroom < delta -> unreachable_gate; if B2 '
                    'near ceiling -> separate budget-to-target problem, never silently switch endpoint',
            'U_max': 1.0, 'delta': DELTA, 'requires_headroom_ge_delta': True,
            'headroom_seed_base': HEADROOM_SEED_BASE, 'headroom_reps': HEADROOM_REPS,
        },
    }
    say('    n_eff=%.3f MDE80=%.5f<=.05:%s n_req=%d<=%d' % (
        N_EFF, mde, mde <= DELTA, n_req_cluster, N_UNITS))

    say('[4/7] methods / equal-budget freeze ...')
    methods = {
        'primary_comparison': 'M (N1 method) vs B2 (static S-add)',
        'baselines': ['B1 full retrain', 'B2 static S-add', 'B3 hierarchical/EB', 'B4 GP',
                      'B5 random plan-pair', 'B6 decision AL'],
        'equal_budget': {'T_rounds': T_ROUNDS, 'feedback_per_round': 1, 'features_same': True,
                         'prior_same': True, 'initial_data_same': True, 'tuning_configs_max': 20,
                         'query_count_same': T_ROUNDS, 'compute_caps_same': True,
                         'seed_same_for_baseline_initialization': True},
        'B2_equivalence_audit': 'must be re-confirmed at execution with final effect runner (same initial-data '
                                'hash, menus/round, query count, prior, tuning budget, shared dataset seed)',
        'frozen_generator_import': 'read-only import of research/2026-10-28-n1-synthetic-prereg/generator_n1_v0_4.py '
                                   '(SHA AA5D454A...); do not copy/modify frozen code',
    }
    say('    primary M vs B2; baselines B1-B6; T=6/1 feedback/tuning<=20 frozen')

    say('[5/7] analysis / multiplicity / decision tree freeze ...')
    analysis = {
        'primary_endpoint': 'paired held-out decision regret D_i = R_i(M) - R_i(B2) (lower better); '
                            'R_i = mean held-out regret over T_hold=2 rounds for unit i; U in [0,1]',
        'delta': DELTA, 'delta_units': 'normalized utility (0.05)',
        'primary_units': 'decision units i nested in replicates r; paired D_i; all R*n_units=15000 units',
        'clustering': 'cluster-robust SE by replicate (G=50); conservative MDE computed on n_units=300 single '
                      'replicate (see precision)',
        'primary_success': 'mean DeltaR <= -delta AND 95% CI upper < 0 AND Holm-adjusted p < 0.05 in the '
                           'pre-registered family of 6 planned comparisons (primary + 5 secondaries)',
        'multiplicity': {'family_size': 6, 'method': 'Holm', 'alpha': ALPHA,
                         'tests': ['M vs B1', 'M vs B2 (primary)', 'M vs B3', 'M vs B4', 'M vs B5', 'M vs B6']},
        'secondary': 'B1, B3, B4, B5, B6 vs M paired DeltaR; same Holm family; descriptive direction only if '
                     'primary fails',
        'no_endpoint_switch': 'primary must remain held-out decision regret; cannot switch to prediction/top-k/'
                              'budget endpoint after results; headroom<delta -> unreachable_gate; near-ceiling -> '
                              'separate budget-to-target problem',
        'decision_tree': {
            'unreachable_gate': 'headroom < delta on pre-effect headroom calibration; stop, not algorithm failure',
            'precision_insufficient': 'conservative MDE80 > delta or n_req > n_units; stop/expand resources, not '
                                      'algorithm failure',
            'success': 'primary criteria all met',
            'no_increment': 'primary CI excludes -delta on the non-improving side (upper >= 0 or lower > -delta) '
                            'and no secondary significant in favor of M; retract algorithm claim',
            'inconclusive': 'primary CI overlaps both 0 and -delta without meeting success; no positive/negative '
                            'algorithm claim',
            'design_invalid': 'chain_mismatch, schema_mismatch, two_run_mismatch, leakage, compute_budget_exceeded, '
                              'generator_misspecified, calibration_failed, nonidentifiable',
        },
        'reporting': 'mean DeltaR, 95% CI, Holm p for each comparison; per-method/per-replicate selection regret, '
                     'selected U, oracle U, cost ledger; no exploratory endpoints',
    }
    say('    primary M vs B2; Holm family 6; decision tree frozen')

    say('[6/7] budget / schema / failure categories ...')
    budget = {
        'main': {'n_units': N_UNITS, 'replicates': N_REPS, 'methods': N_METHODS, 'T_rounds': T_ROUNDS,
                 'feedback_per_round': 1},
        'caps': {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8},
        'new_wells': 0, 'compute_only': True, 'A_B_resources': 'none',
        'C204_pilot_reference': {'per_replicate_total_seconds': EXPECTED_GATES['G7_per_rep_s'],
                                 'projected_main_wall_seconds': EXPECTED_GATES['G7_projected_main_s'],
                                 'memory_gb_observed': EXPECTED_GATES['G7_memory_gb'],
                                 'timing_file': 'research/2026-10-28-n1-implementation/timing_n1_gates.json',
                                 'sha': '5A52E42F845A4127E2FB09E0DA9061FB591C83DE474E8C5286380CF17F7F75AC'},
        'pre_execution_G7_recheck': 'run effect-runner pilot (2 replicates) with final implementation; if projected '
                                    'wall > 1800 s or CPU > 7200 s or memory > 8 GB -> compute_budget_exceeded '
                                    '(no reduction of n_units/R/methods allowed)',
        'two_runs': {'run1': 'same seeds, separate process', 'run2': 'same seeds, separate process',
                     'check': 'result JSON (no telemetry) byte-identical; else design_invalid: two_run_mismatch',
                     'telemetry': 'wall/CPU/memory only in separate timing file'},
    }
    schema = {
        'top_keys': ['task_id', 'status', 'frozen_chain', 'seeds', 'design', 'per_replicate', 'summary',
                     'headroom', 'cost_ledger', 'run_shas', 'failure_category', 'verdict'],
        'per_replicate_fields': ['replicate_id', 'dataset_seed', 'method_seeds', 'n_units',
                                 'heldout_regret_mean', 'heldout_selected_U_mean', 'oracle_U_mean',
                                 'n_queries', 'n_feedback', 'tuning_configs', 'method'],
        'summary_fields': ['primary_mean_DeltaR', 'primary_CI95', 'primary_holm_p',
                           'secondary_effects', 'secondary_holm_p', 'n_units_total', 'n_replicates'],
        'forbidden_fields': ['prediction_accuracy', 'topk_hit', 'budget_to_target_effect', 'exploratory_endpoint',
                             'pharmacology_claim', 'real_decision_claim', 'transfer_claim', 'mechanism_claim',
                             'novelty_claim'],
        'no_unregistered_endpoints': True,
    }
    failures = {
        'categories': ['design_invalid: chain_mismatch', 'design_invalid: schema_mismatch',
                       'design_invalid: two_run_mismatch', 'design_invalid: leakage',
                       'design_invalid: compute_budget_exceeded', 'design_invalid: generator_misspecified',
                       'design_invalid: calibration_failed', 'design_invalid: nonidentifiable',
                       'unreachable_gate', 'precision_insufficient', 'no_increment', 'inconclusive'],
        'failure_policy': 'any design_invalid stops and writes failure_category only (no method differences); '
                          'unreachable_gate/precision_insufficient are not algorithm failures; no_increment/inconclusive '
                          'retract/withhold algorithm claim; no endpoint switch',
    }
    say('    budget caps 1800/7200/8GB; 0 wells; schema+forbidden fields; failure categories frozen')

    say('[7/7] write exec_plan.json ...')
    out = {
        'task': 'R203-N1-EXEC-PREREG',
        'status': 'planning_only_no_effect_results',
        'pre_execution_chain': {'chain': chain, 'mismatches': mismatches, 'pass': chain_pass,
                                'gate_checks': checks, 'full_pass': prechain_pass},
        'seed_plan': seed_table,
        'precision_headroom': precision,
        'methods_equal_budget': methods,
        'analysis_multiplicity': analysis,
        'budget': budget,
        'schema': schema,
        'failure_categories': failures,
        'frozen_chain_files': EXPECTED_CHAIN,
        'V4_model_spec_sha256': EXPECTED_V4_SPEC_SHA,
        'execution_design': {
            'n_units': N_UNITS, 'replicates': N_REPS, 'methods': N_METHODS, 'T_rounds': T_ROUNDS,
            'T_fit': T_FIT, 'T_hold': T_HOLD, 'menu_m': M_MENU,
            'primary_endpoint': 'paired held-out decision regret D_i=R_i(M)-R_i(B2), delta=.05 normalized',
            'primary_unit': 'decision unit within replicate; cluster-robust by replicate',
            'generator': 'frozen read-only generator_n1_v0_4.py (SHA AA5D454A...)',
            'runner': 'new effect runner at execution time (must not modify frozen generator/methods)',
        },
        'boundaries': ['mechanism account only; synthetic compute-only; 0 wells',
                       'no pharmacology/real decisions/transfer/mechanism/novelty claims',
                       'no effect results in this planning task; no method differences reported',
                       'no code promotion; no modification of old gates/judgments; no revival of stopped experiments',
                       'N1 effect execution requires independent challenge + Lead approval'],
        'no_effect_results': True,
        'no_method_comparison_executed': True,
        'log_milestones': ['frozen chain + C204 gate verification', 'independent execution seeds allocated',
                           'precision/headroom planned', 'analysis/multiplicity frozen', 'budget/schema/failure tree frozen'],
    }
    write_json(out, OUTJSON)
    print('exec_plan.json sha256:', sha256_file(OUTJSON))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
