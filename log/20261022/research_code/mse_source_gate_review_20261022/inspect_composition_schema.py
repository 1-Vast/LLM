"""Inspect worksheet relationships and headers; never read biological scalars."""
from pathlib import Path
import hashlib
import json
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/biological_decision_scout/sources'
OUT = ROOT / 'log/20261022/mse_source_gate_review/COMPOSITION_SCHEMA_INSPECTION.json'
FILE = SOURCE / 'complete_members/41467_2024_52694_MOESM6_ESM.xlsx'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
result = {'workbook_sha256': hashlib.sha256(FILE.read_bytes()).hexdigest(),
          'biological_scalar_reads': 0, 'sheets': []}
with ZipFile(FILE) as z:
    ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
    strings = [''.join(n.itertext()) for n in ss]
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = {r.attrib['Id']: r.attrib['Target'] for r in
            ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    for sheet in wb.find('m:sheets', NS):
        target = rels[sheet.attrib[RID]]
        path = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        xml = ET.fromstring(z.read(path))
        headers = []
        for row in xml.findall('m:sheetData/m:row', NS):
            if row.attrib['r'] != '1':
                continue
            for cell in row:
                assert cell.attrib.get('t') == 's'
                # This index is a header-string index, not a biological value.
                headers.append({'ref': cell.attrib['r'],
                                'label': strings[int(cell.find('m:v', NS).text)]})
        result['sheets'].append({'name': sheet.attrib['name'], 'relationship': sheet.attrib[RID],
                                 'xml_member': path, 'headers': headers})

primary = ET.parse(SOURCE / 'mse_primary.body')
result['primary_excerpts'] = []
for p in primary.iter('p'):
    value = ''.join(p.itertext())
    if 'Cell compositions per sample' in value or 'Supplementary Data 3' in value or 'cell-type abundances' in value:
        result['primary_excerpts'].append(value)
OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=True))
