import datetime
import hashlib
import json
from pathlib import Path
import requests

OUT = Path('log/20261023/mixed_feedback_estimator/prior')
OUT.mkdir(parents=True, exist_ok=True)
queries = [
    'low rank adaptation gradient initialization task aware 2025',
    'multi fidelity active learning vector scalar observations decision 2025',
    'reduced rank regression heterogeneous response linear measurements 2025',
]
receipts = []
for i, query in enumerate(queries):
    url = 'https://api.crossref.org/works'
    response = requests.get(url, params={'query': query, 'filter': 'from-pub-date:2025-01-01,until-pub-date:2026-10-23', 'rows': 6}, timeout=45)
    body = response.content
    name = f'search_{i}.json'
    (OUT / name).write_bytes(body)
    receipt = {'query': query, 'url': response.url, 'status': response.status_code,
               'sha256': hashlib.sha256(body).hexdigest(), 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if response.status_code == 200:
        receipt['titles'] = [{'title': item.get('title'), 'DOI': item.get('DOI'), 'URL': item.get('URL')}
                             for item in response.json()['message']['items']]
    receipts.append(receipt)
(OUT / 'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
print(json.dumps(receipts, indent=2))
