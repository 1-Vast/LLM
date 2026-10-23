"""One official supplement package; export workbook schema only."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/mechanism_reentry'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12301861/supplementaryFiles'
record = dict(url=URL, utc=datetime.now(timezone.utc).isoformat(),
               contract_sha256=hashlib.sha256((OUT/'ALL597_SCHEMA_PROTOCOL.md').read_bytes()).hexdigest())
body = bytearray()
books = []
members = []
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
rel = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
try:
    with requests.get(URL, stream=True, timeout=40) as response:
        record['status'] = response.status_code
        for part in response.iter_content(65536):
            if len(body)+len(part) > 16*1024*1024:
                record['stop'] = 'COMPRESSED_CAP'
                break
            body.extend(part)
        else:
            record['stop'] = 'COMPLETE'
    if record['status'] == 200 and record['stop'] == 'COMPLETE':
        with zipfile.ZipFile(io.BytesIO(body)) as package:
            members = [dict(name=item.filename, bytes=item.file_size) for item in package.infolist()]
            for member in members:
                if not member['name'].endswith('.xlsx'):
                    continue
                raw = package.read(member['name'])
                book = dict(name=member['name'], sha256=hashlib.sha256(raw).hexdigest(), sheets=[])
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    strings = [''.join(node.itertext()) for node in
                        ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', ns)]
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
                                continue
                            except ValueError:
                                text.append(dict(cell=cell.attrib['r'], text=value))
                        dimension = xml.find('s:dimension', ns)
                        book['sheets'].append(dict(name=sheet.attrib['name'],
                            dimension=dimension.attrib if dimension is not None else None, row1_text=text))
                books.append(book)
except Exception as error:
    record.update(error_type=type(error).__name__, error=str(error))
record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
(OUT/'all597_supplements.body').write_bytes(body)
(OUT/'all597_supplements.receipt.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
output = dict(receipt=record, members=members, workbooks=books,
              scope='row1 text/sheet dimensions only; no numeric export, PDF reading or fits')
(OUT/'ALL597_SCHEMA.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
print(json.dumps(output, indent=2))
