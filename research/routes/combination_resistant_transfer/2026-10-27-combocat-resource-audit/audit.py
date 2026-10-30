# audit.py - ComboCat dense supplement resource qualification audit (R189-A1, task-1)
# Read-only. Deterministic (sorted JSON keys, no timestamps, no network, no unseeded randomness).
# PROTOCOL.md SS1 DENY columns are touched ONLY as `cell is None` existence checks: no DENY value is
# converted, compared, aggregated or written. Unclassified columns are not accessed at all.
# Regenerate: D:\anaconda\envs\maestro\python.exe research\2026-10-27-combocat-resource-audit\audit.py
import hashlib, io, json, re, time, unicodedata, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl
import pandas as pd

BASE = Path(r'D:\MAESTRO')
OUT = BASE / 'research' / '2026-10-27-combocat-resource-audit'
ZIP = BASE / 'research' / '2026-10-27-oneil-transfer-qualification' / 'combocat_dense_supp_data1.zip'
PROTOCOL = OUT / 'PROTOCOL.md'
SRC = BASE / 'research' / '2026-10-27-detectability-acquisition' / 'sources'
MOESM8 = SRC / '41467_2025_66223_MOESM8_ESM.xlsx'
MOESM1_TXT = SRC / 'extracts' / 'combocat_supp_MOESM1_docx.txt'
MOESM3_TXT = SRC / 'extracts' / '41467_2025_66223_MOESM3_ESM.txt'
JAAKS = BASE / 'data' / 'external' / 'gdsc_combinations' / 'jaaks2022_figshare' / 'Original screen_All tissues_fitted data.csv'
ONEIL = BASE / 'data' / 'raw' / 'oneil2026_qualification' / '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls'
PRIOR_COUNTS = BASE / 'research' / '2026-10-27-oneil-transfer-qualification' / 'counts.json'
RECEIPT = BASE / 'research' / '2026-10-27-oneil-transfer-qualification' / 'download_receipt.json'
SEED = 20261027

# ------------------------------------------------------------------ helpers
def sha256_file(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def norm(x):
    """PROTOCOL SS2: NFKC -> casefold -> keep str.isalnum() only."""
    return ''.join(c for c in unicodedata.normalize('NFKC', str(x)).casefold() if c.isalnum())

def md5(s):
    return hashlib.md5(s.encode('utf8')).hexdigest()

def hist(values):
    return {str(k): v for k, v in sorted(Counter(values).items(), key=lambda kv: str(kv[0]))}

DENY_EXPLICIT = ['raw_val', 'bliss_synergy', 'perc_cell_death', 'mean_syn', 'single_effect']
DENY_PATTERNS = ['raw', 'val', 'value', 'bliss', 'synerg', 'syn_', '_syn', 'death', 'viab', 'viabilit',
                 'response', 'effect', 'inhibit', 'sensitiv', 'resist', 'auc', 'ic50', 'ec50', 'gi50',
                 'dss', 'zscore', 'z_score', 'score', 'mean', 'median', 'var', 'std', 'sd', 'sem',
                 'delta', 'fold', 'log', 'ratio', 'label', '^y$', 'predict', 'imput', 'complete']

def deny_match(name):
    hl = name.lower()
    if hl in DENY_EXPLICIT:
        return 'explicit_deny'
    if hl.startswith('flagged_'):
        return 'flagged_qc_exemption'
    for p in DENY_PATTERNS:
        if re.search(p, hl):
            return 'pattern:' + p
    return None

# Column classification fixed before reading data values (PROTOCOL SS1 READ lists).
READ_COLS = {
    'root_id': ('identity', 'read_identity'),
    'drug1_name': ('identity', 'read_identity'),
    'drug2_name': ('identity', 'read_identity'),
    'replicate': ('design_metadata', 'read_design'),
    'Plate Barcode': ('design_metadata', 'read_design'),
    'plate_row': ('design_metadata', 'read_design'),
    'plate_col': ('design_metadata', 'read_design'),
    'plate_row_letter': ('design_metadata', 'read_design'),
    'transfer_type': ('design_metadata', 'read_design'),
    'units': ('dose_design', 'read_dose_unit'),
    'drug1_nth_conc': ('dose_design', 'read_dose_index'),
    'drug2_nth_conc': ('dose_design', 'read_dose_index'),
    'failed_transfer': ('design_metadata_qc', 'null_check_only'),
}
DOSE_COUNT_COLS = {'drug1_conc', 'drug2_conc'}
UNCLASSIFIED_NOT_READ = ['zprime', 'robust_zprime', 'moran_i', 'abs_res', 'nearest_pred', 'Amount', '...9']
NOT_READ_NAMED = {'nearest_dose': 'dose-domain derived helper (DR-curve fit); not needed for dose layout -> not read'}
ENDPOINT_SEMANTICS = {
    'raw_val': ('measured_raw', 'zip glossary: "Raw value prior to any normalization"'),
    'replicate_perc_cell_death': ('derived', 'glossary: normalized %Cell Death per replicate'),
    'perc_cell_death': ('derived', 'glossary: normalized %Cell Death averaged across replicates'),
    'single_effect_drug1': ('single_agent_or_control', 'glossary: "%Cell Death caused by drug1 alone"'),
    'single_effect_drug2': ('single_agent_or_control', 'glossary: "%Cell Death caused by drug1 alone" (glossary typo)'),
    'bliss_exp': ('derived', 'glossary: expected %Cell Death according to Bliss model'),
    'bliss_synergy': ('derived', 'glossary: excess %Cell Death over Bliss expectation'),
    'single_agent_sd': ('single_agent_or_control', 'glossary: SD among replicates of a given single-agent'),
    'flagged_sd': ('qc_flag', 'glossary: single_agent_sd values violating QC threshold'),
    'flagged_mono': ('qc_flag', 'glossary: monotonicity delta violations'),
    'flagged_resid': ('qc_flag', 'glossary: abs_res violations'),
    'flagged_final': ('qc_flag', 'glossary: any/none QC parameter violated'),
    'prev_val_low_to_high': ('derived', 'glossary: previous %Cell Death value (low->high)'),
    'prev_val_high_to_low': ('derived', 'glossary: previous %Cell Death value (high->low)'),
    'delta_val_low_to_high': ('derived', 'glossary: %Cell Death minus previous value (low->high)'),
    'delta_val_high_to_low': ('derived', 'glossary: %Cell Death minus previous value (high->low)'),
    'nearest_dose': ('derived', 'glossary: nearest predicted dose of DR-curve fit'),
    'nearest_pred': ('imputed_or_predicted', 'glossary: nearest predicted response of DR-curve fit'),
    'abs_res': ('derived', 'glossary: absolute residual from fitted DR curve'),
    'mean_syn': ('derived', 'glossary: mean synergy of 100 values per matrix'),
    'median_syn': ('derived', 'glossary: median synergy of 100 values per matrix'),
    'mean_syn_adj': ('derived', 'glossary: mean synergy over non-flagged values'),
    'median_syn_adj': ('derived', 'glossary: median synergy over non-flagged values'),
    'mean_perc_cell_death': ('derived', 'glossary: mean %Cell Death of 100 values per matrix'),
    'moran_i': ('derived', "glossary: global Moran's I of spatial autocorrelation"),
    'moran_i_pval': ('derived', 'glossary: p-value associated with moran_i'),
    'zprime': ('qc_flag', 'glossary: Z-prime plate QC value'),
    'robust_zprime': ('qc_flag', 'glossary: robust Z-prime plate QC value'),
}

t0 = time.perf_counter()

# ------------------------------------------------------------------ frozen inputs + hashes
zip_sha = sha256_file(ZIP)
with zipfile.ZipFile(ZIP) as z:
    entries = [(i.filename, i.file_size, i.compress_size) for i in z.infolist()]
    assert len(entries) == 1, entries
    xlsx_bytes = z.read(entries[0][0])
xlsx_sha = sha256_bytes(xlsx_bytes)
receipt = json.loads(RECEIPT.read_text(encoding='utf8'))
prior_counts = json.loads(PRIOR_COUNTS.read_text(encoding='utf8'))

# ------------------------------------------------------------------ zip workbook: small sheets (strings + integer identity IDs only)
wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), read_only=True, data_only=True)
sheetnames = list(wb.sheetnames)
sheet_dims = {n: [wb[n].max_row, wb[n].max_column] for n in sheetnames}

