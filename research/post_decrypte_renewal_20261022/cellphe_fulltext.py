"""Fetch original paper prose only, not experimental datasets."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/skeptic/source'
url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10070448/fullTextXML'
start = datetime.now(timezone.utc).isoformat()
with urllib.request.urlopen(url, timeout=45) as r:
    body = r.read()
    receipt = {'url': url, 'final_url': r.url, 'status': r.status, 'headers': dict(r.headers),
               'started_utc': start, 'completed_utc': datetime.now(timezone.utc).isoformat(),
               'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
(OUT / 'CellPhe.fulltext.xml').write_bytes(body)
(OUT / 'CellPhe.fulltext.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
tree = ET.fromstring(body)
paragraphs = []
for p in tree.findall('.//body//p'):
    s = ''.join(p.itertext())
    if re.search(r'drug|death|died|paclitaxel|docetaxel|apoptos|availab|Zenodo|treated|functional|mitos|24.h', s, re.I):
        paragraphs.append(s)
for sec in tree.findall('.//back//sec'):
    title = sec.find('title')
    if title is not None and 'availability' in ''.join(title.itertext()).lower():
        paragraphs.append(''.join(sec.itertext()))
(OUT / 'CellPhe.targeted_prose.json').write_text(json.dumps(paragraphs, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(paragraphs, ensure_ascii=False, indent=2))
