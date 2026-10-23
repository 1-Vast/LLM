"""Authenticate author full texts and exact-title index responses."""
from discover import OUT, fetch
import concurrent.futures
import hashlib
import json
import requests
import xml.etree.ElementTree as ET

PAPERS = {'bestdr': 'PMC13055639', 'melanoma_combo': 'PMC13338063', 'egf_benchmark': 'PMC12949236'}

def fulltext(item):
    name, pmcid = item
    url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML'
    response = requests.get(url, timeout=90)
    with (OUT / (name + '_fulltext.body')).open('xb') as f:
        f.write(response.content)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}
    (OUT / (name + '_fulltext.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    rows = []
    if response.ok:
        root = ET.fromstring(response.content)
        for node in root.iter():
            if node.tag in ('p', 'title', 'ext-link', 'supplementary-material'):
                value = ' '.join(''.join(node.itertext()).split())
                if any(word in value.lower() for word in ('data', 'github', 'zenodo', 'figshare', 'mitosis', 'division', 'death', 'time-lapse', 'doi.org')):
                    rows.append({'tag': node.tag, 'text': value, 'href': node.get('{http://www.w3.org/1999/xlink}href')})
    (OUT / (name + '_extraction.json')).write_text(json.dumps(rows, indent=2), encoding='utf-8')
    return {'name': name, **receipt, 'selected': [row for row in rows if any(k in row['text'].lower() for k in ('data availab', 'github', 'zenodo', 'figshare'))]}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fulltext, item) for item in PAPERS.items()]
        futures.append(pool.submit(fetch, ('hpn_exact', 'TITLE:"A Community Challenge to Evaluate the Inferability of Human Cell Signaling Networks"')))
        for future in futures:
            print(json.dumps(future.result()))
