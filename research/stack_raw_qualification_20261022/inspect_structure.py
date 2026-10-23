"""Project OOXML structure only, without reading any cell values or formulas."""
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/stack_raw_qualification'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def sheets(archive):
    relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
    targets = {r.attrib['Id']: r.attrib['Target'] for r in relationships}
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    return [{'name': sheet.attrib['name'],
             'path': posixpath.normpath(posixpath.join('xl', targets[sheet.attrib[RID]]))}
            for sheet in workbook.find(NS + 'sheets')]


def structure(stream):
    result = {'dimension': None, 'first_rows': []}
    for event, element in ET.iterparse(stream, events=['start', 'end']):
        if event == 'start' and element.tag == NS + 'dimension':
            result['dimension'] = element.attrib.get('ref')
        if event == 'end' and element.tag == NS + 'row':
            result['first_rows'].append({'row': element.attrib.get('r'),
                'cells': [{'ref': c.attrib['r'], 'type': c.attrib.get('t', 'n'),
                           'has_formula': c.find(NS + 'f') is not None}
                          for c in element.findall(NS + 'c')]})
            element.clear()
            if len(result['first_rows']) == 2:
                break
    return result


def main():
    acquisition = json.loads((LOG / 'RAW_ACQUISITION_FINAL.json').read_text(encoding='utf-8'))
    assert acquisition['all_qualified']
    report = {'files': [], 'cell_values_decoded': 0, 'formula_bodies_decoded': 0}
    for item in acquisition['files']:
        record = {'id': item['id'], 'filename': item['filename'], 'sheets': []}
        with ZipFile(item['body_path']) as archive:
            for sheet in sheets(archive):
                with archive.open(sheet['path']) as stream:
                    record['sheets'].append({**sheet, **structure(stream)})
        report['files'].append(record)
    with (LOG / 'WORKBOOK_STRUCTURE.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    for item in report['files']:
        print(item['filename'])
        for sheet in item['sheets']:
            print(json.dumps({**sheet, 'first_rows': [
                {**row, 'cells': row['cells'][:8], 'cell_count': len(row['cells'])}
                for row in sheet['first_rows']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
