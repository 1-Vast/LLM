"""Complete schema projection locally, including valid inline-string workbooks."""
import hashlib
import io
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/mechanism_reentry'
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
rel = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
books = []
with zipfile.ZipFile(OUT/'all597_supplements.body') as package:
    for name in package.namelist():
        if not name.endswith('.xlsx'):
            continue
        raw = package.read(name)
        book = dict(name=name, sha256=hashlib.sha256(raw).hexdigest(), sheets=[])
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            strings = ([''.join(node.itertext()) for node in
                       ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', ns)]
                       if 'xl/sharedStrings.xml' in archive.namelist() else [])
            relations = {node.attrib['Id']: node.attrib['Target'] for node in
                         ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
            for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', ns):
                target = relations[sheet.attrib[rel]]
                target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
                xml = ET.fromstring(archive.read(target))
                text = []
                for cell in xml.findall('s:sheetData/s:row[@r="1"]/s:c', ns):
                    if cell.find('s:f', ns) is not None:
                        continue
                    if cell.attrib.get('t') == 's':
                        value = strings[int(cell.findtext('s:v', namespaces=ns))]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('s:is', ns).itertext())
                    else:
                        continue
                    try:
                        float(value)
                    except ValueError:
                        text.append(dict(cell=cell.attrib['r'], text=value))
                dimension = xml.find('s:dimension', ns)
                book['sheets'].append(dict(name=sheet.attrib['name'],
                    dimension=dimension.attrib if dimension is not None else None, row1_text=text))
        books.append(book)
output = dict(workbooks=books, http_requests=0,
    contract_sha256=hashlib.sha256((OUT/'ALL597_SCHEMA_PROTOCOL.md').read_bytes()).hexdigest(),
    correction='Inline-string workbooks need not contain sharedStrings; original failed projection and receipt retained.',
    scope='row1 text/sheet dimensions only; no numeric export, PDF reading or fits')
(OUT/'ALL597_SCHEMA_COMPLETE.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
print(json.dumps(output, indent=2))