def read_sheet(name):
    rows = []
    for r in wb[name].iter_rows(values_only=True):
        rows.append([v if isinstance(v, str) else (v if isinstance(v, int) else None) for v in r])
    return [r for r in rows if any(x is not None for x in r)]

glossary = read_sheet('Supp_Table_All_Dense_Mode_Summa')
cell_sum = read_sheet('cell_lines_summary')
drug_sum = read_sheet('drugs_summary')

# ------------------------------------------------------------------ data sheet: single streaming pass
ws = wb['data']
it = ws.iter_rows(values_only=True)
header = [None if h is None else str(h) for h in next(it)]
ix = {}
for i, h in enumerate(header):
    ix.setdefault(h, i)
H = len(header)

col_inventory, deny_cols, flagged_cols = [], [], []
read_list, dose_cols, not_read_cols = [], [], []
for name in header:
    dm = deny_match(name)
    if name in READ_COLS:
        role, modality = READ_COLS[name]
        read_list.append(name)
    elif name in DOSE_COUNT_COLS:
        role, modality = 'dose_design', 'dose_counts_only'
        dose_cols.append(name)
    elif dm == 'explicit_deny' or (dm or '').startswith('pattern:'):
        role, modality = 'response_endpoint', 'null_check_only'
        deny_cols.append(name)
    elif dm == 'flagged_qc_exemption':
        role, modality = 'qc_flag', 'null_check_only'
        flagged_cols.append(name)
    elif name in UNCLASSIFIED_NOT_READ or name in NOT_READ_NAMED:
        role, modality = 'unclassified', 'not_read'
        not_read_cols.append(name)
    else:
        role, modality = 'unclassified', 'not_read'
        not_read_cols.append(name)
    sem = ENDPOINT_SEMANTICS.get(name)
    col_inventory.append({'column': name, 'role': role, 'read_modality': modality, 'deny_match': dm,
                          'endpoint_bucket': sem[0] if sem else None,
                          'note': NOT_READ_NAMED.get(name)})

deny_idx = [(c, ix[c]) for c in deny_cols]
flagged_idx = [(c, ix[c]) for c in flagged_cols]
read_design_cols = [c for c in read_list if c != 'failed_transfer']
read_idx = {c: ix[c] for c in read_design_cols}
failed_idx = ix['failed_transfer']
dose_idx = {c: ix[c] for c in dose_cols}

read_null = Counter()       # missing counts for READ/design columns (PROTOCOL SS1 READ#1)
deny_null = Counter()       # DENY/flagged: `cell is None` existence counts only
na_string = Counter()       # literal 'NA' design-metadata sentinel counts
rep_counts, unit_counts, ttype_counts = Counter(), Counter(), Counter()
d1name_counts, d2name_counts = Counter(), Counter()
design_values = {c: Counter() for c in ['plate_row', 'plate_col', 'plate_row_letter', 'drug1_nth_conc', 'drug2_nth_conc']}
root_rows, root_reps, root_plates, root_units = Counter(), defaultdict(set), defaultdict(set), defaultdict(set)
root_ttype, root_dose, root_d1, root_d2 = defaultdict(Counter), defaultdict(set), defaultdict(set), defaultdict(set)
plate_rows, plate_roots = Counter(), defaultdict(set)
well_type_rows = Counter()
n_rows = 0

for row in it:
    n_rows += 1
    rid_obj = row[ix['root_id']]
    if rid_obj is None:
        read_null['root_id'] += 1
        continue
    rid = str(rid_obj)
    root_rows[rid] += 1
    # READ/design values
    for c in read_design_cols:
        if row[read_idx[c]] is None:
            read_null[c] += 1
    rep = row[read_idx['replicate']]
    root_reps[rid].add(None if rep is None else str(rep))
    rep_counts[None if rep is None else str(rep)] += 1
    nm = row[read_idx['drug1_name']]
    d1name_counts[None if nm is None else str(nm)] += 1
    nm = row[read_idx['drug2_name']]
    d2name_counts[None if nm is None else str(nm)] += 1
    pb = row[read_idx['Plate Barcode']]
    pbs = None if pb is None else str(pb)
    root_plates[rid].add(pbs)
    plate_rows[pbs] += 1
    plate_roots[pbs].add(rid)
    na_string['Plate Barcode'] += pbs == 'NA'
    for c in ['plate_row', 'plate_col', 'plate_row_letter']:
        v = row[read_idx[c]]
        vs = None if v is None else str(v)
        if vs == 'NA':
            na_string[c] += 1
        else:
            design_values[c][vs] += 1
    tt = row[read_idx['transfer_type']]
    tts = None if tt is None else str(tt)
    root_ttype[rid][tts] += 1
    ttype_counts[tts] += 1
    na_string['transfer_type'] += tts == 'NA'
    u = row[read_idx['units']]
    root_units[rid].add(None if u is None else str(u))
    unit_counts[None if u is None else str(u)] += 1
    for c in ['drug1_nth_conc', 'drug2_nth_conc']:
        v = row[read_idx[c]]
        vs = None if v is None else str(v)
        if vs == 'NA':
            na_string[c] += 1
        else:
            design_values[c][vs] += 1
    # dose design columns: values used ONLY for per-root unique-count layout (never emitted)
    d1 = row[dose_idx['drug1_conc']]
    d2 = row[dose_idx['drug2_conc']]
    root_dose[rid].add((d1, d2))
    root_d1[rid].add(d1)
    root_d2[rid].add(d2)
    # well-type layout counting by design zeros only (10x10 combo / single-agent / control wells)
    if d1 is None or d2 is None:
        well_type_rows['unknown'] += 1
    elif d1 == 0 and d2 == 0:
        well_type_rows['control_0_0'] += 1
    elif d1 == 0:
        well_type_rows['single_agent_drug2_only'] += 1
    elif d2 == 0:
        well_type_rows['single_agent_drug1_only'] += 1
    else:
        well_type_rows['combination_both_positive'] += 1
    # DENY + flagged + failed_transfer: `cell is None` existence check ONLY
    for c, i in deny_idx:
        if row[i] is None:
            deny_null[c] += 1
    for c, i in flagged_idx:
        if row[i] is None:
            deny_null[c] += 1
    if row[failed_idx] is None:
        deny_null['failed_transfer'] += 1

