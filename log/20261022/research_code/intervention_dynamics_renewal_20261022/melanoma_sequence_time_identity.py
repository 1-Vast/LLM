"""Project only the exact header-qualified elapsed/time identities."""
import collections
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

BASE = Path('log/20261022/intervention_dynamics_renewal/melanoma_sequence')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def main():
    out = {'sheet': 'Fig 4B data', 'design_numeric_whitelist': 'B6:B22',
           'response_closed_range': 'C6:Q22', 'responses_projected': False, 'time_design': []}
    with zipfile.ZipFile(BASE / 'Suppl Data 03.xlsx') as book:
        shared_root = ET.fromstring(book.read('xl/sharedStrings.xml'))
        shared = [''.join(v.text or '' for v in item.findall('.//m:t', NS)) for item in shared_root]
        sheet = ET.fromstring(book.read('xl/worksheets/sheet1.xml'))
        cells = {c.attrib['r']: c for c in sheet.findall('.//m:sheetData/m:row/m:c', NS)}
        assert shared[int(cells['B5'].find('m:v', NS).text)] == 'Elapsed'
        counts = collections.Counter()
        missing = []
        for row in range(6, 23):
            time_cell = cells[f'B{row}']
            if time_cell.attrib.get('t', 'n') != 'n' or time_cell.find('m:f', NS) is not None:
                raise RuntimeError('Elapsed design field has unexpected storage')
            elapsed = time_cell.find('m:v', NS).text
            date_cell = cells[f'A{row}']
            date_text = shared[int(date_cell.find('m:v', NS).text)]
            out['time_design'].append({'elapsed_cell': f'B{row}', 'elapsed_hours': elapsed,
                                       'timestamp_cell': f'A{row}', 'timestamp': date_text})
            for column in 'CDEFGHIJKLMNOPQ':
                address = f'{column}{row}'
                cell = cells.get(address)
                if cell is None:
                    missing.append(address)
                else:
                    # Only inspect XML node presence and attributes, never response payload text/index.
                    counts[(cell.attrib.get('t', 'n'), cell.find('m:v', NS) is not None,
                            cell.find('m:f', NS) is not None)] += 1
        out['response_metadata_counts'] = [{'type': k[0], 'has_v_node': k[1],
                                            'has_formula_node': k[2], 'cells': v} for k, v in counts.items()]
        out['absent_response_coordinates'] = missing
    (BASE / 'TIME_IDENTITY_AND_RESPONSE_METADATA.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
