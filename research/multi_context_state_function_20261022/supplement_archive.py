"""Use the official EuropePMC supplement service; inspect workbook headers only."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'supplements.body').exists()
url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9380471/supplementaryFiles'
response = requests.get(url, timeout=60)
(OUT / 'supplements.body').write_bytes(response.content)
receipt = {'url': url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
           'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
           'content_type': response.headers.get('Content-Type'), 'zip_signature': response.content[:2] == b'PK'}
(OUT / 'supplements.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
response.raise_for_status()
if not receipt['zip_signature']:
    print('NOT_AN_ARCHIVE: retained response without parsing values')
    raise SystemExit(2)
with zipfile.ZipFile(io.BytesIO(response.content)) as outer:
    inventory = [{'name': entry.filename, 'bytes': entry.file_size} for entry in outer.infolist()]
    (OUT / 'SUPPLEMENT_ARCHIVE_INVENTORY.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    workbooks = {}
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for name in outer.namelist():
        if name.endswith('.xlsx'):
            with zipfile.ZipFile(io.BytesIO(outer.read(name))) as archive:
                workbook = ET.fromstring(archive.read('xl/workbook.xml'))
                sheets = [node.attrib for node in workbook.findall('m:sheets/m:sheet', ns)]
                strings = []
                if 'xl/sharedStrings.xml' in archive.namelist():
                    strings = [''.join(item.itertext()) for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
                headers = {}
                for filename in archive.namelist():
                    if filename.startswith('xl/worksheets/sheet') and filename.endswith('.xml'):
                        rows = []
                        with archive.open(filename) as stream:
                            for _, node in ET.iterparse(stream, events=('end',)):
                                if node.tag == '{' + ns['m'] + '}row':
                                    if int(node.get('r')) > 3:
                                        break
                                    row = {}
                                    for cell in node:
                                        if cell.get('t') == 's':
                                            value = cell.find('m:v', ns)
                                            row[cell.get('r')] = strings[int(value.text)]
                                        elif cell.get('t') == 'inlineStr':
                                            row[cell.get('r')] = ''.join(cell.itertext())
                                    rows.append(row)
                                    node.clear()
                        headers[filename] = rows
                workbooks[name] = {'sheets': sheets, 'first_three_rows_strings_only': headers}
    (OUT / 'SUPPLEMENT_WORKBOOK_SCHEMAS.json').write_text(json.dumps(workbooks, indent=2), encoding='utf-8')
print(json.dumps(workbooks, indent=2)[:18000])