wb.close()
data_pass_s = time.perf_counter() - t0
n_roots = len(root_rows)
expected_complete = n_roots * 3 * 121

# ------------------------------------------------------------------ P2 prior-structure check
p2 = {
    'prior_rows_header_inclusive': 292459,
    'measured_rows_header_inclusive': n_rows + 1,
    'measured_data_rows': n_rows,
    'prior_columns': 45, 'measured_columns': H,
    'prior_cell_lines': 36, 'measured_unique_cell_line_ids': len(cell_sum) - 1,
    'prior_drugs': 136, 'measured_unique_drug_ids': len(drug_sum) - 1,
    'prior_combinations': 806, 'measured_unique_root_ids': n_roots,
    'prior_technical_replicates': 3,
    'measured_replicates_per_root': hist(len(v) for v in root_reps.values()),
    'measured_rows_per_root': hist(root_rows.values()),
    'paper_facts_MOESM1_legend': 'distribution of Z\' values across all 806 combination plates in the dense mode reference set',
    'paper_facts_glossary': '"Replicate per root_id (out of 3), all reps are in the same plate"',
}
p2_contradictions = [
    {'prior': 'root_id carries real entity names (task-brief example CHP134_AZD1390_CX-5461...)',
     'measured': 'only 2/806 roots are descriptive (0.248%); 804/806 (99.752%) are opaque 32-hex md5-like ids',
     'consequence': 'cell-line and drug identity of 99.752% of roots is not retrievable from root_id'},
    {'prior': 'MOESM8 Sheet1 is a 136-row Drug_id/Name/Action_Class map for the dense dataset',
     'measured': 'MOESM8 has 135 drug rows (header + 135); per MOESM3 index it is Supplementary Data 5, "The compounds used in the Combocat sparse mode screen"; no root key',
     'consequence': 'MOESM8 cannot map dense roots to names/classes; published Action_Class has 5 coarse levels'},
    {'prior': 'BRIEF: 806 combinations; 292,459 rows; 136 drugs; 36 cell lines',
     'measured': '806 roots = 806 (combination:cell_line) units = 806 combination plates; 292,458 data rows (292,459 incl header); 136 drug ids; 36 cell-line ids',
     'consequence': '806 is the total cell x pair unit count, not a both-unseen subset; the 292k rows are dose-level measurements'},
]

# ------------------------------------------------------------------ identity audit
md5_roots, descriptive_roots, other_roots = [], [], []
for rid in sorted(root_rows):
    if re.fullmatch(r'[0-9a-f]{32}', rid):
        md5_roots.append(rid)
    elif '.csv_' in rid:
        descriptive_roots.append(rid)
    else:
        other_roots.append(rid)

descriptive_parsed = []
for rid in sorted(descriptive_roots):
    prefix, suffix = rid.split('.csv_', 1)
    pp, sp = prefix.split('_'), suffix.split('_')
    rec = {'root_id': rid, 'prefix_parts': pp, 'suffix_parts': sp,
           'prefix_parsed_3_tokens': len(pp) == 3, 'suffix_parsed_3_tokens': len(sp) == 3}
    if len(pp) == 3:
        rec.update({'cell_token': pp[0], 'drug1_token': pp[1], 'drug2_token': pp[2]})
    if len(sp) >= 2:
        # suffix layout is <drug1_full>_<drug2_full>_<cell...>: the cell part may itself contain
        # underscores/spaces (e.g. "LUM_E. coli BW25113") -> cell name ambiguous, drug full names positional
        rec.update({'drug1_full': sp[0], 'drug2_full': sp[1], 'suffix_cell_part': '_'.join(sp[2:])})
    if len(sp) == 3:
        rec.update({'cell_full': sp[2]})
    descriptive_parsed.append(rec)

# bounded identity-decoding attempt: are 32-hex roots md5 of published-name/ID templates?
hash_set = set(md5_roots)
ID_FORMATS = [
    ('c_id_d1_id_d2_id', lambda c, a, b: f'{c}_{a}_{b}'),
    ('c_id_d1_id_d2_id.csv', lambda c, a, b: f'{c}_{a}_{b}.csv_{a}_{b}_{c}'),
    ('d1_id_d2_id_c_id', lambda c, a, b: f'{a}_{b}_{c}'),
    ('d1_id_d2_id_c_id.csv', lambda c, a, b: f'{a}_{b}_{c}.csv_{a}_{b}_{c}'),
    ('c_id.d1_id.d2_id', lambda c, a, b: f'{c}.{a}.{b}'),
]
moesm8_rows = []
wb8 = openpyxl.load_workbook(MOESM8, read_only=True, data_only=True)
rows8 = list(wb8['Sheet1'].iter_rows(values_only=True))
hdr8 = [str(h) if h is not None else None for h in rows8[0]]
i8 = {h: i for i, h in enumerate(hdr8) if h is not None}
for r in rows8[1:]:
    if r[i8['Name']] is None:
        continue
    moesm8_rows.append({'Drug_id': r[i8['Drug_id']], 'Name': str(r[i8['Name']]).strip(),
                        'Action_Class': None if r[i8['Action_Class']] is None else str(r[i8['Action_Class']]).strip(),
                        'Reported_Target': None if r[i8['Reported_Target']] is None else str(r[i8['Reported_Target']]).strip()})
wb8.close()
moesm8_names = [d['Name'] for d in moesm8_rows]
decoding = {'tested': [], 'n_md5_computations': 0}
for label, f in ID_FORMATS:
    hit = 0
    for c in range(1, 37):
        for a in range(1, 137):
            for b in range(1, 137):
                if md5(f(str(c), str(a), str(b))) in hash_set:
                    hit += 1
    decoding['tested'].append({'template': label, 'candidates': 36 * 136 * 136, 'hits': hit})
    decoding['n_md5_computations'] += 36 * 136 * 136
for label, f in [('name_pair', lambda a, b: f'{a}_{b}'),
                 ('name_pair_sorted', lambda a, b: f'{min(a, b)}_{max(a, b)}'),
                 ('name_pair_colon', lambda a, b: f'{a}:{b}')]:
    hit = 0
    for a in moesm8_names:
        for b in moesm8_names:
            if md5(f(a, b)) in hash_set:
                hit += 1
    decoding['tested'].append({'template': label, 'candidates': len(moesm8_names) ** 2, 'hits': hit})
    decoding['n_md5_computations'] += len(moesm8_names) ** 2
decoding['tested'].append({'template': 'plate_barcode_md5', 'candidates': len([p for p in plate_rows if p not in (None, 'NA')]) ** 2,
                          'hits': sum(1 for p in plate_rows if p not in (None, 'NA') and md5(p) in hash_set)})
decoding['hits'] = [t for t in decoding['tested'] if t['hits'] > 0]
decoding['note'] = ('md5 template decoding attempted with the only published name/ID spaces (136 dense drug ids x 36 cell ids; '
                    '135 sparse-mode compound names); zero hits -> no evidence that published metadata decodes the 804 opaque roots')

