"""Bounded primary-source metadata search; no biological response payloads."""
from pathlib import Path
import hashlib
import json
import time
import requests

OUT = Path('log/20261023/action_rule_search/constructive')
OUT.mkdir(parents=True, exist_ok=True)
queries = {
    'activity': '(TITLE_ABS:"target engagement" AND TITLE_ABS:"prediction") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
    'phospho': '(TITLE_ABS:"kinase" AND TITLE_ABS:"phosphoproteomics" AND TITLE_ABS:"drug") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
    'action': '(TITLE_ABS:"mechanistic" AND TITLE_ABS:"perturbation" AND TITLE_ABS:"model") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
}
receipts = []
for key, query in queries.items():
    started = time.perf_counter()
    response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params={'query':query, 'format':'json', 'pageSize':12, 'resultType':'lite'}, timeout=45)
    body = response.content
    (OUT / f'{key}_metadata.json').write_bytes(body)
    receipts.append({'key':key,'url':response.url,'status':response.status_code,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'seconds':time.perf_counter()-started})
    print(key, response.status_code)
    if response.ok:
        data=response.json()
        print('hitCount', data.get('hitCount'))
        for item in data.get('resultList',{}).get('result',[]):
            print(json.dumps({k:item.get(k) for k in ('id','title','doi','pmcid','pubYear','authorString')},ensure_ascii=False))
(OUT / 'SOURCE_REQUESTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
