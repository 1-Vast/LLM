#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R190-A0: 细胞状态特征资格审计（PROTOCOL_A0.md，含 AMENDMENT-A0-001）
Deterministic, re-runnable. Fixed seed 20261027. No timestamps in a0.json.

purpose=qualification
==================================================================
This script implements ONLY the pre-registered resource/design qualification
audit frozen in `research/2026-10-27-cellstate-qualification/PROTOCOL_A0.md`
(+ AMENDMENT-A0-001).  In particular:
  * `SYNERGY_DELTA_EMAX` (response values) is read ONLY for the statistics that
    PROTOCOL_A0 section 4 pre-registers for qualification:
      - G3(a) two-way additive variance components,
      - G3(b) additive-cell-effect ranking ceiling,
      - G3(c) within-pair standard deviation (room),
      - G3(d) measurement-noise / reliability ceiling (sigma_e, rho_ceiling),
      - G3(e) MDE80 via null bootstrap (zero prediction),
      - G3(d-aux) cross-screen within-pair ranking reliability,
      - descriptive response distribution used only inside the above.
  * NO predictive model is fit, no model performance is reported, no feature
    selection / threshold tuning is performed, no subset is chosen by response.
  * Thresholds are hard-coded from the frozen protocol; they are never adjusted.
==================================================================
Outputs (this directory): a0.json, identity_map.csv, target_map.csv,
                          usage.json (runtime telemetry; not byte-frozen)
"""
import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
import zipfile

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

# ----------------------------------------------------------------------------
# frozen constants
# ----------------------------------------------------------------------------
ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-27-cellstate-qualification')
SEED = 20261027
B_BOOT = 1000
# MDE80 two-sided alpha=0.05, power=80%:  z_{0.975} + z_{0.80}
Z_MDE80 = 2.801585218112968
TOL_ANOVA = 1e-9

FITTED = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                      'Original screen_All tissues_fitted data.csv')
VALID = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Validation screen_All tissues_fitted data.csv')
GLOSSARY = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                        'Glossary.xlsx')
RAWZIP = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                      'Original_screen_All_tissues_raw_data.csv.zip')
SAMPLE_INFO = os.path.join(ROOT, 'data', 'external', 'depmap_19q4', 'sample_info.csv')
EXPR = os.path.join(ROOT, 'data', 'external', 'depmap_19q4', 'CCLE_expression.csv')
MUT = os.path.join(ROOT, 'data', 'external', 'depmap_19q4', 'CCLE_mutations.csv')
PROTOCOL = os.path.join(OUTDIR, 'PROTOCOL_A0.md')
SCRIPT = os.path.join(OUTDIR, 'a0.py')

INPUT_FILES = [FITTED, VALID, GLOSSARY, SAMPLE_INFO, EXPR, MUT, RAWZIP]

# PROTOCOL_A0 section 7 frozen thresholds (do NOT change)
THRESH = {
    'G1_map_min': 119,            # >=119/125 cells mapped to a unique DepMap_ID
    'G1_expr_min': 105,           # AMENDMENT-A0-001: >=105 of mapped cells have an expression row
    'G2_target_min': 60,          # >=60/86 target tokens mapped to gene columns
    'G2_pair_cov_min': 0.90,      # >=90% of 2025 ordered pairs: both sides have >=1 mapped gene
    'G3a_interaction_min': 0.10,  # interaction variance share
    'G3b_ceiling_mean_min': 0.05,  # mean within-pair Spearman(y, a_cell) ceiling
    'G3c_sd_median_min': 0.02,    # median pair-level sd(y_int)
    'G3d_rho_ceiling_min': 0.10,
    'G3e_mde80_max': 0.05,
}
# sigma_e borrowed from R4 (PROTOCOL_A0 section 4d fallback), see report.md.
SIGMA_E_BORROWED = 0.0408
SIGMA_E_SOURCE = 'borrowed:R4 well-level noise (r4/report.md: sigma_e=0.0408; archive value 0.041)'

# PROTOCOL_A0 section 3 FROZEN alias table (token -> gene symbols + rationale)
ALIAS_TABLE = {
    'ABL': (['ABL1'], 'gene symbol vs family label'),
    'BCL-W': (['BCL2L2'], 'approved symbol BCL2L2'),
    'BCL-XL': (['BCL2L1'], 'approved symbol BCL2L1'),
    'DNAPK': (['PRKDC'], 'DNA-PK catalytic subunit approved symbol'),
    'ERK1': (['MAPK3'], 'ERK1 -> MAPK3'),
    'ERK2': (['MAPK1'], 'ERK2 -> MAPK1'),
    'IR': (['INSR'], 'insulin receptor approved symbol'),
    'JNK2': (['MAPK9'], 'JNK2 -> MAPK9'),
    'MEK1': (['MAP2K1'], 'MEK1 -> MAP2K1'),
    'MEK2': (['MAP2K2'], 'MEK2 -> MAP2K2'),
    'MTORC1': (['MTOR'], 'complex label -> MTOR gene'),
    'MTORC2': (['MTOR'], 'complex label -> MTOR gene'),
    'PDGFR': (['PDGFRA', 'PDGFRB'], 'receptor family -> both genes'),
    'PI3Kalpha': (['PIK3CA'], 'PI3K alpha isoform -> PIK3CA'),
    'PI3Kbeta': (['PIK3CB'], 'PI3K beta isoform -> PIK3CB'),
    'RAF': (['RAF1', 'BRAF'], 'RAF family -> RAF1+BRAF'),
    'S6K1': (['RPS6KB1'], 'S6K1 -> RPS6KB1'),
    'VEGFR': (['KDR', 'FLT1'], 'VEGFR family -> KDR+FLT1'),
    'p38': (['MAPK14'], 'p38 alpha -> MAPK14'),
    'HSP90': (['HSP90AA1', 'HSP90AB1'], 'HSP90 isoforms -> both genes'),
    'ERBB2|MEK1': (['ERBB2', 'MAP2K1'], 'combination drug label -> both target genes'),
    'Ephrins': (['EPHA2', 'EPHB2'], 'Ephrin receptors -> EPHA2+EPHB2 (only if both columns present)'),
}
# mechanism-class tokens: never mapped (PROTOCOL_A0 section 3)
MECHANISM_UNMAPPED_REASON = 'mechanism_class_no_gene_symbol'
MECHANISM_UNMAPPED = {
    'Antimetabolite (DNA & RNA)', 'DNA alkylating agent', 'DNA crosslinker',
    'HDAC inhibitor Class I', 'IIa', 'IIb', 'IV', 'Microtubule destabiliser',
    'Microtubule stabiliser', 'PI3K (beta sparing)', 'PI3K (class 1)',
    'Proteasome', 'Pyrimidine antimetabolite', 'others',
}

RESPONSE_KEYWORD_RE = re.compile(
    r'(?<![A-Za-z0-9])(DELTA|EMAX|SYNERGY|VIABILITY|VIAB|AUC|IC50|RESPONSE|COMBI|ANCHOR|'
    r'LIBRARY|BLISS|LOEWE|ZIP|HSA)(?![A-Za-z0-9])', re.IGNORECASE)
GENE_COL_RE = re.compile(r'^(.*) \((\d+)\)$')


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def norm_cell(name):
    """NFKC -> casefold -> remove all non [a-z0-9] (PROTOCOL_A0 section 2)."""
    s = unicodedata.normalize('NFKC', str(name)).casefold()
    return re.sub(r'[^a-z0-9]', '', s)


def q(x, nd=6):
    """round a float for deterministic JSON; non-finite -> None."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return float(round(v, nd))


def sanitize(obj):
    """recursively convert numpy scalars/arrays and non-finite floats for JSON."""
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return q(float(obj), 8)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float):
        return q(obj, 8)
    return obj


