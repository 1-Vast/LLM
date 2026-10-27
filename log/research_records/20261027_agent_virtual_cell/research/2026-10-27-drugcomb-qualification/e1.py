"""R190-E1: DrugComb second-resource qualification audit (offline, deterministic).

Implements PROTOCOL_E1.md. NEVER reads response values: only identity / annotation /
unit-string columns are indexed; response columns are used as header strings only.

Run:  D:\\anaconda\\envs\\maestro\\python.exe e1.py
Output: e1.json  (deterministic: sorted keys, no timestamps)
"""
from __future__ import annotations

import collections
import csv
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import zipfile

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
DL = os.path.join(BASE, 'downloads')
CH = os.path.join(DL, 'v15_chunks')

V14 = os.path.join(DL, 'summary_table_v1.4.csv')
V15_DRUG_ID = os.path.join(DL, 'DrugComb_drug_identifiers.xlsx')
V15_CELL_ID = os.path.join(DL, 'DrugComb_cell_line_identifiers.xlsx')
EPMC_SUPP = os.path.join(DL, 'drugcomb_2021_supplementary_PMC8218202.zip')
RECEIPT = os.path.join(BASE, 'download_receipt.json')
PROTOCOL = os.path.join(BASE, 'PROTOCOL_E1.md')

JAAKS_ORIG = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                          'Original screen_All tissues_fitted data.csv')
JAAKS_VAL = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                         'Validation screen_All tissues_fitted data.csv')

# v1.5 summary sampling (frozen in PROTOCOL_E1.md section 2)
V15_BYTES = 1421694989
N_CHUNKS = 60
CHUNK_SIZE = 1000000

