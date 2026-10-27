"""R191-PB: DrugComb v1.4 endpoint mapping / saturation / reliability audit.

Implements PROTOCOL_PB.md (frozen before any response distribution was computed).
Offline, deterministic, single process: sorted JSON keys, no timestamps, identical
bytes on re-run.

DISCIPLINE (PROTOCOL_PB.md section 1): response values of the 12 v1.4 response/derived
columns are indexed ONLY for the whitelisted statistics:
  (1) endpoint distribution / saturation, (2) semantic column checks,
  (3) reliability, (4) measurement-regime description, (5) MDE variance estimation.
No identity/annotation model is fitted; no effect is estimated; nothing is trained.

Run:  & D:\\anaconda\\envs\\maestro\\python.exe research\\2026-10-27-drugcomb-endpoint\\pb.py
Out:  pb.json, endpoint_audit.csv (next to this script)
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import os
import platform
import re
import sys

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, rankdata, skew

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QUAL = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification')
DL = os.path.join(QUAL, 'downloads')
V14 = os.path.join(DL, 'summary_table_v1.4.csv')
V15CH = os.path.join(DL, 'v15_chunks')
V15_DRUG_ID = os.path.join(DL, 'DrugComb_drug_identifiers.xlsx')
V15_CELL_ID = os.path.join(DL, 'DrugComb_cell_line_identifiers.xlsx')
E1_JSON = os.path.join(QUAL, 'e1.json')
EPMC_ZIP = os.path.join(DL, 'drugcomb_2021_supplementary_PMC8218202.zip')
SOURCES = os.path.join(BASE, 'sources')
NAR2021_XML = os.path.join(SOURCES, 'drugcomb2021_fullTextXML.xml')
NAR2019_XML = os.path.join(SOURCES, 'drugcomb2019_fullTextXML.xml')
MALY2019_XML = os.path.join(SOURCES, 'malyutina2019_fullTextXML.xml')
SYN_SRC = [os.path.join(SOURCES, n) for n in (
    'R__Calculate_score.R', 'R__Bliss.R', 'R__HSA.R', 'R__Loewe.R',
    'R__ZIP.R', 'R__Plot_synergy.R', 'R__Fitting_single_drug.R', 'README.md')]
SYN_COMMIT = '64876b193d5cba140a1fee57bccf242d29d51f74'
SYN_REPO = 'google/synergyfinderengineered'
JAAKS_XML = os.path.join(ROOT, 'data', 'external', 'research_sources', '20261022',
                         'intervention_program_renewal', 'data_auditor', 'jaaks_primary_lineage.body')
JAAKS_ORIG = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                          'Original screen_All tissues_fitted data.csv')
JAAKS_VAL = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                         'Validation screen_All tissues_fitted data.csv')
PROTOCOL = os.path.join(BASE, 'PROTOCOL_PB.md')
SCRIPT = os.path.abspath(__file__)
OUT_JSON = os.path.join(BASE, 'pb.json')
OUT_CSV = os.path.join(BASE, 'endpoint_audit.csv')

# ------------------------------------------------------------------ frozen constants
SEED = 20261027
Z_MDE80 = 2.801585218112968          # z_{0.975} + z_{0.80} (PROTOCOL_PB section 11)
ALPHA_Z = 1.959963984540054
DELTA_MIN = 0.03
B_MDE = 2000
B_MDE_SENS = 1000
N_POWER = 1000
METRICS = ['synergy_bliss', 'synergy_zip', 'synergy_hsa', 'synergy_loewe', 'S', 'css']
PRIMARY = 'synergy_bliss'
AUX = ['css_row', 'css_col', 'ri_row', 'ri_col', 'ic50_row', 'ic50_col']
METRIC_ORDER = {m: i for i, m in enumerate(METRICS)}
# construction scales / bounds (PROTOCOL_PB section 5)
SYN_BOUND_CAND = [-200.0, -100.0, -50.0, 0.0, 50.0, 100.0, 200.0]
CSS_BOUND_CAND = [0.0, 50.0, 100.0]
# saturation thresholds (PROTOCOL_PB section 5)
TH = {'S1_edge_mass': 0.90, 'S2_edge_mass': 0.20, 'S3_bound_atom': 0.05,
      'S4_sd_floor': 2.0, 'S5_extreme_atom': 0.001, 'S6_range_violation': 0.01,
      'S7_missing': 0.20}
# aggregation robustness thresholds (section 6)
TH_A1 = 0.99
TH_A2 = 0.80
TH_A3_FLAG = 0.10
# redundancy thresholds (section 7)
TH_REDUNDANT = 0.90
TH_PARTIAL = 0.70
TH_PCA1 = 0.80
# scale consistency (section 8, C5)
SCALE_RATIO_LO, SCALE_RATIO_HI = 1.0 / 3.0, 3.0
# study proxy: `eta^2` condition flag (section 9)
TH_ETA2_STUDY = 0.10

NULLISH = {'', 'NA', 'NULL', '\\N'}


# ------------------------------------------------------------------------ helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest().upper()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest().upper()


def norm(s):
    """PROTOCOL / R190-E1 convention: NFKC -> casefold -> keep alphanumerics."""
    import unicodedata
    s = unicodedata.normalize('NFKC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())


def q(x, nd=6):
    """JSON-safe rounding: NaN/inf -> None."""
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
    return round(v, nd)


def qd(d):
    """recursively round a dict/list structure."""
    if isinstance(d, dict):
        return {k: qd(v) for k, v in d.items()}
    if isinstance(d, (list, tuple)):
        return [qd(v) for v in d]
    if isinstance(d, (np.floating, np.integer, np.bool_)):
        return q(d.item())
    if isinstance(d, float):
        return q(d)
    return d


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def clean_xml_text(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'&#x[0-9a-fA-F]+;', ' ', t)
    t = re.sub(r'&[a-zA-Z]+;', ' ', t)
    return ' '.join(t.split())


def verify_quote(text_norm, quote):
    qt = ' '.join(str(quote).split())
    return qt in text_norm


def parse_float(s):
    if s is None:
        return np.nan
    s = s.strip()
    if s == '' or s.upper() in NULLISH:
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def spearman_fast(x, y):
    """Spearman rho = Pearson on average ranks (ties handled by rankdata)."""
    if len(x) < 3:
        return float('nan')
    rx = rankdata(x, method='average')
    ry = rankdata(y, method='average')
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float(np.dot(rx, rx)) * float(np.dot(ry, ry)))
    if den == 0.0:
        return float('nan')
    return float(np.dot(rx, ry) / den)


def pearson(x, y):
    if len(x) < 3:
        return float('nan')
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x - x.mean()
    y = y - y.mean()
    den = math.sqrt(float(np.dot(x, x)) * float(np.dot(y, y)))
    return float('nan') if den == 0 else float(np.dot(x, y) / den)


def dist_stats(vals, metric):
    """Block- or unit-level distribution + boundary quality (PROTOCOL_PB section 5)."""
    v = np.asarray(vals, dtype=float)
    v = v[np.isfinite(v)]
    n = int(v.size)
    out = {'n': n, 'n_missing': int(vals.size - n)}
    if n == 0:
        return out
    is_raw = metric in ('ri_row', 'ri_col', 'ic50_row', 'ic50_col')
    is_css = metric in ('css', 'css_row', 'css_col')
    cand = CSS_BOUND_CAND if is_css else SYN_BOUND_CAND
    atoms = {str(int(b)) if float(b).is_integer() else str(b): int(np.count_nonzero(v == b)) for b in cand}
    mn, mx = float(v.min()), float(v.max())
    absv = np.abs(v)
    if is_css:
        edge = np.count_nonzero((v <= 5.0) | (v >= 95.0))
        beyond = np.count_nonzero((v < 0.0) | (v > 100.0))
    elif is_raw:
        edge = None
        beyond = None
    else:
        edge = np.count_nonzero(absv >= 95.0)
        beyond = np.count_nonzero(absv > 200.0)
    pcts = np.percentile(v, [1, 25, 50, 75, 99])
    out.update({
        'mean': float(v.mean()),
        'sd': float(v.std(ddof=1)) if n > 1 else None,
        'min': mn, 'max': mx,
        'p1': float(pcts[0]), 'p25': float(pcts[1]), 'p50': float(pcts[2]),
        'p75': float(pcts[3]), 'p99': float(pcts[4]),
        'sd_over_scale': float(v.std(ddof=1)) / 100.0 if n > 1 else None,
        'atom_zero': int(np.count_nonzero(v == 0.0)),
        'atom_zero_frac': float(np.count_nonzero(v == 0.0)) / n,
        'atom_min': int(np.count_nonzero(v == mn)),
        'atom_min_frac': float(np.count_nonzero(v == mn)) / n,
        'atom_max': int(np.count_nonzero(v == mx)),
        'atom_max_frac': float(np.count_nonzero(v == mx)) / n,
        'bound_atoms': atoms,
        'bound_atom_max_frac': max(atoms.values()) / n,
        'frac_abs_ge_95': (float(edge) / n) if edge is not None else None,
        'frac_abs_ge_99': float(np.count_nonzero(absv >= 99.0)) / n,
        'frac_beyond_documented': (float(beyond) / n) if beyond is not None else None,
        'frac_gt0': float(np.count_nonzero(v > 0)) / n,
        'frac_lt0': float(np.count_nonzero(v < 0)) / n,
        'frac_eq0': float(np.count_nonzero(v == 0)) / n,
        'n_distinct': int(np.unique(v).size),
        'skew': float(skew(v)) if n > 2 else None,
        'kurtosis': float(kurtosis(v)) if n > 3 else None,
    })
    return out


def saturation_flags(stats, level):
    """PROTOCOL_PB section 5 decision rules (frozen)."""
    flags = []
    edge = stats.get('frac_abs_ge_95')
    if edge is not None and edge > TH['S1_edge_mass']:
        flags.append('S1_edge_mass_gt_0.90')
    if edge is not None and edge > TH['S2_edge_mass']:
        flags.append('S2_edge_mass_gt_0.20')
    ba = stats.get('bound_atom_max_frac')
    if ba is not None and ba > TH['S3_bound_atom']:
        flags.append('S3_boundary_atom_gt_0.05')
    sd = stats.get('sd')
    if sd is not None and sd < TH['S4_sd_floor']:
        flags.append('S4_sd_lt_2.0')
    aminf = stats.get('atom_min_frac')
    amaxf = stats.get('atom_max_frac')
    if ((aminf is not None and aminf > TH['S5_extreme_atom'])
            or (amaxf is not None and amaxf > TH['S5_extreme_atom'])):
        flags.append('S5_clipping_atom_gt_0.001')
    saturated = any(f.startswith(('S1', 'S2', 'S3', 'S4', 'S5')) for f in flags)
    rv = stats.get('frac_beyond_documented')
    range_violation = bool(rv is not None and rv > TH['S6_range_violation'])
    incomplete = bool(stats.get('n_missing') is not None and stats['n'] > 0
                      and stats['n_missing'] / max(1, stats['n_missing'] + stats['n']) > TH['S7_missing'])
    return {'level': level, 'flags': flags, 'saturated': saturated,
            'range_violation': range_violation, 'incomplete': incomplete,
            'metric_usable': bool(not saturated and not range_violation and not incomplete)}


# ---------------------------------------------------------------------- inputs
def verify_inputs():
    rec = {'errors': []}
    single = {
        'v14_summary': V14, 'e1_json': E1_JSON, 'epmc_supp_zip': EPMC_ZIP,
        'nar2021_fulltext_xml': NAR2021_XML, 'nar2019_fulltext_xml': NAR2019_XML,
        'malyutina2019_fulltext_xml': MALY2019_XML, 'jaaks_primary_lineage_body': JAAKS_XML,
        'jaaks_original_fitted': JAAKS_ORIG, 'jaaks_validation_fitted': JAAKS_VAL,
        'v15_drug_identifiers': V15_DRUG_ID, 'v15_cell_line_identifiers': V15_CELL_ID,
        'protocol_pb': PROTOCOL,
    }
    out = {}
    for k, p in single.items():
        if not os.path.exists(p):
            rec['errors'].append('missing input: ' + k)
            out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'), 'status': 'missing'}
            continue
        out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                  'bytes': os.path.getsize(p), 'sha256': sha256_file(p), 'status': 'ok'}
    # v1.5 byte-chunk sample
    chunks = {}
    for fn in sorted(os.listdir(V15CH)):
        m = re.match(r'chunk_(\d+)_(\d+)\.bin$', fn)
        if not m:
            continue
        p = os.path.join(V15CH, fn)
        chunks[fn] = {'start_byte': int(m.group(2)), 'bytes': os.path.getsize(p),
                      'sha256': sha256_file(p)}
    rec['v15_chunks'] = {'n': len(chunks), 'total_bytes': sum(c['bytes'] for c in chunks.values()),
                         'files': dict(sorted(chunks.items()))}
    # SynergyFinder implementation sources
    src = {}
    for p in SYN_SRC:
        src[os.path.basename(p)] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                                    'bytes': os.path.getsize(p), 'sha256': sha256_file(p)}
    rec['synergyfinder_src'] = {'repo': SYN_REPO, 'commit': SYN_COMMIT, 'files': dict(sorted(src.items()))}
    rec['v14_summary'] = out.pop('v14_summary')
    rec['files'] = dict(sorted(out.items()))
    rec['script_pb'] = {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                        'bytes': os.path.getsize(SCRIPT), 'sha256': sha256_file(SCRIPT)}
    return rec


# ------------------------------------------------------------- v1.4 summary read
def read_v14():
    """Single streaming pass. Response values are indexed only for the whitelist stats."""
    names = METRICS + AUX
    resp_idx = {}
    with open(V14, newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        col = {c: i for i, c in enumerate(header)}
        missing = [c for c in ['block_id', 'drug_row', 'drug_col', 'cell_line_name'] if c not in col]
        if missing:
            raise SystemExit('v1.4 header missing: %s' % missing)
        for m in names:
            resp_idx[m] = col.get(m)
        i_b, i_dr, i_dc, i_cl = col['block_id'], col['drug_row'], col['drug_col'], col['cell_line_name']
        cap = 600_000

        def grow(a, n):
            b = np.empty(max(cap, int(n * 1.5) + 1), dtype=a.dtype)
            b[:n] = a[:n]
            return b

        n = 0
        rows_total = 0
        mono = 0
        blk_id = np.empty(cap, dtype=np.int64)
        unit_code = np.empty(cap, dtype=np.int32)
        pair_code = np.empty(cap, dtype=np.int32)
        cell_code = np.empty(cap, dtype=np.int32)
        drug_code = np.empty(cap, dtype=np.int32)
        vals = {m: np.empty(cap, dtype=float) for m in names}
        unit_map, pair_map, cell_map, drug_map = {}, {}, {}, {}
        unit_keys, pair_keys, cell_names, drug_names = [], [], [], []

        def enc(s, mp, lst):
            v = mp.get(s)
            if v is None:
                v = len(lst)
                mp[s] = v
                lst.append(s)
            return v

        for row in rdr:
            rows_total += 1
            dr = row[i_dr].strip()
            dc = row[i_dc].strip()
            cl = row[i_cl].strip()
            if dr.upper() in NULLISH or dc.upper() in NULLISH:
                mono += 1
                continue
            ndr, ndc, ncl = norm(dr), norm(dc), norm(cl)
            a, b = (ndr, ndc) if ndr <= ndc else (ndc, ndr)
            pk = enc(a + '\x1f' + b, pair_map, pair_keys)
            uk = enc(ncl + '\x1f' + a + '\x1f' + b, unit_map, unit_keys)
            ck = enc(ncl, cell_map, cell_names)
            dak = enc(a, drug_map, drug_names)
            dbk = enc(b, drug_map, drug_names)
            if n >= cap:
                cap = int(cap * 1.5)
                blk_id = grow(blk_id, n)
                unit_code = grow(unit_code, n)
                pair_code = grow(pair_code, n)
                cell_code = grow(cell_code, n)
                drug_code = grow(drug_code, n)
                for m in names:
                    vals[m] = grow(vals[m], n)
            try:
                blk_id[n] = int(row[i_b])
            except (TypeError, ValueError):
                blk_id[n] = -1
            unit_code[n] = uk
            pair_code[n] = pk
            cell_code[n] = ck
            drug_code[n] = dak
            for m in names:
                j = resp_idx[m]
                vals[m][n] = parse_float(row[j]) if j is not None and j < len(row) else np.nan
            n += 1
    out = {
        'header': header, 'rows_total': rows_total, 'rows_monotherapy_like': mono,
        'n_blocks_combo': n, 'conc_units': {},
        'arrays': {'block_id': blk_id[:n], 'unit': unit_code[:n], 'pair': pair_code[:n],
                   'cell': cell_code[:n], 'drug_a': drug_code[:n]},
        'values': {m: vals[m][:n] for m in names},
        'unit_keys': unit_keys, 'pair_keys': pair_keys,
        'cell_names': cell_names, 'drug_names': drug_names,
    }
    # pair -> drug codes (from keys)
    pair_a = np.empty(len(pair_keys), dtype=np.int32)
    pair_b = np.empty(len(pair_keys), dtype=np.int32)
    for i, k in enumerate(pair_keys):
        a, b = k.split('\x1f')
        pair_a[i] = drug_map[a]
        pair_b[i] = drug_map[b]
    out['pair_drug'] = (pair_a, pair_b)
    return out


def read_v15_sample():
    """Parse the fixed 60x1MB byte-chunk sample of the v1.5 summary table."""
    files = sorted(f for f in os.listdir(V15CH) if f.startswith('chunk_'))
    header = None
    idx = None
    rows = 0
    mono = 0
    study_rows = collections.Counter()
    study_block_ids = collections.defaultdict(list)
    bliss_vals = collections.defaultdict(list)
    per_chunk = {}
    for fn in files:
        m = re.match(r'chunk_(\d+)_(\d+)\.bin$', fn)
        start = int(m.group(2))
        data = open(os.path.join(V15CH, fn), 'rb').read()
        if start > 0:
            k = data.find(b'\n')
            if k < 0:
                continue
            data = data[k + 1:]
        k = data.rfind(b'\n')
        if k < 0:
            continue
        text = data[:k + 1].decode('utf-8', errors='replace')
        rdr = csv.reader(text.split('\n'))
        cnt = 0
        for row in rdr:
            if not row:
                continue
            if start == 0 and row[0] == 'block_id':
                header = row
                idx = {c: i for i, c in enumerate(header)}
                continue
            if idx is None:
                continue
            rows += 1
            cnt += 1
            dr = row[idx['drug_row']].strip()
            dc = row[idx['drug_col']].strip()
            study = row[idx['study_name']].strip()
            study_rows[study] += 1
            if dr.upper() in NULLISH or dc.upper() in NULLISH:
                mono += 1
                continue
            try:
                study_block_ids[study].append(int(row[idx['block_id']]))
            except (TypeError, ValueError):
                pass
            b = parse_float(row[idx['synergy_bliss']]) if 'synergy_bliss' in idx else np.nan
            if math.isfinite(b):
                bliss_vals[study].append(b)
        per_chunk[fn] = cnt
    table = {}
    for s in sorted(study_rows):
        bl = study_block_ids.get(s, [])
        bv = np.asarray(bliss_vals.get(s, []), dtype=float)
        table[s] = {
            'sample_rows': int(study_rows[s]),
            'sample_combo_rows': int(len(bl)),
            'block_id_min': int(min(bl)) if bl else None,
            'block_id_max': int(max(bl)) if bl else None,
            'synergy_bliss_n': int(bv.size),
            'synergy_bliss_mean': float(bv.mean()) if bv.size else None,
            'synergy_bliss_sd': float(bv.std(ddof=1)) if bv.size > 1 else None,
            'synergy_bliss_p50': float(np.median(bv)) if bv.size else None,
        }
    all_bliss = np.asarray([x for s in sorted(bliss_vals) for x in bliss_vals[s]], dtype=float)
    return {'chunks': len(files), 'rows': rows, 'mono_rows': mono,
            'combo_rows': rows - mono, 'header': header,
            'studies': table, 'per_chunk_rows': per_chunk,
            'synergy_bliss_all': {
                'n': int(all_bliss.size),
                'mean': float(all_bliss.mean()) if all_bliss.size else None,
                'sd': float(all_bliss.std(ddof=1)) if all_bliss.size > 1 else None,
                'p1': float(np.percentile(all_bliss, 1)) if all_bliss.size else None,
                'p50': float(np.median(all_bliss)) if all_bliss.size else None,
                'p99': float(np.percentile(all_bliss, 99)) if all_bliss.size else None,
                'min': float(all_bliss.min()) if all_bliss.size else None,
                'max': float(all_bliss.max()) if all_bliss.size else None}}


# ----------------------------------------------------------- unit-level utilities
def unit_aggregates(unit, values, n_units):
    """mean / median / max / first-block value / count, per unit (NaN-aware)."""
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(v)
    cnt = np.bincount(unit[ok], minlength=n_units).astype(np.int64)
    sums = np.bincount(unit[ok], weights=v[ok], minlength=n_units)
    mean = np.full(n_units, np.nan)
    mean[cnt > 0] = sums[cnt > 0] / cnt[cnt > 0]
    mx = np.full(n_units, -np.inf)
    if ok.any():
        np.maximum.at(mx, unit[ok], v[ok])
    mx[~np.isfinite(mx)] = np.nan
    # median via pandas groupby
    med = np.full(n_units, np.nan)
    if ok.any():
        s = pd.Series(v[ok]).groupby(unit[ok], sort=False).median()
        med[s.index.to_numpy()] = s.to_numpy()
    return {'mean': mean, 'median': med, 'max': mx, 'count': cnt}


def first_block_values(unit, block_id, values, n_units):
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(v) & (block_id >= 0)
    idx = np.nonzero(ok)[0]
    order = idx[np.argsort(block_id[idx], kind='stable')]
    uo = unit[order]
    uniq, first_pos = np.unique(uo, return_index=True)   # first occurrence in block_id order
    out = np.full(n_units, np.nan)
    out[uniq] = v[order[first_pos]]
    return out


def eta_squared(groups, values):
    """between-group variance share for categorical `groups` on finite values."""
    v = np.asarray(values, dtype=float)
    g = np.asarray(groups)
    ok = np.isfinite(v)
    v, g = v[ok], g[ok]
    if v.size < 3:
        return None, 0
    grand = v.mean()
    ss_tot = float(((v - grand) ** 2).sum())
    if ss_tot == 0:
        return None, 0
    uniq, inv = np.unique(g, return_inverse=True)
    cnt = np.bincount(inv)
    sums = np.bincount(inv, weights=v)
    keep = cnt > 0
    means = sums[keep] / cnt[keep]
    ss_between = float((cnt[keep] * (means - grand) ** 2).sum())
    return ss_between / ss_tot, int(uniq.size)


def icc_oneway(unit, values, n_units):
    """One-way random-effects ICC(1) + split-half reliability (PROTOCOL_PB section 9)."""
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(v)
    cnt = np.bincount(unit[ok], minlength=n_units).astype(np.int64)
    keep = cnt >= 2
    if int(keep.sum()) < 10:
        return {'n_units_ge2': int(keep.sum())}
    sums = np.bincount(unit[ok], weights=v[ok], minlength=n_units)
    sumsq = np.bincount(unit[ok], weights=v[ok] ** 2, minlength=n_units)
    m = cnt[keep].astype(float)
    s1 = sums[keep]
    s2 = sumsq[keep]
    ss_within_units = np.maximum(s2 - s1 ** 2 / m, 0.0)
    ss_within = float(ss_within_units.sum())
    df_within = int((m - 1).sum())
    sigma2_w = ss_within / df_within if df_within > 0 else None
    grand = float(s1.sum() / m.sum())
    ss_between = float((m * (s1 / m - grand) ** 2).sum())
    k_units = int(keep.sum())
    msb = ss_between / (k_units - 1) if k_units > 1 else None
    m0 = (m.sum() - (m ** 2).sum() / m.sum()) / (k_units - 1) if k_units > 1 else None
    sigma2_b = max(0.0, (msb - sigma2_w) / m0) if (msb is not None and m0) else None
    icc = (sigma2_b / (sigma2_b + sigma2_w)) if (sigma2_b is not None and sigma2_w) else None
    within_sd = np.sqrt(ss_within_units / np.maximum(m - 1, 1))
    return {
        'n_units_ge2': k_units,
        'icc1': icc,
        'sigma2_between': sigma2_b,
        'sigma2_within': sigma2_w,
        'mean_blocks': float(m.mean()),
        'within_unit_sd_median': float(np.median(within_sd)),
        'within_unit_sd_p25': float(np.percentile(within_sd, 25)),
        'within_unit_sd_p75': float(np.percentile(within_sd, 75)),
        'reliability_at_mean_m': (float(icc * m.mean() / (1 + (m.mean() - 1) * icc))
                                  if icc is not None else None),
        'rho_ceiling_sqrt_reliability': (float(math.sqrt(icc * m.mean() / (1 + (m.mean() - 1) * icc)))
                                          if icc is not None and icc > 0 else None),
    }


def split_half(unit, block_id, values, n_units):
    """Alternating split on block_id order within unit; Spearman-Brown corrected."""
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(v)
    idx = np.nonzero(ok)[0]
    order = idx[np.lexsort((block_id[idx], unit[idx]))]
    u = unit[order]
    starts = np.searchsorted(u, np.arange(n_units), side='left')
    rank = np.arange(order.size) - starts[u]
    half = (rank % 2).astype(np.int64)
    key = u.astype(np.int64) * 2 + half
    cnt = np.bincount(key, minlength=n_units * 2)
    sums = np.bincount(key, weights=v[order], minlength=n_units * 2)
    cntA, cntB = cnt[0::2], cnt[1::2]
    mA = np.where(cntA > 0, sums[0::2] / np.maximum(cntA, 1), np.nan)
    mB = np.where(cntB > 0, sums[1::2] / np.maximum(cntB, 1), np.nan)
    okc = np.isfinite(mA) & np.isfinite(mB)
    n = int(okc.sum())
    if n < 10:
        return {'n_units_split': n}
    r = pearson(mA[okc], mB[okc])
    rs = spearman_fast(mA[okc], mB[okc])
    sb = (2 * r / (1 + r)) if (r == r and r > -1) else None
    return {'n_units_split': n, 'pearson_half': r, 'spearman_half': rs,
            'spearman_brown': sb}


def pairwise_corr_matrix(arrays, metrics, min_n=100, method='spearman'):
    """Spearman (or Pearson) matrix with pairwise-complete cases."""
    out = {}
    for i, a in enumerate(metrics):
        for b in metrics[i + 1:]:
            x = arrays[a]
            y = arrays[b]
            ok = np.isfinite(x) & np.isfinite(y)
            n = int(ok.sum())
            if n < min_n:
                r = float('nan')
            elif method == 'pearson':
                r = pearson(x[ok], y[ok])
            else:
                r = spearman_fast(x[ok], y[ok])
            out['%s~%s' % (a, b)] = {'rho': r, 'n': n}
    return out


# ------------------------------------------------------------------------- MDE
def mde80(se):
    return Z_MDE80 * se if se is not None and math.isfinite(se) else None


def bootstrap_mde(y, pair_idx, cell_idx, npairs, ncells, B, seed):
    """Null-information clustered bootstrap (PROTOCOL_PB section 11)."""
    rng = np.random.default_rng(seed)
    nunits = y.size
    ro = np.arange(nunits)
    rhos_a = np.empty(B)
    rhos_b = np.empty(B)
    for b in range(B):
        # Regime A: drug-pair clusters only
        cp = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        idx = np.repeat(ro, cp[pair_idx])
        z = rng.normal(size=npairs)
        rhos_a[b] = spearman_fast(z[pair_idx][idx], y[idx])
        # Regime B: two-way (drug pair x cell line) clusters
        cp2 = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        cc = np.bincount(rng.integers(0, ncells, ncells), minlength=ncells)
        idx2 = np.repeat(ro, cp2[pair_idx] * cc[cell_idx])
        z2 = rng.normal(size=npairs)
        rhos_b[b] = spearman_fast(z2[pair_idx][idx2], y[idx2])
    out = {'B': B, 'seed': seed}
    for tag, arr in (('A_pair_clustered', rhos_a), ('B_two_way_clustered', rhos_b)):
        sd = float(arr.std(ddof=1))
        out[tag] = {'se': sd, 'mde80': mde80(sd), 'mean_null_rho': float(arr.mean()),
                    'q025': float(np.percentile(arr, 2.5)),
                    'q975': float(np.percentile(arr, 97.5))}
    n = nunits
    out['iid_analytic'] = {'se': 1.0 / math.sqrt(n - 1) if n > 2 else None,
                           'mde80': mde80(1.0 / math.sqrt(n - 1)) if n > 2 else None}
    return out


def mde_diagnostics(y, pair_idx, npairs, B, seed):
    """Post-pre-registration decomposition of the MDE (reported, does NOT change the gate).

    The pre-registered MDE gate uses the two-way cluster bootstrap of PROTOCOL_PB section 11.
    These three additional operationalizations are reported to show how much of the MDE is
    prediction-vector randomness vs pair-sampling vs cell-sampling:
      perm_fixed_y   : z redrawn iid per pair, y fixed (permutation null of the arm);
      pair_bootstrap : pairs resampled, statistic on pair-level means;
      z_fixed        : pairs resampled but z fixed across replicates.
    """
    rng = np.random.default_rng(seed)
    nunits = y.size
    ro = np.arange(nunits)
    cntp = np.bincount(pair_idx, minlength=npairs).astype(float)
    pmean = np.bincount(pair_idx, weights=y, minlength=npairs) / np.maximum(cntp, 1)
    out = {}
    r_perm = np.empty(B)
    r_pair = np.empty(B)
    r_zfix = np.empty(B)
    zf = rng.normal(size=npairs)
    for b in range(B):
        z = rng.normal(size=npairs)
        r_perm[b] = spearman_fast(z[pair_idx], y)
        idxp = rng.integers(0, npairs, npairs)
        r_pair[b] = spearman_fast(rng.normal(size=npairs)[idxp], pmean[idxp])
        cp = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        idx = np.repeat(ro, cp[pair_idx])
        r_zfix[b] = spearman_fast(zf[pair_idx][idx], y[idx])
    for tag, arr in (('permutation_fixed_y', r_perm),
                     ('pair_level_bootstrap', r_pair),
                     ('pair_bootstrap_z_fixed', r_zfix)):
        sd = float(arr.std(ddof=1))
        out[tag] = {'se': sd, 'mde80': mde80(sd), 'mean_null_rho': float(arr.mean())}
    out['note'] = ('post-pre-registration diagnostic decomposition; the pre-registered gate '
                   'remains the two-way cluster bootstrap MDE80 (PROTOCOL_PB section 11/12)')
    return out


def power_check(y, pair_idx, npairs, se_ref, targets, reps, seed):
    """Empirical power at given unit-level rho (diagnostic of the MDE definition)."""
    cntp = np.bincount(pair_idx, minlength=npairs).astype(float)
    sums = np.bincount(pair_idx, weights=y, minlength=npairs)
    pair_mean = sums / np.maximum(cntp, 1)
    pm_unit = pair_mean[pair_idx]
    rho_pm = spearman_fast(pm_unit, y)
    sdpm = float(pm_unit.std())
    base = (pair_mean - pair_mean.mean()) / sdpm if sdpm > 0 else np.zeros(npairs)
    out = {'rho_pair_mean_replication': rho_pm, 'reps': reps}
    vals = {}
    for delta in targets:
        c = min(1.0, float(delta) / rho_pm) if (rho_pm and rho_pm > 0) else 0.0
        resid = math.sqrt(max(0.0, 1.0 - c * c))
        rng = np.random.default_rng((seed + int(round(float(delta) * 1000003))) & 0x7FFFFFFF)
        rej = 0
        for _ in range(reps):
            z = c * base + resid * rng.normal(size=npairs)
            rho = spearman_fast(z[pair_idx], y)
            if rho > ALPHA_Z * se_ref:
                rej += 1
        vals[str(delta)] = {'realized_pair_weight': c, 'reject_rate': rej / reps}
    out['targets'] = vals
    return out


# ------------------------------------------------------------- study proxy logic
def study_proxy(v14, v15):
    """Assign v1.4 blocks to v1.5-sample study windows (PROTOCOL_PB section 3)."""
    windows = {}
    for s, rec in v15['studies'].items():
        lo, hi = rec['block_id_min'], rec['block_id_max']
        if lo is not None and hi is not None:
            windows[s] = (int(lo), int(hi))
    studies = sorted(windows)
    bid = v14['arrays']['block_id']
    codes = np.full(bid.size, -1, dtype=np.int32)   # -1 unassigned
    for si, s in enumerate(studies):                 # explicit (small n_studies)
        lo, hi = windows[s]
        codes[(bid >= lo) & (bid <= hi)] = si
    # overlap accounting (windows are derived from a 4.22% byte sample, so a v1.4
    # block can fall in more than one sampled study window)
    cnt_windows = np.zeros(bid.size, dtype=np.int16)
    for s in studies:
        lo, hi = windows[s]
        cnt_windows[(bid >= lo) & (bid <= hi)] += 1
    overlap_blocks = int(np.count_nonzero(cnt_windows > 1))
    ambiguous_studies = sorted({studies[i] for i in range(len(studies))
                                if any(j != i and not (windows[studies[i]][1] < windows[studies[j]][0]
                                                       or windows[studies[j]][1] < windows[studies[i]][0])
                                       for j in range(len(studies)))})
    return {'windows': {s: list(windows[s]) for s in studies},
            'block_study_code': codes, 'studies': studies,
            'ambiguous_study_windows': ambiguous_studies,
            'overlapping_blocks': overlap_blocks,
            'assigned_blocks': int(np.count_nonzero(codes >= 0)),
            'n_blocks': int(bid.size)}


def matrix_sizes_from_e1():
    """Study -> matrix sizes / identity counts from the paper S1 (via e1.json)."""
    d = json.load(open(E1_JSON, encoding='utf-8'))['s1_study_table']['studies']
    out = {}
    for rec in d:
        sizes = []
        for m in re.finditer(r'(\d+)\s*[x×]\s*(\d+)', rec.get('matrix') or ''):
            sizes.append((int(m.group(1)), int(m.group(2))))
        out[rec['study']] = {'matrix': rec.get('matrix'), 'sizes': sizes,
                             'monotherapy': rec.get('monotherapy'),
                             'n_blocks': rec.get('n_blocks'),
                             'n_cell_lines': rec.get('n_cell_lines'),
                             'n_drugs': rec.get('n_drugs')}
    return out


# ---------------------------------------------------------------- main analysis
def main():
    import time
    t0 = time.time()
    print('[1/12] hash inputs ...', flush=True)
    inputs = verify_inputs()
    t_inputs = time.time()

    print('[2/12] read v1.4 summary (streaming, single pass) ...', flush=True)
    v14 = read_v14()
    blk = v14['arrays']['block_id']
    unit = v14['arrays']['unit']
    pair = v14['arrays']['pair']
    cell = v14['arrays']['cell']
    drug_a = v14['arrays']['drug_a']
    vals = v14['values']
    n_blocks = int(blk.size)
    n_units = len(v14['unit_keys'])
    n_pairs = len(v14['pair_keys'])
    n_cells = len(v14['cell_names'])
    n_drugs = len(v14['drug_names'])
    t_v14 = time.time()
    print('    combo blocks %d / units %d / pairs %d / drugs %d / cells %d (%.1fs)'
          % (n_blocks, n_units, n_pairs, n_drugs, n_cells, t_v14 - t_inputs), flush=True)

    unit_sizes = np.bincount(unit, minlength=n_units)
    unit_pair = np.zeros(n_units, dtype=np.int64)
    unit_cell = np.zeros(n_units, dtype=np.int64)
    unit_pair[unit] = pair
    unit_cell[unit] = cell
    pair_a, pair_b = v14['pair_drug']

    structure = {
        'rows_total': v14['rows_total'],
        'rows_monotherapy_like': v14['rows_monotherapy_like'],
        'n_blocks_combo': n_blocks,
        'n_blocks_distinct_block_id': int(np.unique(blk).size),
        'block_id_min_combo': int(blk.min()), 'block_id_max_combo': int(blk.max()),
        'n_drugs_normalized': n_drugs, 'n_cells': n_cells, 'n_pairs': n_pairs,
        'n_cell_x_pair_units': n_units,
        'blocks_per_unit_mean': float(n_blocks / n_units),
        'blocks_per_unit_distribution': {str(k): int(v) for k, v in
                                         sorted(collections.Counter(unit_sizes.tolist()).items())},
        'units_with_ge2_blocks': int(np.count_nonzero(unit_sizes >= 2)),
        'units_with_ge3_blocks': int(np.count_nonzero(unit_sizes >= 3)),
        'has_study_column': 'study_name' in v14['header'],
        'dose_value_columns': [c for c in v14['header'] if c.startswith('conc')],
    }

    # ------------------------------------------------ both-unseen design (r grid)
    names_enc = v14['drug_names']                  # code -> normalized name (encounter order)
    names_sorted = sorted(names_enc)                # lexicographic split (R190-E1 convention)
    hold_sets = {}
    for r in (0.20, 0.30, 0.40):
        k = max(1, round(r * len(names_sorted)))
        step = max(1, len(names_sorted) // k)
        hold = set(names_sorted[0::step][:k])
        hold_sets['%.2f' % r] = {
            'k_holdout': len(hold), 'step': step,
            'member_code': np.array([1 if n in hold else 0 for n in names_enc], dtype=np.int8)}
    bu = {}
    for rtag, h in hold_sets.items():
        mem = h['member_code']
        keep = (mem[pair_a[unit_pair]] == 1) & (mem[pair_b[unit_pair]] == 1)
        bu[rtag] = {'n_units': int(keep.sum()),
                    'n_pairs': int(np.unique(unit_pair[keep]).size),
                    'mask': keep}
    structure['both_unseen'] = {rt: {'k_holdout': hold_sets[rt]['k_holdout'],
                                     'step_lexicographic': hold_sets[rt]['step'],
                                     'n_cell_x_pair_units': bu[rt]['n_units'],
                                     'n_pairs': bu[rt]['n_pairs']}
                                for rt in hold_sets}

    print('[3/12] block-level endpoint distributions + saturation ...', flush=True)
    blk_stats = {m: dist_stats(vals[m], m) for m in METRICS}
    aux_stats = {m: dist_stats(vals[m], m) for m in AUX}

    print('[4/12] unit-level aggregation (mean/median/max/first) ...', flush=True)
    aggs = {m: unit_aggregates(unit, vals[m], n_units) for m in METRICS}
    firsts = {m: first_block_values(unit, blk, vals[m], n_units) for m in METRICS}
    unit_stats = {m: dist_stats(aggs[m]['mean'], m) for m in METRICS}

    saturation = {}
    for m in METRICS:
        b = saturation_flags(blk_stats[m], 'block')
        u = saturation_flags(unit_stats[m], 'unit')
        # missing fraction on block level
        miss_frac = blk_stats[m]['n_missing'] / n_blocks if n_blocks else None
        b['missing_frac'] = miss_frac
        u['missing_frac'] = None
        if miss_frac is not None and miss_frac > TH['S7_missing']:
            b['incomplete'] = True
            b['metric_usable'] = False
            b['flags'].append('S7_missing_gt_0.20')
        saturation[m] = {
            'block': b, 'unit': u,
            'saturated': bool(b['saturated'] or u['saturated']),
            'range_violation': bool(b['range_violation'] or u['range_violation']),
            'incomplete': bool(b['incomplete'] or u['incomplete']),
            'metric_usable': bool(b['metric_usable'] and u['metric_usable']),
        }
    primary_usable = saturation[PRIMARY]['metric_usable']

    print('[5/12] aggregation robustness (A1-A4) ...', flush=True)
    agg_rob = {}
    for m in METRICS:
        mean_v = aggs[m]['mean']
        med_v = aggs[m]['median']
        first_v = firsts[m]
        max_v = aggs[m]['max']
        ok = np.isfinite(mean_v) & np.isfinite(med_v)
        a1 = spearman_fast(mean_v[ok], med_v[ok]) if int(ok.sum()) > 10 else None
        ok2 = (unit_sizes >= 2) & np.isfinite(mean_v) & np.isfinite(first_v)
        a2 = spearman_fast(mean_v[ok2], first_v[ok2]) if int(ok2.sum()) > 10 else None
        ok3 = np.isfinite(mean_v)
        a3 = spearman_fast(unit_sizes[ok3].astype(float), mean_v[ok3]) if int(ok3.sum()) > 10 else None
        ok4 = np.isfinite(mean_v) & np.isfinite(max_v)
        a4 = spearman_fast(mean_v[ok4], max_v[ok4]) if int(ok4.sum()) > 10 else None
        agg_rob[m] = {
            'A1_rho_mean_median': a1, 'A1_pass': bool(a1 is not None and a1 >= TH_A1),
            'A2_rho_mean_firstblock_ge2': a2, 'A2_pass': bool(a2 is not None and a2 >= TH_A2),
            'A3_rho_nblocks_mean': a3,
            'A3_block_count_bias_flag': bool(a3 is not None and abs(a3) > TH_A3_FLAG),
            'A4_rho_mean_max': a4,
            'n_units_ge2': int(np.count_nonzero(unit_sizes >= 2)),
            'n_units_defined': int(np.count_nonzero(np.isfinite(mean_v))),
        }

    primary_agg_ok = bool(agg_rob[PRIMARY]['A1_pass'] and agg_rob[PRIMARY]['A2_pass'])

    print('[6/12] semantic / construction checks ...', flush=True)
    sem = {}

    def identity_check(target, candidates, names_):
        tv = vals[target] if target in vals else aggs[target]['mean']
        res = {}
        for cand, expr in candidates:
            av = expr
            ok = np.isfinite(tv) & np.isfinite(av)
            n = int(ok.sum())
            if n < 10:
                res[cand] = {'n': n}
                continue
            d = tv[ok] - av[ok]
            res[cand] = {'n': n, 'max_abs_diff': float(np.abs(d).max()),
                         'rms_diff': float(np.sqrt((d ** 2).mean())),
                         'frac_within_1e-6': float(np.count_nonzero(np.abs(d) <= 1e-6)) / n,
                         'frac_within_0.01': float(np.count_nonzero(np.abs(d) <= 0.01)) / n,
                         'pearson': pearson(tv[ok], av[ok]),
                         'spearman': spearman_fast(tv[ok], av[ok])}
        return res

    sem['S_identity_block'] = identity_check('S', [
        ('css_minus_ri_sum', vals['css'] - vals['ri_row'] - vals['ri_col']),
        ('css_minus_ri_max', vals['css'] - np.maximum(vals['ri_row'], vals['ri_col'])),
        ('css_minus_ri_mean', vals['css'] - 0.5 * (vals['ri_row'] + vals['ri_col'])),
    ], None)
    sem['css_identity_block'] = identity_check('css', [
        ('mean_css_row_col', 0.5 * (vals['css_row'] + vals['css_col'])),
        ('css_row_only', vals['css_row']),
        ('css_col_only', vals['css_col']),
    ], None)
    sem['range_checks'] = {}
    for m in METRICS + AUX:
        v = vals[m]
        ok = np.isfinite(v)
        if not ok.any():
            continue
        vv = v[ok]
        sem['range_checks'][m] = {
            'n': int(ok.sum()), 'min': float(vv.min()), 'max': float(vv.max()),
            'frac_outside_0_100': float(np.count_nonzero((vv < 0) | (vv > 100)) / vv.size),
            'frac_abs_gt_200': float(np.count_nonzero(np.abs(vv) > 200) / vv.size),
        }
    # exact duplicate blocks inside a unit (same 6-metric vector)
    ok_all = np.ones(n_blocks, dtype=bool)
    for m in METRICS:
        ok_all &= np.isfinite(vals[m])
    dup_units = 0
    dup_blocks = 0
    if ok_all.any():
        seen = collections.Counter()
        order = np.lexsort((np.arange(n_blocks), unit[ok_all]))
        keys = []
        idxs = np.nonzero(ok_all)[0][order]
        for i in idxs:
            key = (int(unit[i]),) + tuple(round(float(vals[m][i]), 9) for m in METRICS)
            keys.append(key)
        cnt = collections.Counter(keys)
        dup_groups = {k: c for k, c in cnt.items() if c > 1}
        dup_units = len({k[0] for k in dup_groups})
        dup_blocks = int(sum(v - 1 for v in dup_groups.values()))
    sem['exact_duplicate_blocks'] = {'units_with_duplicates': dup_units,
                                     'extra_duplicate_blocks': dup_blocks,
                                     'blocks_with_complete_metrics': int(ok_all.sum())}

    print('[7/12] redundancy (block + unit) ...', flush=True)
    rho_block = pairwise_corr_matrix(vals, METRICS, method='spearman')
    pearson_block = pairwise_corr_matrix(vals, METRICS, method='pearson')
    unit_mean_arrays = {m: aggs[m]['mean'] for m in METRICS}
    rho_unit = pairwise_corr_matrix(unit_mean_arrays, METRICS, method='spearman')
    pearson_unit = pairwise_corr_matrix(unit_mean_arrays, METRICS, method='pearson')
    # PCA on block-level ranks (complete cases)
    pca = {}
    okc = np.ones(n_blocks, dtype=bool)
    for m in METRICS:
        okc &= np.isfinite(vals[m])
    n_pca = int(okc.sum())
    if n_pca > 100:
        R = np.column_stack([rankdata(vals[m][okc]) for m in METRICS])
        R = (R - R.mean(0)) / R.std(0)
        C = np.corrcoef(R, rowvar=False)
        ev = np.linalg.eigvalsh(C)[::-1]
        pca = {'n': n_pca,
               'eigenvalues': [float(x) for x in ev],
               'pc1_var_share': float(ev[0] / ev.sum()),
               'pc2_var_share': float(ev[1] / ev.sum()),
               'pc1_pc2_share': float((ev[0] + ev[1]) / ev.sum())}
    # redundancy verdict between primary and each other metric (unit level)
    red_classes = {}
    prim = PRIMARY
    for m in METRICS:
        if m == prim:
            continue
        rec = rho_unit.get('%s~%s' % (prim, m)) or rho_unit.get('%s~%s' % (m, prim))
        r = rec['rho'] if rec else None
        if r is None:
            cls = 'unknown'
        elif r >= TH_REDUNDANT:
            cls = 'redundant'
        elif r >= TH_PARTIAL:
            cls = 'partially_redundant'
        else:
            cls = 'distinct'
        red_classes['%s_vs_%s' % (prim, m)] = {'rho_unit': r, 'class': cls}
    redundancy = {
        'block_spearman': dict(sorted(rho_block.items())),
        'block_pearson': dict(sorted(pearson_block.items())),
        'unit_spearman': dict(sorted(rho_unit.items())),
        'unit_pearson': dict(sorted(pearson_unit.items())),
        'pca_block_ranks': pca,
        'classes_primary_vs_others': dict(sorted(red_classes.items())),
        'single_dominant_factor': bool(pca.get('pc1_var_share') is not None
                                       and pca['pc1_var_share'] >= TH_PCA1),
        'pre_probe_reconciliation': ('R191 Lead pre-probe (reference only) reported block-level '
                                     'bliss-zip 0.920 and bliss-hsa 0.801; the corresponding '
                                     'Pearson block values are reported here for reconciliation. '
                                     'The pre-registered endpoint selection uses Spearman '
                                     '(rank) redundancy, which is the criterion stated in '
                                     'PROTOCOL_PB section 7.'),
    }

    print('[8/12] v1.5 byte-chunk sample (study layer) ...', flush=True)
    v15 = read_v15_sample()
    t_v15 = time.time()

    print('[9/12] study / dose-matrix regime + reliability ...', flush=True)
    prox = study_proxy(v14, v15)
    codes = prox['block_study_code']
    studies = prox['studies']
    sizes_map = matrix_sizes_from_e1()

    # reliability per metric (block level) + split-half + same-study vs cross-study
    reliability = {}
    for m in METRICS:
        icc = icc_oneway(unit, vals[m], n_units)
        sh = split_half(unit, blk, vals[m], n_units)
        reliability[m] = {'icc': icc, 'split_half': sh}
    # primary: within-unit sd by same-study vs cross-study proxy
    prim_v = vals[PRIMARY]
    okp = np.isfinite(prim_v)
    unit_codes = np.full(n_units, -1, dtype=np.int32)
    unit_codes[unit[okp]] = codes[okp]
    cnt_codes = np.bincount(unit[okp], weights=None, minlength=n_units)
    # per-unit: min/max study code among its blocks
    umin = np.full(n_units, 10 ** 6, dtype=np.int64)
    umax = np.full(n_units, -10 ** 6, dtype=np.int64)
    np.minimum.at(umin, unit[okp & (codes >= 0)], codes[okp & (codes >= 0)])
    np.maximum.at(umax, unit[okp & (codes >= 0)], codes[okp & (codes >= 0)])
    # use only units where all finite blocks are assigned (>=0) and >=2 blocks
    n_fin = np.bincount(unit[okp], minlength=n_units)
    n_asg = np.bincount(unit[okp & (codes >= 0)], minlength=n_units)
    all_assigned = (n_asg == n_fin) & (n_fin >= 2)
    same_study = all_assigned & (umin == umax)
    cross_study = all_assigned & (umin != umax)
    def within_sd_subset(mask_units):
        sel = np.zeros(n_blocks, dtype=bool)
        sel[okp] = mask_units[unit[okp]]
        if not sel.any():
            return {'n_units': 0}
        u = unit[sel]
        v = prim_v[sel]
        cu = np.bincount(u, minlength=n_units)
        su = np.bincount(u, weights=v, minlength=n_units)
        sq = np.bincount(u, weights=v ** 2, minlength=n_units)
        keep = cu >= 2
        m = cu[keep].astype(float)
        ss = np.maximum(sq[keep] - su[keep] ** 2 / m, 0.0)
        wsd = np.sqrt(ss / np.maximum(m - 1, 1))
        return {'n_units': int(keep.sum()), 'within_unit_sd_median': float(np.median(wsd)),
                'within_unit_sd_mean': float(wsd.mean())}
    reliability['primary_within_unit_by_study_proxy'] = {
        'same_study_proxy': within_sd_subset(same_study),
        'cross_study_proxy': within_sd_subset(cross_study),
        'units_ge2_fully_assigned': int(all_assigned.sum()),
        'units_same_study': int(same_study.sum()),
        'units_cross_study': int(cross_study.sum()),
    }

    # by-cell stability (primary), block level and unit level
    eta_cell_blk, n_cell_groups = eta_squared(cell, prim_v)
    cell_means = np.full(n_cells, np.nan)
    okc2 = np.isfinite(prim_v)
    cntc = np.bincount(cell[okc2], minlength=n_cells)
    sumc = np.bincount(cell[okc2], weights=prim_v[okc2], minlength=n_cells)
    have = cntc > 0
    cell_means[have] = sumc[have] / cntc[have]
    by_cell = {
        'n_cells': n_cells,
        'eta2_cell_block_level': eta_cell_blk,
        'cell_mean_sd': float(np.nanstd(cell_means, ddof=1)),
        'cell_mean_p25': float(np.nanpercentile(cell_means, 25)),
        'cell_mean_p50': float(np.nanpercentile(cell_means, 50)),
        'cell_mean_p75': float(np.nanpercentile(cell_means, 75)),
        'cell_mean_min': float(np.nanmin(cell_means)),
        'cell_mean_max': float(np.nanmax(cell_means)),
    }
    # block_id 20 quantile bins (design-era proxy, no study assumption)
    bins = 20
    edges = np.percentile(blk, np.linspace(0, 100, bins + 1))
    edges[-1] += 1
    bid_bin = np.digitize(blk, edges[1:-1])
    eta_bin, n_bins = eta_squared(bid_bin, prim_v)
    bin_stats = []
    for bi in range(bins):
        sel = (bid_bin == bi) & np.isfinite(prim_v)
        if sel.sum() >= 100:
            bin_stats.append({'bin': bi,
                              'block_id_lo': int(blk[bid_bin == bi].min()),
                              'block_id_hi': int(blk[bid_bin == bi].max()),
                              'n': int(sel.sum()),
                              'mean': float(prim_v[sel].mean()),
                              'sd': float(prim_v[sel].std(ddof=1))})
    # study proxy stats (v1.4 blocks)
    cell_names_list = v14['cell_names']
    study_table = []
    for si, s in enumerate(studies):
        sel = (codes == si) & np.isfinite(prim_v)
        if sel.sum() < 50:
            continue
        sizes = sizes_map.get(s, {})
        kk = []
        ff = []
        for (nr, nc) in sizes.get('sizes', []):
            kk.append((nr - 1) * (nc - 1))
            ff.append(((nr - 1) * (nc - 1)) / float(nr * nc))
        n_cells_v14 = int(np.unique(cell[sel]).size)
        s1_cells = sizes.get('n_cell_lines')
        s1_blocks = sizes.get('n_blocks')
        study_table.append({
            'study': s, 'n_blocks': int(sel.sum()),
            'mean': float(prim_v[sel].mean()),
            'sd': float(prim_v[sel].std(ddof=1)),
            'p50': float(np.median(prim_v[sel])),
            'matrix': sizes.get('matrix'),
            'k_real_doses_mean': float(np.mean(kk)) if kk else None,
            'f_zero_padding_mean': float(np.mean(ff)) if ff else None,
            'inv_sqrt_k_mean': float(np.mean([1.0 / math.sqrt(x) for x in kk])) if kk else None,
            'n_cells_v14_in_window': n_cells_v14,
            's1_n_cell_lines': s1_cells,
            's1_n_blocks': s1_blocks,
            'cell_count_matches_s1': bool(s1_cells is not None and n_cells_v14 == s1_cells),
            'block_coverage_vs_s1': (float(sel.sum()) / s1_blocks) if s1_blocks else None,
            'window_quality': ('validated' if (s1_cells is not None and n_cells_v14 == s1_cells)
                               else 'mixed_window_excluded_from_design_test'),
            'v15_sample_combo_rows': (v15['studies'].get(s) or {}).get('sample_combo_rows'),
            'v15_sample_bliss_mean': (v15['studies'].get(s) or {}).get('synergy_bliss_mean'),
            'v15_sample_bliss_sd': (v15['studies'].get(s) or {}).get('synergy_bliss_sd'),
        })
    eta_study_all, n_study_groups_all = eta_squared(codes, prim_v)
    asg = codes >= 0
    eta_study, n_study_groups = eta_squared(codes[asg], prim_v[asg])
    # blocks that fall in no sampled study window (sample-derived windows truncate true ranges)
    unas = (~asg) & np.isfinite(prim_v)
    unassigned_stats = {
        'n_blocks': int(unas.sum()),
        'mean': float(prim_v[unas].mean()) if unas.any() else None,
        'sd': float(prim_v[unas].std(ddof=1)) if int(unas.sum()) > 1 else None,
        'p50': float(np.median(prim_v[unas])) if unas.any() else None,
        'block_id_min': int(blk[unas].min()) if unas.any() else None,
        'block_id_max': int(blk[unas].max()) if unas.any() else None,
        'caveat': ('study windows are min/max block_id of each study in the 4.22% v1.5 byte '
                   'sample; they are lower bounds on the true study ranges, so a v1.4 block can '
                   'be left unassigned or be near a window boundary. The study labels are a '
                   'proxy, not a v1.4 study column (v1.4 has none).'),
    }
    # correlation of per-study sd with the two competing design predictions
    def col_corr(key, target='sd', only_validated=True):
        xs, ys = [], []
        for rec in study_table:
            if only_validated and rec.get('window_quality') != 'validated':
                continue
            if rec.get(key) is not None:
                xs.append(rec[key])
                ys.append(rec[target])
        if len(xs) < 4:
            return {'n_studies': len(xs)}
        return {'n_studies': len(xs), 'pearson': pearson(xs, ys), 'spearman': spearman_fast(xs, ys)}
    # eta^2 using only study windows whose v1.4 cell-line count equals the S1 count
    validated_studies = [rec['study'] for rec in study_table
                         if rec.get('window_quality') == 'validated']
    val_codes = [studies.index(s) for s in validated_studies]
    val_mask = np.isin(codes, val_codes) & np.isfinite(prim_v)
    eta_valid, n_valid_groups = eta_squared(codes[val_mask], prim_v[val_mask])
    matrix_test = {
        'prediction_A_zero_padding_attenuation': col_corr('f_zero_padding_mean'),
        'prediction_B_averaging_over_real_doses': col_corr('inv_sqrt_k_mean'),
        'per_study_mean_vs_f_zero_padding': col_corr('f_zero_padding_mean', 'mean'),
        'window_quality_filter': ('only study windows whose v1.4 cell-line count equals the '
                                  'paper S1 cell-line count are used (mixed windows excluded)'),
        'caveat': ('matrix sizes are paper-reported (S1); the actual SynergyFinder input '
                   'convention per study is not verifiable from the summary table'),
    }
    stability = {
        'by_cell': by_cell,
        'by_block_id_bins': {'n_bins': bins, 'eta2_block_id_bin': eta_bin, 'bins': bin_stats},
        'study_proxy': {
            'n_studies_windows': len(studies),
            'ambiguous_study_windows': prox['ambiguous_study_windows'],
            'assigned_blocks': prox['assigned_blocks'],
            'n_blocks': prox['n_blocks'],
            'assigned_frac': prox['assigned_blocks'] / prox['n_blocks'],
            'overlapping_blocks': prox['overlapping_blocks'],
            'eta2_study_proxy': eta_study,
            'eta2_study_proxy_including_unassigned': eta_study_all,
            'eta2_validated_studies_only': eta_valid,
            'n_validated_study_groups': n_valid_groups,
            'validated_studies': validated_studies,
            'n_study_groups': n_study_groups,
            'n_study_groups_including_unassigned': n_study_groups_all,
            'unassigned_blocks': unassigned_stats,
            'study_table': study_table,
        },
        'matrix_size_test': matrix_test,
    }

    print('[10/12] Jaaks ΔEMAX scale reference ...', flush=True)
    jaaks = {}
    for tag, path in (('original', JAAKS_ORIG), ('validation', JAAKS_VAL)):
        d = pd.read_csv(path, usecols=['SYNERGY_DELTA_EMAX', 'SYNERGY_EXP_EMAX',
                                       'SYNERGY_OBS_EMAX'], low_memory=False)
        delta = pd.to_numeric(d['SYNERGY_DELTA_EMAX'], errors='coerce').to_numpy(float)
        exp = pd.to_numeric(d['SYNERGY_EXP_EMAX'], errors='coerce').to_numpy(float)
        obs = pd.to_numeric(d['SYNERGY_OBS_EMAX'], errors='coerce').to_numpy(float)
        ok = np.isfinite(delta)
        resid = np.abs(delta - (exp - obs))
        jaaks[tag] = {
            'n_rows': int(len(delta)),
            'n_finite': int(ok.sum()),
            'mean': float(delta[ok].mean()),
            'sd': float(delta[ok].std(ddof=1)),
            'min': float(delta[ok].min()), 'max': float(delta[ok].max()),
            'p1': float(np.percentile(delta[ok], 1)),
            'p25': float(np.percentile(delta[ok], 25)),
            'p50': float(np.percentile(delta[ok], 50)),
            'p75': float(np.percentile(delta[ok], 75)),
            'p99': float(np.percentile(delta[ok], 99)),
            'frac_ge_threshold_0.2': float(np.count_nonzero(delta[ok] >= 0.2) / ok.sum()),
            'frac_le_minus_threshold': float(np.count_nonzero(delta[ok] <= -0.2) / ok.sum()),
            'identity_max_abs_resid_delta_vs_exp_minus_obs': float(np.nanmax(resid)),
            'identity_frac_within_1e-6': float(np.count_nonzero(resid <= 1e-6) / ok.sum()),
        }
    jaaks['definition'] = ('Jaaks 2022 Methods: dEmax = Bliss Emax - combination Emax, on the '
                           'viability scale (threshold 0.2 = 20% shift); Emax reported at the '
                           'highest tested concentration of the fitted curves.')
    prim_blk = blk_stats[PRIMARY]
    ratios = {}
    for tag in ('original', 'validation'):
        s = jaaks[tag]['sd']
        if s and prim_blk['sd']:
            ratios[tag] = {
                'jawks_sd_x100': s * 100.0,
                'drugcomb_primary_sd': prim_blk['sd'],
                'ratio_drugcomb_over_jaaks_x100': prim_blk['sd'] / (s * 100.0),
                'ratio_within_1_3_3': bool(SCALE_RATIO_LO <= prim_blk['sd'] / (s * 100.0) <= SCALE_RATIO_HI),
            }
    jaaks['scale_comparison_vs_drugcomb_bliss_block'] = ratios

    print('[11/12] comparability quotes ...', flush=True)
    nar21 = clean_xml_text(NAR2021_XML)
    nar19 = clean_xml_text(NAR2019_XML)
    maly = clean_xml_text(MALY2019_XML)
    jaaks_txt = clean_xml_text(JAAKS_XML)
    syn_txt = ' '.join(open(p, encoding='utf-8', errors='replace').read()
                       for p in SYN_SRC if p.endswith('.R'))
    syn_txt = ' '.join(syn_txt.replace('#', ' ').split())
    quotes = {
        'jaaks_delta_emax_definition': {
            'source': 'Jaaks 2022 Nature 603:594, Methods "Classifying synergy" (PMID 35197630, PMC8891012)',
            'quote': 'Shifts in potency (∆IC 50 ) and in efficacy (∆ E max ) were calculated as the difference between the observed combination response and expected Bliss',
            'verified': None},
        'jaaks_bliss_expected_product': {
            'source': 'Jaaks 2022 Methods',
            'quote': 'every point on the Bliss dose response curve is defined as the product between the anchor viability and the corresponding point on the library dose response curve',
            'verified': None},
        'jaaks_emax_at_highest_conc': {
            'source': 'Jaaks 2022 Methods',
            'quote': 'E max is reported at the highest tested concentration for the drug',
            'verified': None},
        'jaaks_averaging_replicates': {
            'source': 'Jaaks 2022 Methods',
            'quote': 'Drug responses were averaged across technical and biological replicates',
            'verified': None},
        'nar2021_four_models': {
            'source': 'NAR 2021 gkab438 (PMC8218202), "Algorithms for assessing sensitivity and synergy"',
            'quote': 'For evaluating the drug synergy, we implement four major mathematical models including Bliss, Loewe, HSA and ZIP',
            'verified': None},
        'nar2021_bliss_independence': {
            'source': 'NAR 2021 gkab438',
            'quote': 'the Bliss model assumes probabilistic independence when drugs are non-interactive while the Loewe model assumes that the efficacy of non-synergistic drug combinations is identical to that of a drug combined with itself',
            'verified': None},
        'nar2021_zip_combines': {
            'source': 'NAR 2021 gkab438',
            'quote': 'The ZIP model, on the other hand, can be considered as an Ensembl model as it combines the assumptions of Bliss and Loewe',
            'verified': None},
        'nar2021_sign_convention': {
            'source': 'NAR 2021 gkab438',
            'quote': 'Drug combinations with synergy scores of zero are considered additive, while a positive synergy score suggests synergy, and a negative score suggests antagonism',
            'verified': None},
        'nar2021_summary_table_block': {
            'source': 'NAR 2019 gkz337 (PMC6602441), "Database content"',
            'quote': 'a unique identifier, termed block id, is needed to differentiate the same drug combination—cell line pair that has been repeated in multiple experiments',
            'verified': None},
        'nar2021_qc_range': {
            'source': 'NAR 2021 gkab438, "Data curation"',
            'quote': 'less than −200% or larger than 200%, were marked as poor-quality data points',
            'verified': None},
        'malyutina_css_scale': {
            'source': 'Malyutina 2019 PLoS Comput Biol 15:e1006752 (PMC6544320)',
            'quote': 'The CSS for the foreground drug is defined as a percentage which varies between 0 and 100',
            'verified': None},
        'malyutina_same_unit': {
            'source': 'Malyutina 2019',
            'quote': 'utilize the same unit as the percentage of inhibition of cell viability. Therefore, the synergy score can be interpreted as the extra percentage inhibition effect beyond the expectation',
            'verified': None},
        'synergyfinder_bliss_reference': {
            'source': 'SynergyFinder R implementation %s@%s R/Bliss.R' % (SYN_REPO, SYN_COMMIT[:12]),
            'quote': 'drug1.response[i] + drug2.response[j] - drug1.response[i] * drug2.response[j]/100',
            'verified': None},
        'synergyfinder_average_title': {
            'source': 'SynergyFinder R implementation %s@%s R/Plot_synergy.R' % (SYN_REPO, SYN_COMMIT[:12]),
            'quote': 'the mean value of all scores in the selected ranges',
            'verified': None},
    }
    # normalise the exact-spacing variants for verification
    quote_sources = {
        'jaaks': jaaks_txt, 'nar2021': nar21, 'nar2019': nar19, 'malyutina': maly,
        'synergyfinder': syn_txt,
    }
    qmap = {
        'jaaks_delta_emax_definition': 'jaaks', 'jaaks_bliss_expected_product': 'jaaks',
        'jaaks_emax_at_highest_conc': 'jaaks', 'jaaks_averaging_replicates': 'jaaks',
        'nar2021_four_models': 'nar2021', 'nar2021_bliss_independence': 'nar2021',
        'nar2021_zip_combines': 'nar2021', 'nar2021_sign_convention': 'nar2021',
        'nar2021_summary_table_block': 'nar2019', 'nar2021_qc_range': 'nar2021',
        'malyutina_css_scale': 'malyutina', 'malyutina_same_unit': 'malyutina',
        'synergyfinder_bliss_reference': 'synergyfinder',
        'synergyfinder_average_title': 'synergyfinder',
    }
    for k, v in quotes.items():
        v['verified'] = bool(verify_quote(quote_sources[qmap[k]], v['quote']))
    # literature-based construct facts recorded for the C1-C5 argument
    comparability = {
        'quotes': quotes,
        'all_quotes_verified': bool(all(v['verified'] for v in quotes.values())),
        'C1_same_null_model': {
            'pass': bool(PRIMARY == 'synergy_bliss'),
            'argument': ('dEmax uses Bliss independence as expected response (Jaaks quote above); '
                         'among the six DrugComb candidates only synergy_bliss is constructed from '
                         'the Bliss independence reference (NAR2021 + SynergyFinder R/Bliss.R).'),
        },
        'C2_same_orientation': {
            'pass': True,
            'argument': ('dEmax = Bliss Emax - combination Emax (positive = combination more effective); '
                         'DrugComb: positive synergy score suggests synergy (NAR2021). Same sign convention.'),
        },
        'C3_convertible_scale': {
            'pass': True,
            'argument': ('dEmax is on the viability fraction scale (threshold 0.2 = 20% viability shift); '
                         'DrugComb synergy scores are in percentage-inhibition points (Malyutina 2019); '
                         'x100 converts dEmax to the DrugComb scale.'),
        },
        'C4_documented_differences': [
            'the summary synergy score is a dose-matrix summary (mean over the matrix / landscape), '
            'while dEmax is a fitted efficacy contrast between observed and expected response at the '
            'highest tested concentration: not the same statistic (aggregation/potency content differs)',
            'Jaaks screen is an anchored 2x7 design; DrugComb blocks pool studies with different '
            'dose-matrix designs (2x2 ... 10x10) and v1.4 carries no study/design column',
            'Jaaks uses fitted curve parameters (Emax) and replicate nesting; DrugComb uses '
            'SynergyFinder matrix scores and 93.2% of curated data points have no replicates (NAR2021)',
            'DrugComb summary block = one experiment/dose matrix; dEmax is one formula per '
            '(anchor concentration, library, cell line) tuple',
        ],
        'C5_scale_consistency': {
            'result': ratios,
            'flag': bool(any(not r.get('ratio_within_1_3_3', True) for r in ratios.values())),
        },
        'equivalence_not_claimable': ('no entity-level response pairing exists between DrugComb and the '
                                      'project Jaaks table (cells 18, drugs 40, unit keys 241 overlap; '
                                      'different designs), so ONLY construct/null-model/sign/scale '
                                      'comparability is argued; no numerical equivalence claim.'),
    }

    print('[12/12] MDE80 + judgment ...', flush=True)
    y_all = aggs[PRIMARY]['mean']
    mde = {}
    for rtag, target in (('0.20', ('0.20', B_MDE)), ('0.30', ('0.30', B_MDE_SENS)), ('0.40', ('0.40', B_MDE_SENS))):
        mask = bu[target[0]]['mask'] & np.isfinite(y_all)
        y = y_all[mask]
        pr = unit_pair[mask]
        ce = unit_cell[mask]
        # compact cluster codes
        upairs, pr2 = np.unique(pr, return_inverse=True)
        ucells, ce2 = np.unique(ce, return_inverse=True)
        seed_r = SEED + int(round(float(rtag) * 100))
        res = bootstrap_mde(y, pr2.astype(np.int64), ce2.astype(np.int64),
                            int(upairs.size), int(ucells.size), target[1], seed_r)
        res.update({'n_units': int(y.size), 'n_pairs': int(upairs.size),
                    'n_cells': int(ucells.size), 'n_drugs_holdout': hold_sets[target[0]]['k_holdout']})
        mde[rtag] = res
    # power diagnostics at the primary design
    mde_primary = mde['0.20']
    se_b = mde_primary['B_two_way_clustered']['se']
    mask20 = bu['0.20']['mask'] & np.isfinite(y_all)
    y20 = y_all[mask20]
    pr20 = np.unique(unit_pair[mask20], return_inverse=True)[1].astype(np.int64)
    n_pairs20 = int(pr20.max()) + 1
    mde_primary['diagnostic_decomposition'] = mde_diagnostics(
        y20, pr20, n_pairs20, B_MDE, SEED + 11)
    pc = power_check(y20, pr20, n_pairs20, se_b,
                     targets=(0.03, (mde_primary['B_two_way_clustered']['mde80']
                                     if mde_primary['B_two_way_clustered']['mde80'] else 0.05),
                              0.05, 0.10, 0.1183), reps=N_POWER, seed=SEED + 7)
    mde_primary['power_check'] = pc
    mde_primary['delta_min'] = DELTA_MIN
    mde_primary['gate_mde80_two_way_le_delta_min'] = bool(
        mde_primary['B_two_way_clustered']['mde80'] is not None
        and mde_primary['B_two_way_clustered']['mde80'] <= DELTA_MIN)
    mde['0.30']['gate_mde80_two_way_le_delta_min'] = bool(
        mde['0.30']['B_two_way_clustered']['mde80'] is not None
        and mde['0.30']['B_two_way_clustered']['mde80'] <= DELTA_MIN)
    mde['0.40']['gate_mde80_two_way_le_delta_min'] = bool(
        mde['0.40']['B_two_way_clustered']['mde80'] is not None
        and mde['0.40']['B_two_way_clustered']['mde80'] <= DELTA_MIN)

    # ------------------------------------------------------------ judgment
    conditions = []
    failures = []
    if not primary_usable:
        failures.append('endpoint_saturated' if saturation[PRIMARY]['saturated']
                        else ('range_violation' if saturation[PRIMARY]['range_violation']
                              else 'endpoint_incomplete'))
    if not primary_agg_ok:
        failures.append('aggregation_unstable')
    c_ok = bool(comparability['C1_same_null_model']['pass']
                and comparability['C2_same_orientation']['pass']
                and comparability['C3_convertible_scale']['pass']
                and comparability['all_quotes_verified'])
    if not c_ok:
        failures.append('construct_mismatch')
    mde_gate_020 = mde['0.20']['gate_mde80_two_way_le_delta_min']
    mde_path = None
    if not mde_gate_020:
        if mde['0.40']['gate_mde80_two_way_le_delta_min']:
            mde_path = 'r=0.40 redesign (pre-registered section 12.3)'
            conditions.append('stage-2 primary design must use the pre-registered r=0.40 split; '
                              'r=0.20 is sensitivity only (power, not a result-driven switch)')
        else:
            failures.append('evaluation_cannot_distinguish')
    eta2_study = stability['study_proxy']['eta2_study_proxy']
    eta2_study_all = stability['study_proxy']['eta2_study_proxy_including_unassigned']
    eta2_candidates = [x for x in (eta2_study, eta2_study_all) if x is not None]
    eta2_flag = max(eta2_candidates) if eta2_candidates else None
    if eta2_flag is not None and eta2_flag >= TH_ETA2_STUDY:
        conditions.append('endpoint shows strong study/design-proxy heterogeneity '
                          '(eta^2(study proxy, assigned)=%s; including unassigned=%s; flag threshold %.2f): '
                          'blocks come from heterogeneous dose-matrix designs (2x2 ... 10x10) and '
                          'v1.4 has no study/design column, so this is an unadjustable confound that '
                          'must be disclosed and handled in stage 2 (e.g. study/segment stratified '
                          'sensitivity)' % (q(eta2_study), q(eta2_study_all), TH_ETA2_STUDY))
    if comparability['C5_scale_consistency']['flag']:
        conditions.append('C5 scale-divergence flag raised (see comparability C5): explain in stage 2')
    verdict = 'endpoint_usable' if not failures else 'endpoint_not_usable'
    primary_ok_block = bool(saturation[PRIMARY]['block']['metric_usable'])
    primary_ok_unit = bool(saturation[PRIMARY]['unit']['metric_usable'])
    mde_ops = {
        'iid_analytic_reference_only': mde['0.20']['iid_analytic']['mde80'],
        'permutation_fixed_y': mde['0.20']['diagnostic_decomposition']['permutation_fixed_y']['mde80'],
        'pair_level_bootstrap': mde['0.20']['diagnostic_decomposition']['pair_level_bootstrap']['mde80'],
        'two_way_cluster_bootstrap_GATE': mde['0.20']['B_two_way_clustered']['mde80'],
        'pair_cluster_bootstrap': mde['0.20']['A_pair_clustered']['mde80'],
    }
    power_at_headline = (mde['0.20'].get('power_check', {}).get('targets', {})
                         .get('0.1183', {}).get('reject_rate'))
    reopen = []
    if not mde_gate_020:
        reopen.append('if the Lead amends delta_min in the stage-2 protocol with an explicit '
                      'justification (e.g. delta_min = the frozen headline magnitude 0.1183 '
                      'or half of it 0.059): under this design MDE80(two-way)=%.3f, so a '
                      'delta_min >= 0.115 would pass; this is a protocol amendment decision, '
                      'not an auditor decision' % (mde['0.20']['B_two_way_clustered']['mde80'] or float('nan')))
        reopen.append('increase the number of independent drug pairs/cells in the both-unseen '
                      'design; r=0.40 gives MDE80(two-way)=%.3f, still above 0.03'
                      % (mde['0.40']['B_two_way_clustered']['mde80'] or float('nan')))
        reopen.append('a raw dose-level refit (2,008,117,325 B) would change the endpoint '
                      'construct but not the evaluation-unit count; its power gain is unknown '
                      'and requires a separate frozen protocol + download budget approval')
    judgment = {
        'verdict': verdict,
        'verdict_interpretation': ('failure is power/design (evaluation_cannot_distinguish) at the '
                                   'pre-registered delta_min, NOT endpoint saturation and NOT '
                                   'construct mismatch: the primary endpoint passes the saturation, '
                                   'aggregation and comparability gates'),
        'primary_endpoint': 'synergy_bliss',
        'aggregation_rule': ('arithmetic mean of block-level synergy_bliss within '
                             '(cell_line_name normalized, unordered normalized drug pair); '
                             'blocks with non-missing value, at least 1 block'),
        'primary_metric_usable_block_level': primary_ok_block,
        'primary_metric_usable_unit_level': primary_ok_unit,
        'aggregation_robustness_pass': primary_agg_ok,
        'comparability_argument_holds': c_ok,
        'mde80_two_way_r020': mde['0.20']['B_two_way_clustered']['mde80'],
        'mde80_pair_r020': mde['0.20']['A_pair_clustered']['mde80'],
        'mde80_operationalizations': mde_ops,
        'power_at_frozen_headline_0.1183_two_way': power_at_headline,
        'power_check_note': ('empirical reject rate of the one-sided rho>1.96*SE(two-way) test at the '
                             'given effect, simulated on the fixed evaluation units; it validates the '
                             'normal MDE approximation and is not an effect estimate'),
        'delta_min': DELTA_MIN,
        'mde_gate_pass_r020': mde_gate_020,
        'mde_upgrade_path': mde_path,
        'reopen_conditions_for_stage_2': reopen,
        'failure_categories': failures,
        'conditions': conditions,
        'no_metric_switch_note': ('PROTOCOL_PB section 12.2: switching to synergy_zip/hsa/loewe/S/css '
                                  'because the primary fails is prohibited (construct-inferior for '
                                  'dEmax comparability) and would be recorded as '
                                  'endpoint_not_usable + metric_switch_prohibited.'),
    }

    # ------------------------------------------------------------ assemble output
    print('    assembling outputs ...', flush=True)
    endpoint_times = {'inputs_sha256': q(t_inputs - t0), 'v14_read': q(t_v14 - t_inputs),
                      'v15_sample': q(t_v15 - t_v14), 'total': q(time.time() - t0)}
    out = {
        'protocol': {'path_rel': os.path.relpath(PROTOCOL, ROOT).replace('\\', '/'),
                     'bytes': os.path.getsize(PROTOCOL), 'sha256': sha256_file(PROTOCOL)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'bytes': os.path.getsize(SCRIPT), 'sha256': sha256_file(SCRIPT)},
        'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                        'pandas': pd.__version__, 'platform': platform.platform()},
        'seeds': {'master': SEED, 'bootstrap_B': B_MDE, 'bootstrap_B_sensitivity': B_MDE_SENS,
                  'power_reps': N_POWER, 'z_mde80': Z_MDE80, 'alpha_z': ALPHA_Z},
        'inputs': inputs,
        'structure': structure,
        'saturation': saturation,
        'aggregation_robustness': agg_rob,
        'semantic_checks': sem,
        'redundancy': redundancy,
        'reliability': reliability,
        'stability': stability,
        'v15_sample': {'chunks': v15['chunks'], 'rows': v15['rows'],
                       'mono_rows': v15['mono_rows'], 'combo_rows': v15['combo_rows'],
                       'n_studies': len(v15['studies']), 'studies': v15['studies'],
                       'synergy_bliss_all': v15['synergy_bliss_all']},
        'jaaks_scale_reference': jaaks,
        'comparability': comparability,
        'mde': mde,
        'judgment': judgment,
        'block_level_stats': blk_stats,
        'unit_level_stats': unit_stats,
        'aux_column_stats': aux_stats,
        'response_value_use_attestation': {
            'identity_or_annotation_model_fitted': False,
            'effect_estimated': False,
            'training_or_feature_selection_on_responses': False,
            'response_columns_used_only_for': ['distribution/saturation', 'semantic column checks',
                                               'reliability', 'measurement-regime description',
                                               'MDE variance estimation'],
        },
    }
    out = qd(out)
    write_json(out, OUT_JSON)

    # ------------------------------------------------------------ audit CSV
    rows = []
    for m in METRICS:
        b = blk_stats[m]
        u = unit_stats[m]
        s = saturation[m]
        a = agg_rob[m]
        rb = rho_unit.get('%s~%s' % (PRIMARY, m)) or rho_unit.get('%s~%s' % (m, PRIMARY))
        rows.append({
            'metric': m,
            'role': 'PRIMARY' if m == PRIMARY else 'candidate',
            'n_blocks': b['n'],
            'n_missing_blocks': b['n_missing'],
            'frac_missing_blocks': q(b['n_missing'] / n_blocks),
            'block_mean': q(b['mean']), 'block_sd': q(b['sd']),
            'block_min': q(b['min']), 'block_p1': q(b['p1']), 'block_p25': q(b['p25']),
            'block_p50': q(b['p50']), 'block_p75': q(b['p75']), 'block_p99': q(b['p99']),
            'block_max': q(b['max']),
            'block_atom_zero_frac': q(b['atom_zero_frac']),
            'block_atom_min_frac': q(b['atom_min_frac']),
            'block_atom_max_frac': q(b['atom_max_frac']),
            'block_bound_atom_max_frac': q(b['bound_atom_max_frac']),
            'block_frac_edge': q(b['frac_abs_ge_95']),
            'block_frac_beyond_documented': q(b['frac_beyond_documented']),
            'block_sd_over_scale': q(b['sd_over_scale']),
            'n_units': u['n'], 'unit_mean': q(u['mean']), 'unit_sd': q(u['sd']),
            'unit_p1': q(u['p1']), 'unit_p25': q(u['p25']), 'unit_p50': q(u['p50']),
            'unit_p75': q(u['p75']), 'unit_p99': q(u['p99']),
            'unit_frac_edge': q(u['frac_abs_ge_95']),
            'unit_frac_beyond_documented': q(u['frac_beyond_documented']),
            'saturated_block': s['block']['saturated'], 'saturated_unit': s['unit']['saturated'],
            'range_violation': s['range_violation'], 'incomplete': s['incomplete'],
            'saturation_flags_block': ';'.join(s['block']['flags']),
            'saturation_flags_unit': ';'.join(s['unit']['flags']),
            'metric_usable': s['metric_usable'],
            'A1_rho_mean_median': q(a['A1_rho_mean_median']), 'A2_rho_mean_firstblock': q(a['A2_rho_mean_firstblock_ge2']),
            'A3_rho_nblocks_mean': q(a['A3_rho_nblocks_mean']),
            'rho_unit_vs_primary': q(rb['rho'] if rb else None),
            'class_vs_primary': redundancy['classes_primary_vs_others'].get('%s_vs_%s' % (PRIMARY, m), {}).get('class', 'PRIMARY'),
            'icc1': q(reliability[m]['icc'].get('icc1')),
            'split_half_spearman_brown': q(reliability[m]['split_half'].get('spearman_brown')),
            'within_unit_sd_median': q(reliability[m]['icc'].get('within_unit_sd_median')),
        })
    cols = list(rows[0].keys())
    pd.DataFrame(rows, columns=cols).to_csv(OUT_CSV, index=False, encoding='utf-8')

    print('    judgment: %s' % verdict, flush=True)
    print('    primary usable=%s agg_ok=%s comparability=%s MDE80(two-way)=%s (delta_min %.2f)'
          % (primary_usable, primary_agg_ok, c_ok,
             mde['0.20']['B_two_way_clustered']['mde80'], DELTA_MIN), flush=True)
    print('    done in %.1fs' % (time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
