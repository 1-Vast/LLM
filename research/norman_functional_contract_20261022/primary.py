"""Read primary text and author source; do not display notebook outputs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract/root_sources'
revision = '3b25109aeb9c0c2026bd70abd50304a0ad4e5395'
urls = [
    ('primary_bioc', 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC6746554/unicode'),
    ('population', f'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/{revision}/GI_generate_populations.ipynb'),
]


def fetch(item):
    name, url = item
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / (name + '.body')).write_bytes(data)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if response.status_code == 200:
        if name == 'population':
            book = response.json()
            text = '\n\n'.join(''.join(c.get('source', [])) for c in book['cells'])
        else:
            xml = ET.fromstring(data)
            text = '\n\n'.join(n.text or '' for n in xml.iter('text'))
        (OUT / (name + '.source.txt')).write_text(text, encoding='utf-8')
    return receipt


with ThreadPoolExecutor(max_workers=2) as pool:
    for result in pool.map(fetch, urls):
        print(json.dumps(result))