# ---------------------------------------------------------------- helpers

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def md5_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def norm(s) -> str:
    """PROTOCOL_E1 section 4: NFKC -> casefold -> keep alphanumerics."""
    s = unicodedata.normalize('NFKC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())


def norm_series(series) -> pd.Series:
    """norm() that maps missing / non-string values to ''."""
    return series.map(lambda x: norm(x) if isinstance(x, str) else '')


def pct(a, b):
    return None if not b else round(100.0 * a / b, 2)


def collision_report(raw_names):
    """normalized key -> sorted distinct casefold-different raw names when >=2."""
    d = collections.defaultdict(set)
    for x in raw_names:
        if not isinstance(x, str):
            continue
        n = norm(x)
        if n:
            d[n].add(x)
    return {k: sorted(v) for k, v in d.items() if len({v.casefold() for v in v}) > 1}


# ================================================================ 1. inputs
def verify_inputs():
    receipt = json.load(open(RECEIPT, encoding='utf-8'))
    files = {f['key']: f for f in receipt['files']}
    out = {'receipt_sha256': sha256_file(RECEIPT), 'files': {}, 'chunks': {}, 'errors': []}
    for key, f in sorted(files.items()):
        p = os.path.join(BASE, f['saved_as'])
        rec = {'saved_as': f['saved_as'], 'url': f['url'],
               'bytes_expected': f['bytes_actual']}
        if not os.path.exists(p):
            rec['status'] = 'missing'
            out['errors'].append('missing input: ' + key)
        else:
            rec['bytes_actual'] = os.path.getsize(p)
            rec['sha256'] = sha256_file(p)
            rec['sha256_matches_receipt'] = (rec['sha256'] == f['sha256'])
            rec['md5'] = md5_file(p)
            rec['md5_published'] = f['md5_reported']
            rec['md5_matches_published'] = (f['md5_reported'] is None) or (
                rec['md5'] == f['md5_reported'])
            rec['status'] = 'ok'
            if not rec['sha256_matches_receipt']:
                out['errors'].append('sha256 mismatch: ' + key)
            if not rec['md5_matches_published']:
                out['errors'].append('published md5 mismatch: ' + key)
        out['files'][key] = rec
    ch = receipt['chunks']
    bad = 0
    for c in ch['chunks']:
        p = os.path.join(BASE, c['saved_as'])
        ok = (os.path.exists(p) and os.path.getsize(p) == c['bytes']
              and sha256_file(p) == c['sha256'])
        if not ok:
            bad += 1
    out['chunks'] = {'n': len(ch['chunks']), 'bad': bad,
                     'bytes': sum(c['bytes'] for c in ch['chunks']),
                     'full_file_bytes': ch['file_bytes'],
                     'md5_published': ch['md5_published'] if 'md5_published' in ch else ch.get('md5_reported'),
                     'full_file_sha256': None,
                     'sampling_note': ch['sampling_note']}
    if bad:
        out['errors'].append('chunk verification failed: %d' % bad)
    return receipt, out


# ====================================================== 2. v1.4 summary table
V14_READ = ['block_id', 'drug_row', 'drug_col', 'cell_line_name', 'conc_r_unit', 'conc_c_unit']
V14_DENY = ['css', 'synergy_zip', 'synergy_bliss', 'synergy_loewe', 'synergy_hsa',
            'ic50_row', 'ic50_col', 'ri_row', 'ri_col', 'css_row', 'css_col', 'S']


def audit_v14():
    res = {'path': os.path.relpath(V14, BASE)}
    with open(V14, newline='', encoding='utf-8') as f:
        rdr = csv.reader(f)
        header = next(rdr)
        idx = {name: i for i, name in enumerate(header)}
        res['columns'] = header
        res['read_columns_missing'] = [c for c in V14_READ if c not in idx]
        res['deny_columns_present'] = [c for c in V14_DENY if c in idx]
        i_block, i_dr, i_dc, i_cl = idx['block_id'], idx['drug_row'], idx['drug_col'], idx['cell_line_name']
        i_ur, i_uc = idx.get('conc_r_unit'), idx.get('conc_c_unit')
        rows = mono = combo = 0
        drug_raw = []
        cell_raw = []
        pair_norm = set()
        cp_norm = set()
        block_ids = []
        unit_r = collections.Counter()
        unit_c = collections.Counter()
        for row in rdr:
            rows += 1
            b = row[i_block].strip()
            dr = row[i_dr].strip()
            dc = row[i_dc].strip()
            cl = row[i_cl].strip()
            block_ids.append(b)
            if (not dc) or dc.upper() in ('NA', 'NULL') or (not dr) or dr.upper() in ('NA', 'NULL'):
                mono += 1
                continue
            combo += 1
            drug_raw.append(dr)
            drug_raw.append(dc)
            cell_raw.append(cl)
            if i_ur is not None and row[i_ur]:
                unit_r[row[i_ur].strip()] += 1
            if i_uc is not None and row[i_uc]:
                unit_c[row[i_uc].strip()] += 1
            ndr, ndc, ncl = norm(dr), norm(dc), norm(cl)
            pk = (ndr, ndc) if ndr <= ndc else (ndc, ndr)
            pair_norm.add(pk)
            cp_norm.add(ncl + '\x1f' + pk[0] + '\x1f' + pk[1])
    drug_coll = collision_report(drug_raw)
    cell_coll = collision_report(cell_raw)
    drug_norm = {norm(x) for x in drug_raw if norm(x)}
    cell_norm = {norm(x) for x in cell_raw if norm(x)}
    digits = [int(b) for b in block_ids if b.isdigit()]
    res.update({
        'rows_total': rows,
        'rows_monotherapy_like': mono,
        'rows_combination': combo,
        'has_study_column': 'study_name' in idx,
        'block_ids_distinct': len(set(block_ids)),
        'block_id_min': min(digits) if digits else None,
        'block_id_max': max(digits) if digits else None,
        'drugs_raw': len({x for x in drug_raw}),
        'drugs_norm': len(drug_norm),
        'drug_collision_keys': len(drug_coll),
        'drug_collisions': dict(sorted(drug_coll.items())),
        'cells_raw': len({x for x in cell_raw}),
        'cells_norm': len(cell_norm),
        'cell_collision_keys': len(cell_coll),
        'cell_collisions': dict(sorted(cell_coll.items())),
        'pairs_norm': len(pair_norm),
        'cell_x_pair_units_norm': len(cp_norm),
        'conc_row_units': dict(sorted(unit_r.items())),
        'conc_col_units': dict(sorted(unit_c.items())),
    })
    d1 = drug_norm - set(drug_coll)
    res['D1_size'] = len(d1)
    res['D1_collision_removed'] = len(drug_coll)
    return res, d1, drug_norm, cell_norm, pair_norm, cp_norm


# ==================================================== 3. v1.5 identifiers
def audit_identifiers():
    d = pd.read_excel(V15_DRUG_ID)
    c = pd.read_excel(V15_CELL_ID)
    dn = norm_series(d['dname']) if 'dname' in d.columns else pd.Series(dtype=str)
    cn = norm_series(c['name']) if 'name' in c.columns else pd.Series(dtype=str)
    target_ok = (d['target_name'].fillna('').astype(str).str.strip() != '') if 'target_name' in d.columns else None
    res = {
        'drug_rows': int(len(d)),
        'drug_cols': list(d.columns),
        'drug_dname_distinct_raw': int(d['dname'].nunique()) if 'dname' in d.columns else None,
        'drug_dname_norm_distinct': int(dn[dn != ''].nunique()),
        'drug_dname_nonempty_norm': int((dn != '').sum()),
        'drug_dname_norm_rate_pct': pct(int((dn != '').sum()), len(d)),
        'drug_norm_collision_keys': int(sum(1 for s in dn[dn != ''].value_counts().tolist() if s > 1)),
        'drug_target_name_present_rows': int(target_ok.sum()) if target_ok is not None else None,
        'drug_target_name_coverage_pct': pct(int(target_ok.sum()), len(d)) if target_ok is not None else None,
        'cell_rows': int(len(c)),
        'cell_cols': list(c.columns),
        'cell_name_nonempty_norm': int((cn != '').sum()),
        'cell_name_norm_distinct': int(cn[cn != ''].nunique()),
        'cell_name_norm_rate_pct': pct(int((cn != '').sum()), len(c)),
        'cell_norm_collision_keys': int(sum(1 for s in cn[cn != ''].value_counts().tolist() if s > 1)),
    }
    if 'clinical_phase' in d.columns:
        res['drug_clinical_phase_nonnull'] = int(d['clinical_phase'].notna().sum())
        res['drug_clinical_phase_levels'] = sorted({str(x) for x in d['clinical_phase'].dropna().unique()})
    if 'target_type' in d.columns:
        res['drug_target_type_levels'] = int(d['target_type'].nunique())
    for k in ['depmap_id', 'cosmic_id', 'tissue_id', 'cellosaurus_accession']:
        if k in c.columns:
            res['cell_%s_nonnull' % k] = int(c[k].notna().sum())
    res['cell_tissue_levels'] = int(c['tissue_id'].nunique()) if 'tissue_id' in c.columns else None
    id_drug = set(dn[dn != ''])
    id_cell = set(cn[cn != ''])
    id_target = set(dn[target_ok]) if target_ok is not None else set()
    return res, id_drug, id_cell, id_target


# ================================================== 4. v1.5 summary sample
V15_READ = ['block_id', 'drug_row', 'drug_col', 'cell_line_name', 'study_name', 'tissue_name',
            'conc_row_unit', 'conc_col_unit', 'drug_row_clinical_phase', 'drug_col_clinical_phase',
            'drug_row_target_name', 'drug_col_target_name']
V15_DENY = ['ic50_row', 'ic50_col', 'ri_row', 'ri_col', 'css_row', 'css_col', 'css_ri',
            'S_sum', 'S_mean', 'S_max', 'synergy_zip', 'synergy_loewe', 'synergy_hsa', 'synergy_bliss']


def _nullish(x):
    if x is None:
        return True
    x = str(x)
    return x == '' or x == '\\N' or x.upper() in ('NULL', 'NA')


def parse_chunk_rows(path, start_byte, idx):
    data = open(path, 'rb').read()
    if start_byte > 0:
        k = data.find(b'\n')
        if k < 0:
            return []
        data = data[k + 1:]
    k = data.rfind(b'\n')
    if k < 0:
        return []
    text = data[:k + 1].decode('utf-8')
    out = []
    rdr = csv.reader(io.StringIO(text))
    for row in rdr:
        if start_byte == 0 and row and row[0] == 'block_id':
            continue
        vals = []
        for name in V15_READ:
            i = idx.get(name)
            vals.append(row[i] if (i is not None and i < len(row)) else '')
        out.append(vals)
    return out


def audit_v15_sample(header_idx, header, id_drug, id_cell):
    res = {
        'header': header,
        'read_columns_missing': [c for c in V15_READ if c not in header_idx],
        'deny_columns_present': [c for c in V15_DENY if c in header_idx],
        'rows': 0, 'monotherapy_like': 0, 'combination': 0,
        'studies': collections.Counter(),
        'study_combo': collections.Counter(),
        'study_mono': collections.Counter(),
        'study_cp': collections.defaultdict(set),
        'study_block_ids': collections.defaultdict(list),
        'study_cells': collections.defaultdict(set),
        'study_drugs': collections.defaultdict(set),
        'cp_all': set(), 'cp_nogdscjaaks': set(),
        'drug_norm': set(), 'cell_norm': set(),
        'unit_r': collections.Counter(), 'unit_c': collections.Counter(),
        'gdsc_study_combo_rows': 0, 'gdsc_study_mono_rows': 0,
        'target_row_nonnull': 0, 'clinphase_row_nonnull': 0,
        'cell_matched_id': set(), 'cell_unmatched_id': set(),
        'drug_matched_id': set(), 'drug_unmatched_id': set(),
        'chunks_used': 0,
    }
    for fn in sorted(os.listdir(CH)):
        m = re.match(r'chunk_(\d+)_(\d+)\.bin$', fn)
        if not m:
            continue
        rows = parse_chunk_rows(os.path.join(CH, fn), int(m.group(2)), header_idx)
        res['chunks_used'] += 1
        for vals in rows:
            block, dr, dc, cl, study, tissue, ur, uc, cpr, cpc, tr, tc = vals
            res['rows'] += 1
            study = study.strip()
            dr, dc, cl = dr.strip(), dc.strip(), cl.strip()
            res['studies'][study] += 1
            is_gdsc = bool(re.search(r'jaaks|gdsc', norm(study)))
            if _nullish(dc) or _nullish(dr):
                res['monotherapy_like'] += 1
                res['study_mono'][study] += 1
                if is_gdsc:
                    res['gdsc_study_mono_rows'] += 1
                continue
            res['combination'] += 1
            res['study_combo'][study] += 1
            if is_gdsc:
                res['gdsc_study_combo_rows'] += 1
            ndr, ndc, ncl = norm(dr), norm(dc), norm(cl)
            pk = (ndr, ndc) if ndr <= ndc else (ndc, ndr)
            key = ncl + '\x1f' + pk[0] + '\x1f' + pk[1]
            res['cp_all'].add(key)
            if not is_gdsc:
                res['cp_nogdscjaaks'].add(key)
            res['drug_norm'].update((ndr, ndc))
            res['cell_norm'].add(ncl)
            res['study_cp'][study].add(key)
            res['study_cells'][study].add(ncl)
            res['study_drugs'][study].update((ndr, ndc))
            if ur:
                res['unit_r'][ur.strip()] += 1
            if uc:
                res['unit_c'][uc.strip()] += 1
            if not (_nullish(tr) and _nullish(tc)):
                res['target_row_nonnull'] += 1
            if not (_nullish(cpr) and _nullish(cpc)):
                res['clinphase_row_nonnull'] += 1
            try:
                res['study_block_ids'][study].append(int(block))
            except (TypeError, ValueError):
                pass
            if ncl in id_cell:
                res['cell_matched_id'].add(ncl)
            else:
                res['cell_unmatched_id'].add(ncl)
            for nd in (ndr, ndc):
                if nd in id_drug:
                    res['drug_matched_id'].add(nd)
                else:
                    res['drug_unmatched_id'].add(nd)
    study_table = {}
    for s in sorted(res['studies']):
        bl = res['study_block_ids'].get(s, [])
        study_table[s] = {
            'sample_rows': int(res['studies'][s]),
            'sample_combo_rows': int(res['study_combo'].get(s, 0)),
            'sample_mono_rows': int(res['study_mono'].get(s, 0)),
            'sample_cell_x_pair_lower_bound': len(res['study_cp'].get(s, set())),
            'sample_cells': len(res['study_cells'].get(s, set())),
            'sample_drugs': len(res['study_drugs'].get(s, set())),
            'block_id_min': min(bl) if bl else None,
            'block_id_max': max(bl) if bl else None,
            'matches_gdsc_jaaks_pattern': bool(re.search(r'jaaks|gdsc', norm(s))),
        }
    out = {
        'header': header,
        'read_columns_missing': res['read_columns_missing'],
        'deny_columns_present': res['deny_columns_present'],
        'chunks_used': res['chunks_used'],
        'rows': res['rows'],
        'monotherapy_like': res['monotherapy_like'],
        'combination': res['combination'],
        'n_studies_observed': len(study_table),
        'study_table': study_table,
        'cp_lower_bound_all': len(res['cp_all']),
        'cp_lower_bound_after_exclusion': len(res['cp_nogdscjaaks']),
        'drug_norm_lower_bound': len(res['drug_norm']),
        'cell_norm_lower_bound': len(res['cell_norm']),
        'cell_id_match_pct': pct(len(res['cell_matched_id']),
                                 len(res['cell_matched_id']) + len(res['cell_unmatched_id'])),
        'drug_id_match_pct': pct(len(res['drug_matched_id']),
                                 len(res['drug_matched_id']) + len(res['drug_unmatched_id'])),
        'cell_unmatched_in_identifier_count': len(res['cell_unmatched_id']),
        'drug_unmatched_in_identifier_count': len(res['drug_unmatched_id']),
        'gdsc_study_combo_rows': res['gdsc_study_combo_rows'],
        'gdsc_study_mono_rows': res['gdsc_study_mono_rows'],
        'target_name_nonnull_row_pct': pct(res['target_row_nonnull'], res['combination']),
        'clinical_phase_nonnull_row_pct': pct(res['clinphase_row_nonnull'], res['combination']),
        'conc_row_units': dict(sorted(res['unit_r'].items())),
        'conc_col_units': dict(sorted(res['unit_c'].items())),
        'combo_fraction_of_sample_pct': pct(res['combination'], res['rows']),
        'sampled_bytes': N_CHUNKS * CHUNK_SIZE,
        'file_bytes': V15_BYTES,
        'sampled_fraction_pct': round(100.0 * N_CHUNKS * CHUNK_SIZE / V15_BYTES, 2),
    }
    return out


# ==================================================== 5. S1 study table (paper)
S1_ROW = re.compile(
    r'^([A-Za-z0-9_\-\(\)\/\.\+]+)\s+'
    r'(Cancer|SARS-CoV-2|Malaria|Ebola)\s+'
    r'(Publication|NCATS Tripod|PharmacoDB|AstraZeneca|ChEMBL)\s+(.+)$')
S1_NUM = re.compile(r'^(?:(\d+)\s+)?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$')


def _matrix_is_mono(matrix):
    dims = re.findall(r'(\d+)\s*x\s*(\d+)', matrix)
    if not dims:
        return None
    return all(int(b) == 1 for _, b in dims)


def audit_s1():
    res = {'source': os.path.relpath(EPMC_SUPP, BASE), 'parse_ok': False}
    try:
        z = zipfile.ZipFile(EPMC_SUPP)
    except Exception as exc:  # noqa: BLE001
        res['error'] = 'cannot open zip: %s' % exc
        return res
    pdfs = [n for n in z.namelist() if n.lower().endswith('.pdf')]
    if not pdfs:
        res['error'] = 'no pdf in supplement zip'
        return res
    from pypdf import PdfReader
    raw = z.read(pdfs[0])
    reader = PdfReader(io.BytesIO(raw))
    text = '\n'.join((p.extract_text() or '') for p in reader.pages)
    # Single-drug-screening studies: PharmacoDB monotherapy datasets plus four
    # explicitly single-agent studies.  Rule frozen after reconciling the paper
    # reported totals (751,498 combination blocks / 717,684 single-agent blocks):
    # only this rule reproduces both totals exactly.
    MONO_STUDIES = {'BEATAML', 'TOURET', 'GORDON', 'ELLINGER'}
    rows = []
    divergences = []
    for line in text.split('\n'):
        line = ' '.join(line.split())
        m = S1_ROW.match(line)
        if not m:
            continue
        name, disease, source, rest = m.groups()
        m2 = S1_NUM.match(rest.strip())
        if not m2:
            continue
        pmid, ndrug, nblock, ncell, ntissue, matrix = m2.groups()
        mono_matrix = _matrix_is_mono(matrix)
        if mono_matrix is None:
            continue
        mono = (source == 'PharmacoDB') or (name in MONO_STUDIES)
        if bool(mono) != bool(mono_matrix):
            divergences.append({'study': name, 'matrix': matrix.strip(),
                                'matrix_heuristic': 'mono' if mono_matrix else 'combo',
                                'adopted': 'mono' if mono else 'combo'})
        rows.append({'study': name, 'disease': disease, 'data_source': source,
                     'pubmed_id': pmid or None,
                     'n_drugs': int(ndrug), 'n_blocks': int(nblock),
                     'n_cell_lines': int(ncell), 'n_tissues': int(ntissue),
                     'matrix': matrix.strip().rstrip('.'),
                     'monotherapy': bool(mono),
                     'monotherapy_matrix_heuristic': bool(mono_matrix)})
    combo_blocks = sum(r['n_blocks'] for r in rows if not r['monotherapy'])
    mono_blocks = sum(r['n_blocks'] for r in rows if r['monotherapy'])
    res.update({
        'pdf_bytes': len(raw),
        'pdf_sha256': sha256_bytes(raw),
        'n_studies': len(rows),
        'studies': rows,
        'classification_rule': ('monotherapy = data_source==PharmacoDB or study in '
                                '{BEATAML, TOURET, GORDON, ELLINGER}; only this rule reproduces the '
                                'paper-reported block totals (matrix heuristic is secondary)'),
        'mono_combo_classification_divergences': divergences,
        'reported_combo_blocks': combo_blocks,
        'reported_mono_blocks': mono_blocks,
        'reported_total_blocks': combo_blocks + mono_blocks,
        'paper_reported': {'combo_blocks': 751498, 'mono_blocks': 717684,
                           'total_blocks': 1469182, 'cell_lines': 2320, 'drugs': 8397},
        'sum_checks': {
            'mono_matches_paper': mono_blocks == 717684,
            'combo_matches_paper': combo_blocks == 751498,
            'total_matches_paper': (combo_blocks + mono_blocks) == 1469182,
        },
        'parse_ok': len(rows) >= 30,
    })
    return res


# ============================================================ 6. Jaaks overlap
JAAKS_COLS = ['CELL_LINE_NAME', 'ANCHOR_NAME', 'LIBRARY_NAME', 'ANCHOR_PATHWAY', 'LIBRARY_PATHWAY']


def load_jaaks():
    jf = pd.read_csv(JAAKS_ORIG, usecols=JAAKS_COLS)
    vf = pd.read_csv(JAAKS_VAL, usecols=JAAKS_COLS)
    out = {'orig_rows': int(len(jf)), 'val_rows': int(len(vf))}
    for tag, df in [('orig', jf), ('val', vf)]:
        cn = norm_series(df['CELL_LINE_NAME'])
        cells = set(cn[cn != ''])
        an = norm_series(df['ANCHOR_NAME'])
        ln = norm_series(df['LIBRARY_NAME'])
        drugs = (set(an[an != '']) | set(ln[ln != '']))
        pw = {}
        for nm, p in list(zip(df['ANCHOR_NAME'], df['ANCHOR_PATHWAY'])) + list(
                zip(df['LIBRARY_NAME'], df['LIBRARY_PATHWAY'])):
            n = norm(nm) if isinstance(nm, str) else ''
            if n and isinstance(p, str) and p.strip():
                pw[n] = p.strip()
        keys = set()
        for cl, a, b in zip(df['CELL_LINE_NAME'], df['ANCHOR_NAME'], df['LIBRARY_NAME']):
            ncl = norm(cl) if isinstance(cl, str) else ''
            na = norm(a) if isinstance(a, str) else ''
            nb = norm(b) if isinstance(b, str) else ''
            if not (ncl and na and nb):
                continue
            pk = (na, nb) if na <= nb else (nb, na)
            keys.add(ncl + '\x1f' + pk[0] + '\x1f' + pk[1])
        out[tag] = {
            'rows': int(len(df)),
            'cells_raw': int(df['CELL_LINE_NAME'].nunique()),
            'cells_norm': len(cells),
            'drugs_norm': len(drugs),
            'anchor_drugs_norm': int(an[an != ''].nunique()),
            'library_drugs_norm': int(ln[ln != ''].nunique()),
            'anchor_pathway_levels': int(df['ANCHOR_PATHWAY'].nunique()),
            'library_pathway_levels': int(df['LIBRARY_PATHWAY'].nunique()),
            'pathway_onehot_columns': int(df['ANCHOR_PATHWAY'].nunique() + df['LIBRARY_PATHWAY'].nunique()),
            'pathway_text_levels_union': len(set(df['ANCHOR_PATHWAY'].dropna()) | set(df['LIBRARY_PATHWAY'].dropna())),
            'pathway_drugs': len(pw),
            'pathway_levels': len(set(pw.values())),
            'pathway_counts': dict(sorted(collections.Counter(pw.values()).items())),
            'cell_collision_keys': len(collision_report(df['CELL_LINE_NAME'].dropna())),
            'drug_collision_keys': len(collision_report(
                list(df['ANCHOR_NAME'].dropna()) + list(df['LIBRARY_NAME'].dropna()))),
            'cell_drug_drug_keys_ordered': int(df.groupby(
                ['CELL_LINE_NAME', 'ANCHOR_NAME', 'LIBRARY_NAME']).ngroups),
            'cell_x_pair_keys_norm_unordered': len(keys),
            '_cells': cells, '_drugs': drugs, '_keys': keys,
        }
    union_cells = out['orig']['_cells'] | out['val']['_cells']
    union_drugs = out['orig']['_drugs'] | out['val']['_drugs']
    union_keys = out['orig']['_keys'] | out['val']['_keys']
    out['union'] = {'cells_norm': len(union_cells), 'drugs_norm': len(union_drugs),
                    'cell_x_pair_keys_norm_unordered': len(union_keys),
                    '_cells': union_cells, '_drugs': union_drugs, '_keys': union_keys}
    out['pathway_levels_union'] = len(set(out['orig']['pathway_counts']) | set(out['val']['pathway_counts']))
    return out


# ============================================================ 7. annotation
def load_annotation_sources():
    src = {}
    drh = pd.read_csv(os.path.join(ROOT, 'data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt'),
                      sep='\t', skiprows=9, low_memory=False)
    ann = (drh['target'].fillna('').astype(str).str.strip() != '') | (
        drh['moa'].fillna('').astype(str).str.strip() != '')
    src['DRH_moa_target'] = {
        'path': 'data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt',
        'rows': int(len(drh)), 'annotated_rows': int(ann.sum()),
        'names': set(norm_series(drh.loc[ann, 'pert_iname'])) - {''},
        'moa_levels': int(drh['moa'].nunique()), 'target_field_levels': int(drh['target'].nunique())}
    for tag, p in [
            ('PRISM_primary', 'data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv'),
            ('PRISM_secondary', 'data/external/prism_19q4/raw/secondary-screen-replicate-collapsed-treatment-info.csv')]:
        df = pd.read_csv(os.path.join(ROOT, p), low_memory=False)
        ann = (df['target'].fillna('').astype(str).str.strip() != '') | (
            df['moa'].fillna('').astype(str).str.strip() != '')
        src[tag] = {'path': p, 'rows': int(len(df)), 'annotated_rows': int(ann.sum()),
                    'names': set(norm_series(df.loc[ann, 'name'])) - {''},
                    'moa_levels': int(df['moa'].nunique()),
                    'target_field_levels': int(df['target'].nunique())}
    mk = pd.read_parquet(os.path.join(ROOT, 'data/external/mapkg_20261009/drug_metadata.parquet'))
    ann = (mk['targets'].fillna('').astype(str).str.strip() != '') | (
        mk['moa-fine'].fillna('').astype(str).str.strip() != '')
    src['MAPKG_moa_target'] = {
        'path': 'data/external/mapkg_20261009/drug_metadata.parquet',
        'rows': int(len(mk)), 'annotated_rows': int(ann.sum()),
        'names': set(norm_series(mk.loc[ann, 'drug'])) - {''},
        'moa_fine_levels': int(mk['moa-fine'].nunique()),
        'target_field_levels': int(mk['targets'].nunique())}
    fp = pd.read_excel(os.path.join(ROOT, 'data/external/fpmtb_zenodo_7370747/File_2_Drug_library_515D.xlsx'))
    mech = fp['Mechanism/Targets'].fillna('').astype(str).str.strip() != ''
    fnames = (set(norm_series(fp.loc[mech, 'Preferred name']))
              | set(norm_series(fp.loc[mech, 'Non-proprietary name'])))
    src['FPMTB_mechanism'] = {
        'path': 'data/external/fpmtb_zenodo_7370747/File_2_Drug_library_515D.xlsx',
        'rows': int(len(fp)), 'annotated_rows': int(mech.sum()),
        'names': fnames - {''},
        'sub_class_levels': int(fp['Drug_Sub_Class'].nunique()),
        'class_levels': int(fp['Drug_Class'].nunique())}
    bm = pd.read_excel(os.path.join(ROOT, 'data/external/beataml2_20261017/beataml_drug_families.xlsx'),
                       sheet_name='drug_family')
    ann = bm['family'].fillna('').astype(str).str.strip() != ''
    src['BeatAML_family'] = {
        'path': 'data/external/beataml2_20261017/beataml_drug_families.xlsx',
        'rows': int(len(bm)), 'annotated_rows': int(ann.sum()),
        'names': set(norm_series(bm.loc[ann, 'inhibitor'])) - {''},
        'family_levels': int(bm['family'].nunique())}
    jf = pd.read_csv(JAAKS_ORIG, usecols=JAAKS_COLS)
    vf = pd.read_csv(JAAKS_VAL, usecols=JAAKS_COLS)
    pw = {}
    for df in (jf, vf):
        for nm, p in list(zip(df['ANCHOR_NAME'], df['ANCHOR_PATHWAY'])) + list(
                zip(df['LIBRARY_NAME'], df['LIBRARY_PATHWAY'])):
            n = norm(nm) if isinstance(nm, str) else ''
            if n and isinstance(p, str) and p.strip():
                pw[n] = p.strip()
    src['Jaaks_pathway'] = {
        'path': 'data/external/gdsc_combinations/jaaks2022_figshare/*_fitted data.csv',
        'rows': int(len(jf) + len(vf)), 'annotated_rows': len(pw),
        'names': set(pw), 'pathway_levels': len(set(pw.values()))}
    return src


def coverage(denom, source_sets):
    out = {k: {'covered': len(denom & s), 'pct': pct(len(denom & s), len(denom))}
           for k, s in source_sets.items()}
    union = set().union(*source_sets.values())
    out['LOCAL_UNION'] = {'covered': len(denom & union), 'pct': pct(len(denom & union), len(denom))}
    return out


# ================================================== 8. both-unseen feasibility
def both_unseen_v14(drug_norm, cp_norm, r_values=(0.20, 0.30, 0.40)):
    names = sorted(drug_norm)
    n = len(names)
    out = {}
    for r in r_values:
        k = max(1, round(r * n))
        step = max(1, n // k)
        hold = set(names[0::step][:k])
        bu = []
        bpairs = set()
        for s in cp_norm:
            _, a, b = s.split('\x1f')
            if a in hold and b in hold:
                bu.append(s)
                bpairs.add((a, b) if a <= b else (b, a))
        out['%.2f' % r] = {'n_drug': n, 'k_holdout': len(hold),
                           'both_unseen_cell_x_pairs': len(bu), 'both_unseen_pairs': len(bpairs)}
    return out


# ======================================================= endpoint inventory
def endpoint_inventory(header14, header15):
    def bucket(name):
        n = name.lower()
        if n in {'block_id', 'drug_row', 'drug_col', 'cell_line_name', 'study_name',
                 'tissue_name', 'conc_r_unit', 'conc_c_unit', 'conc_row_unit', 'conc_col_unit'}:
            return 'identity/design'
        if n in {'drug_row_clinical_phase', 'drug_col_clinical_phase',
                 'drug_row_target_name', 'drug_col_target_name'}:
            return 'annotation'
        if (n in {'css', 's'} or n.startswith('synergy_') or n.startswith('ic50_')
                or n.startswith('ri_') or n.startswith('css_') or n.startswith('s_')):
            return 'response_derived(no-read)'
        return 'unknown'
    b14 = {c: bucket(c) for c in header14}
    b15 = {c: bucket(c) for c in header15}
    return {'v1.4': b14, 'v1.5': b15,
            'v1.4_response_columns': [c for c, b in b14.items() if b.startswith('response')],
            'v1.5_response_columns': [c for c, b in b15.items() if b.startswith('response')],
            'v1.5_annotation_columns': [c for c, b in b15.items() if b == 'annotation'],
            'v1.4_study_column': 'study_name' in header14,
            'v1.5_study_column': 'study_name' in header15,
            'explicit_qc_flag_columns': []}


# =================================================================== main
def main():
    print('[1/9] verify inputs ...', flush=True)
    receipt, inputs = verify_inputs()

    print('[2/9] v1.4 summary table ...', flush=True)
    v14, d1, drug_norm14, cell_norm14, pair_norm14, cp_norm14 = audit_v14()

    print('[3/9] v1.5 identifier tables ...', flush=True)
    ids, id_drug, id_cell, id_target = audit_identifiers()

    print('[4/9] v1.5 summary chunks ...', flush=True)
    chunk_files = sorted(f for f in os.listdir(CH) if f.startswith('chunk_'))
    if not chunk_files:
        raise SystemExit('no v1.5 chunks in %s' % CH)
    first = chunk_files[0]
    head_text = open(os.path.join(CH, first), 'rb').read().decode('utf-8', errors='replace')
    header15 = [c.strip() for c in next(csv.reader(io.StringIO(head_text.split('\n', 1)[0])))]
    header_idx = {name: i for i, name in enumerate(header15)}
    sample = audit_v15_sample(header_idx, header15, id_drug, id_cell)

    print('[5/9] S1 study table ...', flush=True)
    s1 = audit_s1()
    reported_studies = {r['study'] for r in s1.get('studies', [])}
    observed_studies = set(sample['study_table'].keys())
    s1['sample_coverage'] = {
        'reported_studies': sorted(reported_studies),
        'observed_studies_in_v15_sample': sorted(observed_studies & reported_studies),
        'reported_but_not_sampled': sorted(reported_studies - observed_studies),
        'sampled_but_not_reported': sorted(observed_studies - reported_studies),
        'n_reported': len(reported_studies),
        'n_observed': len(observed_studies & reported_studies),
    }
    # cross-check: v1.4 has no study column; v1.5 sample study names matching GDSC pattern
    sample['gdsc_jaaks_studies_in_sample'] = sorted(
        s for s, v in sample['study_table'].items() if v['matches_gdsc_jaaks_pattern'])
    sample['gdsc_jaaks_combo_rows_in_sample'] = sample['gdsc_study_combo_rows']

    print('[6/9] Jaaks overlap ...', flush=True)
    jaaks = load_jaaks()
    jcells = jaaks['union']['_cells']
    jdrugs = jaaks['union']['_drugs']
    jkeys = jaaks['union']['_keys']
    overlap = {
        'jaaks_cells_norm': len(jcells),
        'jaaks_drugs_norm': len(jdrugs),
        'jaaks_cell_x_pair_keys_norm': len(jkeys),
        'v14_combo_cells_norm': len(cell_norm14),
        'v14_combo_drugs_norm': len(drug_norm14),
        'v14_combo_cell_x_pair_units_norm': len(cp_norm14),
        'cell_overlap': len(jcells & cell_norm14),
        'cell_overlap_pct_of_v14': pct(len(jcells & cell_norm14), len(cell_norm14)),
        'cell_overlap_pct_of_jaaks': pct(len(jcells & cell_norm14), len(jcells)),
        'drug_overlap': len(jdrugs & drug_norm14),
        'drug_overlap_pct_of_v14': pct(len(jdrugs & drug_norm14), len(drug_norm14)),
        'drug_overlap_pct_of_jaaks': pct(len(jdrugs & drug_norm14), len(jdrugs)),
        'cell_x_pair_key_overlap': len(jkeys & cp_norm14),
        'v15id_cell_overlap': len(jcells & id_cell),
        'v15id_drug_overlap': len(jdrugs & id_drug),
        'note': 'strict normalized text-name intersection; synonym inference forbidden',
    }
    for k in ('_cells', '_drugs', '_keys'):
        for tag in ('orig', 'val'):
            jaaks[tag].pop(k, None)
        jaaks['union'].pop(k, None)

    print('[7/9] annotation sources ...', flush=True)
    src = load_annotation_sources()
    src_sets = {k: v['names'] for k, v in src.items()}
    cov = {
        'D1_main': coverage(d1, src_sets),
        'D1_all': coverage(drug_norm14, src_sets),
        'D2_v15_identifiers': coverage(id_drug, src_sets),
    }
    for v in src.values():
        v.pop('names')
    annotation = {
        'sources': src,
        'denominators': {'D1_main': len(d1), 'D1_all': len(drug_norm14),
                         'D2_v15_identifiers': len(id_drug)},
        'coverage': cov,
        'internal_target_name_coverage': {
            'D1_main': {'covered': len(d1 & id_target), 'pct': pct(len(d1 & id_target), len(d1))},
            'D2_v15_identifiers': {'covered': len(id_drug & id_target),
                                   'pct': pct(len(id_drug & id_target), len(id_drug))}},
        'local_union_gate_value': cov['D1_main']['LOCAL_UNION']['pct'],
        'pathway_mapping_protocol': 'not available locally -> next-round condition per PROTOCOL_E1 section 7',
    }

    print('[8/9] both-unseen feasibility ...', flush=True)
    bu = both_unseen_v14(drug_norm14, cp_norm14)

    print('[9/9] judgment ...', flush=True)
    endpoint = endpoint_inventory(v14['columns'], header15)

    files_ok = (not inputs['errors']) and all(v['status'] == 'ok' for v in inputs['files'].values()) \
        and inputs['chunks']['bad'] == 0
    g1 = {'id': 1, 'name': 'files_available_and_parsed', 'pass': bool(files_ok),
          'value': {'files': {k: v['status'] for k, v in inputs['files'].items()},
                    'chunks_bad': inputs['chunks']['bad'],
                    'v14_rows': v14['rows_total'], 'v15_sample_rows': sample['rows'],
                    's1_parse_ok': s1['parse_ok']},
          'errors': inputs['errors'],
          'threshold': 'all frozen inputs verified (bytes/SHA256; 60/60 chunks) and parsed'}
    g2 = {'id': 2, 'name': 'drug_cell_names_retrievable',
          'value': {'v15_drug_norm_rate_pct': ids['drug_dname_norm_rate_pct'],
                    'v15_cell_norm_rate_pct': ids['cell_name_norm_rate_pct'],
                    'v14_combination_rows': v14['rows_combination'],
                    'v14_drugs_raw': v14['drugs_raw'], 'v14_cells_raw': v14['cells_raw'],
                    'v15sample_cell_id_match_pct': sample['cell_id_match_pct'],
                    'v15sample_drug_id_match_pct': sample['drug_id_match_pct']},
          'threshold': 'v1.5 identifier normalization rate >=99%; v1.4 combo names non-empty; Jaaks intersection computable'}
    g2['pass'] = bool((ids['drug_dname_norm_rate_pct'] or 0) >= 99.0
                      and (ids['cell_name_norm_rate_pct'] or 0) >= 99.0
                      and v14['rows_combination'] > 0 and v14['drugs_raw'] > 0 and v14['cells_raw'] > 0)
    g3 = {'id': 3, 'name': 'cell_x_pair_units_after_jaaks_gdsc_exclusion_ge_2000',
          'value': {'v15_sample_cell_x_pair_lower_bound_after_exclusion': sample['cp_lower_bound_after_exclusion'],
                    'v15_sample_cell_x_pair_lower_bound_all': sample['cp_lower_bound_all'],
                    'v15_sample_total_rows': sample['rows'],
                    'v14_exact_cell_x_pair_units': v14['cell_x_pair_units_norm'],
                    'v14_rows_combination': v14['rows_combination'],
                    'v14_excluded_units': 0,
                    'v14_has_study_column': v14['has_study_column'],
                    'gdsc_jaaks_combo_rows_in_sample': sample['gdsc_study_combo_rows'],
                    'published_v15_combo_blocks': s1.get('reported_combo_blocks')},
          'threshold': '>=2000: v1.5 sample lower bound after GDSC/Jaaks study exclusion AND exact v1.4 count'}
    g3['pass'] = bool(sample['cp_lower_bound_after_exclusion'] >= 2000
                      and v14['cell_x_pair_units_norm'] >= 2000)
    g4 = {'id': 4, 'name': 'coarse_annotation_source_covers_ge_50pct_drugs',
          'value': {'D1_main_size': len(d1),
                    'local_union_covered': cov['D1_main']['LOCAL_UNION']['covered'],
                    'local_union_pct': cov['D1_main']['LOCAL_UNION']['pct'],
                    'D2_local_union_pct': cov['D2_v15_identifiers']['LOCAL_UNION']['pct'],
                    'internal_target_name_D2_pct': annotation['internal_target_name_coverage']['D2_v15_identifiers']['pct'],
                    'source_level_counts': {
                        'DRH_moa_levels': src['DRH_moa_target']['moa_levels'],
                        'DRH_target_levels': src['DRH_moa_target']['target_field_levels'],
                        'PRISM_primary_moa_levels': src['PRISM_primary']['moa_levels'],
                        'Jaaks_pathway_levels': src['Jaaks_pathway']['pathway_levels'],
                        'BeatAML_family_levels': src['BeatAML_family']['family_levels']}},
          'threshold': 'local union coverage of D1 >=50% (>=12-level potential reported separately)'}
    g4['pass'] = bool((cov['D1_main']['LOCAL_UNION']['pct'] or 0) >= 50.0)
    g5 = {'id': 5, 'name': 'non_saturated_evidence_checkable_later',
          'value': {'v14_response_columns': endpoint['v1.4_response_columns'],
                    'v15_response_columns': endpoint['v1.5_response_columns'],
                    'v15_study_column': endpoint['v1.5_study_column'],
                    'v15_annotation_columns': endpoint['v1.5_annotation_columns'],
                    'explicit_qc_flag_columns': endpoint['explicit_qc_flag_columns'],
                    'v15sample_target_name_nonnull_row_pct': sample['target_name_nonnull_row_pct']},
          'threshold': 'response/derived columns + study-level annotation columns exist; saturation test deferred'}
    g5['pass'] = bool(len(endpoint['v1.4_response_columns']) > 0
                      and len(endpoint['v1.5_response_columns']) > 0
                      and endpoint['v1.5_study_column'])
    gates = [g1, g2, g3, g4, g5]
    all_pass = all(g['pass'] for g in gates)

    conditions = []
    conditions.append(
        'v1.5 summary table is 1.42 GB: only a fixed 60x1MB byte-range sample (%.2f%% of bytes) was obtained '
        'within the <=300 MB budget; the file-level SHA256 was not computed (official Zenodo MD5 recorded). '
        'v1.5 cell x pair counts are sample lower bounds; the exact end-to-end verified analysis table is v1.4 '
        '(193 MB, full file).' % sample['sampled_fraction_pct'])
    conditions.append(
        'Annotation coverage is threshold-borderline: local union covers %.2f%% of D1 (the v1.4 combination-drug '
        'universe) but only %.2f%% of the full v1.5 identifier universe (D2); if the full v1.5 universe is used, '
        'sources must be extended or the analysis universe restricted.' % (
            cov['D1_main']['LOCAL_UNION']['pct'], cov['D2_v15_identifiers']['LOCAL_UNION']['pct']))
    conditions.append(
        'No local mapping exists from the available coarse annotations (MoA / target / family) to the project '
        'pathway/target coarse levels used by the frozen conclusion; the mapping protocol must be frozen in the '
        'next round (>=12-level potential exists but comparability is unverified).')
    conditions.append(
        'Endpoint saturation is NOT tested in this round (response values are not read); the saturation / '
        'measurement-regime check must be done before any effect estimation.')
    conditions.append(
        'Entity overlap with the Jaaks training resource is non-zero (cells %d, drugs %d, cell x pair keys %d); '
        'any both-unseen / external split must be frozen accordingly.' % (
            overlap['cell_overlap'], overlap['drug_overlap'], overlap['cell_x_pair_key_overlap']))
    conditions.append(
        'The v1.4 summary table has no study/source column, so a row-level Jaaks/GDSC study exclusion cannot be '
        'applied to v1.4; only v1.5 exposes study_name. Evidence that the excluded GDSC1 study is monotherapy-only '
        'comes from Supplementary Table S1 (matrix 5x1/9x1) and the v1.5 sample (0 combination rows under '
        'GDSC-pattern studies).')
    if not (s1.get('parse_ok') and s1['sum_checks']['mono_matches_paper']
            and s1['sum_checks']['total_matches_paper']):
        conditions.append('Supplementary Table S1 parse does not reproduce paper block totals; '
                          'study-level block counts are paper-reported facts only.')
    if ids['drug_norm_collision_keys'] or ids['cell_norm_collision_keys']:
        conditions.append(
            'Identifier tables contain normalized-name collisions (drug keys %d, cell keys %d); strict matching '
            'excludes them conservatively.' % (ids['drug_norm_collision_keys'], ids['cell_norm_collision_keys']))
    verdict = 'not_eligible' if not all_pass else ('eligible_with_conditions' if conditions else 'eligible')

    out = {
        'protocol': {'path': os.path.relpath(PROTOCOL, BASE), 'sha256': sha256_file(PROTOCOL)},
        'script': {'path': 'e1.py', 'sha256': sha256_file(os.path.join(BASE, 'e1.py'))},
        'inputs': inputs,
        'download_receipt': {'path': 'download_receipt.json', 'sha256': sha256_file(RECEIPT),
                             'total_bytes': receipt['total_bytes'],
                             'chunk_sampling': receipt['chunks']['sampling_note']},
        'v1.4_summary': v14,
        'v1.5_identifiers': ids,
        'v1.5_summary_sample': sample,
        's1_study_table': s1,
        'jaaks_training_resource': jaaks,
        'external_overlap': overlap,
        'annotation': annotation,
        'both_unseen_feasibility_v14': bu,
        'endpoints': endpoint,
        'judgment': {'gates': gates, 'all_gates_pass': all_pass, 'verdict': verdict,
                     'conditions': conditions,
                     'failure_categories': [] if all_pass else ['data_insufficient'],
                     'unfreeze_conditions': [] if all_pass else ['see report.md']},
    }
    with open(os.path.join(BASE, 'e1.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        f.write('\n')

    print('\n==== JUDGMENT: %s ====' % verdict)
    for g in gates:
        print('  gate %d %-52s pass=%s' % (g['id'], g['name'], g['pass']))
    print('\nkey numbers:')
    print('  v1.4 rows', v14['rows_total'], 'combo', v14['rows_combination'],
          'drugs', v14['drugs_raw'], 'cells', v14['cells_raw'],
          'cellxpair', v14['cell_x_pair_units_norm'])
    print('  v1.5 identifiers: drugs', ids['drug_rows'], 'cells', ids['cell_rows'])
    print('  v1.5 sample rows', sample['rows'], 'combo', sample['combination'],
          'studies', sample['n_studies_observed'],
          'cellxpair lower bound (after exclusion)', sample['cp_lower_bound_after_exclusion'])
    print('  S1 studies', s1.get('n_studies'), 'combo blocks', s1.get('reported_combo_blocks'),
          'mono blocks', s1.get('reported_mono_blocks'))
    print('  Jaaks overlap: cells', overlap['cell_overlap'], 'drugs', overlap['drug_overlap'],
          'keys', overlap['cell_x_pair_key_overlap'])
    print('  annotation D1 local union: %s / %s = %s%%' % (
        cov['D1_main']['LOCAL_UNION']['covered'], len(d1), cov['D1_main']['LOCAL_UNION']['pct']))
    print('  e1.json written.')


if __name__ == '__main__':
    sys.exit(main())
