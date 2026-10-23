"""One canonical primary-page attempt and a narrowly identified legacy primary search."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
OUT.mkdir(parents=True, exist_ok=True)


def fetch(name, url, params=None):
    assert not (OUT / (name + '.body')).exists()
    response = requests.get(url, params=params, timeout=45)
    (OUT / (name + '.body')).write_bytes(response.content)
    receipt = {'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
               'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
               'retry_after': response.headers.get('Retry-After'), 'content_type': response.headers.get('Content-Type')}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
    return response


with ThreadPoolExecutor(max_workers=2) as pool:
    html = pool.submit(fetch, 'cancer16_html', 'https://www.biorxiv.org/content/10.64898/2026.08.24.746802v1.full')
    legacy = pool.submit(fetch, 'replogle_search', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                         {'query': 'TITLE:"Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq"',
                          'format': 'json', 'pageSize': 3, 'resultType': 'core'})
    html.result()
    result = legacy.result()
    result.raise_for_status()
    entries = [{key: item.get(key) for key in ('id', 'pmcid', 'title', 'doi', 'firstPublicationDate', 'abstractText', 'fullTextUrlList')}
               for item in result.json().get('resultList', {}).get('result', [])]
    (OUT / 'REPlOGLE_IDENTITIES.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
    print(json.dumps(entries, indent=2))
