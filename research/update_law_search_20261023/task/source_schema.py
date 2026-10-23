"""Acquire one author-linked supplement and inspect headers, never outcome values."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/update_law_search/task'
OUT.mkdir(parents=True, exist_ok=True)
links = json.loads((ROOT / 'log/20261023/function_update_renewal/root_sources/multilineage.links.json').read_text())
url = next(x for x in links if 'MOESM4_ESM.xlsx' in x)
request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO public research'})
try:
    with urllib.request.urlopen(request, timeout=50) as response:
        body = response.read(12_000_001)
        receipt = {'url': url, 'status': response.status, 'final_url': response.url,
                   'bytes': len(body), 'content_type': response.headers.get('Content-Type')}
    (OUT / 'interaction_supplement.body').write_bytes(body)
    receipt['sha256'] = hashlib.sha256(body).hexdigest()
    if len(body) > 12_000_000:
        receipt['schema_status'] = 'BODY_CAPPED_NOT_PARSED'
    else:
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            shared = []
            if 'xl/sharedStrings.xml' in z.namelist():
                shared = [''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)]
            workbook = ET.fromstring(z.read('xl/workbook.xml'))
            sheets = [{'name': e.attrib['name'], 'sheet_id': e.attrib['sheetId']} for e in workbook.findall('s:sheets/s:sheet', ns)]
            schema = []
            for name in z.namelist():
                if not name.startswith('xl/worksheets/sheet') or not name.endswith('.xml'):
                    continue
                tree = ET.fromstring(z.read(name))
                rows = tree.findall('s:sheetData/s:row', ns)
                header = []
                if rows:
                    for cell in rows[0]:
                        kind = cell.attrib.get('t')
                        v = cell.find('s:v', ns)
                        # Only textual header cells are emitted; no numeric casts.
                        value = shared[int(v.text)] if kind == 's' and v is not None else ''.join(cell.find('s:is', ns).itertext()) if kind == 'inlineStr' else '<NON_TEXT_HEADER>'
                        header.append([cell.attrib.get('r'), value])
                schema.append({'member': name, 'row_count': len(rows), 'textual_first_row': header})
            (OUT / 'SUPPLEMENT_SCHEMA.json').write_text(json.dumps({'sheets': sheets, 'schema': schema}, indent=2), encoding='utf-8')
        receipt['schema_status'] = 'TEXT_HEADER_ONLY'
except Exception as error:
    receipt = {'url': url, 'error_type': type(error).__name__, 'error': str(error)}
(OUT / 'SOURCE_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt))
