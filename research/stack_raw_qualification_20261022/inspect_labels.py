"""Exact-cell string labels only; numerical and formula cells remain closed."""
from io import BytesIO
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from inspect_structure import LOG, NS, sheets


def selected_strings(sheet_stream, string_stream, allowed):
    cells, needed = {}, set()
    for _, element in ET.iterparse(sheet_stream, events=['end']):
        if element.tag != NS + 'c':
            continue
        address = element.attrib['r']
        if address in allowed:
            if element.find(NS + 'f') is not None or element.attrib.get('t') != 's':
                cells[address] = {'blocked_nonstring_or_formula': True}
            else:
                index = int(element.findtext(NS + 'v'))
                needed.add(index)
                cells[address] = {'shared_string_index': index}
        element.clear()
    resolved = {}
    index = 0
    for _, element in ET.iterparse(string_stream, events=['end']):
        if element.tag == NS + 'si':
            if index in needed:
                text = ''.join(t.text or '' for t in element.iter(NS + 't'))
                resolved[index] = ({'blocked_numeric_string': True} if
                    re.fullmatch(r'\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*', text)
                    else {'label_or_identity_text': text})
            index += 1
            element.clear()
    return {address: resolved[item['shared_string_index']] if 'shared_string_index' in item else item
            for address, item in cells.items()}


def main():
    acquisition = json.loads((LOG / 'RAW_ACQUISITION_FINAL.json').read_text(encoding='utf-8'))
    structure = json.loads((LOG / 'WORKBOOK_STRUCTURE.json').read_text(encoding='utf-8'))
    report = {'files': [], 'numeric_or_formula_values_decoded': 0}
    for item, metadata in zip(acquisition['files'], structure['files']):
        assert item['id'] == metadata['id']
        record = {'id': item['id'], 'filename': item['filename'], 'sheets': []}
        with ZipFile(item['body_path']) as archive:
            for sheet in metadata['sheets']:
                if sheet['name'] == 'Chemical Data':
                    allowed = {chr(col) + '1' for col in range(ord('A'), ord('K') + 1)}
                elif sheet['name'] == 'Counts':
                    allowed = {'A1'}
                elif sheet['name'] == 'Pass QC':
                    allowed = {c['ref'] for c in sheet['first_rows'][0]['cells'] if c['type'] == 's'}
                else:
                    allowed = {'A1', 'B1', 'A2', 'B2'}
                with archive.open(sheet['path']) as stream, archive.open('xl/sharedStrings.xml') as strings:
                    labels = selected_strings(stream, strings, allowed)
                record['sheets'].append({'name': sheet['name'], 'selected': sorted(allowed), 'labels': labels})
        report['files'].append(record)
    with (LOG / 'LABEL_PROJECTION.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
