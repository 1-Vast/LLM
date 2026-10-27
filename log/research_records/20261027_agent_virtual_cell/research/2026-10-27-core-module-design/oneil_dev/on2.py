#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R199-ON2: O'Neil COMPLETE-CASE v2 protocol -- qualification/data-preparation runner.
NO fitting, NO effect estimation, NO updater comparison, NO training.

Post-observation protocol revision (v2), frozen in PROTOCOL_ON2.md before any ON2
qualification count. v1 remains data_unavailable; AMENDMENT_ON1-001 is NOT frozen.

Metadata-only: reads BatchID / cell / drug names / numeric doses and the
viability1-4 nullness mask (for complete-case cohort and missingness pattern only);
response values are never used in any statistic (no means/variances/effects).
Missingness patterns are counts only.

Deterministic: JSON sorted keys, no timestamps, input/script SHA256 recorded;
identical code must produce byte-identical on2.json on rerun.
"""
import hashlib
import json
import math
import os
import sys
import time
import unicodedata
from collections import Counter

import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev')
COMP = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                    '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
SINGLE = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                      '15357163mct150843-sup-156849_1_supp_0_w2lh45.xlsx')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
PROTOCOL_ON2 = os.path.join(OUTDIR, 'PROTOCOL_ON2.md')
PROTOCOL_ON1 = os.path.join(OUTDIR, 'PROTOCOL_ON1.md')
ON1JSON = os.path.join(OUTDIR, 'on1.json')
CHALLENGE_ON1 = os.path.join(OUTDIR, 'challenge_ON1_amendment.md')
AMENDMENT_ON1 = os.path.join(OUTDIR, 'AMENDMENT_ON1-001.md')
Q0JSON = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'qualification', 'q0.json')
PROTOCOL_Q0 = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'qualification', 'PROTOCOL_Q0.md')
R199BRIEF = os.path.join(ROOT, 'research', '2026-10-27-innovation-round-r199', 'BRIEF.md')
SCRIPT = os.path.join(OUTDIR, 'on2.py')
OUTJSON = os.path.join(OUTDIR, 'on2.json')
OUTUSAGE = os.path.join(OUTDIR, 'usage_on2.json')

# frozen v2 thresholds / constants (PROTOCOL_ON2 section 3; do not change)
DG1_MIN_UNITS = 5000
DG1_MIN_CONTRIB_CELLS = 30
DG1_MIN_CONTEXTS = 200
DG1_MIN_CROSS_CONTEXTS = 10
DG1_MIN_CROSS_CELLS = 3
DG2_MIN_COMPLETE_FRAC = 0.95
DG3_REPLICATE_COLS = ['viability1', 'viability2', 'viability3', 'viability4']
DSG1_FOLDS = 5
DSG1_MIN_UNITS_PER_FOLD = 1000
DSG1_MIN_CONTEXTS_PER_FOLD = 5
DELTA_MIN_PROVISIONAL = 0.10
MDE_FACTOR = 2.801585218112968
SIGMA_E_GRID = (0.041, 0.058, 0.109)
N_EFF_GRID = (6, 12, 24, 30)
TARGET_N_CELLS = 30
V11_MIN_REP_ROWS_FRAC = 0.95   # v1.1 sensitivity: per member context, >=95% of 16 rows have >=2 reps
V11_MIN_ROWS_GE2 = 12          # v1.1 sensitivity: member usable only if >=12/16 rows have >=2 reps
V11_CONTEXT_PASS_FRAC = 0.95   # v1.1 sensitivity: >=95% of member contexts pass row criterion
MI_M = 20
MI_SEED = 20261120


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def norm(s):
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())


def rq(x, nd=8):
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    try:
        v = float(x)
    except (TypeError, ValueError):
        return x
    if not math.isfinite(v):
        return None
    return float(round(v, nd))


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


def describe_counts(s):
    s = pd.Series(s)
    if s.empty:
        return None
    return {'count': int(s.size), 'min': rq(s.min()), 'q25': rq(s.quantile(0.25)),
            'median': rq(s.median()), 'mean': rq(s.mean()), 'q75': rq(s.quantile(0.75)),
            'max': rq(s.max())}


def main():
    t0 = time.time()
    print('[ON2] hashing inputs ...', flush=True)
    inputs = {}
    for key, path in (('oneil_combination_workbook', COMP),
                      ('oneil_single_agent_workbook', SINGLE),
                      ('jaaks_original_fitted_cellnames_only', JAAKS),
                      ('protocol_on2', PROTOCOL_ON2), ('protocol_on1', PROTOCOL_ON1),
                      ('on1_json_v1', ON1JSON), ('challenge_on1_amendment', CHALLENGE_ON1),
                      ('amendment_on1_001', AMENDMENT_ON1),
                      ('protocol_q0', PROTOCOL_Q0), ('q0_json', Q0JSON),
                      ('r199_brief', R199BRIEF), ('script_on2', SCRIPT)):
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    v1 = json.load(open(ON1JSON, encoding='utf-8'))  # read-only comparison (v1 numbers must NOT be reused)

    print('[ON2] reading O\'Neil combination workbook (metadata + replicate nullness mask) ...', flush=True)
    usecols = ['BatchID', 'cell_line', 'drugA_name', 'drugA Conc (µM)',
               'drugB_name', 'drugB Conc (µM)'] + DG3_REPLICATE_COLS
    d = pd.read_excel(COMP, sheet_name='combination response', usecols=usecols)
    hdr = [str(c) for c in pd.read_excel(COMP, sheet_name='combination response', nrows=0).columns]
    n_rows_raw = int(len(d))
    for c in ('cell_line', 'drugA_name', 'drugB_name'):
        d[c] = d[c].astype(str).map(norm)
    d['batch'] = d.BatchID.astype(int)
    d['da'] = pd.to_numeric(d['drugA Conc (µM)'], errors='coerce').round(9)
    d['db'] = pd.to_numeric(d['drugB Conc (µM)'], errors='coerce').round(9)
    d['upair'] = [tuple(sorted((a, b))) for a, b in zip(d.drugA_name, d.drugB_name)]
    d['rep_nonnull'] = d[DG3_REPLICATE_COLS].notna().sum(axis=1)
    d['complete_case'] = d.rep_nonnull == 4
    miss_cols = {c: d[c].isna() for c in DG3_REPLICATE_COLS}
    missing_by_col = {c: int(miss_cols[c].sum()) for c in DG3_REPLICATE_COLS}
    # co-missing patterns (only which columns are missing; no values)
    pattern_cols = DG3_REPLICATE_COLS
    Mmiss = np.column_stack([d[c].isna().to_numpy() for c in pattern_cols])
    bits = (Mmiss * (1 << np.arange(Mmiss.shape[1]))).sum(axis=1).astype(np.int64)
    bit_counts = np.bincount(bits, minlength=1 << Mmiss.shape[1])
    co_missing_pattern = {}
    for b in range(bit_counts.size):
        cnt = int(bit_counts[b])
        if cnt == 0:
            continue
        names = [pattern_cols[k] for k in range(len(pattern_cols)) if (b >> k) & 1]
        co_missing_pattern[(';'.join(names) if names else 'complete')] = cnt
    rows_all4 = int(d.complete_case.sum())
    rows_all4_frac = float(rows_all4 / n_rows_raw) if n_rows_raw else 0.0
    rows_min_reps_dist = {str(int(k)): int(v) for k, v in d.rep_nonnull.value_counts().sort_index().items()}
    # batch-level cohort table
    batch_table = {}
    for bt in sorted(d.batch.unique()):
        sub = d[d.batch == bt]
        batch_table[str(bt)] = {
            'rows_raw': int(len(sub)),
            'rows_complete_case': int(sub.complete_case.sum()),
            'rows_dropped': int((~sub.complete_case).sum()),
            'cells_raw': int(sub.cell_line.nunique()),
            'cells_complete_case': int(sub[sub.complete_case].cell_line.nunique()),
            'pair_cells_raw': int(sub.groupby(['cell_line', 'upair']).ngroups),
            'pair_cells_complete_case': int(sub[sub.complete_case].groupby(['cell_line', 'upair']).ngroups),
            'missing_by_col': {c: int(sub[c].isna().sum()) for c in DG3_REPLICATE_COLS},
        }
    # response columns are no longer needed: keep only the row-level complete-case mask
    d = d.drop(columns=DG3_REPLICATE_COLS)
    print('[ON2] raw rows=%d complete_case=%d (%.4f) (%.1fs)'
          % (n_rows_raw, rows_all4, rows_all4_frac, time.time() - t0), flush=True)

    # missingness by pair-cell / grid position (metadata only)
    pc_raw = d.groupby(['batch', 'cell_line', 'upair']).agg(rows_raw=('batch', 'size')).reset_index()
    d_cc = d[d.complete_case].copy()
    pc_cc = d_cc.groupby(['batch', 'cell_line', 'upair']).agg(rows_cc=('batch', 'size')).reset_index()
    pc_cmp = pc_raw.merge(pc_cc, on=['batch', 'cell_line', 'upair'], how='left').fillna({'rows_cc': 0})
    pc_cmp['rows_cc'] = pc_cmp.rows_cc.astype(int)
    pc_rows_cc_dist = {str(int(k)): int(v) for k, v in pc_cmp.rows_cc.value_counts().sort_index().items()}
    n_pc_15 = int((pc_cmp.rows_cc == 15).sum())
    n_pc_partial = int((pc_cmp.rows_cc < 16).sum())
    # grid position: rank of member dose and partner dose within each pair-cell group (raw)
    d['i_member_dose'] = d.groupby(['batch', 'cell_line', 'upair'])['da'].rank(method='dense').astype(int)
    d['j_partner_dose'] = d.groupby(['batch', 'cell_line', 'upair'])['db'].rank(method='dense').astype(int)
    grid_pos_missing = {}
    miss_rows = d[~d.complete_case]
    gtab = miss_rows.groupby(['i_member_dose', 'j_partner_dose']).size()
    grid_pos_missing = {('%d,%d' % (i, j)): int(v) for (i, j), v in gtab.items()}
    # expected grid cells: per pair-cell expected rows_raw grid; normalise missing fraction per position
    exp_cells = pc_raw.rows_raw.sum()
    grid_pos_expected = {}
    for (i, j), sub in d.groupby(['i_member_dose', 'j_partner_dose']):
        grid_pos_expected['%d,%d' % (i, j)] = int(len(sub))
    grid_pos_missing_frac = {k: rq(grid_pos_missing.get(k, 0) / v) if v else None
                             for k, v in grid_pos_expected.items()}
    # missing by cell and by partner-role
    miss_by_cell = {c: int(v) for c, v in miss_rows.cell_line.value_counts().items()}
    rec_all = pd.concat([
        pd.DataFrame({'batch': d.batch, 'cell': d.cell_line, 'partner': d.drugB_name,
                      'prole': 'B', 'member': d.drugA_name, 'complete_case': d.complete_case}),
        pd.DataFrame({'batch': d.batch, 'cell': d.cell_line, 'partner': d.drugA_name,
                      'prole': 'A', 'member': d.drugB_name, 'complete_case': d.complete_case}),
    ], ignore_index=True)
    miss_by_partner_role = {('%s|%s' % (p, r)): int(v) for (p, r), v in
                            rec_all[~rec_all.complete_case].groupby(['partner', 'prole']).size().items()}

    # ---------- complete-case cohort structure (primary)
    cells_all = sorted(set(d.cell_line))
    drugs_all = sorted(set(d.drugA_name) | set(d.drugB_name))
    jc = pd.read_csv(JAAKS, usecols=['CELL_LINE_NAME'], low_memory=False)
    jcells = sorted({norm(x) for x in jc.CELL_LINE_NAME.unique()})
    target = sorted(set(cells_all) - set(jcells))
    overlap = sorted(set(cells_all) & set(jcells))
    target_set = set(target)

    rec_a = pd.DataFrame({'batch': d_cc.batch, 'cell': d_cc.cell_line, 'partner': d_cc.drugB_name,
                          'prole': 'B', 'pdose': d_cc.db, 'member': d_cc.drugA_name, 'mdose': d_cc.da})
    rec_b = pd.DataFrame({'batch': d_cc.batch, 'cell': d_cc.cell_line, 'partner': d_cc.drugA_name,
                          'prole': 'A', 'pdose': d_cc.da, 'member': d_cc.drugB_name, 'mdose': d_cc.db})
    R = pd.concat([rec_a, rec_b], ignore_index=True).dropna(subset=['pdose', 'mdose'])
    ctx_cols = ['batch', 'cell', 'partner', 'prole']
    ctx = R.groupby(ctx_cols).agg(n_pdose=('pdose', 'nunique'),
                                  n_members=('member', 'nunique'),
                                  n_rows=('pdose', 'size')).reset_index()
    mset = R.groupby(ctx_cols + ['member']).agg(n_pdose=('pdose', 'nunique'),
                                                n_mdose=('mdose', 'nunique'),
                                                n_rows=('pdose', 'size')).reset_index()
    mset = mset.merge(ctx[ctx_cols + ['n_pdose']], on=ctx_cols, suffixes=('', '_ctx'))
    mset['complete'] = (mset.n_pdose == 4) & (mset.n_mdose == 4) & (mset.n_rows == 16)
    member_ctx_total = int(len(mset))
    member_ctx_complete = int(mset.complete.sum())
    member_complete_frac = float(member_ctx_complete / member_ctx_total) if member_ctx_total else 0.0
    cm = mset[mset.complete][ctx_cols + ['member']]
    n_comp = cm.groupby(ctx_cols).size().reset_index(name='n_comp')
    n_comp['pairs'] = n_comp.n_comp * (n_comp.n_comp - 1) // 2
    legal_ctx = n_comp[n_comp.n_comp >= 2].copy()

    def scope(df, batches_keep, cells_keep=None):
        f = df[df.batch.isin(batches_keep)]
        if cells_keep is not None:
            f = f[f.cell.isin(cells_keep)]
        return f

    def summ(frame):
        mcol = ('n_comp' if 'n_comp' in frame.columns else
                ('n_members' if 'n_members' in frame.columns else
                 ('n_usable' if 'n_usable' in frame.columns else None)))
        return {'contexts': int(len(frame)), 'units': int(frame.pairs.sum()),
                'median_members': rq(float(frame[mcol].median())) if (len(frame) and mcol) else None}

    scopes = {
        'all_batches_all_cells': summ(legal_ctx),
        'batch1_all_cells': summ(scope(legal_ctx, [1], None)),
        'batch1_target_cells': summ(scope(legal_ctx, [1], target_set)),
        'batch2_all_cells': summ(scope(legal_ctx, [2], None)),
    }
    # strict same-partner-dose-row units
    row_members = R.groupby(ctx_cols + ['pdose', 'member']).agg(
        n_mdose=('mdose', 'nunique'), n_rows=('mdose', 'size')).reset_index()
    row_full = row_members[(row_members.n_mdose == 4) & (row_members.n_rows == 4)]
    row_ctx = row_full.groupby(ctx_cols + ['pdose']).size().reset_index(name='n_members')
    row_ctx['pairs'] = row_ctx.n_members * (row_ctx.n_members - 1) // 2
    row_ctx = row_ctx[row_ctx.n_members >= 2]
    strict_scopes = {'all_batches_all_cells': summ(row_ctx),
                     'batch1_all_cells': summ(scope(row_ctx, [1], None)),
                     'batch1_target_cells': summ(scope(row_ctx, [1], target_set))}
    b1_legal = scope(legal_ctx, [1], None)
    b1_target_legal = scope(legal_ctx, [1], target_set)
    per_cpr = describe_counts(b1_legal.pairs)
    cm_b1 = cm[cm.batch == 1]
    pair_union = {}
    for (cell, partner, prole), grp in cm_b1.groupby(['cell', 'partner', 'prole']):
        ml = sorted(grp.member)
        s = pair_union.setdefault((cell, partner), set())
        for i in range(len(ml)):
            for j in range(i + 1, len(ml)):
                s.add(tuple(sorted((ml[i], ml[j]))))
    per_cp_union = describe_counts([len(v) for v in pair_union.values()])
    pair_cell_map = {}
    for (cell, partner, prole), grp in cm_b1.groupby(['cell', 'partner', 'prole']):
        ml = sorted(grp.member)
        for i in range(len(ml)):
            for j in range(i + 1, len(ml)):
                pair_cell_map.setdefault((partner, prole, ml[i], ml[j]), set()).add(cell)
    cov_all = describe_counts([len(v) for v in pair_cell_map.values()])
    pair_cell_target = {k: v & target_set for k, v in pair_cell_map.items()}
    cov_target = describe_counts([len(v) for v in pair_cell_target.values()])
    cross_ge3_target = int(sum(1 for v in pair_cell_target.values() if len(v) >= DG1_MIN_CROSS_CELLS))
    cross_ge3_all = int(sum(1 for v in pair_cell_map.values() if len(v) >= DG1_MIN_CROSS_CELLS))
    ctx_per_cell = describe_counts(b1_legal.groupby('cell').size())
    units_per_cell_target = describe_counts(b1_target_legal.groupby('cell').pairs.sum())
    contrib_cells = int(b1_target_legal.cell.nunique())
    # fold design
    folds = {f: [target[i] for i in range(len(target)) if i % 5 == f] for f in range(DSG1_FOLDS)}
    fold_stats = []
    for f in range(DSG1_FOLDS):
        fc = set(folds[f])
        sub = b1_target_legal[b1_target_legal.cell.isin(fc)]
        subrow = scope(row_ctx, [1], fc)
        fold_stats.append({'fold': f, 'n_cells': len(folds[f]), 'cells': folds[f],
                           'n_units': int(sub.pairs.sum()), 'n_contexts': int(len(sub)),
                           'n_strict_row_units': int(subrow.pairs.sum()),
                           'n_partner_role': int(sub.groupby(['partner', 'prole']).ngroups) if len(sub) else 0})
    # ---------- all-available (v1.1 rule) sensitivity -- fully closed definitions
    d_av = d[d.rep_nonnull >= 1].copy()
    R_av = pd.concat([
        pd.DataFrame({'batch': d_av.batch, 'cell': d_av.cell_line, 'partner': d_av.drugB_name,
                      'prole': 'B', 'pdose': d_av.db, 'member': d_av.drugA_name,
                      'mdose': d_av.da, 'rep_nonnull': d_av.rep_nonnull}),
        pd.DataFrame({'batch': d_av.batch, 'cell': d_av.cell_line, 'partner': d_av.drugA_name,
                      'prole': 'A', 'pdose': d_av.da, 'member': d_av.drugB_name,
                      'mdose': d_av.db, 'rep_nonnull': d_av.rep_nonnull}),
    ], ignore_index=True).dropna(subset=['pdose', 'mdose'])
    av_mset = R_av.groupby(ctx_cols + ['member']).agg(
        n_rows=('rep_nonnull', 'size'),
        n_rows_ge2=('rep_nonnull', lambda x: int((x >= 2).sum())),
        n_pdose=('pdose', 'nunique'), n_mdose=('mdose', 'nunique')).reset_index()
    av_mset['frac_ge2'] = av_mset.n_rows_ge2 / av_mset.n_rows
    av_full = av_mset[(av_mset.n_pdose == 4) & (av_mset.n_mdose == 4) & (av_mset.n_rows == 16)]
    av_ctx_num = int(((av_full.frac_ge2 >= V11_MIN_REP_ROWS_FRAC)).sum())
    av_ctx_den = int(len(av_full))
    av_ctx_pass_frac = float(av_ctx_num / av_ctx_den) if av_ctx_den else 0.0
    av_failing = av_full[av_full.frac_ge2 < V11_MIN_REP_ROWS_FRAC]
    av_fail_count = int(len(av_failing))
    av_fail_min_frac = rq(float(av_failing.frac_ge2.min())) if av_fail_count else None
    av_fail_frac_dist = {str(rq(k)): int(v) for k, v in av_failing.frac_ge2.value_counts().sort_index().items()}
    av_usable = av_full[av_full.frac_ge2 >= V11_MIN_REP_ROWS_FRAC]
    av_usable2 = av_usable[av_usable.n_rows_ge2 >= V11_MIN_ROWS_GE2]
    av_n_pairs = av_usable2.groupby(ctx_cols).size().reset_index(name='n_usable')
    av_n_pairs['pairs'] = av_n_pairs.n_usable * (av_n_pairs.n_usable - 1) // 2
    av_legal = av_n_pairs[av_n_pairs.n_usable >= 2].copy()
    av_scopes = {'all_batches_all_cells': summ(av_legal),
                 'batch1_all_cells': summ(scope(av_legal, [1], None)),
                 'batch1_target_cells': summ(scope(av_legal, [1], target_set))}
    # closed row-completeness denominators: full table vs batch1-target analysis population
    raw_b1_target = d[d.batch == 1]
    raw_b1_target = raw_b1_target[raw_b1_target.cell_line.isin(target_set)]
    cc_b1_target = raw_b1_target[raw_b1_target.complete_case]
    row_comp = {
        'full_table': {'denominator_rows': int(n_rows_raw), 'numerator_rows_all4': rows_all4,
                       'frac': rq(rows_all4_frac),
                       'viability2_missing': missing_by_col['viability2'],
                       'viability3_missing': missing_by_col['viability3'],
                       'viability4_missing': missing_by_col['viability4']},
        'batch1_target_population': {'denominator_rows': int(len(raw_b1_target)),
                                     'numerator_rows_all4': int(len(cc_b1_target)),
                                     'frac': rq(len(cc_b1_target) / len(raw_b1_target)) if len(raw_b1_target) else None},
    }
    # ---------- sigma_e execution clause (frozen; not measured in ON2)
    se_unit_factor = math.sqrt(2.0 / 64.0)
    mde_table = {}
    for sg in SIGMA_E_GRID:
        se_unit = sg * se_unit_factor
        mde_table[str(sg)] = {str(ne): rq(MDE_FACTOR * se_unit / math.sqrt(ne)) for ne in N_EFF_GRID}
    conservative_mde = mde_table[str(max(SIGMA_E_GRID))][str(min(N_EFF_GRID))]
    sigma_e_clause = {
        'status_in_on2': 'EXECUTION-STAGE requirement frozen; measured sigma_e/MDE NOT computed in ON2 (metadata-only)',
        'calibration': {
            'cohort_primary': 'complete-case rows (all 4 viability replicates non-null)',
            'cohort_sensitivity': 'all-available rows with >=2 non-null replicates for the row; rows with 1 replicate excluded and counted',
            'half_split': 'sort viability replicates; first ceil(k/2) vs rest; complete-case k=4 -> 2+2; all-available k>=2',
            'member_half_mean': 'mean over 16 grid rows of row half means',
            'delta_half': 'member half mean difference',
            'sigma_e_sq_estimator': 'sum_units(Delta_half1 - Delta_half2)^2 / sum_units denom, denom = sum over both members over 16 rows (1/h1+1/h2)/16^2 (complete-case denom per unit = 2*16*(1/2+1/2)/256 = 1/8)',
            'se_unit': 'sigma_e_hat / sqrt(32)',
            'mde80': '2.801585 * se_unit / sqrt(n_eff)',
            'n_eff': 'held-out cells per fold (6, conservative); technical replicates are precision only and NOT independent n',
            'stop_rule': 'if measured MDE80 > delta_min_provisional=0.10 -> design_invalid: precision_insufficient (stop; no effect run)',
            'reporting': 'calibrated sigma_e, number of units used, excluded rows/units, and measured MDE80 must be reported before any effect protocol',
        },
        'prior_expectation_only': {'sigma_e_grid_borrowed': list(SIGMA_E_GRID),
                                   'mde80_table': mde_table,
                                   'conservative_mde80': conservative_mde,
                                   'conservative_le_delta_min': bool(conservative_mde <= DELTA_MIN_PROVISIONAL),
                                   'note': 'borrowed A0/A2 sigma_e values; NOT qualification evidence and NOT a measured SEM'},
    }
    mi_plan = {
        'status_in_on2': 'frozen plan; NOT run in ON2 (requires response values; metadata-only ON2 does not read them)',
        'm': MI_M, 'seed': MI_SEED,
        'imputation_model': 'row-level viability values imputed from batch/cell/partner/dose-row structure; no cross-endpoint/cross-study borrowing',
        'sensitivity_outputs': ['Delta unit set and mean Delta under MI vs complete-case', 'excluded/added unit counts', 'report alongside complete-case primary; never replaces primary'],
    }

    # ---------- gates
    gates = []
    def add_gate(name, value, threshold, ok, note=''):
        gates.append({'name': name, 'value': value, 'threshold': threshold, 'pass': bool(ok), 'note': note})
    add_gate('DG1_min_units_batch1_target', scopes['batch1_target_cells']['units'], DG1_MIN_UNITS,
             scopes['batch1_target_cells']['units'] >= DG1_MIN_UNITS)
    add_gate('DG1_min_contributing_target_cells', contrib_cells, DG1_MIN_CONTRIB_CELLS,
             contrib_cells >= DG1_MIN_CONTRIB_CELLS)
    add_gate('DG1_min_contexts_batch1_target', scopes['batch1_target_cells']['contexts'], DG1_MIN_CONTEXTS,
             scopes['batch1_target_cells']['contexts'] >= DG1_MIN_CONTEXTS)
    add_gate('DG1_min_cross_contexts_ge3_target', cross_ge3_target, DG1_MIN_CROSS_CONTEXTS,
             cross_ge3_target >= DG1_MIN_CROSS_CONTEXTS)
    add_gate('DG2_complete_member_context_frac', rq(member_complete_frac), DG2_MIN_COMPLETE_FRAC,
             member_complete_frac >= DG2_MIN_COMPLETE_FRAC,
             note='numerator=%d / denominator=%d complete-case member contexts' % (member_ctx_complete, member_ctx_total))
    add_gate('DG3_missingness_disclosure', {'rows_all4_frac': rq(rows_all4_frac),
                                           'missing_by_col': missing_by_col,
                                           'batch3_rows_complete_case': batch_table.get('3', {}).get('rows_complete_case'),
                                           'pair_cells_15rows': n_pc_15,
                                           'assumption': 'no MCAR/MAR assumption; complete-case primary'},
             'complete', True)
    add_gate('DG4_target_cells', len(target), TARGET_N_CELLS, len(target) == TARGET_N_CELLS)
    add_gate('DG4_all_target_cells_contribute', contrib_cells, TARGET_N_CELLS,
             contrib_cells == TARGET_N_CELLS)
    add_gate('DG5_target_overlap_with_jaaks', len(set(target) & set(jcells)), 0,
             len(set(target) & set(jcells)) == 0)
    data_gate_ok = all(g['pass'] for g in gates)
    dg = []
    def add_dg(name, value, threshold, ok, note=''):
        dg.append({'name': name, 'value': value, 'threshold': threshold, 'pass': bool(ok), 'note': note})
    fold_sizes_ok = all(f['n_cells'] == 6 for f in fold_stats)
    add_dg('DSG1_fold_sizes', {str(f['fold']): f['n_cells'] for f in fold_stats}, '6 each', fold_sizes_ok)
    min_units_fold = min(f['n_units'] for f in fold_stats)
    add_dg('DSG1_min_units_per_fold', min_units_fold, DSG1_MIN_UNITS_PER_FOLD,
           min_units_fold >= DSG1_MIN_UNITS_PER_FOLD)
    min_ctx_fold = min(f['n_contexts'] for f in fold_stats)
    add_dg('DSG1_min_contexts_per_fold', min_ctx_fold, DSG1_MIN_CONTEXTS_PER_FOLD,
           min_ctx_fold >= DSG1_MIN_CONTEXTS_PER_FOLD)
    add_dg('DSG1_heldout_disjoint_from_train', True, True, True,
           'by construction: each target cell assigned to exactly one fold')
    add_dg('DSG2a_prior_expectation_conservative_le_delta_min', conservative_mde, DELTA_MIN_PROVISIONAL,
           conservative_mde is not None and conservative_mde <= DELTA_MIN_PROVISIONAL,
           note='borrowed sigma_e prior expectation only; NOT qualification evidence')
    add_dg('DSG2b_execution_sigma_e_clause_frozen', True, True, True,
           note='O\'Neil split-half calibration + measured MDE stop rule frozen; measured MDE deferred to execution')
    add_dg('DSG3_endpoint_frozen', True, True, True,
           note='viability-only complete-case 4x4 grid delta; no dEMAX / no cross-endpoint mixing')
    add_dg('DSG4_independence_boundary', True, True, True,
           note='development-only; no independent confirmation / migration / decision benefit claim')
    design_gate_ok = all(g['pass'] for g in dg)
    if not data_gate_ok:
        verdict = 'data_unavailable'
        cat_map = {'DG1': 'cross_scale_insufficient', 'DG2': 'replicates_missing',
                   'DG3': 'missingness_undisclosed', 'DG4': 'lineage_reaggregation',
                   'DG5': 'lineage_reaggregation'}
        cats = sorted({cat_map[g['name'].split('_')[0]] for g in gates if not g['pass']})
        failure_categories = cats
    elif not design_gate_ok:
        verdict = 'design_invalid'
        failure_categories = ['precision_insufficient']
    else:
        verdict = 'design_frozen_qualified_with_conditions'
        failure_categories = []

    # ---------- v1 comparison (for disclosure only; v1 numbers must NOT be reused)
    v1_dg1 = v1.get('replacement_qualification', {}).get('scopes', {}).get('batch1_target_cells', {})
    v1_folds = [f.get('n_units') for f in v1.get('fold_design', {}).get('fold_stats', [])]
    v1_cross = v1.get('replacement_qualification', {}).get('cross_cell_coverage_batch1_target_cells', {})
    v1_compare = {
        'v1_batch1_target_units': v1_dg1.get('units'),
        'v1_batch1_target_contexts': v1_dg1.get('contexts'),
        'v1_fold_units': v1_folds,
        'v1_complete_member_context_frac': v1.get('replacement_qualification', {}).get('member_context_complete_frac'),
        'v1_cross_ge3_target': v1_cross.get('n_contexts_ge3_cells'),
        'v2_batch1_target_units': scopes['batch1_target_cells']['units'],
        'v2_batch1_target_contexts': scopes['batch1_target_cells']['contexts'],
        'v2_fold_units': [f['n_units'] for f in fold_stats],
        'v2_complete_member_context_frac': rq(member_complete_frac),
        'v2_cross_ge3_target': cross_ge3_target,
        'rule': 'v1 numbers are disclosure-only and must NOT be reused as v2 qualification numbers',
    }

    out = {
        'protocol': {'path_rel': inputs['protocol_on2']['path_rel'],
                     'sha256': inputs['protocol_on2']['sha256'],
                     'version': 'PROTOCOL_ON2 v2 (post-observation revision; NOT pre-registered)'},
        'script': {'path_rel': inputs['script_on2']['path_rel'],
                   'bytes': inputs['script_on2']['bytes'], 'sha256': inputs['script_on2']['sha256']},
        'inputs': inputs,
        'status_of_prior_rounds': {
            'v1_protocol': 'PROTOCOL_ON1 v1 FROZEN (kept; SHA in inputs)',
            'v1_verdict': v1.get('verdict', {}).get('verdict'),
            'v1_failure_categories': v1.get('verdict', {}).get('failure_categories'),
            'amendment_on1_001': 'NOT frozen (ON1-C1: post-observation threshold relaxation); kept as record only',
            'this_protocol': 'v2 = new post-observation protocol revision; requires independent challenge; no effects run',
        },
        'scope': {
            'object': "O'Neil complete-case development-only internal cell holdout",
            'endpoint': 'viability1-4 mean of complete rows; full 4x4 dose grid; complete-case cohort only',
            'not': ['independent confirmation', 'source->target migration', 'decision benefit', 'mechanism',
                    'updater comparison', 'acquisition/Agent', 'new algorithm', 'pre-registration claim for v2'],
            'delta_min_provisional': DELTA_MIN_PROVISIONAL,
            'target_cells': target,
            'jaaks_overlap_excluded': overlap,
            'batch_primary': 1,
        },
        'cohort': {
            'definition': 'rows with all four viability1-4 non-null (complete-case mask only; no response-based selection)',
            'rows_raw': n_rows_raw, 'rows_complete_case': rows_all4,
            'coverage_frac': rq(rows_all4_frac),
            'batch_table': batch_table,
            'pair_cell_rows_distribution_raw': {str(int(k)): int(v) for k, v in
                                                d.groupby(['batch', 'cell_line', 'upair']).size().value_counts().sort_index().items()},
            'pair_cell_rows_distribution_complete_case': pc_rows_cc_dist,
            'pair_cells_partial_lt16': n_pc_partial,
            'pair_cells_15rows': n_pc_15,
            'rows_min_replicates_distribution_raw': rows_min_reps_dist,
            'missing_by_col': missing_by_col,
            'co_missing_patterns': co_missing_pattern,
            'missing_by_cell': miss_by_cell,
            'missing_by_partner_role': miss_by_partner_role,
            'missing_grid_position_counts': grid_pos_missing,
            'missing_grid_position_fractions': grid_pos_missing_frac,
            'batch3_note': 'batch3 rows all dropped by complete-case (viability4 all missing); reported, not used',
        },
        'structure_complete_case': {
            'cells': len(cells_all), 'drugs': len(drugs_all),
            'target_n': len(target), 'jaaks_overlap_n': len(overlap),
            'directed_records': int(len(R)),
            'partner_role_contexts': int(len(ctx)),
            'member_contexts_total': member_ctx_total,
            'member_contexts_complete': member_ctx_complete,
            'member_context_complete_frac': rq(member_complete_frac),
        },
        'replacement_qualification': {
            'definitions': {
                'cohort': 'complete-case',
                'member_context_complete': 'member grid: n_pdose=4, n_mdose=4 and n_rows=16 in complete-case cohort',
                'unit_delta': 'mean of the complete 4x4 grid per member; delta = member_a - member_aprime (sorted names)',
                'partner_role_context': '(batch, cell, partner, partner_role)',
            },
            'scopes': scopes,
            'strict_same_partner_dose_row_scopes': strict_scopes,
            'per_context_pair_counts_batch1': per_cpr,
            'per_cell_partner_union_pair_counts_batch1': per_cp_union,
            'cross_cell_coverage_batch1_all_cells': {'distribution': cov_all, 'n_contexts_ge3_cells': cross_ge3_all},
            'cross_cell_coverage_batch1_target_cells': {'distribution': cov_target,
                                                        'n_contexts_ge3_cells': cross_ge3_target},
            'contexts_per_cell_batch1': ctx_per_cell,
            'units_per_cell_batch1_target_cells': units_per_cell_target,
            'contributing_target_cells': contrib_cells,
        },
        'fold_design': {
            'rule': '30 target cells sorted by normalized name; fold = index % 5; complete-case units',
            'folds': {str(f): folds[f] for f in range(DSG1_FOLDS)},
            'fold_stats': fold_stats,
        },
        'missingness_and_sensitivity': {
            'mechanism_assumption': 'NO MCAR/MAR assumption (metadata-only cannot verify); complete-case primary; row selection only by blank mask, not by response',
            'v1_1_sensitivity_fully_closed': {
                'definitions': {
                    'cohort': 'rows with >=1 non-null technical replicate',
                    'row_value': 'mean over available (>=1) non-null replicates',
                    'member_context_unit': 'one member context = 16 grid rows (4 partner doses x 4 member doses); row-criterion fraction denominator = 16',
                    'member_usable': 'member context 16 rows present AND >=95% of its 16 rows have >=2 non-null replicates AND >=12/16 rows have >=2 non-null replicates',
                    'unit_delta': 'member curve = mean over rows with >=2 non-null reps; delta = usable member pair in same context',
                },
                'row_completeness_denominators': row_comp,
                'context_level_double_95pct': {
                    'numerator_member_contexts_passing_row_criterion': av_ctx_num,
                    'denominator_complete_member_contexts': av_ctx_den,
                    'frac': rq(av_ctx_pass_frac),
                    'threshold': V11_CONTEXT_PASS_FRAC,
                    'min_row_fraction_allowed': V11_MIN_REP_ROWS_FRAC,
                },
                'failing_contexts': {
                    'count_member_contexts_below_row_95pct': av_fail_count,
                    'min_row_fraction_observed': av_fail_min_frac,
                    'row_fraction_distribution_of_failing': av_fail_frac_dist,
                    'wording': ('contexts at 15/16=93.75% do NOT satisfy the in-context >=95% row '
                                'criterion; they are only tolerated by the context-level 95% allowance; '
                                'count reported above'),
                },
                'sensitivity_scopes': av_scopes,
                'note': 'v1.1 is sensitivity ONLY; it does not enter the v2 primary verdict and its numbers are not reused',
            },
            'multiple_imputation_plan': mi_plan,
            'technical_replicates': 'precision/calibration only; never independent n; n_eff = held-out cells (6)',
        },
        'sigma_e_mde': sigma_e_clause,
        'gates': {'data_gates': gates, 'design_gates': dg,
                  'data_gate_passed': bool(data_gate_ok),
                  'design_gate_passed': bool(design_gate_ok)},
        'verdict': {
            'verdict': verdict,
            'failure_categories': failure_categories,
            'post_observation_revision': True,
            'not_pre_registered': True,
            'requires_independent_challenge_before_interpretation': True,
            'conditions': [
                'complete-case cohort (363,090 rows / 98.44% coverage); missing 78/198/5,742; batch3 all dropped; 702 pair-cells with 15 rows; missing mechanism unknown (no MCAR/MAR assumption)',
                'development-only internal cell holdout; NOT independent confirmation / migration / decision benefit / mechanism',
                'viability-only endpoint (mu/muMax, X/X0 are derived, not independent readouts); no DeltaEMAX mixing',
                'technical replicates are precision only, never independent cultures/n; 3 BatchIDs same lab',
                'sigma_e/MDE: borrowed prior is expectation only; O\'Neil split-half calibration and measured MDE are mandatory before any effect protocol; MDE>delta_min -> design_invalid stop',
                'v1.1 all-available and MI are sensitivity only; v1 numbers (363,304 / 71,004-74,580 / 100% / 12,430) are NOT used as v2 qualification numbers',
                'delta_min_provisional=0.10 is a temporary prior, not a decision-utility threshold',
            ],
            'wording_fix': ('v1 remains data_unavailable; v2 is a post-observation protocol revision, not a '
                            'pre-registered protocol; the resource is NOT declared "sufficient" before the '
                            'v2 independent challenge; no effects/updaters are run'),
        },
        'v1_vs_v2_disclosure_only': v1_compare,
        'determinism': {'json_keys_sorted': True, 'timestamps': False,
                        'hash_seed_env': os.environ.get('PYTHONHASHSEED', '')},
    }
    write_json(out, OUTJSON)
    wall = time.time() - t0
    write_json({
        'wall_seconds_total': rq(wall),
        'response_value_use_attestation': 'viability1-4 used only as nullness mask for cohort/missingness; response values never used in any statistic',
        'gpu_hours': None, 'cpu_hours': None, 'peak_rss_mb': None,
        'inputs_bytes_total': sum(v['bytes'] for v in inputs.values()),
        'unknown_values': 'null',
        'memory_bounded_enumeration': {'pair_cell_map_keys': len(pair_cell_map),
                                       'pair_union_keys': len(pair_union)},
    }, OUTUSAGE)
    print('[ON2] verdict=%s data_gate=%s design_gate=%s units(b1,target)=%d folds=%s wall=%.1fs'
          % (verdict, data_gate_ok, design_gate_ok, scopes['batch1_target_cells']['units'],
             [f['n_units'] for f in fold_stats], wall), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
