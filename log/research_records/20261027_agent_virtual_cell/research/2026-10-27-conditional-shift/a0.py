# a0.py - R193 A0 matched-quadruple qualification audit (Jaaks Original/Validation fitted tables).
# READ-ONLY. RESPONSE-BLIND: response columns are never read as values; only `isna` existence counts
# via a streaming csv pass that tests empty strings (no numeric conversion). No timestamps, sorted JSON
# keys. Deterministic. Regenerate: D:\anaconda\envs\maestro\python.exe research\2026-10-27-conditional-shift\a0.py
import csv, hashlib, json, math, time, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import openpyxl
import pandas as pd

BASE = Path(r'D:\MAESTRO')
OUT = BASE / 'research' / '2026-10-27-conditional-shift'
D = BASE / 'data' / 'external' / 'gdsc_combinations' / 'jaaks2022_figshare'
ORIG = D / 'Original screen_All tissues_fitted data.csv'
VAL = D / 'Validation screen_All tissues_fitted data.csv'
GLOSS = D / 'Glossary.xlsx'
PROTOCOL = OUT / 'PROTOCOL_A0.md'
SEED = 20261027          # declared for auditability; no random step is used in A0

META_COLS = ['BARCODE', 'COMBI_ID', 'Tissue', 'CELL_LINE_NAME', 'SIDM', 'COSMIC_ID',
             'ANCHOR_ID', 'ANCHOR_NAME', 'ANCHOR_TARGET', 'ANCHOR_PATHWAY', 'ANCHOR_DRUG_TYPE',
             'ANCHOR_Clin_Rel', 'ANCHOR_CONC',
             'LIBRARY_ID', 'LIBRARY_NAME', 'LIBRARY_TARGET', 'LIBRARY_PATHWAY',
             'LIBRARY_DRUG_TYPE', 'LIBRARY_Clin_Rel', 'LIBRARY_CONC']
ENDPOINTS = ['SYNERGY_DELTA_EMAX', 'SYNERGY_DELTA_AUC', 'SYNERGY_DELTA_fAUC', 'SYNERGY_DELTA_XMID']
PRIMARY_ENDPOINT = 'SYNERGY_DELTA_EMAX'
QUAD_CSV_CAP = 200000
t0 = time.perf_counter()

def sha256_file(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def sha256_text(s):
    return hashlib.sha256(s.encode('utf8')).hexdigest()

def nk(s):
    """NFKC -> casefold -> keep alnum only (frozen normalization)."""
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())

