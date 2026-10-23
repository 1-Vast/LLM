"""Probe one public publisher asset URI derived from its authenticated PII.

The URI convention is an explicit hypothesis, not a link observed in the article.
Any returned workbook must be authenticated from its own schema before use.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/replogle_growth_acquisition/root_sources'
asset = sys.argv[1] if len(sys.argv) > 1 else '2'
assert asset in ('1', '2')
stem = 'public_asset' if asset == '2' else 'public_asset1'
assert not (OUT / (stem + '.body')).exists()
url = 'https://ars.els-cdn.com/content/image/1-s2.0-S0092867422005979-mmc' + asset + '.xlsx'
response = requests.get(url, timeout=45)
(OUT / (stem + '.body')).write_bytes(response.content)
receipt = {'url': url, 'uri_basis': 'Publisher convention plus Crossref-confirmed PII; not an observed article link',
           'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
           'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
           'content_type': response.headers.get('Content-Type'), 'zip_signature': response.content[:2] == b'PK'}
(OUT / (stem + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
response.raise_for_status()
assert receipt['zip_signature'], 'Not a workbook; no numerical values parsed'
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
                                row[cell.get('r')] = strings[int(cell.find('m:v', ns).text)]
                            elif cell.get('t') == 'inlineStr':
                                row[cell.get('r')] = ''.join(cell.itertext())
                        rows.append(row)
                        node.clear()
            headers[filename] = rows
result = {'sheets': sheets, 'first_three_rows_strings_only': headers}
(OUT / (stem.upper() + '_SCHEMA.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
