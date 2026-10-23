"""Inspect first invalid selected Count serialization; do not read adjacent outcomes."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/next_mechanism/source/cdk_review'
OUT = ROOT / 'log/20261022/cdk_middle_feedback'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def strings(archive):
    result = []
    with archive.open('xl/sharedStrings.xml') as stream:
        for _, element in ET.iterparse(stream, events=('end',)):
            if element.tag == NS + 'si':
                result.append(''.join(t.text or '' for t in element.iter(NS + 't')))
                element.clear()
    return result


def sheet_members(archive):
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
    by_id = {r.attrib['Id']: r.attrib['Target'] for r in rels}
    result = {}
    for sheet in workbook.find(NS + 'sheets'):
        target = by_id[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        result[sheet.attrib['name']] = target.lstrip('/') if target.startswith('/') else 'xl/' + target
    return result


def cell_value(cell, shared):
    node = cell.find(NS + 'v')
    raw = node.text if node is not None else None
    if cell.attrib.get('t') == 's' and raw is not None:
        return shared[int(raw)]
    if cell.attrib.get('t') == 'inlineStr':
        return ''.join(t.text or '' for t in cell.iter(NS + 't'))
    return raw


def main():
    chosen = [b for b in json.loads((SOURCE / 'SAMPLE_HEADER_CONTRACT.json').read_text())['bindings'] if b['treatment_label'] != 'Veh']
    findings = []
    with zipfile.ZipFile(SOURCE / 'table_s3.body') as archive:
        shared = strings(archive)
        members = sheet_members(archive)
        for sheet in dict.fromkeys(b['sheet'] for b in chosen):
            columns = {b['count_column'].rstrip('0123456789') for b in chosen if b['sheet'] == sheet}
            fractions = {b['count_column'].rstrip('0123456789'): b['fraction_column'].rstrip('0123456789') for b in chosen if b['sheet'] == sheet}
            with archive.open(members[sheet]) as stream:
                for _, element in ET.iterparse(stream, events=('end',)):
                    if element.tag != NS + 'row':
                        continue
                    if int(element.attrib['r']) > 1:
                        cells = {c.attrib.get('r', '').rstrip('0123456789'): c for c in element}
                        for column in columns - cells.keys():
                            fraction = cells.get(fractions[column])
                            findings.append({'sheet': sheet, 'cell': column + element.attrib['r'],
                                             'missing_count_cell': True,
                                             'fraction_serialization': None if fraction is None else cell_value(fraction, shared)})
                            if len(findings) >= 6:
                                break
                        for cell in element:
                            address = cell.attrib.get('r', '')
                            if address.rstrip('0123456789') not in columns:
                                continue
                            value = cell_value(cell, shared)
                            try:
                                float(value)
                            except (ValueError, TypeError):
                                findings.append({'sheet': sheet, 'cell': address, 'serialization_type': cell.attrib.get('t', 'numeric'),
                                                 'value': value, 'has_formula': cell.find(NS + 'f') is not None})
                            if len(findings) >= 6:
                                break
                    element.clear()
                    if len(findings) >= 6:
                        break
    (OUT / 'COUNT_SERIALIZATION_DIAGNOSTIC.json').write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print(json.dumps(findings, indent=2))


if __name__ == '__main__':
    main()
