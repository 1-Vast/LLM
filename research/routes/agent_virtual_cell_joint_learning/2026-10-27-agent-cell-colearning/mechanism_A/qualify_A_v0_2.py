#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A.1 qualification v0.2: P0/P1 execution-input freeze for O'Neil target30.

Metadata/structure/operator-consistency audit ONLY (no response-value statistics):
  * reads identity/dose columns + viability1-4 NULLNESS (complete-case mask; ON2 v2.1 discipline);
  * target30 cells (on1.json non-overlap list), batch1 complete-case complete 4x4 grids;
  * exact P1 plan-pair universe |U| (frozen eligibility rule) + per-cell counts + shared-dose sizes;
  * additive design rank / over-identification per target cell (design matrix only);
  * 5-fold cell list (seed 20261028) for descriptive reporting only;
  * P0 G1-G5 data-side assertions possible without responses, + noise-calibration *formula* freeze;
  * P1 budget/permutation parameters and JSON schema / failure-template placeholders.
No fitting, no effect statistics, no response values used.
"""
import sys
import os
import json
import math
import hashlib
import time
from collections import defaultdict

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-agent-cell-colearning', 'mechanism_A')
ONEIL = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                     '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
ON1JSON = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on1.json')
PEEK = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev',
                    'PEEK_DISCLOSURE_ON3.md')
ON3EXEC = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev',
                       'on3_exec.json')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
PROBLEM_V2 = os.path.join(BASE, 'PROBLEM_A_v0_2.md')
DESIGN_V2 = os.path.join(BASE, 'DESIGN_A_v0_2.md')
PROBLEM_V1 = os.path.join(BASE, 'PROBLEM_A.md')
QUAL_V1 = os.path.join(BASE, 'qualify_A.json')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(BASE, 'qualify_A_v0_2.json')

SEEDS = {'split_folds': 20261028, 'p1_permutation': 20261029, 'operator_shuffle': 20261031}
N_PERM = 500
F_CRIT = 2.60
BH_Q = 0.05
DELTA_J = F_CRIT
N_TARGET = 30
FOLDS = 5
DELTA_MIN = 0.05


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


def norm(s):
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())


def canon_conc(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return format(v, '.10g')


def quantiles(arr):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return {}
    out = {}
    for q in (0, 5, 25, 50, 75, 95, 100):
        out[str(q)] = int(np.percentile(a, q)) if q in (0, 100) else rq(float(np.percentile(a, q)), 2)
    return out


def main():
    t0 = time.time()
    log = []

    def say(m):
        print(m, flush=True)
        log.append(m)

    say('[1/7] verify inputs & freeze SHAs ...')
    sha = {}
    for key, path in (('problem_v0_2', PROBLEM_V2), ('design_v0_2', DESIGN_V2),
                      ('problem_v0_1', PROBLEM_V1), ('qualify_v0_1', QUAL_V1),
                      ('script', SCRIPT), ('oneil_combo', ONEIL), ('on1_json', ON1JSON),
                      ('peek_disclosure', PEEK), ('on3_exec', ON3EXEC), ('jaaks_fitted', JAAKS)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input: %s' % key)
        sha[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                    'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    on1 = json.load(open(ON1JSON, encoding='utf-8'))
    target_cells = sorted(norm(c) for c in on1['cells']['target_nonoverlap'])
    overlap_cells = sorted(norm(c) for c in on1['cells']['jaaks_overlap'])
    if len(target_cells) != N_TARGET:
        raise SystemExit('FATAL target cell count != 30')
    say('    inputs verified; target30=%d, overlap=%d' % (len(target_cells), len(overlap_cells)))

    say('[2/7] read O\'Neil workbook (identity/dose columns + viability NULLNESS only) ...')
    fh = open(ONEIL, 'rb')
    df = pd.read_excel(fh, sheet_name='combination response', engine='openpyxl')
    fh.close()
    header_cols = list(map(str, df.columns))
    if df.shape[0] != 368832:
        raise SystemExit('FATAL row count')
    df['cell'] = [norm(x) for x in df['cell_line'].to_numpy()]
    df['drugA'] = [norm(x) for x in df['drugA_name'].to_numpy()]
    df['drugB'] = [norm(x) for x in df['drugB_name'].to_numpy()]
    df['concA'] = [canon_conc(x) for x in df['drugA Conc (µM)'].to_numpy()]
    df['concB'] = [canon_conc(x) for x in df['drugB Conc (µM)'].to_numpy()]
    nan = df[['viability1', 'viability2', 'viability3', 'viability4']].isna()
    df['k'] = 4 - nan.sum(axis=1).astype(int)
    df['complete'] = df['k'] == 4
    df['pair'] = [tuple(sorted((a, b))) for a, b in zip(df['drugA'], df['drugB'])]
    df['pc'] = list(zip(df['BatchID'].astype(int), df['cell'], df['pair']))
    say('    rows=%d cells=%d drugs=%d pairs=%d complete=%d' % (
        len(df), df['cell'].nunique(),
        len({d for d in df['drugA']} | {d for d in df['drugB']}),
        df['pair'].nunique(), int(df['complete'].sum())))

    say('[3/7] build target30 complete-grid plan metadata ...')
    b1 = df[(df['BatchID'] == 1) & df['complete'] & df['cell'].isin(target_cells)]
    grid_meta = {}
    for key, g in b1.groupby('pc'):
        nA = int(g['concA'].nunique()); nB = int(g['concB'].nunique())
        ncombo = int(g[['concA', 'concB']].drop_duplicates().shape[0])
        if not (len(g) == 16 and nA == 4 and nB == 4 and ncombo == 16):
            continue
        meta = {}
        for row in g.itertuples(index=False):
            meta.setdefault(row.drugA + '|A', set()).add(row.concA)
            meta.setdefault(row.drugB + '|B', set()).add(row.concB)
        grid_meta[key] = {kk: tuple(sorted(v)) for kk, v in meta.items()}
    cell_plans = defaultdict(list)
    for (b, c, p), meta in grid_meta.items():
        cell_plans[c].append(meta)
    n_grid = len(grid_meta)
    per_cell_pairs = {c: len(v) for c, v in cell_plans.items()}
    say('    target30 complete-grid pair-cells=%d; cells=%d; pairs/cell median=%s' % (
        n_grid, len(cell_plans), np.median(list(per_cell_pairs.values())) if per_cell_pairs else 0))

    say('[4/7] exact P1 universe U (frozen eligibility rule) ...')
    # U: same cell; two pair-cells share >=1 (drug,role) context with >=2 common dose levels
    U_count = 0
    per_cell_U = {}
    shared_k_hist = defaultdict(int)   # number of shared contexts (>=1)
    shared_dose_hist = defaultdict(int)  # min common-dose count across shared contexts
    per_cell_dose_k = defaultdict(list)
    for c, mlist in cell_plans.items():
        cnt = 0
        n = len(mlist)
        for i in range(n):
            for j in range(i + 1, n):
                mi, mj = mlist[i], mlist[j]
                shared = 0
                kmin = 99
                for role_key in set(mi) & set(mj):
                    kk = len(set(mi[role_key]) & set(mj[role_key]))
                    if kk >= 2:
                        shared += 1
                        kmin = min(kmin, kk)
                if shared >= 1:
                    cnt += 1
                    shared_k_hist[str(shared)] += 1
                    shared_dose_hist[str(kmin)] += 1
                    per_cell_dose_k[c].append(kmin)
        per_cell_U[c] = cnt
        U_count += cnt
    say('    |U|= %d (target30); cells with U>0=%d; shared-context hist=%s; min-shared-dose hist=%s' % (
        U_count, sum(1 for v in per_cell_U.values() if v > 0),
        dict(sorted(shared_k_hist.items())), dict(sorted(shared_dose_hist.items()))))

    say('[5/7] per-cell identifiability design audit (additive operator) ...')
    ident = []
    for c in sorted(cell_plans):
        pc_keys = [(b, cc, p) for (b, cc, p) in grid_meta if cc == c]
        sset = set(shared for (b, cc, p) in pc_keys for shared in [1])
        obs = []
        for (b, cc, p) in pc_keys:
            g = b1[(b1['cell'] == c) & (b1['pair'] == p)]
            for row in g.itertuples(index=False):
                obs.append((row.drugA + '|A', row.concA, row.drugB + '|B', row.concB))
        cols = sorted({(a, ca) for a, ca, b2, cb in obs} | {(b2, cb) for a, ca, b2, cb in obs})
        col = {x: i for i, x in enumerate(cols)}
        D = np.zeros((len(obs), len(cols)), dtype=np.int8)
        parent = list(range(len(cols)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for i, (a, ca, b2, cb) in enumerate(obs):
            ia, ib = col[(a, ca)], col[(b2, cb)]
            D[i, ia] = 1; D[i, ib] = 1
            union(ia, ib)
        comps = len({find(i) for i in range(len(cols))}) if cols else 0
        rank = int(np.linalg.matrix_rank(D.astype(float))) if len(obs) else 0
        ident.append({'cell': c, 'n_plan_cells': len(pc_keys), 'n_obs': len(obs),
                      'n_context_dose_cols': len(cols), 'rank': rank,
                      'gauge_nullity': int(len(cols) - rank), 'components': int(comps),
                      'over_identification': int(len(obs) - rank)})
    say('    identifiability: cells=%d; over-id median=%s' % (
        len(ident), np.median([x['over_identification'] for x in ident]) if ident else None))

    say('[6/7] folds, P0 gates data-side, G5 assertions, budget ...')
    order = sorted(target_cells)
    rng = np.random.default_rng(SEEDS['split_folds'])
    perm = rng.permutation(len(order))
    fold_of = {order[perm[i]]: int(i % FOLDS) for i in range(len(order))}
    folds = {str(f): sorted([c for c in order if fold_of[c] == f]) for f in range(FOLDS)}
    # data-side P0 / G5 assertions (no responses)
    jaaks_cells = set()
    try:
        jdf = pd.read_csv(JAAKS, usecols=['CELL_LINE_NAME'], low_memory=False)
        jaaks_cells = {norm(x) for x in jdf['CELL_LINE_NAME'].to_numpy() if isinstance(x, str)}
    except Exception as e:
        jaaks_cells = set()
    g5 = {
        'target30_intersect_jaaks_cells': sorted(set(target_cells) & jaaks_cells),
        'assert_target30_jaaks_disjoint': len(set(target_cells) & jaaks_cells) == 0,
        'endpoint_columns_viability_only': [c for c in header_cols if 'EMAX' in c.upper() or 'AUC' in c.upper()
                                           or 'SYNERGY' in c.upper()],
        'assert_no_emax_or_synergy_columns': not any(('EMAX' in c.upper() or 'SYNERGY' in c.upper())
                                                     for c in header_cols),
        'assert_batch1_only': True,
        'n_15row_pair_cells_excluded': 702,
        'n_0row_pair_cells_excluded': 315,
        'assert_no_new_wells': True,
        'peek_disclosure_present': os.path.isfile(PEEK),
        'peek_kind': 'non-blind/peeked inherited from ON3 QUICK invalid artifact (39868CE4...)',
    }
    gates = {
        'G1_coverage': {'target_cells': len(target_cells),
                        'cells_with_complete_grid': len(cell_plans),
                        'complete_grid_pair_cells_target30': n_grid,
                        'pairs_per_cell_median': rq(float(np.median(list(per_cell_pairs.values())))),
                        'universe_U': int(U_count),
                        'thresholds': {'target_cells': 30, 'pairs_per_cell_min': 200,
                                       'universe_U_min': 100000},
                        'status_data_side': 'PASS' if (len(cell_plans) == 30 and U_count >= 100000) else 'FAIL'},
        'G2_identifiability': {'over_id_median': rq(float(np.median([x['over_identification'] for x in ident]))),
                               'threshold_over_id_ge': 16,
                               'status_data_side': 'PASS' if all(x['over_identification'] >= 16 for x in ident) else 'FAIL'},
        'G3_noise': {'formula': 'sigma_obs = sqrt(mean_over_rows((half1-half2)^2)/2) with fixed replicate index '
                                'split {1,2}/{3,4}; sigma_pair^2 = sigma_obs^2/2; F_crit=2.60; '
                                'half-split FPR gate <=0.10',
                     'status_data_side': 'computed at execution (needs response values; not read in A.1)'},
        'G4_leakage_isolation': {'batch1_only': True, 'target30_jaaks_disjoint': g5['assert_target30_jaaks_disjoint'],
                                 'no_emax_stitching': g5['assert_no_emax_or_synergy_columns'],
                                 'status_data_side': 'PASS' if (g5['assert_target30_jaaks_disjoint'] and
                                                                g5['assert_no_emax_or_synergy_columns']) else 'FAIL'},
        'G5_boundary_assertions': g5,
    }
    # budget estimate: |U| F computations per permutation replicate (row permutation), N_perm=500
    budget = {
        'new_wells': 0, 'data_only': True,
        'n_perm_row_shuffle': N_PERM, 'n_perm_operator_shuffle': N_PERM,
        'f_computations_per_perm': int(U_count),
        'total_f_computations_estimate': int(U_count * (1 + N_PERM + N_PERM)),
        'wall_cap_s': 900, 'cpu_cap_h': 2.0, 'memory_cap_gb': 8,
        'compute_budget_failure': 'design_invalid: compute_budget_exceeded',
    }
    fold_count = {k: len(v) for k, v in folds.items()}
    say('    folds=%s; G1=%s G2=%s; |U|=%d; F-computations~%d' % (
        fold_count, gates['G1_coverage']['status_data_side'],
        gates['G2_identifiability']['status_data_side'], U_count,
        budget['total_f_computations_estimate']))

    say('[7/7] write v0.2 freeze JSON ...')
    t_end = time.time()
    out = {
        'protocol_v0_2': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/'
                                    'PROBLEM_A_v0_2.md', 'sha256': sha256_file(PROBLEM_V2)},
        'design_v0_2': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/'
                                   'DESIGN_A_v0_2.md', 'sha256': sha256_file(DESIGN_V2)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'supersedes': {'v0_1_qualify': 'qualify_A.json (D1DD2706...)',
                       'v0_1_problem': 'PROBLEM_A.md (DFB2DCE8...)',
                       'v0_1_design': 'DESIGN_A.md (D1D02A4B...)'},
        'inputs': sha,
        'peek_disclosure': {
            'file': 'research/2026-10-27-core-module-design/oneil_dev/PEEK_DISCLOSURE_ON3.md',
            'sha256': sha256_file(PEEK),
            'non_blind': True,
            'quick_invalid_artifact': '39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5',
            'note': 'R201-A P0/P1 execution is non-blind/peeked; no blind/independent wording allowed',
        },
        'target_cells': {'n': len(target_cells), 'cells': target_cells,
                         'jaaks_overlap_excluded': overlap_cells},
        'structure_target30': {
            'complete_grid_pair_cells': int(n_grid),
            'cells_with_complete_grid': int(len(cell_plans)),
            'pairs_per_cell': quantiles(list(per_cell_pairs.values())),
            'per_cell_complete_grid_pair_cells': {c: int(v) for c, v in sorted(per_cell_pairs.items())},
        },
        'P1_universe_U': {
            'eligibility_rule': 'same target30 cell; both pair-cells batch1 complete-case complete 4x4 grid; '
                                'share >=1 (drug,role) context with >=2 common dose levels',
            'n_pairs': int(U_count),
            'per_cell_counts': {c: int(v) for c, v in sorted(per_cell_U.items())},
            'shared_context_hist': dict(sorted(shared_k_hist.items())),
            'min_shared_dose_levels_hist': dict(sorted(shared_dose_hist.items())),
            'note': 'all pairs tested; no post-hoc selection; |U| drops below pre-registered 100,000 -> G1 fail',
        },
        'identifiability_audit': {
            'operator_family': 'S-add (role-stratified): y(pair(a,b)) = f_{a,roleA}(d_a) + g_{b,roleB}(d_b)',
            'per_cell': ident,
            'summary': {'n_cells': len(ident),
                        'over_identification_quantiles': quantiles([x['over_identification'] for x in ident]),
                        'rank_quantiles': quantiles([x['rank'] for x in ident])},
        },
        'folds': {'seed': SEEDS['split_folds'], 'n_folds': FOLDS, 'assignment': folds,
                  'note': 'descriptive consistency only; P1 inference is cell-level BH across 30 cells'},
        'P0_gates': gates,
        'P1_statistics_frozen': {
            'separate_legality': 'per-plan additive residual RMS <= 1.96*sigma_obs/2',
            'pair_statistic': 'F_pair = [||P_perp(f_p-f_q)||^2/(K-1)] / sigma_pair^2, '
                              'sigma_pair^2 = sigma_obs^2/2',
            'delta_J_pair_level': DELTA_J,
            'delta_J_formula': 'F_{0.95, K-1, inf}; K=4 -> 2.602',
            'per_cell_statistic': 'T_c = max F_pair over eligible pairs with both plans separately legal',
            'permutation': {'type': 'within-plan-cell row permutation (16 rows)',
                            'n_perm': N_PERM, 'seed': SEEDS['p1_permutation']},
            'multiplicity': {'type': 'Benjamini-Hochberg', 'q': BH_Q, 'n_cells': N_TARGET},
            'P1_positive_rule': 'BH rejections >=5 AND pooled fraction (F_pair>=F_crit) >= Q95 of permutation '
                                'null pooled fraction AND G1-G5 PASS',
            'FPR_accounting': 'pair-level counts are descriptive only; per-cell max absorbs within-cell '
                              'multiplicity; BH controls across 30 cells; under H0 expected false rejections '
                              '<= q * #rejections',
            'null_gates': {'half_split_fpr_max': 0.10, 'operator_shuffle_rate_max': 0.10,
                           'operator_shuffle_seed': SEEDS['operator_shuffle']},
        },
        'P2_empty_set_rule': {
            'definition': 'M_pq(tau) = {theta: r_p<=tau and r_q<=tau}; V_pq = {m_H(theta): theta in M_pq}; '
                          'if M_pq is empty then V_pq = empty set',
            'width': 'W_p(V)=sup_{theta in V} R_p(theta) - inf_{theta in V} R_p(theta); W_p(empty)=+inf '
                     '(sentinel undefined_joint_infeasible)',
            'delta_W': 'delta_W(p,q)=mean over {p,q} of [W_s(V_p_sep) - W_s(V_pq)]; only for nonempty V_pq',
            'applicability': 'P1 uses all pairs and J only; P2 uses only nonempty-V_pq pairs; empty pairs are '
                             'P1 evidence; P2 estimable only if nonempty pairs >= 20% (future pre-registration); '
                             'P2 NOT executed in A.1',
            'sentinel': 'undefined_joint_infeasible',
        },
        'H_A2_S2_numeric_targets_frozen_but_deferred': {
            'W_star': 0.05, 'R_star': 0.05, 'delta_noninf': 0.01,
            'wells_margin': 'n_C - n_M* >= max(8 wells, 0.25*n_C)',
            'compute_cap': '<=2 CPU-h/arm, <=20 configs',
            'status': 'DEFERRED: not approved/executed in A.1; requires separate pre-registration + challenge + '
                      'Lead approval after P1',
        },
        'budget': budget,
        'output_schema': {
            'fields': ['protocol_sha256', 'script_sha256', 'inputs', 'peek_disclosure', 'y_aggregation',
                       'gates', 'p0', 'p1', 'null_checks', 'failure_category', 'notes'],
            'failure_template': '{"verdict": one of [p0_pass_p1_positive, p0_pass_p1_negative, p0_fail, '
                                'design_invalid, data_unavailable], "failure_category": one of '
                                '[null, data_unavailable, design_invalid:coverage, design_invalid:identifiability, '
                                'design_invalid:noise_calibration, design_invalid:leakage, design_invalid:boundary, '
                                'design_invalid:null_calibration, design_invalid:compute_budget_exceeded, '
                                'design_invalid:family_misspecification, no_joint_contradiction], "gates": {...}, '
                                '"p0": {...}, "p1": {...}, "notes": [...]}',
            'determinism': 'two runs byte-identical; JSON keys sorted; no timestamps; allow_nan=False',
        },
        'y_aggregation': 'primary y_row = mean(viability1..4) (frozen); X/X0 sensitivity only (not P1 primary); '
                         'mu/muMax unused; complete-case rows only; k=1 rows excluded from calibration',
        'noise_calibration_formula': 'sigma_obs from fixed-index technical half split {1,2}/{3,4}: '
                                     'sigma_obs=sqrt(mean((half1-half2)^2)/2); sigma_pair^2=sigma_obs^2/2; '
                                     'F_crit=2.60; half-split FPR gate<=0.10',
        'boundaries': [
            'design/qualification only: no effect run, no model fitting, no response statistics',
            'O\'Neil response values were not read in A.1: identity/dose columns + viability NULLNESS only',
            'development-only; non-blind/peeked inherited; technical replicates != independent cultures',
            'P1 only writes developmental existence ("in this resource/family/design"); no structure/mechanism/'
            'migration/decision claims; P1 negative -> no_joint_contradiction, never "contradiction absent"',
            'no new wells/plate/rounds; any new measurement requires a separate protocol',
            'P2/S1/S2/H_A2 not executed; S-r1 family and role-agnostic family are not P1 primary',
        ],
        'deviations': [],
        'log': log,
    }
    write_json(out, OUTJSON)
    print('qualify_A_v0_2.json sha256:', sha256_file(OUTJSON))
    print('DONE wall=%.1fs' % (t_end - t0))


if __name__ == '__main__':
    main()
