"""Acquire one exact primary identified in the index, with limited Methods projection."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/functional_mechanism_frontier/root_sources'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13600678/fullTextXML'
assert not (OUT / 'uncertainty.receipt.json').exists()
record = dict(url=URL, utc=datetime.now(timezone.utc).isoformat(), purpose='Exact 2026 drug-response uncertainty/feedback primary; no author code or data')
try:
    response = requests.get(URL, timeout=45)
    (OUT / 'uncertainty.body').write_bytes(response.content)
    record.update(status=response.status_code, bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest())
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        selected = []
        for sec in root.findall('.//sec'):
            title = ' '.join(sec.findtext('title', '').split())
            if any(key in title.lower() for key in ['uncertain', 'active', 'method', 'acquisition', 'calibrat', 'experimental setup']):
                selected.append(dict(title=title, paragraphs=[' '.join(''.join(p.itertext()).split()) for p in sec.findall('p')]))
        (OUT / 'uncertainty.METHODS.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
        print(json.dumps(selected, indent=2))
except Exception as error:
    record.update(error_type=type(error).__name__, error=str(error))
finally:
    (OUT / 'uncertainty.receipt.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
