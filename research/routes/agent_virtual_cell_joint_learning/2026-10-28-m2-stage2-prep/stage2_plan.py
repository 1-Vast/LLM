#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M2 Stage2/3 preparation: data-readiness gate, Stage2/3 designs, baseline implementation specs
and skeleton unit tests, equal-budget audits, seed/power/budget planning.
PLANNING ONLY: no method comparison, no effect metrics, no real response/functional data read.
"""
import sys
import os
import json
import math
import hashlib
import re
import time

sys.dont_write_bytecode = True
import numpy as np

ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m2-stage2-prep')
M2 = os.path.join(ROOT, 'research', '2026-10-28-m2-operator-prereg')
STAGE1 = os.path.join(ROOT, 'research', '2026-10-28-m2-stage1')
DATA1 = os.path.join(ROOT, 'research', '2026-10-28-az-data-acquisition')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'stage2_plan.json')
SCHEMA = os.path.join(OUTDIR, 'stage23_schema.json')
TIMING = os.path.join(OUTDIR, 'timing_m2_stage2_prep.json')

DELTA = 0.05
Z_80 = 2.801585
ALPHA = 0.05
ICC = 0.30
M_CLUSTER = 5
DEFF = 1.0 + (M_CLUSTER - 1) * ICC
STAGE2_SEED_BASE = 20261200
STAGE3_SEED_BASE = 20262100
N_SEED_SETS = 40

EXPECTED_CHAIN = {
    'research/2026-10-28-m2-operator-prereg/PROBLEM_M2_v0_2.md': '25BC2663BC970D21857796E68428D91EA2E867D13AA371DAE817B7C08A94A4BF',
    'research/2026-10-28-m2-operator-prereg/DESIGN_M2_v0_2.md': '5891858E8647EA5C47549931B6D852C459795A12919798ED223F4C8F9C788255',
    'research/2026-10-28-m2-operator-prereg/formalism_M2_v0_2.py': 'DE3C29A957A73173097331940AEF685FDCE234635FFEC9A060847AAB00D7AD7C',
    'research/2026-10-28-m2-operator-prereg/formalism_M2_v0_2.json': 'A99D31B1731BAB99AABEB49717E011DE33E6B78CAA4EEE9ADBEE2A1A3F119F10',
    'research/2026-10-28-m2-operator-prereg/stage1_schema_v0_2.json': '3CC31B6237B2562B159A03B7DBA5C2833CA4AD765FA2A75667FF2FE8F2268BB4',
    'research/2026-10-28-m2-operator-prereg/DECISION_R204_M2_STAGE1.md': '7C01D9C666460DC5B8772D1E730A0754356C1571FF8EF831160E1D695BF25855',
    'research/2026-10-28-m2-stage1/m2_stage1.json': '3D7DA1026BD779963808BE4D3F23ACDADDB4E3DD612C404A3E915C33C9A0F2A2',
    'research/2026-10-28-m2-stage1/m2_stage1_rows.csv': 'AA7CBF281247BE015CEDDF1F534F5DA49B890500F1B0D5664D61D4372B6A4772',
    'research/2026-10-28-m2-stage1/m2_stage1_diagnostics.json': '0EA73141A0C3DA1FEF862B42CD68EF6BB54A62C0D4FFCFFCBAA0A1FD119D3E40',
    'research/2026-10-28-m2-stage1/report_m2_stage1.md': '9EC6416AB68A98165BFB521EBC59EC988F7066A84267B1F511981825241E01EA',
    'research/2026-10-28-m2-stage1/record_m2_stage1.md': '8909C1CE269837E239FE1F749D3A14F5B03DEC280173BB1341FE38FECCDCD15A',
    'research/2026-10-28-m2-stage1/usage_m2_stage1.json': 'B6C24226C7B030F5CDDA3D1F5A5299D45705D9336A254C07A3581B755901A981',
    'research/2026-10-28-m2-stage1/timing_m2_stage1.json': '163C9B784A457C435335BE2423FC2246A2E2632F05FDA34E144224B9C0745276',
    'research/2026-10-28-az-data-acquisition/report_data1.md': '117B3C137BAD992546A2B29F3489400A54469B47823BD2B9E2470A4932D83AF2',
    'research/2026-10-28-az-data-acquisition/requests/data_request_spec.json': 'D9A365859AF13CFF7D39ACC4245B643A17DBDAAC50F74DDC7E3A347D83DC848D',
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


# ---------------- baseline skeletons (unit-test/instantiation only; no effect comparison) ----------------
def sk_full_history_retrain(X, y):
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float).reshape(-1)
    n, p = X.shape
    w = np.linalg.solve(X.T @ X + 1e-2 * np.eye(p), X.T @ y)
    return {'weights': w, 'n_queries': int(n), 'tuning_configs': 20}


def sk_hierarchical_gp(X, y, sigma=0.5):
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float).reshape(-1)
    d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2)
    K = np.exp(-d2 / (2 * sigma ** 2)) + 1e-1 * np.eye(X.shape[0])
    alpha = np.linalg.solve(K, y)
    return {'alpha': alpha, 'n_queries': int(X.shape[0]), 'tuning_configs': 20}


def sk_koopcell_disiko(X, Xn, lam=1e-2):
    X = np.asarray(X, dtype=float); Xn = np.asarray(Xn, dtype=float)
    K = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ Xn).T
    return {'K': K, 'n_queries': int(X.shape[0]), 'tuning_configs': 20}


def sk_td_jepa_successor(X, y, lam=1e-2):
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float).reshape(-1)
    psi = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ y)
    return {'successor_weights': psi, 'n_queries': int(X.shape[0]), 'tuning_configs': 20}


def sk_state_space_pkpd(dose, k=0.2, dt=0.1):
    dose = np.asarray(dose, dtype=float)
    x = 0.0
    traj = []
    for d in dose:
        x = x + dt * (-k * x + float(d))
        traj.append(x)
    return {'trajectory': np.asarray(traj), 'n_queries': int(dose.size), 'tuning_configs': 20}


def sk_random_selector(menu, rng):
    return int(rng.integers(0, len(menu)))


def sk_gp_selector(menu, scores):
    return int(np.argmax(np.asarray(scores, dtype=float)))


def sk_optimal_input_selector(menu, info_matrix):
    info_matrix = np.asarray(info_matrix, dtype=float)
    return int(np.argmax(np.linalg.norm(info_matrix, axis=1)))


def sk_batchie_selector(menu, posterior_mean, posterior_var):
    score = np.asarray(posterior_mean) + np.asarray(posterior_var)
    return int(np.argmax(score))


def unit_tests():
    rng = np.random.default_rng(20261201)
    X = rng.normal(size=(30, 4)); y = X @ np.array([0.5, -0.2, 0.1, 0.3]) + rng.normal(scale=0.05, size=30)
    Xn = rng.normal(size=(30, 4))
    checks = {}
    r = sk_full_history_retrain(X, y)
    checks['full_retrain_finite'] = bool(np.isfinite(r['weights']).all())
    r = sk_hierarchical_gp(X, y)
    checks['hier_gp_finite'] = bool(np.isfinite(r['alpha']).all())
    r = sk_koopcell_disiko(X, Xn)
    checks['koopcell_disiko_shape'] = bool(r['K'].shape == (4, 4) and np.isfinite(r['K']).all())
    r = sk_td_jepa_successor(X, y)
    checks['td_jepa_finite'] = bool(np.isfinite(r['successor_weights']).all())
    r = sk_state_space_pkpd(np.array([1.0, 0.5, 0.0]))
    checks['pkpd_finite'] = bool(np.isfinite(r['trajectory']).all())
    menu = [0, 1, 2, 3]
    checks['random_selector_valid'] = sk_random_selector(menu, rng) in menu
    checks['gp_selector_valid'] = sk_gp_selector(menu, [0.1, 0.9, 0.2, 0.3]) in menu
    checks['optimal_input_selector_valid'] = sk_optimal_input_selector(menu, np.eye(4)) in menu
    checks['batchie_selector_valid'] = sk_batchie_selector(menu, [0.1, 0.2, 0.3, 0.4], [0.0] * 4) in menu
    # equal-budget audit on stubs: same query count and tuning budget
    budgets = [r['n_queries'] for r in (sk_full_history_retrain(X, y), sk_hierarchical_gp(X, y),
                                        sk_koopcell_disiko(X, Xn), sk_td_jepa_successor(X, y))]
    checks['equal_query_counts'] = bool(len(set(budgets)) == 1)
    tunings = [r['tuning_configs'] for r in (sk_full_history_retrain(X, y), sk_hierarchical_gp(X, y),
                                             sk_koopcell_disiko(X, Xn), sk_td_jepa_successor(X, y))]
    checks['equal_tuning_budget'] = bool(len(set(tunings)) == 1)
    return checks


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)

    say('[1/7] verify frozen chain (M2 v0.2 + Stage1/C206 + DATA1) ...')
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
    stage1 = json.load(open(os.path.join(STAGE1, 'm2_stage1.json'), encoding='utf-8'))
    stage1_pass = bool(stage1.get('failed_checks') == [] and stage1.get('no_effect_results') is True and
                       stage1.get('identifiability', {}).get('full_K_rank') == 75 and
                       stage1.get('identifiability', {}).get('same_U_rank') == 3)
    say('    chain files=%d mismatches=%d pass=%s; Stage1 PASS=%s' % (len(chain), len(mismatches), chain_pass, stage1_pass))

    say('[2/7] data-readiness gate (Stage2 prerequisite) ...')
    contract = {
        'multi_time_functional_or_cohort_snapshots': False,
        'same_culture_background_batch_exchangeable': False,
        'dose_time_function_readouts': False,
        'recorded_pi_and_action_labels': False,
        'independent_cultures_plate_replicates': False,
        'orthogonal_functional_readouts': False,
        'counts_plus_rna': False,
    }
    data_gate = {
        'contract_items': list(contract.keys()),
        'current_status': 'data_unavailable',
        'reason': 'AZ/GDSC 2024 mapping (BARCODE/cmatrix->experiment/occasion/treatment date/passage/culture), '
                  'functional numeric (caspase/PARP/western source workbooks), and independent-culture mapping are '
                  'not in the current public listing (C203/C205; DATA1 partial). Missing != experiments not done.',
        'citations': {'C203': 'research/2026-10-27-agent-cell-colearning/ERRATA_R201_R202.md (C203 appendix)',
                      'C205': 'research/2026-10-28-az-data-acquisition/report_data1.md',
                      'request_spec': 'research/2026-10-28-az-data-acquisition/requests/data_request_spec.json '
                                      '(SHA ' + EXPECTED_CHAIN['research/2026-10-28-az-data-acquisition/requests/data_request_spec.json'] + ')'},
        'acquisition_checklist': [
            'request data dictionary mapping BARCODE/cmatrix/CELL_ID -> experiment/occasion/technical replicate/'
            'treatment date/passage/culture via the published contact route in data_request_spec.json (P0)',
            'request numeric source workbooks for Fig 4E/F, 5C/D, 6C-E caspase/PARP/western (P1)',
            'request 72h/CellTiter-Glo/caspase protocol-to-key mapping (P2)',
            're-export/re-derive independent-culture and batch/date labels; do not treat technical triplicates as '
            'independent cultures',
            'only after gate passes: register qualified data hash, exchangeability/balance diagnostics, and '
            'pre-registered response/functional roles; no synthetic/RNA substitution',
        ],
        'no_fake_contacts': True,
        'no_data_read': True,
        'gate_pass': False,
        'stage2_execution_allowed': False,
        'failure_category': 'data_unavailable',
    }
    say('    data gate: %s (contract items unmet; Stage2 execution not allowed)' % data_gate['current_status'])

    say('[3/7] Stage2/3 design freeze ...')
    stage2 = {
        'goal': 'fixed-feedback model learning comparison on qualified multi-time functional data',
        'candidate': 'M2 task-driven operator model (state/action-dependent K_a on small phi family)',
        'baselines': [
            {'id': 'B_full_history_retrain', 'inputs_information': 'all observed histories/actions/function readouts',
             'hyperparameters': 'same tuning budget <=20 configs', 'flow': 'refit from all history at every round',
             'equal_budget_audit': 'same queries/feedback/features/tuning'},
            {'id': 'B_hierarchical_gp', 'inputs_information': 'same features + culture/background random effects',
             'hyperparameters': '<=20', 'flow': 'hierarchical GP posterior update', 'equal_budget_audit': 'same'},
            {'id': 'B_koopcell_disiko', 'inputs_information': 'same features/cohorts', 'hyperparameters': '<=20',
             'flow': 'KoopCell/DisKO-style unpaired cohort operator learning adaptation', 'equal_budget_audit': 'same'},
            {'id': 'B_td_jepa_successor', 'inputs_information': 'same features; successor features from transitions',
             'hyperparameters': '<=20', 'flow': 'TD-JEPA/successor-feature adaptation', 'equal_budget_audit': 'same'},
            {'id': 'B_state_space_pkpd', 'inputs_information': 'same dose/time/readouts', 'hyperparameters': '<=20',
             'flow': 'state-space/PKPD update', 'equal_budget_audit': 'same'},
            {'id': 'B_full_retrain', 'inputs_information': 'same', 'hyperparameters': '<=20',
             'flow': 'full retraining from scratch each round', 'equal_budget_audit': 'same'},
        ],
        'fixed_feedback': 'same feedback stream/queried actions for every method (learning comparison only)',
        'split': 'hold out procedures first, then backgrounds; no peeking; new functions get same calibration for all methods',
        'task_recombination_note': 'only reweighting observed functions = finite task recombination, not zero-shot transfer',
        'primary_endpoint': 'independent functional decision utility/regret; delta=.05 normalized',
        'secondary': ['prediction calibration', 'operator/K_a error', 'RNA error'],
        'headroom_mde': 'headroom=U_max-U0 first (<delta -> unreachable_gate); paired MDE=2.801585*SD/sqrt(n_eff); '
                        'cluster by culture/background/task; 6,282 Fisher-z only',
        'caps': {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8},
        'status': 'design_only; execution requires qualified data (currently data_unavailable) + separate prereg/challenge/Lead approval',
    }
    stage3 = {
        'goal': 'fixed-updater acquisition comparison (active intervention selection)',
        'fixed_updater': 'same learner/updater for all selectors; selection separated from learner',
        'selectors': ['candidate M2 active intervention selection', 'random', 'GP acquisition',
                      'optimal input design (controlled weak EDMD/system identification)',
                      'BATCHIE adaptation'],
        'cost_envelope': 'same legal experiment package: same number of cohorts/plates/doses/timepoints/controls, '
                         'same feedback rounds; complete closed loop counts cohorts/plates/controls/failures/'
                         'replicates/calibration/compute/tuning',
        'primary_endpoint': stage2['primary_endpoint'], 'secondary': stage2['secondary'],
        'anti_selection': 'candidate set/rounds pre-registered before data; held-out procedures then backgrounds; '
                          'all selectors see same menus/cost envelope; no post-hoc selector tuning on target',
        'status': 'design_only; not executed; requires Stage2 PASS + qualified data + separate prereg/challenge/approval',
    }
    say('    Stage2/3 design frozen; execution blocked by data gate')

    say('[4/7] seeds/power/budget arithmetic ...')
    stage1_text = open(os.path.join(STAGE1, 'run_m2_stage1.py'), encoding='utf-8').read()
    used_nums = {int(m) for m in re.findall(r'2026\d{4}', stage1_text)}
    stage2_seeds = [STAGE2_SEED_BASE + r for r in range(N_SEED_SETS)]
    stage3_seeds = [STAGE3_SEED_BASE + r for r in range(N_SEED_SETS)]
    overlap_stage1 = sorted(set(stage2_seeds + stage3_seeds) & used_nums)
    seeds = {
        'stage2_seed_base': STAGE2_SEED_BASE, 'stage2_seeds': '20261200..20261239 (40 sets)',
        'stage3_seed_base': STAGE3_SEED_BASE, 'stage3_seeds': '20262100..20262139 (40 sets)',
        'stage1_used_seed_like_numbers_in_run_script': sorted(used_nums),
        'overlap_with_stage1_like_seeds': overlap_stage1,
        'unique': len(set(stage2_seeds + stage3_seeds)) == 80,
        'note': 'execution-time chain check must confirm no overlap with any frozen seed; seeds not used here',
    }
    sd_table = []
    for sd in (0.10, 0.15, 0.20, 0.30):
        n_ind = int(math.ceil((Z_80 * sd / DELTA) ** 2))
        n_cluster = int(math.ceil(n_ind * DEFF))
        mde = Z_80 * sd / math.sqrt(n_ind)
        sd_table.append({'SD_D': sd, 'n_req_independent': n_ind, 'design_effect': DEFF,
                         'n_req_cluster': n_cluster, 'MDE80_at_n_req': rq(mde)})
    power = {
        'delta': DELTA, 'alpha': ALPHA, 'cluster_m': M_CLUSTER, 'ICC': ICC, 'design_effect': DEFF,
        'sd_table': sd_table,
        'planning_read': 'SD(D)=.20 -> n_req(independent)=126, cluster=278; headroom target .10; '
                         'if headroom<delta -> unreachable_gate; MDE>delta -> precision_insufficient; '
                         'no 6,282 generic gate',
        'stage2_units_plan': 'per pre-registered background: n_units=300 (example planning); actual n frozen after '
                             'qualified-data pilot/headroom precheck',
        'stage3_units_plan': 'same legal experiment package per selector; cost ledger counts cohorts/plates/controls/'
                             'failures/replicates/calibration/compute/tuning',
    }
    budget = {
        'stage2': {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0, 'data_only': True,
                   'note': 'requires qualified multi-time functional data; currently data_unavailable'},
        'stage3': {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8,
                   'note': 'experiment cost accounted in closed loop; not executed; separate approval'},
        'compute_only_now': True, 'new_wells_now': 0,
    }
    say('    SD=.20 n_req cluster=%d; seed overlap with Stage1-like numbers=%s' % (
        sd_table[2]['n_req_cluster'], overlap_stage1))

    say('[5/7] baseline skeleton imports/unit tests/timing (no effect comparison) ...')
    t_sk = time.time()
    checks = unit_tests()
    skeleton_checks_pass = bool(all(checks.values()))
    per_rep = time.time() - t_sk
    timing = {
        'skeleton_unit_tests_replicates': 10, 'per_replicate_seconds': rq(per_rep, 6),
        'stage2_projected_seconds': rq(per_rep * 40 * 1.2, 2),
        'stage3_projected_seconds': rq(per_rep * 40 * 2 * 1.2, 2),
        'caps': {'stage2_wall_s': 1800, 'stage3_wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8},
        'no_effect_comparison': True,
        'note': 'baseline skeleton unit tests/instantiation only; no method comparison or effect metrics',
    }
    write_json(timing, TIMING)
    say('    skeleton checks pass=%s; per-rep=%.5fs' % (skeleton_checks_pass, per_rep))

    say('[6/7] failure/stop tree + schema ...')
    failures = {
        'categories': ['design_invalid: identifiability', 'design_invalid: randomization',
                       'design_invalid: closure', 'design_invalid: leakage',
                       'design_invalid: compute_budget_exceeded', 'design_invalid: rename_edmd',
                       'data_unavailable', 'unreachable_gate', 'precision_insufficient',
                       'no_increment', 'inconclusive'],
        'stop_rules': ['data readiness gate fails -> data_unavailable (current status)',
                       'equal-budget standard method replicates/exceeds -> withdraw main algorithm claim (no_increment/rename_edmd)',
                       'closure/randomization/measurement contract fails -> stop design_invalid',
                       'benefit only in RNA/prediction/operator error without independent functional decision -> withdraw',
                       'feedback/experiment cost above frozen cap -> stop',
                       'CI cannot exclude no utility -> inconclusive',
                       'cross-task failure -> limit to current task; no endpoint switch'],
    }
    schema = {
        'schema': 'R204-M2-stage2-stage3',
        'stage2_fields': ['stage', 'status', 'data_gate', 'dataset_sha256', 'split', 'methods',
                          'per_replicate', 'summary', 'headroom', 'cost_ledger', 'run_shas', 'failure_category'],
        'stage3_fields': ['stage', 'status', 'data_gate', 'selectors', 'legal_experiment_package',
                          'per_round', 'summary', 'cost_ledger', 'run_shas', 'failure_category'],
        'per_method_fields': ['method_id', 'inputs_information', 'hyperparameters', 'n_queries', 'n_feedback',
                              'tuning_configs', 'heldout_utility_mean', 'heldout_regret_mean', 'cluster'],
        'forbidden_fields': ['pharmacology_claim', 'real_decision_claim', 'transfer_claim', 'mechanism_claim',
                             'novelty_claim', 'exploratory_endpoint', 'topk_reported_as_primary',
                             'rna_gain_as_primary'],
        'no_unregistered_endpoints': True,
        'no_effect_results': True,
    }
    write_json(schema, SCHEMA)
    say('    failure tree + schema written')

    say('[7/7] write stage2_plan.json ...')
    out = {
        'task': 'R204-M2-STAGE2-PREP',
        'status': 'design_only_stage2_stage3; data_unavailable; no effect run',
        'chain': {'files': chain, 'mismatches': mismatches, 'pass': chain_pass, 'stage1_pass': stage1_pass},
        'data_readiness_gate': data_gate,
        'stage2_design': stage2,
        'stage3_design': stage3,
        'baselines': stage2['baselines'] + stage3['selectors'],
        'seeds': seeds,
        'power': power,
        'budget': budget,
        'baseline_skeleton': {'unit_tests': checks, 'all_pass': skeleton_checks_pass,
                              'timing_file': 'timing_m2_stage2_prep.json',
                              'no_effect_comparison': True},
        'failure_categories': failures,
        'schema_file': 'stage23_schema.json',
        'frozen_inputs': EXPECTED_CHAIN,
        'boundaries': ['mechanism account only; design preparation only; Stage2/3 not executed',
                       'Stage2 currently data_unavailable (C203/C205); no synthetic/RNA substitution for independent functional decision',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'no modification of old gates/judgments; no revival of stopped experiments; 0 new wells',
                       'Stage2/3 execution requires qualified data + separate prereg + independent challenge + Lead approval'],
        'no_effect_results': True,
        'no_method_comparison_executed': True,
        'log_milestones': ['chain + Stage1 PASS verified', 'data gate evaluated (data_unavailable)',
                           'Stage2/3 design frozen', 'baseline skeleton unit tests/timing',
                           'failure tree + schema written'],
    }
    write_json(out, OUTJSON)
    print('stage2_plan.json sha256:', sha256_file(OUTJSON))
    print('stage23_schema.json sha256:', sha256_file(SCHEMA))
    print('timing_m2_stage2_prep.json sha256:', sha256_file(TIMING))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
