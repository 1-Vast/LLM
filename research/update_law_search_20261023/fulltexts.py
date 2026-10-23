"""Retrieve selected primary full texts; retain status and relevant paragraphs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/update_law_search/root_sources'
IDS = ['PMC13605750', 'PMC13341120', 'PMC13557097']


def fetch(pmc):
    url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML'
    receipt = {'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=35)
        body = response.content
        (OUT / (pmc + '.xml')).write_bytes(body)
        receipt.update(status=response.status_code, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        if response.ok:
            tree = ET.fromstring(body)
            paragraphs = [' '.join(''.join(p.itertext()).split()) for p in tree.iter('p')]
            text = '\n'.join(paragraphs)
            (OUT / (pmc + '.txt')).write_text(text, encoding='utf-8')
            terms = ['adapt', 'feedback', 'operator', 'baseline', 'data avail', 'github', 'control', 'identif', 'function', 'retrain']
            selected = [p for p in paragraphs if any(t in p.lower() for t in terms)]
            (OUT / (pmc + '.selected.txt')).write_text('\n\n'.join(selected), encoding='utf-8')
            receipt.update(title=''.join(tree.find('.//article-title').itertext()), paragraphs=len(paragraphs), selected=len(selected))
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    (OUT / (pmc + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(fetch, IDS)), indent=2))
