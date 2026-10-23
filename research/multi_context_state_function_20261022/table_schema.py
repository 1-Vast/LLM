"""Fetch the exact NIH manuscript supplemental workbook, inspect headers only."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
name = 'NIHMS1812939-supplement-11.xlsx'
url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/9380471/bin/' + name
assert not (OUT / name).exists()
response = requests.get(url, timeout=45)
(OUT / name).write_bytes(response.content)
receipt = {'url': url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
           'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
           'content_type': response.headers.get('Content-Type'), 'zip_signature': response.content[:2] == b'PK'}
(OUT / 'growth_workbook.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
response.raise_for_status()
if not receipt['zip_signature']:
    print('NOT_A_WORKBOOK: retained response, no values parsed')
    raise SystemExit(2)
ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
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
result = {'sheets': sheets, 'first_three_rows_strings_only': headers}
(OUT / 'GROWTH_WORKBOOK_HEADER_SCHEMA.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