def canon(x):
    """Canonical numeric string for a design value (dose), or None if missing."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return format(v, '.10g')

def is_composite(*vals):
    return any(('|' in str(v)) for v in vals if v is not None)

def endpoint_availability(path, endpoints):
    """Stream the csv and only test empty-string existence for endpoint columns.
    No numeric conversion, no aggregation of values. Returns (n_rows, isna_counts, ok_flags)."""
    counts = [0] * len(endpoints)
    ok = []
    with Path(path).open('r', encoding='utf-8', errors='replace', newline='') as f:
        r = csv.reader(f)
        header = next(r)
        idx = [header.index(c) for c in endpoints]
        n = 0
        for row in r:
            n += 1
            good = True
            for j, i in enumerate(idx):
                if i >= len(row) or row[i] == '':
                    counts[j] += 1
                    good = False
            ok.append(good)
    return n, counts, np.asarray(ok, dtype=bool)

# ---------------------------------------------------------------- load metadata + endpoint existence
load = {}
for key, path in [('original', ORIG), ('validation', VAL)]:
    df = pd.read_csv(path, usecols=META_COLS, low_memory=False)
    n_rows, isna_counts, ok_flags = endpoint_availability(path, ENDPOINTS)
    assert n_rows == len(df), (key, n_rows, len(df))
    load[key] = {'path': path, 'df': df, 'n_rows': n_rows,
                 'isna_counts': dict(zip(ENDPOINTS, [int(x) for x in isna_counts])),
                 'endpoint_ok': ok_flags}

def prep(entry, endpoint_col=PRIMARY_ENDPOINT):
    df = entry['df'].copy()
    ep_ok = entry['endpoint_ok'] if endpoint_col == PRIMARY_ENDPOINT else None
    comp = []
    for i in range(len(df)):
        comp.append(is_composite(df['ANCHOR_ID'].iloc[i], df['LIBRARY_ID'].iloc[i],
                                 df['ANCHOR_CONC'].iloc[i]))
    comp = np.asarray(comp, dtype=bool)
    df['COMPOSITE'] = comp
    df['CELL'] = df['CELL_LINE_NAME'].map(lambda x: nk(x) if isinstance(x, str) else None)
    df['TISSUE'] = df['Tissue'].astype(str).str.strip()
    df['AID'] = df['ANCHOR_ID'].astype(str).str.strip()
    df['LID'] = df['LIBRARY_ID'].astype(str).str.strip()
    df['AC'] = df['ANCHOR_CONC'].map(canon)
    df['LC'] = df['LIBRARY_CONC'].map(canon)
    df['EPOK'] = ep_ok
    df['VALID'] = ((~df['COMPOSITE']) & df['CELL'].notna() & df['EPOK'] &
                   df['AID'].notna() & df['LID'].notna() & (df['AID'] != 'nan') & (df['LID'] != 'nan') &
                   df['AC'].notna() & df['LC'].notna())
    df['COND'] = list(zip(df['AID'], df['LID'], df['AC'], df['LC']))
    return df

orig = prep(load['original'])
val = prep(load['validation'])

# normalization collisions over the union of raw names (cells) - conservative exclusion rule (frozen)
raw_cells = set(orig['CELL_LINE_NAME'].dropna().unique().tolist()) | set(val['CELL_LINE_NAME'].dropna().unique().tolist())
coll_map = defaultdict(set)
for c in raw_cells:
    coll_map[nk(c)].add(c)
cell_collisions = {k: sorted(v) for k, v in coll_map.items() if len(v) > 1}
coll_cell_keys = set(cell_collisions)
# drug-name normalization collisions are reported for completeness (identity uses integer IDs)
drug_names = set(orig['ANCHOR_NAME'].dropna().unique()) | set(orig['LIBRARY_NAME'].dropna().unique()) | \
             set(val['ANCHOR_NAME'].dropna().unique()) | set(val['LIBRARY_NAME'].dropna().unique())
dnorm = defaultdict(set)
for dnm in drug_names:
    dnorm[nk(dnm)].add(dnm)
drug_name_collisions = {k: sorted(v) for k, v in dnorm.items() if len(v) > 1}
# validity also excludes normalized-collision cell keys (none expected in this dataset)
for df in (orig, val):
    df.loc[df['CELL'].isin(coll_cell_keys), 'VALID'] = False

# ---------------------------------------------------------------- group structures (metadata only)
def build(df):
    keys = defaultdict(set)                  # cell -> set(cond) with >=1 valid row
    bar = defaultdict(set)                   # (cell,cond) -> set(barcode)
    rows = Counter()                         # (cell,cond) -> valid rows
    cond_meta = {}                           # cond -> (aid,lid,ac,lc)
    cell_tissue = {}
    for cell, tissue, aid, lid, ac, lc, cond, barcode, validflag in zip(
            df['CELL'], df['TISSUE'], df['AID'], df['LID'], df['AC'], df['LC'], df['COND'],
            df['BARCODE'], df['VALID']):
        if not validflag:
            continue
        keys[cell].add(cond)
        rows[(cell, cond)] += 1
        bar[(cell, cond)].add(int(barcode))
        cond_meta.setdefault(cond, (aid, lid, ac, lc))
        cell_tissue.setdefault(cell, tissue)
    return {'keys': keys, 'bar': bar, 'rows': rows, 'cond_meta': cond_meta, 'cell_tissue': cell_tissue}

G1 = build(orig)
G2 = build(val)

# replicated keys across the two primary groups (endpoint-available in both)
rep_primary = {(c, k) for c in set(G1['keys']) & set(G2['keys']) for k in (G1['keys'][c] & G2['keys'][c])}
rep2 = defaultdict(set)
for c, k in rep_primary:
    rep2[c].add(k)

# barcode-split secondary group structure (Original only): deterministic half split per key
bc_A = defaultdict(set)
bc_B = defaultdict(set)
for (c, k), bars in G1['bar'].items():
    if len(bars) >= 2:
        bs = sorted(bars)
        h = (len(bs) + 1) // 2
        for b in bs[:h]:
            bc_A[c].add(k)
        for b in bs[h:]:
            bc_B[c].add(k)
bc_rep = {(c, k) for c in set(bc_A) for k in (bc_A[c] & bc_B[c])}
bc_rep2 = defaultdict(set)
for c, k in bc_rep:
    bc_rep2[c].add(k)

# condition-level metadata for all conditions seen
CTX = dict(G1['cond_meta'])
for k, v in G2['cond_meta'].items():
    CTX.setdefault(k, v)
CELL_TISSUE = dict(G1['cell_tissue'])
for k, v in G2['cell_tissue'].items():
    CELL_TISSUE.setdefault(k, v)

def pair_counts(sets_by_cell, name):
    """Counts of (c,c',p,q) from availability sets (cell -> set cond): p,q differ as unordered pairs."""
    cells = sorted(sets_by_cell)
    total = 0
    cell_pairs = 0
    for i in range(len(cells)):
        a = sets_by_cell[cells[i]]
        if len(a) < 2:
            continue
        for j in range(i + 1, len(cells)):
            b = sets_by_cell[cells[j]]
            if len(b) < 2:
                continue
            m = len(a & b)
            if m < 2:
                continue
            cell_pairs += 1
            inter = a & b
            dp = Counter((x[0], x[1]) for x in inter)
            same = sum(v * (v - 1) // 2 for v in dp.values())
            total += m * (m - 1) // 2 - same
    return {'quadruples': int(total), 'cell_pairs_with_ge2_shared': int(cell_pairs)}

def count_levels(a1, a2):
    """Replication-level counts R0..R4 over (c,c',p,q) whose four legs all exist in >=1 group.
    state(c,cond): 2 = available in both groups, 1 = one group only. level = #legs with state 2."""
    cells = sorted(set(a1) | set(a2))
    state = {}
    for c in cells:
        s = {k: 2 for k in (a1.get(c, set()) & a2.get(c, set()))}
        for k in (a1.get(c, set()) | a2.get(c, set())):
            s.setdefault(k, 1)
        state[c] = s
    levels = Counter()
    for i in range(len(cells)):
        ca = cells[i]
        sa = state[ca]
        if len(sa) < 2:
            continue
        for j in range(i + 1, len(cells)):
            cb = cells[j]
            sb = state[cb]
            if len(sb) < 2:
                continue
            common = sa.keys() & sb.keys()
            if len(common) < 2:
                continue
            cls = defaultdict(int)
            for k in common:
                cls[(sa[k], sb[k])] += 1
            classes = list(cls)
            for x in range(len(classes)):
                for y in range(x, len(classes)):
                    cx, cy = classes[x], classes[y]
                    n = cls[cx] * cls[cy] if x != y else cls[cx] * (cls[cx] - 1) // 2
                    if n == 0:
                        continue
                    lev = (cx[0] == 2) + (cx[1] == 2) + (cy[0] == 2) + (cy[1] == 2)
                    levels[lev] += n
            # subtract same-INTENDED-pair (same unordered drug id pair) pairs
            bydp = defaultdict(list)
            for k in common:
                bydp[tuple(sorted((k[0], k[1])))].append(k)
            for dps, ks in bydp.items():
                for x in range(len(ks)):
                    for y in range(x + 1, len(ks)):
                        kx, ky = ks[x], ks[y]
                        cx, cy = (sa[kx], sb[kx]), (sa[ky], sb[ky])
                        lev = (cx[0] == 2) + (cx[1] == 2) + (cy[0] == 2) + (cy[1] == 2)
                        levels[lev] -= 1
    return {str(k): int(v) for k, v in sorted(levels.items()) if v != 0}, sum(levels.values())

# ---------------------------------------------------------------- primary matched quadruples R4
def r4_stats(rep_map):
    """Combinatorial R4 counts, strata, coverage and participation for replicated keys."""
    cells = sorted(rep_map)
    strata = Counter()
    cell_deg = Counter(); cond_deg = Counter(); dp_deg = Counter(); anchor_deg = Counter(); library_deg = Counter()
    total = 0
    cell_pairs_used = 0
    conds_used = set(); dps_used = set(); anchors_used = set(); libraries_used = set()
    cells_used = set()
    for i in range(len(cells)):
        ca = cells[i]
        A = rep_map[ca]
        if len(A) < 2:
            continue
        for j in range(i + 1, len(cells)):
            cb = cells[j]
            Y = sorted(A & rep_map[cb])
            m = len(Y)
            if m < 2:
                continue
            bydp = defaultdict(list)
            for k in Y:
                bydp[tuple(sorted((k[0], k[1])))].append(k)
            same_dp = sum(len(v) * (len(v) - 1) // 2 for v in bydp.values())
            u = m * (m - 1) // 2 - same_dp
            if u <= 0:
                continue
            total += u
            cell_pairs_used += 1
            cells_used.add(ca); cells_used.add(cb)
            cell_deg[ca] += u; cell_deg[cb] += u
            # strata (combinatorial)
            by_anchor = defaultdict(list)
            by_lib = defaultdict(list)
            by_ctl = defaultdict(list)
            for k in Y:
                aid, lid, ac, lc = CTX[k]
                by_anchor[aid].append(k)
                by_lib[lid].append(k)
                by_ctl[(aid, ac, lc)].append(k)
                conds_used.add(k)
                dps_used.add(tuple(sorted((aid, lid))))
                anchors_used.add(aid); libraries_used.add(lid)
            same_anchor = sum(len(v) * (len(v) - 1) // 2 for v in by_anchor.values()) - same_dp
            same_library = sum(len(v) * (len(v) - 1) // 2 for v in by_lib.values()) - same_dp
            controlled = 0
            for key, ks in by_ctl.items():
                n = len(ks)
                lib_counter = Counter(CTX[k][1] for k in ks)
                same_lib = sum(v * (v - 1) // 2 for v in lib_counter.values())
                controlled += n * (n - 1) // 2 - same_lib
            strata['controlled_anchor'] += controlled
            strata['same_anchor_any_conc'] += same_anchor
            strata['same_library'] += same_library
            strata['disjoint_pairs'] += max(0, u - same_anchor - same_library)
            if CELL_TISSUE.get(ca) == CELL_TISSUE.get(cb):
                strata['same_tissue'] += u
            else:
                strata['cross_tissue'] += u
            # per-condition participation (units involving each condition)
            for k in Y:
                other = m - 1
                same = len(bydp[tuple(sorted((k[0], k[1])))]) - 1
                cond_deg[k] += other - same
                aid, lid, ac, lc = CTX[k]
                dp_deg[tuple(sorted((aid, lid)))] += other - same
                anchor_deg[aid] += other - same
                library_deg[lid] += other - same
    return {
        'quadruples': int(total), 'cell_pairs_used': int(cell_pairs_used),
        'cells_used': len(cells_used), 'conditions_used': len(conds_used),
        'directed_pairs_used': len(dps_used), 'anchors_used': len(anchors_used), 'libraries_used': len(libraries_used),
        'strata': dict(strata),
        'cells_used_set': cells_used, 'conditions_used_set': conds_used,
        'cell_degree': {c: int(v) for c, v in cell_deg.items()},
        'condition_degree_n': len(cond_deg),
        'directed_pair_degree': {f'{a}:{b}': int(v) for (a, b), v in dp_deg.items()},
        'anchor_degree': dict(anchor_deg), 'library_degree': dict(library_deg),
    }

R4 = r4_stats(rep2)
G1only = pair_counts(G1['keys'], 'G1')
G2only = pair_counts(G2['keys'], 'G2')
BC = r4_stats(bc_rep2)
levels_primary, sum_levels = count_levels(G1['keys'], G2['keys'])
levels_bc, sum_levels_bc = count_levels(bc_A, bc_B)

# matched replication subgraph (cell x condition bipartite graph restricted to R4 participants)
cells_used_set = R4['cells_used_set']
conds_used_set = R4['conditions_used_set']
graph_edges = sum(1 for c in cells_used_set if c in rep2 for k in rep2[c] if k in conds_used_set)
tissue_counts = Counter(CELL_TISSUE.get(c, '') for c in cells_used_set)

# ---------------------------------------------------------------- structure/overlap summaries
def keyset(df):
    ok = df[df['VALID']]
    return {
        'rows_total': int(len(df)), 'composite_rows': int(df['COMPOSITE'].sum()),
        'valid_rows': int(len(ok)),
        'cells': int(ok['CELL'].nunique()), 'directed_pairs': len({(a, l) for a, l in zip(ok['AID'], ok['LID'])}),
        'unordered_pairs': len({tuple(sorted((a, l))) for a, l in zip(ok['AID'], ok['LID'])}),
        'conditions': int(ok['COND'].nunique()),
        'barcodes': int(ok['BARCODE'].nunique()),
        'tissues': sorted(ok['TISSUE'].unique().tolist()),
        'conditions_per_cell': {x: int(ok.groupby('CELL')['COND'].nunique().agg(x)) for x in ['min', 'median', 'max']},
        'rows_per_key_hist': {str(k): int(v) for k, v in sorted(Counter(ok.groupby(['CELL', 'COND']).size().values).items())},
        'barcodes_per_key_hist': {str(k): int(v) for k, v in sorted(Counter(
            ok.groupby(['CELL', 'COND'])['BARCODE'].nunique().values).items())},
    }
S = {'original': keyset(orig), 'validation': keyset(val)}

# exclusion breakdown (raw -> composite -> identity/design -> endpoint -> valid)
def excl(df):
    comp = df['COMPOSITE']
    identity_bad = (~comp) & (df['CELL'].isna() | df['AID'].isin(['nan', 'None']) | df['LID'].isin(['nan', 'None']))
    design_bad = (~comp) & (~identity_bad) & (df['AC'].isna() | df['LC'].isna())
    ep_bad = (~comp) & (~identity_bad) & (~design_bad) & (~df['EPOK'])
    valid = df['VALID']
    return {'rows_total': int(len(df)), 'composite_pipe': int(comp.sum()),
            'identity_missing': int(identity_bad.sum()), 'design_missing': int(design_bad.sum()),
            'endpoint_empty': int(ep_bad.sum()), 'valid': int(valid.sum())}
EXCL = {'original': excl(orig), 'validation': excl(val)}

# glossary (published data dictionary; text metadata only)
wb = openpyxl.load_workbook(GLOSS, read_only=True, data_only=True)
ws = wb.worksheets[0]
gloss_rows = [[('' if v is None else str(v)) for v in row] for row in ws.iter_rows(values_only=True)]
wb.close()
gloss_terms = [r[0] for r in gloss_rows[1:] if r and r[0]]

# Original/Validation overlap at metadata levels
cells_o = {c for c, ks in G1['keys'].items() if ks}
cells_v = {c for c, ks in G2['keys'].items() if ks}
cond_o = {(c, k) for c in cells_o for k in G1['keys'][c]}
cond_v = {(c, k) for c in cells_v for k in G2['keys'][c]}
dp_o = {(k[0], k[1]) for c in cells_o for k in G1['keys'][c]}
dp_v = {(k[0], k[1]) for c in cells_v for k in G2['keys'][c]}
overlap = {
    'cells': {'original': len(cells_o), 'validation': len(cells_v), 'common': len(cells_o & cells_v)},
    'directed_pairs': {'original': len(dp_o), 'validation': len(dp_v), 'common': len(dp_o & dp_v)},
    'cell_condition_keys': {'original': len(cond_o), 'validation': len(cond_v), 'common': len(cond_o & cond_v)},
    'barcode_sets_disjoint': len(set(orig.loc[orig['VALID'], 'BARCODE']) & set(val.loc[val['VALID'], 'BARCODE'])) == 0,
    'barcode_ranges': {'original': [int(orig.loc[orig['VALID'], 'BARCODE'].min()), int(orig.loc[orig['VALID'], 'BARCODE'].max())],
                       'validation': [int(val.loc[val['VALID'], 'BARCODE'].min()), int(val.loc[val['VALID'], 'BARCODE'].max())]},
}
# dose-layout comparability between sources (design columns only)
dose_cmp = {
    'anchor_conc_levels': {'original': sorted({k[2] for c in G1['keys'] for k in G1['keys'][c]}, key=float),
                           'validation': sorted({k[2] for c in G2['keys'] for k in G2['keys'][c]}, key=float)},
    'library_conc_levels': {'original': sorted({k[3] for c in G1['keys'] for k in G1['keys'][c]}, key=float),
                            'validation': sorted({k[3] for c in G2['keys'] for k in G2['keys'][c]}, key=float)},
}
dose_cmp['anchor_conc_common'] = len(set(dose_cmp['anchor_conc_levels']['original']) & set(dose_cmp['anchor_conc_levels']['validation']))
dose_cmp['library_conc_common'] = len(set(dose_cmp['library_conc_levels']['original']) & set(dose_cmp['library_conc_levels']['validation']))
# per-key condition-tuple equality across the two sources (design-level dose match)
common_keys = cond_o & cond_v
dose_cmp['common_cell_condition_keys'] = len(common_keys)
dose_cmp['common_key_share_of_validation'] = round(len(common_keys) / len(cond_v), 6) if cond_v else None
# same directed pair with differing design columns -> layout inconsistency count
by_pair_design = defaultdict(set)
for c, k in common_keys:
    by_pair_design[(k[0], k[1])].add((k[2], k[3]))
inconsistent_pairs = {p: sorted(v) for p, v in by_pair_design.items() if len(v) > 1}
dose_cmp['pairs_with_multiple_common_design_tuples'] = len(inconsistent_pairs)

# ---------------------------------------------------------------- qualification gates (frozen)
gate = {
    'Q1_primary_common_quadruples_ge_500': R4['quadruples'] >= 500,
    'Q2_two_independent_groups': (overlap['cells']['common'] >= 2) and overlap['barcode_sets_disjoint'],
    'Q3_each_group_ge_500_quadruples': (G1only['quadruples'] >= 500) and (G2only['quadruples'] >= 500),
    'Q4_coverage_cells_ge_10_pairs_ge_10': (R4['cells_used'] >= 10) and (R4['directed_pairs_used'] >= 10),
    'Q5_primary_endpoint_available': (load['original']['isna_counts'][PRIMARY_ENDPOINT] == 0 and
                                      load['validation']['isna_counts'][PRIMARY_ENDPOINT] == 0),
}
qualified = all(gate.values())
judgment = 'matching_qualified' if qualified else 'matching_not_qualified'
required_spec = [] if qualified else [
    'need >=500 matched quadruples replicated across >=2 independent measurement groups',
    'need >=2 independent screens/boards with same drug pair + direction + anchor concentration + library dose layout',
    'need >=10 distinct cells and >=10 distinct directed pairs in replicated quadruples',
    'need SYNERGY_DELTA_EMAX available for all four keys in both groups',
]
# MDE note for the frozen threshold (documented, not used to change the threshold)
mde_note = {
    'threshold_units': 500,
    'iid_spearman_note': 'n=500 gives ~80% power (two-sided alpha=.05) for Spearman rho~=0.125 under iid; effective n is lower after clustering by cell/pair, so 500 is a floor, not a power guarantee (A1 must report clustered MDE)',
    'brier': 'BRIEF default 500 frozen; no post-hoc change',
}

# ---------------------------------------------------------------- outputs: CSVs
def cond_fields(k):
    aid, lid, ac, lc = CTX[k]
    return {'anchor_id': aid, 'library_id': lid, 'anchor_conc': ac, 'library_conc': lc}

cond_rows = []
for c, k in sorted(common_keys, key=lambda x: (x[0], x[1])):
    aid, lid, ac, lc = CTX[k]
    cond_rows.append({
        'cell': c, 'tissue': CELL_TISSUE.get(c, ''),
        'anchor_id': aid, 'library_id': lid, 'anchor_conc': ac, 'library_conc': lc,
        'original_rows': int(G1['rows'].get((c, k), 0)),
        'validation_rows': int(G2['rows'].get((c, k), 0)),
        'original_barcodes': len(G1['bar'].get((c, k), set())),
        'validation_barcodes': len(G2['bar'].get((c, k), set())),
    })
cond_csv = OUT / 'matched_conditions.csv'
with cond_csv.open('w', encoding='utf8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(cond_rows[0].keys()))
    w.writeheader(); w.writerows(cond_rows)

# quadruple CSV: canonical order, frozen cap rule (first QUAD_CSV_CAP rows lexicographically)
quad_csv = OUT / 'matched_quadruples.csv'
written = 0
cells_sorted = sorted(rep2)
with quad_csv.open('w', encoding='utf8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['cell_a', 'cell_b', 'tissue_a', 'tissue_b',
                'anchor_p', 'library_p', 'anchor_conc_p', 'library_conc_p',
                'anchor_q', 'library_q', 'anchor_conc_q', 'library_conc_q',
                'controlled_anchor', 'same_anchor_any_conc', 'same_library', 'disjoint_pairs', 'same_tissue'])
    stop = False
    for i in range(len(cells_sorted)):
        if stop:
            break
        ca = cells_sorted[i]
        A = rep2[ca]
        if len(A) < 2:
            continue
        for j in range(i + 1, len(cells_sorted)):
            cb = cells_sorted[j]
            Y = sorted(A & rep2[cb])
            if len(Y) < 2:
                continue
            for x in range(len(Y)):
                if stop:
                    break
                kp = Y[x]
                ap, lp, acp, lcp = CTX[kp]
                dpp = (kp[0], kp[1])
                for y in range(x + 1, len(Y)):
                    kq = Y[y]
                    if (kq[0], kq[1]) == dpp or tuple(sorted((kq[0], kq[1]))) == tuple(sorted(dpp)):
                        continue
                    aq, lq, acq, lcq = CTX[kq]
                    w.writerow([ca, cb, CELL_TISSUE.get(ca, ''), CELL_TISSUE.get(cb, ''),
                                ap, lp, acp, lcp, aq, lq, acq, lcq,
                                int(ap == aq and acp == acq and lcp == lcq and lp != lq),
                                int(ap == aq), int(lp == lq), int(ap != aq and lp != lq and lp != aq and ap != lq),
                                int(CELL_TISSUE.get(ca) == CELL_TISSUE.get(cb))])
                    written += 1
                    if written >= QUAD_CSV_CAP:
                        stop = True
                        break
if written == 0:
    quad_csv.write_text('', encoding='utf8')

# ---------------------------------------------------------------- a0.json
elapsed = time.perf_counter() - t0
a0 = {
    'task': 'R193-A0 matched-quadruple qualification audit',
    'protocol': {'path': str(PROTOCOL.relative_to(BASE)), 'sha256': sha256_file(PROTOCOL)},
    'script': {'path': 'research/2026-10-27-conditional-shift/a0.py', 'sha256': sha256_file(Path(__file__))},
    'inputs': {
        'original_fitted': {'path': str(ORIG.relative_to(BASE)), 'bytes': ORIG.stat().st_size, 'sha256': sha256_file(ORIG)},
        'validation_fitted': {'path': str(VAL.relative_to(BASE)), 'bytes': VAL.stat().st_size, 'sha256': sha256_file(VAL)},
        'glossary': {'path': str(GLOSS.relative_to(BASE)), 'bytes': GLOSS.stat().st_size, 'sha256': sha256_file(GLOSS)},
    },
    'method': {
        'response_values_read': False,
        'endpoint_access': 'streaming empty-string existence only (no numeric conversion/aggregation); matching is response-blind',
        'matching_uses': 'identity/direction/dose-layout/endpoint-availability/screen only',
        'deterministic': 'sorted JSON keys, no timestamps, no random draws (declared seed unused)',
        'python': '3.11.16', 'pandas': pd.__version__, 'numpy': np.__version__,
    },
    'structure': {
        'original': S['original'], 'validation': S['validation'],
        'exclusion_breakdown': EXCL,
        'filter_rules': {'composite_pipe_rows': 'excluded', 'missing_identity_or_design': 'excluded',
                         'normalized_cell_collisions': sorted(cell_collisions), 'endpoint_missing_rows': 'excluded'},
        'endpoint_availability_isna_counts': {'original': load['original']['isna_counts'],
                                              'validation': load['validation']['isna_counts']},
        'cell_name_collisions_over_union': cell_collisions,
        'drug_name_collisions_over_union': drug_name_collisions,
        'glossary_terms': gloss_terms,
        'glossary_term_count': len(gloss_terms),
    },
    'primary_endpoint': PRIMARY_ENDPOINT,
    'condition_definition': 'directed (ANCHOR_ID -> LIBRARY_ID, ANCHOR_CONC uM, LIBRARY_CONC highest uM)',
    'independent_groups': {
        'primary': {'G1': 'Original screen fitted table', 'G2': 'Validation screen fitted table',
                    'barcode_sets_disjoint': overlap['barcode_sets_disjoint']},
        'secondary_barcode_split': {'rule': 'per (cell,condition) key with >=2 distinct Original barcodes: sorted ascending, A=first ceil(n/2), B=rest',
                                    'replicated_keys': len(bc_rep)},
    },
    'overlap_original_validation': overlap,
    'dose_layout_comparability': dose_cmp,
    'quadruples': {
        'R4_common_primary': R4['quadruples'],
        'R3_half_matches': levels_primary.get('3', 0),
        'replication_level_counts_common': levels_primary,
        'G1_only_quadruples': G1only, 'G2_only_quadruples': G2only,
        'barcode_split_R4': BC['quadruples'],
        'barcode_split_levels': levels_bc,
        'csv': {'matched_conditions_rows': len(cond_rows), 'quadruples_csv_cap': QUAD_CSV_CAP,
                'quadruples_csv_rows_written': written,
                'note': 'if R4 > cap the CSV holds the lexicographically first cap rows (frozen rule); full count above; full list regenerable by a0.py enumeration'},
        'csv_sha256': {'matched_conditions.csv': sha256_file(cond_csv), 'matched_quadruples.csv': sha256_file(quad_csv)},
        'strata_R4': R4['strata'],
        'coverage_R4': {k: R4[k] for k in ['cells_used', 'conditions_used', 'directed_pairs_used', 'anchors_used', 'libraries_used', 'cell_pairs_used']},
        'matched_replication_graph': {
            'nodes_total': R4['cells_used'] + R4['conditions_used'],
            'node_cells': R4['cells_used'], 'node_conditions': R4['conditions_used'],
            'edges_cell_condition_keys': int(graph_edges),
            'loops_4_cycles': R4['quadruples'],
            'note': 'each matched quadruple is exactly a 4-cycle; trees cannot identify non-additivity',
        },
        'cells_used_tissue_counts': dict(tissue_counts),
        'cell_degree_summary': {
            'n_cells': len(R4['cell_degree']),
            'min': min(R4['cell_degree'].values()) if R4['cell_degree'] else 0,
            'median': float(np.median(list(R4['cell_degree'].values()))) if R4['cell_degree'] else 0,
            'max': max(R4['cell_degree'].values()) if R4['cell_degree'] else 0,
        },
        'directed_pair_degree_summary': {
            'n_pairs': len(R4['directed_pair_degree']),
            'min': min(R4['directed_pair_degree'].values()) if R4['directed_pair_degree'] else 0,
            'median': float(np.median(list(R4['directed_pair_degree'].values()))) if R4['directed_pair_degree'] else 0,
            'max': max(R4['directed_pair_degree'].values()) if R4['directed_pair_degree'] else 0,
        },
        'top_cells_by_degree': sorted(R4['cell_degree'].items(), key=lambda kv: (-kv[1], kv[0]))[:10],
        'top_directed_pairs_by_degree': sorted(R4['directed_pair_degree'].items(), key=lambda kv: (-kv[1], kv[0]))[:10],
        'top_anchors_by_degree': sorted(R4['anchor_degree'].items(), key=lambda kv: (-kv[1], kv[0]))[:10],
        'top_libraries_by_degree': sorted(R4['library_degree'].items(), key=lambda kv: (-kv[1], kv[0]))[:10],
    },
    'estimability_notes': {
        'minimal_loop': 'a matched quadruple is exactly a 4-cycle (loop) in the cell x condition bipartite graph; trees cannot identify non-additivity, 2x2 is the minimal loop',
        'single_agent_reference': 'single-agent fitted columns exist (ANCHOR_VIABILITY, LIBRARY_EMAX/XMID/AUC/fAUC) but their values are DENY in A0; H193b adjusted-Q needs them in A1',
        'batch_confounding': 'Original vs Validation are separate screens (disjoint barcodes); screen identity is confounded with measurement batch and cannot be separated from "independent group"',
        'dose_layout': 'only ANCHOR_CONC and LIBRARY_CONC(highest) are published in the fitted table; full library dose-point sets are not available, and no raw Validation layout file exists locally -> dose-layout equivalence verified only at the design-column level',
        'replicate_plates': 'Original has repeated barcode measurements for some (cell,condition) keys; fitted table has no plate date/batch, so barcode-level independence is weaker than cross-screen',
    },
    'mde_note': mde_note,
    'qualification': {
        'gates': gate, 'qualified': qualified, 'judgment': judgment,
        'failed_gates': [k for k, v in gate.items() if not v],
        'required_measurement_specs_if_not_qualified': required_spec,
        'threshold': {'primary_common_quadruples': 500, 'min_cells': 10, 'min_directed_pairs': 10},
    },
    'limitations': [
        'metadata-only matching; no response values read; Q not estimated',
        'library dose-point sets not published in fitted table -> dose-layout match only at published design columns',
        'no raw Validation plate layout available locally -> cannot verify per-well layout equality across screens',
        'Original repeated plates lack date/batch metadata -> barcode split independence weaker than cross-screen',
        'text/ID matching does not prove biological identity',
        'matching qualification does not imply Q is stable or transferable; that is A1',
    ],
}
(OUT / 'a0.json').write_text(json.dumps(a0, indent=2, ensure_ascii=False, sort_keys=True), encoding='utf8')
print(json.dumps({
    'judgment': judgment, 'gates': gate,
    'R4_common': R4['quadruples'], 'R3_half': a0['quadruples']['R3_half_matches'],
    'levels_common': levels_primary,
    'G1_only': G1only['quadruples'], 'G2_only': G2only['quadruples'],
    'barcode_split_R4': BC['quadruples'],
    'coverage': a0['quadruples']['coverage_R4'], 'strata': R4['strata'],
    'csv_rows_written': written, 'total_csv_conditions': len(cond_rows),
    'elapsed_s': round(elapsed, 1),
}, indent=1, ensure_ascii=False))
