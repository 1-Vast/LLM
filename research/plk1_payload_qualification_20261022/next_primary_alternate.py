"""One independent official-index route after bioRxiv rate limiting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/plk1_payload_qualification/alternative'
assert not (OUT / 'epmc_primary.body').exists()
response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/PPR1305187/fullTextXML', timeout=45)
(OUT / 'epmc_primary.body').write_bytes(response.content)
(OUT / 'epmc_primary.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
    'retry_after': response.headers.get('Retry-After')}, indent=2), encoding='utf-8')
print('HTTP', response.status_code, 'bytes', len(response.content))
response.raise_for_status()
tree = ET.fromstring(response.content)
paragraphs = [' '.join(' '.join(item.itertext()).split()) for item in tree.iter('p')]
(OUT / 'epmc_primary.paragraphs.json').write_text(json.dumps(paragraphs, indent=2), encoding='utf-8')
terms = ('availability', 'accession', 'figshare', 'zenodo', 'depmap', 'fitness', 'viability', 'GSE', 'GEO', 'download')
selected = [{'index': i, 'text': text} for i, text in enumerate(paragraphs) if any(term.lower() in text.lower() for term in terms)]
(OUT / 'EPMC_DATA_PASSAGES.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print(json.dumps(selected, indent=2)[:17000])
