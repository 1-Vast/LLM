"""Read one metadata-nominated primary, retaining full body and bounded source facts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_signal_reassessment/root_sources'
assert not (OUT / 'plk1.body').exists()
url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12230241/fullTextXML'
response = requests.get(url, timeout=60)
(OUT / 'plk1.body').write_bytes(response.content)
(OUT / 'plk1.receipt.json').write_text(json.dumps({
    'url': url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
tree = ET.fromstring(response.content)
lines = [' '.join(' '.join(node.itertext()).split()) for node in tree.iter()
         if node.tag in ('article-title', 'title', 'p', 'data-availability')]
(OUT / 'plk1.txt').write_text('\n'.join(lines), encoding='utf-8')
keys = ('availability', 'accession', 'deposited', 'geo', 'perturb-seq', 'viability', 'screen')
selected = [{'paragraph': i, 'text': line} for i, line in enumerate(lines)
            if any(key in line.lower() for key in keys)]
(OUT / 'PLK1_PASSAGES.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print(json.dumps({'paragraphs': len(lines), 'selected': len(selected)}))
