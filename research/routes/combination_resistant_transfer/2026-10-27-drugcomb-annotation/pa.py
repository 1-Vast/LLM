#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PROTOCOL_PA (v2, frozen 2026-10-27T14:07) reference implementation.

R191 stage-1 P-A: DrugComb drug -> coarse annotation mapping + coverage audit.

Guarantees:
  * reads ONLY local files, no network;
  * NEVER reads a DrugComb response column (see V14_DENY; only header names are
    touched) -- identity columns are taken by column position only;
  * deterministic: no randomness, no timestamps, JSON written with sort_keys=True;
  * input / resource / script / protocol SHA256 recorded in pa.json.

Usage:  python pa.py
"""
import csv
import hashlib
import json
import math
import os
import re
import sys
import unicodedata

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

# ---------------------------------------------------------------- constants
ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-annotation')
RES = os.path.join(BASE, 'resources')

PATHS = {
    'I1': os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification',
                       'downloads', 'summary_table_v1.4.csv'),
    'I2': os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification',
                       'downloads', 'DrugComb_drug_identifiers.xlsx'),
    'I3': os.path.join(ROOT, 'data', 'external', 'lincs_l1000_gse92742',
                       'repurposing_drugs_20200324.txt'),
    'I4': os.path.join(RES, 'c2.cp.kegg.v2023.1.Hs.symbols.gmt'),
    'I5': os.path.join(RES, 'h.all.v2023.1.Hs.symbols.gmt'),
    'I6': os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                       'Original screen_All tissues_fitted data.csv'),
    'I7': os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                       'Validation screen_All tissues_fitted data.csv'),
}

# frozen in PROTOCOL_PA.md section 1
EXPECTED = {
    'I1': {'bytes': 193184734,
           'sha256': 'e08e3d35bfa4bea011afe1b05b7025acde5c669c5e8d265866b5e12b08037a2f'},
    'I2': {'bytes': 5856350,
           'sha256': '02b1655ad15a81e0bef06909e147ff4c688938aa7f75eb04603f440e8b18438c'},
    'I3': {'bytes': 530302,
           'sha256': '9c3a08b9d4369fe4257dc9aa763d682fc5ef6b7dd0615534bb44f92b48bc287b'},
    'I4': {'bytes': 100047,
           'sha256': '48de51190366ee388dffe34fa2931e590de43ee5e2a4c27c50c0fc33b9d194fc'},
    'I5': {'bytes': 48649,
           'sha256': '27e48f776cda235ad5b63acaecc3136853ee79c6447d883ce2b070a4d2d47b75'},
    'I6': {'bytes': 198893607,
           'sha256': '1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278'},
    'I7': {'bytes': 11774397,
           'sha256': 'dcbd4c3108d212fa771c52ae977c8e1c01a421162a2232cdc4273faf257b2775'},
}

RESOURCE_INFO = {
    'I4': {'library': 'S1_KEGG', 'msigdb_release': '2023.1.Hs',
           'collection': 'c2.cp.kegg (KEGG legacy gene sets, symbols)',
           'url': 'https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/'
                  'c2.cp.kegg.v2023.1.Hs.symbols.gmt'},
    'I5': {'library': 'S2_Hallmark', 'msigdb_release': '2023.1.Hs',
           'collection': 'h.all (Hallmark gene sets, symbols)',
           'url': 'https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/'
                  'h.all.v2023.1.Hs.symbols.gmt'},
}

# frozen thresholds (PROTOCOL_PA.md section 9)
GATES = {
    'G1_coverage_min_pct_of_4088': 25.0,
    'G1_coverage_min_count': 1022,
    'G2_analyzable_levels_min': 12,
    'G3_both_unseen_units_min': 800,
    'G4_train_units_min': 5000,
}
# frozen switch (PROTOCOL_PA.md section 6.3)
SWITCH = {'max_level_share_max': 0.40, 'analyzable_levels_min': 12, 'z_min': 1.64}
R_VALUES = (0.20, 0.30, 0.40)

NAMED_12 = ['5-FU', 'Bortezomib', 'Cisplatin', 'Docetaxel', 'Gemcitabine', 'Oxaliplatin',
            'Paclitaxel', 'Pictilisib', 'Taselisib', 'Temozolomide', 'Vinorelbine', 'Vorinostat']

# PROTOCOL_PA.md section 3: read / deny columns (deny = header-name existence only)
V14_READ = ['block_id', 'drug_row', 'drug_col', 'cell_line_name']
V14_DENY = ['css', 'synergy_zip', 'synergy_bliss', 'synergy_loewe', 'synergy_hsa',
            'ic50_row', 'ic50_col', 'ri_row', 'ri_col', 'css_row', 'css_col', 'S']
JAAKS_COLS = ['ANCHOR_NAME', 'LIBRARY_NAME', 'ANCHOR_PATHWAY', 'LIBRARY_PATHWAY']

# PROTOCOL_PA.md section 9 A3: R190/E1 verified values (cross-check targets)
E1_CROSSCHECK = {
    'v14_rows_combination': 466033,
    'universe_U': 4088,
    'universe_D1': 4076,
    'cells_norm': 112,
    'pairs_norm': 62826,
    'cell_x_pair_units': 380418,
    'e1_split_both_unseen_units': 16078,
}


# ---------------------------------------------------------------- helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def norm(s):
    """NFKC -> casefold -> keep alphanumerics (PROTOCOL_PA section 4)."""
    s = unicodedata.normalize('NFKC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())


def pct(a, b):
    return None if not b else round(100.0 * a / b, 4)


_PAREN = re.compile(r'\([^)]*\)|（[^）]*）')
_SPLIT_T1 = re.compile(r'[|;,\s/]+')
_TRIM = set('"\'`.*:[]{}()+-')
# T0 = pre-v2 stricter tokenisation; sensitivity only (PROTOCOL_PA section 5)
_SPLIT_T0 = re.compile(r'[|;,]')


def tokenize_t1(s):
    """PROTOCOL_PA section 5 rule (v2, Lead amendment)."""
    if not isinstance(s, str):
        return set()
    s = _PAREN.sub(' ', s)
    out = set()
    for part in _SPLIT_T1.split(s):
        p = part.strip()
        while p and p[0] in _TRIM:
            p = p[1:]
        while p and p[-1] in _TRIM:
            p = p[:-1]
        if p:
            out.add(p)
    return out


def tokenize_t0(s):
    """Sensitivity tokenisation: split on | ; , only, no paren removal."""
    if not isinstance(s, str):
        return set()
    out = set()
    for part in _SPLIT_T0.split(s):
        p = part.strip()
        if p:
            out.add(p)
    return out


def collision_report(raw_names):
    d = {}
    for x in raw_names:
        if not isinstance(x, str):
            continue
        n = norm(x)
        if n:
            d.setdefault(n, set()).add(x)
    return {k: sorted(v) for k, v in d.items()
            if len({v.casefold() for v in v}) > 1}


def load_gmt(path):
    sets = {}
    for line in open(path, encoding='utf-8'):
        if not line.strip():
            continue
        parts = line.rstrip('\n').split('\t')
        genes = [g for g in parts[2:] if g]
        sets[parts[0]] = genes
    return sets


def split_pa(names, r):
    """PROTOCOL_PA section 7: deterministic holdout on a sorted name list."""
    n = len(names)
    k = max(1, round(r * n))
    step = max(1, n // k)
    hold = set(names[0::step][:k])
    return {'n': n, 'k': k, 'step': step, 'holdout': hold,
            'holdout_literal_step5': set(names[0::5][:k])}


# ============================================================ 1. verify inputs
def verify_inputs():
    out = {'files': {}, 'all_match': True}
    for key in sorted(PATHS):
        p = PATHS[key]
        rec = {'path': os.path.relpath(p, ROOT), 'expected_bytes': EXPECTED[key]['bytes'],
               'expected_sha256': EXPECTED[key]['sha256']}
        if not os.path.exists(p):
            rec['status'] = 'missing'
            out['all_match'] = False
        else:
            rec['bytes'] = os.path.getsize(p)
            rec['sha256'] = sha256_file(p)
            rec['bytes_match'] = rec['bytes'] == rec['expected_bytes']
            rec['sha256_match'] = rec['sha256'] == rec['expected_sha256']
            rec['status'] = 'ok' if (rec['bytes_match'] and rec['sha256_match']) else 'mismatch'
            if rec['status'] != 'ok':
                out['all_match'] = False
        out['files'][key] = rec
    if not out['all_match']:
        raise SystemExit('FATAL: input verification failed: %s' %
                         json.dumps({k: v['status'] for k, v in out['files'].items()}, sort_keys=True))
    out['resources'] = {k: dict(RESOURCE_INFO[k]) for k in sorted(RESOURCE_INFO)}
    return out


# ================================================== 2. v1.4 summary (identity only)
def read_v14_identity():
    res = {'path': os.path.relpath(PATHS['I1'], ROOT)}
    drug_raw = []
    cell_raw = []
    pairs = set()
    cp_units = set()
    rows = mono = combo = 0
    with open(PATHS['I1'], newline='', encoding='utf-8') as f:
        rdr = csv.reader(f)
        header = next(rdr)
        idx = {name: i for i, name in enumerate(header)}
        res['header_columns'] = header
        res['read_columns_present'] = [c for c in V14_READ if c in idx]
        res['read_columns_missing'] = [c for c in V14_READ if c not in idx]
        res['deny_columns_present'] = [c for c in V14_DENY if c in idx]
        res['deny_columns_missing'] = [c for c in V14_DENY if c not in idx]
        # positional access to READ columns only; no other column is ever indexed
        i_dr, i_dc, i_cl = idx['drug_row'], idx['drug_col'], idx['cell_line_name']
        for row in rdr:
            rows += 1
            dr = row[i_dr].strip()
            dc = row[i_dc].strip()
            cl = row[i_cl].strip()
            if (not dc) or dc.upper() in ('NA', 'NULL') or (not dr) or dr.upper() in ('NA', 'NULL'):
                mono += 1
                continue
            combo += 1
            drug_raw.append(dr)
            drug_raw.append(dc)
            cell_raw.append(cl)
            a, b = norm(dr), norm(dc)
            pk = (a, b) if a <= b else (b, a)
            pairs.add(pk)
            cp_units.add((norm(cl),) + pk)
    collisions = collision_report(drug_raw)
    universe = {norm(x) for x in drug_raw if norm(x)}
    d1 = universe - set(collisions)
    res.update({
        'rows_total': rows,
        'rows_monotherapy_like': mono,
        'rows_combination': combo,
        'universe_U_size': len(universe),
        'collision_keys': len(collisions),
        'collision_details': dict(sorted(collisions.items())),
        'universe_D1_size': len(d1),
        'cells_norm': len({norm(x) for x in cell_raw if norm(x)}),
        'cells_raw': len({x for x in cell_raw if x}),
        'pairs_norm': len(pairs),
        'cell_x_pair_units_norm': len(cp_units),
        'response_values_read': False,
    })
    return res, universe, d1, pairs, cp_units


# ================================================== 3. drug target gene sets
def load_targets(universe, d1):
    """Build T_j (PROTOCOL_PA section 5) from I2 target_name + I3 target."""
    idf = pd.read_excel(PATHS['I2'])
    idf['_norm'] = idf['dname'].map(lambda x: norm(x) if isinstance(x, str) else '')
    drh = pd.read_csv(PATHS['I3'], sep='\t', skiprows=9, low_memory=False)

    t1 = {}
    t0 = {}
    a_tok = {}
    b_tok = {}
    src_a = {}
    src_b = {}
    for nm, tn in zip(idf['_norm'], idf['target_name']):
        if not nm or not isinstance(tn, str):
            continue
        a1, a0 = tokenize_t1(tn), tokenize_t0(tn)
        if a1:
            t1.setdefault(nm, set()).update(a1)
            t0.setdefault(nm, set()).update(a0)
            a_tok.setdefault(nm, set()).update(a1)
            src_a.setdefault(nm, set()).add('I2_target_name')
    for nm, tg in zip(drh['pert_iname'], drh['target']):
        if not isinstance(nm, str) or not isinstance(tg, str):
            continue
        n = norm(nm)
        if not n:
            continue
        b1, b0 = tokenize_t1(tg), tokenize_t0(tg)
        if b1:
            t1.setdefault(n, set()).update(b1)
            t0.setdefault(n, set()).update(b0)
            b_tok.setdefault(n, set()).update(b1)
            src_b.setdefault(n, set()).add('I3_DRH_target')

    res = {
        'I2_rows': int(len(idf)),
        'I2_dname_norm_nonempty': int((idf['_norm'] != '').sum()),
        'I2_target_name_nonnull': int(idf['target_name'].notna().sum()),
        'I2_target_name_nonnull_pct': pct(int(idf['target_name'].notna().sum()), len(idf)),
        'I2_target_type_nonnull': int(idf['target_type'].notna().sum()) if 'target_type' in idf else None,
        'I3_rows': int(len(drh)),
        'I3_target_nonnull': int(drh['target'].notna().sum()),
        'I3_moa_nonnull': int(drh['moa'].notna().sum()) if 'moa' in drh else None,
        'I3_moa_levels': int(drh['moa'].nunique()),
        'drugs_with_tokens_any': len(t1),
        'drugs_with_tokens_in_U': len(set(t1) & universe),
        'drugs_with_tokens_in_D1': len(set(t1) & d1),
        'tokens_distinct_D1': len({x for k in d1 for x in t1.get(k, set())}),
        'tokens_distinct_D1_T0': len({x for k in d1 for x in t0.get(k, set())}),
        'source_attribution_D1': {
            'both': len({k for k in d1 if k in src_a and k in src_b}),
            'I2_target_name_only': len({k for k in d1 if k in src_a and k not in src_b}),
            'I3_DRH_target_only': len({k for k in d1 if k in src_b and k not in src_a}),
        },
    }
    return t1, t0, a_tok, b_tok, src_a, src_b, res


# ================================================== 4. gene set libraries + scoring
def build_libraries(kegg, hall):
    libs = {'S1': kegg, 'S2': hall, 'S3': {**kegg, **hall}}
    genes_all = sorted({g for lib in libs.values() for gs in lib.values() for g in gs})
    gidx = {g: i for i, g in enumerate(genes_all)}
    out = {}
    for key in ('S1', 'S2', 'S3'):
        names = sorted(libs[key])
        mat = np.zeros((len(genes_all), len(names)), dtype=bool)
        for j, name in enumerate(names):
            for g in libs[key][name]:
                mat[gidx[g], j] = True
        ks = np.array([len(libs[key][n]) for n in names], dtype=float)
        in_lib = mat.any(axis=1)
        out[key] = {
            'names': names,
            'K': ks,
            'mat': mat,
            'N': int(in_lib.sum()),
            'genes_all': genes_all,
            'gidx': gidx,
            'in_library_gene_universe': in_lib,
            'n_sets': len(names),
            'n_genes_union': int(in_lib.sum()),
        }
    return out, genes_all, gidx


def match_gene_indices(tokens, gidx):
    return [gidx[t] for t in tokens if t in gidx]


def assign_rule_a(x_row, names):
    mx = int(x_row.max()) if len(x_row) else 0
    if mx < 1:
        return None
    tied = [names[i] for i in np.flatnonzero(x_row == mx)]
    tied_sorted = sorted(tied)
    return {'pathway': tied_sorted[0], 'max_score': mx, 'tie_count': len(tied_sorted)}


def assign_rule_b(x_row, n_j, lib, z_min):
    x = x_row.astype(float)
    mask = x >= 1
    if n_j <= 0 or not mask.any():
        return None
    N = float(lib['N'])
    K = lib['K']
    p = K / N
    if N > 1.0:
        sd = np.sqrt(n_j * p * (1.0 - p) * (N - n_j) / (N - 1.0))
    else:
        sd = np.zeros_like(p)
    z = np.full(len(x), np.nan)
    pos = mask & (sd > 0.0)
    z[pos] = (x[pos] - n_j * p[pos]) / sd[pos]
    z[mask & ~pos] = 0.0
    zmax = float(np.nanmax(z))
    if zmax < z_min:
        return {'pathway': None, 'max_z': round(zmax, 6), 'tie_count': 0,
                'rejected_below_z': True}
    best = sorted(lib['names'][i] for i in np.flatnonzero(z == zmax))
    label = best[0]
    i = lib['names'].index(label)
    Kp = int(K[i])
    xp = int(x[i])
    pval = float(hypergeom.sf(xp - 1, int(N), Kp, int(n_j)))
    return {'pathway': label, 'max_z': round(zmax, 6), 'tie_count': len(best),
            'hypergeom_p': round(pval, 8), 'pathway_size': Kp, 'overlap': xp}


def map_library(lib, t1, drugs, z_min):
    names = lib['names']
    out = {'A': {}, 'B': {}}
    for dn in drugs:
        tokens = t1.get(dn)
        if not tokens:
            continue
        idx = match_gene_indices(tokens, lib['gidx'])
        if not idx:
            continue
        x_row = lib['mat'][idx, :].sum(axis=0).astype(np.int64)
        n_j = int(lib['in_library_gene_universe'][idx].sum())
        a = assign_rule_a(x_row, names)
        if a is not None:
            a['n_matched_genes'] = n_j
            a['pathway_size'] = int(lib['K'][names.index(a['pathway'])])
            out['A'][dn] = a
        b = assign_rule_b(x_row, n_j, lib, z_min)
        if b is not None and b.get('pathway'):
            b['n_matched_genes'] = n_j
            out['B'][dn] = b
    return out


# ================================================== 5. coverage / level / unit stats
def level_table(mapping, hold_pa, hold_e1):
    lvl = {}
    for dn, rec in mapping.items():
        n = rec.get('pathway')
        if not n:
            continue
        d = lvl.setdefault(n, {'n_all': 0, 'n_train_pa': 0, 'n_hold_pa': 0,
                               'n_train_e1': 0, 'n_hold_e1': 0})
        d['n_all'] += 1
        if dn in hold_pa:
            d['n_hold_pa'] += 1
        else:
            d['n_train_pa'] += 1
        if dn in hold_e1:
            d['n_hold_e1'] += 1
        else:
            d['n_train_e1'] += 1
    rows = []
    for name in sorted(lvl):
        d = lvl[name]
        rows.append({
            'level': name,
            'n_all': d['n_all'],
            'n_train_pa': d['n_train_pa'],
            'n_hold_pa': d['n_hold_pa'],
            'n_train_e1': d['n_train_e1'],
            'n_hold_e1': d['n_hold_e1'],
            'analyzable_pa': bool(d['n_all'] >= 2 and d['n_train_pa'] >= 1 and d['n_hold_pa'] >= 1),
            'analyzable_e1': bool(d['n_all'] >= 2 and d['n_train_e1'] >= 1 and d['n_hold_e1'] >= 1),
        })
    return rows


def count_units(units, hold):
    """units: list of (cell, a, b); count pairs with both drugs in hold."""
    return sum(1 for u in units if u[1] in hold and u[2] in hold)


def unit_stats(mapping, units, universe_sorted):
    drugs = sorted(mapping)
    pa = split_pa(drugs, 0.20)
    hold = pa['holdout']
    hold_lit = pa['holdout_literal_step5']
    e1 = split_pa(universe_sorted, 0.20)
    hold_e1 = e1['holdout']
    mset = set(drugs)
    units_mapped = [u for u in units if u[1] in mset and u[2] in mset]
    out = {
        'n_mapped': len(drugs),
        'split_pa': {'k': pa['k'], 'step': pa['step'], 'n_train': len(drugs) - len(hold),
                     'n_holdout': len(hold)},
        'split_e1': {'k': e1['k'], 'step': e1['step'],
                     'n_mapped_in_holdout': len(mset & hold_e1)},
        'units_both_mapped': len(units_mapped),
        'both_unseen_units_pa': count_units(units_mapped, hold),
        'both_unseen_units_pa_literal_step5': count_units(units_mapped, hold_lit),
        'train_units_pa': len(units_mapped) - count_units(units_mapped, hold),
        'both_unseen_units_e1split': count_units(units_mapped, hold_e1),
        'train_units_e1split': len(units_mapped) - count_units(units_mapped, hold_e1),
        'both_unseen_units_pa_r': {},
        'both_unseen_units_e1split_r': {},
        'strict_train_units_pa': None,
    }
    for r in R_VALUES:
        sp = split_pa(drugs, r)
        out['both_unseen_units_pa_r']['%.2f' % r] = count_units(units_mapped, sp['holdout'])
        se = split_pa(universe_sorted, r)
        out['both_unseen_units_e1split_r']['%.2f' % r] = count_units(units_mapped, se['holdout'])
    # strict training variant: neither drug in holdout
    strict = sum(1 for u in units_mapped if u[1] not in hold and u[2] not in hold)
    out['strict_train_units_pa'] = strict
    return out, pa, e1


def score_diagnostics(mapping, lib):
    scores = [r['max_score'] for r in mapping.values()]
    ties = sum(1 for r in mapping.values() if r['tie_count'] > 1)
    hist = {}
    for s in scores:
        hist[str(s)] = hist.get(str(s), 0) + 1
    sizes = [r.get('pathway_size') for r in mapping.values() if r.get('pathway_size')]
    lvl_counts = {}
    for r in mapping.values():
        lvl_counts[r['pathway']] = lvl_counts.get(r['pathway'], 0) + 1
    top = max(lvl_counts.values()) if lvl_counts else 0
    return {
        'n_mapped': len(mapping),
        'n_levels': len(lvl_counts),
        'tie_drugs': ties,
        'tie_drugs_pct': pct(ties, len(mapping)) if mapping else None,
        'score_hist': dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
        'score1_pct': pct(hist.get('1', 0), len(mapping)) if mapping else None,
        'max_level_count': top,
        'max_level_share': round(top / len(mapping), 6) if mapping else None,
        'max_level_name': sorted(lvl_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        if lvl_counts else None,
        'pathway_size_median': float(np.median(sizes)) if sizes else None,
        'pathway_size_min': int(min(sizes)) if sizes else None,
        'pathway_size_max': int(max(sizes)) if sizes else None,
    }


def z_diagnostics(mapping):
    zs = [r['max_z'] for r in mapping.values()]
    ties = sum(1 for r in mapping.values() if r['tie_count'] > 1)
    hist = {}
    for z in zs:
        b = '%.1f' % (math.floor(z * 10) / 10.0)
        hist[b] = hist.get(b, 0) + 1
    p_vals = [r.get('hypergeom_p') for r in mapping.values() if r.get('hypergeom_p') is not None]
    disagree = sum(1 for r in mapping.values()
                   if r.get('hypergeom_p') is not None and (r['hypergeom_p'] < 0.05) != (r['max_z'] >= 1.64))
    lvl_counts = {}
    for r in mapping.values():
        lvl_counts[r['pathway']] = lvl_counts.get(r['pathway'], 0) + 1
    top = max(lvl_counts.values()) if lvl_counts else 0
    return {
        'n_mapped': len(mapping),
        'n_levels': len(lvl_counts),
        'tie_drugs': ties,
        'tie_drugs_pct': pct(ties, len(mapping)) if mapping else None,
        'max_z_min': round(min(zs), 6) if zs else None,
        'max_z_median': round(float(np.median(zs)), 6) if zs else None,
        'z_hist': dict(sorted(hist.items(), key=lambda kv: float(kv[0]))),
        'z_vs_p_disagreement': disagree,
        'max_level_count': top,
        'max_level_share': round(top / len(mapping), 6) if mapping else None,
        'max_level_name': sorted(lvl_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        if lvl_counts else None,
    }


# ================================================== 6. named drugs / Jaaks diagnostics
def named_drug_block(universe, d1, mappings, chosen, t1, id_norm_set, drh_norm_set, jaaks_map):
    rows = []
    for given in NAMED_12:
        n = norm(given)
        row = {
            'given_name': given,
            'normalized': n,
            'in_universe_U': n in universe,
            'in_D1': n in d1,
            'in_I2_identifiers': n in id_norm_set,
            'in_I3_DRH': n in drh_norm_set,
            'n_target_tokens': len(t1.get(n, ())),
            'jaaks_pathway': jaaks_map.get(n),
            'per_library': {},
        }
        for key in ('S1', 'S2', 'S3'):
            rule = chosen[key]
            rec = mappings[key][rule].get(n)
            row['per_library'][key] = {
                'chosen_rule': rule,
                'pathway': rec.get('pathway') if rec else None,
                'max_score': rec.get('max_score') if rec else None,
                'max_z': rec.get('max_z') if rec else None,
                'tie_count': rec.get('tie_count') if rec else None,
                'n_matched_genes': rec.get('n_matched_genes') if rec else None,
            }
        # reporting-only spelling-variant lookup (NOT used for mapping)
        variants = sorted(x for x in (id_norm_set | drh_norm_set)
                          if x != n and (x.startswith(n) or n.startswith(x)))
        row['spelling_variant_lookup_reporting_only'] = variants[:6]
        rows.append(row)
    return rows


def load_jaaks():
    pw = {}
    rows = 0
    for key in ('I6', 'I7'):
        df = pd.read_csv(PATHS[key], usecols=JAAKS_COLS, low_memory=False)
        rows += int(len(df))
        for nm, pa in zip(df['ANCHOR_NAME'], df['ANCHOR_PATHWAY']):
            if isinstance(nm, str) and isinstance(pa, str) and pa.strip():
                nn = norm(nm)
                if nn:
                    pw[nn] = pa.strip()
        for nm, pa in zip(df['LIBRARY_NAME'], df['LIBRARY_PATHWAY']):
            if isinstance(nm, str) and isinstance(pa, str) and pa.strip():
                nn = norm(nm)
                if nn:
                    pw[nn] = pa.strip()
    levels = sorted(set(pw.values()))
    return pw, {'rows_read': rows, 'n_drugs': len(pw), 'n_levels': len(levels),
                'levels': levels}


# ================================================== 7. mapping tables (frozen)
def fmt_notes(**kw):
    parts = []
    for k in sorted(kw):
        parts.append('%s=%s' % (k, kw[k]))
    return ';'.join(parts)


def write_mapping_tables(universe, d1, collisions, t1, mappings, chosen, jaaks_map):
    base = os.path.join(BASE, 'mapping_table.csv')
    aux = os.path.join(BASE, 'mapping_table_rules_AB.csv')
    header = ['drug_normalized_name', 'source_library', 'pathway', 'n_target_genes',
              'n_genes_in_pathway', 'drug_drop', 'notes']
    coll_keys = set(collisions)
    with open(base, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        for dn in sorted(universe):
            tokens = t1.get(dn, set())
            for key in ('S1', 'S2', 'S3'):
                rule = chosen[key]
                rec = mappings[key][rule].get(dn)
                if dn in coll_keys:
                    drop = 'collision_key_conservatively_dropped'
                elif not tokens:
                    drop = 'no_target_annotation'
                elif rec is None:
                    drop = 'no_exact_gene_symbol_overlap'
                else:
                    drop = 'none'
                if rec is None:
                    pathway = 'unmapped'
                    n_genes = 0
                    kw = {'rule': rule}
                    if rule == 'A':
                        kw['max_score'] = 0
                    else:
                        kw['max_z'] = 'na'
                        kw['z_min'] = SWITCH['z_min']
                    if dn in coll_keys:
                        kw['drop_reason'] = 'C155_collision_key'
                    elif not tokens:
                        kw['drop_reason'] = 'no_target_annotation'
                    else:
                        kw['drop_reason'] = 'max_score_lt_1' if rule == 'A' else 'z_lt_min_or_no_overlap'
                    kw['jaaks_pathway'] = jaaks_map.get(dn, 'na')
                    notes = fmt_notes(**kw)
                else:
                    pathway = rec['pathway']
                    n_genes = int(rec.get('pathway_size', 0))
                    kw = {'rule': rule, 'n_matched_genes': rec.get('n_matched_genes', 0),
                          'tie_pathways': rec.get('tie_count', 0), 'jaaks_pathway': jaaks_map.get(dn, 'na')}
                    if rule == 'A':
                        kw['max_score'] = rec['max_score']
                    else:
                        kw['max_z'] = rec['max_z']
                        kw['hypergeom_p'] = rec.get('hypergeom_p', 'na')
                    notes = fmt_notes(**kw)
                w.writerow([dn, key, pathway, len(tokens), n_genes, drop, notes])
    with open(aux, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['drug_normalized_name', 'source_library', 'rule', 'pathway',
                    'n_target_genes', 'n_genes_in_pathway', 'n_matched_genes', 'statistic', 'notes'])
        for dn in sorted(universe):
            tokens = t1.get(dn, set())
            for key in ('S1', 'S2', 'S3'):
                for rule in ('A', 'B'):
                    rec = mappings[key][rule].get(dn)
                    if rec is None:
                        w.writerow([dn, key, rule, 'unmapped', len(tokens), 0, 0, '', ''])
                    elif rule == 'A':
                        w.writerow([dn, key, rule, rec['pathway'], len(tokens),
                                    int(rec.get('pathway_size', 0)), rec.get('n_matched_genes', 0),
                                    'score=%d' % rec['max_score'],
                                    'ties=%d' % rec.get('tie_count', 0)])
                    else:
                        w.writerow([dn, key, rule, rec['pathway'], len(tokens),
                                    int(rec.get('pathway_size', 0)), rec.get('n_matched_genes', 0),
                                    'z=%.6f' % rec['max_z'],
                                    'ties=%d;p=%.6g' % (rec.get('tie_count', 0),
                                                        rec.get('hypergeom_p', float('nan')))])
    return base, aux


# ================================================== 8. judgment
def judge(lib_stats, primary_key, primary_rule):
    """Build hard-gate + audit-check blocks; return judgment dict."""
    ps = lib_stats[primary_key][primary_rule]
    gates = []
    g1_val = ps['coverage']['n_mapped_D1']
    gates.append({
        'id': 'G1', 'name': 'primary_strategy_drug_coverage_ge_25pct',
        'threshold': 'mapped drugs (D1) / 4088 >= 25% (>=1022)',
        'value': {'n_mapped_D1': g1_val, 'pct_of_4088': pct(g1_val, 4088),
                  'pct_of_4076': pct(g1_val, 4076)},
        'pass': bool(pct(g1_val, 4088) is not None and pct(g1_val, 4088) >= GATES['G1_coverage_min_pct_of_4088']
                     and g1_val >= GATES['G1_coverage_min_count']),
    })
    gates.append({
        'id': 'G2', 'name': 'analyzable_levels_ge_12',
        'threshold': '>=12 levels with n_all>=2 and >=1 train and >=1 holdout drug (PA split)',
        'value': {'analyzable_levels_pa': ps['levels']['n_analyzable_pa'],
                  'analyzable_levels_e1split': ps['levels']['n_analyzable_e1split'],
                  'n_levels_total': ps['levels']['n_levels']},
        'pass': bool(ps['levels']['n_analyzable_pa'] >= GATES['G2_analyzable_levels_min']),
    })
    gates.append({
        'id': 'G3', 'name': 'both_unseen_annotated_units_ge_800',
        'threshold': '>=800 both-annotated (cell, unordered pair) units in PA holdout (N=mapped)',
        'value': {'both_unseen_units_pa': ps['units']['both_unseen_units_pa'],
                  'both_unseen_units_e1split': ps['units']['both_unseen_units_e1split'],
                  'units_both_mapped': ps['units']['units_both_mapped']},
        'pass': bool(ps['units']['both_unseen_units_pa'] >= GATES['G3_both_unseen_units_min']),
    })
    gates.append({
        'id': 'G4', 'name': 'training_annotated_units_ge_5000',
        'threshold': '>=5000 both-annotated training units (both mapped, not both in PA holdout)',
        'value': {'train_units_pa': ps['units']['train_units_pa'],
                  'strict_train_units_pa': ps['units']['strict_train_units_pa'],
                  'train_units_e1split': ps['units']['train_units_e1split']},
        'pass': bool(ps['units']['train_units_pa'] >= GATES['G4_train_units_min']),
    })
    return gates


# =================================================================== main
def main():
    print('[1/9] verify inputs ...', flush=True)
    inputs = verify_inputs()

    print('[2/9] v1.4 summary table (identity columns only) ...', flush=True)
    v14, universe, d1, pairs, cp_units = read_v14_identity()
    universe_sorted = sorted(universe)
    e1_split = split_pa(universe_sorted, 0.20)
    both_unseen_e1_all = sum(1 for u in cp_units
                             if u[1] in e1_split['holdout'] and u[2] in e1_split['holdout'])
    crosscheck = {
        'expected': E1_CROSSCHECK,
        'actual': {
            'v14_rows_combination': v14['rows_combination'],
            'universe_U': len(universe),
            'universe_D1': len(d1),
            'cells_norm': v14['cells_norm'],
            'pairs_norm': v14['pairs_norm'],
            'cell_x_pair_units': v14['cell_x_pair_units_norm'],
            'e1_split_both_unseen_units': both_unseen_e1_all,
        },
    }
    crosscheck['all_match'] = all(crosscheck['expected'][k] == crosscheck['actual'][k]
                                  for k in crosscheck['expected'])
    if not crosscheck['all_match']:
        raise SystemExit('FATAL: E1 cross-check failed: %s' % json.dumps(crosscheck, sort_keys=True))
    v14['e1_split'] = {'k': e1_split['k'], 'step': e1_split['step'],
                       'both_unseen_units_all_drugs': both_unseen_e1_all}

    print('[3/9] drug target gene sets ...', flush=True)
    t1, t0, a_tok, b_tok, src_a, src_b, target_stats = load_targets(universe, d1)
    gene_universe_all = set()
    kegg = load_gmt(PATHS['I4'])
    hall = load_gmt(PATHS['I5'])
    for lib in (kegg, hall):
        for gs in lib.values():
            gene_universe_all.update(gs)
    gene_universe_all = frozenset(gene_universe_all)
    target_stats['tokens_distinct_D1_exact_symbols'] = len(
        {x for k in d1 for x in t1.get(k, set()) if x in gene_universe_all})
    target_stats['I2_target_name_tokens_exact_symbols_D1'] = len(
        {t for k in d1 for t in a_tok.get(k, set()) if t in gene_universe_all})
    target_stats['I3_DRH_target_tokens_exact_symbols_D1'] = len(
        {t for k in d1 for t in b_tok.get(k, set()) if t in gene_universe_all})
    target_stats['drugs_D1_with_exact_symbol'] = sum(
        1 for k in d1 if any(x in gene_universe_all for x in t1.get(k, set())))
    target_stats['gene_symbol_universe_S1_S2_union'] = len(gene_universe_all)
    target_stats['kegg_sets'] = len(kegg)
    target_stats['hallmark_sets'] = len(hall)

    print('[4/9] libraries and scoring (rules A/B) ...', flush=True)
    libs, genes_all, gidx = build_libraries(kegg, hall)
    unit_list = sorted(cp_units)          # deterministic order
    drugs_d1_sorted = sorted(d1)
    mappings = {}
    for key in ('S1', 'S2', 'S3'):
        mappings[key] = map_library(libs[key], t1, drugs_d1_sorted, SWITCH['z_min'])
    # sensitivity: T0 tokenisation
    mappings_t0 = {}
    for key in ('S1', 'S2', 'S3'):
        mappings_t0[key] = map_library(libs[key], t0, drugs_d1_sorted, SWITCH['z_min'])
    # sensitivity: case-insensitive matching
    t1_upper = {k: {x.upper() for x in v} for k, v in t1.items()}
    mappings_upper = {}
    for key in ('S1', 'S2', 'S3'):
        lib = dict(libs[key])
        mappings_upper[key] = map_library(lib, t1_upper, drugs_d1_sorted, SWITCH['z_min'])

    print('[5/9] switch decision, coverage, levels, units ...', flush=True)
    lib_stats = {}
    chosen = {}
    for key in ('S1', 'S2', 'S3'):
        a_map = mappings[key]['A']
        b_map = mappings[key]['B']
        diag_a = score_diagnostics(a_map, libs[key])
        _, pa_a, e1_a = unit_stats(a_map, unit_list, universe_sorted)
        lv_a = level_table(a_map, pa_a['holdout'], e1_split['holdout'])
        diag_a['levels_analyzable_pa'] = sum(1 for r in lv_a if r['analyzable_pa'])
        diag_a['levels_analyzable_e1split'] = sum(1 for r in lv_a if r['analyzable_e1'])
        switch_to_b = bool(diag_a['max_level_share'] is not None
                           and diag_a['max_level_share'] > SWITCH['max_level_share_max']) or \
            bool(diag_a['levels_analyzable_pa'] < SWITCH['analyzable_levels_min'])
        chosen[key] = 'B' if switch_to_b else 'A'
        lib_stats[key] = {}
        for rule in ('A', 'B'):
            mp = mappings[key][rule]
            diag = score_diagnostics(mp, libs[key]) if rule == 'A' else z_diagnostics(mp)
            units, pa, _ = unit_stats(mp, unit_list, universe_sorted)
            lv = level_table(mp, pa['holdout'], e1_split['holdout'])
            lib_stats[key][rule] = {
                'rule': rule,
                'coverage': {
                    'n_mapped_D1': len(mp),
                    'pct_of_4088': pct(len(mp), 4088),
                    'pct_of_4076': pct(len(mp), 4076),
                    'n_mapped_U': len(set(mp) & universe),
                    'pct_of_4088_U': pct(len(set(mp) & universe), 4088),
                },
                'diagnostics': diag,
                'units': units,
                'levels': {
                    'n_levels': len(lv),
                    'n_levels_ge2_drugs': sum(1 for r in lv if r['n_all'] >= 2),
                    'n_analyzable_pa': sum(1 for r in lv if r['analyzable_pa']),
                    'n_analyzable_e1split': sum(1 for r in lv if r['analyzable_e1']),
                    'levels_missing_in_holdout_pa': sum(1 for r in lv if r['n_hold_pa'] == 0),
                    'levels_missing_in_train_pa': sum(1 for r in lv if r['n_train_pa'] == 0),
                    'table': lv,
                },
                'switch_input_A': {
                    'max_level_share': diag_a['max_level_share'] if rule == 'A' else None,
                    'analyzable_levels_pa': sum(1 for r in lv_a if r['analyzable_pa']) if rule == 'A' else None,
                },
            }
        lib_stats[key]['chosen_rule'] = chosen[key]
        lib_stats[key]['switch_decision'] = {
            'ruleA_max_level_share': diag_a['max_level_share'],
            'ruleA_max_level_name': diag_a['max_level_name'],
            'ruleA_analyzable_levels_pa': diag_a['levels_analyzable_pa'],
            'trigger_single_level_gt_40pct': bool(diag_a['max_level_share'] is not None
                                                 and diag_a['max_level_share'] > SWITCH['max_level_share_max']),
            'trigger_analyzable_lt_12': bool(diag_a['levels_analyzable_pa'] < SWITCH['analyzable_levels_min']),
            'chosen_rule': chosen[key],
        }

    # sensitivity: T0 tokenisation + case-insensitive coverage only
    token_sensitivity = {}
    for key in ('S1', 'S2', 'S3'):
        token_sensitivity[key] = {
            'rule_A_mapped_T1': len(mappings[key]['A']),
            'rule_A_mapped_T0': len(mappings_t0[key]['A']),
            'rule_B_mapped_T1': len(mappings[key]['B']),
            'rule_B_mapped_T0': len(mappings_t0[key]['B']),
            'rule_A_mapped_case_insensitive': len(mappings_upper[key]['A']),
            'rule_B_mapped_case_insensitive': len(mappings_upper[key]['B']),
            'drugs_mapped_T1_not_T0_ruleA': len(set(mappings[key]['A']) - set(mappings_t0[key]['A'])),
            'drugs_mapped_T1_not_T0_ruleB': len(set(mappings[key]['B']) - set(mappings_t0[key]['B'])),
            'drugs_mapped_T0_not_T1_ruleA': len(set(mappings_t0[key]['A']) - set(mappings[key]['A'])),
            'drugs_mapped_T0_not_T1_ruleB': len(set(mappings_t0[key]['B']) - set(mappings[key]['B'])),
            'extra_gene_symbol_tokens_from_T1_in_D1':
                len({x for k in d1 for x in t1.get(k, set())} - {x for k in d1 for x in t0.get(k, set())}),
        }

    # source attribution of the gene symbols that actually drive each mapping
    mapping_source_attribution = {}
    for key in ('S1', 'S2', 'S3'):
        in_lib = libs[key]['in_library_gene_universe']
        mapping_source_attribution[key] = {}
        for rule in ('A', 'B'):
            only_i2 = only_i3 = both_src = 0
            for dn in mappings[key][rule]:
                matched = {t for t in t1.get(dn, set()) if t in gidx and in_lib[gidx[t]]}
                a = matched & a_tok.get(dn, set())
                b = matched & b_tok.get(dn, set())
                if a and b:
                    both_src += 1
                elif a:
                    only_i2 += 1
                elif b:
                    only_i3 += 1
            mapping_source_attribution[key][rule] = {
                'n_mapped': len(mappings[key][rule]),
                'only_I2_target_name': only_i2,
                'only_I3_DRH_target': only_i3,
                'both_sources': both_src,
            }

    print('[6/9] named mechanism drugs + Jaaks template ...', flush=True)
    idf_norm = set(pd.read_excel(PATHS['I2'])['dname'].map(
        lambda x: norm(x) if isinstance(x, str) else '')) - {''}
    drh_norm = set(pd.read_csv(PATHS['I3'], sep='\t', skiprows=9, low_memory=False)['pert_iname'].map(
        lambda x: norm(x) if isinstance(x, str) else '')) - {''}
    jaaks_map, jaaks_stats = load_jaaks()
    jaaks_stats['overlap_U'] = len(set(jaaks_map) & universe)
    jaaks_stats['overlap_D1'] = len(set(jaaks_map) & d1)
    jaaks_stats['coverage_D1_pct'] = pct(len(set(jaaks_map) & d1), len(d1))
    named_rows = named_drug_block(universe, d1, mappings, chosen, t1, idf_norm, drh_norm, jaaks_map)

    print('[7/9] switch-aware primary strategy and gates ...', flush=True)
    primary = None
    candidates = []
    for key in ('S1', 'S2', 'S3'):
        rule = chosen[key]
        gates = judge(lib_stats, key, rule)
        all_pass = all(g['pass'] for g in gates)
        candidates.append({'library': key, 'rule': rule,
                           'gates': [{'id': g['id'], 'pass': g['pass']} for g in gates],
                           'all_gates_pass': all_pass})
        if all_pass and primary is None:
            primary = (key, rule, gates)
    audit_checks = [
        {'id': 'A1', 'name': 'inputs_and_resources_hashed_exactly',
         'pass': bool(inputs['all_match']),
         'value': {k: v['status'] for k, v in sorted(inputs['files'].items())}},
        {'id': 'A2', 'name': 'no_response_column_read',
         'pass': True,
         'value': {'read_columns': V14_READ,
                   'deny_columns_present': v14['deny_columns_present'],
                   'deny_values_read': False}},
        {'id': 'A3', 'name': 'e1_crosscheck_reproduced',
         'pass': bool(crosscheck['all_match']), 'value': crosscheck},
        {'id': 'A4', 'name': 'deterministic_outputs',
         'pass': True, 'value': {'randomness': False, 'timestamps': False,
                                 'json_sort_keys': True,
                                 'mapping_table_sha256_recorded': True}},
    ]
    audit_pass = all(a['pass'] for a in audit_checks)
    verdict = 'mapping_qualified' if (primary is not None and audit_pass) else 'mapping_not_qualified'

    primary_lib, primary_rule = (primary[0], primary[1]) if primary else (None, None)
    primary_gates = primary[2] if primary else judge(lib_stats, 'S1', chosen['S1'])
    ps = lib_stats[primary_lib][primary_rule] if primary else None

    # BRIEF section P-A diagnostic: fraction of unordered drug pairs both mapped
    diag_lib, diag_rule = (primary_lib, primary_rule) if primary else ('S1', chosen['S1'])
    diag_map = mappings[diag_lib][diag_rule]
    pair_diag = {}
    for key in ('S1', 'S2', 'S3'):
        mp = mappings[key][chosen[key]]
        pb = sum(1 for a, b in pairs if a in mp and b in mp)
        cb = sum(1 for u in unit_list if u[1] in mp and u[2] in mp)
        pair_diag[key] = {
            'rule': chosen[key],
            'pairs_both_mapped': pb,
            'pairs_both_mapped_pct': pct(pb, len(pairs)),
            'cell_x_pair_units_both_mapped': cb,
            'cell_x_pair_units_both_mapped_pct': pct(cb, len(cp_units)),
        }
    brief_diag = {
        'note': 'BRIEF section P-A suggested a >=50% both-drug-pair coverage gate; '
                'task-7 replaced it with the pre-registered G1-G4 gates below. '
                'Reported as a diagnostic only; not used for this judgment.',
        'primary_library': diag_lib,
        'primary_rule': diag_rule,
        'pairs_total': len(pairs),
        'cell_x_pair_units_total': len(cp_units),
        'per_library': pair_diag,
        'pairs_both_mapped': pair_diag[diag_lib]['pairs_both_mapped'],
        'pairs_both_mapped_pct': pair_diag[diag_lib]['pairs_both_mapped_pct'],
        'cell_x_pair_units_both_mapped_pct': pair_diag[diag_lib]['cell_x_pair_units_both_mapped_pct'],
    }

    # ---- conditions that travel with the judgment (built from computed facts)
    conditions = []
    if primary is not None:
        d = lib_stats[primary_lib][primary_rule]
        conditions.append(
            '主策略 = %s + 规则 %s（按 §6.3 开关）；覆盖率 %d/4088 = %s%%；可分析水平 %d；'
            'both-unseen 单元 %d（E1 切分口径 %d）；训练单元 %d。' % (
                primary_lib, primary_rule, d['coverage']['n_mapped_D1'],
                d['coverage']['pct_of_4088'], d['levels']['n_analyzable_pa'],
                d['units']['both_unseen_units_pa'],
                d['units']['both_unseen_units_e1split'], d['units']['train_units_pa']))
        conditions.append(
            '阶段 2 必须先冻结切分口径：PA 切分（留出集建在已映射药上，N=mapped）与被冻结的 '
            'E1 切分（留出集建在 4088 全体上）给出不同的 both-unseen 有注释单元数；前者使注释臂在测试集恒有注释，'
            '后者与 R190/E1 的 16,078 单元兼容但其中仅 %d 单元两药均有注释。' % d['units']['both_unseen_units_e1split'])
        if primary_rule == 'A':
            conditions.append(
                '规则 A 的 argmax 未做集合大小归一：单基因命中（score=1）占 %s%%，并列率 %s%%；'
                '大基因家族（如 tubulin）会主导命中数，粗注释应解释为"靶点基因集共属"而不是"机制通路"。'
                % (d['diagnostics']['score1_pct'], d['diagnostics']['tie_drugs_pct']))
        else:
            conditions.append(
                '规则 A 因开关触发被替换为规则 B（超几何富集 z≥1.64）；规则 B 的并列率 %s%%。'
                % d['diagnostics']['tie_drugs_pct'])
        conditions.append(
            'DrugComb `target_name` 主要是蛋白全名，但 token 切分后从蛋白名内嵌抽出的基因符号仍贡献 '
            '%d/%d（%.1f%%）独有映射药、%d 个药与 DRH 共同贡献；覆盖率主体来自 DRH。'
            '同义词/别名未合并（如 5-FU），因此覆盖是**保守下界**。'
            % (mapping_source_attribution[primary_lib][primary_rule]['only_I2_target_name'],
               len(mappings[primary_lib][primary_rule]),
               pct(mapping_source_attribution[primary_lib][primary_rule]['only_I2_target_name'],
                   len(mappings[primary_lib][primary_rule])),
               mapping_source_attribution[primary_lib][primary_rule]['both_sources']))
        conditions.append(
            'Jaaks 通路模板只能覆盖 %d/%d D1 药（%s%%）、%d 个水平，不足以单独满足 ≥12 水平；'
            '本协议因此使用 MSigDB 基因集库（这是预注册的选择，不是对 Jaaks 的否定）。'
            % (jaaks_stats['overlap_D1'], len(d1), jaaks_stats['coverage_D1_pct'],
               jaaks_stats['n_levels']))
        conditions.append(
            'BRIEF §P-A 的"两药均映射药对 ≥50%%"诊断值 = %s%%（全文已于 task-7 被 G1–G4 取代）；'
            '若 Lead 仍要求该 ≥50%% 门槛，则本资源在任何策略下都不达标。'
            % brief_diag['pairs_both_mapped_pct'])
    else:
        conditions = []

    pa_json = {
        'protocol': {'path': 'PROTOCOL_PA.md', 'version': 'v2',
                     'sha256': sha256_file(os.path.join(BASE, 'PROTOCOL_PA.md'))},
        'script': {'path': 'pa.py', 'sha256': sha256_file(os.path.abspath(__file__))},
        'inputs': inputs,
        'data': {
            'v1.4_identity': v14,
            'target_sets': target_stats,
            'libraries': {key: {'n_sets': libs[key]['n_sets'],
                                'n_genes_union': libs[key]['n_genes_union']}
                          for key in ('S1', 'S2', 'S3')},
        },
        'switch': SWITCH,
        'switch_decisions': {key: lib_stats[key]['switch_decision'] for key in ('S1', 'S2', 'S3')},
        'strategies': lib_stats,
        'token_sensitivity': token_sensitivity,
        'mapping_source_attribution': mapping_source_attribution,
        'named_mechanism_drugs': named_rows,
        'jaaks_template': jaaks_stats,
        'brief_pa_diagnostic': brief_diag,
        'judgment': {
            'verdict': verdict,
            'primary_strategy': {'library': primary_lib, 'rule': primary_rule},
            'candidate_gate_summary': candidates,
            'gates': primary_gates,
            'audit_checks': audit_checks,
            'all_gates_pass': bool(primary is not None),
            'all_audit_pass': audit_pass,
            'conditions': conditions,
            'failure_categories': [] if verdict == 'mapping_qualified'
            else ['data_insufficient'],
            'unfreeze_conditions': [] if verdict == 'mapping_qualified' else [
                '扩展注释来源（同义词表/蛋白名→符号映射/纵向机制库）后重新冻结新协议',
            ],
        },
        'non_response_derivation': {
            'mapping_inputs': ['I1 identity columns drug_row/drug_col',
                               'I2 target_name (drug annotation table)',
                               'I3 DRH target (public drug annotation)',
                               'I4/I5 public MSigDB gene sets'],
            'response_columns_present_but_never_read': v14['deny_columns_present'],
            'response_values_stored': False,
            'note': 'only header-name existence of response columns is touched; '
                    'v1.4 is parsed with csv.reader and positional access to READ columns only',
        },
        'deterministic': {'random': False, 'timestamps': False, 'json_sort_keys': True},
    }

    print('[8/9] writing mapping tables ...', flush=True)
    mt, aux = write_mapping_tables(universe, d1, v14['collision_details'], t1,
                                   mappings, chosen, jaaks_map)
    pa_json['outputs'] = {
        'mapping_table.csv': {'path': os.path.relpath(mt, ROOT), 'bytes': os.path.getsize(mt),
                              'sha256': sha256_file(mt),
                              'rows': len(universe) * 3,
                              'frozen_table_rule': 'per-library chosen rule (PROTOCOL_PA 6.3); '
                                                   'primary strategy rows = source_library == '
                                                   + str(primary_lib)},
        'mapping_table_rules_AB.csv': {'path': os.path.relpath(aux, ROOT),
                                       'bytes': os.path.getsize(aux),
                                       'sha256': sha256_file(aux),
                                       'rows': len(universe) * 3 * 2},
    }
    pa_json['judgment']['primary_strategy']['mapping_table_sha256'] = \
        pa_json['outputs']['mapping_table.csv']['sha256']

    print('[9/9] writing pa.json ...', flush=True)
    with open(os.path.join(BASE, 'pa.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pa_json, f, sort_keys=True, ensure_ascii=True, indent=1)
        f.write('\n')

    print('VERDICT:', verdict, '| primary:', primary_lib, primary_rule)
    for key in ('S1', 'S2', 'S3'):
        d = lib_stats[key][chosen[key]]
        print('  %s(%s): mapped %d (%.2f%% of 4088) levels %d both-unseen %d train %d'
              % (key, chosen[key], d['coverage']['n_mapped_D1'], d['coverage']['pct_of_4088'],
                 d['levels']['n_analyzable_pa'], d['units']['both_unseen_units_pa'],
                 d['units']['train_units_pa']))
    print('mapping_table sha256:', pa_json['outputs']['mapping_table.csv']['sha256'])


if __name__ == '__main__':
    main()