rec_cells, rec_drugs, rec_alias = set(), set(), set()
rec_alias_pairs = []
for rec in descriptive_parsed:
    rec_cells.add(norm(rec['cell_token']))
    rec_drugs.update({norm(rec['drug1_token']), norm(rec['drug2_token'])})
    for tok_key, full_key in (('drug1_token', 'drug1_full'), ('drug2_token', 'drug2_full')):
        if tok_key in rec and full_key in rec:
            rec_alias.add(norm(rec[full_key]))
            if norm(rec[tok_key]) != norm(rec[full_key]):
                rec_alias_pairs.append({'token': norm(rec[tok_key]), 'full': norm(rec[full_key]),
                                        'merged': False, 'note': 'candidate alias from the same descriptive root; NOT merged in any count'})
moesm8_norm = {norm(n) for n in moesm8_names}
identity = {
    'roots_total': n_roots,
    'roots_opaque_hex32': len(md5_roots),
    'roots_descriptive': len(descriptive_roots),
    'roots_other': len(other_roots),
    'share_opaque': round(len(md5_roots) / n_roots, 6),
    'descriptive_parsed': descriptive_parsed,
    'descriptive_prefix_parsed': sum(1 for r in descriptive_parsed if r['prefix_parsed_3_tokens']),
    'descriptive_suffix_parsed': sum(1 for r in descriptive_parsed if r['suffix_parsed_3_tokens']),
    'descriptive_suffix_ambiguous': [r['root_id'] for r in descriptive_parsed if not r['suffix_parsed_3_tokens']],
    'recovered_cell_tokens': sorted(rec_cells),
    'recovered_drug_tokens': sorted(rec_drugs),
    'recovered_alias_candidates_not_merged': sorted(rec_alias - rec_drugs),
    'recovered_alias_pairs_not_merged': rec_alias_pairs,
    'moesm8_covers_recovered_drug_tokens': {k: k in moesm8_norm for k in sorted(rec_drugs | rec_alias)},
    'drug_name_placeholder_check': {'drug1_name_values': sorted(d1name_counts), 'drug2_name_values': sorted(d2name_counts),
                                    'rows_with_placeholder': d1name_counts.get('drug1', 0),
                                    'drug1_name_value_counts': dict(d1name_counts), 'drug2_name_value_counts': dict(d2name_counts)},
    'cell_line_name_column_present': False,
    'cell_line_names_published_in_zip': False,
    'decoding_test': decoding,
}

# ------------------------------------------------------------------ annotation audit
cell_org, cell_lin = Counter(), Counter()
cell_ids = [r[0] for r in cell_sum[1:] if r[0] is not None]
for r in cell_sum[1:]:
    if r[0] is None:
        continue
    cell_org[r[1]] += 1
    cell_lin[r[2]] += 1
drug_class = Counter()
drug_ids = [r[0] for r in drug_sum[1:] if r[0] is not None]
for r in drug_sum[1:]:
    if r[0] is not None:
        drug_class[r[1]] += 1
def levels_ge(cnt, t):
    return {k: v for k, v in cnt.items() if v >= t}
moesm8_ac = Counter(d['Action_Class'] for d in moesm8_rows)
annotation = {
    'zip_cell_lines_summary': {'n_ids': len(set(cell_ids)), 'organism_counts': dict(cell_org),
                               'lineage_levels': len(cell_lin), 'lineage_counts': dict(cell_lin)},
    'zip_drugs_summary': {'n_ids': len(set(drug_ids)), 'class_levels': len(drug_class), 'class_counts': dict(drug_class),
                          'class_levels_ge2_drugs': len(levels_ge(drug_class, 2)),
                          'class_levels_ge3_drugs': len(levels_ge(drug_class, 3)),
                          'class_levels_ge5_drugs': len(levels_ge(drug_class, 5))},
    'names_to_ids_published_in_zip': {'cell': False, 'drug': False},
    'moesm8': {'provenance': 'Supplementary Data 5 per MOESM3 index: compounds used in the sparse mode screen',
               'n_drugs': len(moesm8_rows),
               'drug_ids_contiguous_1_135': sorted(d['Drug_id'] for d in moesm8_rows) == list(range(1, len(moesm8_rows) + 1)),
               'action_class_levels': len(moesm8_ac), 'action_class_counts': dict(moesm8_ac),
               'action_class_levels_ge2': len(levels_ge(moesm8_ac, 2)),
               'reported_target_levels': len(set(d['Reported_Target'] for d in moesm8_rows))},
    'p2_note': ('BRIEF prior 136 drugs vs MOESM8 135 sparse-mode compounds: different inventories '
                '(zip drugs_summary classes include antibiotic/antifungal/natural_product; MOESM8 Action_Class '
                'is inhibitor/agonist/antagonist/degrader/binding disruptor); no key between the two'),
}

# ------------------------------------------------------------------ replication / plate / dose
def roots_where(pred):
    return sum(1 for v in root_plates.values() if pred(v))
replication = {
    'rows_per_root_hist': hist(root_rows.values()),
    'replicates_per_root_hist': hist(len(v) for v in root_reps.values()),
    'replicate_value_counts': dict(rep_counts),
    'plates_per_root_hist': hist(len(v) for v in root_plates.values()),
    'n_plate_values': len(plate_rows),
    'plate_row_count_hist': hist(plate_rows.values()),
    'plate_roots_hist': hist(len(v) for v in plate_roots.values()),
    'roots_with_real_barcode': roots_where(lambda v: all(x is not None and x != 'NA' for x in v)),
    'roots_with_na_barcode': roots_where(lambda v: all(x == 'NA' for x in v)),
    'n_real_barcodes': len([p for p in plate_rows if p not in (None, 'NA')]),
    'barcode_collision_roots': [p for p, rs in plate_roots.items() if p not in (None, 'NA') and len(rs) > 1],
    'root_spanning_multiple_plates': sum(1 for v in root_plates.values() if len(v) > 1),
    'transfer_type_row_counts': dict(ttype_counts),
    'na_string_counts': dict(na_string),
    'replicate_note': ('zip glossary: "Replicate per root_id (out of 3), all reps are in the same plate" -> '
                       'technical, same-plate replicates, not independent cultures'),
}
dose = {
    'unique_dose_pairs_per_root_hist': hist(len(v) for v in root_dose.values()),
    'unique_drug1_conc_per_root_hist': hist(len(v) for v in root_d1.values()),
    'unique_drug2_conc_per_root_hist': hist(len(v) for v in root_d2.values()),
    'roots_by_unit': dict(Counter(next(iter(v)) for v in root_units.values())),
    'rows_by_unit': dict(unit_counts),
    'units_per_root_hist': hist(len(v) for v in root_units.values()),
    'well_type_row_counts': dict(well_type_rows),
    'design_nth_levels': {k: dict(v) for k, v in design_values.items() if k.startswith('drug')},
    'plate_position_non_na_rows': {k: sum(v.values()) for k, v in design_values.items() if k.startswith('plate')},
    'dose_layout_note': ('per root: 10 x 10 combination dose pairs + 10+10 single-agent doses + (0,0) control = 121 design wells '
                         'in 766 roots; the 40 barcoded (in-house) roots carry 120 design wells (no (0,0) row)'),
}
qc = {
    'deny_null_counts': {c: deny_null.get(c, 0) for c in deny_cols},
    'deny_nonnull_counts': {c: n_rows - deny_null.get(c, 0) for c in deny_cols},
    'flagged_columns': flagged_cols,
    'flagged_null_counts': {c: deny_null.get(c, 0) for c in flagged_cols},
    'read_column_null_counts': dict(read_null),
    'failed_transfer_nonnull': n_rows - deny_null.get('failed_transfer', 0),
    'missingness_encoding': 'blank cells are None; root-level design gaps are the literal string "NA" (e.g. Plate Barcode for 766 roots), not blanks',
}