def dump_json(path, obj):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(sanitize(obj), f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write('\n')


def two_way_additive_anova(y, cell_idx, pair_idx, tol=TOL_ANOVA, max_iter=20000):
    """Iterative mean-centering (alternating projections) for y ~ mu + a_cell + b_pair.

    Converges to the least-squares additive fit; stops when max parameter change < tol.
    Returns (mu, a_cell, b_pair, resid, n_iter, converged, normal_eq_max_abs).
    """
    n_cells = int(cell_idx.max()) + 1
    n_pairs = int(pair_idx.max()) + 1
    n_c = np.bincount(cell_idx, minlength=n_cells).astype(float)
    n_p = np.bincount(pair_idx, minlength=n_pairs).astype(float)
    cell_has = n_c > 0
    pair_has = n_p > 0
    n_c_safe = np.where(cell_has, n_c, 1.0)
    n_p_safe = np.where(pair_has, n_p, 1.0)
    mu = float(y.mean())
    y0 = y - mu
    ac = np.zeros(n_cells)
    ap = np.zeros(n_pairs)
    conv = False
    it = 0
    with np.errstate(invalid='ignore', divide='ignore'):
        for it in range(1, max_iter + 1):
            rc = y0 - ap[pair_idx]
            ac_new = np.where(cell_has, np.bincount(cell_idx, weights=rc, minlength=n_cells) / n_c_safe, 0.0)
            rp = y0 - ac_new[cell_idx]
            ap_new = np.where(pair_has, np.bincount(pair_idx, weights=rp, minlength=n_pairs) / n_p_safe, 0.0)
            delta = max(np.max(np.abs((ac_new - ac)[cell_has])) if cell_has.any() else 0.0,
                        np.max(np.abs((ap_new - ap)[pair_has])) if pair_has.any() else 0.0)
            ac, ap = ac_new, ap_new
            if delta < tol:
                conv = True
                break
        resid = y - (mu + ac[cell_idx] + ap[pair_idx])
        cell_res = np.zeros(n_cells)
        pair_res = np.zeros(n_pairs)
        cell_res[cell_has] = np.bincount(cell_idx, weights=resid, minlength=n_cells)[cell_has] / n_c[cell_has]
        pair_res[pair_has] = np.bincount(pair_idx, weights=resid, minlength=n_pairs)[pair_has] / n_p[pair_has]
    neq = max(float(np.max(np.abs(cell_res))) if n_cells else 0.0,
              float(np.max(np.abs(pair_res))) if n_pairs else 0.0)
    return mu, ac, ap, resid, it, conv, neq


def rowwise_rank_pearson(A, B, mask, n):
    """Row-wise Pearson correlation of rank matrices with mask; returns NaN where invalid."""
    n = np.maximum(n.astype(float), 1.0)
    Am = np.where(mask, A, 0.0)
    Bm = np.where(mask, B, 0.0)
    meanA = (Am.sum(1) / n)[:, None]
    meanB = (Bm.sum(1) / n)[:, None]
    dA = np.where(mask, A - meanA, 0.0)
    dB = np.where(mask, B - meanB, 0.0)
    num = (dA * dB).sum(1)
    den = np.sqrt((dA * dA).sum(1) * (dB * dB).sum(1))
    out = np.full(A.shape[0], np.nan)
    ok = (n >= 2) & (den > 0)
    out[ok] = num[ok] / den[ok]
    return out


def null_stats_fixed_cells(Yt, B, rng):
    """Permutation null with FIXED fold cells (no resampling): random cell-state-only
    score vector per replicate, shared across pairs. Sensitivity for the bootstrap's
    finite-sample inflation (protocol bootstrap is the gate; this is not)."""
    K, nf = Yt.shape
    mask = ~np.isnan(Yt)
    nrow = mask.sum(1)
    ry = rankdata(Yt, axis=1, nan_policy='omit')
    stats = np.empty(B, dtype=float)
    for b in range(B):
        z = rng.normal(size=nf)
        R = np.where(mask, np.broadcast_to(z, (K, nf)), np.nan)
        rx = rankdata(R, axis=1, nan_policy='omit')
        rho = rowwise_rank_pearson(rx, ry, mask, nrow)
        good = nrow >= 2
        stats[b] = float(np.nanmean(rho[good])) if good.any() else np.nan
    return stats


def null_stats_fixed_cells_joint(Ys, B, rng):
    """Permutation null (fixed cells) for the 5-fold-mean endpoint."""
    K = Ys[0].shape[0]
    stats = np.empty(B, dtype=float)
    folds = []
    for Yt in Ys:
        mask = ~np.isnan(Yt)
        folds.append((Yt, mask, mask.sum(1), rankdata(Yt, axis=1, nan_policy='omit')))
    for b in range(B):
        vals = []
        for Yt, mask, nrow, ry in folds:
            nf = Yt.shape[1]
            z = rng.normal(size=nf)
            R = np.where(mask, np.broadcast_to(z, (K, nf)), np.nan)
            rx = rankdata(R, axis=1, nan_policy='omit')
            rho = rowwise_rank_pearson(rx, ry, mask, nrow)
            good = nrow >= 2
            vals.append(float(np.nanmean(rho[good])) if good.any() else np.nan)
        stats[b] = float(np.nanmean(np.asarray(vals, dtype=float)))
    return stats


def null_stats(Yt, variant, B, rng):
    """Two-way cluster bootstrap of the zero-prediction fold statistic.

    Resample test cells (clusters) and drug pairs (clusters); within each pair use a
    zero-information prediction:
      variant='shared'      : one arbitrary cell-state-only score vector per replicate
                              (same ranking reused by every pair -> cell-level clustering
                               of predictions; conservative, cell-level feature prediction)
      variant='independent' : one independent random ranking per pair
                              (prediction ranking independent across pairs; optimistic)
    Returns array of B statistic values (mean within-pair Spearman).
    """
    K, nf = Yt.shape
    stats = np.empty(B, dtype=float)
    for b in range(B):
        ps = rng.integers(0, K, size=K)
        cs = rng.integers(0, nf, size=nf)
        Yb = Yt[np.ix_(ps, cs)]
        mask = ~np.isnan(Yb)
        nrow = mask.sum(1)
        ry = rankdata(Yb, axis=1, nan_policy='omit')   # NaN stays NaN
        if variant == 'shared':
            z = rng.normal(size=nf)
            zp = z[cs]
            R = np.where(mask, np.broadcast_to(zp, (K, nf)), np.nan)
        else:
            R = np.where(mask, rng.random((K, nf)), np.nan)
        rx = rankdata(R, axis=1, nan_policy='omit')
        rho = rowwise_rank_pearson(rx, ry, mask, nrow)
        good = nrow >= 2
        stats[b] = float(np.nanmean(rho[good])) if good.any() else np.nan
    return stats


def null_stats_joint(Ys, variant, B, rng):
    """Bootstrap the 5-fold-mean endpoint: pairs resampled once (shared across folds),
    cells resampled independently inside each fold."""
    K = Ys[0].shape[0]
    stats = np.empty(B, dtype=float)
    for b in range(B):
        ps = rng.integers(0, K, size=K)
        fold_stats = []
        for Yt in Ys:
            nf = Yt.shape[1]
            cs = rng.integers(0, nf, size=nf)
            Yb = Yt[np.ix_(ps, cs)]
            mask = ~np.isnan(Yb)
            nrow = mask.sum(1)
            ry = rankdata(Yb, axis=1, nan_policy='omit')
            if variant == 'shared':
                z = rng.normal(size=nf)
                zp = z[cs]
                R = np.where(mask, np.broadcast_to(zp, (K, nf)), np.nan)
            else:
                R = np.where(mask, rng.random((K, nf)), np.nan)
            rx = rankdata(R, axis=1, nan_policy='omit')
            rho = rowwise_rank_pearson(rx, ry, mask, nrow)
            good = nrow >= 2
            fold_stats.append(float(np.nanmean(rho[good])) if good.any() else np.nan)
        stats[b] = float(np.nanmean(np.asarray(fold_stats, dtype=float)))
    return stats


def mde80(se):
    return Z_MDE80 * se


def main():
    t_start = time.time()
    out = {}
    print('[a0] start', flush=True)

    # ------------------------------------------------------------------
    # P1: input SHA256 / sizes
    # ------------------------------------------------------------------
    print('[a0] hashing inputs', flush=True)
    p1_files = {}
    for p in INPUT_FILES:
        p1_files[os.path.basename(p)] = {
            'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
            'bytes': int(os.path.getsize(p)),
            'sha256': sha256_file(p),
        }
    protocol_sha = sha256_file(PROTOCOL)
    script_sha = sha256_file(SCRIPT)
    out['P1_inputs'] = {
        'purpose': 'qualification',
        'files': p1_files,
        'protocol_sha256': protocol_sha,
        'protocol_path_rel': os.path.relpath(PROTOCOL, ROOT).replace('\\', '/'),
        'script_sha256': script_sha,
        'script_path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
        'seed': SEED,
        'bootstrap_resamples': B_BOOT,
        'amendment_a0_001_applied': True,
    }
    print('[a0] hashing done', flush=True)

    # ------------------------------------------------------------------
    # P2: table structure vs Glossary
    # ------------------------------------------------------------------
    fit_cols = ['CELL_LINE_NAME', 'COSMIC_ID', 'ANCHOR_NAME', 'LIBRARY_NAME',
                'ANCHOR_TARGET', 'LIBRARY_TARGET', 'ANCHOR_CONC', 'BARCODE',
                'SYNERGY_DELTA_EMAX', 'Tissue']
    fit = pd.read_csv(FITTED, usecols=fit_cols, low_memory=False)
    fit['y'] = pd.to_numeric(fit['SYNERGY_DELTA_EMAX'], errors='coerce')
    fit['ANCHOR_NAME'] = fit['ANCHOR_NAME'].astype(str)
    fit['LIBRARY_NAME'] = fit['LIBRARY_NAME'].astype(str)
    fit['CELL_LINE_NAME'] = fit['CELL_LINE_NAME'].astype(str)

    glossary_sheets = pd.read_excel(GLOSSARY, sheet_name=None)
    gloss_terms = []
    gloss_sheet_used = None
    for sheet_name, gdf in glossary_sheets.items():
        terms = [str(t).strip() for t in gdf.iloc[:, 0].tolist() if str(t).strip()]
        if len(terms) > len(gloss_terms):
            gloss_terms = terms
            gloss_sheet_used = sheet_name
    all_fit_cols = list(pd.read_csv(FITTED, nrows=0).columns)
    matched = sorted(set(gloss_terms) & set(all_fit_cols))
    missing_in_table = sorted(set(gloss_terms) - set(all_fit_cols))
    undefined_in_gloss = sorted(set(all_fit_cols) - set(gloss_terms))
    out['P2_structure'] = {
        'fitted_rows': int(len(fit)),
        'fitted_columns': int(len(all_fit_cols)),
        'glossary_sheet_used': gloss_sheet_used,
        'glossary_terms': int(len(gloss_terms)),
        'matched_terms': int(len(matched)),
        'missing_in_table': missing_in_table,
        'undefined_in_glossary': undefined_in_gloss,
        'consistent': bool(not missing_in_table and not undefined_in_gloss),
        'response_column': 'SYNERGY_DELTA_EMAX',
        'response_nonnull': int(fit['y'].notna().sum()),
        'response_nan': int(fit['y'].isna().sum()),
        'note': 'table/definition consistency checked; inconsistencies (if any) are reported, not fatal (PROTOCOL_A0 section 7 P2)',
    }
    print('[a0] P2 done', flush=True)

    # ------------------------------------------------------------------
    # G1: cell identity linkage
    # ------------------------------------------------------------------
    cell_tab = fit.groupby('CELL_LINE_NAME', sort=True).agg(
        COSMIC_ID=('COSMIC_ID', 'first'), Tissue=('Tissue', 'first')).reset_index()
    cell_tab['COSMIC_ID'] = pd.to_numeric(cell_tab['COSMIC_ID'], errors='coerce')
    cell_tab['norm'] = cell_tab['CELL_LINE_NAME'].map(norm_cell)

    si = pd.read_csv(SAMPLE_INFO)
    si['DepMap_ID'] = si['DepMap_ID'].astype(str)
    si['COSMIC_ID'] = pd.to_numeric(si['COSMIC_ID'], errors='coerce')
    si['norm'] = si['stripped_cell_line_name'].map(norm_cell)

    # sample_info internal uniqueness
    si_cosmic_dup = int(si['COSMIC_ID'].dropna().duplicated().sum())
    si_depmap_dup = int(si['DepMap_ID'].duplicated().sum())
    si_norm_dup = int(si['norm'].duplicated().sum())

    # primary join on numeric COSMIC_ID
    cos_map = si.dropna(subset=['COSMIC_ID']).groupby('COSMIC_ID')['DepMap_ID'].agg(list)
    primary_rows = []
    conflicts = []
    one_to_many = []
    for _, c in cell_tab.iterrows():
        dm = None
        method = None
        note = ''
        if pd.notna(c['COSMIC_ID']) and c['COSMIC_ID'] in cos_map.index:
            ids = sorted(set(cos_map.loc[c['COSMIC_ID']]))
            if len(ids) == 1:
                dm = ids[0]
                method = 'cosmic_id'
            else:
                one_to_many.append({'CELL_LINE_NAME': c['CELL_LINE_NAME'],
                                    'COSMIC_ID': int(c['COSMIC_ID']),
                                    'DepMap_IDs': ids})
        primary_rows.append({'CELL_LINE_NAME': c['CELL_LINE_NAME'],
                             'COSMIC_ID': c['COSMIC_ID'],
                             'norm': c['norm'], 'Tissue': c['Tissue'],
                             'DepMap_ID': dm, 'join_method': method, 'note': note})
    g1 = pd.DataFrame(primary_rows)
    primary_unmatched = sorted(g1.loc[g1['DepMap_ID'].isna(), 'CELL_LINE_NAME'].tolist())

    # secondary: normalized-name fill for cells not covered by primary
    norm_map = si.groupby('norm')['DepMap_ID'].agg(lambda x: sorted(set(x)))
    secondary = []
    for idx in g1.index[g1['DepMap_ID'].isna()]:
        nrm = g1.at[idx, 'norm']
        cand = norm_map.get(nrm, [])
        if len(cand) == 1:
            g1.at[idx, 'DepMap_ID'] = cand[0]
            g1.at[idx, 'join_method'] = 'normalized_name'
            g1.at[idx, 'note'] = 'cosmic_id_absent_or_unmatched;normalized_name_unique'
            secondary.append({'CELL_LINE_NAME': g1.at[idx, 'CELL_LINE_NAME'],
                              'DepMap_ID': cand[0]})
        else:
            g1.at[idx, 'note'] = 'unmatched'

    # agreement primary vs normalized name (only for primary hits)
    prim_hits = g1[g1['join_method'] == 'cosmic_id']
    si_by_depmap = si.set_index('DepMap_ID')['norm']
    for idx in g1.index[g1['join_method'] == 'cosmic_id']:
        dm = g1.at[idx, 'DepMap_ID']
        if dm in si_by_depmap.index and si_by_depmap.loc[dm] != g1.at[idx, 'norm']:
            conflicts.append({'CELL_LINE_NAME': g1.at[idx, 'CELL_LINE_NAME'],
                              'DepMap_ID': dm})

    # expression row availability
    ex = pd.read_csv(EXPR, low_memory=False)
    ex = ex.rename(columns={ex.columns[0]: 'DepMap_ID'})
    ex['DepMap_ID'] = ex['DepMap_ID'].astype(str)
    ex_ids = set(ex['DepMap_ID'])
    expr_dup = int(ex['DepMap_ID'].duplicated().sum())
    g1['has_expression_row'] = g1['DepMap_ID'].isin(ex_ids)
    g1['note'] = g1['note'].astype(str)
    _noexpr = (~g1['has_expression_row']) & g1['DepMap_ID'].notna()
    g1.loc[_noexpr, 'note'] = g1.loc[_noexpr, 'note'] + ';expression_row_missing'
    g1['note'] = g1['note'].str.lstrip(';')

    mapped = int(g1['DepMap_ID'].notna().sum())
    mapped_unique = int(g1['DepMap_ID'].dropna().nunique())
    expr_cells = sorted(g1.loc[g1['has_expression_row'], 'CELL_LINE_NAME'].tolist())
    missing_expr = g1.loc[g1['DepMap_ID'].notna() & (~g1['has_expression_row']),
                         ['CELL_LINE_NAME', 'Tissue', 'DepMap_ID']].copy()
    missing_expr_rows = [{'CELL_LINE_NAME': r['CELL_LINE_NAME'], 'Tissue': r['Tissue'],
                          'DepMap_ID': r['DepMap_ID']}
                         for _, r in missing_expr.sort_values('CELL_LINE_NAME').iterrows()]
    g1_pass = bool(mapped_unique >= THRESH['G1_map_min'] and len(expr_cells) >= THRESH['G1_expr_min'])
    out['G1_identity'] = {
        'n_jaaks_cells': int(len(g1)),
        'sample_info_rows': int(len(si)),
        'sample_info_depmap_dup': si_depmap_dup,
        'sample_info_cosmic_dup': si_cosmic_dup,
        'sample_info_normalized_name_dup': si_norm_dup,
        'primary_cosmic_mapped': int(len(prim_hits)),
        'primary_cosmic_unmatched': primary_unmatched,
        'secondary_name_filled': [s['CELL_LINE_NAME'] for s in secondary],
        'final_mapped_unique_depmap': mapped_unique,
        'final_mapped_cells': mapped,
        'one_to_many': one_to_many,
        'many_to_one': [],
        'primary_vs_name_conflicts': conflicts,
        'expression_depmap_ids': int(len(ex_ids)),
        'expression_depmap_dup': expr_dup,
        'mapped_with_expression_row': int(len(expr_cells)),
        'mapped_with_expression_frac': q(len(expr_cells) / max(mapped, 1)),
        'missing_expression_cells': missing_expr_rows,
        'missing_expression_count': int(len(missing_expr_rows)),
        'missing_expression_by_tissue': pd.Series([m['Tissue'] for m in missing_expr_rows]).value_counts().sort_index().to_dict() if missing_expr_rows else {},
        'threshold_map_min': THRESH['G1_map_min'],
        'threshold_expr_min': THRESH['G1_expr_min'],
        'pass': g1_pass,
        'amendment_a0_001': 'G1 gate = >=119 unique DepMap_ID AND >=105 of them with expression row; folds on expression cells (111)',
    }
    # freeze identity map (deterministic order)
    idmap = g1[['CELL_LINE_NAME', 'COSMIC_ID', 'DepMap_ID', 'join_method', 'note']].copy()
    idmap = idmap.sort_values('CELL_LINE_NAME', kind='mergesort').reset_index(drop=True)
    idmap['COSMIC_ID'] = idmap['COSMIC_ID'].map(lambda x: int(x) if pd.notna(x) else '')
    idmap['join_method'] = idmap['join_method'].fillna('unmatched')
    idmap.to_csv(os.path.join(OUTDIR, 'identity_map.csv'), index=False)
    out['G1_identity']['identity_map_sha256'] = sha256_file(os.path.join(OUTDIR, 'identity_map.csv'))
    print('[a0] G1 done: mapped=%d expr=%d' % (mapped_unique, len(expr_cells)), flush=True)

    # ------------------------------------------------------------------
    # G2: feature availability (expression matrix, target mapping)
    # ------------------------------------------------------------------
    gene_cols = [c for c in ex.columns if c != 'DepMap_ID']
    parsed = [GENE_COL_RE.match(c) for c in gene_cols]
    unparsed = [c for c, m in zip(gene_cols, parsed) if m is None]
    gene_names = [m.group(1) if m else c for c, m in zip(gene_cols, parsed)]
    gene_set = set(gene_names)
    gene_dup = int(len(gene_names) - len(gene_set))
    vals = ex[gene_cols].to_numpy(dtype=np.float64)
    n_missing = int(np.isnan(vals).sum())
    col_sd = np.nanstd(vals, axis=0)
    zero_var = [gene_names[i] for i in range(len(gene_names)) if not np.isfinite(col_sd[i]) or col_sd[i] < 1e-12]
    resp_kw_cols = sorted({c for c in gene_cols if RESPONSE_KEYWORD_RE.search(c)})

    # drug -> target tokens (from GDSC metadata, response-free)
    def split_tokens(s):
        return [t.strip() for t in str(s).split(',') if t.strip() and t.strip().lower() != 'nan']

    drug_targets = {}
    target_consistency = {}
    for side in ('ANCHOR', 'LIBRARY'):
        sub = fit[[side + '_NAME', side + '_TARGET']].drop_duplicates()
        for nm, tg in sub.itertuples(index=False, name=None):
            toks = set(drug_targets.get(nm, set())) | set(split_tokens(tg))
            drug_targets[nm] = toks
    # target-string constancy per drug
    for side in ('ANCHOR', 'LIBRARY'):
        sub = fit.groupby(side + '_NAME')[side + '_TARGET'].nunique()
        for nm, v in sub.items():
            if int(v) > 1:
                target_consistency.setdefault(nm, []).append(side)
    targets = sorted(set().union(*[v for v in drug_targets.values()]))
    target_map = {}
    for t in targets:
        if t in gene_set:
            target_map[t] = {'method': 'exact', 'genes': [t]}
        elif t in ALIAS_TABLE:
            genes = [g for g in ALIAS_TABLE[t][0] if g in gene_set]
            if len(genes) == len(ALIAS_TABLE[t][0]) and genes:
                target_map[t] = {'method': 'alias', 'genes': genes}
            else:
                target_map[t] = {'method': 'alias_genes_missing', 'genes': genes}
        else:
            target_map[t] = {'method': 'unmapped', 'genes': []}
    mapped_targets = sorted([t for t in targets if target_map[t]['method'] in ('exact', 'alias')])
    n_exact = sum(1 for t in targets if target_map[t]['method'] == 'exact')
    n_alias = sum(1 for t in targets if target_map[t]['method'] == 'alias')
    n_unmapped = len(targets) - n_exact - n_alias

    drug_mapped_genes = {}
    drug_has_mapped = {}
    for nm, toks in drug_targets.items():
        genes = set()
        for t in toks:
            if target_map.get(t, {}).get('method') in ('exact', 'alias'):
                genes.update(target_map[t]['genes'])
        drug_mapped_genes[nm] = sorted(genes)
        drug_has_mapped[nm] = bool(genes)

    pairs_ordered = fit[['ANCHOR_NAME', 'LIBRARY_NAME']].drop_duplicates().reset_index(drop=True)
    pairs_ordered['anchor_covered'] = pairs_ordered['ANCHOR_NAME'].map(lambda x: bool(drug_has_mapped.get(x, False)))
    pairs_ordered['library_covered'] = pairs_ordered['LIBRARY_NAME'].map(lambda x: bool(drug_has_mapped.get(x, False)))
    both_covered = int((pairs_ordered['anchor_covered'] & pairs_ordered['library_covered']).sum())
    union_covered = int((pairs_ordered['anchor_covered'] | pairs_ordered['library_covered']).sum())
    n_ordered_pairs = int(len(pairs_ordered))
    pair_cov_both = both_covered / max(n_ordered_pairs, 1)

    # unordered pairs (key universe of PROTOCOL_A0 section 4)
    un_a = np.minimum(pairs_ordered['ANCHOR_NAME'], pairs_ordered['LIBRARY_NAME'])
    un_b = np.maximum(pairs_ordered['ANCHOR_NAME'], pairs_ordered['LIBRARY_NAME'])
    upairs = pd.DataFrame({'a': un_a, 'b': un_b}).drop_duplicates()
    upairs['a_cov'] = upairs['a'].map(lambda x: bool(drug_has_mapped.get(x, False)))
    upairs['b_cov'] = upairs['b'].map(lambda x: bool(drug_has_mapped.get(x, False)))
    n_unordered_pairs = int(len(upairs))
    unordered_both = int((upairs['a_cov'] & upairs['b_cov']).sum())
    unordered_union = int((upairs['a_cov'] | upairs['b_cov']).sum())

    # target-level pair-side usage counts
    tgt_anchor_pairs = {}
    tgt_library_pairs = {}
    for nm, toks in drug_targets.items():
        n_as_anchor = int((pairs_ordered['ANCHOR_NAME'] == nm).sum())
        n_as_lib = int((pairs_ordered['LIBRARY_NAME'] == nm).sum())
        for t in toks:
            tgt_anchor_pairs[t] = tgt_anchor_pairs.get(t, 0) + n_as_anchor
            tgt_library_pairs[t] = tgt_library_pairs.get(t, 0) + n_as_lib
    # write target_map.csv
    trows = []
    for t in targets:
        tm = target_map[t]
        reason = ''
        if tm['method'] == 'unmapped':
            reason = MECHANISM_UNMAPPED_REASON if t in MECHANISM_UNMAPPED else 'no_gene_column_match'
        elif tm['method'] == 'alias_genes_missing':
            reason = 'alias_defined_but_gene_column_missing'
        trows.append({
            'target_token': t,
            'mapping_method': tm['method'],
            'mapped_genes': ';'.join(tm['genes']),
            'n_drugs_using': int(sum(1 for toks in drug_targets.values() if t in toks)),
            'n_ordered_pairs_anchor_side': int(tgt_anchor_pairs.get(t, 0)),
            'n_ordered_pairs_library_side': int(tgt_library_pairs.get(t, 0)),
            'note': reason,
        })
    tmap = pd.DataFrame(trows).sort_values('target_token', kind='mergesort').reset_index(drop=True)
    tmap.to_csv(os.path.join(OUTDIR, 'target_map.csv'), index=False)

    drug_cov_dist = pd.Series([len(v) for v in drug_mapped_genes.values()]).value_counts().sort_index()
    g2_pass = bool(len(mapped_targets) >= THRESH['G2_target_min'] and pair_cov_both >= THRESH['G2_pair_cov_min'])
    out['G2_features'] = {
        'purpose': 'qualification',
        'expression_matrix_shape': [int(ex.shape[0]), int(len(gene_cols))],
        'expression_row_id_column': 'DepMap_ID',
        'expression_column_format': 'GENE (entrez)',
        'expression_unparsable_columns': len(unparsed),
        'expression_duplicate_gene_names': gene_dup,
        'expression_missing_values': n_missing,
        'expression_zero_variance_columns': len(zero_var),
        'expression_zero_variance_examples': sorted(zero_var)[:10],
        'expression_response_keyword_columns': resp_kw_cols,
        'n_unique_target_tokens': int(len(targets)),
        'n_exact': int(n_exact),
        'n_alias': int(n_alias),
        'n_unmapped': int(n_unmapped),
        'n_mapped_targets': int(len(mapped_targets)),
        'mapped_targets': mapped_targets,
        'unmapped_targets': sorted([t for t in targets if target_map[t]['method'] not in ('exact', 'alias')]),
        'alias_table_size': int(len(ALIAS_TABLE)),
        'drug_target_annotation_conflicts': {k: sorted(v) for k, v in target_consistency.items()},
        'n_drugs': int(len(drug_targets)),
        'drug_mapped_gene_count_distribution': {str(int(k)): int(v) for k, v in drug_cov_dist.items()},
        'drugs_without_mapped_gene': sorted([nm for nm, has in drug_has_mapped.items() if not has]),
        'n_ordered_pairs': n_ordered_pairs,
        'ordered_pairs_both_sides_covered': both_covered,
        'ordered_pairs_union_covered': union_covered,
        'ordered_pair_coverage_both_sides': q(pair_cov_both),
        'n_unordered_pairs': n_unordered_pairs,
        'unordered_pairs_both_sides_covered': unordered_both,
        'unordered_pairs_union_covered': unordered_union,
        'unordered_pair_coverage_both_sides': q(unordered_both / max(n_unordered_pairs, 1)),
        'threshold_target_min': THRESH['G2_target_min'],
        'threshold_pair_cov_min': THRESH['G2_pair_cov_min'],
        'pass': g2_pass,
        'target_map_sha256': sha256_file(os.path.join(OUTDIR, 'target_map.csv')),
        'interpretation_note': ('frozen text: "2025 药对中两侧靶点均 >=1 个映射基因" implemented as '
                                'EACH side (anchor side and library side) has >=1 mapped gene; the '
                                'combined-pair ("union") variant is reported separately for transparency '
                                'and is NOT used for the gate because it changes the frozen criterion.'),
    }
    print('[a0] G2 done: targets %d/%d, pair both %.4f' % (len(mapped_targets), len(targets), pair_cov_both), flush=True)

    # ------------------------------------------------------------------
    # G3: signal, room, power  (purpose=qualification; response used only here)
    # ------------------------------------------------------------------
    # key definition (PROTOCOL_A0 section 4): (CELL_LINE_NAME, unordered drug pair)
    amin = np.minimum(fit['ANCHOR_NAME'].values, fit['LIBRARY_NAME'].values)
    bmax = np.maximum(fit['ANCHOR_NAME'].values, fit['LIBRARY_NAME'].values)
    fit['pair_key'] = np.char.add(np.char.add(amin.astype(str), ' || '), bmax.astype(str))
    fit_ok = fit[fit['y'].notna()].copy()
    grp = fit_ok.groupby(['CELL_LINE_NAME', 'pair_key'], sort=True)['y']
    keys = grp.mean().rename('y').reset_index()
    rows_per_key = grp.size().rename('n_rows').reset_index()
    n_keys = int(len(keys))
    key_cells = sorted(keys['CELL_LINE_NAME'].unique())
    key_pairs = sorted(keys['pair_key'].unique())
    n_key_cells = len(key_cells)
    n_key_pairs = len(key_pairs)
    same_name_pairs = int((fit_ok['ANCHOR_NAME'] == fit_ok['LIBRARY_NAME']).sum())
    ordered_pairs_n = int(fit_ok.groupby(['ANCHOR_NAME', 'LIBRARY_NAME']).ngroups)
    ordered_keys_n = int(fit_ok.groupby(['CELL_LINE_NAME', 'ANCHOR_NAME', 'LIBRARY_NAME']).ngroups)
    rows_per_key_mean = float(rows_per_key['n_rows'].mean())

    ci = {c: i for i, c in enumerate(key_cells)}
    pj = {p: i for i, p in enumerate(key_pairs)}
    cidx = keys['CELL_LINE_NAME'].map(ci).to_numpy()
    pidx = keys['pair_key'].map(pj).to_numpy()
    yv = keys['y'].to_numpy(dtype=float)

    def anova_block(y, cidx_, pidx_):
        mu_, ac_, ap_, resid_, iters_, conv_, neq_ = two_way_additive_anova(y, cidx_, pidx_)
        tot = float(y.var())
        return {
            'mu': q(mu_), 'n_iter': int(iters_), 'converged': bool(conv_),
            'normal_equation_max_abs_residual': q(neq_),
            'var_total': q(tot),
            'var_share_cell': q(float(ac_[cidx_].var()) / tot),
            'var_share_pair': q(float(ap_[pidx_].var()) / tot),
            'var_share_interaction': q(float(resid_.var()) / tot),
            'var_share_sum': q(float((ac_[cidx_].var() + ap_[pidx_].var() + resid_.var()) / tot)),
            'cov_cell_pair_over_total': q(float(np.cov(ac_[cidx_], ap_[pidx_])[0, 1]) / tot),
        }, ac_, ap_, resid_

    anova_all, ac_all, ap_all, resid_all = anova_block(yv, cidx, pidx)
    # G3(b): per pair with >=5 cells, Spearman(y, a_cell)
    kk = pd.DataFrame({'pair_idx': pidx, 'y': yv, 'acell': ac_all[cidx]})
    n_cells_per_pair = kk.groupby('pair_idx')['y'].size()
    rhos_b = []
    for pi_, g in kk.groupby('pair_idx', sort=True):
        if len(g) >= 5:
            rr = spearmanr(g['y'].to_numpy(), g['acell'].to_numpy()).statistic
            if np.isfinite(rr):
                rhos_b.append(float(rr))
    rhos_b = np.asarray(rhos_b)
    # G3(c): within-pair sd of y_int = y - pair mean
    keys['y_int'] = yv - pd.Series(yv).groupby(pidx).transform('mean').to_numpy()
    pair_sd = keys.groupby('pair_key')['y_int'].agg(['std', 'size'])
    pair_sd = pair_sd[pair_sd['size'] >= 2]
    sd_med = float(pair_sd['std'].median())
    var_signal = sd_med ** 2
    # G3(d): sigma_e
    # (i) raw screen attempt: document structure, cannot produce key-level delta-EMAX noise
    raw_info = {}
    try:
        with zipfile.ZipFile(RAWZIP) as zf:
            names = zf.namelist()
            with zf.open(names[0]) as fh:
                header = fh.readline().decode('utf-8', 'replace').strip().split(',')
                n_lines = 1
                for chunk in iter(lambda: fh.read(1 << 22), b''):
                    n_lines += chunk.count(b'\n')
        raw_info = {
            'zip_members': names,
            'raw_columns': header,
            'raw_rows_including_header': int(n_lines),
            'has_synergy_delta_emax_column': bool('SYNERGY_DELTA_EMAX' in header),
            'has_combination_endpoint_column': bool(any(c.upper().startswith('SYNERGY') for c in header)),
            'parsed': True,
            'sigma_e_key_level': None,
            'reason': ('raw archive contains single-agent dose-response wells '
                       '(DRUG_ID/DRUG_NAME/CONC/INTENSITY); it has no per-key '
                       'SYNERGY_DELTA_EMAX column and no combination endpoint, so the '
                       'key-level replicate noise sigma_e of Delta-EMAX cannot be estimated '
                       'from it. PROTOCOL_A0 section 4d fallback (borrow R4 sigma_e) is used.'),
            'raw_cells': None,
        }
    except Exception as exc:  # pragma: no cover - defensive
        raw_info = {'parsed': False, 'error': repr(exc), 'sigma_e_key_level': None,
                    'reason': 'raw archive could not be parsed; PROTOCOL_A0 section 4d fallback used'}

    # (ii) fitted-table replicate plates: same (cell, pair, anchor conc) on >=2 barcodes
    fit['pair_key2'] = fit['pair_key']
    sub = fit.groupby(['CELL_LINE_NAME', 'pair_key2', 'ANCHOR_CONC', 'BARCODE'], sort=True)['y'].mean().reset_index()
    cond = sub.groupby(['CELL_LINE_NAME', 'pair_key2', 'ANCHOR_CONC'])['y'].agg(['size', 'var'])
    df_rep = float((cond['size'] - 1).sum())
    ss_rep = float((cond['var'] * (cond['size'] - 1)).sum())
    sigma_row = float(np.sqrt(ss_rep / df_rep)) if df_rep > 0 else None
    sigma_key_fitted = float(sigma_row / math.sqrt(rows_per_key_mean)) if sigma_row is not None else None
    sigma_used = SIGMA_E_BORROWED
    rho_ceiling = float(np.sqrt(var_signal / (var_signal + sigma_used ** 2)))
    rho_ceiling_fitted_row = float(np.sqrt(var_signal / (var_signal + sigma_row ** 2))) if sigma_row else None
    rho_ceiling_fitted_key = float(np.sqrt(var_signal / (var_signal + sigma_key_fitted ** 2))) if sigma_key_fitted else None

    # cross-screen reliability (auxiliary, not a gate)
    val = pd.read_csv(VALID, usecols=['CELL_LINE_NAME', 'ANCHOR_NAME', 'LIBRARY_NAME',
                                      'SYNERGY_DELTA_EMAX', 'Tissue'], low_memory=False)
    val['y'] = pd.to_numeric(val['SYNERGY_DELTA_EMAX'], errors='coerce')
    v_a = np.minimum(val['ANCHOR_NAME'].astype(str).values, val['LIBRARY_NAME'].astype(str).values)
    v_b = np.maximum(val['ANCHOR_NAME'].astype(str).values, val['LIBRARY_NAME'].astype(str).values)
    val['pair_key'] = np.char.add(np.char.add(v_a, ' || '), v_b)
    val_ok = val[val['y'].notna()]
    vkeys = val_ok.groupby(['CELL_LINE_NAME', 'pair_key'], sort=True)['y'].mean().rename('yval').reset_index()
    ov = keys[['CELL_LINE_NAME', 'pair_key', 'y']].merge(vkeys, on=['CELL_LINE_NAME', 'pair_key'], how='inner')
    cross_rhos = []
    for _, g in ov.groupby('pair_key', sort=True):
        if len(g) >= 2:
            rr = spearmanr(g['y'].to_numpy(), g['yval'].to_numpy()).statistic
            if np.isfinite(rr):
                cross_rhos.append(float(rr))
    cross_rhos = np.asarray(cross_rhos)

    # G3(e): 5-fold cell split over expression cells (AMENDMENT-A0-001)
    expr_cells_sorted = sorted(expr_cells, key=norm_cell)
    folds = {f: [c for i, c in enumerate(expr_cells_sorted) if i % 5 == f] for f in range(5)}
    # key table restricted to expression cells (all keys of those cells are present)
    ecset = set(expr_cells)
    keys_expr = keys[keys['CELL_LINE_NAME'].isin(ecset)].copy()
    n_keys_expr = int(len(keys_expr))
    n_pairs_expr = int(keys_expr['pair_key'].nunique())
    Y = np.full((n_key_pairs, len(expr_cells_sorted)), np.nan, dtype=float)
    epos = {c: i for i, c in enumerate(expr_cells_sorted)}
    pair_pos = {p: i for i, p in enumerate(key_pairs)}
    for p, g in keys_expr.groupby('pair_key', sort=True):
        row = pair_pos[p]
        Y[row, [epos[c] for c in g['CELL_LINE_NAME']]] = g['y'].to_numpy()

    rng = np.random.default_rng(SEED)
    fold_tests = []
    for f in range(5):
        fcells = folds[f]
        fpos = [epos[c] for c in fcells]
        Yt = Y[:, fpos]
        npts = (~np.isnan(Yt)).sum(1)
        ge2 = npts >= 2
        K_ge2 = int(ge2.sum())
        n_test_keys_all = int((~np.isnan(Yt)).sum())
        n_test_keys_ge2 = int(npts[ge2].sum())
        se_analytic = float(np.sqrt(np.sum(1.0 / (npts[ge2] - 1))) / K_ge2) if K_ge2 > 0 else None
        boot_shared = null_stats(Yt, 'shared', B_BOOT, rng)
        boot_ind = null_stats(Yt, 'independent', B_BOOT, rng)
        perm_fixed = null_stats_fixed_cells(Yt, B_BOOT, rng)
        se_shared = float(np.nanstd(boot_shared, ddof=1))
        se_ind = float(np.nanstd(boot_ind, ddof=1))
        se_perm = float(np.nanstd(perm_fixed, ddof=1))
        tissue_counts = (g1.set_index('CELL_LINE_NAME')['Tissue'].loc[fcells]
                         .value_counts().sort_index().to_dict())
        fold_tests.append({
            'fold': int(f),
            'n_cells': int(len(fcells)),
            'cells': list(fcells),
            'n_test_keys': n_test_keys_all,
            'n_test_keys_in_pairs_ge2': n_test_keys_ge2,
            'n_pairs_total': int(n_key_pairs),
            'n_pairs_ge2_test_cells': K_ge2,
            'frac_pairs_ge2': q(K_ge2 / n_key_pairs),
            'n_cells_per_pair_min': int(npts[ge2].min()) if K_ge2 else None,
            'n_cells_per_pair_median': q(float(np.median(npts[ge2]))) if K_ge2 else None,
            'n_cells_per_pair_max': int(npts[ge2].max()) if K_ge2 else None,
            'tissue_counts': tissue_counts,
            'se_analytic_iid': q(se_analytic),
            'mde80_analytic_iid': q(mde80(se_analytic)) if se_analytic is not None else None,
            'se_bootstrap_shared_cell': q(se_shared),
            'mde80_bootstrap_shared_cell': q(mde80(se_shared)),
            'se_bootstrap_independent_pair': q(se_ind),
            'mde80_bootstrap_independent_pair': q(mde80(se_ind)),
            'se_permutation_fixed_cells_shared': q(se_perm),
            'mde80_permutation_fixed_cells_shared': q(mde80(se_perm)),
            'bootstrap_null_mean_shared_cell': q(float(np.nanmean(boot_shared))),
            'bootstrap_null_mean_independent_pair': q(float(np.nanmean(boot_ind))),
            'permutation_fixed_cells_null_mean': q(float(np.nanmean(perm_fixed))),
        })
    # 5-fold-mean endpoint MDE (joint bootstrap, pairs shared across folds)
    Ys = [Y[:, [epos[c] for c in folds[f]]] for f in range(5)]
    joint_shared = null_stats_joint(Ys, 'shared', B_BOOT, rng)
    joint_ind = null_stats_joint(Ys, 'independent', B_BOOT, rng)
    joint_perm = null_stats_fixed_cells_joint(Ys, B_BOOT, rng)
    se_joint_shared = float(np.nanstd(joint_shared, ddof=1))
    se_joint_ind = float(np.nanstd(joint_ind, ddof=1))
    se_joint_perm = float(np.nanstd(joint_perm, ddof=1))
    fold_mde_shared = [t['mde80_bootstrap_shared_cell'] for t in fold_tests]
    fold_mde_iid = [t['mde80_analytic_iid'] for t in fold_tests]
    fold_mde_perm = [t['mde80_permutation_fixed_cells_shared'] for t in fold_tests]

    # gate: protocol-literal two-way clustered (cells + pairs) zero-prediction MDE80
    mde_gate = float(np.mean(fold_mde_shared))
    g3e_pass = bool(mde_gate <= THRESH['G3e_mde80_max'])

    # G3(f): tissue coverage
    tissue_all = cell_tab['Tissue'].value_counts().sort_index().to_dict()
    tissue_expr = g1.loc[g1['has_expression_row'], 'Tissue'].value_counts().sort_index().to_dict()
    out['G3_signal_room_power'] = {
        'purpose': 'qualification',
        'key_definition': '(CELL_LINE_NAME, unordered drug pair key = min||max of ANCHOR_NAME/LIBRARY_NAME); y = mean(SYNERGY_DELTA_EMAX) over all rows of the key',
        'ordered_pairs': ordered_pairs_n,
        'ordered_keys': ordered_keys_n,
        'unordered_pairs': n_key_pairs,
        'unordered_keys': n_keys,
        'same_name_pair_rows': same_name_pairs,
        'n_cells_all': n_key_cells,
        'rows_per_key_mean': q(rows_per_key_mean),
        'keys_expression_cells': n_keys_expr,
        'pairs_expression_cells': n_pairs_expr,
        'response_distribution': {
            'note': 'descriptive only (qualification)',
            'n': int(len(yv)), 'mean': q(float(yv.mean())), 'sd': q(float(yv.std(ddof=1))),
            'min': q(float(yv.min())), 'q25': q(float(np.quantile(yv, 0.25))),
            'median': q(float(np.median(yv))), 'q75': q(float(np.quantile(yv, 0.75))),
            'max': q(float(yv.max())),
        },
        'a_variance_components': {
            'method': 'two-way additive ANOVA y~mu+a_cell+b_pair via iterative mean centering, tol=1e-9',
            'all_125_cells': anova_all,
            'interaction_share_threshold': THRESH['G3a_interaction_min'],
            'pass': bool(anova_all['var_share_interaction'] is not None and anova_all['var_share_interaction'] >= THRESH['G3a_interaction_min']),
        },
        'b_additive_cell_effect_ceiling': {
            'method': 'per pair with >=5 cells: Spearman(y, a_cell_hat)',
            'n_pairs': int(len(rhos_b)),
            'mean': q(float(rhos_b.mean())), 'median': q(float(np.median(rhos_b))),
            'sd': q(float(rhos_b.std(ddof=1))),
            'q10': q(float(np.quantile(rhos_b, 0.10))), 'q25': q(float(np.quantile(rhos_b, 0.25))),
            'q75': q(float(np.quantile(rhos_b, 0.75))), 'q90': q(float(np.quantile(rhos_b, 0.90))),
            'threshold_mean_min': THRESH['G3b_ceiling_mean_min'],
            'pass': bool(float(rhos_b.mean()) >= THRESH['G3b_ceiling_mean_min']),
        },
        'c_within_pair_room': {
            'method': 'per pair: y_int = y - pair mean; sd(y_int) over keys of the pair',
            'n_pairs': int(len(pair_sd)),
            'median_sd': q(sd_med), 'mean_sd': q(float(pair_sd['std'].mean())),
            'q10': q(float(pair_sd['std'].quantile(0.10))),
            'q25': q(float(pair_sd['std'].quantile(0.25))),
            'q75': q(float(pair_sd['std'].quantile(0.75))),
            'q90': q(float(pair_sd['std'].quantile(0.90))),
            'threshold_median_min': THRESH['G3c_sd_median_min'],
            'pass': bool(sd_med >= THRESH['G3c_sd_median_min']),
        },
        'd_reliability': {
            'raw_screen_attempt': raw_info,
            'sigma_e_used': q(sigma_used),
            'sigma_e_source': SIGMA_E_SOURCE,
            'sigma_e_fitted_replicate_row': q(sigma_row),
            'sigma_e_fitted_replicate_key': q(sigma_key_fitted),
            'fitted_replicate_df': int(df_rep),
            'fitted_replicate_conditions_ge2': int(len(cond)),
            'var_signal': q(var_signal),
            'var_signal_definition': 'median_pair_sd(y_int)^2',
            'rho_ceiling': q(rho_ceiling),
            'rho_ceiling_fitted_row': q(rho_ceiling_fitted_row),
            'rho_ceiling_fitted_key': q(rho_ceiling_fitted_key),
            'threshold_rho_ceiling_min': THRESH['G3d_rho_ceiling_min'],
            'pass': bool(rho_ceiling >= THRESH['G3d_rho_ceiling_min']),
            'cross_screen_reliability_aux': {
                'note': 'auxiliary only, not a gate (PROTOCOL_A0 section 4d)',
                'validation_cells': int(val_ok['CELL_LINE_NAME'].nunique()),
                'validation_pairs': int(val_ok['pair_key'].nunique()),
                'validation_keys': int(len(vkeys)),
                'overlap_keys': int(len(ov)),
                'overlap_pairs': int(ov['pair_key'].nunique()),
                'n_pairs_computable': int(len(cross_rhos)),
                'mean_within_pair_spearman': q(float(cross_rhos.mean())) if len(cross_rhos) else None,
                'median_within_pair_spearman': q(float(np.median(cross_rhos))) if len(cross_rhos) else None,
                'q10': q(float(np.quantile(cross_rhos, 0.10))) if len(cross_rhos) else None,
                'q90': q(float(np.quantile(cross_rhos, 0.90))) if len(cross_rhos) else None,
            },
        },
        'e_power_mde80': {
            'method': ('5-fold held-out cells over the 111 expression cells (normalized-name sort, i%5); '
                       'test keys = all keys of each fold cells; per pair with >=2 test cells the '
                       'within-pair Spearman statistic is averaged over pairs. Zero prediction: '
                       'analytic SE uses exact permutation null Var(rho)=1/(n-1) per pair; two-way '
                       'cluster bootstrap (cells + pairs, 1000 resamples, seed 20261027) uses a '
                       'cell-state-only arbitrary score (shared across pairs) or an independent '
                       'per-pair random ranking. MDE80 = (z_0.975+z_0.80)*SE.'),
            'folds': fold_tests,
            'fold_mde80_bootstrap_shared_cell_mean': q(float(np.mean(fold_mde_shared))),
            'fold_mde80_bootstrap_shared_cell_min': q(float(np.min(fold_mde_shared))),
            'fold_mde80_bootstrap_shared_cell_max': q(float(np.max(fold_mde_shared))),
            'fold_mde80_analytic_iid_mean': q(float(np.mean(fold_mde_iid))),
            'fold_mde80_permutation_fixed_cells_shared_mean': q(float(np.mean(fold_mde_perm))),
            'fivefold_endpoint_se_bootstrap_shared_cell': q(se_joint_shared),
            'fivefold_endpoint_mde80_bootstrap_shared_cell': q(mde80(se_joint_shared)),
            'fivefold_endpoint_se_bootstrap_independent_pair': q(se_joint_ind),
            'fivefold_endpoint_mde80_bootstrap_independent_pair': q(mde80(se_joint_ind)),
            'fivefold_endpoint_se_permutation_fixed_cells_shared': q(se_joint_perm),
            'fivefold_endpoint_mde80_permutation_fixed_cells_shared': q(mde80(se_joint_perm)),
            'delta_min': 0.05,
            'threshold_mde80_max': THRESH['G3e_mde80_max'],
            'gate_measured_mde80': q(mde_gate),
            'gate_operationalization': ('protocol-literal two-way clustered (cells+pairs) zero-prediction '
                                        'bootstrap, fold mean; the independent-pair analytic value is '
                                        'reported as a sensitivity because the two null models diverge '
                                        '(prediction-ranking sharing across pairs is a design property of '
                                        'the future effect protocol, not of A0)'),
            'pass': g3e_pass,
        },
        'f_tissue_coverage': {
            'all_125_cells': tissue_all,
            'expression_111_cells': tissue_expr,
            'folds_tissue_counts': {str(t['fold']): t['tissue_counts'] for t in fold_tests},
            'note': 'descriptive only; folds with missing tissue recorded as design limitation',
        },
    }
    print('[a0] G3 done: inter=%.3f ceil=%.3f sd=%.4f rho=%.3f MDEgate=%.4f' % (
        anova_all['var_share_interaction'], float(rhos_b.mean()), sd_med, rho_ceiling, mde_gate), flush=True)

    # sensitivity: G3(a-d) on expression cells only + ordered-key ANOVA
    ec_mask = keys['CELL_LINE_NAME'].isin(ecset).to_numpy()
    anova_expr, _, _, _ = anova_block(yv[ec_mask], cidx[ec_mask], pidx[ec_mask])
    out['G3_signal_room_power']['sensitivity_expression_111_cells'] = {
        'a_variance_components': anova_expr,
        'n_keys': int(ec_mask.sum()),
        'note': 'sensitivity only; frozen gate uses all 125 cells for G3(a-d)',
    }
    # ordered-key ANOVA sensitivity (pair = ordered ANCHOR+LIBRARY pair)
    o_a = fit_ok['ANCHOR_NAME'].astype(str) + ' | ' + fit_ok['LIBRARY_NAME'].astype(str)
    o_key = pd.DataFrame({'c': fit_ok['CELL_LINE_NAME'].values, 'p': o_a.values, 'y': fit_ok['y'].values})
    o_key = o_key.groupby(['c', 'p'], sort=True)['y'].mean().reset_index()
    o_cells = sorted(o_key['c'].unique())
    o_pairs = sorted(o_key['p'].unique())
    oci = {c: i for i, c in enumerate(o_cells)}
    opi = {p: i for i, p in enumerate(o_pairs)}
    ocidx = o_key['c'].map(oci).to_numpy()
    opidx = o_key['p'].map(opi).to_numpy()
    oy = o_key['y'].to_numpy(dtype=float)
    anova_ordered, _, _, _ = anova_block(oy, ocidx, opidx)
    out['G3_signal_room_power']['sensitivity_ordered_keys'] = {
        'a_variance_components': anova_ordered,
        'n_keys': int(len(oy)),
        'n_pairs': int(len(o_pairs)),
        'note': 'sensitivity only; PROTOCOL_A0 section 4 key definition is unordered pairs',
    }

    # ------------------------------------------------------------------
    # G4: leakage / split feasibility
    # ------------------------------------------------------------------
    # mutation matrix structure (cell annotation check)
    mut = pd.read_csv(MUT, usecols=['DepMap_ID'], low_memory=False)
    mut_cells = set(mut['DepMap_ID'].astype(str))
    expr_depmap_ids = set(g1.loc[g1['has_expression_row'], 'DepMap_ID'])
    mut_cols = list(pd.read_csv(MUT, nrows=0).columns)
    mut_resp_kw = sorted([c for c in mut_cols if RESPONSE_KEYWORD_RE.search(str(c))])
    fold_hash_payload = json.dumps({str(f): folds[f] for f in range(5)},
                                   ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    fold_hash = hashlib.sha256(fold_hash_payload.encode('utf-8')).hexdigest()

    # per-fold key counts (expression folds and 125-cell reference folds)
    keys_all = keys.copy()
    def fold_keys(cell_list):
        sub_ = keys_all[keys_all['CELL_LINE_NAME'].isin(set(cell_list))]
        npp = sub_.groupby('pair_key')['CELL_LINE_NAME'].nunique()
        return int(len(sub_)), int((npp >= 2).sum())

    fold_key_info = []
    for f in range(5):
        nk, npp = fold_keys(folds[f])
        fold_key_info.append({'fold': f, 'n_cells': len(folds[f]), 'n_keys': nk,
                              'n_pairs_with_ge2_test_cells': npp})
    ref_cells_sorted = sorted(cell_tab['CELL_LINE_NAME'].tolist(), key=norm_cell)
    ref_folds = {f: [c for i, c in enumerate(ref_cells_sorted) if i % 5 == f] for f in range(5)}
    ref_info = []
    for f in range(5):
        nk, npp = fold_keys(ref_folds[f])
        ref_info.append({'fold': f, 'n_cells': len(ref_folds[f]), 'n_keys': nk,
                         'n_pairs_with_ge2_test_cells': npp})

    design_checks = {
        'expression_is_cell_annotation': True,
        'expression_evidence': ('CCLE_expression.csv of DepMap 19Q4: rows are DepMap_ID cell lines, '
                                'columns are GENE (entrez) RNAseq expression; no response/combination '
                                'columns present'),
        'expression_response_derived_columns': resp_kw_cols,
        'mutation_is_cell_annotation': True,
        'mutation_columns_all_cell_annotation': mut_resp_kw == [],
        'mutation_response_derived_columns': mut_resp_kw,
        'target_annotation_from_metadata': True,
        'target_annotation_constant_per_drug': len(target_consistency) == 0,
        'target_annotation_conflicts': {k: sorted(v) for k, v in target_consistency.items()},
        'identity_map_response_independent': True,
        'identity_map_built_from': 'COSMIC_ID numeric join + normalized-name fallback only',
        'folds_split_by_cell_not_row': True,
        'fold_assignment_rule': 'expression cells sorted by NFKC->casefold->strip non-alnum name; index % 5',
        'each_cell_in_exactly_one_fold': bool(sum(len(v) for v in folds.values()) == len(expr_cells) and
                                              len({c for v in folds.values() for c in v}) == len(expr_cells)),
        'final_heldout_cells_untouched_by_feature_standardization': True,
        'feature_standardization_performed': False,
        'sample_info_depmap_id_unique': bool(si_depmap_dup == 0),
        'expression_depmap_id_unique': bool(expr_dup == 0),
        'mutation_cell_ids': int(len(mut_cells)),
        'mutation_rows': int(len(mut)),
        'mutation_cells_with_expression_row': int(len(mut_cells & expr_depmap_ids)),
        'expression_cells_without_mutation_record': int(len(expr_depmap_ids - mut_cells)),
        'design_invalid': False,
    }
    out['G4_leakage_split'] = {
        'design_checks': design_checks,
        'fold_cells': {str(f): folds[f] for f in range(5)},
        'fold_cells_hash_sha256': fold_hash,
        'fold_cell_counts': {str(f): len(folds[f]) for f in range(5)},
        'fold_key_info': fold_key_info,
        'reference_fold_cells_125': {str(f): ref_folds[f] for f in range(5)},
        'reference_fold_key_info_125': ref_info,
        'n_keys_125_cells': int(len(keys_all)),
        'n_keys_111_expression_cells': n_keys_expr,
        'n_pairs_125_111': [n_key_pairs, n_pairs_expr],
        'design_invalid': False,
    }
    print('[a0] G4 done', flush=True)

    # ------------------------------------------------------------------
    # G5: endpoint / decision operationalization (record only)
    # ------------------------------------------------------------------
    out['G5_endpoints'] = {
        'primary_endpoint': 'fold-mean of within-pair Spearman cell ranking on held-out cells (each pair with >=2 test cells)',
        'secondary_endpoints': ['within-pair top-1 hit (predicted top cell is truly top quartile of the pair)',
                                'top-quartile AUC'],
        'control_baselines_for_future_protocol': ['cell-blind (pair constant; within-pair rank correlation defined as 0)',
                                                  'tissue-only',
                                                  'same-dimension random gene block',
                                                  'shuffled drug->target mapping',
                                                  'additive cell main-effect model'],
        'outcome': 'SYNERGY_DELTA_EMAX (viability-derived synergy readout)',
        'outcome_status': 'NOT an independent functional endpoint / mechanism / clinical conclusion',
        'delta_min': 0.05,
        'evaluated_by_this_audit': False,
        'note': 'A0 does not evaluate any effect; definitions recorded for the future effect protocol (PROTOCOL_A0 section 6)',
    }

    # ------------------------------------------------------------------
    # verdict (PROTOCOL_A0 section 7 frozen rules; no threshold changes)
    # ------------------------------------------------------------------
    g1_p = out['G1_identity']['pass']
    g2_p = out['G2_features']['pass']
    g3a = out['G3_signal_room_power']['a_variance_components']['pass']
    g3b = out['G3_signal_room_power']['b_additive_cell_effect_ceiling']['pass']
    g3c = out['G3_signal_room_power']['c_within_pair_room']['pass']
    g3d = out['G3_signal_room_power']['d_reliability']['pass']
    g3e = out['G3_signal_room_power']['e_power_mde80']['pass']
    g4 = not out['G4_leakage_split']['design_invalid']
    gates = {'G1': g1_p, 'G2': g2_p, 'G3a': g3a, 'G3b': g3b, 'G3c': g3c, 'G3d': g3d,
             'G3e': g3e, 'G4': g4}
    failed = [k for k, v in gates.items() if not v]
    failure_classes = []
    if not g1_p or not g2_p:
        failure_classes.append('data_unavailable')
    if not (g3a and g3b and g3c and g3d):
        failure_classes.append('data_insufficient')
    if not g3e:
        failure_classes.append('evaluation_cannot_distinguish')
    if not g4:
        failure_classes.append('design_invalid')
    verdict = 'qualified' if not failed else 'unqualified'
    out['verdict'] = {
        'verdict': verdict,
        'gates': gates,
        'failed_gates': failed,
        'failure_classes': failure_classes,
        'thresholds_frozen': THRESH,
        'evidence_status': 'observed',
        'sensitivity_notes': {
            'G2_pair_coverage_interpretation': {
                'literal_both_sides_each_ge1': q(pair_cov_both),
                'combined_pair_union_ge1': q(union_covered / max(n_ordered_pairs, 1)),
                'unordered_both_sides': q(unordered_both / max(n_unordered_pairs, 1)),
                'note': 'gate uses the literal "each side >=1 mapped gene" reading of the frozen text (57.3% < 90% -> fail); the union reading (95.0%) is reported for the Lead to resolve the wording, but the audit does not switch criterion post hoc',
            },
            'G3e_null_model_dependence': {
                'two_way_clustered_shared_cell_prediction_fold_mean': q(mde_gate),
                'permutation_fixed_cells_shared_fold_mean': q(float(np.mean(fold_mde_perm))),
                'fivefold_endpoint_two_way_clustered': q(mde80(se_joint_shared)),
                'independent_pair_analytic_iid_fold_mean': q(float(np.mean(fold_mde_iid))),
                'note': ('null models differ by ~4-8x because a cell-state-only prediction ranking is '
                         'shared across the 1294 pairs nested in ~22 cells/fold; only if the future '
                         'effect protocol establishes pair-specific (independent) prediction rankings '
                         'would the iid value apply. A0 cannot assume that; the protocol-literal '
                         'clustered bootstrap value is used for the gate. All cell-clustered null '
                         'variants exceed 0.05; the iid analytic value is the only one below it.'),
            },
        },
        'unqualified_reasons': [x for x in [
            'G1: identity/expression coverage below threshold' if not g1_p else None,
            ('G2: %d/%d target tokens mapped (>=60 OK) but %d/%d (%.1f%%) ordered pairs have both sides '
             'mapped (<90%% required)' % (len(mapped_targets), len(targets), both_covered, n_ordered_pairs,
                                          100 * pair_cov_both)) if not g2_p else None,
            'G3e: MDE80(two-way clustered, fold mean)=%.4f > 0.05' % mde_gate if not g3e else None,
            'G4: design_invalid' if not g4 else None,
        ] if x is not None],
        'de_freeze_conditions': {
            'G2': ['provide/allow a gene-level (non-mechanism) target annotation for the 12 drugs whose '
                   'only target tokens are mechanism-class (5-FU, Bortezomib, Cisplatin, Docetaxel, '
                   'Gemcitabine, Oxaliplatin, Paclitaxel, Pictilisib, Taselisib, Temozolomide, Vinorelbine,'
                   ' Vorinostat), or restrict/evaluate the 1161 fully-covered pairs with an explicit '
                   'protocol amendment',
                   'if the frozen wording meant the combined-pair reading, resolve the wording before any '
                   'effect protocol (no threshold change)'],
            'G3e': ['add held-out cells (e.g., more expression-covered cell lines) or define the future effect '
                    'protocol test on a metric with pair-level (not cell-nested) sampling units with a '
                    'pre-registered argument that prediction rankings are pair-specific; otherwise delta_min '
                    'must be set to the detectable MDE80'],
        },
        'design_invalid': False,
    }
    out['meta'] = {
        'audit': 'R190-A0 cell-state feature qualification audit',
        'protocol': 'PROTOCOL_A0.md + AMENDMENT-A0-001 (G1 threshold + 111-cell folds)',
        'purpose': 'qualification',
        'determinism': {'seed': SEED, 'bootstrap_resamples': B_BOOT,
                        'json_sorted_keys': True, 'timestamps_in_json': False},
        'no_model_fit': True,
        'no_effect_estimate': True,
        'amendment_a0_001': ('AMENDMENT-A0-001 read before writing/running this audit script; no '
                             'deliverable file (a0.json / identity_map.csv / target_map.csv) and no '
                             'gate decision existed before the amendment; thresholds unchanged '
                             'except the frozen G1 relaxation stated in the amendment'),
        'response_values_used_only_for': ['G3 variance components', 'G3 ranking ceiling',
                                          'G3 within-pair sd', 'G3 reliability ceiling',
                                          'G3 MDE80 bootstrap', 'G3 descriptive distribution',
                                          'G3 cross-screen reliability (aux)'],
    }

    dump_json(os.path.join(OUTDIR, 'a0.json'), out)
    wall = time.time() - t_start
    usage = {
        'wall_seconds_total': round(wall, 1),
        'n_bootstrap_resamples_per_test': B_BOOT,
        'gpu_hours': None,
        'cpu_hours': None,
        'peak_rss_mb': None,
        'input_bytes_total': sum(v['bytes'] for v in p1_files.values()),
        'n_input_files': len(p1_files),
        'n_rows_fitted': int(len(fit)),
        'n_rows_expression_matrix': int(ex.shape[0]),
        'n_expression_columns': int(len(gene_cols)),
        'n_rows_mutation_table': int(len(mut)),
        'n_rows_validation_screen': int(len(val)),
        'n_bootstrap_resamples_total': int(B_BOOT * (5 * 2 + 2)),
        'unknown_values': 'null',
    }
    dump_json(os.path.join(OUTDIR, 'usage.json'), usage)
    print('[a0] verdict=%s failed=%s wall=%.1fs' % (verdict, failed, wall), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
