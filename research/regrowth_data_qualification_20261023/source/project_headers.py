"""Project workbook identities and rows 1-2 textual headers; never cast numeric cells."""
from pathlib import Path
import io
import json
import zipfile
import xml.etree.ElementTree as ET

out = Path('log/20261023/regrowth_data_qualification/source')
tables = zipfile.ZipFile(out / 'TABLES_ORIGINAL.zip')
raw = tables.read('aec5436_tables_s1_to_s7.xlsx')
(out / 'TABLE_WORKBOOK_ORIGINAL.xlsx').write_bytes(raw)
book = zipfile.ZipFile(io.BytesIO(raw))
ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
rel_ns = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
rels = ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))
targets = {r.attrib['Id']: r.attrib['Target'] for r in rels}
wb = ET.fromstring(book.read('xl/workbook.xml'))
sheets = []
needed = set()
for sheet in wb.find('m:sheets', ns):
    target = targets[sheet.attrib[rel_ns]].lstrip('/')
    if not target.startswith('xl/'):
        target = 'xl/' + target
    cells = []
    with book.open(target) as stream:
        for _, row in ET.iterparse(stream, events=('end',)):
            if row.tag != '{' + ns['m'] + '}row':
                continue
            if int(row.attrib.get('r', '0')) > 2:
                break
            for cell in row.findall('m:c', ns):
                typ = cell.attrib.get('t')
                value = cell.find('m:v', ns)
                item = {'cell': cell.attrib['r'], 'type': typ or 'untyped_or_numeric_suppressed'}
                if typ == 's' and value is not None:
                    # This integer is a string-table index, never an assay value.
                    item['shared_string_index'] = int(value.text)
                    needed.add(item['shared_string_index'])
                elif typ == 'inlineStr':
                    item['text'] = ''.join(cell.find('m:is', ns).itertext())
                elif typ == 'str' and value is not None:
                    item['text'] = value.text
                cells.append(item)
            row.clear()
    sheets.append({'sheet': sheet.attrib['name'], 'worksheet_part': target,
                   'header_rows': [1, 2], 'cells': cells})
strings = {}
if needed:
    index = 0
    with book.open('xl/sharedStrings.xml') as stream:
        for _, elem in ET.iterparse(stream, events=('end',)):
            if elem.tag != '{' + ns['m'] + '}si':
                continue
            if index in needed:
                strings[index] = ''.join(elem.itertext())
            index += 1
            elem.clear()
            if len(strings) == len(needed):
                break
for sheet in sheets:
    for cell in sheet['cells']:
        if 'shared_string_index' in cell:
            cell['text'] = strings[cell.pop('shared_string_index')]
result = {'scope': 'sheet identities and rows 1-2 text only; numeric cells suppressed; no later rows projected',
          'sheets': sheets}
(out / 'HEADERS.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
