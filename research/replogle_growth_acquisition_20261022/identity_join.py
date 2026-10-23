"""Authenticate construct identities using string fields only, not assay values."""
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import h5py

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/replogle_growth_acquisition'
SOURCE = OUT / 'root_sources'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def string_rows(path, worksheet, columns):
    with zipfile.ZipFile(path) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(item.itertext()) for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        with archive.open(worksheet) as stream:
            for _, row in ET.iterparse(stream, events=('end',)):
                if row.tag == '{' + NS['m'] + '}row':
                    result = {}
                    for cell in row:
                        column = ''.join(character for character in cell.get('r') if character.isalpha())
                        if column not in columns:
                            continue
                        if cell.get('t') == 's':
                            result[column] = shared[int(cell.find('m:v', NS).text)]
                        elif cell.get('t') == 'inlineStr':
                            result[column] = ''.join(cell.itertext())
                    yield result
                    row.clear()


library_rows = list(string_rows(SOURCE / 'public_asset1.body', 'xl/worksheets/sheet1.xml', {'A', 'B', 'C', 'D'}))
assert library_rows[0] == {'A': 'unique sgRNA pair ID', 'B': 'gene', 'C': 'transcript', 'D': 'ensembl gene id'}
library = {row['A']: {'gene': row.get('B', ''), 'transcript': row.get('C', ''), 'ensembl': row.get('D', '')}
           for row in library_rows[1:] if 'A' in row}
assert len(library) == len(library_rows) - 1
summary_rows = list(string_rows(SOURCE / 'public_asset.body', 'xl/worksheets/sheet2.xml', {'A'}))
assert summary_rows[0]['A'] == 'genetic perturbation'
summary_ids = [row['A'] for row in summary_rows[1:] if 'A' in row]
state_path = ROOT / 'log/20261022/multi_context_state_function/data/K562_gwps_raw_bulk_01.h5ad'
with h5py.File(state_path, 'r') as handle:
    state_ids = list(handle['obs/gene_transcript'].asstr()[...])
assert len(set(state_ids)) == len(state_ids)
assert len(set(summary_ids)) == len(summary_ids)
with (OUT / 'CONSTRUCT_IDENTITY_MAPPING.csv').open('x', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=['construct', 'gene', 'transcript', 'ensembl', 'in_library', 'in_summary'])
    writer.writeheader()
    for name in state_ids:
        writer.writerow({'construct': name, **library.get(name, {}), 'in_library': name in library, 'in_summary': name in summary_ids})
definitions = list(string_rows(SOURCE / 'public_asset.body', 'xl/worksheets/sheet1.xml', {'A', 'B'}))
(OUT / 'FIELD_DEFINITIONS.json').write_text(json.dumps(definitions, indent=2), encoding='utf-8')
result = {'state_rows': len(state_ids), 'library_rows': len(library), 'summary_rows': len(summary_ids),
          'state_in_library': len(set(state_ids) & set(library)),
          'state_in_summary': len(set(state_ids) & set(summary_ids)),
          'library_not_state': len(set(library) - set(state_ids)),
          'summary_not_state': len(set(summary_ids) - set(state_ids)),
          'state_not_library': sorted(set(state_ids) - set(library)),
          'target_ensembl_groups': len({library[name]['ensembl'] for name in state_ids if name in library and library[name]['ensembl']}),
          'numeric_expression_or_assay_values_decoded': False,
          'functional_gamma_join': 'NOT_AUTHENTICATED'}
(OUT / 'IDENTITY_JOIN.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2)[:16000])
