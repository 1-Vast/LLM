"""Fetch three actual primary texts/landing pages with bounded requests."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/observation_law_search/root_sources'
SOURCES = [
    ('stochastic_landscape', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13557085/fullTextXML'),
    ('multiscale_network', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13434742/fullTextXML'),
    ('inverse_transport', 'https://www.biorxiv.org/content/10.64898/2026.10.01.756056v1.full'),
]


def fetch(item):
    name, url = item
    receipt = {'name': name, 'requested_url': url, 'started_utc': datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=35)
        body = response.content
        (OUT / (name + '.fulltext.body')).write_bytes(body)
        receipt.update(status=response.status_code, final_url=response.url, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        if response.ok and 'fullTextXML' in url:
            tree = ET.fromstring(body)
            title = tree.find('.//article-title')
            receipt['title'] = ''.join(title.itertext()) if title is not None else None
            paragraphs = [' '.join(''.join(p.itertext()).split()) for p in tree.iter('p')]
            (OUT / (name + '.txt')).write_text('\n\n'.join(paragraphs), encoding='utf-8')
            terms = ['growth', 'death', 'prolifer', 'identif', 'intervention', 'drug', 'limitation', 'github', 'data avail']
            selected = [p for p in paragraphs if any(term in p.lower() for term in terms)]
            (OUT / (name + '.selected.txt')).write_text('\n\n'.join(selected), encoding='utf-8')
            receipt.update(paragraphs=len(paragraphs), selected=len(selected))
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    (OUT / (name + '.fulltext.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch, SOURCES))
    (OUT.parent / 'ROOT_FULLTEXT.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