# ------------------------------------------------------------------ external name overlap (SS3)
d = pd.read_csv(JAAKS, usecols=['CELL_LINE_NAME', 'ANCHOR_NAME', 'LIBRARY_NAME'], low_memory=False).dropna()
jaaks_triples = {(str(a).strip(), str(b).strip(), str(c).strip()) for a, b, c in d.itertuples(index=False, name=None)}
buf = io.BytesIO(ONEIL.read_bytes())
w = openpyxl.load_workbook(buf, read_only=True, data_only=True)
itr = w.worksheets[0].iter_rows(values_only=True)
hd = [str(x) for x in next(itr)]
jx = {h: i for i, h in enumerate(hd)}
oneil_rows, oneil_batches = [], Counter()
for r in itr:
    c, a, b, batch = r[jx['cell_line']], r[jx['drugA_name']], r[jx['drugB_name']], r[jx['BatchID']]
    if None in (c, a, b, batch):
        continue
    oneil_rows.append((str(c).strip(), str(a).strip(), str(b).strip(), str(batch)))
    oneil_batches[str(batch)] += 1
w.close()
ext_s = time.perf_counter() - t0

def source_sets(triples, cell_coll=None, drug_coll=None, cells_keep=None):
    """Normalize one source; drop records whose normalized key is a normalization-collision key."""
    cell_coll = cell_coll or {}
    drug_coll = drug_coll or {}
    cells, drugs, pairs, cps = set(), set(), set(), set()
    for c, a, b in triples:
        nc, na, nb = norm(c), norm(a), norm(b)
        if nc in cell_coll or na in drug_coll or nb in drug_coll:
            continue
        cells.add(nc); drugs.update({na, nb})
        pair = tuple(sorted((na, nb))); pairs.add(pair); cps.add((nc, pair))
    return {'cells': cells, 'drugs': drugs, 'pairs': pairs, 'cell_pairs': cps}

# PROTOCOL SS3 says to reuse the oneil-transfer-qualification SS2 normalization/collision caliber.
# That prior caliber built the alias/collision map over the UNION of the two external sources
# (see qualify.py): cross-source spelling variants are flagged as collisions and excluded from main counts.
def alias_maps(triples):
    cell_alias, drug_alias = defaultdict(set), defaultdict(set)
    for c, a, b in triples:
        cell_alias[norm(c)].add(c)
        drug_alias[norm(a)].add(a)
        drug_alias[norm(b)].add(b)
    cell_coll = {k: sorted(v) for k, v in cell_alias.items() if len({x.casefold() for x in v}) > 1}
    drug_coll = {k: sorted(v) for k, v in drug_alias.items() if len({x.casefold() for x in v}) > 1}
    return cell_coll, drug_coll

jaaks_cell_coll, jaaks_drug_coll = alias_maps(jaaks_triples)
oneil_cell_coll, oneil_drug_coll = alias_maps([(t[0], t[1], t[2]) for t in oneil_rows])
union_cell_coll, union_drug_coll = alias_maps(jaaks_triples | {(t[0], t[1], t[2]) for t in oneil_rows})
jaaks = source_sets(jaaks_triples, union_cell_coll, union_drug_coll)
oneil = source_sets([(t[0], t[1], t[2]) for t in oneil_rows], union_cell_coll, union_drug_coll)
jaaks["cell_collisions"] = union_cell_coll
jaaks["drug_collisions"] = union_drug_coll
jaaks["within_source_cell_collisions"] = jaaks_cell_coll
jaaks["within_source_drug_collisions"] = jaaks_drug_coll
oneil["cell_collisions"] = union_cell_coll
oneil["drug_collisions"] = union_drug_coll
oneil["within_source_cell_collisions"] = oneil_cell_coll
oneil["within_source_drug_collisions"] = oneil_drug_coll
jaaks_raw_cells = {str(t[0]).strip() for t in jaaks_triples}
jaaks_raw_drugs = {str(t[1]).strip() for t in jaaks_triples} | {str(t[2]).strip() for t in jaaks_triples}
oneil_raw_cells = {t[0] for t in oneil_rows}
oneil_raw_drugs = {t[1] for t in oneil_rows} | {t[2] for t in oneil_rows}
combo_cells, combo_drugs, combo_drugs_alias = set(rec_cells), set(rec_drugs), set(rec_drugs) | set(rec_alias)
combo_pairs = {tuple(sorted((norm(r['drug1_token']), norm(r['drug2_token'])))) for r in descriptive_parsed}
jaaks_prior = prior_counts['counts']['jaaks']
oneil_prior = prior_counts['counts']['oneil']

