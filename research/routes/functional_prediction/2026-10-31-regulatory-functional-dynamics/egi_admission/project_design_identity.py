"""Independently verify identity and sample keys without parsing any count value."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

BASE = Path('D:/MAESTRO/data/external/conditional_interventions_20261030/egi')
OUT = Path(__file__).parent

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1_048_576), b''):
            h.update(chunk)
    return h.hexdigest()

sources = ['04_primary_fulltext.xml', '07_geo_samples.soft', '02_geo_series.soft', '06_call_genetic_interactions.ipynb', '08_differential_analysis.ipynb', '09_replicate_quality_control.ipynb', '14_GI_expt1_counts.txt.gz', '15_GI_expt2_counts.txt.gz', '17_redirect1_dualsgrna_alignedlibrary.txt', '08_primary_supplementary.zip', 'NIHMS2148368-supplement-MMC1.pdf', 'request_receipts.jsonl']
original_manifest = [{'file': name, 'path': str(BASE / name), 'bytes': (BASE / name).stat().st_size, 'sha256': sha(BASE / name)} for name in sources]

counts = []
identity_sets = []
for filename in ['14_GI_expt1_counts.txt.gz', '15_GI_expt2_counts.txt.gz']:
    identities = set()
    rows = 0
    with gzip.open(BASE / filename, 'rb') as stream:
        first = stream.readline().rstrip(b'\r\n')
        delimiter = b'\t' if b'\t' in first else b','
        header = first.decode('utf-8-sig').split(delimiter.decode())
        for line in stream:
            # The entire row remains opaque except its first identity field.
            # No count token is converted, retained, summarized, or displayed.
            identity = line.split(delimiter, 1)[0].decode('utf-8')
            identities.add(identity)
            rows += 1
    a = set()
    b = set()
    for identity in identities:
        aa, bb = identity.split(':')
        a.add(aa)
        b.add(bb)
    counts.append({'file': filename, 'delimiter': delimiter.decode(), 'header': header, 'identity_rows': rows, 'unique_construct_identities': len(identities), 'vector_a_guide_identities': len(a), 'vector_b_guide_identities': len(b), 'same_guide_sets_in_vector_positions': a == b, 'complete_ordered_identity_cartesian_grid': len(identities) == len(a) * len(b), 'sorted_identity_sha256': hashlib.sha256(('\n'.join(sorted(identities)) + '\n').encode()).hexdigest()})
    identity_sets.append(identities)

guide_gene = defaultdict(set)
guide_sequence = defaultdict(set)
library_ids = set()
bad_double_name = 0
with (BASE / '17_redirect1_dualsgrna_alignedlibrary.txt').open(encoding='utf-8') as stream:
    reader = csv.DictReader(stream, delimiter='\t')
    library_header = reader.fieldnames
    for row in reader:
        library_ids.add(row['double'])
        if row['double'] != row['name_a'] + ':' + row['name_b']:
            bad_double_name += 1
        for position in ['a', 'b']:
            guide_gene[row['name_' + position]].add(row['gene_' + position])
            guide_sequence[row['name_' + position]].add(row['seq_' + position])
assert all(len(v) == 1 for v in guide_gene.values())
assert all(len(v) == 1 for v in guide_sequence.values())
guide_gene = {k: next(iter(v)) for k, v in sorted(guide_gene.items())}
guide_sequence = {k: next(iter(v)) for k, v in sorted(guide_sequence.items())}
negative = sorted(k for k, v in guide_gene.items() if v == 'negative')
targeted = {k: v for k, v in guide_gene.items() if v != 'negative'}
gene_counts = Counter(targeted.values())
guide_rows = [{'guide_identity': k, 'source_gene_label': v, 'analysis_gene_label': 'non-targeting' if v == 'negative' else 'REV3L' if v == 'REV3' and k.startswith('REV3L_') else v, 'is_ntc': v == 'negative', 'source_sequence': guide_sequence[k]} for k, v in guide_gene.items()]
with (OUT / 'guide_identity.tsv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(guide_rows[0]), delimiter='\t')
    writer.writeheader()
    writer.writerows(guide_rows)

samples = []
current = None
for line in (BASE / '07_geo_samples.soft').read_text(encoding='utf-8').splitlines():
    if line.startswith('^SAMPLE = '):
        current = {'accession': line.split(' = ', 1)[1]}
        samples.append(current)
    elif current is not None and ' = ' in line:
        key, value = line.split(' = ', 1)
        if key in ['!Sample_title', '!Sample_source_name_ch1', '!Sample_characteristics_ch1', '!Sample_data_processing', '!Sample_relation']:
            current.setdefault(key, []).append(value)
samples = [s for s in samples if any(t.startswith(('GI1_', 'GI2_')) for t in s.get('!Sample_title', []))]
sample_by_title = {s['!Sample_title'][0]: s for s in samples}

binding = []
for batch, conditions in [('GI1', [('T0', 'T0', 'T0'), ('UT', 'dmso', 'untreated_DMSO'), ('ATR', 'atr', 'ATR_inhibition')]), ('GI2', [('T0', 't0', 'T0'), ('UT', 'dmso', 'untreated_DMSO'), ('ETOP', 'etop', 'etoposide'), ('KETO', 'keto', 'glucose_deprivation')])]:
    for rep in [1, 2]:
        for geo_arm, code_arm, environment in conditions:
            title = f'{batch}_Rep{rep}_{geo_arm}'
            sample = sample_by_title[title]
            if batch == 'GI1':
                column = f'Rep{rep}_' + {'T0': 'T0', 'UT': 'UT', 'ATR': 'DRUG'}[geo_arm]
            else:
                column = f'{code_arm}_r{rep}'
            file = counts[0 if batch == 'GI1' else 1]['file']
            assert column in counts[0 if batch == 'GI1' else 1]['header']
            binding.append({'batch': batch, 'biological_replicate': rep, 'culture_ancestry_group': f'{batch}_Rep{rep}', 'geo_accession': sample['accession'], 'geo_title': title, 'environment': environment, 'count_file': file, 'count_column': column, 'paired_T0_column': f'Rep{rep}_T0' if batch == 'GI1' else f't0_r{rep}', 'matched_reference_column': f'Rep{rep}_UT' if batch == 'GI1' else f'dmso_r{rep}', 'relative_endpoint_day': 0 if geo_arm == 'T0' else 9, 'source_methods_section': 'S24.1' if geo_arm == 'T0' else {'UT': 'S24.3-S24.5', 'ATR': 'S24.3', 'ETOP': 'S24.4', 'KETO': 'S24.5'}[geo_arm], 'binding_evidence': 'GEO original title/characteristics + calling notebook source cells 6-10; values not read'})
with (OUT / 'sample_binding.tsv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(binding[0]), delimiter='\t')
    writer.writeheader()
    writer.writerows(binding)

# Only row-1 / column-A identities are decoded from worksheet XML. Matrix cells
# outside these ranges are discarded by coordinate before their text is read.
matrix_headers = []
ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(BASE / '08_primary_supplementary.zip') as archive:
    for mmc in range(4, 12):
        name = f'NIHMS2148368-supplement-MMC{mmc}.xlsx'
        raw = archive.read(name)
        with zipfile.ZipFile(io.BytesIO(raw)) as workbook:
            string_table = []
            if 'xl/sharedStrings.xml' in workbook.namelist():
                table = ET.fromstring(workbook.read('xl/sharedStrings.xml'))
                string_table = [''.join(x.itertext()) for x in table]
            axes = {'row1': [], 'columnA': []}
            for _, element in ET.iterparse(io.BytesIO(workbook.read('xl/worksheets/sheet1.xml')), events=['end']):
                if element.tag != '{' + ns['m'] + '}c':
                    continue
                coordinate = element.get('r', '')
                is_row1 = coordinate.rstrip('0123456789') != 'A' and coordinate.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ') == '1'
                is_columnA = coordinate.rstrip('0123456789') == 'A' and coordinate != 'A1'
                if is_row1 or is_columnA:
                    if element.get('t') == 'inlineStr':
                        value = ''.join(x.text or '' for x in element.findall('.//m:t', ns))
                    else:
                        value_node = element.find('m:v', ns)
                        value = value_node.text if value_node is not None else ''
                        if element.get('t') == 's':
                            value = string_table[int(value)]
                    assert value and not value.replace('.', '', 1).isdigit(), 'Only string axis identities are admissible'
                    axes['row1' if is_row1 else 'columnA'].append(value)
                element.clear()
            matrix_headers.append({'member': name, 'sha256_member': hashlib.sha256(raw).hexdigest(), 'member_bytes': len(raw), 'column_gene_identities': axes['row1'], 'row_gene_identities': axes['columnA'], 'same_axis_order': axes['row1'] == axes['columnA'], 'header_count': len(axes['row1']), 'source_sheet': 'xl/worksheets/sheet1.xml'})

output = {'created_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'Identity/source/design only; no count value conversion, GI numerical cell access, response distribution or notebook-output access', 'originals': original_manifest, 'count_files': counts, 'count_identity_sets_equal': identity_sets[0] == identity_sets[1], 'aligned_library_identity_set_equals_counts': library_ids == identity_sets[0] == identity_sets[1], 'library_header': library_header, 'construct_identity_name_a_name_b_disagreements': bad_double_name, 'guide_count': len(guide_gene), 'targeting_guide_count': len(targeted), 'source_target_gene_count': len(gene_counts), 'per_gene_guide_identity_cardinalities': dict(sorted(Counter(gene_counts.values()).items())), 'negative_guides': negative, 'source_internal_alias': {'source_gene_label': 'REV3', 'analysis_gene_label': 'REV3L', 'basis': 'Both exact matching guide names use REV3L_; processed matrix identity uses REV3L. No general external synonym assertion.'}, 'samples': samples, 'sample_binding': binding, 'matrix_headers': matrix_headers}
(OUT / 'identity_design_projection.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: output[k] for k in ['scope', 'count_files', 'count_identity_sets_equal', 'aligned_library_identity_set_equals_counts', 'construct_identity_name_a_name_b_disagreements', 'guide_count', 'targeting_guide_count', 'source_target_gene_count', 'per_gene_guide_identity_cardinalities', 'negative_guides']}, indent=2))
print(json.dumps({'sample_count': len(binding), 'matrix_count': len(matrix_headers), 'matrix_axis_identity_counts': [m['header_count'] for m in matrix_headers], 'same_matrix_axis_order': all(m['same_axis_order'] for m in matrix_headers)}, indent=2))
