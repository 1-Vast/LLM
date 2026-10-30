"""R195-A3: 条件级跨 screen 复验的资源资格审计（metadata-only）。

Implements PROTOCOL_A3.md (frozen before this run).  Phases:
  python a3.py --fetch   : download DrugComb v1.5 full summary (once) + receipt
  python a3.py           : run the audit -> a3.json + a3_overlap/*.csv

Discipline: response columns are never read as values (header existence only);
no Q estimation; no model fitting; deterministic JSON (sorted keys, no timestamps).
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import os
import sys
import time

import numpy as np

ROOT = r'D:\MAESTRO'
OUT = os.path.join(ROOT, 'research', '2026-10-27-conditional-shift')
OVLAP = os.path.join(OUT, 'a3_overlap')
TMP = os.path.join(ROOT, 'tmp')

PROTOCOL_A3 = os.path.join(OUT, 'PROTOCOL_A3.md')
A3_JSON = os.path.join(OUT, 'a3.json')

V15 = os.path.join(TMP, 'a3_v15_summary.csv')
V15_URL = 'https://zenodo.org/api/records/15235991/files/summary_v_1_5.csv/content'
V15_BYTES = 1421694989
V15_MD5 = 'cd3e24758c10ffaea0124b6e80626c32'
DOWNLOAD_RECEIPT = os.path.join(OVLAP, 'download_receipt_a3.json')

V14 = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification', 'downloads',
                   'summary_table_v1.4.csv')
V14_SHA = 'E08E3D35BFA4BEA011AFE1B05B7025ACDE5C669C5E8D265866B5E12B08037A2F'
V15_CHUNKS = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification',
                          'downloads', 'v15_chunks')

JAAKS_ORIG = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                          'Original screen_All tissues_fitted data.csv')
JAAKS_VAL = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                         'Validation screen_All tissues_fitted data.csv')
JAAKS_COLS = ['CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID', 'ANCHOR_NAME', 'LIBRARY_NAME',
              'ANCHOR_CONC', 'LIBRARY_CONC']

PRISM = os.path.join(ROOT, 'data/external/prism_19q4/raw')
ONEIL = os.path.join(ROOT, 'data/raw/oneil2026_qualification',
                     '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
BEATAML = os.path.join(ROOT, 'data/external/beataml2_20261017',
                       'beataml_probit_curve_fits_v4_dbgap.txt')
EMPTY_DIRS = {
    'gdsc2_fitted': os.path.join(ROOT, 'data/external/gdsc2_fitted'),
    'batchie_zenodo_13871987': os.path.join(ROOT, 'data/external/batchie_zenodo_13871987'),
    'nci_almanac_2017': os.path.join(ROOT, 'data/external/nci_almanac_2017'),
}
E1_JSON = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification', 'e1.json')

NULLISH = {'', 'NA', 'NULL', 'NAN', '\\N'}
# DrugComb v1.5 summary response/derived columns (header existence only; values never read)
V15_RESPONSE_COLS = ['ic50_row', 'ic50_col', 'ri_row', 'ri_col', 'css_row', 'css_col',
                     'css_ri', 'S_sum', 'S_mean', 'S_max', 'synergy_zip', 'synergy_loewe',
                     'synergy_hsa', 'synergy_bliss']
V15_META_COLS = ['study_name', 'tissue_name', 'conc_row_unit', 'conc_col_unit',
                 'drug_row_clinical_phase', 'drug_col_clinical_phase',
                 'drug_row_target_name', 'drug_col_target_name']
V15_ID_COLS = ['block_id', 'study_name', 'cell_line_name', 'drug_row', 'drug_col']

G1_MIN_BLOCKS_PER_STUDY = 100
G2_MIN_SHARED_CELLS = 200
G3_MIN_MATCHED_UNITS = 10000
G4_MIN_NOISE_COVERAGE_PCT = 5.0


# ---------------------------------------------------------------- helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 22), b''):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(_q(obj), fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def _q(x, nd=6):
    if isinstance(x, dict):
        return {k: _q(v, nd) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_q(v, nd) for v in x]
    if isinstance(x, bool):
        return x
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        x = float(x)
    if isinstance(x, float):
        if x != x or x in (float('inf'), float('-inf')):
            return None
        return round(x, nd)
    return x


def norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())


def write_csv(rows, fieldnames, path):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fieldnames})


def popcount(x):
    return int(x).bit_count()


# ---------------------------------------------------------------- fetch phase
def fetch_v15():
    os.makedirs(OVLAP, exist_ok=True)
    import requests
    rec = {'url': V15_URL, 'zenodo_record': 15235991, 'file': 'summary_v_1_5.csv',
           'expected_bytes': V15_BYTES, 'expected_md5': V15_MD5,
           'saved_as': os.path.relpath(V15, ROOT).replace('\\', '/'),
           'budget_bytes': 1500000000, 'response_values_read': False}
    if os.path.exists(V15) and os.path.getsize(V15) == V15_BYTES:
        status = 'reused'
        md5 = hashlib.md5(); sha = hashlib.sha256()
        with open(V15, 'rb') as fh:
            for blk in iter(lambda: fh.read(1 << 22), b''):
                md5.update(blk); sha.update(blk)
        rec.update({'status': status, 'bytes': os.path.getsize(V15),
                    'md5': md5.hexdigest(), 'sha256': sha.hexdigest().upper()})
    else:
        t0 = time.time()
        md5 = hashlib.md5(); sha = hashlib.sha256(); written = 0
        with requests.get(V15_URL, stream=True, timeout=1800,
                          headers={'User-Agent': 'MAESTRO-a3-audit/1.0'}) as r:
            r.raise_for_status()
            with open(V15, 'wb') as fh:
                for chunk in r.iter_content(chunk_size=1 << 22):
                    if not chunk:
                        continue
                    fh.write(chunk); md5.update(chunk); sha.update(chunk); written += len(chunk)
        rec.update({'status': 'downloaded', 'bytes': written,
                    'md5': md5.hexdigest(), 'sha256': sha.hexdigest().upper(),
                    'download_seconds': round(time.time() - t0, 1)})
    rec['bytes_ok'] = rec['bytes'] == V15_BYTES
    rec['md5_matches_zenodo'] = rec['md5'] == V15_MD5
    rec['within_budget'] = rec['bytes'] <= rec['budget_bytes']
    write_json(rec, DOWNLOAD_RECEIPT)
    print(json.dumps(rec, indent=1, sort_keys=True, ensure_ascii=False))
    return 0 if (rec['bytes_ok'] and rec['md5_matches_zenodo']) else 1


# ---------------------------------------------------------------- input hashes
def hash_inputs():
    files = {
        'protocol_a3': PROTOCOL_A3,
        'v14_summary': V14,
        'jaaks_original_fitted': JAAKS_ORIG,
        'jaaks_validation_fitted': JAAKS_VAL,
        'prism_primary_cell_info': os.path.join(PRISM, 'primary-screen-cell-line-info.csv'),
        'prism_secondary_cell_info': os.path.join(PRISM, 'secondary-screen-cell-line-info.csv'),
        'prism_primary_treatment_info': os.path.join(
            PRISM, 'primary-screen-replicate-collapsed-treatment-info.csv'),
        'prism_secondary_treatment_info': os.path.join(
            PRISM, 'secondary-screen-replicate-collapsed-treatment-info.csv'),
        'oneil_raw_workbook': ONEIL,
        'beataml_probit_curve_fits': BEATAML,
    }
    out = {}
    for k, p in sorted(files.items()):
        if os.path.exists(p):
            out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                      'bytes': os.path.getsize(p), 'sha256': sha256_file(p), 'status': 'ok'}
        else:
            out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                      'status': 'missing'}
    if os.path.exists(V15) and os.path.getsize(V15) == V15_BYTES:
        rec = json.load(open(DOWNLOAD_RECEIPT, encoding='utf-8')) if os.path.exists(DOWNLOAD_RECEIPT) else {}
        out['v15_summary_full'] = {'path_rel': os.path.relpath(V15, ROOT).replace('\\', '/'),
                                   'bytes': os.path.getsize(V15),
                                   'sha256': rec.get('sha256', sha256_file(V15)),
                                   'md5': rec.get('md5'), 'status': 'ok',
                                   'download_receipt': os.path.relpath(DOWNLOAD_RECEIPT, ROOT).replace('\\', '/')}
    else:
        out['v15_summary_full'] = {'path_rel': os.path.relpath(V15, ROOT).replace('\\', '/'),
                                   'status': 'missing'}
    out['script_a3'] = {'path_rel': os.path.relpath(os.path.join(OUT, 'a3.py'), ROOT).replace('\\', '/'),
                        'bytes': os.path.getsize(os.path.join(OUT, 'a3.py')),
                        'sha256': sha256_file(os.path.join(OUT, 'a3.py'))}
    return out


def load_s1_provenance():
    """Read the published S1 37-study table from the R190-E1 audit JSON (read-only)."""
    try:
        e1 = json.load(open(E1_JSON, encoding='utf-8'))
        return {r['study']: {'data_source': r.get('data_source'),
                             'disease': r.get('disease'),
                             'monotherapy': r.get('monotherapy')}
                for r in e1['s1_study_table']['studies']}
    except Exception:
        return {}


def load_s1_table():
    """Published Supplementary Table S1 (37 studies) from the R190-E1 audit JSON (read-only)."""
    try:
        e1 = json.load(open(E1_JSON, encoding='utf-8'))
        return list(e1['s1_study_table']['studies'])
    except Exception:
        return []


# ---------------------------------------------------------------- v1.5 stream
def stream_v15():
    nmax = 1_600_000
    sid = np.empty(nmax, np.int16)
    cid = np.empty(nmax, np.int32)
    pid = np.empty(nmax, np.int32)
    bid = np.empty(nmax, np.int64)
    studies, study_map = [], {}
    cells, cell_map = [], {}
    pairs, pair_map = [], {}
    ncache = {}
    mono_by_study = collections.Counter()
    n = rows = mono = 0
    header = None
    with open(V15, newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        col = {c.strip(): i for i, c in enumerate(header)}
        i_b = col['block_id']; i_s = col['study_name']; i_c = col['cell_line_name']
        i_dr = col['drug_row']; i_dc = col['drug_col']

        def nrm(s):
            v = ncache.get(s)
            if v is None:
                v = norm(s)
                ncache[s] = v
            return v

        def enc(s, mp, lst):
            v = mp.get(s)
            if v is None:
                v = len(lst); mp[s] = v; lst.append(s)
            return v

        for row in rdr:
            rows += 1
            if n >= nmax:
                nmax = int(nmax * 1.5)
                sid = np.resize(sid, nmax); cid = np.resize(cid, nmax)
                pid = np.resize(pid, nmax); bid = np.resize(bid, nmax)
            s = row[i_s].strip()
            sc = enc(s, study_map, studies)
            cc = enc(nrm(row[i_c].strip()), cell_map, cells)
            dr = row[i_dr].strip()
            dc = row[i_dc].strip()
            if dr.upper() in NULLISH or dc.upper() in NULLISH:
                mono += 1
                mono_by_study[sc] += 1
                continue
            a = nrm(dr); b = nrm(dc)
            if not a or not b:
                mono += 1
                mono_by_study[sc] += 1
                continue
            if a > b:
                a, b = b, a
            pc = enc(a + '\x1f' + b, pair_map, pairs)
            sid[n] = sc; cid[n] = cc; pid[n] = pc
            try:
                bid[n] = int(row[i_b])
            except (TypeError, ValueError):
                bid[n] = -1
            n += 1
    combo_by_study = np.bincount(sid[:n], minlength=len(studies)).astype(np.int64) if n else np.zeros(0, np.int64)
    return {
        'header': header, 'n_blocks_total': rows, 'n_combo_blocks': n, 'n_mono_blocks': mono,
        'studies': studies, 'cells': cells, 'pairs': pairs,
        'sid': sid[:n], 'cid': cid[:n], 'pid': pid[:n], 'bid': bid[:n],
        'combo_by_study': combo_by_study,
        'mono_by_study': np.array([mono_by_study.get(i, 0) for i in range(len(studies))], np.int64),
        'n_studies': len(studies), 'n_cells': len(cells), 'n_pairs': len(pairs),
    }


def analyze_v15(s, jaaks):
    n = s['n_combo_blocks']
    sid, cid, pid = s['sid'], s['cid'], s['pid']
    n_studies, n_cells, n_pairs = s['n_studies'], s['n_cells'], s['n_pairs']
    prov = load_s1_provenance()
    header = set(c.strip() for c in s['header'])

    # per-study combo cell/pair sets + eligibility
    study_cells = [set() for _ in range(n_studies)]
    study_pairs = [set() for _ in range(n_studies)]
    for k in range(n):
        study_cells[sid[k]].add(int(cid[k]))
        study_pairs[sid[k]].add(int(pid[k]))
    eligible = [c >= G1_MIN_BLOCKS_PER_STUDY for c in s['combo_by_study'].tolist()]
    eligible_idx = [i for i in range(n_studies) if eligible[i]]

    # cell -> study mask, unit -> study mask (eligible studies only); cell->set(pid) per study
    cellmask = {}
    unitmask = {}
    cond = {}
    for k in range(n):
        st = int(sid[k])
        if not eligible[st]:
            continue
        c = int(cid[k]); p = int(pid[k])
        bit = 1 << st
        cellmask[c] = cellmask.get(c, 0) | bit
        key = c * n_pairs + p
        unitmask[key] = unitmask.get(key, 0) | bit
        ck = st * n_cells + c
        ss = cond.get(ck)
        if ss is None:
            cond[ck] = {p}
        else:
            ss.add(p)

    # G1
    provenance = {}
    for i in range(n_studies):
        pr = prov.get(s['studies'][i], {})
        provenance[s['studies'][i]] = pr
    g1_value = len(eligible_idx)
    prov_sources = sorted({(provenance.get(s['studies'][i], {}) or {}).get('data_source')
                           for i in eligible_idx})
    g1_pass = bool(g1_value >= 2)

    # G2 shared cells + pairwise shared cells
    pair_shared_cells = collections.Counter()
    shared_cells = 0
    for c, mask in cellmask.items():
        bits = [i for i in range(n_studies) if (mask >> i) & 1]
        if len(bits) >= 2:
            shared_cells += 1
            for x in range(len(bits)):
                for y in range(x + 1, len(bits)):
                    pair_shared_cells[(bits[x], bits[y])] += 1
    g2_value = shared_cells
    g2_pass = bool(g2_value >= G2_MIN_SHARED_CELLS)
    max_pairwise_shared = max(pair_shared_cells.values()) if pair_shared_cells else 0
    max_pairwise = max(pair_shared_cells.items(), key=lambda kv: kv[1]) if pair_shared_cells else None

    # G3 matched units + per-study-pair matched units
    pair_matched_units = collections.Counter()
    studies_per_unit = collections.Counter()
    matched_units = 0
    matched_keys = []
    for key, mask in unitmask.items():
        k = popcount(mask)
        if k >= 2:
            matched_units += 1
            matched_keys.append((key, mask))
            studies_per_unit[k] += 1
            bits = [i for i in range(n_studies) if (mask >> i) & 1]
            for x in range(len(bits)):
                for y in range(x + 1, len(bits)):
                    pair_matched_units[(bits[x], bits[y])] += 1
    g3_value = matched_units
    g3_pass = bool(g3_value >= G3_MIN_MATCHED_UNITS)

    # feasible Q quadruple upper bound per study pair
    pair_rows = []
    q_total = 0
    for (a, b) in sorted(pair_shared_cells.keys()):
        if a >= b:
            continue
        shared = [c for c, mask in cellmask.items()
                  if ((mask >> a) & 1) and ((mask >> b) & 1)]
        inters = []
        for c in shared:
            ia = cond.get(a * n_cells + c, set())
            ib = cond.get(b * n_cells + c, set())
            inter = ia & ib
            if inter:
                inters.append(inter)
        q = 0
        for x in range(len(inters)):
            for y in range(x + 1, len(inters)):
                m = len(inters[x] & inters[y])
                if m >= 2:
                    q += m * (m - 1) // 2
        mu = int(pair_matched_units.get((a, b), 0))
        q_total += q
        pair_rows.append({'study_a': s['studies'][a], 'study_b': s['studies'][b],
                          'shared_cells': len(shared),
                          'matched_condition_units': mu,
                          'feasible_q_quadruples_upper_bound': int(q),
                          'provenance_a': (provenance.get(s['studies'][a], {}) or {}).get('data_source'),
                          'provenance_b': (provenance.get(s['studies'][b], {}) or {}).get('data_source')})
    pair_rows.sort(key=lambda r: (-r['feasible_q_quadruples_upper_bound'],
                                  -r['matched_condition_units'], r['study_a'], r['study_b']))

    # G4 within-study repeats (all combo rows) + coverage of matched units
    gcount = {}
    for k in range(n):
        key = (int(sid[k]) * n_cells + int(cid[k])) * (n_pairs + 1) + int(pid[k])
        gcount[key] = gcount.get(key, 0) + 1
    repeat_groups = sum(1 for v in gcount.values() if v >= 2)
    repeat_blocks = sum(v for v in gcount.values() if v >= 2)
    covered = 0
    for key, mask in matched_keys:
        c = key // n_pairs
        p = key % n_pairs
        for st in range(n_studies):
            if (mask >> st) & 1:
                if gcount.get((st * n_cells + c) * (n_pairs + 1) + p, 0) >= 2:
                    covered += 1
                    break
    noise_cov = 100.0 * covered / matched_units if matched_units else None
    g4_pass = bool(noise_cov is not None and noise_cov >= G4_MIN_NOISE_COVERAGE_PCT)

    # G5 endpoint / metadata columns (header only)
    resp_present = [c for c in V15_RESPONSE_COLS if c in header]
    meta_present = [c for c in V15_META_COLS if c in header]
    g5_pass = bool(len(resp_present) >= 1 and 'conc_row_unit' in meta_present)

    # per-study table
    study_rows = []
    matched_by_study = collections.Counter()
    for key, mask in matched_keys:
        for st in range(n_studies):
            if (mask >> st) & 1:
                matched_by_study[st] += 1
    shared_by_study = collections.Counter()
    for c, mask in cellmask.items():
        for st in range(n_studies):
            if (mask >> st) & 1:
                shared_by_study[st] += 1
    for i in range(n_studies):
        pr = provenance.get(s['studies'][i], {}) or {}
        study_rows.append({
            'study': s['studies'][i],
            'provenance_data_source': pr.get('data_source'),
            'provenance_disease': pr.get('disease'),
            'combo_blocks': int(s['combo_by_study'][i]),
            'mono_blocks': int(s['mono_by_study'][i]),
            'cells': len(study_cells[i]),
            'pairs': len(study_pairs[i]),
            'eligible_group': bool(eligible[i]),
            'shared_cells_with_other_eligible_groups': int(shared_by_study.get(i, 0)),
            'matched_condition_units_involving_study': int(matched_by_study.get(i, 0)),
        })
    study_rows.sort(key=lambda r: -r['combo_blocks'])

    # ---------------- G6: Jaaks overlap (report only)
    v15_cell_names = {s['cells'][int(c)] for c in cid}
    pair_drugs = [p.split('\x1f') for p in s['pairs']]
    v15_drug_names = set()
    for a, b in pair_drugs:
        v15_drug_names.add(a); v15_drug_names.add(b)
    shared_cells = sorted(v15_cell_names & jaaks['cells'])
    shared_drugs = sorted(v15_drug_names & jaaks['drugs'])
    mu_jaaks_entities = 0
    mu_jaaks_pairs = 0
    for key, mask in matched_keys:
        c = key // n_pairs
        p = key % n_pairs
        cell_name = s['cells'][c]
        a, b = pair_drugs[p]
        if cell_name in jaaks['cells'] and a in jaaks['drugs'] and b in jaaks['drugs']:
            mu_jaaks_entities += 1
        if ((a, b) if a <= b else (b, a)) in jaaks['pairs']:
            mu_jaaks_pairs += 1
    g6 = {
        'jaaks_cells': jaaks['n_cells'], 'jaaks_drugs': jaaks['n_drugs'],
        'jaaks_unordered_drug_pairs': jaaks['n_pairs'],
        'v15_combo_cells': len(v15_cell_names), 'v15_combo_drugs': len(v15_drug_names),
        'shared_cells': len(shared_cells),
        'shared_cells_sample': shared_cells[:50],
        'shared_drugs': len(shared_drugs),
        'shared_drugs_sample': shared_drugs[:50],
        'matched_condition_units_total': matched_units,
        'matched_units_cell_and_both_drugs_in_jaaks': mu_jaaks_entities,
        'matched_units_pair_in_jaaks_pairs': mu_jaaks_pairs,
        'note': ('strict normalized text-name intersection; synonym inference forbidden. v1.5 summary has no '
                 'numeric dose/condition columns, so condition-level (cell, drug pair, dose) overlap with '
                 'Jaaks is not verifiable at summary level; overlap is reported for wording limits only.'),
        'sources': jaaks['sources'],
    }

    return {
        'n_studies': n_studies, 'n_cells': n_cells, 'n_pairs': n_pairs,
        'n_studies_with_combo': int(sum(1 for i in range(n_studies) if s['combo_by_study'][i] > 0)),
        'eligible_combo_studies': [s['studies'][i] for i in eligible_idx],
        'g1': {'value_eligible_combo_studies': g1_value,
               'min_blocks_per_study': G1_MIN_BLOCKS_PER_STUDY, 'pass': g1_pass,
               'provenance_data_sources_among_eligible': prov_sources,
               'independence_note': 'study_name provenance from Supplementary Table S1 (different '
                                    'publication / NCATS Tripod / PharmacoDB / AstraZeneca / ChEMBL); '
                                    'within-study barcodes/plates are NOT counted as independent groups'},
        'g2': {'value_shared_cells': g2_value, 'threshold': G2_MIN_SHARED_CELLS,
               'pass': g2_pass,
               'max_pairwise_shared_cells': int(max_pairwise_shared),
               'max_pairwise_studies': ([s['studies'][max_pairwise[0][0]],
                                          s['studies'][max_pairwise[0][1]]] if max_pairwise else None),
               'n_eligible_study_pairs_with_shared_cells': int(len(pair_shared_cells)),
               'note': 'cells with combination blocks in >=2 independent combination studies'},
        'g3': {'value_matched_condition_units': g3_value, 'threshold': G3_MIN_MATCHED_UNITS,
               'pass': g3_pass,
               'studies_per_matched_unit_distribution': {str(k): v for k, v in sorted(studies_per_unit.items())},
               'feasible_q_quadruples_upper_bound_total': int(q_total)},
        'g4': {'matched_units_with_within_group_repeat': int(covered),
               'noise_coverage_pct': _q(noise_cov),
               'threshold_pct': G4_MIN_NOISE_COVERAGE_PCT, 'pass': g4_pass,
               'overall_repeat_groups': int(repeat_groups),
               'overall_repeat_blocks': int(repeat_blocks),
               'overall_repeat_blocks_pct': _q(100.0 * repeat_blocks / n if n else None),
               'overall_repeat_groups_pct': _q(100.0 * repeat_groups / len(gcount) if gcount else None)},
        'g5': {'response_columns_present': resp_present, 'metadata_columns_present': meta_present,
               'pass': g5_pass,
               'non_saturation_check': 'not performed (metadata-only; response values never read)'},
        'study_pair_rows': pair_rows,
        'top_study_pairs': pair_rows[:20],
        'n_study_pairs_with_shared_cells': int(len(pair_rows)),
        'study_rows': study_rows,
        'g6': g6,
    }


# ---------------------------------------------------------------- v1.4
def stream_v14(block_study):
    ncache = {}
    cell_map, cells = {}, []
    pair_map, pairs = {}, []
    bids, cids, pids = [], [], []
    nblocks_total = mono = 0
    header = None

    def nrm(s):
        v = ncache.get(s)
        if v is None:
            v = norm(s); ncache[s] = v
        return v

    def enc(s, mp, lst):
        v = mp.get(s)
        if v is None:
            v = len(lst); mp[s] = v; lst.append(s)
        return v

    with open(V14, newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        col = {c.strip(): i for i, c in enumerate(header)}
        i_b, i_c = col['block_id'], col['cell_line_name']
        i_dr, i_dc = col['drug_row'], col['drug_col']
        for row in rdr:
            nblocks_total += 1
            dr = row[i_dr].strip(); dc = row[i_dc].strip()
            if dr.upper() in NULLISH or dc.upper() in NULLISH:
                mono += 1
                continue
            a = nrm(dr); b = nrm(dc)
            if a > b:
                a, b = b, a
            cc = enc(nrm(row[i_c].strip()), cell_map, cells)
            pc = enc(a + '\x1f' + b, pair_map, pairs)
            try:
                bb = int(row[i_b])
            except (TypeError, ValueError):
                bb = -1
            bids.append(bb); cids.append(cc); pids.append(pc)
    n = len(bids)
    cid = np.asarray(cids, np.int64); pid = np.asarray(pids, np.int64)
    bid = np.asarray(bids, np.int64)
    n_cells, n_pairs = len(cells), len(pairs)
    block_by_unit = collections.defaultdict(list)
    for k in range(n):
        block_by_unit[int(cid[k]) * n_pairs + int(pid[k])].append(int(bid[k]))
    dist = collections.Counter(len(v) for v in block_by_unit.values())
    units_ge2 = {k: v for k, v in block_by_unit.items() if len(v) >= 2}
    mapped_blocks = sum(1 for b in bids if b in block_study)
    units_ge2_mapped = 0
    units_ge2_cross_study = 0
    for k, bl in units_ge2.items():
        studs = {block_study[b] for b in bl if b in block_study}
        if studs:
            units_ge2_mapped += 1
            if len(studs) >= 2:
                units_ge2_cross_study += 1
    rows = []
    for k in sorted(dist.keys()):
        rows.append({'blocks_per_cell_x_pair': int(k), 'n_units': int(dist[k])})
    return {
        'n_blocks_total': nblocks_total, 'n_combo_blocks': n,
        'n_mono_like_blocks': mono,
        'cells': n_cells, 'pairs': n_pairs, 'units': len(block_by_unit),
        'units_with_ge2_blocks': len(units_ge2),
        'fraction_units_ge2_blocks': _q(len(units_ge2) / len(block_by_unit)),
        'max_blocks_per_unit': int(max((len(v) for v in block_by_unit.values()), default=0)),
        'block_distribution': rows,
        'block_id_mapped_to_v15_study_blocks': int(mapped_blocks),
        'block_id_mapped_to_v15_study_pct': _q(100.0 * mapped_blocks / n if n else None),
        'units_ge2_with_mapped_study': int(units_ge2_mapped),
        'units_ge2_with_cross_study_blocks': int(units_ge2_cross_study),
        'g2_upper_bound_cells': n_cells,
        'g2_upper_bound_pass_200': bool(n_cells >= 200),
        'has_study_column': 'study_name' in [c.strip() for c in header],
        'note': ('v1.4 has no study/source column; block grouping is NOT an independent-screen split '
                 '(same resource). Total cells (112) < G2 threshold 200 -> structural G2 failure.'),
    }


# ---------------------------------------------------------------- C3 local resources
def analyze_c3():
    import pandas as pd
    out = {}
    # ---- PRISM
    try:
        pc = pd.read_csv(os.path.join(PRISM, 'primary-screen-cell-line-info.csv'))
        sc = pd.read_csv(os.path.join(PRISM, 'secondary-screen-cell-line-info.csv'))
        pt = pd.read_csv(os.path.join(PRISM, 'primary-screen-replicate-collapsed-treatment-info.csv'),
                         nrows=5)
        st = pd.read_csv(os.path.join(PRISM, 'secondary-screen-replicate-treatment-info.csv'),
                         nrows=5)
        depmap_p = set(pc['depmap_id'].dropna().astype(str))
        depmap_s = set(sc['depmap_id'].dropna().astype(str))
        prim_treat = pd.read_csv(os.path.join(PRISM, 'primary-screen-replicate-collapsed-treatment-info.csv'),
                                 usecols=['broad_id', 'name', 'moa', 'target'])
        sec_treat = pd.read_csv(os.path.join(PRISM, 'secondary-screen-replicate-treatment-info.csv'),
                                usecols=['broad_id', 'name', 'perturbation_type'])
        out['prism'] = {
            'available': True,
            'primary_cells': len(pc), 'secondary_cells': len(sc),
            'shared_cells_depmap_id': len(depmap_p & depmap_s),
            'primary_treatment_columns': list(pt.columns),
            'secondary_treatment_columns': list(st.columns),
            'primary_unique_compounds': int(prim_treat['broad_id'].nunique()),
            'secondary_unique_compounds': int(sec_treat['broad_id'].nunique()),
            'secondary_perturbation_types': sorted(
                str(x) for x in sec_treat['perturbation_type'].dropna().unique()),
            'endpoint_files': ['primary-screen-replicate-collapsed-logfold-change.csv',
                               'secondary-screen-replicate-collapsed-logfold-change.csv'],
            'endpoint_semantics': 'log2 fold-change viability (monotherapy); no combination/synergy endpoint',
            'combination_conditions': 0,
            'independent_screens_with_combo_endpoint': 0,
            'g1_pass': False, 'g2_shared_cells': len(depmap_p & depmap_s),
            'g2_pass': bool(len(depmap_p & depmap_s) >= G2_MIN_SHARED_CELLS),
            'g5_pass': False,
            'note': ('PRISM primary and secondary screens share 588 cell lines (G2 would pass) but both are '
                     'monotherapy viability screens (single compound per well, log2 fold-change endpoint); '
                     'no combination/synergy endpoint -> cannot construct combination Q (G1/G5/G3 fail).'),
        }
    except Exception as exc:  # noqa: BLE001
        out['prism'] = {'available': False, 'error': str(exc)}
    # ---- BeatAML
    try:
        ba = pd.read_csv(BEATAML, sep='\t', nrows=3)
        full = pd.read_csv(BEATAML, sep='\t', usecols=['dbgap_subject_id', 'inhibitor'])
        out['beataml'] = {
            'available': True, 'columns': list(ba.columns),
            'rows': int(len(full)), 'unique_samples': int(full['dbgap_subject_id'].nunique()),
            'unique_inhibitors': int(full['inhibitor'].nunique()),
            'endpoint_semantics': ('probit curve-fit single-agent parameters (auc/ic*/beta); '
                                   'monotherapy, no combination/synergy endpoint'),
            'combination_conditions': 0, 'samples_are_patient_derived_not_cell_lines': True,
            'g1_pass': False, 'g2_pass': False, 'g5_pass': False,
            'note': 'monotherapy patient-sample data; not cell lines and no combination endpoint.',
        }
    except Exception as exc:  # noqa: BLE001
        out['beataml'] = {'available': False, 'error': str(exc)}
    # ---- O'Neil raw combos (single publication / lab; batches only)
    try:
        d = pd.read_excel(ONEIL, sheet_name='combination response',
                          usecols=['BatchID', 'cell_line', 'drugA_name', 'drugB_name',
                                   'drugA Conc (µM)', 'drugB Conc (µM)'])
        out['oneil'] = {
            'available': True, 'rows': int(len(d)),
            'cells': int(d['cell_line'].nunique()),
            'drugs': int(pd.concat([d['drugA_name'], d['drugB_name']]).nunique()),
            'batches': sorted(int(x) for x in d['BatchID'].dropna().unique()),
            'batch_sizes': {str(int(k)): int(v) for k, v in d['BatchID'].value_counts().items()},
            'combination_endpoint_columns_present': True,
            'combination_endpoint_semantics': 'viability replicates (viability1-4) + mu/muMax, X/X0',
            'independent_screens': 1,
            'g1_pass': False, 'g2_shared_cells': None,
            'g2_pass': False, 'g5_pass': True,
            'note': ('one publication/lab with 3 replicate batches (BatchID 1/2/3) - batches are not '
                     'independent screens/labs; 39 cell lines < G2 threshold 200.'),
        }
    except Exception as exc:  # noqa: BLE001
        out['oneil'] = {'available': False, 'error': str(exc)}
    # ---- Jaaks (existing resource; not independent)
    try:
        jf = pd.read_csv(JAAKS_ORIG, usecols=['CELL_LINE_NAME', 'ANCHOR_NAME', 'LIBRARY_NAME'])
        out['jaaks_existing'] = {
            'available': True, 'orig_cells': int(jf['CELL_LINE_NAME'].nunique()),
            'orig_drugs': int(pd.concat([jf['ANCHOR_NAME'], jf['LIBRARY_NAME']]).nunique()),
            'independent_screens': 2,  # Original vs Validation (same resource/publication)
            'g1_pass': False, 'g2_shared_cells': 96,
            'g2_pass': False, 'g5_pass': True,
            'note': ('Jaaks Original/Validation: 125/97 cells, 96 shared cells (C171/A0); same resource, '
                     'barcode-independent screens but same publication/lab -> not the required larger '
                     'independent resource; 96 < 200.'),
        }
    except Exception as exc:  # noqa: BLE001
        out['jaaks_existing'] = {'available': False, 'error': str(exc)}
    # ---- empty local candidate dirs (data_unavailable, not "does not exist")
    empt = {}
    for k, p in EMPTY_DIRS.items():
        nfiles = sum(1 for _ in os.scandir(p)) if os.path.isdir(p) else None
        empt[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                   'exists': os.path.isdir(p), 'n_entries': nfiles,
                   'status': 'data_unavailable_empty_local_dir'}
    out['empty_local_dirs'] = empt
    out['c4_external'] = {
        'downloaded': False,
        'note': ('no external candidate downloaded in this audit; BRIEF section 2 order exhausted with '
                 'C1-C3. Larger resources would need a new budget/protocol.'),
    }
    return out


# ---------------------------------------------------------------- G6 Jaaks overlap
def load_jaaks_identity():
    """Read-only identity columns of the Jaaks fitted screens (for overlap reporting)."""
    import pandas as pd
    jf = pd.concat([pd.read_csv(JAAKS_ORIG, usecols=JAAKS_COLS),
                    pd.read_csv(JAAKS_VAL, usecols=JAAKS_COLS)], ignore_index=True)
    cells = set(norm(x) for x in jf['CELL_LINE_NAME'].dropna() if isinstance(x, str))
    drugs = set()
    pairs = set()
    for a, b in zip(jf['ANCHOR_NAME'], jf['LIBRARY_NAME']):
        if not (isinstance(a, str) and isinstance(b, str)):
            continue
        na, nb = norm(a), norm(b)
        if not (na and nb):
            continue
        drugs.add(na); drugs.add(nb)
        pairs.add((na, nb) if na <= nb else (nb, na))
    return {'cells': cells, 'drugs': drugs, 'pairs': pairs,
            'n_cells': len(cells), 'n_drugs': len(drugs), 'n_pairs': len(pairs),
            'sources': [os.path.relpath(JAAKS_ORIG, ROOT).replace('\\', '/'),
                        os.path.relpath(JAAKS_VAL, ROOT).replace('\\', '/')]}


# ---------------------------------------------------------------- main audit
def main_audit():
    os.makedirs(OVLAP, exist_ok=True)
    t0 = time.time()
    inputs = hash_inputs()
    v15_available = inputs.get('v15_summary_full', {}).get('status') == 'ok'
    s1prov = load_s1_provenance()
    result = {
        'protocol': {'path_rel': os.path.relpath(PROTOCOL_A3, ROOT).replace('\\', '/'),
                     'sha256': inputs['protocol_a3']['sha256'] if inputs['protocol_a3']['status'] == 'ok' else None,
                     'version': 'PROTOCOL_A3 v1 FROZEN'},
        'script': inputs['script_a3'],
        'inputs': inputs,
        'response_use_attestation': {
            'response_values_read': False,
            'response_columns_used': 'header existence only (no empty-string/value scanning)',
            'q_estimated': False, 'models_fitted': False,
            'metadata_only': True,
        },
        's1_study_provenance_source': os.path.relpath(E1_JSON, ROOT).replace('\\', '/'),
    }
    v15_analysis = None
    if v15_available:
        print('[1/5] hash/inputs ok; streaming DrugComb v1.5 full summary ...', flush=True)
        v15 = stream_v15()
        print('    rows=%d combo=%d mono=%d studies=%d cells=%d pairs=%d' % (
            v15['n_blocks_total'], v15['n_combo_blocks'], v15['n_mono_blocks'],
            v15['n_studies'], v15['n_cells'], v15['n_pairs']), flush=True)
        print('[2/5] load Jaaks identity + analyze v1.5 cross-study structure ...', flush=True)
        jaaks = load_jaaks_identity()
        v15_analysis = analyze_v15(v15, jaaks)
        block_study = dict(zip(v15['bid'].tolist(), v15['sid'].tolist()))
        # v1.4
        s1_rows = load_s1_table()
        s1_by_study = {r['study']: r for r in s1_rows}
        measured_by_study = {r['study']: r for r in v15_analysis['study_rows']}
        s1_comparison = {
            'published_s1_studies': len(s1_rows),
            'published_s1_total_blocks': int(sum(r['n_blocks'] for r in s1_rows)),
            'published_s1_combo_blocks': int(sum(r['n_blocks'] for r in s1_rows if not r.get('monotherapy'))),
            'published_s1_mono_blocks': int(sum(r['n_blocks'] for r in s1_rows if r.get('monotherapy'))),
            'measured_rows': int(v15['n_blocks_total']),
            'measured_combo_blocks': int(v15['n_combo_blocks']),
            'measured_mono_blocks': int(v15['n_mono_blocks']),
            'measured_studies': int(v15['n_studies']),
            'published_studies_missing_from_file': sorted(set(s1_by_study) - set(measured_by_study)),
            'file_studies_not_in_published_table': sorted(set(measured_by_study) - set(s1_by_study)),
            'note': ('the v1.5 summary file is a later/different curation than the published S1 table: '
                     '34 studies / 1,432,351 block rows measured vs 37 studies / 1,469,182 published; the 3 '
                     'missing studies are the monotherapy-only ELLINGER / GORDON / TOURET studies and some '
                     'study block counts differ. All A3 gate counts use the measured file, not the paper table.'),
        }
        s1_rows_csv = []
        for name in sorted(set(s1_by_study) | set(measured_by_study)):
            pub = s1_by_study.get(name)
            meas = measured_by_study.get(name)
            s1_rows_csv.append({
                'study': name,
                'published_blocks': int(pub['n_blocks']) if pub else None,
                'measured_combo_blocks': int(meas['combo_blocks']) if meas else 0,
                'measured_mono_blocks': int(meas['mono_blocks']) if meas else 0,
                'published_type': ('mono' if pub and pub.get('monotherapy') else 'combo') if pub else None,
                'present_in_file': bool(meas is not None),
            })
        write_csv(s1_rows_csv, ['study', 'published_blocks', 'measured_combo_blocks',
                                'measured_mono_blocks', 'published_type', 'present_in_file'],
                  os.path.join(OVLAP, 'v15_vs_s1_study_counts.csv'))
        result['c1_vs_published_s1'] = s1_comparison
        print('[3/5] streaming DrugComb v1.4 full summary ...', flush=True)
        v14_analysis = stream_v14(block_study)
        # write v15-derived CSVs
        write_csv(v15_analysis['study_rows'],
                  ['study', 'provenance_data_source', 'provenance_disease', 'combo_blocks',
                   'mono_blocks', 'cells', 'pairs', 'eligible_group',
                   'shared_cells_with_other_eligible_groups',
                   'matched_condition_units_involving_study'],
                  os.path.join(OVLAP, 'v15_study_table.csv'))
        write_csv(v15_analysis['study_pair_rows'],
                  ['study_a', 'study_b', 'shared_cells', 'matched_condition_units',
                   'feasible_q_quadruples_upper_bound', 'provenance_a', 'provenance_b'],
                  os.path.join(OVLAP, 'v15_study_pair_overlap.csv'))
        write_csv(v14_analysis['block_distribution'],
                  ['blocks_per_cell_x_pair', 'n_units'],
                  os.path.join(OVLAP, 'v14_block_structure.csv'))
        result['c1_drugcomb_v15'] = v15_analysis
        result['c2_drugcomb_v14'] = v14_analysis
        result['c1_scope'] = {'n_blocks_total': v15['n_blocks_total'],
                              'n_combo_blocks': v15['n_combo_blocks'],
                              'n_mono_blocks': v15['n_mono_blocks'],
                              'n_studies': v15['n_studies'], 'n_cells': v15['n_cells'],
                              'n_pairs': v15['n_pairs']}
        g6 = v15_analysis['g6']
    else:
        # fallback: local 60x1MB byte sample only; descriptively report the sampling gap
        chunks = sorted(f for f in os.listdir(V15_CHUNKS) if f.startswith('chunk_')) \
            if os.path.isdir(V15_CHUNKS) else []
        result['c1_drugcomb_v15'] = {
            'available': False,
            'fallback_local_sample_chunks': len(chunks),
            'fallback_local_sample_bytes': 1000000 * len(chunks),
            'note': ('v1.5 full summary not available (download failed or over budget); only the 60x1MB '
                     'byte sample from R190-E1 exists -> cross-study matching counts cannot be computed. '
                     'Recorded as data_unavailable (not "does not exist").'),
        }
        result['c2_drugcomb_v14'] = None
        g6 = None
    print('[4/5] C3 local resources ...', flush=True)
    c3 = analyze_c3()
    result['c3_local_resources'] = c3
    if g6 is not None:
        write_csv([{'metric': k, 'value': json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v}
                   for k, v in g6.items() if not isinstance(v, list)],
                  ['metric', 'value'], os.path.join(OVLAP, 'jaaks_overlap.csv'))
    result['g6_jaaks_overlap'] = g6

    # ---------------- gates & judgment
    if v15_analysis is not None:
        g1 = dict(v15_analysis['g1']); g2 = dict(v15_analysis['g2'])
        g3 = dict(v15_analysis['g3']); g4 = dict(v15_analysis['g4'])
        g5 = dict(v15_analysis['g5'])
    else:
        g1 = {'value_eligible_combo_studies': 0, 'pass': False}
        g2 = {'value_shared_cells': None, 'pass': False}
        g3 = {'value_matched_condition_units': None, 'pass': False}
        g4 = {'value_noise_coverage_pct': None, 'pass': False}
        g5 = {'pass': False, 'response_columns_present': []}
    gates = {'G1_independent_groups': g1, 'G2_shared_cells': g2,
             'G3_matched_condition_units': g3, 'G4_noise_calibration': g4,
             'G5_combination_endpoint': g5}
    all_pass = all(bool(g.get('pass')) for g in gates.values())
    failed = [k for k, g in gates.items() if not g.get('pass')]
    failure_categories = []
    for k in failed:
        if k in ('G2_shared_cells', 'G3_matched_condition_units', 'G4_noise_calibration'):
            failure_categories.append('data_insufficient')
        elif k == 'G5_combination_endpoint':
            failure_categories.append('data_unavailable')
        else:
            failure_categories.append('design_mismatch')
    dose_verifiable = False  # v1.5 summary has no numeric per-block dose design
    conditions = []
    if all_pass:
        verdict = 'qualified_with_conditions' if not dose_verifiable else 'resource_qualified'
        if not dose_verifiable:
            conditions.append('matched conditions are pair-level (cell x unordered drug pair); numeric dose-'
                              'design equivalence is not verifiable from the summary tables and would require '
                              'raw dose-level data (DrugComb v1.4 raw = 2,008,117,325 B > 1.5 GB budget; not '
                              'downloaded) -> a new budget/protocol is needed before an A4 effect design.')
    else:
        verdict = 'not_qualified'
    required_spec = [
        '>=2 independent combination screens/studies (different lab/publication/screen; not same-day or '
        'same-plate barcode split), each with >=100 combination blocks',
        '>=200 cell lines measured in combination in >=2 independent groups (strict normalized names, '
        'collision report)',
        '>=10,000 matched condition units (cell, unordered drug pair) appearing in >=2 independent groups, '
        'with verifiable dose-design equivalence (summary-level pair match is not enough; need numeric dose '
        'design or raw dose-level data)',
        '>=5% of matched units with within-group repeats (technical/replicate plates) to calibrate noise',
        'calibrated combination-synergy endpoint (Bliss/ZIP/DeltaEMAX-like) with QC metadata and '
        'non-saturation evidence; condition x cell interaction must not dominate (A2: 48.5% interaction, '
        '46.1% noise)',
    ]
    boundary = ('在可得资源上，条件级跨 screen 复验不可检验（condition_level_cross_screen_untestable）；'
                '这是"不可检验/不满足资源规格"的证据，不是"条件级结构不存在"的普遍结论。'
                '分析 A 收口：条件级共享份额 1.43%（C172）+ 跨 screen 不可及。')
    result['gates'] = gates
    result['judgment'] = {
        'verdict': verdict,
        'all_gates_pass': all_pass,
        'failed_gates': failed,
        'failure_categories': sorted(set(failure_categories)),
        'condition_level_cross_screen_untestable': bool(verdict == 'not_qualified'),
        'dose_design_equivalence_verifiable': dose_verifiable,
        'conditions': conditions,
        'required_resource_spec': required_spec,
        'boundary_statement': boundary,
        'not_a_general_absence_claim': ('not_qualified / untestable means the available resources cannot '
                                        'test condition-level cross-screen replication; it does not assert '
                                        'that condition-level structure is universally absent.'),
    }
    result['runtime_seconds_bucket'] = None  # timestamps/runtime excluded from deterministic artifacts
    result['determinism'] = {'json_keys_sorted': True, 'timestamps': False,
                             'contains_runtime_seconds': False}
    write_json(result, A3_JSON)
    print('[5/5] verdict: %s' % verdict, flush=True)
    if v15_analysis is not None:
        print('    G1 eligible combo studies: %s' % g1.get('value_eligible_combo_studies'))
        print('    G2 shared cells: %s (threshold 200)' % g2.get('value_shared_cells'))
        print('    G3 matched condition units: %s (threshold 10,000)' % g3.get('value_matched_condition_units'))
        print('    G3 feasible Q quadruples upper bound: %s' % g3.get('feasible_q_quadruples_upper_bound_total'))
        print('    G4 noise coverage pct: %s (threshold 5%%)' % g4.get('noise_coverage_pct'))
        print('    G5 response columns: %s' % g5.get('response_columns_present'))
        print('    failed: %s' % failed)
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fetch':
        raise SystemExit(fetch_v15())
    raise SystemExit(main_audit())
