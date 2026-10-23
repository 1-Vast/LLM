"""Bounded primary metadata lookup; no biological outcome acquisition."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

out = Path('log/20261023/observation_law_search/constructive')
out.mkdir(parents=True, exist_ok=True)
queries = ['TITLE_ABS:DeepRUOT', '(TITLE_ABS:"unbalanced optimal transport") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23] AND TITLE_ABS:cell']
receipts = []
for i, query in enumerate(queries):
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urllib.parse.urlencode({'query': query, 'format': 'json', 'pageSize': 15, 'resultType': 'core'})
    try:
        with urllib.request.urlopen(url, timeout=35) as response:
            body = response.read()
            status = response.status
    except Exception as error:
        body = str(error).encode()
        status = 'ERROR'
    name = f'search_{i}.body'
    (out / name).write_bytes(body)
    receipts.append({'url': url, 'status': status, 'body': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()})
    if status == 200:
        data = json.loads(body)
        print(json.dumps({'query': query, 'hitCount': data['hitCount'], 'papers': [{'title': x.get('title'), 'doi': x.get('doi'), 'pmcid': x.get('pmcid'), 'firstPublicationDate': x.get('firstPublicationDate'), 'abstractText': x.get('abstractText')} for x in data['resultList']['result']]}, ensure_ascii=False))
(out / 'SOURCE_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
