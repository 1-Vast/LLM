#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R199-ON1: O'Neil development-only internal cell-holdout protocol DRAFT --
qualification/data-preparation runner. NO fitting, NO effect estimation,
NO updater comparison.

Frozen protocol: research/2026-10-27-core-module-design/oneil_dev/PROTOCOL_ON1.md
(v1 FROZEN before any ON1 qualification count).

Metadata-only: reads BatchID / cell / drug names / numeric doses; the four
viability replicate columns are read ONLY for existence/non-null counting and are
never used in any statistic (no means, variances, noise or effect). mu/muMax and
X/X0 are checked for header existence only.

Deterministic: JSON sorted keys, no timestamps, input/script SHA256 recorded;
identical code must produce byte-identical on1.json on rerun.
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
JAaks = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
PROTOCOL_ON1 = os.path.join(OUTDIR, 'PROTOCOL_ON1.md')
PROTOCOL_Q0 = os.path.join(ROOT, 'research', '2026-10-27-core-module-design',
                           'qualification', 'PROTOCOL_Q0.md')
Q0JSON = os.path.join(ROOT, 'research', '2026-10-27-core-module-design',
                      'qualification', 'q0.json')
R199BRIEF = os.path.join(ROOT, 'research', '2026-10-27-innovation-round-r199', 'BRIEF.md')
SCRIPT = os.path.join(OUTDIR, 'on1.py')
OUTJSON = os.path.join(OUTDIR, 'on1.json')
OUTUSAGE = os.path.join(OUTDIR, 'usage_on1.json')

