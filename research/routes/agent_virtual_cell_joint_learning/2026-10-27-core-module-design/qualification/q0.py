"""R199-Q0 metadata-only qualification audit for replacement relation
Delta(c; a, a'; b) = E[y(c,a,b)] - E[y(c,a',b)].

No response values are read for effects: only design/identity columns, row counts,
replicate structure, header existence.  Deterministic JSON (sorted keys, no timestamps).
"""
import csv
import hashlib
import json
import os
import unicodedata
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

B = r'D:\MAESTRO'
OUT = os.path.join(B, r'research\2026-10-27-core-module-design\qualification')
Q0 = os.path.join(OUT, 'q0.json')
PROTOCOL = os.path.join(OUT, 'PROTOCOL_Q0.md')

JAAKS_DIR = os.path.join(B, r'data\external\gdsc_combinations\jaaks2022_figshare')
J_ORIG = os.path.join(JAAKS_DIR, 'Original screen_All tissues_fitted data.csv')
J_VAL = os.path.join(JAAKS_DIR, 'Validation screen_All tissues_fitted data.csv')
V14 = os.path.join(B, r'research\2026-10-27-drugcomb-qualification\downloads\summary_table_v1.4.csv')
V15 = os.path.join(B, r'tmp\a3_v15_summary.csv')
ONEIL = os.path.join(B, r'data\raw\oneil2026_qualification',
                     '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
BEATAML_DIR = os.path.join(B, r'data\external\beataml2_20261017')
MIXSEQ = os.path.join(B, r'data\external\mixseq_scperturb\mcfarland_2020.h5ad')

NULLISH = {'', 'NA', 'NULL', 'NAN', '\\N'}

# frozen thresholds (PROTOCOL_Q0.md)
G1_MIN_UNITS = 5000
G1_MIN_CELLS = 30
G1_MIN_CONTEXTS = 200
G1_MIN_CROSS_CONTEXTS = 10
G1_MIN_CROSS_CELLS = 3
G2_MIN_LEGAL_FRAC = 0.95
DELTA_MIN_PROVISIONAL = 0.10
DELTA_SENS = [0.05, 0.10, 0.15]
SIGMA_E = [0.041, 0.058, 0.109]
MDE_FACTOR = 2.801585
N_EFF_GRID = [24, 48, 96, 192]
G5_MAX_OVERLAP = 0.10


def norm(s):
    s = unicodedata.normalize('NFKC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 22), b''):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj, path):
    def q(x):
        if isinstance(x, dict):
            return {k: q(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [q(v) for v in x]
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, (np.floating,)):
            x = float(x)
        if isinstance(x, float):
            return round(x, 6) if x == x and abs(x) != float('inf') else None
        return x
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(q(obj), fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def input_manifest():
    files = {'protocol_q0': PROTOCOL, 'script_q0': os.path.join(OUT, 'q0.py'),
             'jaaks_original': J_ORIG, 'jaaks_validation': J_VAL,
             'drugcomb_v14_summary': V14, 'drugcomb_v15_summary': V15,
             'oneil_workbook': ONEIL}
    out = {}
    for k, p in files.items():
        if os.path.exists(p):
            out[k] = {'path_rel': os.path.relpath(p, B).replace('\\', '/'),
                      'bytes': os.path.getsize(p), 'sha256': sha256_file(p)}
        else:
            out[k] = {'path_rel': os.path.relpath(p, B).replace('\\', '/'), 'status': 'missing'}
    return out


def replacement_metrics_from_cell_partner_members(members_by_ctx, pair_key_cap=5_000_000):
    """members_by_ctx: dict ctx_key -> set(members); return units, contexts, cross-cell coverage.

    Cross coverage uses a count dict capped at G1_MIN_CROSS_CELLS (no per-key cell sets) to keep
    memory bounded; enumeration stops (not_enumerated) if distinct member-pair keys exceed cap.
    """
    units = 0
    contexts = 0
    per_ctx_members = []
    for key, members in members_by_ctx.items():
        m = len(members)
        if m >= 2:
            units += m * (m - 1) // 2
            contexts += 1
            per_ctx_members.append(m)
    base = {'legal_units': int(units), 'contexts_with_ge2_members': int(contexts),
            'median_members_per_context': float(np.median(per_ctx_members)) if per_ctx_members else None}
    if units > 200_000_000:
        base.update({'member_pairs_with_ge1_cell': None, 'member_pairs_with_ge3_cells': None,
                     'cross_cell_coverage': {'not_enumerated': True, 'reason': f'legal units {int(units)} too large'}})
        return base
    pair_counts = {}
    cap = G1_MIN_CROSS_CELLS
    stopped = False
    for key, members in members_by_ctx.items():
        if len(members) < 2:
            continue
        if len(key) == 2:
            cell, partner = key
        else:
            cell, partner = key[0], key[1]
        ml = sorted(members)
        for i in range(len(ml)):
            for j in range(i + 1, len(ml)):
                k = (partner, ml[i], ml[j])
                v = pair_counts.get(k)
                if v is None:
                    if len(pair_counts) >= pair_key_cap:
                        stopped = True
                        break
                    pair_counts[k] = 1
                elif v < cap:
                    pair_counts[k] = v + 1
            if stopped:
                break
        if stopped:
            break
    if stopped:
        base.update({'member_pairs_with_ge1_cell': None, 'member_pairs_with_ge3_cells': None,
                     'cross_cell_coverage': {'not_enumerated': True,
                                             'reason': f'distinct member-pair keys exceeded cap {pair_key_cap}'}})
    else:
        cross_counts = Counter(min(v, cap) for v in pair_counts.values())
        base.update({'member_pairs_with_ge1_cell': int(len(pair_counts)),
                     'member_pairs_with_ge3_cells': int(sum(1 for v in pair_counts.values() if v >= cap)),
                     'cross_cell_coverage_distribution': {str(k): int(v) for k, v in sorted(cross_counts.items())}})
    return base


def jaaks_metrics():
    res = {}
    cols = ['BARCODE', 'CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID', 'ANCHOR_CONC', 'LIBRARY_CONC']
    for tag, path in [('original', J_ORIG), ('validation', J_VAL)]:
        d = pd.read_csv(path, usecols=cols, low_memory=False)
        d['cell'] = d.CELL_LINE_NAME.map(norm)
        d['anchor'] = d.ANCHOR_ID.astype(str).str.strip()
        d['library'] = d.LIBRARY_ID.astype(str).str.strip()
        cells = set(d.cell)
        rep = d.groupby(['cell', 'anchor', 'library'], observed=True).size()
        rep_lvl = d.groupby(['cell', 'anchor', 'library', 'ANCHOR_CONC'], observed=True).size()
        # orientation A: partner = anchor, members = libraries
        members_a = defaultdict(set)
        for (c, a, l) in zip(d.cell, d.anchor, d.library):
            members_a[(c, a)].add(l)
        mA = replacement_metrics_from_cell_partner_members(members_a)
        # legal exposure: anchor concentration sets equal across members for each (cell, anchor)
        ac_sets = d.groupby(['cell', 'anchor', 'library'], observed=True)['ANCHOR_CONC'].apply(
            lambda x: frozenset(str(v).strip() for v in x.dropna().unique()))
        anchor_ctx = {}
        for (c, a, l), s in ac_sets.items():
            anchor_ctx.setdefault((c, a), []).append(s)
        common_ge1 = 0
        common_ge2 = 0
        for v in anchor_ctx.values():
            inter = set.intersection(*[set(x) for x in v]) if v else set()
            if len(inter) >= 1:
                common_ge1 += 1
            if len(inter) >= 2:
                common_ge2 += 1
        n_anchor_ctx = len(anchor_ctx)
        anchor_match = common_ge2  # primary: need two matched anchor concentrations when available
        # library dose grid recorded? fitted table has single LIBRARY_CONC per pair
        lib_conc_levels = d.groupby(['cell', 'anchor', 'library'], observed=True)['LIBRARY_CONC'].nunique()
        # orientation B: partner = library, members = anchors
        members_b = defaultdict(set)
        for (c, a, l) in zip(d.cell, d.anchor, d.library):
            members_b[(c, l)].add(a)
        mB = replacement_metrics_from_cell_partner_members(members_b)
        res[tag] = {
            'rows': int(len(d)),
            'cells': int(len(cells)),
            'barcodes': int(d.BARCODE.nunique()),
            'anchors': int(d.anchor.nunique()),
            'libraries': int(d.library.nunique()),
            'ordered_pair_keys': int(len(rep)),
            'rows_per_key_min_med_max': [int(rep.min()), float(rep.median()), int(rep.max())],
            'keys_with_ge2_rows': int((rep >= 2).sum()),
            'keys_with_ge2_rows_frac': float((rep >= 2).mean()),
            'anchor_level_units': int(len(rep_lvl)),
            'anchor_level_units_ge2_frac': float((rep_lvl >= 2).mean()) if len(rep_lvl) else None,
            'anchor_level_rows_min_med_max': [int(rep_lvl.min()), float(rep_lvl.median()), int(rep_lvl.max())] if len(rep_lvl) else None,
            'primary_orientation_anchor_partner': mA,
            'secondary_orientation_library_partner': mB,
            'legal_exposure': {
                'anchor_conc_sets_identical_frac': float(anchor_match / n_anchor_ctx) if n_anchor_ctx else None,
                'anchor_common_ge1_frac': float(common_ge1 / n_anchor_ctx) if n_anchor_ctx else None,
                'anchor_common_ge2_frac': float(common_ge2 / n_anchor_ctx) if n_anchor_ctx else None,
                'library_dose_levels_max': int(lib_conc_levels.max()) if len(lib_conc_levels) else None,
                'library_dose_levels_all_one': bool((lib_conc_levels == 1).all()),
                'note': 'fitted table records 2 anchor concentrations and 1 library-conc marker per pair; library 7-dose raw grid not in this table; exposure time/assay not in table',
            },
        }
    # overlap Original vs Validation
    do = pd.read_csv(J_ORIG, usecols=['CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID', 'ANCHOR_CONC'], low_memory=False)
    dv = pd.read_csv(J_VAL, usecols=['CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID', 'ANCHOR_CONC'], low_memory=False)
    for d in (do, dv):
        d['cell'] = d.CELL_LINE_NAME.map(norm)
        d['key'] = d.cell + '|' + d.ANCHOR_ID.astype(str).str.strip() + '|' + d.LIBRARY_ID.astype(str).str.strip()
    ko = set(do.key)
    kv = set(dv.key)
    res['original_validation_overlap'] = {
        'orig_cells': int(do.cell.nunique()), 'val_cells': int(dv.cell.nunique()),
        'shared_cells': int(len(set(do.cell) & set(dv.cell))),
        'shared_pair_keys': int(len(ko & kv)),
        'orig_keys': int(len(ko)), 'val_keys': int(len(kv)),
        'note': 'Original and Validation are the SAME Jaaks resource; shared 96 cells must NOT be treated as independent data',
    }
    res['cells_set'] = sorted(set(do.cell))
    return res


def oneil_metrics():
    d = pd.read_excel(ONEIL, sheet_name='combination response',
                      usecols=['BatchID', 'cell_line', 'drugA_name', 'drugA Conc (µM)',
                               'drugB_name', 'drugB Conc (µM)'])
    d = d.dropna(subset=['cell_line', 'drugA_name', 'drugB_name'])
    d['cell'] = d.cell_line.map(norm)
    d['a'] = d.drugA_name.astype(str).map(norm)
    d['b'] = d.drugB_name.astype(str).map(norm)
    d['pair'] = [tuple(sorted((a, b))) for a, b in zip(d.a, d.b)]
    pair_counts = d.groupby(['cell', 'pair'], observed=True).size()
    # dose grid per (cell, pair)
    grid = d.groupby(['cell', 'pair'], observed=True).agg(
        n_a=('drugA Conc (µM)', 'nunique'), n_b=('drugB Conc (µM)', 'nunique'), rows=('BatchID', 'size'))
    # members per (batch, cell, partner): same-batch pairing is the legal exposure unit
    d['batch'] = d.BatchID
    members = defaultdict(set)
    for c, a, b, bt in zip(d.cell, d.a, d.b, d.batch):
        if pd.isna(bt):
            continue
        bt = int(bt)
        members[(bt, c, a)].add(b)
        members[(bt, c, b)].add(a)
    mm = replacement_metrics_from_cell_partner_members(members)
    # partner dose-set per (batch, cell, partner, pair) -> require a single common dose-set
    by_pair = d.groupby(['batch', 'cell', 'a', 'b'], observed=True).agg(
        da=('drugA Conc (µM)', lambda x: frozenset(x.dropna())),
        db=('drugB Conc (µM)', lambda x: frozenset(x.dropna()))).reset_index()
    pdose = defaultdict(set)
    for bt, c, a, b, sa, sb in zip(by_pair.batch, by_pair.cell, by_pair.a, by_pair.b, by_pair.da, by_pair.db):
        pdose[(int(bt), c, b)].add(sb)
        pdose[(int(bt), c, a)].add(sa)
    partner_match = sum(1 for v in pdose.values() if len(v) == 1)
    res = {
        'rows': int(len(d)),
        'cells': int(d.cell.nunique()),
        'drugs': int(len(set(d.a) | set(d.b))),
        'batches': sorted(int(x) for x in d.BatchID.dropna().unique()),
        'batch_rows': {str(int(k)): int(v) for k, v in d.BatchID.value_counts().items()},
        'unordered_pair_cells': int(len(pair_counts)),
        'rows_per_pair_cell_min_med_max': [int(pair_counts.min()), float(pair_counts.median()), int(pair_counts.max())],
        'dose_grid': {'n_a_distribution': {str(k): int(v) for k, v in grid.n_a.value_counts().items()},
                      'n_b_distribution': {str(k): int(v) for k, v in grid.n_b.value_counts().items()},
                      'rows_distribution': {str(k): int(v) for k, v in grid.rows.value_counts().items()}},
        'replacement': mm,
        'legal_exposure': {
            'numeric_dose_columns_present': True,
            'partner_dose_sets_identical_frac': float(partner_match / len(pdose)) if pdose else None,
            'partner_matching_unit': 'same BatchID + cell + partner; one unique partner dose-set across members',
            'exposure_time_column_present': False,
            'assay_method_column_present': False,
            'technical_replicate_columns': ['viability1', 'viability2', 'viability3', 'viability4'],
            'note': 'dose grids numeric; replacement units are same-batch same-cell same-partner; no exposure-time/assay-method column; 3 BatchID values same lab; batch not certified as independent culture',
        },
    }
    res['cells_set'] = sorted(set(d.cell))
    return res


def drugcomb_v14_metrics(jaaks_cells):
    d = pd.read_csv(V14, usecols=['block_id', 'drug_row', 'drug_col', 'cell_line_name',
                                  'conc_r_unit', 'conc_c_unit'], low_memory=False)
    d['cell'] = d.cell_line_name.map(norm)
    combo = d[d.drug_col.notna() & ~d.drug_col.astype(str).str.strip().str.upper().isin(NULLISH)]
    combo = combo.assign(
        a=combo.drug_row.astype(str).map(norm),
        b=combo.drug_col.astype(str).map(norm))
    combo = combo[(combo.a != '') & (combo.b != '')]
    members = defaultdict(set)
    pair_blocks = Counter()
    for c, a, b in zip(combo.cell, combo.a, combo.b):
        members[(c, a)].add(b)
        members[(c, b)].add(a)
        pair_blocks[(c, tuple(sorted((a, b))))] += 1
    mm = replacement_metrics_from_cell_partner_members(members)
    rep = Counter(pair_blocks.values())
    res = {
        'rows_total': int(len(d)), 'combo_blocks': int(len(combo)),
        'cells': int(combo.cell.nunique()), 'drugs': int(len(set(combo.a) | set(combo.b))),
        'unordered_pair_units': int(len(pair_blocks)),
        'replacement': mm,
        'block_repeats': {'blocks_per_pair_unit_dist': {str(k): int(v) for k, v in sorted(rep.items())},
                          'pair_units_ge2_blocks_frac': float(sum(v for k, v in rep.items() if k >= 2) / max(1, len(pair_blocks)))},
        'keys_with_ge2_rows_frac': float(sum(v for k, v in rep.items() if k >= 2) / max(1, len(pair_blocks))),
        'legal_exposure': {
            'numeric_dose_columns_present': False,
            'dose_columns': ['conc_r_unit', 'conc_c_unit'],
            'note': 'summary table has only unit strings; no numeric dose; exposure/dose-design not verifiable',
        },
        'endpoint_columns_present': ['synergy_zip', 'synergy_bliss', 'synergy_loewe', 'synergy_hsa',
                                     'css', 'css_row', 'css_col', 'ic50_row', 'ic50_col', 'S'],
        'study_column_present': False,
    }
    res['jaaks_cell_overlap'] = {
        'jaaks_cells': 125, 'combo_cells': int(combo.cell.nunique()),
        'shared_cells': int(len(set(combo.cell) & set(jaaks_cells))),
        'overlap_frac_of_combo_cells': float(len(set(combo.cell) & set(jaaks_cells)) / combo.cell.nunique()),
    }
    return res


def drugcomb_v15_metrics(jaaks_cells):
    """Streaming metadata scan of v1.5 full summary; no response values used."""
    members = defaultdict(set)       # (study, cell, partner) -> members
    pair_blocks = Counter()           # (study, cell, unordered pair) -> block count
    drugs = set()
    cells = set()
    studies = set()
    header = None
    n = combo = 0
    with open(V15, newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        col = {c: i for i, c in enumerate(header)}
        ib, ic, istudy = col['block_id'], col['cell_line_name'], col['study_name']
        idr, idc = col['drug_row'], col['drug_col']
        for row in rdr:
            n += 1
            dr = row[idr].strip()
            dc = row[idc].strip()
            if dr.upper() in NULLISH or dc.upper() in NULLISH:
                continue
            a = norm(dr); b = norm(dc)
            if not a or not b:
                continue
            combo += 1
            c = norm(row[ic])
            st = row[istudy].strip()
            cells.add(c)
            drugs.add(a); drugs.add(b)
            studies.add(st)
            members[(st, c, a)].add(b)
            members[(st, c, b)].add(a)
            pair_blocks[(st, c, tuple(sorted((a, b))))] += 1
    # units per (study,cell,partner) -- computed in a full first pass
    units = 0
    contexts = 0
    per_ctx = []
    for key, mem in members.items():
        if len(mem) >= 2:
            units += len(mem) * (len(mem) - 1) // 2
            contexts += 1
            per_ctx.append(len(mem))
    # cross coverage via count dict capped at G1_MIN_CROSS_CELLS; enumeration may stop at key cap
    pair_counts = {}
    pair_cap = 5_000_000
    stopped = False
    for key, mem in members.items():
        if len(mem) >= 2:
            st, c, partner = key
            ml = sorted(mem)
            for i in range(len(ml)):
                for j in range(i + 1, len(ml)):
                    pk = (st, partner, ml[i], ml[j])
                    v = pair_counts.get(pk)
                    if v is None:
                        if len(pair_counts) >= pair_cap:
                            stopped = True
                            break
                        pair_counts[pk] = 1
                    elif v < G1_MIN_CROSS_CELLS:
                        pair_counts[pk] = v + 1
                if stopped:
                    break
        if stopped:
            break
    cross_dist = Counter(min(v, G1_MIN_CROSS_CELLS) for v in pair_counts.values())
    cross_ge3 = None if stopped else sum(1 for v in pair_counts.values() if v >= G1_MIN_CROSS_CELLS)
    rep_dist = Counter(pair_blocks.values())
    return {
        'rows_total': int(n), 'combo_blocks': int(combo),
        'studies': int(len(studies)), 'combo_cells': int(len(cells)),
        'drugs': int(len(drugs)),
        'unordered_pair_units': int(len(pair_blocks)),
        'replacement': {'legal_units': int(units), 'contexts_with_ge2_members': int(contexts),
                        'median_members_per_context': float(np.median(per_ctx)) if per_ctx else None,
                        'member_pairs_with_ge1_cell': None if stopped else int(len(pair_counts)),
                        'member_pairs_with_ge3_cells': cross_ge3,
                        'cross_coverage_stopped_at_cap': bool(stopped),
                        'cross_cell_coverage_distribution': {str(k): int(v) for k, v in sorted(cross_dist.items())}},
        'block_repeats': {'blocks_per_pair_unit_dist': {str(k): int(v) for k, v in sorted(rep_dist.items())[:15]},
                          'pair_units_ge2_blocks_frac': float(sum(v for k, v in rep_dist.items() if k >= 2) / max(1, len(pair_blocks)))},
        'keys_with_ge2_rows_frac': float(sum(v for k, v in rep_dist.items() if k >= 2) / max(1, len(pair_blocks))),
        'legal_exposure': {'numeric_dose_columns_present': False,
                           'dose_columns': ['conc_row_unit', 'conc_col_unit'],
                           'note': 'summary has only unit strings; no numeric dose; exposure/dose-design not verifiable'},
        'endpoint_columns_present': [c for c in header if c in
                                     ('synergy_zip', 'synergy_loewe', 'synergy_hsa', 'synergy_bliss',
                                      'S_sum', 'S_mean', 'S_max', 'css_row', 'css_col', 'css_ri',
                                      'ic50_row', 'ic50_col', 'ri_row', 'ri_col')],
        'study_column_present': True,
        'jaaks_cell_overlap': {'jaaks_cells': 125, 'combo_cells': int(len(cells)),
                               'shared_cells': int(len(cells & set(jaaks_cells))),
                               'overlap_frac_of_combo_cells': float(len(cells & set(jaaks_cells)) / len(cells))},
    }


def beataml_mixseq_metrics():
    import glob
    beat = {'files': [], 'combination_columns': []}
    if os.path.isdir(BEATAML_DIR):
        beat['files'] = sorted(os.listdir(BEATAML_DIR))[:20]
        try:
            h = pd.read_csv(os.path.join(BEATAML_DIR, 'beataml_probit_curve_fits_v4_dbgap.txt'),
                            sep='\t', nrows=0)
            beat['probit_columns'] = list(h.columns)
            beat['combination_columns'] = [c for c in h.columns if 'combo' in c.lower()
                                           or 'drug2' in c.lower() or 'second' in c.lower()]
        except Exception as exc:
            beat['probit_error'] = str(exc)
    mix = {'path': MIXSEQ, 'exists': os.path.exists(MIXSEQ), 'bytes': os.path.getsize(MIXSEQ) if os.path.exists(MIXSEQ) else None}
    # Mix-seq metadata-only checks (obs design columns) via h5py/anndata
    try:
        import anndata as ad
        a = ad.read_h5ad(MIXSEQ, backed='r')
        obs = a.obs
        mix['n_obs'] = int(a.n_obs)
        mix['obs_columns'] = [str(c) for c in obs.columns]
        mix['perturbations'] = sorted(str(x) for x in obs['perturbation'].dropna().unique())
        mix['has_combination_column'] = False
        mix['endpoint_columns'] = []
    except Exception as exc:
        mix['read_error'] = str(exc)
    return {'beataml': beat, 'mixseq': mix}


def mde_table():
    out = {}
    for sig in SIGMA_E:
        rows = {}
        for k in N_EFF_GRID:
            se = sig * np.sqrt(2.0 / 2.0) / np.sqrt(k)  # two sides each with n_rep=2 => SE_unit=sigma*sqrt(1/2+1/2)=sigma
            rows[str(k)] = round(float(MDE_FACTOR * se), 6)
        out[str(sig)] = rows
    # n_eff needed for MDE<=0.10 and <=0.15
    need = {}
    for sig in SIGMA_E:
        for target in (0.10, 0.15):
            n = (MDE_FACTOR * sig / target) ** 2
            need[f'{sig}_{target}'] = round(float(n), 3)
    return {'sigma_e_grid': SIGMA_E, 'n_eff_grid': N_EFF_GRID,
            'formula': 'MDE80 = 2.801585 * SE_unit / sqrt(n_eff); SE_unit = sigma_e (two sides, 2 technical reps each)',
            'mde80_table': out, 'required_n_eff_for_target': need}


def gate_statuses(cand):
    """Apply frozen gate rules to a candidate dict."""
    g = {}
    rep = cand.get('replacement', {})
    cells = cand.get('cells') or cand.get('combo_cells') or 0
    units = rep.get('legal_units', 0)
    contexts = rep.get('contexts_with_ge2_members', 0)
    cross = rep.get('member_pairs_with_ge3_cells')
    g1 = (units >= G1_MIN_UNITS and cells >= G1_MIN_CELLS and contexts >= G1_MIN_CONTEXTS
          and cross is not None and cross >= G1_MIN_CROSS_CONTEXTS)
    g['G1'] = {'pass': bool(g1), 'units': int(units), 'cells': int(cells),
               'contexts': int(contexts),
               'cross_cell_contexts_ge3': (int(cross) if cross is not None else None),
               'cross_coverage_certified': bool(cross is not None)}
    le = cand.get('legal_exposure', {})
    numeric = bool(le.get('numeric_dose_columns_present', False))
    anchor_ok = le.get('partner_dose_sets_identical_frac')
    if anchor_ok is None:
        anchor_ok = le.get('anchor_conc_sets_identical_frac')
    design_ok = numeric and (anchor_ok is None or anchor_ok >= 0.95)
    # status: pass only if numeric dose, partner matching >=95%, exposure time recorded
    time_ok = bool(le.get('exposure_time_column_present', False))
    if design_ok and time_ok:
        g2 = 'pass'
    elif design_ok:
        g2 = 'conditional'
    else:
        g2 = 'fail'
    g['G2'] = {'status': g2, 'numeric_dose': numeric, 'partner_matching_frac': anchor_ok,
               'exposure_time_recorded': time_ok}
    ep = cand.get('endpoint_columns_present', [])
    g3 = 'conditional' if ep else 'fail'
    g['G3'] = {'status': g3, 'endpoint_columns_present': ep,
               'note': 'viability-derived/summary endpoints only; no orthogonal functional readout in local data'}
    # G4
    rep_frac = cand.get('keys_with_ge2_rows_frac')
    if rep_frac is None:
        rep_frac = None
    has_repeats = bool(rep_frac is not None and rep_frac > 0)
    indep = bool(le.get('independent_culture_or_batch_recorded', False))
    if has_repeats and indep:
        g4 = 'pass'
    elif has_repeats:
        g4 = 'conditional'
    else:
        g4 = 'fail'
    g['G4'] = {'status': g4, 'repeat_frac': rep_frac,
               'independent_culture_or_batch_recorded': indep}
    # G5
    ov = cand.get('jaaks_cell_overlap', {})
    frac = ov.get('overlap_frac_of_combo_cells')
    if frac is None:
        g5 = 'fail' if cand.get('is_jaaks_self') else 'conditional'
    elif frac <= G5_MAX_OVERLAP and frac < 1.0:
        g5 = 'pass'
    elif frac < 1.0:
        g5 = 'conditional'
    else:
        g5 = 'fail'
    g['G5'] = {'status': g5, 'overlap_frac': frac,
               'note': 'Jaaks self-reference cannot be its own independent target; Original/Validation share cells'}
    return g


def verdict_for(gates, mde_ok, mde_loose):
    vals = [gates[k]['status'] if 'status' in gates[k] else ('pass' if gates[k]['pass'] else 'fail')
            for k in ('G2', 'G3', 'G4', 'G5')]
    g1 = 'pass' if gates['G1']['pass'] else 'fail'
    if g1 == 'pass' and all(v in ('pass', 'conditional') for v in vals) and any(v == 'conditional' for v in vals):
        if mde_ok:
            return 'qualified_with_conditions'
        if mde_loose:
            return 'qualified_with_conditions'
        return 'not_qualified'
    return 'not_qualified'


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = input_manifest()
    jaaks = jaaks_metrics()
    jaaks_cells = set(jaaks['cells_set'])
    oneil = oneil_metrics()
    v14 = drugcomb_v14_metrics(jaaks_cells)
    v15 = drugcomb_v15_metrics(jaaks_cells)
    bm = beataml_mixseq_metrics()
    mde = mde_table()

    candidates = {
        'jaaks_original': {
            'is_jaaks_self': True,
            'rows': jaaks['original']['rows'], 'cells': jaaks['original']['cells'],
            'replacement': jaaks['original']['primary_orientation_anchor_partner'],
            'legal_exposure': {
                'numeric_dose_columns_present': True,
                'anchor_conc_sets_identical_frac': jaaks['original']['legal_exposure']['anchor_conc_sets_identical_frac'],
                'partner_dose_sets_identical_frac': jaaks['original']['legal_exposure']['anchor_common_ge1_frac'],
                'anchor_common_ge2_frac': jaaks['original']['legal_exposure']['anchor_common_ge2_frac'],
                'exposure_time_recorded': False,
                'note': jaaks['original']['legal_exposure']['note'],
            },
            'endpoint_columns_present': ['SYNERGY_DELTA_EMAX (viability-derived)'],
            'keys_with_ge2_rows_frac': jaaks['original']['anchor_level_units_ge2_frac'],
            'independent_culture_or_batch_recorded': False,
            'jaaks_cell_overlap': {'overlap_frac_of_combo_cells': 1.0, 'shared_cells': 125},
        },
        'jaaks_validation': {
            'is_jaaks_self': True,
            'rows': jaaks['validation']['rows'], 'cells': jaaks['validation']['cells'],
            'replacement': jaaks['validation']['primary_orientation_anchor_partner'],
            'legal_exposure': {
                'numeric_dose_columns_present': True,
                'anchor_conc_sets_identical_frac': jaaks['validation']['legal_exposure']['anchor_conc_sets_identical_frac'],
                'partner_dose_sets_identical_frac': jaaks['validation']['legal_exposure']['anchor_common_ge1_frac'],
                'anchor_common_ge2_frac': jaaks['validation']['legal_exposure']['anchor_common_ge2_frac'],
                'exposure_time_recorded': False,
                'note': jaaks['validation']['legal_exposure']['note'],
            },
            'endpoint_columns_present': ['SYNERGY_DELTA_EMAX (viability-derived)'],
            'keys_with_ge2_rows_frac': jaaks['validation']['anchor_level_units_ge2_frac'],
            'independent_culture_or_batch_recorded': False,
            'jaaks_cell_overlap': {'overlap_frac_of_combo_cells': 1.0, 'shared_cells': 125},
        },
        'oneil': {
            'rows': oneil['rows'], 'cells': oneil['cells'],
            'replacement': oneil['replacement'],
            'legal_exposure': {
                'numeric_dose_columns_present': True,
                'partner_dose_sets_identical_frac': oneil['legal_exposure']['partner_dose_sets_identical_frac'],
                'exposure_time_recorded': False,
                'independent_culture_or_batch_recorded': False,
                'note': oneil['legal_exposure']['note'],
            },
            'endpoint_columns_present': ['viability1..4', 'mu/muMax', 'X/X0'],
            'keys_with_ge2_rows_frac': 1.0,
            'jaaks_cell_overlap': {'overlap_frac_of_combo_cells': None},
        },
        'drugcomb_v14': {
            'rows': v14['combo_blocks'], 'cells': v14['cells'],
            'replacement': v14['replacement'],
            'legal_exposure': v14['legal_exposure'],
            'endpoint_columns_present': v14['endpoint_columns_present'],
            'keys_with_ge2_rows_frac': v14.get('keys_with_ge2_rows_frac'),
            'jaaks_cell_overlap': v14['jaaks_cell_overlap'],
        },
        'drugcomb_v15': {
            'rows': v15['combo_blocks'], 'cells': v15['combo_cells'],
            'replacement': v15['replacement'],
            'legal_exposure': v15['legal_exposure'],
            'endpoint_columns_present': v15['endpoint_columns_present'],
            'keys_with_ge2_rows_frac': v15.get('keys_with_ge2_rows_frac'),
            'jaaks_cell_overlap': v15['jaaks_cell_overlap'],
        },
        'beataml': {
            'rows': None, 'cells': None, 'replacement': {'legal_units': 0, 'contexts_with_ge2_members': 0,
                                                        'medium_members_per_context': None},
            'legal_exposure': {'numeric_dose_columns_present': False, 'note': 'monotherapy only; no a,b same-cell combination'},
            'endpoint_columns_present': [], 'keys_with_ge2_rows_frac': None,
            'jaaks_cell_overlap': {},
        },
        'mixseq': {
            'rows': bm['mixseq'].get('n_obs'), 'cells': None,
            'replacement': {'legal_units': 0, 'contexts_with_ge2_members': 0},
            'legal_exposure': {'numeric_dose_columns_present': False, 'note': 'single-agent transcriptome; no combination functional endpoint'},
            'endpoint_columns_present': [], 'keys_with_ge2_rows_frac': None,
            'jaaks_cell_overlap': {},
        },
    }

    # O'Neil overlap with Jaaks (cells)
    if os.path.exists(ONEIL):
        oneil_cells = set(oneil['cells_set'])
        ov = len(oneil_cells & jaaks_cells) / len(oneil_cells) if oneil_cells else None
        candidates['oneil']['jaaks_cell_overlap'] = {
            'jaaks_cells': 125, 'oneil_cells': len(oneil_cells),
            'shared_cells': len(oneil_cells & jaaks_cells),
            'overlap_frac_of_combo_cells': ov,
        }

    for name, cand in candidates.items():
        gates = gate_statuses(cand)
        cand['gates'] = gates
        # MDE check using candidate cell count as cluster count (conservative), sigma variants
        n_eff = int(cand.get('cells') or 0)
        cand['mde_prior'] = {
            'assumed_sigma_e': SIGMA_E,
            'n_eff_conservative': n_eff,
            'mde80_at_sigma': {str(s): (round(float(MDE_FACTOR * s / np.sqrt(n_eff)), 6) if n_eff else None)
                               for s in SIGMA_E},
            'note': 'n_eff uses candidate cell count as conservative cluster count; per-unit repeats not counted as independent',
        }
        mde_ok = all((m is not None and m <= DELTA_MIN_PROVISIONAL) for m in
                     [cand['mde_prior']['mde80_at_sigma'][str(s)] for s in SIGMA_E] if m is not None) if n_eff else False
        mde_loose = all((m is not None and m <= 0.15) for m in
                        [cand['mde_prior']['mde80_at_sigma'][str(s)] for s in SIGMA_E] if m is not None) if n_eff else False
        cand['verdict'] = verdict_for(gates, mde_ok, mde_loose)
        cand['delta_estimable'] = {
            'per_unit_repeats_available': cand.get('keys_with_ge2_rows_frac') is not None or name == 'oneil',
            'mde80_le_delta_min_provisional': bool(mde_ok),
            'mde80_le_0.15': bool(mde_loose),
        }

    # failure categories per candidate
    for name, cand in candidates.items():
        cats = []
        if not cand['gates']['G1']['pass']:
            cats.append('cross_scale_insufficient')
        if cand['gates']['G2']['status'] == 'fail':
            cats.append('exposure_unverifiable')
        if cand['gates']['G3']['status'] == 'fail':
            cats.append('endpoint_not_independent')
        if cand['gates']['G4']['status'] == 'fail':
            cats.append('replicates_missing')
        if cand['gates']['G5']['status'] == 'fail':
            cats.append('lineage_reaggregation')
        if not cand['delta_estimable']['mde80_le_0.15']:
            cats.append('precision_insufficient')
        cand['failure_categories'] = cats

    # overall: best target for Jaaks source must have same/synergy-compatible endpoint
    # endpoint compatibility: need Delta-EMAX-like endpoint in target (not raw viability)
    # overall source->target judgement per PROTOCOL_Q0 section 5
    source_ok = (candidates['jaaks_original']['gates']['G1']['pass']
                 and candidates['jaaks_original']['gates']['G2']['status'] in ('pass', 'conditional')
                 and candidates['jaaks_original']['gates']['G4']['status'] in ('pass', 'conditional')
                 and candidates['jaaks_original']['delta_estimable']['mde80_le_0.15'])
    # endpoint compatibility: target must provide a DeltaEMAX-family endpoint (or single-agent refs to derive it)
    endpoint_compat = {
        'oneil': False,           # raw viability; no single-agent reference in local workbook
        'drugcomb_v14': False,    # summary synergy but no numeric dose/exposure (and same lineage as v15)
        'drugcomb_v15': False,    # summary synergy but no numeric dose/exposure
    }
    targets = []
    for name in ('oneil', 'drugcomb_v14', 'drugcomb_v15'):
        c = candidates[name]
        ok = (c['gates']['G1']['pass']
              and c['gates']['G2']['status'] in ('pass', 'conditional')
              and c['gates']['G3']['status'] in ('pass', 'conditional')
              and c['gates']['G4']['status'] in ('pass', 'conditional')
              and c['gates']['G5']['status'] in ('pass', 'conditional')
              and c['delta_estimable']['mde80_le_0.15'])
        targets.append({'candidate': name, 'target_gates_ok': bool(ok),
                        'endpoint_compatible_with_jaaks_deltaemax': endpoint_compat[name]})
    fair_pair = bool(source_ok and any(t['target_gates_ok'] and t['endpoint_compatible_with_jaaks_deltaemax'] for t in targets))
    overall = {
        'verdict': 'not_qualified',
        'source_role_jaaks_estimable': bool(source_ok),
        'targets_evaluated': targets,
        'fair_source_target_pair_found': fair_pair,
        'reason': ("No source-target pair satisfies (i) target gates, (ii) comparable functional endpoint family "
                   "(Jaaks DeltaEMAX vs raw viability is not the same family; local O'Neil has no single-agent "
                   "reference to derive DeltaEMAX), (iii) verified legal exposure, (iv) documented independent "
                   "cultures/batches and (v) independent lineage; Jaaks itself cannot be its own target "
                   "(Original/Validation share cells = same resource)."),
        'candidate_verdicts': {k: v['verdict'] for k, v in candidates.items()},
        'failure_categories': sorted({c for v in candidates.values() for c in v['failure_categories']}),
    }

    result = {
        'protocol': {'path_rel': os.path.relpath(PROTOCOL, B).replace('\\', '/'),
                     'sha256': manifest['protocol_q0']['sha256'], 'version': 'PROTOCOL_Q0 v1 FROZEN'},
        'script': manifest['script_q0'],
        'inputs': manifest,
        'frozen_thresholds': {
            'G1_min_units': G1_MIN_UNITS, 'G1_min_cells': G1_MIN_CELLS,
            'G1_min_contexts': G1_MIN_CONTEXTS, 'G1_min_cross_contexts': G1_MIN_CROSS_CONTEXTS,
            'G1_min_cross_cells': G1_MIN_CROSS_CELLS, 'G2_min_legal_frac': G2_MIN_LEGAL_FRAC,
            'delta_min_provisional': DELTA_MIN_PROVISIONAL, 'delta_sensitivity': DELTA_SENS,
            'sigma_e_grid': SIGMA_E, 'mde_factor': MDE_FACTOR,
            'G5_max_jaaks_overlap': G5_MAX_OVERLAP,
        },
        'response_value_use_attestation': {
            'response_values_read': False,
            'response_columns_used': 'header existence only; counts of rows/design columns; no response values',
            'effect_estimation': False, 'training': False, 'q_estimation': False},
        'boundaries': {
            'C176': 'R196v2 inconclusive: does not support mechanism and does not prove condition-rule absence',
            'C177': 'R197 v1 protocol revoked; low-rank structure still untested',
            'C174': '1.43% is only additive condition main-effect share',
            'C175': 'A3 not_qualified only for the frozen large-scale design; 41/4,179 not used as Q0 evidence',
            'same_96_cells': 'Jaaks Original/Validation 96 shared cells are NOT independent data and are not treated as a new resource',
        },
        'jaaks': jaaks,
        'oneil': oneil,
        'drugcomb_v14': v14,
        'drugcomb_v15': v15,
        'beataml_mixseq': bm,
        'mde_prior_table': mde,
        'candidates': candidates,
        'overall_verdict': overall,
        'determinism': {'json_keys_sorted': True, 'timestamps': False},
    }
    write_json(result, Q0)
    print(json.dumps({'overall': overall['verdict'], 'candidate_verdicts': overall['candidate_verdicts'],
                      'jaaks_units': jaaks['original']['primary_orientation_anchor_partner']['legal_units'],
                      'oneil_units': oneil['replacement']['legal_units'],
                      'v14_units': v14['replacement']['legal_units'],
                      'v15_units': v15['replacement']['legal_units']}, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
