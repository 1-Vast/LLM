"""Project registered metadata addresses; never convert other response cells."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from inspect_structure import LOG, NS, sheets

LIBRARY_COLS = {'A', 'B', 'C', 'D', 'F', 'H', 'I', 'K'}


def project(sheet_stream, string_stream, library=False):
    cells, needed = {}, set()
    for _, element in ET.iterparse(sheet_stream, events=['end']):
        if element.tag != NS + 'c':
            continue
        address = element.attrib['r']
        col, row = re.fullmatch(r'([A-Z]+)(\d+)', address).groups()
        allowed = col in LIBRARY_COLS if library else row == '1' or col in {'A', 'B'}
        if allowed:
            kind = element.attrib.get('t', 'n')
            if element.find(NS + 'f') is not None:
                cells[address] = {'blocked_formula': True}
            elif kind == 's':
                index = int(element.findtext(NS + 'v'))
                needed.add(index)
                cells[address] = {'string_index': index}
            elif library or row == '1':
                cells[address] = {'type': kind, 'metadata_literal': element.findtext(NS + 'v')}
            else:
                cells[address] = {'blocked_nonstring_identity': True}
        element.clear()
    strings = {}
    index = 0
    for _, element in ET.iterparse(string_stream, events=['end']):
        if element.tag == NS + 'si':
            if index in needed:
                strings[index] = ''.join(t.text or '' for t in element.iter(NS + 't'))
            index += 1
            element.clear()
    return {address: {'type': 's', 'metadata_literal': strings[value['string_index']]}
            if 'string_index' in value else value for address, value in cells.items()}


def row_values(cells):
    rows = defaultdict(dict)
    for address, cell in cells.items():
        col, row = re.fullmatch(r'([A-Z]+)(\d+)', address).groups()
        rows[int(row)][col] = cell.get('metadata_literal')
    return dict(rows)


def main():
    acquired = json.loads((LOG / 'RAW_ACQUISITION_FINAL.json').read_text(encoding='utf-8'))
    records = []
    for item in acquired['files']:
        path = Path(item['body_path'])
        record = {'id': item['id'], 'filename': item['filename'],
                  'source_sha256_before_projection': hashlib.sha256(path.read_bytes()).hexdigest()}
        with ZipFile(path) as archive:
            selected = [s for s in sheets(archive) if s['name'] not in {'Pass QC', 'Counts'}]
            assert len(selected) == 1
            sheet = selected[0]
            with archive.open(sheet['path']) as data, archive.open('xl/sharedStrings.xml') as strings:
                record['cells'] = project(data, strings, library=sheet['name'] == 'Chemical Data')
            record['sheet'] = sheet
        records.append(record)
    library_rows = row_values(records[0]['cells'])
    names = defaultdict(list)
    for row, fields in library_rows.items():
        if row > 1 and fields.get('B'):
            names[fields['B']].append(row)
    summary = {'library_nonempty_compound_rows': sum(map(len, names.values())),
               'library_unique_exact_names': len(names),
               'library_duplicate_names': {name: rows for name, rows in names.items() if len(rows) > 1},
               'screens': [], 'response_values_converted': 0, 'qc_membership_read': False}
    for record in records[1:]:
        rows = row_values(record['cells'])
        identities = [(row, fields.get('A'), fields.get('B')) for row, fields in rows.items() if row > 1]
        pairs = Counter((name, marker) for _, name, marker in identities)
        unique_names = {name for _, name, _ in identities}
        join = Counter(len(names.get(name, [])) for name in unique_names)
        screen = {'filename': record['filename'], 'identity_rows': len(identities),
                  'unique_compound_labels': len(unique_names),
                  'marker_counts': dict(Counter(marker for _, _, marker in identities)),
                  'duplicate_compound_marker_keys': [{'compound': name, 'marker': marker, 'rows': count}
                                                     for (name, marker), count in pairs.items() if count > 1],
                  'missing_name_or_marker_rows': [row for row, name, marker in identities if not name or not marker],
                  'unique_name_exact_library_join_multiplicity': dict(join),
                  'unmatched_exact_names': sorted(name for name in unique_names if name not in names and name is not None),
                  'header': rows[1]}
        summary['screens'].append(screen)
    for name, data in [('IDENTITY_PROJECTION.json', {'files': records}), ('IDENTITY_SUMMARY.json', summary)]:
        with (LOG / name).open('x', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