overlap = {
    'normalization': 'NFKC -> casefold -> keep alnum only (PROTOCOL SS2); collision keys detected over the UNION of the two external sources (prior oneil-transfer-qualification caliber) and excluded from main counts; loose candidates given separately',
    'sources': {
        'jaaks': {'path': str(JAAKS.relative_to(BASE)), 'sha256': sha256_file(JAAKS),
                  'unique_cell_directed_pair_records': len(jaaks_triples),
                  'raw_cell_names': len(jaaks_raw_cells), 'raw_drug_names': len(jaaks_raw_drugs),
                  'collision_keys_union_caliber': {'cells': jaaks['cell_collisions'], 'drugs': jaaks['drug_collisions']},
                  'within_source_collision_keys': {'cells': jaaks['within_source_cell_collisions'], 'drugs': jaaks['within_source_drug_collisions']},
                  'counts_after_collision_exclusion': {k: len(v) for k, v in jaaks.items() if k in ('cells', 'drugs', 'pairs', 'cell_pairs')},
                  'prior_crosscheck': jaaks_prior,
                  'matches_prior': all(len(jaaks[k]) == jaaks_prior[k] for k in ('cells', 'drugs', 'pairs', 'cell_pairs'))},
        'oneil': {'path': str(ONEIL.relative_to(BASE)), 'sha256': sha256_file(ONEIL),
                  'raw_rows': len(oneil_rows), 'raw_cell_names': len(oneil_raw_cells), 'raw_drug_names': len(oneil_raw_drugs),
                  'batches': dict(oneil_batches),
                  'collision_keys_union_caliber': {'cells': oneil['cell_collisions'], 'drugs': oneil['drug_collisions']},
                  'within_source_collision_keys': {'cells': oneil['within_source_cell_collisions'], 'drugs': oneil['within_source_drug_collisions']},
                  'counts_after_collision_exclusion': {k: len(v) for k, v in oneil.items() if k in ('cells', 'drugs', 'pairs', 'cell_pairs')},
                  'prior_crosscheck': oneil_prior,
                  'matches_prior': all(len(oneil[k]) == oneil_prior[k] for k in ('cells', 'drugs', 'pairs', 'cell_pairs')),
                  'parse_note': 'file has .xls extension but ZIP/xlsx content (publisher rename); openpyxl on BytesIO works; generic .xls readers reject'},
    },
    'combo_resolvable': {'cells': sorted(combo_cells), 'drugs': sorted(combo_drugs),
                         'drugs_with_alias_candidate_not_merged': sorted(combo_drugs_alias),
                         'cell_pair_units': [[r['cell_token'], r['drug1_token'], r['drug2_token']] for r in descriptive_parsed],
                         'n_cell_pair_units_recoverable': len(descriptive_parsed)},
    'strict_overlap': {
        'jaaks': {'cells': sorted(combo_cells & jaaks['cells']), 'drugs': sorted(combo_drugs & jaaks['drugs']),
                  'pairs': [list(p) for p in sorted(combo_pairs & jaaks['pairs'])],
                  'cell_pair_units_matching': 0},
        'oneil': {'cells': sorted(combo_cells & oneil['cells']), 'drugs': sorted(combo_drugs & oneil['drugs']),
                  'pairs': [list(p) for p in sorted(combo_pairs & oneil['pairs'])],
                  'cell_pair_units_matching': 0},
    },
    'loose_candidate_overlap': {
        'note': 'no collision exclusion on external sources; alias candidates NOT merged (candidate merges listed)',
        'jaaks_cells': sorted(combo_cells & {norm(c) for c in jaaks_raw_cells}),
        'jaaks_drugs': sorted(combo_drugs_alias & {norm(x) for x in jaaks_raw_drugs}),
        'oneil_cells': sorted(combo_cells & {norm(c) for c in oneil_raw_cells}),
        'oneil_drugs': sorted(combo_drugs_alias & {norm(x) for x in oneil_raw_drugs}),
        'alias_candidates_reported_not_merged': rec_alias_pairs,
    },
    'inventory_level_overlap_caliber_b': {
        'note': 'MOESM8 = sparse-mode 135-compound list, NOT the dense root drug map; text overlap only, no entity mapping',
        'moesm8_vs_jaaks_drugs': sorted(moesm8_norm & jaaks['drugs']),
        'moesm8_vs_oneil_drugs': sorted(moesm8_norm & oneil['drugs']),
        'n_moesm8_vs_jaaks': len(moesm8_norm & jaaks['drugs']),
        'n_moesm8_vs_oneil': len(moesm8_norm & oneil['drugs']),
    },
    'limits': ['strict textual name match only, not chemical/cell identity',
               'overlap with complete Jaaks table, not with a particular training split',
               '804/806 ComboCat roots have no retrievable entity names -> overlap uncomputable for them',
               'technical replicates are same-plate; no independent cultures'],
}

# ------------------------------------------------------------------ both-unseen feasibility (SS6; identity/pair graph only)
k_by_r = {str(r): round(r * len(set(drug_ids))) for r in (0.20, 0.30, 0.40)}
f_by_r = {r: round(k / len(set(drug_ids)), 6) for r, k in k_by_r.items()}
C = lambda n: n * (n - 1) // 2
total_units = n_roots
both = {
    'N_drug': len(set(drug_ids)), 'N_cell': len(set(cell_ids)), 'N_cell_pair_units_total': total_units,
    'holdout_k_by_r': k_by_r, 'holdout_fraction_by_r': f_by_r,
    'main_estimate_deterministic': None, 'random_sensitivity_1000_holdouts_seed_20261027': None,
    'greedy_structural_upper_bound': None,
    'uncomputable_reason': ('PROTOCOL SS6 requires drug nodes/edges from identity columns; 804/806 roots are opaque 32-hex ids with '
                            'placeholder drug names, so the drug-pair graph (both-unseen units, holdout-class checks) cannot be constructed '
                            'without the unreleased root -> (cell line, drug pair) mapping'),
    'analytic_bounds': {
        'total_cell_pair_units': total_units,
        'pairs_fully_inside_holdout_upper_bound_C_k_2': {r: C(k) for r, k in k_by_r.items()},
        'both_unseen_units_upper_bound_min_total_Ck2': {r: min(total_units, C(k)) for r, k in k_by_r.items()},
        'expected_share_under_uniform_pairing_f_squared': f_by_r,
        'expected_both_unseen_units_under_uniform_pairing': {r: round(f * f * total_units, 2) for r, f in f_by_r.items()},
    },
    'brief_threshold_cell_pair_units': 800,
    'brief_threshold_analyzable_class_levels': 12,
    'meets_q2_by_r': {'0.2': False,
                      '0.3': 'undetermined: min(806, 820)=806 >= 800 only if >=99.25% of all units contain a pair fully inside holdout; pair graph unavailable',
                      '0.4': 'undetermined: min(806, 1431)=806 >= 800 only if >=99.25% of all units contain a pair fully inside holdout; pair graph unavailable'},
}

# ------------------------------------------------------------------ qualification (SS8 frozen thresholds)
q1_levels = len(drug_class)
q1 = {'metric': 'analyzable class levels (frozen: class field with >=2 drugs, present in train and holdout)',
      'zip_class_levels': q1_levels, 'zip_levels_ge2': annotation['zip_drugs_summary']['class_levels_ge2_drugs'],
      'moesm8_action_class_levels': len(moesm8_ac), 'moesm8_levels_ge2': annotation['moesm8']['action_class_levels_ge2'],
      'max_available_levels': max(q1_levels, len(moesm8_ac)), 'threshold': 12, 'pass': max(q1_levels, len(moesm8_ac)) >= 12,
      'judgment': ('FAIL: the only published class taxonomies have 5 levels (zip drugs_summary class = 5; '
                   'MOESM8 Action_Class = 5), below the frozen 12-level threshold; per-holdout train/holdout '
                   'analyzability is additionally not computable because drug identity of roots is unavailable')}
q2_upper = both['analytic_bounds']['both_unseen_units_upper_bound_min_total_Ck2']
q2 = {'metric': 'both-unseen cell x pair units', 'threshold': 800,
      'main_estimate': None, 'random_sensitivity': None,
      'structural_upper_bound_by_r': q2_upper,
      'expected_uniform_by_r': both['analytic_bounds']['expected_both_unseen_units_under_uniform_pairing'],
      'pass': False,
      'judgment': ('FAIL: main estimate and random sensitivity are not computable (identity unavailable); the analytic upper bound at '
                   'r=0.20 is C(27,2)=351 < 800; at r=0.30/0.40 the trivial 806-unit cap can reach 800 only if >=99.25% of all '
                   'units are both-unseen, while the uniform-pairing expectation is 73.2/127.0 -> the threshold is effectively unreachable '
                   'for a resource with only 806 total cell x pair units')}
q3 = {'metric': 'training-unseen class levels', 'computed': None, 'pass': None,
      'judgment': 'NOT COMPUTABLE -> not satisfied: no per-root drug identity/class assignment is possible'}
q4 = {'strict_cell_overlap': len(overlap['strict_overlap']['jaaks']['cells']) + len(overlap['strict_overlap']['oneil']['cells']),
      'strict_drug_overlap': len(overlap['strict_overlap']['jaaks']['drugs']) + len(overlap['strict_overlap']['oneil']['drugs']),
      'strict_pair_overlap': len(overlap['strict_overlap']['jaaks']['pairs']) + len(overlap['strict_overlap']['oneil']['pairs']),
      'inventory_text_overlap_moesm8': {'jaaks': overlap['inventory_level_overlap_caliber_b']['n_moesm8_vs_jaaks'],
                                        'oneil': overlap['inventory_level_overlap_caliber_b']['n_moesm8_vs_oneil']},
      'judgment': ('report-only: zero strict textual overlap with Jaaks/O\'Neil for the 2 recoverable cell tokens and 4 recoverable dense '
                   'drug tokens; inventory-level text overlap of the sparse-mode MOESM8 list is 28 drug names with Jaaks and 13 with O\'Neil, '
                   'but that list is not the dense root drug map; externalness for the 804 opaque roots is unverifiable')}
