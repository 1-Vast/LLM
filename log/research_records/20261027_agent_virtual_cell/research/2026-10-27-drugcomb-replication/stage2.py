"""R192-R2 STAGE-2 effect run (frozen v3 = PROTOCOL_STAGE2 v1 + AMENDMENT-001 + AMENDMENT-002).

Pre-requisite: preflight.py has been run and preflight.json gates_all_pass == true
(runtime assertion below).  Main design r is the one selected in preflight.json by
the pre-registered ladder; it is never changed here.

Arms: Xboth (main), annotation_only, identity_only (=constant), Xboth_random
(10 fixed seeds: 5 size-matched + 5 uniform, single null-family mean),
Xboth_capacity, constant.  Judgment uses R1/R2/R3 with the P-B2 Regime-B
**pair x cell** two-way cluster bootstrap (B=1000, seed 20261027).

Outputs: stage2.json, rows.csv (deterministic; no timestamps; sorted JSON keys).

Run:  D:\\anaconda\\envs\\maestro\\python.exe research\\2026-10-27-drugcomb-replication\\stage2.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys

import numpy as np

import s2lib as L


# ------------------------------------------------------------------ helpers
def fail(msg):
    print('STAGE2 ABORT: ' + msg, flush=True)
    L.write_json({'verdict': 'inconclusive', 'abort_reason': msg,
                  'protocol': 'PROTOCOL_STAGE2 v3'},
                 L.STAGE2_JSON)
    return 2


def load_preflight():
    if not os.path.exists(L.PREFLIGHT_JSON):
        raise SystemExit('preflight.json missing: run preflight.py first')
    with open(L.PREFLIGHT_JSON, encoding='utf-8') as fh:
        pf = json.load(fh)
    if not pf.get('gates_all_pass'):
        raise SystemExit('preflight gates did not pass; stage-2 must not run (verdict=%s)'
                         % pf.get('verdict'))
    if not pf.get('selected_design'):
        raise SystemExit('preflight selected_design missing')
    return pf


def verify_against_preflight(pf):
    inp = pf['inputs']
    checks = {
        'v14_summary_sha_ok': L.sha256_file(L.V14) == inp['v14_summary']['sha256'],
        'mapping_v2_sha_ok': L.sha256_file(L.MAP2) == inp['mapping_v2']['sha256'],
        'mapping_v1_sha_ok': L.sha256_file(L.MAP1) == inp['mapping_v1']['sha256'],
        'preflight_sha_ok': L.sha256_file(L.PREFLIGHT_JSON) is not None,
    }
    if not all(checks.values()):
        raise SystemExit('stage2 input hash mismatch vs preflight: %s' % checks)
    return checks


def labels_to_lab(data, labels):
    """labels: drug name -> label id (int) or label string; returns global label array."""
    vals = list(labels.values())
    if vals and not all(isinstance(v, (int, np.integer)) for v in vals):
        vocab = sorted(set(vals))
        vidx = {v: i for i, v in enumerate(vocab)}
        labels = {k: vidx[v] for k, v in labels.items()}
    lab = np.full(len(data['drug_names']), -1, np.int64)
    for i, d in enumerate(data['drug_names']):
        v = labels.get(d)
        if v is not None:
            lab[i] = int(v)
    return lab


def design_arrays(data, mapped, r):
    H, k, N, sha = L.split_permutation(mapped.keys(), r)
    return H, k, N, sha


def fit_design(data, mapped_labels, r, H=None, include_random=False):
    """Fit the pre-registered pipeline on one design (used for main + sensitivities)."""
    vals = list(mapped_labels.values())
    if vals and not all(isinstance(v, (int, np.integer)) for v in vals):
        vocab = sorted(set(vals))
        vidx = {v: i for i, v in enumerate(vocab)}
        mapped_labels = {k: vidx[v] for k, v in mapped_labels.items()}
    if H is None:
        H, k, N, sha = design_arrays(data, mapped_labels, r)
    else:
        k = int(round(r * len(mapped_labels)))
        N = len(mapped_labels)
        sha = L.sha256_text('\n'.join(sorted(H)))
    lab = labels_to_lab(data, mapped_labels)
    pools = L.build_pools(data, lab, H)
    test_units, train_units = pools['test_units'], pools['train_units']
    out = {'r': r, 'k_holdout': k, 'N_mapped_drugs': N, 'split_sha256': sha,
           'test': L.pool_summary(data, test_units),
           'train': L.pool_summary(data, train_units),
           'test_units': test_units, 'train_units': train_units, 'lab': lab}
    if len(test_units) < 100 or len(train_units) < 1000:
        out['error'] = 'pool too small for a sensitivity fit'
        return out
    y = data['y'][test_units]
    xb = L.fit_arm(train_units, test_units, data, mapped_labels, include_identity=True)
    out['xboth'] = {'rho': L.spearman(xb['pred'], y), 'lambda': xb['lambda'],
                    'fold_mean': xb['fold_mean'], 'D': xb['D'], 'L': xb['L'],
                    'pred': xb['pred']}
    _, pair_codes = np.unique(data['unit_pair'][test_units], return_inverse=True)
    _, cell_codes = np.unique(data['unit_cell'][test_units], return_inverse=True)
    npairs, ncells = int(pair_codes.max()) + 1, int(cell_codes.max()) + 1
    out['pair_codes'] = pair_codes.astype(np.int64)
    out['cell_codes'] = cell_codes.astype(np.int64)
    if include_random:
        ranks = []
        preds = {'xboth': xb['pred']}
        for i, a in enumerate(L.random_label_assignments(data, lab)):
            rr = L.fit_arm(train_units, test_units, data, a['labels'], include_identity=True)
            preds['rand_%02d' % i] = rr['pred']
            ranks.append(L.spearman(rr['pred'], y))
        out['random_rhos'] = ranks
        out['random_mean_rho'] = float(np.mean(ranks))
        boot = L.bootstrap_rho_pair_cell(y, preds, out['pair_codes'], out['cell_codes'],
                                         npairs, ncells, B=L.N_BOOT_CI, seed=L.SEED_MASTER)
        rand_mean_boot = np.mean([boot['rand_%02d' % i] for i in range(L.N_RANDOM)], axis=0)
        out['boot'] = boot
        out['rand_mean_boot'] = rand_mean_boot
        out['xboth_ci'] = L.boot_ci(boot['xboth'])
        out['rand_mean_ci'] = L.boot_ci(rand_mean_boot)
        out['diff_ci'] = L.boot_ci(boot['xboth'] - rand_mean_boot)
        out['diff_point'] = float(out['xboth']['rho'] - out['random_mean_rho'])
        # drug-cluster sensitivity
        a_idx = data['pair_a'][data['unit_pair'][test_units]]
        b_idx = data['pair_b'][data['unit_pair'][test_units]]
        bootd = L.bootstrap_rho_drugs(y, preds, a_idx, b_idx, len(data['drug_names']),
                                      B=L.N_BOOT_CI, seed=L.SEED_MASTER)
        rand_mean_bootd = np.mean([bootd['rand_%02d' % i] for i in range(L.N_RANDOM)], axis=0)
        out['drug_cluster'] = {'xboth_ci': L.boot_ci(bootd['xboth']),
                               'diff_ci': L.boot_ci(bootd['xboth'] - rand_mean_bootd)}
    else:
        boot = L.bootstrap_rho_pair_cell(y, {'xboth': xb['pred']}, out['pair_codes'],
                                         out['cell_codes'], npairs, ncells,
                                         B=L.N_BOOT_CI, seed=L.SEED_MASTER)
        out['boot'] = boot
        out['xboth_ci'] = L.boot_ci(boot['xboth'])
    out['pred'] = out['xboth']['pred']
    out['y'] = y
    return out


def partial_spearman(y, pred, group):
    """Partial Spearman controlling a categorical group (rank residualization)."""
    from scipy.stats import rankdata
    rp = rankdata(pred)
    ry = rankdata(y)
    g = np.asarray(group, np.int64)
    cnt = np.bincount(g)
    mp = np.bincount(g, weights=rp) / cnt
    my = np.bincount(g, weights=ry) / cnt
    a = rp - mp[g]
    b = ry - my[g]
    den = math.sqrt(float(a @ a) * float(b @ b))
    return float('nan') if den == 0 else float(a @ b / den)


def partial_spearman_boot(y, pred, group, pair_codes, cell_codes, npairs, ncells,
                          B=L.N_BOOT_CI, seed=L.SEED_MASTER):
    from scipy.stats import rankdata
    rng = np.random.default_rng(seed)
    ro = np.arange(len(y))
    arr = np.empty(B)
    for b in range(B):
        cp = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        cc = np.bincount(rng.integers(0, ncells, ncells), minlength=ncells)
        idx = np.repeat(ro, cp[pair_codes] * cc[cell_codes])
        rp = rankdata(pred[idx]); ry = rankdata(y[idx])
        g = group[idx]
        cnt = np.bincount(g)
        a = rp - (np.bincount(g, weights=rp) / cnt)[g]
        bb = ry - (np.bincount(g, weights=ry) / cnt)[g]
        den = math.sqrt(float(a @ a) * float(bb @ bb))
        arr[b] = float(a @ bb / den) if den > 0 else float('nan')
    return arr


def cramers_v(row_group, col_group, nrow, ncol):
    table = np.zeros((nrow, ncol), float)
    np.add.at(table, (row_group, col_group), 1.0)
    n = table.sum()
    if n == 0:
        return None
    exp = table.sum(1, keepdims=True) * table.sum(0, keepdims=True) / n
    mask = exp > 0
    chi2 = float((((table - exp) ** 2)[mask] / exp[mask]).sum())
    denom = n * (min(nrow - 1, ncol - 1))
    return math.sqrt(chi2 / denom) if denom > 0 else None


def jaaks_overlap(data):
    """Normalized text-name overlap with the Jaaks training resource (entity + key level)."""
    import pandas as pd
    cells, drugs = set(), set()
    jaaks_keys = set()
    for path in (L.JAAKS_ORIG, L.JAAKS_VAL):
        df = pd.read_csv(path, usecols=['CELL_LINE_NAME', 'ANCHOR_NAME', 'LIBRARY_NAME'])
        for cl, a, b in zip(df['CELL_LINE_NAME'], df['ANCHOR_NAME'], df['LIBRARY_NAME']):
            if not (isinstance(cl, str) and isinstance(a, str) and isinstance(b, str)):
                continue
            ncl, na, nb = L.norm(cl), L.norm(a), L.norm(b)
            if not (ncl and na and nb):
                continue
            cells.add(ncl)
            drugs.add(na); drugs.add(nb)
            pair = (na, nb) if na <= nb else (nb, na)
            jaaks_keys.add(ncl + '\x1f' + pair[0] + '\x1f' + pair[1])
    drugs_all = data['drug_names']
    cells_all = data['cell_names']
    up = data['unit_pair']
    pa, pb = data['pair_a'], data['pair_b']
    jcells = cells & set(cells_all)
    jdrugs = drugs & set(drugs_all)
    data_keys = set()
    for u in range(data['n_units']):
        cl = cells_all[data['unit_cell'][u]]
        a = drugs_all[pa[up[u]]]
        b = drugs_all[pb[up[u]]]
        pair = (a, b) if a <= b else (b, a)
        data_keys.add(cl + '\x1f' + pair[0] + '\x1f' + pair[1])
    return {'overlap_cells': sorted(jcells), 'overlap_drugs': sorted(jdrugs),
            'n_overlap_cells': len(jcells), 'n_overlap_drugs': len(jdrugs),
            'n_overlap_keys': len(jaaks_keys & data_keys),
            'jaaks_cells_norm': len(cells), 'jaaks_drugs_norm': len(drugs)}


# ------------------------------------------------------------------ main
def main():
    print('[1/6] load + verify preflight ...', flush=True)
    pf = load_preflight()
    hashes = verify_against_preflight(pf)
    sd = pf['selected_design']
    r_main = float(sd['r'])
    print('    selected r=%.2f split %s ...' % (r_main, sd['split_sha256'][:12]), flush=True)

    print('[2/6] load data / mapping ...', flush=True)
    m2 = L.load_mapping(L.MAP2)
    m1 = L.load_mapping(L.MAP1)
    data = L.load_v14()
    lab2, vocab2 = L.drug_level_arrays(data, m2['mapped'])
    labels_real = L.label_dict_from_array(data, lab2)
    H, k, N, sha = design_arrays(data, m2['mapped'], r_main)
    if sha != sd['split_sha256']:
        return fail('split hash mismatch vs preflight')
    pools = L.build_pools(data, lab2, H)
    test_units, train_units = pools['test_units'], pools['train_units']
    if (len(test_units) != sd['test_units'] or len(train_units) != sd['strict_train_units']):
        return fail('pool counts mismatch vs preflight')
    y_test = data['y'][test_units]
    _, pair_codes = np.unique(data['unit_pair'][test_units], return_inverse=True)
    _, cell_codes = np.unique(data['unit_cell'][test_units], return_inverse=True)
    npairs, ncells = int(pair_codes.max()) + 1, int(cell_codes.max()) + 1
    pair_codes = pair_codes.astype(np.int64)
    cell_codes = cell_codes.astype(np.int64)
    structure = {'test': L.pool_summary(data, test_units),
                 'train': L.pool_summary(data, train_units)}

    print('[3/6] main design arms (Xboth, annotation_only, random x10, capacity, proxy) ...', flush=True)
    arms = {}
    xboth = L.fit_arm(train_units, test_units, data, labels_real, include_identity=True)
    arms['xboth'] = xboth
    print('    Xboth fitted (lambda=%s, inner-folds=%s)' % (xboth['lambda'], xboth['fold_mean']), flush=True)
    ann = L.fit_arm(train_units, test_units, data, labels_real, include_identity=False)
    arms['annotation_only'] = ann
    const = float(np.mean(data['y'][train_units]))
    arms['identity_only'] = {'pred': np.full(len(test_units), const), 'lambda': None,
                             'fold_mean': {}, 'constant_value': const}
    arms['constant'] = {'pred': np.full(len(test_units), const), 'lambda': None,
                        'fold_mean': {}, 'constant_value': const}
    rand_assign = L.random_label_assignments(data, lab2)
    random_preds = []
    random_meta = []
    for i, a in enumerate(rand_assign):
        rr = L.fit_arm(train_units, test_units, data, a['labels'], include_identity=True)
        arms['xboth_random_%02d' % i] = rr
        random_preds.append(rr['pred'])
        random_meta.append({'index': i, 'kind': a['kind'], 'seed': a['seed'],
                            'multiset_preserved': a['multiset_preserved'],
                            'lambda': rr['lambda']})
    L_train = len(xboth['train_levels'])
    R_cap = 2 * L_train
    C, pos = L.random_feature_matrix(np.concatenate([train_units, test_units]), R_cap, L.CAPACITY_SEED)
    extra_train = C[[pos[int(u)] for u in train_units]]
    extra_test = C[[pos[int(u)] for u in test_units]]
    cap = L.fit_arm(train_units, test_units, data, labels_real,
                    include_identity=True, extra_train=extra_train, extra_test=extra_test)
    arms['xboth_capacity'] = cap
    # proxy one-hot diagnostic arm (Xboth + block_id-20bin proxy one-hot); NOT part of judgment
    bins = data['unit_bin']
    nbin = L.PROXY_BINS
    def proxy_mat(units):
        M = np.zeros((len(units), nbin))
        M[np.arange(len(units)), bins[units]] = 1.0
        return M
    proxy = L.fit_arm(train_units, test_units, data, labels_real, include_identity=True,
                      extra_train=proxy_mat(train_units), extra_test=proxy_mat(test_units))
    arms['xboth_plus_proxy_diagnostic'] = proxy

    print('[4/6] main metrics + cluster bootstraps ...', flush=True)
    rho = {name: L.spearman(a['pred'], y_test) for name, a in arms.items()}
    auc = {name: L.top_quartile_auc(a['pred'], y_test) for name, a in arms.items()}
    top100 = {name: L.topk_hits(a['pred'], y_test, 100) for name, a in arms.items()}
    y_rand = float(np.std(y_test))
    rand_rho_mean = float(np.mean([rho['xboth_random_%02d' % i] for i in range(L.N_RANDOM)]))
    rand_rho_sd = float(np.std([rho['xboth_random_%02d' % i] for i in range(L.N_RANDOM)], ddof=1))
    preds = {name: np.asarray(a['pred'], float) for name, a in arms.items()
             if name not in ('identity_only', 'constant')}
    boot = L.bootstrap_rho_pair_cell(y_test, preds, pair_codes, cell_codes, npairs, ncells,
                                     B=L.N_BOOT_CI, seed=L.SEED_MASTER)
    rand_mean_boot = np.mean([boot['xboth_random_%02d' % i] for i in range(L.N_RANDOM)], axis=0)
    diff_boot = boot['xboth'] - rand_mean_boot
    ann_minus_rand_boot = boot['annotation_only'] - rand_mean_boot
    main = {
        'rho': {k: L.q(v) for k, v in rho.items()},
        'top_quartile_auc': {k: L.q(v) for k, v in auc.items()},
        'top100_hit': {k: L.q(v) for k, v in top100.items()},
        'lambda': {k: arms[k].get('lambda') for k in arms},
        'inner_fold_mean_rho': {k: arms[k].get('fold_mean') for k in arms},
        'random_arms_meta': random_meta,
        'random_mean_rho': L.q(rand_rho_mean), 'random_rho_sd': L.q(rand_rho_sd),
        'xboth_ci_pair_cell': L.boot_ci(boot['xboth']),
        'annotation_only_ci_pair_cell': L.boot_ci(boot['annotation_only']),
        'random_mean_ci_pair_cell': L.boot_ci(rand_mean_boot),
        'diff_vs_random_ci_pair_cell': L.boot_ci(diff_boot),
        'diff_vs_random_point': L.q(rho['xboth'] - rand_rho_mean),
        'annotation_minus_random_ci_pair_cell': L.boot_ci(ann_minus_rand_boot),
        'capacity_ci_pair_cell': L.boot_ci(boot['xboth_capacity']),
        'proxy_diagnostic_ci_pair_cell': L.boot_ci(boot['xboth_plus_proxy_diagnostic']),
        'n_test_units': int(len(test_units)), 'n_test_pairs': int(npairs),
        'n_test_cells': int(ncells),
        'y_test_mean': L.q(float(np.mean(y_test))), 'y_test_sd': L.q(float(np.std(y_test))),
    }
    # drug-cluster sensitivity (held-out drug two-way)
    a_idx = data['pair_a'][data['unit_pair'][test_units]]
    b_idx = data['pair_b'][data['unit_pair'][test_units]]
    bootd = L.bootstrap_rho_drugs(y_test, {k: preds[k] for k in
                                           ['xboth', 'annotation_only'] +
                                           ['xboth_random_%02d' % i for i in range(L.N_RANDOM)]},
                                  a_idx, b_idx, len(data['drug_names']),
                                  B=L.N_BOOT_CI, seed=L.SEED_MASTER)
    rand_mean_bootd = np.mean([bootd['xboth_random_%02d' % i] for i in range(L.N_RANDOM)], axis=0)
    main['drug_cluster_sensitivity'] = {
        'xboth_ci': L.boot_ci(bootd['xboth']),
        'diff_vs_random_ci': L.boot_ci(bootd['xboth'] - rand_mean_bootd),
        'note': 'held-out-drug two-way (anchor-drug x library-drug) cluster bootstrap; sensitivity only',
    }
    # diagnostics (NOT part of the judgment): pair-cluster-only CI and null-z bootstrap sanity
    boot_pair = L.bootstrap_rho_pairs(y_test, {'xboth': preds['xboth'],
                                               'annotation_only': preds['annotation_only']},
                                      pair_codes, npairs, B=L.N_BOOT_CI, seed=L.SEED_MASTER)
    nullz = L.bootstrap_null_pair_z(y_test, pair_codes, cell_codes, npairs, ncells,
                                    B=L.N_BOOT_MDE, seed=L.SEED_MASTER)
    f3_se = pf['gates']['f3']['a_mde80_two_way']['se_two_way']
    f3_mde = pf['gates']['f3']['a_mde80_two_way']['mde80_two_way']
    realized_se = main['xboth_ci_pair_cell']['se']
    main['diagnostics_not_judgment'] = {
        'pair_cluster_only_xboth_ci': L.boot_ci(boot_pair['xboth']),
        'pair_cluster_only_annotation_only_ci': L.boot_ci(boot_pair['annotation_only']),
        'null_fixed_pair_z_two_way_se': L.q(float(np.std(nullz, ddof=1))),
        'null_fixed_pair_z_mde80': L.q(L.Z_MDE80 * float(np.std(nullz, ddof=1))),
        'f3_se_two_way': f3_se, 'f3_mde80': f3_mde,
        'realized_xboth_se_two_way': realized_se,
        'realized_mde80_equivalent': L.q(L.Z_MDE80 * realized_se),
        'note': ('pair-cluster-only CI and the fixed-iid-null-prediction bootstrap are diagnostics only. '
                 'The fixed-iid-null bootstrap (' + str(L.q(L.Z_MDE80 * float(np.std(nullz, ddof=1)))) +
                 ' MDE80-equivalent) is consistent with the pre-flight F3(a) MDE80 (' + str(f3_mde) +
                 '), but the realised SE for the fitted Xboth prediction vector is larger '
                 '(' + str(realized_se) + ' -> MDE80-equivalent ' + str(L.q(L.Z_MDE80 * realized_se)) +
                 '): the pre-flight power calculation used an iid pair-level null prediction and did not '
                 'cover the sampling variability of a structured (level-pair-constant) prediction vector. '
                 'This is a post-hoc diagnostic and does NOT change the frozen design or judgment.')}
    # judgment R1/R2/R3 (primary = pair x cell, v3)
    R1 = bool(rho['xboth'] >= L.DELTA_MIN)
    R2 = bool(main['xboth_ci_pair_cell']['ci_lower'] > 0)
    R3 = bool(main['diff_vs_random_ci_pair_cell']['ci_lower'] > 0)
    if R1 and R2 and R3:
        verdict = 'replicated'
    elif R2 and not (R1 and R3):
        verdict = 'partial'
    else:
        verdict = 'not_replicated'
    main['judgment'] = {'R1_point_ge_delta_min': R1, 'R2_ci_lower_gt0': R2,
                        'R3_control_ci_lower_gt0': R3, 'verdict': verdict,
                        'delta_min': L.DELTA_MIN,
                        'rho_xboth': L.q(rho['xboth']),
                        'ci_pair_cell': main['xboth_ci_pair_cell'],
                        'diff_point': main['diff_vs_random_point'],
                        'diff_ci': main['diff_vs_random_ci_pair_cell']}

    print('[5/6] pre-declared sensitivities ...', flush=True)
    sens = {}
    # (a) other r leg
    r_other = 0.50 if abs(r_main - 0.55) < 1e-9 else 0.55
    print('    sensitivity r=%.2f ...' % r_other, flush=True)
    sens['r_other'] = fit_design(data, m2['mapped'], r_other, include_random=True)
    # (b) E1 split (holdout built on all 4,088 drugs, same seed-permutation rule)
    print('    sensitivity E1 split ...', flush=True)
    H_e1, k_e1, N_e1, sha_e1 = L.split_permutation(data['drug_names'], r_main)
    pools_e1 = L.build_pools(data, lab2, H_e1)
    if len(pools_e1['test_units']) > 100 and len(pools_e1['train_units']) > 1000:
        e1 = fit_design(data, m2['mapped'], r_main, H=H_e1, include_random=False)
        e1['note'] = 'holdout built on the full 4,088-drug universe; annotation universe unchanged'
        e1['holdout_drugs_total'] = N_e1
        sens['E1_split'] = e1
    else:
        sens['E1_split'] = {'error': 'pool too small'}
    # (c) v1 mapping table
    print('    sensitivity v1 mapping ...', flush=True)
    sens['mapping_v1'] = fit_design(data, m1['mapped'], r_main, include_random=False)
    sens['mapping_v1']['note'] = 'v1 mapping table (1,418 mapped drugs); sensitivity only'
    # (d) Jaaks-overlap-entity exclusion
    print('    sensitivity Jaaks overlap exclusion ...', flush=True)
    jo = jaaks_overlap(data)
    drugs_all = data['drug_names']
    ocells = set(jo['overlap_cells'])
    odrugs = set(jo['overlap_drugs'])
    keep = np.array([(data['cell_names'][data['unit_cell'][u]] not in ocells)
                     and (drugs_all[data['pair_a'][data['unit_pair'][u]]] not in odrugs)
                     and (drugs_all[data['pair_b'][data['unit_pair'][u]]] not in odrugs)
                     for u in range(data['n_units'])])
    lab_j = labels_to_lab(data, labels_real)
    tr_j = np.array([u for u in train_units if keep[u]])
    te_j = np.array([u for u in test_units if keep[u]])
    if len(te_j) > 100 and len(tr_j) > 1000:
        xb_j = L.fit_arm(tr_j, te_j, data, labels_real, include_identity=True)
        yj = data['y'][te_j]
        _, pj = np.unique(data['unit_pair'][te_j], return_inverse=True)
        _, cj = np.unique(data['unit_cell'][te_j], return_inverse=True)
        bj = L.bootstrap_rho_pair_cell(yj, {'xboth': xb_j['pred']}, pj.astype(np.int64),
                                       cj.astype(np.int64), int(pj.max()) + 1, int(cj.max()) + 1,
                                       B=L.N_BOOT_CI, seed=L.SEED_MASTER)
        sens['jaaks_overlap_excluded'] = {
            'overlap': {k: v for k, v in jo.items() if k.startswith('n_')},
            'n_test_units_kept': int(len(te_j)), 'n_train_units_kept': int(len(tr_j)),
            'rho': L.q(L.spearman(xb_j['pred'], yj)), 'lambda': xb_j['lambda'],
            'ci_pair_cell': L.boot_ci(bj['xboth']),
            'note': ('units whose cell is in the 18 Jaaks-overlap cells or whose drug is in the '
                     '40 Jaaks-overlap drugs are dropped (entity exclusion); sensitivity only')}
    else:
        sens['jaaks_overlap_excluded'] = {'error': 'pool too small', 'overlap': jo}
    # (e) annotation_only + capacity already in main; map them for convenience
    sens['annotation_only'] = {'rho': main['rho']['annotation_only'],
                               'ci_pair_cell': main['annotation_only_ci_pair_cell'],
                               'note': 'secondary arm (protocol v3)'}
    sens['xboth_capacity'] = {'rho': main['rho']['xboth_capacity'],
                              'ci_pair_cell': main['capacity_ci_pair_cell'],
                              'note': 'capacity control (same-dim random continuous block)'}
    # keep sensitivity payloads compact
    for k in list(sens):
        v = sens[k]
        if isinstance(v, dict):
            for drop in ('test_units', 'train_units', 'pred', 'y', 'lab', 'boot',
                         'rand_mean_boot', 'pair_codes', 'cell_codes'):
                v.pop(drop, None)
            if 'xboth' in v and isinstance(v['xboth'], dict):
                v['xboth'].pop('pred', None)

    print('[6/6] adjusted analyses (study proxy / cell composition) ...', flush=True)
    # block_id 20-quantile proxy (P-B design-era proxy); unit modal bin
    bins_test = data['unit_bin'][test_units]
    bin_counts = {str(b): int((bins_test == b).sum()) for b in range(L.PROXY_BINS)}
    lev_a_test = lab2[data['pair_a'][data['unit_pair'][test_units]]]
    cram = cramers_v(lev_a_test, bins_test, int(lab2.max()) + 1, L.PROXY_BINS)
    # stratified rho
    strat = []
    rest_pred, rest_y = [], []
    for b in range(L.PROXY_BINS):
        sel = bins_test == b
        if sel.sum() >= 300:
            strat.append({'bin': b, 'n_units': int(sel.sum()),
                          'rho': L.q(L.spearman(preds['xboth'][sel], y_test[sel])) if sel.sum() > 2 else None})
        else:
            rest_pred.append(preds['xboth'][sel])
            rest_y.append(y_test[sel])
    if rest_pred:
        rp = np.concatenate(rest_pred); ry = np.concatenate(rest_y)
        strat.append({'bin': 'rest_merged', 'n_units': int(len(rp)),
                      'rho': L.q(L.spearman(rp, ry))})
    partial_proxy = partial_spearman(y_test, preds['xboth'], bins_test)
    partial_proxy_ci = partial_spearman_boot(y_test, preds['xboth'], bins_test,
                                             pair_codes, cell_codes, npairs, ncells,
                                             B=L.N_BOOT_CI, seed=L.SEED_MASTER)
    cell_group = cell_codes
    partial_cell = partial_spearman(y_test, preds['xboth'], cell_group)
    partial_cell_ci = partial_spearman_boot(y_test, preds['xboth'], cell_group,
                                            pair_codes, cell_codes, npairs, ncells,
                                            B=L.N_BOOT_CI, seed=L.SEED_MASTER)
    # cell eta^2 (descriptive)
    cm = np.bincount(cell_group, weights=y_test) / np.bincount(cell_group)
    ss_between = float(((cm[cell_group] - y_test.mean()) ** 2).sum())
    ss_total = float(((y_test - y_test.mean()) ** 2).sum())
    adjusted = {
        'proxy_definition': 'block_id 20-quantile bins (P-B design-era proxy), unit modal bin',
        'proxy_bin_counts': bin_counts,
        'cramers_v_anchor_level_x_proxy': L.q(cram),
        'stratified_rho': strat,
        'partial_rho_controlling_proxy': L.q(partial_proxy),
        'partial_rho_controlling_proxy_ci_pair_cell': L.boot_ci(partial_proxy_ci),
        'partial_rho_controlling_cell': L.q(partial_cell),
        'partial_rho_controlling_cell_ci_pair_cell': L.boot_ci(partial_cell_ci),
        'cell_eta_squared_on_test_y': L.q(ss_between / ss_total) if ss_total > 0 else None,
        'xboth_plus_proxy_diagnostic_arm_rho': main['rho']['xboth_plus_proxy_diagnostic'],
        'xboth_plus_proxy_diagnostic_arm_ci': main['proxy_diagnostic_ci_pair_cell'],
    }
    adjusted_ok = bool((adjusted['partial_rho_controlling_proxy_ci_pair_cell']['ci_lower'] or 0) > 0
                       and (partial_proxy or 0) >= L.DELTA_MIN)
    confounded_unresolved = bool(verdict == 'replicated' and not adjusted_ok)

    # selection-bias disclosure for the ACTUAL main-design test pool
    drugs_all2 = data['drug_names']
    pa_all = data['pair_a']; pb_all = data['pair_b']; up_all = data['unit_pair']
    mapped_pair = (lab2[pa_all] >= 0) & (lab2[pb_all] >= 0)
    mapped_units = np.where(mapped_pair[up_all] & np.isfinite(data['y']))[0]
    cell_train_all = set(np.unique(data['unit_cell'][train_units]).tolist())
    cell_test_all = set(np.unique(data['unit_cell'][test_units]).tolist())
    main['selection_bias_main_design'] = {
        'test_units': int(len(test_units)),
        'test_pairs': int(npairs),
        'test_pairs_of_mapped_pairs_pct': L.q(100.0 * npairs / int(mapped_pair.sum())),
        'test_units_of_annotated_universe_pct': L.q(100.0 * len(test_units) / len(mapped_units)),
        'test_units_of_all_cell_x_pair_units_pct': L.q(100.0 * len(test_units) / data['n_units']),
        'mapped_pairs': int(mapped_pair.sum()), 'annotated_universe_units': int(len(mapped_units)),
        'all_cell_x_pair_units': int(data['n_units']),
        'multi_block_exposure_test_pct': L.q(100.0 * float(np.mean(data['unit_size'][test_units] >= 2))),
        'multi_block_exposure_annotated_universe_pct': L.q(100.0 * float(np.mean(data['unit_size'][mapped_units] >= 2))),
        'cells_test': len(cell_test_all), 'cells_all': len(data['cell_names']),
        'test_cells_also_in_train_pool': int(len(cell_test_all & cell_train_all)),
        'mapped_drugs': int((lab2 >= 0).sum()), 'all_drugs': len(drugs_all2),
        'mapped_drug_coverage_pct': L.q(100.0 * int((lab2 >= 0).sum()) / len(drugs_all2)),
        'note': ('the design only evaluates the annotated both-unseen subset; the conclusion is limited to '
                 'this subset / endpoint / r; cells are never held out.'),
    }

    # ---------------- outputs
    rows = []
    def add_row(scope, r, arm, kind, statistic, value, ci=None, lam=None, notes=''):
        rows.append({'scope': scope, 'r': r, 'arm': arm, 'kind': kind, 'statistic': statistic,
                     'value': value,
                     'ci_lower': None if ci is None else ci.get('ci_lower'),
                     'ci_upper': None if ci is None else ci.get('ci_upper'),
                     'lambda': lam, 'notes': notes})
    add_row('main', r_main, 'xboth', 'main', 'spearman_rho', main['rho']['xboth'],
            main['xboth_ci_pair_cell'], main['lambda']['xboth'])
    add_row('main', r_main, 'xboth', 'main', 'top_quartile_auc', main['top_quartile_auc']['xboth'])
    add_row('main', r_main, 'xboth', 'main', 'top100_hit', main['top100_hit']['xboth'])
    add_row('main', r_main, 'annotation_only', 'secondary', 'spearman_rho',
            main['rho']['annotation_only'], main['annotation_only_ci_pair_cell'],
            main['lambda']['annotation_only'])
    add_row('main', r_main, 'xboth_random_mean(10)', 'control', 'spearman_rho',
            main['random_mean_rho'], main['random_mean_ci_pair_cell'])
    for i in range(L.N_RANDOM):
        nm = 'xboth_random_%02d' % i
        add_row('main', r_main, nm, random_meta[i]['kind'], 'spearman_rho', main['rho'][nm],
                L.boot_ci(boot[nm]), main['lambda'][nm])
    add_row('main', r_main, 'xboth_minus_random_mean', 'main_contrast', 'spearman_diff',
            main['diff_vs_random_point'], main['diff_vs_random_ci_pair_cell'])
    add_row('main', r_main, 'annotation_only_minus_random_mean', 'secondary_contrast',
            'spearman_diff',
            L.q(rho['annotation_only'] - rand_rho_mean),
            main['annotation_minus_random_ci_pair_cell'])
    add_row('main', r_main, 'xboth_capacity', 'control', 'spearman_rho',
            main['rho']['xboth_capacity'], main['capacity_ci_pair_cell'],
            main['lambda']['xboth_capacity'])
    add_row('main', r_main, 'xboth_plus_proxy_diagnostic', 'diagnostic', 'spearman_rho',
            main['rho']['xboth_plus_proxy_diagnostic'], main['proxy_diagnostic_ci_pair_cell'],
            main['lambda']['xboth_plus_proxy_diagnostic'])
    add_row('main', r_main, 'identity_only', 'sanity', 'spearman_rho_by_definition', 0.0)
    add_row('main', r_main, 'constant', 'sanity', 'spearman_rho_by_definition', 0.0)
    for k in ('xboth', 'annotation_only'):
        for fk, vals in (arms[k].get('fold_mean') or {}).items():
            add_row('main_inner_cv', r_main, k, 'lambda=%.1f' % float(fk),
                    'inner_fold_mean_rho', vals)
    # drug-cluster sensitivity
    dc = main['drug_cluster_sensitivity']
    add_row('main', r_main, 'xboth', 'sensitivity_drug_cluster', 'spearman_rho_ci',
            main['rho']['xboth'], dc['xboth_ci'], main['lambda']['xboth'],
            'held-out-drug two-way cluster bootstrap')
    add_row('main', r_main, 'xboth_minus_random_mean', 'sensitivity_drug_cluster',
            'spearman_diff_ci', main['diff_vs_random_point'], dc['diff_vs_random_ci'], None,
            'held-out-drug two-way cluster bootstrap')
    # other-r sensitivity
    s = sens.get('r_other', {})
    if 'xboth' in s:
        add_row('sensitivity', r_other, 'xboth', 'main', 'spearman_rho', s['xboth']['rho'],
                s['xboth_ci'], s['xboth']['lambda'])
        add_row('sensitivity', r_other, 'xboth_random_mean(10)', 'control', 'spearman_rho',
                s.get('random_mean_rho'), s.get('rand_mean_ci'))
        add_row('sensitivity', r_other, 'xboth_minus_random_mean', 'main_contrast',
                'spearman_diff', s.get('diff_point'), s.get('diff_ci'))
    for key, tag in (('E1_split', 'E1_split'), ('mapping_v1', 'mapping_v1')):
        s = sens.get(key, {})
        xb = s.get('xboth') if isinstance(s, dict) else None
        if isinstance(xb, dict) and 'rho' in xb:
            add_row('sensitivity', r_main, 'xboth', tag, 'spearman_rho', xb['rho'],
                    s.get('xboth_ci'), xb.get('lambda'), s.get('note', ''))
    s = sens.get('jaaks_overlap_excluded', {})
    if 'rho' in s:
        add_row('sensitivity', r_main, 'xboth', 'jaaks_overlap_excluded', 'spearman_rho',
                s['rho'], s.get('ci_pair_cell'), s.get('lambda'), s.get('note', ''))
    add_row('sensitivity', r_main, 'annotation_only', 'annotation_only', 'spearman_rho',
            main['rho']['annotation_only'], main['annotation_only_ci_pair_cell'],
            main['lambda']['annotation_only'])
    add_row('sensitivity', r_main, 'xboth_capacity', 'capacity', 'spearman_rho',
            main['rho']['xboth_capacity'], main['capacity_ci_pair_cell'],
            main['lambda']['xboth_capacity'])
    # adjusted rows
    add_row('adjusted', r_main, 'xboth_partial_proxy', 'partial_spearman',
            'rho', adjusted['partial_rho_controlling_proxy'],
            adjusted['partial_rho_controlling_proxy_ci_pair_cell'], None,
            'partial Spearman controlling block_id 20-quantile proxy (pair x cell cluster bootstrap, B=1000)')
    add_row('adjusted', r_main, 'xboth_partial_cell', 'partial_spearman', 'rho',
            adjusted['partial_rho_controlling_cell'],
            adjusted['partial_rho_controlling_cell_ci_pair_cell'], None,
            'partial Spearman controlling cell identity (pair x cell cluster bootstrap, B=1000)')
    for st in strat:
        if st['n_units'] <= 0:
            continue
        add_row('adjusted', r_main, 'xboth', 'stratified_proxy_bin_%s' % st['bin'],
                'spearman_rho', st['rho'], None, None, 'n=%d' % st['n_units'])
    # write rows.csv
    rows_path = os.path.join(L.OUT, 'rows.csv')
    with open(rows_path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['scope', 'r', 'arm', 'kind', 'statistic',
                                           'value', 'ci_lower', 'ci_upper', 'lambda', 'notes'])
        w.writeheader()
        for row in rows:
            w.writerow(row)

    # ---------------- judgment / wording
    if verdict == 'replicated' and confounded_unresolved:
        interpretation = ('replicated (R1 & R2 & R3) BUT adjusted estimate (partial Spearman controlling the '
                          'block_id 20-quantile study proxy) has CI containing 0 or point < delta_min -> '
                          'explanation must be labelled confounded_unresolved; no "explained/robust" wording.')
    elif verdict == 'replicated':
        interpretation = ('replicated: direction/quantity floor reproduced in this setting (r, synergy_bliss, '
                          'KEGG argmax annotation); NOT a mechanism/clinical claim, NOT an independent Jaaks '
                          'confirmation, NOT "the original effect size reproduced".')
    elif verdict == 'partial':
        interpretation = ('partial: direction significant (CI lower > 0) but point estimate < delta_min or the '
                          'random-control contrast CI lower <= 0; report as "direction consistent but below '
                          'the conservative magnitude / control specificity" - neither success nor failure.')
    else:
        interpretation = ('not_replicated in this setting: the pre-registered composite criterion did not pass. '
                          'Cannot say the conditional structure does not exist: three unseparated explanations '
                          'remain - construct mismatch (endpoint/annotation system/r/single split), power '
                          '(MDE=%.4f, composite-rule power from F3), true negative.' % (
                              0.0 if not main else pf['gates']['f3']['a_mde80_two_way']['mde80_two_way']))

    out = {
        'protocol': {'name': 'PROTOCOL_STAGE2 v3 = v1 + AMENDMENT-001 + AMENDMENT-002',
                     'preflight_sha256': L.sha256_file(L.PREFLIGHT_JSON),
                     'stage2_v1_sha256': pf['protocol']['stage2_v1_sha256'],
                     'amendment_001_sha256': pf['protocol']['amendment_001_sha256'],
                     'amendment_002_sha256': pf['protocol']['amendment_002_sha256']},
        'script': {'stage2.py': L.sha256_file(L.SCRIPT_STAGE2),
                   's2lib.py': L.sha256_file(L.SCRIPT_LIB)},
        'input_hash_verification': hashes,
        'selected_design': {'r': r_main, 'split_sha256': sd['split_sha256'],
                            'k_holdout': sd['k_holdout'],
                            'chosen_by_preflight_ladder': True,
                            'reported_by_preflight': sd.get('chosen_by')},
        'structure': structure,
        'preflight_gates': {'all_pass': pf['gates_all_pass'],
                            'f1': pf['gates']['f1']['pass'], 'f2': pf['gates']['f2']['pass'],
                            'f3': pf['gates']['f3']['pass'], 'f4': pf['gates']['f4']['pass'],
                            'f3_mde80_two_way': pf['gates']['f3']['a_mde80_two_way']['mde80_two_way'],
                            'f3_joint_power_primary': pf['gates']['f3']['b_primary_power_at_0.1183'],
                            'f3_joint_power_alt_reading': pf['gates']['f3']['b_alt_power_at_0.1183']},
        'main': main,
        'judgment': {'verdict': verdict,
                     'R1': R1, 'R2': R2, 'R3': R3,
                     'confounded_unresolved': confounded_unresolved,
                     'adjusted_ok': adjusted_ok,
                     'interpretation': interpretation,
                     'delta_min': L.DELTA_MIN,
                     'wording_boundaries': [
                         'replicated: only "direction/quantity floor reproduced in this setting"',
                         'not_replicated: only "not detected in this setting"; not "DrugComb cannot replicate"',
                         'partial: neither success nor failure',
                         'no mechanism / clinical / target-occupancy claim',
                         'not an independent confirmation of Jaaks; not "original effect size reproduced"']},
        'sensitivities': sens,
        'adjusted': adjusted,
        'disclosures': {
            'cross_r': pf['disclosures'].get('cross_r_disclosure'),
            'cross_endpoint': ('original endpoint DeltaEMAX (dose-response fitted observed-expected Emax) vs '
                               'DrugComb synergy_bliss (mean Bliss residual over dose matrix): same null model / '
                               'direction / comparable scale argued by P-B, NOT the same statistic.'),
            'cross_annotation_system': ('project pathway template = 38 two-sided one-hot pathway levels '
                                        '(21 text levels; source R190-E1/P-A report) vs this design = KEGG 186 '
                                        'single-label argmax, 93 analyzable levels (target-gene-set co-membership '
                                        'coarse proxy; tie/single-gene biases known).'),
            'selection_bias': pf['disclosures'],
            'only_effect_ge_threshold': ('this design can only test effects of about >=0.10; smaller effects '
                                         '(< MDE80) are not decidable and a negative result cannot exclude them.'),
            'single_split': ('one deterministic seed-permutation split; original frozen effect was a mean over 40 '
                             'random splits; uncertainty is reported via cluster bootstrap but split-selection '
                             'sampling uncertainty is not the same estimator.'),
            'cells_not_held_out': ('cells are not part of the split; every test cell also appears in the training '
                                   'pool; predictions are pair-level (C141-type).'),
        },
        'response_use_attestation': {
            'models_fitted': True,
            'response_columns_used': ['synergy_bliss'],
            'test_labels_used_only_for': ['final scoring', 'cluster bootstrap CIs / adjusted descriptive analyses',
                                          'preflight F3 zero-model design step (already frozen before this run)'],
            'test_labels_used_for_tuning_or_selection': False,
            'standardization_and_lambda': 'fitted per inner fold on inner-training rows only; outer test drugs never '
                                          'enter standardization / lambda selection',
        },
        'deviations_from_protocol': [],
        'implementation_choices': [
            'F3(b) AMENDMENT-002 section 1 step 1 is read literally: the pair x cell bootstrap of the '
            'zero prediction yields the null-rho distribution whose SD is SE_two_way, hence '
            'se_null = SE_two_way for the primary joint-power calculation. The alternative reading '
            '(zero-model arm = mean of 10 seeds -> se_null = SE/sqrt(10)) is reported in preflight.json; '
            'the selected r=0.55 design passes F3 under BOTH readings (see preflight ladder record).',
            'F3(b) simulation seed = P-B2 power seed rule (design seed + 7); F3(a) bootstrap B=2000 with '
            'P-B2 design seed rule (SEED2 + 1000 + 100*round(r*100)).',
            'R2/R3 main CI = P-B2 Regime-B pair x cell two-way cluster bootstrap, B=1000, seed 20261027 '
            '(AMENDMENT-002 final version).',
            'held-out-drug clustering sensitivity implemented as held-out-drug two-way '
            '(anchor-drug x library-drug) cluster bootstrap.',
            'study proxy = P-B design-era proxy: block_id 20-quantile bins, unit modal bin.',
        ],
        'amendments_applied': ['AMENDMENT-001', 'AMENDMENT-002 (v3 final)'],
        'preflight_ladder': pf.get('ladder'),
    }
    L.write_json(out, L.STAGE2_JSON)
    print('\n==== STAGE2 VERDICT: %s ====' % verdict)
    print('  main r=%.2f: Xboth rho %.6f  CI [%s, %s]' % (
        r_main, main['rho']['xboth'], main['xboth_ci_pair_cell']['ci_lower'],
        main['xboth_ci_pair_cell']['ci_upper']))
    print('  random mean rho %.6f | diff %.6f CI [%s, %s]' % (
        main['random_mean_rho'], main['diff_vs_random_point'],
        main['diff_vs_random_ci_pair_cell']['ci_lower'],
        main['diff_vs_random_ci_pair_cell']['ci_upper']))
    print('  R1=%s R2=%s R3=%s -> %s' % (R1, R2, R3, verdict))
    print('  annotation_only rho %.6f | capacity %.6f' % (
        main['rho']['annotation_only'], main['rho']['xboth_capacity']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