# frozen thresholds (PROTOCOL_ON1 section 3; do not change)
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
ON1_FROZEN = True


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
    print('[ON1] hashing inputs ...', flush=True)
    inputs = {}
    for key, path in (('oneil_combination_workbook', COMP),
                      ('oneil_single_agent_workbook', SINGLE),
                      ('jaaks_original_fitted_cellnames_only', JAaks),
                      ('protocol_q0', PROTOCOL_Q0), ('q0_json', Q0JSON),
                      ('r199_brief', R199BRIEF), ('protocol_on1', PROTOCOL_ON1),
                      ('script_on1', SCRIPT)):
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    # single-agent workbook: metadata-only registration (no response values)
    print('[ON1] registering single-agent workbook metadata ...', flush=True)
    sa = pd.read_excel(SINGLE, sheet_name=0,
                       usecols=['BatchID', 'cell_line', 'drug_name', 'Drug_concentration (µM)'])
    sa_hdr = list(pd.read_excel(SINGLE, sheet_name=0, nrows=0).columns)
    single_meta = {
        'rows': int(len(sa)),
        'cells': int(sa.cell_line.astype(str).nunique()),
        'drugs': int(sa.drug_name.astype(str).nunique()),
        'batches': sorted(int(x) for x in pd.to_numeric(sa.BatchID, errors='coerce').dropna().unique()),
        'n_concentration_values': int(pd.to_numeric(sa['Drug_concentration (µM)'], errors='coerce').nunique()),
        'columns': [str(c) for c in sa_hdr],
        'technical_replicate_columns_in_header': [c for c in sa_hdr if str(c).lower().startswith('viability')],
        'used_in_on1': False,
        'note': 'registered for future control design only; no response values read/used in ON1',
    }
    del sa

    print('[ON1] reading O\'Neil combination workbook (metadata + replicate existence) ...', flush=True)
    usecols = ['BatchID', 'cell_line', 'drugA_name', 'drugA Conc (µM)',
               'drugB_name', 'drugB Conc (µM)'] + DG3_REPLICATE_COLS
    d = pd.read_excel(COMP, sheet_name='combination response', usecols=usecols)
    hdr = [str(c) for c in pd.read_excel(COMP, sheet_name='combination response', nrows=0).columns]
    n_rows_raw = int(len(d))
    # replicate existence / nullness only (no values used anywhere below)
    replicate_nonnull = {c: int(d[c].notna().sum()) for c in DG3_REPLICATE_COLS}
    missing_by_col = {c: int(n_rows_raw - replicate_nonnull[c]) for c in DG3_REPLICATE_COLS}
    d['rep_nonnull'] = d[DG3_REPLICATE_COLS].notna().sum(axis=1)
    rows_all4 = int((d.rep_nonnull == 4).sum())
    rows_all4_frac = float(rows_all4 / n_rows_raw) if n_rows_raw else 0.0
    rows_min_reps_dist = {str(int(k)): int(v) for k, v in d.rep_nonnull.value_counts().sort_index().items()}
    drop_cols = [c for c in DG3_REPLICATE_COLS]
    d = d.drop(columns=drop_cols).dropna(subset=['cell_line', 'drugA_name', 'drugB_name'])
    for c in ('cell_line', 'drugA_name', 'drugB_name'):
        d[c] = d[c].astype(str).map(norm)
    d['batch'] = d.BatchID.astype(int)
    d['da'] = pd.to_numeric(d['drugA Conc (µM)'], errors='coerce').round(9)
    d['db'] = pd.to_numeric(d['drugB Conc (µM)'], errors='coerce').round(9)
    d['upair'] = [tuple(sorted((a, b))) for a, b in zip(d.drugA_name, d.drugB_name)]
    n_rows = int(len(d))
    cells_all = sorted(set(d.cell_line))
    drugs_all = sorted(set(d.drugA_name) | set(d.drugB_name))
    batches = sorted(int(x) for x in d.batch.unique())
    print('[ON1] rows=%d cells=%d drugs=%d batches=%s (%.1fs)'
          % (n_rows, len(cells_all), len(drugs_all), batches, time.time() - t0), flush=True)

    # ---------- structure
    pc = d.groupby(['cell_line', 'upair']).agg(rows=('batch', 'size'),
                                               nb=('batch', 'nunique'),
                                               na=('da', 'nunique'), nb_dose=('db', 'nunique'),
                                               batches=('batch', lambda s: tuple(sorted(set(s))))).reset_index()
    pair_cell_rows_dist = {str(k): int(v) for k, v in pc.rows.value_counts().items()}
    pair_cell_batch_sets = {str(k): int(v) for k, v in pc.batches.value_counts().items()}
    per_batch = {}
    for bt in batches:
        sub = d[d.batch == bt]
        per_batch[str(bt)] = {
            'rows': int(len(sub)),
            'cells': int(sub.cell_line.nunique()),
            'pair_cells': int(sub.groupby(['cell_line', 'upair']).ngroups),
            'drugs_as_A': int(sub.drugA_name.nunique()),
            'drugs_as_B': int(sub.drugB_name.nunique()),
        }
    grid_dist = {('na=%d,nb=%d,rows=%d' % (k[0], k[1], k[2])): int(v)
                 for k, v in pc.groupby(['na', 'nb_dose', 'rows']).size().to_dict().items()}
    grid_complete_frac = float(((pc.na >= 4) & (pc.nb_dose >= 4)).mean())
    # role orientation per unordered pair (each pair appears with a single A/B orientation)
    role_pairs = d.groupby('upair').apply(lambda g: tuple(sorted(set(zip(g.drugA_name, g.drugB_name)))),
                                          include_groups=False)
    pairs_multi_orientation = int(sum(1 for v in role_pairs if len(v) > 1))
    # partner dose sets per (batch, cell, partner, role) and role consistency
    pds = d.groupby(['batch', 'cell_line', 'drugB_name']).agg(
        n=('db', 'nunique')).reset_index()  # B-role partner doses
    pds_a = d.groupby(['batch', 'cell_line', 'drugA_name']).agg(
        n=('da', 'nunique')).reset_index()
    partner_role_dose_uniform = bool(pds.n.eq(4).all() and pds_a.n.eq(4).all())

    # ---------- directed records (partner, role) -> members
    rec_a = pd.DataFrame({'batch': d.batch, 'cell': d.cell_line, 'partner': d.drugB_name,
                          'prole': 'B', 'pdose': d.db, 'member': d.drugA_name, 'mdose': d.da,
                          'rep_nonnull': d.rep_nonnull})
    rec_b = pd.DataFrame({'batch': d.batch, 'cell': d.cell_line, 'partner': d.drugA_name,
                          'prole': 'A', 'pdose': d.da, 'member': d.drugB_name, 'mdose': d.db,
                          'rep_nonnull': d.rep_nonnull})
    R = pd.concat([rec_a, rec_b], ignore_index=True).dropna(subset=['pdose', 'mdose'])
    ctx_cols = ['batch', 'cell', 'partner', 'prole']
    ctx = R.groupby(ctx_cols).agg(n_pdose=('pdose', 'nunique'),
                                  n_members=('member', 'nunique'),
                                  n_rows=('pdose', 'size')).reset_index()
    mset = R.groupby(ctx_cols + ['member']).agg(n_pdose=('pdose', 'nunique'),
                                                n_mdose=('mdose', 'nunique'),
                                                n_rows=('pdose', 'size')).reset_index()
    mset = mset.merge(ctx[ctx_cols + ['n_pdose']], on=ctx_cols, suffixes=('', '_ctx'))
    mset['complete'] = (mset.n_pdose == mset.n_pdose_ctx) & (mset.n_rows == mset.n_pdose * mset.n_mdose)
    # replicate availability per complete member context (counts only; no response values)
    mrep = R.groupby(ctx_cols + ['member']).agg(
        n_rows=('rep_nonnull', 'size'),
        n_rows_ge2=('rep_nonnull', lambda x: int((x >= 2).sum())),
        min_rep=('rep_nonnull', 'min')).reset_index()
    mset2 = mset.merge(mrep, on=ctx_cols + ['member'], suffixes=('', '_rep'))
    mset2['frac_rows_ge2'] = mset2.n_rows_ge2 / mset2.n_rows_rep
    complete_ctx_rep = mset2[mset2.complete]
    frac_ctx_ge2_ge95 = float((complete_ctx_rep.frac_rows_ge2 >= 0.95).mean()) if len(complete_ctx_rep) else 0.0
    min_rows_ge2_frac = rq(float(complete_ctx_rep.frac_rows_ge2.min())) if len(complete_ctx_rep) else None
    complete_member_rows = int(mset.complete.sum())
    complete_frac = float(mset.complete.mean()) if len(mset) else 0.0
    # complete members per context -> coarse replacement counts
    cm = mset[mset.complete][ctx_cols + ['member']]
    n_comp = cm.groupby(ctx_cols).size().reset_index(name='n_comp')
    n_comp['pairs'] = n_comp.n_comp * (n_comp.n_comp - 1) // 2
    legal_ctx = n_comp[n_comp.n_comp >= 2].copy()

    # Jaaks overlap / target cells
    jc = pd.read_csv(JAaks, usecols=['CELL_LINE_NAME'], low_memory=False)
    jcells = sorted({norm(x) for x in jc.CELL_LINE_NAME.unique()})
    overlap = sorted(set(cells_all) & set(jcells))
    target = sorted(set(cells_all) - set(jcells))
    target_set = set(target)

    def subset_stats(frame, label, cells_keep=None):
        f = frame
        if cells_keep is not None:
            f = f[f.cell.isin(cells_keep)]
        units = int(f.pairs.sum()) if 'pairs' in f else 0
        mcol = 'n_comp' if 'n_comp' in f.columns else ('n_members' if 'n_members' in f.columns else None)
        med = rq(float(f[mcol].median())) if (len(f) and mcol) else None
        return {'label': label, 'contexts': int(len(f)), 'units': units, 'median_members': med}

    def scope(df_ctx, batches_keep, cells_keep):
        f = df_ctx[df_ctx.batch.isin(batches_keep)]
        if cells_keep is not None:
            f = f[f.cell.isin(cells_keep)]
        return f

    scopes = {
        'all_batches_all_cells': subset_stats(legal_ctx, 'all'),
        'batch1_all_cells': subset_stats(scope(legal_ctx, [1], None), 'b1'),
        'batch1_target_cells': subset_stats(scope(legal_ctx, [1], target_set), 'b1_target'),
    }
    # strict row-level units (same partner dose row, full member curve)
    row_members = R.groupby(ctx_cols + ['pdose', 'member']).agg(
        n_mdose=('mdose', 'nunique'), n_rows=('mdose', 'size')).reset_index()
    row_full = row_members[row_members.n_mdose == row_members.n_rows]
    row_ctx = row_full.groupby(ctx_cols + ['pdose']).size().reset_index(name='n_members')
    row_ctx['pairs'] = row_ctx.n_members * (row_ctx.n_members - 1) // 2
    row_ctx = row_ctx[row_ctx.n_members >= 2]
    strict_scopes = {
        'all_batches_all_cells': subset_stats(row_ctx, 'all'),
        'batch1_all_cells': subset_stats(scope(row_ctx, [1], None), 'b1'),
        'batch1_target_cells': subset_stats(scope(row_ctx, [1], target_set), 'b1_target'),
    }
    # per (cell,partner,role) replaceable-pair distribution + per (cell,partner) union
    b1_legal = scope(legal_ctx, [1], None)
    per_cpr = describe_counts(b1_legal.pairs)
    # build actual member-pair sets for per-(cell,partner) union (bounded: 2791 contexts)
    cm_b1 = cm[cm.batch == 1]
    pair_union = {}
    for (cell, partner, prole), grp in cm_b1.groupby(['cell', 'partner', 'prole']):
        ml = sorted(grp.member)
        s = pair_union.setdefault((cell, partner), set())
        for i in range(len(ml)):
            for j in range(i + 1, len(ml)):
                s.add(tuple(sorted((ml[i], ml[j]))))
    per_cp_union = describe_counts([len(v) for v in pair_union.values()])
    # cross-cell coverage (batch1, all cells; and target-only) from complete members
    pair_cell_map = {}
    for (cell, partner, prole), grp in cm_b1.groupby(['cell', 'partner', 'prole']):
        ml = sorted(grp.member)
        for i in range(len(ml)):
            for j in range(i + 1, len(ml)):
                pair_cell_map.setdefault((partner, prole, ml[i], ml[j]), set()).add(cell)
    cov_all = describe_counts([len(v) for v in pair_cell_map.values()])
    cov_thresholds = {str(t): int(sum(1 for v in pair_cell_map.values() if len(v) >= t))
                      for t in (1, 2, 3, 6, 10)}
    pair_cell_target = {k: v & target_set for k, v in pair_cell_map.items()}
    cov_target = describe_counts([len(v) for v in pair_cell_target.values()])
    cross_ctx_ge3_target = int(sum(1 for v in pair_cell_target.values() if len(v) >= DG1_MIN_CROSS_CELLS))
    cross_ctx_ge3_all = int(sum(1 for v in pair_cell_map.values() if len(v) >= DG1_MIN_CROSS_CELLS))

    # contexts per cell (batch1) and per-target-cell units
    ctx_per_cell = describe_counts(b1_legal.groupby('cell').size())
    unit_per_cell = describe_counts(b1_legal.groupby('cell').pairs.sum())
    b1_target_legal = scope(legal_ctx, [1], target_set)
    target_unit_per_cell = describe_counts(b1_target_legal.groupby('cell').pairs.sum())
    contrib_cells = int(b1_target_legal.cell.nunique())

    # ---------- 5-fold design (30 target cells, sorted normalized name, index%5)
    folds = {f: [target[i] for i in range(len(target)) if i % 5 == f] for f in range(DSG1_FOLDS)}
    fold_stat = []
    for f in range(DSG1_FOLDS):
        fc = set(folds[f])
        sub = b1_target_legal[b1_target_legal.cell.isin(fc)]
        subrow = scope(row_ctx, [1], fc)
        n_ctx = int(len(sub))
        fold_stat.append({
            'fold': f, 'n_cells': len(folds[f]), 'cells': folds[f],
            'n_units': int(sub.pairs.sum()),
            'n_contexts': n_ctx,
            'n_strict_row_units': int(subrow.pairs.sum()),
            'n_strict_row_contexts': int(len(subrow)),
            'n_partner_role': int(sub.groupby(['partner', 'prole']).ngroups) if n_ctx else 0,
        })

    # ---------- MDE prior
    se_unit_factor = math.sqrt(2.0 / (4.0 * 4.0 * 4.0))  # sqrt(2/64) = 1/sqrt(32)
    mde_table = {}
    for sg in SIGMA_E_GRID:
        se_unit = sg * se_unit_factor
        mde_table[str(sg)] = {}
        for ne in N_EFF_GRID:
            mde_table[str(sg)][str(ne)] = rq(MDE_FACTOR * se_unit / math.sqrt(ne))
    required_neff = {}
    for sg in SIGMA_E_GRID:
        se_unit = sg * se_unit_factor
        needed = (MDE_FACTOR * se_unit / DELTA_MIN_PROVISIONAL) ** 2
        required_neff[str(sg)] = {'for_mde80_le_0.10': rq(needed),
                                  'for_mde80_le_0.15': rq((MDE_FACTOR * se_unit / 0.15) ** 2)}
    conservative_mde = mde_table[str(max(SIGMA_E_GRID))][str(min(N_EFF_GRID))]

    # ---------- gates
    gates = []
    def add_gate(name, value, threshold, ok, note=''):
        gates.append({'name': name, 'value': value, 'threshold': threshold,
                      'pass': bool(ok), 'note': note})
    add_gate('DG1_min_units_batch1_target', scopes['batch1_target_cells']['units'], DG1_MIN_UNITS,
             scopes['batch1_target_cells']['units'] >= DG1_MIN_UNITS)
    add_gate('DG1_min_contributing_target_cells', contrib_cells, DG1_MIN_CONTRIB_CELLS,
             contrib_cells >= DG1_MIN_CONTRIB_CELLS)
    add_gate('DG1_min_contexts_batch1_target', scopes['batch1_target_cells']['contexts'], DG1_MIN_CONTEXTS,
             scopes['batch1_target_cells']['contexts'] >= DG1_MIN_CONTEXTS)
    add_gate('DG1_min_cross_contexts_ge3_target', cross_ctx_ge3_target, DG1_MIN_CROSS_CONTEXTS,
             cross_ctx_ge3_target >= DG1_MIN_CROSS_CONTEXTS)
    add_gate('DG2_complete_member_frac', rq(complete_frac), DG2_MIN_COMPLETE_FRAC,
             complete_frac >= DG2_MIN_COMPLETE_FRAC)
    add_gate('DG2_numeric_dose_columns_present', True, True, True)
    add_gate('DG2_partner_role_dose_uniform', partner_role_dose_uniform, True, partner_role_dose_uniform)
    replicate_ok = all(replicate_nonnull[c] == n_rows_raw for c in DG3_REPLICATE_COLS)
    add_gate('DG3_replicate_columns_present_and_nonnull', replicate_nonnull, n_rows_raw, replicate_ok,
             note='literal frozen DG3: each viability column non-null count must equal row count')
    revised_dg3 = bool(rows_all4_frac >= 0.95 and frac_ctx_ge2_ge95 >= 0.95)
    add_gate('DG3_revised_criterion_sensitivity_NOT_A_GATE', {
        'rows_with_all4_nonnull': rows_all4,
        'rows_all4_frac': rq(rows_all4_frac),
        'complete_member_contexts_with_ge95pct_rows_ge2_frac': rq(frac_ctx_ge2_ge95),
        'min_frac_rows_with_ge2_reps_over_contexts': min_rows_ge2_frac,
        'would_pass_revised_criterion': revised_dg3,
    }, 'sensitivity', True,
        note='AMENDMENT_ON1-001 proposal only; NOT used for the v1 verdict')
    add_gate('DG4_target_cells', len(target), TARGET_N_CELLS, len(target) == TARGET_N_CELLS)
    add_gate('DG4_all_target_cells_contribute', contrib_cells, TARGET_N_CELLS,
             contrib_cells == TARGET_N_CELLS)
    add_gate('DG5_target_overlap_with_jaaks', len(set(target) & set(jcells)), 0,
             len(set(target) & set(jcells)) == 0)
    data_gate_ok = all(g['pass'] for g in gates)
    # design gates
    dg = []
    def add_dg(name, value, threshold, ok, note=''):
        dg.append({'name': name, 'value': value, 'threshold': threshold,
                   'pass': bool(ok), 'note': note})
    fold_sizes_ok = all(f['n_cells'] == 6 for f in fold_stat)
    add_dg('DSG1_fold_sizes', {str(f['fold']): f['n_cells'] for f in fold_stat}, '6 each', fold_sizes_ok)
    min_units_fold = min(f['n_units'] for f in fold_stat)
    add_dg('DSG1_min_units_per_fold', min_units_fold, DSG1_MIN_UNITS_PER_FOLD,
           min_units_fold >= DSG1_MIN_UNITS_PER_FOLD)
    min_ctx_fold = min(f['n_contexts'] for f in fold_stat)
    add_dg('DSG1_min_contexts_per_fold', min_ctx_fold, DSG1_MIN_CONTEXTS_PER_FOLD,
           min_ctx_fold >= DSG1_MIN_CONTEXTS_PER_FOLD)
    add_dg('DSG1_heldout_disjoint_from_train', True, True, True,
           'by construction: cells assigned to exactly one fold')
    add_dg('DSG2_mde80_conservative_le_delta_min', conservative_mde, DELTA_MIN_PROVISIONAL,
           conservative_mde is not None and conservative_mde <= DELTA_MIN_PROVISIONAL)
    add_dg('DSG3_endpoint_frozen', True, True, True,
           'viability-only full-4x4-grid delta; no dEMAX / no cross-endpoint mixing')
    add_dg('DSG4_independence_boundary', True, True, True,
           'development-only; no independent confirmation / migration / decision benefit claim')
    design_gate_ok = all(g['pass'] for g in dg)
    if not data_gate_ok:
        verdict = 'data_unavailable'
        cat_map = {
            'DG1': 'cross_scale_insufficient', 'DG2': 'exposure_unverifiable',
            'DG3': 'replicates_missing', 'DG4': 'lineage_reaggregation',
            'DG5': 'lineage_reaggregation',
        }
        cats = []
        for g in gates:
            if not g['pass']:
                cats.append(cat_map[g['name'].split('_')[0]])
        failure_categories = sorted(set(cats))
    elif not design_gate_ok:
        verdict = 'design_invalid'
        failure_categories = ['precision_insufficient']
    else:
        verdict = 'design_frozen_qualified_with_conditions'
        failure_categories = []

    out = {
        'protocol': {'path_rel': inputs['protocol_on1']['path_rel'],
                     'sha256': inputs['protocol_on1']['sha256'], 'version': 'PROTOCOL_ON1 v1 FROZEN'},
        'script': {'path_rel': inputs['script_on1']['path_rel'],
                   'bytes': inputs['script_on1']['bytes'], 'sha256': inputs['script_on1']['sha256']},
        'inputs': inputs,
        'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                        'pandas': pd.__version__},
        'scope': {
            'object': "O'Neil development-only internal cell holdout (R199-Q0 only qualified_with_conditions candidate)",
            'not': ['independent confirmation', 'source->target migration', 'decision benefit',
                    'mechanism', 'updater comparison', 'acquisition/Agent', 'new algorithm'],
            'endpoint': 'viability1-4 technical-replicate mean of the combination response (full 4x4 dose grid)',
            'endpoint_limits': ['viability-derived only; mu/muMax and X/X0 are derived and not independent readouts',
                                'technical replicates != independent cultures; BatchIDs same lab',
                                'do not mix with Jaaks SYNERGY_DELTA_EMAX endpoint'],
            'delta_min_provisional': DELTA_MIN_PROVISIONAL,
        },
        'structure': {
            'combination_rows_raw': n_rows_raw,
            'rows_used_metadata': n_rows,
            'cells': len(cells_all), 'drugs': len(drugs_all), 'batches': batches,
            'batch_table': per_batch,
            'pair_cell_rows_distribution': pair_cell_rows_dist,
            'pair_cell_batch_sets': pair_cell_batch_sets,
            'grid_shape_distribution': grid_dist,
            'grid_complete_4x4_frac': rq(grid_complete_frac),
            'pairs_multi_orientation': pairs_multi_orientation,
            'partner_role_dose_uniform': partner_role_dose_uniform,
            'replicate_columns_in_header': [c for c in hdr if str(c).lower().startswith('viability')],
            'replicate_nonnull_counts': replicate_nonnull,
            'replicate_missing_counts': missing_by_col,
            'rows_with_all4_replicates': rows_all4,
            'rows_all4_frac': rq(rows_all4_frac),
            'rows_min_available_replicates_distribution': rows_min_reps_dist,
            'complete_member_contexts_with_ge95pct_rows_ge2_frac': rq(frac_ctx_ge2_ge95),
            'min_frac_rows_with_ge2_reps_over_member_contexts': min_rows_ge2_frac,
            'mu_max_column_present': bool(any(str(c).strip() == 'mu/muMax' for c in hdr)),
            'x0_column_present': bool(any(str(c).strip() == 'X/X0' for c in hdr)),
            'exposure_time_column_present': bool(any('time' in str(c).lower() for c in hdr)),
            'assay_method_column_present': bool(any(('assay' in str(c).lower()) or ('method' in str(c).lower()) for c in hdr)),
        },
        'cells': {
            'all': cells_all,
            'jaaks_overlap': overlap,
            'jaaks_overlap_frac': rq(len(overlap) / len(cells_all)) if cells_all else None,
            'target_nonoverlap': target,
            'target_n': len(target),
        },
        'replacement_qualification': {
            'definitions': {
                'partner_role_context': '(batch, cell, partner, partner_role) with a single partner dose set',
                'member': 'drug co-measured with partner in the other role at that context',
                'unit_delta': 'delta(c, partner, role, {a,a\'}) = grid_mean(c,a,partner) - grid_mean(c,a\',partner)',
                'member_pair': 'unordered member pair {a,a\'} in one context',
                'sign_convention': 'member pair ordered by normalized name ascending; first minus second',
            },
            'directed_records': int(len(R)),
            'partner_role_contexts': int(len(ctx)),
            'partner_role_contexts_n_pdose_dist': {str(k): int(v) for k, v in ctx.n_pdose.value_counts().items()},
            'member_contexts': int(len(mset)),
            'member_contexts_complete': complete_member_rows,
            'member_context_complete_frac': rq(complete_frac),
            'member_context_rows_complete_check': {str(k): int(v) for k, v in mset[mset.complete].n_rows.value_counts().items()},
            'scopes': scopes,
            'strict_same_partner_dose_row_scopes': strict_scopes,
            'per_context_pair_counts_batch1': per_cpr,
            'per_cell_partner_union_pair_counts_batch1': per_cp_union,
            'cross_cell_coverage_batch1_all_cells': {
                'distribution': cov_all,
                'threshold_counts': cov_thresholds,
                'n_contexts_ge3_cells': cross_ctx_ge3_all,
            },
            'cross_cell_coverage_batch1_target_cells': {
                'distribution': cov_target,
                'n_contexts_ge3_cells': cross_ctx_ge3_target,
            },
            'contexts_per_cell_batch1': ctx_per_cell,
            'units_per_cell_batch1_all_cells': unit_per_cell,
            'units_per_cell_batch1_target_cells': target_unit_per_cell,
            'contributing_target_cells': contrib_cells,
        },
        'fold_design': {
            'rule': '30 non-overlap target cells sorted by normalized name; fold = index % 5; held-out cells disjoint from training cells',
            'folds': {str(f): folds[f] for f in range(DSG1_FOLDS)},
            'fold_stats': fold_stat,
        },
        'mde_prior': {
            'formula': 'SE_unit = sigma_e*sqrt(2/(4*4*4)) = sigma_e/sqrt(32); MDE80 = 2.801585*SE_unit/sqrt(n_eff)',
            'per_unit_wells': '4 partner doses x 4 member doses x 4 technical replicates = 64 wells per member; delta of two members',
            'n_eff_definition': 'n_eff = number of held-out cells per fold (6, conservative cluster count); grid 12/24/30 reported',
            'sigma_e_grid_borrowed': list(SIGMA_E_GRID),
            'sigma_e_source': 'borrowed from prior rounds (A0 R4 0.041; A2 single-key 0.058; A2 per-observation 0.109) - NOT measured on O\'Neil in ON1',
            'n_eff_grid': list(N_EFF_GRID),
            'mde80_table': mde_table,
            'required_n_eff_for_target': required_neff,
            'conservative_mde80_for_gate': {'sigma_e': max(SIGMA_E_GRID), 'n_eff': min(N_EFF_GRID),
                                            'mde80': conservative_mde},
            'limitations': ['sigma_e borrowed and not certified for O\'Neil',
                            'well-level independence across plate/batch not established; technical replicates only',
                            'must be replaced by O\'Neil viability1-4 split-half calibration in the execution protocol (noise calibration != effect)'],
        },
        'single_agent_workbook_metadata': single_meta,
        'gates': {'data_gates': gates, 'design_gates': dg,
                  'data_gate_passed': bool(data_gate_ok),
                  'design_gate_passed': bool(design_gate_ok)},
        'verdict': {
            'verdict': verdict,
            'failure_categories': failure_categories,
            'conditions': [
                'development-only internal cell holdout; not independent confirmation / migration / decision benefit / mechanism',
                'viability-only endpoint (mu/muMax, X/X0 are derived; no orthogonal functional readout)',
                'technical replicates only; 3 BatchIDs are same-lab and NOT certified independent cultures; batch1-only primary analysis',
                '9/39 cells overlap Jaaks and are EXCLUDED from target set (30 non-overlap cells)',
                'no O\'Neil single-agent reference used; cannot be converted into Jaaks DeltaEMAX and must not be mixed with it',
                'no exposure-time / assay-method columns: legal exposure is only partially verifiable (conditional)',
                'delta_min_provisional=0.10 is a temporary prior, not a decision-utility threshold',
            ],
            'recommendation': ('DO NOT freeze v1 as-is: the literal frozen DG3 data gate fails on '
                               'technical-replicate completeness (viability2/3/4 blanks). Recommend a '
                               'pre-registered AMENDMENT_ON1-001 revising DG3 (rows all-4 completeness '
                               '>=95% AND complete member contexts with >=95% rows having >=2 non-null '
                               'technical replicates), then freeze v1.1; still DO NOT RUN effects/updaters; '
                               'execution requires a separate effect protocol + independent challenge'),
        },
        'response_value_use_attestation': {
            'effect_estimation': False,
            'model_fitting': False,
            'updater_comparison': False,
            'response_columns_read': 'viability1-4 read only for non-null existence counts; values never used in any statistic',
            'mu_max_x0_read': 'header existence only',
            'no_new_data': True,
            'no_network': True,
        },
        'frozen_thresholds': {
            'DG1_min_units': DG1_MIN_UNITS, 'DG1_min_contributing_cells': DG1_MIN_CONTRIB_CELLS,
            'DG1_min_contexts': DG1_MIN_CONTEXTS,
            'DG1_min_cross_contexts': DG1_MIN_CROSS_CONTEXTS,
            'DG1_min_cross_cells': DG1_MIN_CROSS_CELLS,
            'DG2_min_complete_frac': DG2_MIN_COMPLETE_FRAC,
            'DSG1_folds': DSG1_FOLDS, 'DSG1_min_units_per_fold': DSG1_MIN_UNITS_PER_FOLD,
            'DSG1_min_contexts_per_fold': DSG1_MIN_CONTEXTS_PER_FOLD,
            'delta_min_provisional': DELTA_MIN_PROVISIONAL, 'mde_factor': MDE_FACTOR,
            'sigma_e_grid': list(SIGMA_E_GRID), 'n_eff_grid': list(N_EFF_GRID),
            'target_n_cells': TARGET_N_CELLS,
        },
        'determinism': {'json_keys_sorted': True, 'timestamps': False,
                        'hash_seed_env': os.environ.get('PYTHONHASHSEED', '')},
    }
    write_json(out, OUTJSON)
    wall = time.time() - t0
    usage = {
        'wall_seconds_total': rq(wall),
        'n_replicate_calibration_note': 'no response statistics computed',
        'gpu_hours': None, 'cpu_hours': None, 'peak_rss_mb': None,
        'memory_bounded_enumeration': {'pair_cell_map_keys': len(pair_cell_map),
                                       'pair_union_keys': len(pair_union)},
        'inputs_bytes_total': sum(v['bytes'] for v in inputs.values()),
        'unknown_values': 'null',
    }
    write_json(usage, OUTUSAGE)
    print('[ON1] verdict=%s data_gate=%s design_gate=%s wall=%.1fs'
          % (verdict, data_gate_ok, design_gate_ok, wall), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
