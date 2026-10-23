"""Fetch only the exact JATS location returned by the official bioRxiv API."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/plk1_payload_qualification/alternative'
record = json.loads((OUT / 'biorxiv.body').read_bytes())['collection'][0]
assert not (OUT / 'primary.body').exists()
response = requests.get(record['jatsxml'], timeout=45)
(OUT / 'primary.body').write_bytes(response.content)
(OUT / 'primary.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
tree = ET.fromstring(response.content)
paragraphs = [' '.join(' '.join(item.itertext()).split()) for item in tree.iter('p')]
(OUT / 'primary.paragraphs.json').write_text(json.dumps(paragraphs, indent=2), encoding='utf-8')
terms = ('availability', 'accession', 'figshare', 'zenodo', 'depmap', 'fitness', 'viability', 'GSE', 'GEO', 'download')
selected = [{'index': i, 'text': text} for i, text in enumerate(paragraphs) if any(term.lower() in text.lower() for term in terms)]
(OUT / 'DATA_PASSAGES.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print(json.dumps(selected, indent=2)[:18000])
