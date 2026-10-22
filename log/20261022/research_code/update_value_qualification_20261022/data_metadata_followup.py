"""Metadata, response header/string-ID and byte-hash qualification; no outcomes converted."""
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_value_qualification/data'
RAW = ROOT / 'data/external/prism_19q4/raw'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def meta(name):
    with (RAW / name).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


rows = meta('secondary-screen-replicate-treatment-info.csv')
hts = [r for r in rows if r['screen_id'] == 'HTS002' and r['perturbation_type'] == 'experimental_treatment']
exact = [r for r in hts if Decimal(r['dose']) == Decimal('2.5')]
groups = defaultdict(list)
for row in exact:
    groups[(row['broad_id'][:13], row['broad_id'], row['compound_plate'], row['well'])].append(row)
incomplete = []
for key, group in groups.items():
    counts = Counter((match.group(1) if (match := re.search(r'_(X[123])(?:[_.]|$)', r['detection_plate'])) else 'UNPARSED') for r in group)
    if counts != {'X1': 1, 'X2': 1, 'X3': 1}:
        relatives = [r for r in hts if (r['broad_id'][:13], r['broad_id'], r['compound_plate'], r['well']) == key]
        incomplete.append({'key': list(key), 'exact_replicates': dict(counts),
                           'all_dose_replicates': [{'dose': r['dose'], 'plate': r['detection_plate']} for r in relatives]})


def matrix_ids(name):
    """Decode only the header and first CSV field of each physical row.

    The release is an unquoted numeric wide matrix: assert first ID fields have no
    quote/newline. Remaining bytes are neither decoded nor converted to outcomes.
    """
    path = RAW / name
    row_ids = []
    with path.open('rb') as stream:
        header = next(csv.reader([stream.readline().decode('utf-8-sig')]))
        for line in stream:
            first = line.split(b',', 1)[0]
            assert b'"' not in first and first.strip(), 'Unexpected quoted/empty row identifier'
            row_ids.append(first.decode('utf-8'))
    return {'sha256': digest(path), 'bytes': path.stat().st_size, 'row_ids': row_ids,
            'header': header, 'rows': len(row_ids), 'columns_excluding_row_id': len(header) - 1,
            'duplicate_row_ids': len(row_ids) - len(set(row_ids)),
            'duplicate_column_ids': len(header[1:]) - len(set(header[1:])),
            'numerical_response_conversion': False}


matrices = {name: matrix_ids(name) for name in (
    'secondary-screen-logfold-change.csv',
    'secondary-screen-replicate-collapsed-logfold-change.csv',
    'primary-screen-replicate-collapsed-logfold-change.csv')}
catalog = json.loads((OUT / 'PRISM_METADATA_QUALIFICATION.json').read_text(encoding='utf-8'))
selected_cols = [col for r in catalog['treatment_catalog'] for col in r['replicate_columns'].values()]
secondary = matrices['secondary-screen-logfold-change.csv']
secondary['metadata_columns_missing_from_header'] = sorted(set(r['column_name'] for r in rows) - set(secondary['header'][1:]))
secondary['header_columns_missing_metadata'] = sorted(set(secondary['header'][1:]) - set(r['column_name'] for r in rows))
secondary['selected_columns_missing_header'] = sorted(set(selected_cols) - set(secondary['header'][1:]))
secondary['eligible_contexts_missing_matrix'] = sorted(set(catalog['contexts']) - set(secondary['row_ids']))
secondary['selected_join_rows'] = len(set(catalog['contexts']) & set(secondary['row_ids']))
secondary['selected_join_columns'] = len(set(selected_cols) & set(secondary['header'][1:]))

gdsc_root = ROOT / 'data/external/gdsc_combinations/jaaks2022_figshare'
design = ['BARCODE', 'COMBI_ID', 'Tissue', 'CELL_LINE_NAME', 'SIDM', 'ANCHOR_ID', 'ANCHOR_NAME',
          'ANCHOR_CONC', 'LIBRARY_ID', 'LIBRARY_NAME', 'LIBRARY_CONC']
gdsc = {}
frames = {}
for label, name in [('original', 'Original screen_All tissues_fitted data.csv'),
                    ('validation', 'Validation screen_All tissues_fitted data.csv')]:
    path = gdsc_root / name
    with path.open(encoding='utf-8-sig', newline='') as stream:
        schema = next(csv.reader(stream))
    frame = pd.read_csv(path, usecols=design, dtype=str, keep_default_na=False)
    frames[label] = frame
    gdsc[label] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path), 'header': schema,
        'selected_design_fields': design, 'rows': len(frame),
        'distinct_barcodes': frame.BARCODE.nunique(), 'distinct_combi_ids': frame.COMBI_ID.nunique(),
        'distinct_sidm': frame.SIDM.nunique(), 'distinct_anchor_ids': frame.ANCHOR_ID.nunique(),
        'distinct_library_ids': frame.LIBRARY_ID.nunique(),
        'distinct_pairs': frame[['ANCHOR_ID', 'LIBRARY_ID']].drop_duplicates().shape[0],
        'exact_design_key_duplicate_rows': int(frame.duplicated(['SIDM', 'ANCHOR_ID', 'ANCHOR_CONC', 'LIBRARY_ID']).sum()),
        'physical_replicate_or_culture_independence': 'NOT_ESTABLISHED from fitted-table design fields',
        'outcome_fields_converted': False}
keys = ['SIDM', 'ANCHOR_ID', 'ANCHOR_CONC', 'LIBRARY_ID']
a = set(map(tuple, frames['original'][keys].values.tolist()))
b = set(map(tuple, frames['validation'][keys].values.tolist()))
gdsc['design_key_overlap'] = {'keys': keys, 'original': len(a), 'validation': len(b), 'intersection': len(a & b)}

inventories = {}
for folder in [ROOT / 'data/external/prism_19q4', ROOT / 'data/raw/depmap', ROOT / 'data/external/depmap_24q2']:
    inventories[str(folder.relative_to(ROOT))] = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size}
                                                for p in sorted(folder.rglob('*')) if p.is_file()] if folder.exists() else []
result = {'response_values_converted': False, 'matrix_access': 'header and string row IDs only; byte hash all bytes',
          'prism_exact_dose_incomplete_examples': incomplete[:8], 'incomplete_exact_dose_count': len(incomplete),
          'unparsed_plate_names': sorted({r['detection_plate'] for r in hts if re.search(r'_(X[123])(?:[_.]|$)', r['detection_plate']) is None}),
          'hts002_duration_tokens': sorted({t for r in hts for t in re.findall(r'(?:_|^)(\d+H)(?:_|$)', r['detection_plate'])}),
          'matrices': matrices, 'gdsc_design': gdsc, 'inventories': inventories}
(OUT / 'METADATA_FOLLOWUP.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'incomplete': len(incomplete), 'examples': incomplete[:2],
                  'matrices': {k: {q: v[q] for q in ('sha256', 'rows', 'columns_excluding_row_id')} for k, v in matrices.items()},
                  'selected_join': {k: secondary[k] for k in ('selected_join_rows', 'selected_join_columns', 'selected_columns_missing_header', 'eligible_contexts_missing_matrix')},
                  'gdsc_design': gdsc, 'inventories': inventories}, ensure_ascii=False))