q5 = {'endpoint': 'viability-derived normalised %Cell Death (luminescence CellTiter-Glo/BacTiter-Glo per published methods; raw_val = pre-normalisation readout)',
      'replicates': '3 technical replicates, all in same plate (zip glossary) -> not independent cultures',
      'judgment': ('LIMITATION (always applies): endpoint is a viability-derived metric, not an independent functional endpoint; replicates are '
                   'same-plate technical replicates, not independent cultures. Any A2 result could only test repeatability of coarse-annotation '
                   'vs identity, not independent endpoint/culture/mechanism/clinical evidence')}
qualification = {
    'zip_only_caliber': {
        'verdict': 'unqualified',
        'failures': ['data_unavailable: no cell-line column; drug1_name/drug2_name are placeholders; 804/806 roots are opaque 32-hex ids -> no entity-level identity',
                     'data_insufficient: Q1 max analyzable class levels = 5 (<12)',
                     'data_insufficient: Q2 both-unseen units not computable; analytic upper bound at r=0.20 = 351 (<800); only 806 total cell x pair units',
                     'evaluation_cannot_distinguish: Q3 training-unseen class check needs per-root drug class, unavailable'],
        'unfreeze_conditions': ['release non-anonymised root_id -> (cell-line name, drug1 name, drug2 name) mapping, or a de-anonymised dense table',
                                'publish a dense drug-name -> class annotation with >=12 analyzable levels',
                                'provide a resource with enough cell x pair units that a 20-40% drug holdout yields >=800 both-unseen units (806 total units cannot)'],
    },
    'with_published_metadata_caliber': {
        'verdict': 'unqualified',
        'failures': ['data_unavailable: MOESM8 is the sparse-mode 135-compound list (Supplementary Data 5); no key to dense roots; only AZD1390/CX-5461 recoverable from the 2 descriptive roots, 804 roots unaffected',
                     'data_insufficient: Q1 max class levels = 5 (zip) or 5 (MOESM8 Action_Class) (<12)',
                     'data_insufficient: Q2 as above',
                     'evaluation_cannot_distinguish: Q3 as above'],
        'unfreeze_conditions': ['same as zip-only caliber',
                                'additionally: publish the dense drug inventory names/classes (136 drugs) keyed to root ids'],
    },
    'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5,
    'overall': 'unqualified',
    'frozen_note': 'judgment uses only PROTOCOL SS8 frozen thresholds; no post-hoc adjustment',
}

# ------------------------------------------------------------------ write JSON
audit = {
    'task': 'R189-A1 ComboCat dense supplement resource qualification audit',
    'protocol': {'path': str(PROTOCOL.relative_to(BASE)), 'sha256': sha256_file(PROTOCOL)},
    'script': {'path': 'research/2026-10-27-combocat-resource-audit/audit.py', 'sha256': sha256_file(Path(__file__))},
    'inputs': {
        'zip': {'path': str(ZIP.relative_to(BASE)), 'bytes': ZIP.stat().st_size, 'sha256': zip_sha,
                'receipt_sha256': receipt.get('sha256'), 'sha256_matches_receipt': zip_sha == receipt.get('sha256'),
                'entries': [{'name': e[0], 'bytes': e[1], 'compressed_bytes': e[2]} for e in entries]},
        'xlsx': {'bytes': len(xlsx_bytes), 'sha256': xlsx_sha},
        'moesm8': {'path': str(MOESM8.relative_to(BASE)), 'sha256': sha256_file(MOESM8), 'bytes': MOESM8.stat().st_size},
        'published_text_extracts': {
            'MOESM1_legend_extract': {'path': str(MOESM1_TXT.relative_to(BASE)), 'sha256': sha256_file(MOESM1_TXT)},
            'MOESM3_supp_files_index_extract': {'path': str(MOESM3_TXT.relative_to(BASE)), 'sha256': sha256_file(MOESM3_TXT)},
        },
        'jaaks': {'path': str(JAAKS.relative_to(BASE)), 'sha256': sha256_file(JAAKS), 'bytes': JAAKS.stat().st_size},
        'oneil': {'path': str(ONEIL.relative_to(BASE)), 'sha256': sha256_file(ONEIL), 'bytes': ONEIL.stat().st_size},
        'prior_counts_reference': {'path': str(PRIOR_COUNTS.relative_to(BASE)), 'sha256': sha256_file(PRIOR_COUNTS)},
    },
    'method': {'read_only': True, 'network': False, 'response_values_read': False,
               'deny_columns_access': 'cell is None existence counting only',
               'data_pass': 'single streaming pass; no full-table materialisation',
               'deterministic': 'sorted JSON keys; no timestamps; fixed input hashes; no response modelling/estimation/hypothesis tests',
               'universe': 'zip workbook + AMENDMENT-001 published metadata (MOESM8) + frozen external name lists (Jaaks/O\'Neil)'},
    'p2_priors_check': p2,
    'p2_assumption_contradictions': p2_contradictions,
    'structure': {'sheets': {n: {'max_row': sheet_dims[n][0], 'max_column': sheet_dims[n][1]} for n in sheetnames},
                  'data_sheet': {'n_data_rows': n_rows, 'n_columns': H, 'header': header,
                                 'expected_complete_rows_if_806x3x121': expected_complete,
                                 'missing_rows_vs_complete_grid': expected_complete - n_rows}},
    'column_inventory': col_inventory,
    'deny_columns_not_read': deny_cols,
    'flagged_columns_null_check_only': flagged_cols,
    'unclassified_columns_not_read': not_read_cols,
    'endpoint_semantics': [{'column': c, 'bucket': ENDPOINT_SEMANTICS[c][0], 'evidence': ENDPOINT_SEMANTICS[c][1],
                            'read_modality': next(x['read_modality'] for x in col_inventory if x['column'] == c)}
                           for c in [x['column'] for x in col_inventory if x['column'] in ENDPOINT_SEMANTICS]],
    'identity': identity,
    'annotation': annotation,
    'replication_plate': replication,
    'dose_layout': dose,
    'qc_structure': qc,
    'both_unseen': both,
    'qualification': qualification,
    'failure_categories': ['assumption_contradicts', 'data_unavailable', 'data_insufficient', 'evaluation_cannot_distinguish'],
    'limitations': [
        'technical replicates are same-plate calibration replicates, not independent cultures',
        'viability-derived %Cell Death endpoint is not an independent functional endpoint; no target-engagement/mechanism/clinical claim possible',
        '804/806 roots are opaque 32-hex ids: identity, root->class mapping, drug-pair graph and both-unseen splits are not computable from the frozen inputs',
        'MOESM8 is a sparse-mode compound list (135), not the dense 136-drug inventory; only text-level inventory overlap is reportable',
        'strict textual name matching only; no chemical entity resolution; no synonym inference; no external ID lookup; no network',
        'overlap against the complete Jaaks table, not against a particular future training split',
    ],
}

