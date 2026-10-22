"""Only compound literals and the second named marker identity field."""
from collections import Counter
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from inspect_structure import LOG, NS, sheets


def project_pair(sheet_stream, string_stream, second_marker):
    selected, needed = {}, set()
    for _, element in ET.iterparse(sheet_stream, events=['end']):
        if element.tag != NS + 'c':
            continue
        address = element.attrib['r']
        col, row = re.fullmatch(r'([A-Z]+)(\d+)', address).groups()
        if col in {'A', second_marker} and int(row) > 1:
            if element.find(NS + 'f') is not None:
                selected[address] = {'blocked_formula': True}
            elif element.attrib.get('t') == 's':
                index = int(element.findtext(NS + 'v'))
                selected[address] = {'index': index}
                needed.add(index)
            elif col == 'A':
                selected[address] = {'type': element.attrib.get('t', 'n'),
                                     'identity_literal': element.findtext(NS + 'v')}
            else:
                selected[address] = {'blocked_nonstring_marker': True}
        element.clear()
    strings = {}
    index = 0
    for _, element in ET.iterparse(string_stream, events=['end']):
        if element.tag == NS + 'si':
            if index in needed:
                strings[index] = ''.join(t.text or '' for t in element.iter(NS + 't'))
            index += 1
            element.clear()
    return {address: {'type': 's', 'identity_literal': strings[cell['index']]}
            if 'index' in cell else cell for address, cell in selected.items()}


def main():
    acquisition = json.loads((LOG / 'RAW_ACQUISITION_FINAL.json').read_text(encoding='utf-8'))
    records = []
    for item in acquisition['files'][1:]:
        second_marker = 'BK' if item['filename'].startswith('U2OS') else 'AB'
        with ZipFile(item['body_path']) as archive:
            sheet = [s for s in sheets(archive) if s['name'] != 'Pass QC'][0]
            with archive.open(sheet['path']) as data, archive.open('xl/sharedStrings.xml') as strings:
                cells = project_pair(data, strings, second_marker)
        markers = Counter(c.get('identity_literal') for address, c in cells.items()
                          if address.startswith(second_marker) and address[len(second_marker):].isdigit())
        compound = {address: c for address, c in cells.items() if re.fullmatch(r'A\d+', address)}
        records.append({'id': item['id'], 'filename': item['filename'], 'second_marker_column': second_marker,
                        'second_marker_counts': dict(markers),
                        'empty_or_nonstring_compounds': {a: c for a, c in compound.items()
                                                       if c.get('type') != 's' or not c.get('identity_literal')},
                        'cells': cells})
    with (LOG / 'SECOND_MARKER_PROJECTION.json').open('x', encoding='utf-8') as stream:
        json.dump({'files': records, 'response_values_converted': 0}, stream, ensure_ascii=False, indent=2)
    for record in records:
        print(json.dumps({k: v for k, v in record.items() if k != 'cells'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
