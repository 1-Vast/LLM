"""Project frozen ID/pair metadata and read only the declared S2 workbook."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/az_chemical_identity'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

census_path = ROOT / 'log/20261022/intervention_program_renewal/az_design/CENSUS.json'
design_path = ROOT / 'log/20261022/az_paid_reference_gate/DESIGN.json'
census = load_json(census_path)
design = load_json(design_path)
ids = census['overall']['drug_ids']
projection = {'source_drug_ids': ids,
              'source_member_drug_ids': {key: value['drug_ids'] for key, value in census['by_member'].items()},
              'query_pairs': design['query_pairs'], 'target_pairs': design['target_pairs'],
              'local_source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                      for path in (census_path, design_path)}}
assert len(ids) == len(set(ids)) == 46
assert len(projection['query_pairs']) == 13
assert len(projection['target_pairs']) == 12
projection['design_ids'] = sorted(set(sum(design['query_pairs'] + design['target_pairs'], [])), key=int)
projection['source_id_pair_overlap'] = sorted(
    set(map(tuple, design['query_pairs'])) & set(map(tuple, design['target_pairs'])))
(OUT / 'SOURCE_ID_PROJECTION.json').write_text(
    json.dumps(projection, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
book_path = OUT / 'EMS194010-supplement-Table_S2.xlsx'
if book_path.exists():
    sheets = []
    with zipfile.ZipFile(book_path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(si.itertext()) for si in
                       ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        relationships = {node.attrib['Id']: node.attrib['Target']
                         for node in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        for sheet in book.findall('s:sheets/s:sheet', NS):
            target = relationships[sheet.attrib['{' + NS['r'] + '}id']]
            target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            rows = []
            for row in ET.fromstring(archive.read(target)).findall('s:sheetData/s:row', NS):
                cells = {}
                for cell in row.findall('s:c', NS):
                    value = cell.find('s:v', NS)
                    text = value.text if value is not None else ''
                    if cell.attrib.get('t') == 's' and text:
                        text = strings[int(text)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        text = ''.join(cell.find('s:is', NS).itertext())
                    if text:
                        cells[cell.attrib['r']] = text
                if cells:
                    rows.append({'row': row.attrib['r'], 'cells': cells})
            sheets.append({'sheet': sheet.attrib['name'], 'rows': rows})
    (OUT / 'S2_CELL_PROJECTION.json').write_text(
        json.dumps({'sheets': sheets}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sheets': [{'sheet': s['sheet'], 'rows': len(s['rows']),
                                 'first_rows': s['rows'][:5]} for s in sheets]}, ensure_ascii=False))
else:
    print(json.dumps({'source_drug_ids': len(ids), 'design_ids': projection['design_ids'],
                      's2_recovered': False, 'source_id_pair_overlap': projection['source_id_pair_overlap']}))
