"""Fetch a single primary and retain methods/availability, without assay fitting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/regrowth_data_qualification/root'

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'clpp_primary.receipt.json'
    assert not target.exists()
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13578376/fullTextXML'
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), url=url,
                   purpose='Read one distinct retained-search primary for withdrawal persistence and source-data qualification')
    response = requests.get(url, timeout=45)
    payload = response.content
    (OUT / 'clpp_primary.body').write_bytes(payload)
    receipt.update(status=response.status_code, bytes=len(payload),
                   sha256=hashlib.sha256(payload).hexdigest())
    target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
    if response.status_code != 200:
        raise SystemExit(1)
    tree = ET.fromstring(payload)
    selected = []
    for p in tree.iter('p'):
        text = ' '.join(''.join(p.itertext()).split())
        if any(term in text.lower() for term in ('data availab', 'source data', 'washout', 'wash-out', 'github', 'zenodo', 'figshare')):
            selected.append(text)
    projection = dict(paragraphs=selected,
                      supplements=[ET.tostring(e, encoding='unicode') for e in tree.findall('.//supplementary-material')])
    (OUT / 'clpp_primary.projection.json').write_text(json.dumps(projection, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(projection, ensure_ascii=False, indent=2))
