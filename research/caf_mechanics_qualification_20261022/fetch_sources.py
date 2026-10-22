"""Retain primary/index responses, leaving semantic qualification explicit."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
from urllib.parse import urlencode
import requests
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/caf_mechanics_qualification/sources'

def fetch(item):
    name,url=item;receipt=dict(url=url,method='GET',utc_started=datetime.now(timezone.utc).isoformat())
    assert not (P/(name+'.http.json')).exists() and not (P/(name+'.body')).exists()
    try:
        r=requests.get(url,timeout=45);raw=r.content
        with (P/(name+'.body')).open('xb') as f:f.write(raw)
        receipt.update(status=r.status_code,final_url=r.url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=r.headers.get('Content-Type'),outcome='RETAINED_CONTENT_UNQUALIFIED')
    except Exception as e:receipt.update(outcome='FAILED_RETAINED',error_type=type(e).__name__)
    receipt['utc_finished']=datetime.now(timezone.utc).isoformat()
    with (P/(name+'.http.json')).open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    return dict(name=name,**receipt)

def parallel(sources):
    P.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(fetch,sources.items()):print(json.dumps(result),flush=True)

if __name__=='__main__':
    parallel({
      'datacite_emon':'https://api.datacite.org/dois?'+urlencode({'query':'Emon','page[size]':100}),
      'crossref_mechanics_doi':'https://api.crossref.org/works/10.64898/2026.09.19.752881',
      'openalex_mechanics_doi':'https://api.openalex.org/works/https://doi.org/10.64898/2026.09.19.752881',
      'illinois_saif_official':'https://mechse.illinois.edu/people/profile/saif',
      'illinois_saif_publications':'https://experts.illinois.edu/en/persons/muhammad-tahir-a-saif/publications/'})
