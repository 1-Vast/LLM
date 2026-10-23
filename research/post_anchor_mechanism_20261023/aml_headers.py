"""Project only predeclared header text; no numerical worksheet values."""
import hashlib
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261023/post_anchor_mechanism/root_sources'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
result=[]
for number in [3,6]:
    path=OUT/f'41467_2026_74989_MOESM{number}_ESM.xlsx'
    with zipfile.ZipFile(path) as archive:
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings=[''.join(n.itertext()) for n in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si',NS)]
        relations={n.attrib['Id']:n.attrib['Target'] for n in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets=ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet',NS)
        book=dict(filename=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),sheets=[])
        for sheet in sheets:
            target=relations[sheet.attrib['{'+REL+'}id']]
            member=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            xml=ET.fromstring(archive.read(member))
            headers=[]
            for row in xml.findall('s:sheetData/s:row',NS):
                if int(row.attrib['r'])>2:continue
                for cell in row.findall('s:c',NS):
                    if cell.find('s:f',NS) is not None:continue
                    kind=cell.attrib.get('t')
                    value=cell.findtext('s:v',default='',namespaces=NS)
                    if kind=='s':text=strings[int(value)]
                    elif kind=='inlineStr':text=''.join(cell.find('s:is',NS).itertext())
                    else:continue
                    headers.append(dict(cell=cell.attrib['r'],text=text))
            dimension=xml.find('s:dimension',NS)
            book['sheets'].append(dict(name=sheet.attrib['name'],dimension=dimension.attrib if dimension is not None else None,headers=headers))
        result.append(book)
record=dict(contract_sha256=hashlib.sha256((OUT.parent/'HEADER_PROTOCOL.md').read_bytes()).hexdigest(),
            worksheet_numeric_values_exported=False,formula_text_exported=False,rows_text_exported=[1,2],workbooks=result)
(OUT/'AML_HEADERS.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
