import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

out = Path('log/20261023/observation_law_search/constructive')
url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12628168/fullTextXML'
try:
    with urllib.request.urlopen(url, timeout=35) as response:
        body, status = response.read(), response.status
except Exception as error:
    body, status = str(error).encode(), 'ERROR'
(out / 'fatepredictor.body').write_bytes(body)
(out / 'FULLTEXT_RECEIPT.json').write_text(json.dumps({'url': url, 'status': status, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}, indent=2), encoding='utf-8')
if status == 200:
    root = ET.fromstring(body)
    selected = []
    for node in root.findall('.//p'):
        text = ''.join(node.itertext())
        if any(term in text.lower() for term in ['birth', 'death', 'unbalanced', 'growth rate', 'proliferat', 'deepuot', 'deepruot']):
            selected.append(text)
    (out / 'FATEPREDICTOR_SELECTED.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
    print(json.dumps(selected, ensure_ascii=False))
