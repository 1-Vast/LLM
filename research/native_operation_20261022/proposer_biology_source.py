from pathlib import Path
import requests
import hashlib
import json
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

base = Path('D:/MAESTRO/log/20261022/native_operation/proposer/sources')
url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3501264/fullTextXML'
path = base / 'sequential_cell_fulltext.xml'
if path.exists():
    raise RuntimeError('Refusing overwrite')
r = requests.get(url, timeout=35)
path.write_bytes(r.content)
row = dict(url=url, final_url=r.url, status=r.status_code, bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(), utc=datetime.now(timezone.utc).isoformat())
(base / 'BIOLOGY_RECEIPT.json').write_text(json.dumps(row, indent=2), encoding='utf-8')
print(json.dumps(row))
if r.status_code == 200:
    tree = ET.fromstring(r.content)
    for node in tree.findall('.//sec'):
        title = ''.join(node.find('title').itertext()) if node.find('title') is not None else ''
        if any(term in title.lower() for term in ['experimental procedures', 'methods', 'supplemental']):
            print(title, ' '.join(node.itertext())[:15000])
    for node in tree.findall('.//supplementary-material'):
        print('SUPPLEMENT_METADATA', ET.tostring(node, encoding='unicode')[:2000])
