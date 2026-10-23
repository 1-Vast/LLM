"""Read the identified open primary and inventory actual functional/data passages."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'replogle.body').exists()
response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9380471/fullTextXML', timeout=45)
(OUT / 'replogle.body').write_bytes(response.content)
(OUT / 'replogle.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
tree = ET.fromstring(response.content)
paragraphs = [' '.join(' '.join(item.itertext()).split()) for item in tree.iter('p')]
(OUT / 'replogle.paragraphs.json').write_text(json.dumps(paragraphs, indent=2), encoding='utf-8')
terms = ('fitness', 'growth phenotype', 'growth screen', 'growth rate', 'availability', 'accession', 'GSE', 'figshare', 'download')
selected = [{'index': i, 'text': text} for i, text in enumerate(paragraphs) if any(term.lower() in text.lower() for term in terms)]
(OUT / 'REPlOGLE_PASSAGES.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print(json.dumps(selected, indent=2))
