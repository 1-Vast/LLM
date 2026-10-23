"""Retain retrieval bytes and receipts; no biological outcomes are accessed."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

OUT = Path('log/20261023/update_law_search/mechanism')
queries = ['PerturbODE gene regulatory network perturbation 2025',
           'modular response analysis reconstructing molecular pathways 2002',
           'predicting combinatorial perturbations causal gene regulatory network 2025 2026']
receipts = []
for i, q in enumerate(queries):
    url = 'https://api.openalex.org/works?' + urlencode({'search': q, 'per-page': 5})
    try:
        with urlopen(Request(url, headers={'User-Agent': 'MAESTRO research'}), timeout=40) as r:
            body = r.read()
            status = r.status
        (OUT / f'search_{i}.json').write_bytes(body)
        parsed = json.loads(body)
        projection = [{'id': v['id'], 'title': v['title'], 'doi': v['doi'],
                       'year': v['publication_year'], 'primary_location': v['primary_location'],
                       'abstract_inverted_index': v.get('abstract_inverted_index')}
                      for v in parsed['results']]
        (OUT / f'search_{i}_projection.json').write_text(json.dumps(projection, indent=2), encoding='utf8')
        receipts.append({'query': q, 'url': url, 'status': status,
                         'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()})
    except Exception as e:
        receipts.append({'query': q, 'url': url, 'error': repr(e)})
(OUT / 'SOURCE_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf8')
print(json.dumps(receipts, indent=2))
