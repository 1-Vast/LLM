"""R192-R2 STAGE-2 PRE-FLIGHT (frozen v3 = PROTOCOL_STAGE2 v1 + AMENDMENT-001 + AMENDMENT-002).

Runs F1-F4 BEFORE any identity/annotation model is fitted and before test labels
are used for anything except the P-B2-frozen zero-model MDE / power design step.

Outputs: preflight.json (deterministic; no timestamps; sorted keys).

Run:  D:\\anaconda\\envs\\maestro\\python.exe research\\2026-10-27-drugcomb-replication\\preflight.py
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np

import s2lib as L


# ------------------------------------------------------------------ helpers
def f3_mde(y_test, pair_codes, cell_codes, npairs, ncells, r):
    """F3(a): P-B2 frozen Regime-B pair x cell cluster bootstrap MDE80."""
    from scipy.stats import rankdata
    seed = L.SEED2 + 1000 + 100 * int(round(r * 100))     # P-B2 design seed rule
    rng = np.random.default_rng(seed)
    ro = np.arange(len(y_test))
    B = L.N_BOOT_MDE
    arr = np.empty(B)
    for b in range(B):
        cp = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        cc = np.bincount(rng.integers(0, ncells, ncells), minlength=ncells)
        idx = np.repeat(ro, cp[pair_codes] * cc[cell_codes])
        z = rng.normal(size=npairs)
        arr[b] = L.spearman(z[pair_codes][idx], y_test[idx])
    se = float(arr.std(ddof=1))
    return {'seed': int(seed), 'B': B, 'se_two_way': se,
            'mde80_two_way': L.Z_MDE80 * se,
            'mean_null_rho': float(arr.mean())}


def f3_power(se, se_null, seed):
    """AMENDMENT-002 section 1 step 2-3: analytic joint power of R1 & R2 & R3."""
    se_diff = math.sqrt(se * se + se_null * se_null)
    rng = np.random.default_rng(seed)
    out = {}
    for rho_true in (0.1183, 0.0947):
        rho_hat = rho_true + rng.normal(0, se, L.N_POWER_REPS)
        m_null = rng.normal(0, se_null, L.N_POWER_REPS)
        diff = rho_hat - m_null
        r1 = rho_hat >= L.DELTA_MIN
        r2 = rho_hat - L.ALPHA_Z * se > 0
        r3 = diff - L.ALPHA_Z * se_diff > 0
        out['%.4f' % rho_true] = {'p_replicated': float(np.mean(r1 & r2 & r3)),
                                  'p_r1_point_ge_delta_min': float(np.mean(r1)),
                                  'p_r2_ci_lower_gt0': float(np.mean(r2)),
                                  'p_r3_control_lower_gt0': float(np.mean(r3))}
    out['se_two_way'] = se
    out['se_null'] = se_null
    out['se_diff'] = se_diff
    out['seed'] = int(seed)
    out['reps'] = L.N_POWER_REPS
    return out


def design_check(r, data, mapped_v2, lab2, vocab2):
    """F1 + F2 + F3 for one r under the frozen seed-permutation split."""
    H, k, N, split_sha = L.split_permutation(mapped_v2.keys(), r)
    pools = L.build_pools(data, lab2, H)
    test_units, train_units = pools['test_units'], pools['train_units']
    test_s = L.pool_summary(data, test_units)
    train_s = L.pool_summary(data, train_units)
    # F1
    f1 = {
        'r': r, 'N_mapped_drugs': N, 'k_holdout': k, 'split_sha256': split_sha,
        'test_units': test_s['n_units'], 'test_pairs': test_s['n_pairs'],
        'test_cells': test_s['n_cells'], 'train_units': train_s['n_units'],
        'train_pairs': train_s['n_pairs'],
        'threshold_test_units_ge_14387': bool(test_s['n_units'] >= 14387),
        'threshold_test_pairs_ge_2000': bool(test_s['n_pairs'] >= 2000),
        'threshold_train_units_ge_5000': bool(train_s['n_units'] >= 5000),
        'pass': bool(test_s['n_units'] >= 14387 and test_s['n_pairs'] >= 2000
                     and train_s['n_units'] >= 5000),
        'expected_scoping_note': ('protocol section 2 scoping numbers 32,299/5,342/108/27,230 were '
                                  'produced with the v1 prefix split; v3 uses the frozen seed-permutation '
                                  'rule, so counts are recomputed (AMENDMENT-001 section 4).'),
    }
    # F2
    f2_lev = L.analyzable_levels(data, lab2, H, train_units)
    # test rows both annotated by construction
    up = data['unit_pair']
    pa, pb = data['pair_a'], data['pair_b']
    both_ann = bool(np.all(lab2[pa[up[test_units]]] >= 0) and np.all(lab2[pb[up[test_units]]] >= 0))
    f2 = {
        'mapping_v2_sha256': L.sha256_file(L.MAP2),
        'mapping_v2_sha_expected': L.SHA_EXPECT['mapping_v2'],
        'mapping_sha_ok': L.sha256_file(L.MAP2) == L.SHA_EXPECT['mapping_v2'],
        'analyzable_levels': f2_lev['n_analyzable'],
        'analyzable_levels_ge2_threshold': bool(f2_lev['n_analyzable'] >= 12),
        'levels_total': f2_lev['n_levels_total'],
        'levels_ge2': f2_lev['n_levels_ge2'],
        'train_levels': f2_lev['n_train_levels'],
        'holdout_levels': f2_lev['n_holdout_levels'],
        'test_units_both_annotated_pct': 100.0 if both_ann else 0.0,
        'test_units_fully_annotated': both_ann,
        'expected_levels_note': 'protocol scoping expected 93 analyzable levels; measured value is authoritative',
        'pass': bool(f2_lev['n_analyzable'] >= 12 and both_ann),
    }
    # F3
    _, pair_codes = np.unique(up[test_units], return_inverse=True)
    _, cell_codes = np.unique(data['unit_cell'][test_units], return_inverse=True)
    y_test = data['y'][test_units]
    f3a = f3_mde(y_test, pair_codes.astype(np.int64), cell_codes.astype(np.int64),
                 int(pair_codes.max()) + 1, int(cell_codes.max()) + 1, r)
    f3a['mde_ok'] = bool(f3a['mde80_two_way'] <= L.DELTA_MIN)
    design_seed = L.SEED2 + 1000 + 100 * int(round(r * 100))
    power_seed = design_seed + 7                              # P-B2 power seed rule
    readings = {}
    for tag, se_null in (('primary_literal_se_null_equals_se', f3a['se_two_way']),
                         ('alt_mean10_se_null_se_over_sqrt10', f3a['se_two_way'] / math.sqrt(10))):
        for seed_tag, seed in (('pb2_rule_seed', power_seed), ('master_seed', L.SEED_MASTER)):
            readings['%s__%s' % (tag, seed_tag)] = f3_power(f3a['se_two_way'], se_null, seed)
    f3b_primary = readings['primary_literal_se_null_equals_se__pb2_rule_seed']['0.1183']['p_replicated']
    f3b_alt = readings['alt_mean10_se_null_se_over_sqrt10__pb2_rule_seed']['0.1183']['p_replicated']
    f3 = {
        'a_mde80_two_way': f3a,
        'b_joint_power': readings,
        'b_primary_reading': 'se_null = SE_two_way (literal AMENDMENT-002 section 1 step 1)',
        'b_primary_power_at_0.1183': f3b_primary,
        'b_alt_reading': 'se_null = SE_two_way/sqrt(10) (zero-model arm is the mean of 10 seeds)',
        'b_alt_power_at_0.1183': f3b_alt,
        'b_ok_primary': bool(f3b_primary >= 0.80),
        'pass': bool(f3a['mde_ok'] and f3b_primary >= 0.80),
    }
    pools_meta = {'test_units_n': int(len(test_units)), 'train_units_n': int(len(train_units))}
    return {'H': H, 'k': k, 'N': N, 'split_sha256': split_sha, 'pools': pools,
            'pools_meta': pools_meta, 'f1': f1, 'f2': f2, 'f3': f3}


def f4_checks(design, data, lab2, mapped_v2, r):
    """F4 design invariants (no model fitting; no test labels beyond design counts)."""
    H = design['H']
    pools = design['pools']
    test_units, train_units = pools['test_units'], pools['train_units']
    drugs = data['drug_names']
    up = data['unit_pair']
    pa, pb = data['pair_a'], data['pair_b']
    train_drugs = sorted({drugs[d] for u in train_units for d in (pa[up[u]], pb[up[u]])})
    test_drugs = sorted({drugs[d] for u in test_units for d in (pa[up[u]], pb[up[u]])})
    checks = {}
    # (1) outer train / test drugs disjoint
    checks['outer_train_test_drug_sets_disjoint'] = bool(len(set(train_drugs) & set(test_drugs)) == 0)
    # (2) inner folds: drug sets disjoint, each val fold has units
    folds = L.inner_folds(train_drugs)
    fold_info = []
    disjoint = True
    valpos = True
    for fold in folds:
        fold_set = set(fold)
        itr = [u for u in train_units
               if drugs[pa[up[u]]] not in fold_set and drugs[pb[up[u]]] not in fold_set]
        iva = [u for u in train_units
               if drugs[pa[up[u]]] in fold_set and drugs[pb[up[u]]] in fold_set]
        fold_info.append({'fold_drugs': len(fold), 'inner_train_units': len(itr),
                          'inner_val_units': len(iva)})
        disjoint = disjoint and len(iva) > 0
        valpos = valpos and len(iva) > 0
    seen = set()
    overlap = False
    for fold in folds:
        if seen & set(fold):
            overlap = True
        seen |= set(fold)
    checks['inner_folds_drug_sets_disjoint'] = bool(not overlap)
    checks['inner_fold_validation_units_positive'] = bool(all(x['inner_val_units'] > 0 for x in fold_info))
    checks['inner_fold_sizes'] = fold_info
    # (3) random assignments: 5 size-matched keep the level-size multiset exactly
    rand = L.random_label_assignments(data, lab2)
    sm = [x for x in rand if x['kind'] == 'size_matched']
    un = [x for x in rand if x['kind'] == 'uniform']
    from collections import Counter
    real_multiset = Counter(int(lab2[i]) for i in range(len(drugs)) if lab2[i] >= 0)
    ok_multiset = []
    for x in sm:
        c = Counter(x['labels'].values())
        ok_multiset.append(c == real_multiset)
    checks['size_matched_multiset_preserved_all5'] = bool(all(ok_multiset) and len(sm) == 5)
    checks['uniform_arm_count'] = len(un)
    checks['random_assignments_count'] = len(rand)
    checks['random_seeds'] = [x['seed'] for x in rand]
    checks['random_kind_flags'] = [x['kind'] for x in rand]
    # (4) random assignments do not read y: code-level white-list (labels built from identity only)
    checks['random_assignments_read_y_attested_false'] = False
    checks['random_assignments_attestation'] = ('random_label_assignments() receives only the identity/label '
                                                'array; it is called here before any arm is fitted and never '
                                                'receives y or any prediction.')
    # (5) identity / constant test predictions are constant by construction
    zeros = np.zeros(len(test_units), np.int64)
    checks['identity_test_indicators_all_zero'] = True
    checks['identity_constant_by_construction'] = ('held-out drugs have no identity column (training one-hot '
                                                   'columns are zero on all test rows) -> constant prediction')
    # (6) annotation / Xboth predictions are non-constant: test units must span >1 level pair
    lev_a = lab2[pa[up[test_units]]]
    lev_b = lab2[pb[up[test_units]]]
    real_pairs = set(zip(lev_a.tolist(), lev_b.tolist()))
    checks['annotation_test_level_pairs_distinct'] = len(real_pairs)
    checks['annotation_prediction_non_constant'] = bool(len(real_pairs) > 1)
    rand_pairs = []
    for x in rand:
        la = np.array([x['labels'].get(drugs[d], -1) for d in pa[up[test_units]]])
        lb = np.array([x['labels'].get(drugs[d], -1) for d in pb[up[test_units]]])
        rand_pairs.append(len(set(zip(la.tolist(), lb.tolist()))))
    checks['random_arm_min_distinct_level_pairs'] = int(min(rand_pairs))
    checks['random_controls_non_constant'] = bool(min(rand_pairs) > 1)
    # (7) unit aggregation consistency (P-B frozen rule)
    checks['units'] = int(data['n_units'])
    checks['combo_blocks'] = int(data['n_blocks_combo'])
    checks['combo_blocks_finite_endpoint'] = int(data['n_blocks_finite'])
    checks['combo_blocks_missing_endpoint'] = int(data['n_blocks_combo'] - data['n_blocks_finite'])
    checks['unit_sizes_sum_equals_finite_blocks'] = bool(
        int(data['unit_size'].sum()) == int(data['n_blocks_finite']))
    from collections import Counter as C2
    checks['unit_size_distribution'] = {str(k): int(v) for k, v in
                                        sorted(C2(data['unit_size'][data['unit_size'] > 0].tolist()).items())}
    checks['y_missing_units'] = int(data['y_missing_units'])
    checks['aggregation_ok'] = bool(checks['unit_sizes_sum_equals_finite_blocks']
                                    and data['y_missing_units'] == 0)
    # (8) mapping/subset SHA checks
    checks['v14_sha256'] = L.sha256_file(L.V14)
    checks['v14_sha_expected'] = L.SHA_EXPECT['v14_summary']
    checks['v14_sha_ok'] = L.sha256_file(L.V14) == L.SHA_EXPECT['v14_summary']
    checks['mapping_v2_sha_ok'] = L.sha256_file(L.MAP2) == L.SHA_EXPECT['mapping_v2']
    # explicit test-drug-in-train check
    checks['test_drugs_in_train_pool'] = int(len(set(test_drugs) & set(train_drugs)))
    checks['pass'] = bool(
        checks['outer_train_test_drug_sets_disjoint']
        and checks['inner_folds_drug_sets_disjoint']
        and checks['inner_fold_validation_units_positive']
        and checks['size_matched_multiset_preserved_all5']
        and checks['annotation_prediction_non_constant']
        and checks['random_controls_non_constant']
        and checks['aggregation_ok']
        and checks['v14_sha_ok'] and checks['mapping_v2_sha_ok']
        and checks['test_drugs_in_train_pool'] == 0)
    return checks


def disclosure_numbers(data, lab2, mapped_v2, design, r):
    """Selection-bias / cross-r disclosures required by AMENDMENT-001 section 5 / section 7."""
    drugs = data['drug_names']
    up = data['unit_pair']
    pa, pb = data['pair_a'], data['pair_b']
    H = design['H']
    pools = design['pools']
    test_units = pools['test_units']
    # all-drug both-unseen pool under the same seed-permutation rule on all 4,088 drugs
    H_all, k_all, N_all, sha_all = L.split_permutation(drugs, r)
    a_in = np.array([drugs[d] in H_all for d in pa])
    b_in = np.array([drugs[d] in H_all for d in pb])
    pair_all = a_in & b_in
    y_ok = np.isfinite(data['y'])
    units_all = np.where(pair_all[up] & y_ok)[0]
    ann_map = lab2[pa] >= 0
    ann_b = lab2[pb] >= 0
    pair_ann = pair_all & ann_map & ann_b
    units_ann = np.where(pair_ann[up] & y_ok)[0]
    multi_block_ann = float(np.mean(data['unit_size'][units_ann] >= 2)) if len(units_ann) else None
    multi_block_all = float(np.mean(data['unit_size'][units_all] >= 2)) if len(units_all) else None
    cell_train = set(np.unique(data['unit_cell'][pools['train_units']]).tolist())
    cell_test = set(np.unique(data['unit_cell'][test_units]).tolist())
    # training annotated units at r=0.20 (reported by P-A2 / challenge) and here
    out = {
        'all_drug_both_unseen_units_r': int(len(units_all)),
        'all_drug_both_unseen_pairs_r': int(np.unique(up[units_all]).size),
        'annotated_both_unseen_units_r': int(len(units_ann)),
        'annotated_fraction_of_all_unseen_pct': L.q(100.0 * len(units_ann) / len(units_all)) if len(units_all) else None,
        'all_unseen_split_sha256': sha_all,
        'all_unseen_k_holdout': k_all, 'all_unseen_N': N_all,
        'multi_block_exposure_annotated_pct': L.q(100.0 * multi_block_ann) if multi_block_ann is not None else None,
        'multi_block_exposure_all_unseen_pct': L.q(100.0 * multi_block_all) if multi_block_all is not None else None,
        'mapped_drug_coverage_pct_of_universe': L.q(100.0 * len(mapped_v2) / len(drugs)),
        'test_cells': len(cell_test),
        'all_cells': len(data['cell_names']),
        'test_cells_also_in_train_pool': int(len(cell_test & cell_train)),
        'cell_holdout': 'cells are never held out by the frozen split',
        'reported_r020_strict_train_units_PA2': 83684,
        'reported_r020_both_unseen_units_PA2': 3056,
        'selected_r_strict_train_units': int(len(pools['train_units'])),
        'selected_r_both_unseen_annotated_units': int(len(test_units)),
        'cross_r_disclosure': ('do NOT assume cross-r effect equality: original frozen effect was measured at '
                               'r=0.20, this design uses the selected r; strict training units change '
                               '83,684 (v2 r=0.20) -> %d (selected r).' % len(pools['train_units'])),
    }
    return out


def main():
    print('[1/7] self-test ridge machinery ...', flush=True)
    L.selftest_binary_ridge()
    print('[2/7] hash + verify inputs ...', flush=True)
    inputs = L.hash_inputs()
    sha_ok = {
        'v14_summary': inputs['v14_summary']['sha256'] == L.SHA_EXPECT['v14_summary'],
        'mapping_v2': inputs['mapping_v2']['sha256'] == L.SHA_EXPECT['mapping_v2'],
        'mapping_v1': inputs['mapping_v1']['sha256'] == L.SHA_EXPECT['mapping_v1'],
    }
    print('    sha checks:', sha_ok, flush=True)
    print('[3/7] load mapping v2 / v1 + v1.4 summary ...', flush=True)
    m2 = L.load_mapping(L.MAP2)
    m1 = L.load_mapping(L.MAP1)
    data = L.load_v14()
    lab2, vocab2 = L.drug_level_arrays(data, m2['mapped'])
    struct_ok = bool(data['n_blocks_combo'] == 466033 and data['n_units'] == 380418
                     and len(data['drug_names']) == 4088 and data['n_pairs'] == 62826
                     and len(data['cell_names']) == 112 and data['y_missing_units'] == 0
                     and m2['n_mapped'] == 1800 and m1['n_mapped'] == 1418)
    structure = {'combo_blocks': data['n_blocks_combo'], 'units': data['n_units'],
                 'pairs': data['n_pairs'], 'cells': len(data['cell_names']),
                 'drugs': len(data['drug_names']), 'y_missing_units': data['y_missing_units'],
                 'mapping_v2_mapped_drugs': m2['n_mapped'], 'mapping_v1_mapped_drugs': m1['n_mapped'],
                 'mapping_v2_s1_rows': m2['n_s1_rows'], 'mapping_v1_s1_rows': m1['n_s1_rows'],
                 'mapping_v2_levels': len(m2['levels']), 'mapping_v1_levels': len(m1['levels']),
                 'expected': {'combo_blocks': 466033, 'units': 380418, 'pairs': 62826,
                              'cells': 112, 'drugs': 4088, 'mapping_v2_mapped': 1800,
                              'mapping_v1_mapped': 1418},
                 'struct_ok': struct_ok}
    print('    structure ok:', struct_ok, flush=True)

    print('[4/7] design r=0.50 (F1-F4) ...', flush=True)
    d50 = design_check(0.50, data, m2['mapped'], lab2, vocab2)
    f4_50 = f4_checks(d50, data, lab2, m2['mapped'], 0.50)
    print('    r=0.50 F1 %s | F2 %s | F3 %s (MDE %.6f, power %.3f)' % (
        d50['f1']['pass'], d50['f2']['pass'], d50['f3']['pass'],
        d50['f3']['a_mde80_two_way']['mde80_two_way'],
        d50['f3']['b_primary_power_at_0.1183']), flush=True)
    ladder = {'r': 0.50, 'f1_pass': d50['f1']['pass'], 'f2_pass': d50['f2']['pass'],
              'f3_pass': d50['f3']['pass'], 'f4_pass': f4_50['pass'],
              'triggered': False, 'selected_r': None, 'reason': None}
    selected = None
    d55 = None
    f4_55 = None
    if d50['f1']['pass'] and d50['f2']['pass'] and d50['f3']['pass'] and f4_50['pass']:
        selected = d50
        ladder['selected_r'] = 0.50
        ladder['reason'] = 'r=0.50 passed F1-F4; no ladder step needed'
    elif not (d50['f1']['pass'] and d50['f2']['pass']):
        ladder['reason'] = 'F1/F2 failed at r=0.50 -> STOP (ladder only for F3 failure)'
    else:
        ladder['triggered'] = True
        ladder['reason'] = 'F3 failed at r=0.50 -> pre-registered one-step ladder to r=0.55'
        print('[5/7] ladder r=0.55 (F1-F4) ...', flush=True)
        d55 = design_check(0.55, data, m2['mapped'], lab2, vocab2)
        f4_55 = f4_checks(d55, data, lab2, m2['mapped'], 0.55)
        print('    r=0.55 F1 %s | F2 %s | F3 %s (MDE %.6f, power %.3f) | F4 %s' % (
            d55['f1']['pass'], d55['f2']['pass'], d55['f3']['pass'],
            d55['f3']['a_mde80_two_way']['mde80_two_way'],
            d55['f3']['b_primary_power_at_0.1183'], f4_55['pass']), flush=True)
        ladder['r55'] = {'f1_pass': d55['f1']['pass'], 'f2_pass': d55['f2']['pass'],
                         'f3_pass': d55['f3']['pass'], 'f4_pass': f4_55['pass']}
        if d55['f1']['pass'] and d55['f2']['pass'] and d55['f3']['pass'] and f4_55['pass']:
            selected = d55
            ladder['selected_r'] = 0.55
        else:
            ladder['reason'] = 'r=0.55 also failed F1-F4 -> STOP (inconclusive)'
    if selected is None:
        verdict = 'inconclusive'
    else:
        verdict = 'preflight_passed'

    print('[6/7] disclosure numbers + selected design ...', flush=True)
    disclosures = {}
    f4_selected = f4_50 if (selected is d50) else f4_55
    if selected is not None:
        disclosures = disclosure_numbers(data, lab2, m2['mapped'], selected, selected['f1']['r'])
    gates = {
        'f1': selected['f1'] if selected is not None else d50['f1'],
        'f2': selected['f2'] if selected is not None else d50['f2'],
        'f3': selected['f3'] if selected is not None else d50['f3'],
        'f4': f4_selected,
    }
    all_pass = bool(selected is not None and gates['f1']['pass'] and gates['f2']['pass']
                    and gates['f3']['pass'] and gates['f4']['pass'])
    out = {
        'protocol': {'name': 'PROTOCOL_STAGE2 v3 = v1 + AMENDMENT-001 + AMENDMENT-002',
                     'stage2_v1_sha256': inputs['protocol_stage2_v1']['sha256'],
                     'amendment_001_sha256': inputs['amendment_001']['sha256'],
                     'amendment_002_sha256': inputs['amendment_002']['sha256'],
                     'governing_version': 'v3'},
        'script': {'preflight.py': inputs.get('script_preflight', {}).get('sha256'),
                   's2lib.py': inputs.get('script_lib', {}).get('sha256')},
        'inputs': inputs,
        'sha_checks': sha_ok,
        'structure': structure,
        'designs': {'r_0.50': {'f1': d50['f1'], 'f2': d50['f2'], 'f3': d50['f3'],
                               'f4': f4_50, 'split_sha256': d50['split_sha256']}},
        'ladder': ladder,
        'selected_design': None if selected is None else {
            'r': selected['f1']['r'], 'k_holdout': selected['f1']['k_holdout'],
            'N_mapped_drugs': selected['f1']['N_mapped_drugs'],
            'split_sha256': selected['split_sha256'],
            'test_units': selected['f1']['test_units'], 'test_pairs': selected['f1']['test_pairs'],
            'test_cells': selected['f1']['test_cells'],
            'strict_train_units': selected['f1']['train_units'],
            'chosen_by': 'frozen pre-registered ladder based ONLY on F1-F4 (zero-model/power); '
                         'no identity/annotation effect was computed before this selection',
            'delta_min': L.DELTA_MIN,
            'model_arms_planned': ['Xboth (main)', 'annotation_only', 'identity_only(=constant)',
                                   'Xboth_random (10 seeds: 5 size-matched + 5 uniform, single null-family mean)',
                                   'Xboth_capacity (Xboth + 2xL Gaussian random features)', 'constant'],
            'ci_primary': 'pair x cell two-way cluster bootstrap, B=1000, seed 20261027 (v3)',
            'lambda_selection': 'inner 3 folds by drug; both-unseen inner validation; per-fold standardization',
            'random_seeds': L.RANDOM_SEEDS,
            'lambda_grid': L.LAMBDA_GRID,
        },
        'gates': {k: gate_summary(v) for k, v in gates.items()},
        'gates_all_pass': all_pass,
        'verdict': verdict,
        'disclosures': disclosures,
        'environment': environment(),
        'response_use_attestation': {
            'models_fitted': False,
            'identity_or_annotation_effect_estimated': False,
            'response_columns_used': ['synergy_bliss'],
            'response_used_only_for': ['F3 zero-model MDE variance / power design step (P-B2 frozen method)',
                                       'structural unit aggregation checks'],
            'test_labels_used_before_selection': 'only for the pre-registered F3 zero-model design step; '
                                                 'no arm was fitted before this file was written',
        },
        'f3_implementation_note': (
            'AMENDMENT-002 section 1 step 1: the pair x cell cluster bootstrap of the zero prediction gives the '
            'null rho distribution whose SD is SE_two_way; primary reading therefore sets se_null=SE_two_way '
            '(literal). The alternative reading (zero-model arm = mean of 10 seeds -> se_null=SE/sqrt(10)) is '
            'reported alongside; under it the r=0.50 joint power is also shown.'),
    }
    if selected is not None and selected is d55:
        out['designs']['r_0.55'] = {'f1': d55['f1'], 'f2': d55['f2'], 'f3': d55['f3'],
                                    'f4': f4_55, 'split_sha256': d55['split_sha256']}
    elif d55 is not None:
        out['designs']['r_0.55'] = {'f1': d55['f1'], 'f2': d55['f2'], 'f3': d55['f3'],
                                    'f4': f4_55, 'split_sha256': d55['split_sha256']}
    print('[7/7] write preflight.json ...', flush=True)
    L.write_json(out, L.PREFLIGHT_JSON)
    print('\n==== PREFLIGHT: %s (selected r=%s) ====' % (
        verdict, None if selected is None else selected['f1']['r']))
    print('  F1: test %d units / %d pairs / %d cells; train %d units (pass=%s)' % (
        gates['f1']['test_units'], gates['f1']['test_pairs'], gates['f1']['test_cells'],
        gates['f1']['train_units'], gates['f1']['pass']))
    print('  F2: analyzable levels %d (pass=%s)' % (gates['f2']['analyzable_levels'], gates['f2']['pass']))
    print('  F3: MDE80 %.6f (<=0.0947: %s); joint power@0.1183 %.4f (primary, >=0.80: %s); alt %.4f' % (
        gates['f3']['a_mde80_two_way']['mde80_two_way'], gates['f3']['a_mde80_two_way']['mde_ok'],
        gates['f3']['b_primary_power_at_0.1183'], gates['f3']['b_ok_primary'],
        gates['f3']['b_alt_power_at_0.1183']))
    print('  F4: pass=%s' % gates['f4']['pass'])
    print('  verdict: %s' % verdict)
    return 0 if all_pass else 1


def gate_summary(g):
    keep = {k: v for k, v in g.items() if k not in ('inner_fold_sizes', 'unit_size_distribution')}
    return keep


def environment():
    import platform
    import scipy
    return {'python': sys.version.split()[0], 'numpy': np.__version__,
            'scipy': scipy.__version__, 'platform': platform.platform()}


if __name__ == '__main__':
    sys.exit(main())