counts = {
    'input_sha256': {'zip': zip_sha, 'xlsx': xlsx_sha, 'protocol': sha256_file(PROTOCOL),
                     'script': sha256_file(Path(__file__)), 'moesm8': sha256_file(MOESM8),
                     'jaaks': sha256_file(JAAKS), 'oneil': sha256_file(ONEIL)},
    'structure': {'sheets': sheetnames, 'data_rows': n_rows, 'data_rows_incl_header': n_rows + 1, 'columns': H,
                  'expected_complete_rows': expected_complete, 'missing_vs_complete_grid': expected_complete - n_rows},
    'identity': {'roots_total': n_roots, 'roots_opaque_hex32': len(md5_roots), 'roots_descriptive': len(descriptive_roots),
                 'share_opaque': round(len(md5_roots) / n_roots, 6),
                 'recovered_cell_tokens': len(rec_cells), 'recovered_drug_tokens': len(rec_drugs),
                 'descriptive_prefix_parsed': identity['descriptive_prefix_parsed'],
                 'descriptive_suffix_parsed': identity['descriptive_suffix_parsed'],
                 'descriptive_suffix_ambiguous': len(identity['descriptive_suffix_ambiguous'])},
    'annotation': {'cell_line_ids': annotation['zip_cell_lines_summary']['n_ids'],
                   'cell_organism_levels': len(annotation['zip_cell_lines_summary']['organism_counts']),
                   'cell_lineage_levels': annotation['zip_cell_lines_summary']['lineage_levels'],
                   'drug_ids': annotation['zip_drugs_summary']['n_ids'],
                   'drug_class_levels': annotation['zip_drugs_summary']['class_levels'],
                   'drug_class_counts': annotation['zip_drugs_summary']['class_counts'],
                   'moesm8_drugs': annotation['moesm8']['n_drugs'],
                   'moesm8_action_class_levels': annotation['moesm8']['action_class_levels'],
                   'moesm8_action_class_counts': annotation['moesm8']['action_class_counts'],
                   'moesm8_reported_target_levels': annotation['moesm8']['reported_target_levels']},
    'replication': {'rows_per_root': replication['rows_per_root_hist'],
                    'replicates_per_root': replication['replicates_per_root_hist'],
                    'replicate_values': replication['replicate_value_counts'],
                    'plates_per_root': replication['plates_per_root_hist'],
                    'n_real_barcodes': replication['n_real_barcodes'],
                    'n_roots_with_real_barcode': replication['roots_with_real_barcode'],
                    'n_roots_with_na_barcode': replication['roots_with_na_barcode'],
                    'root_spanning_multiple_plates': replication['root_spanning_multiple_plates'],
                    'transfer_type_row_counts': replication['transfer_type_row_counts'],
                    'na_string_counts': replication['na_string_counts']},
    'dose': {'unique_dose_pairs_per_root': dose['unique_dose_pairs_per_root_hist'],
             'unique_drug1_conc_per_root': dose['unique_drug1_conc_per_root_hist'],
             'unique_drug2_conc_per_root': dose['unique_drug2_conc_per_root_hist'],
             'roots_by_unit': dose['roots_by_unit'],
             'rows_by_unit': dose['rows_by_unit'],
             'well_type_row_counts': dose['well_type_row_counts']},
    'qc': {'deny_columns': len(deny_cols), 'deny_null_counts': qc['deny_null_counts'],
           'deny_all_present': all(v == 0 for v in qc['deny_null_counts'].values()),
           'flagged_columns': flagged_cols, 'flagged_null_counts': qc['flagged_null_counts']},
    'external': {'jaaks': {'unique_records': len(jaaks_triples), 'cells': len(jaaks['cells']), 'drugs': len(jaaks['drugs']),
                           'pairs': len(jaaks['pairs']), 'cell_pairs': len(jaaks['cell_pairs']),
                           'cell_collision_keys': len(jaaks['cell_collisions']), 'drug_collision_keys': len(jaaks['drug_collisions'])},
                 'oneil': {'rows': len(oneil_rows), 'cells': len(oneil['cells']), 'drugs': len(oneil['drugs']),
                           'pairs': len(oneil['pairs']), 'cell_pairs': len(oneil['cell_pairs']),
                           'batches': dict(oneil_batches),
                           'cell_collision_keys': len(oneil['cell_collisions']), 'drug_collision_keys': len(oneil['drug_collisions'])},
                 'strict_intersection': {'cells': q4['strict_cell_overlap'], 'drugs': q4['strict_drug_overlap'],
                                         'pairs': q4['strict_pair_overlap']},
                 'inventory_text_overlap_moesm8': q4['inventory_text_overlap_moesm8']},
    'both_unseen': {'N_drug': both['N_drug'], 'N_cell': both['N_cell'], 'total_cell_pair_units': total_units,
                    'holdout_k_by_r': k_by_r, 'main_estimate_units': None, 'random_sensitivity_mean': None,
                    'analytic_upper_bound_units': q2_upper,
                    'expected_uniform_units': both['analytic_bounds']['expected_both_unseen_units_under_uniform_pairing'],
                    'brief_threshold': 800, 'q2_pass': False},
    'qualification': {'overall': 'unqualified', 'q1_pass': False, 'q2_pass': False, 'q3_computable': False,
                      'zip_only': 'unqualified', 'with_published_metadata': 'unqualified'},
    'prior_crosscheck': {'jaaks_matches_prior_counts': overlap['sources']['jaaks']['matches_prior'],
                         'oneil_matches_prior_counts': overlap['sources']['oneil']['matches_prior']},
}

(OUT / 'audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True), encoding='utf8')
(OUT / 'counts.json').write_text(json.dumps(counts, indent=2, ensure_ascii=False, sort_keys=True), encoding='utf8')
(OUT / 'overlap.json').write_text(json.dumps(overlap, indent=2, ensure_ascii=False, sort_keys=True), encoding='utf8')

elapsed = time.perf_counter() - t0
print(json.dumps({'rows': n_rows, 'roots': n_roots, 'opaque_roots': len(md5_roots), 'descriptive': len(descriptive_roots),
                  'drug_class_levels': q1_levels, 'moesm8_drugs': len(moesm8_rows),
                  'class_counts': dict(drug_class),
                  'jaaks': {k: len(v) for k, v in jaaks.items() if k in ('cells', 'drugs', 'pairs', 'cell_pairs')},
                  'oneil': {k: len(v) for k, v in oneil.items() if k in ('cells', 'drugs', 'pairs', 'cell_pairs')},
                  'strict_overlap': {'cells': q4['strict_cell_overlap'], 'drugs': q4['strict_drug_overlap'],
                                     'pairs': q4['strict_pair_overlap']},
                  'inventory_overlap': q4['inventory_text_overlap_moesm8'],
                  'both_unseen_bounds': both['analytic_bounds'],
                  'verdict': 'unqualified',
                  'timing_s': {'data_pass_incl_load': round(data_pass_s, 2), 'external_sources': round(ext_s - data_pass_s, 2),
                               'writing_and_hashing': round(elapsed - ext_s, 2), 'total': round(elapsed, 2)}},
                 indent=2, ensure_ascii=False, sort_keys=True))
