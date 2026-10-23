"""Check changed version/data-link evidence, without retrying failed fulltext routes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/functional_source_bridge/root'


def fetch(name, url, params=None):
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/(name+'.body')
    assert not path.exists()
    start=datetime.now(timezone.utc).isoformat()
    r=requests.get(url,params=params,timeout=(15,35))
    path.write_bytes(r.content)
    receipt=dict(url=r.url, status=r.status_code, start=start,
        end=datetime.now(timezone.utc).isoformat(), bytes=len(r.content),
        sha256=hashlib.sha256(r.content).hexdigest(),content_type=r.headers.get('Content-Type'))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return name,r


if __name__ == '__main__':
    jobs=[('biorxiv_version','https://api.biorxiv.org/details/biorxiv/10.64898/2026.08.24.746802',None),
          ('crossref','https://api.crossref.org/works/10.64898/2026.08.24.746802',None),
          ('github_repositories','https://api.github.com/search/repositories',{'q':'"context-dependent" "Perturb-seq"'})]
    results=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for name,r in pool.map(lambda args:fetch(*args),jobs):
            row=dict(name=name,status=r.status_code,bytes=len(r.content))
            if r.status_code==200:
                d=r.json()
                if name=='biorxiv_version':
                    row['records']=[{k:x.get(k) for k in ['title','version','date','published','jatsxml']} for x in d.get('collection',[])]
                elif name=='crossref':
                    row['links']={k:d['message'].get(k) for k in ['link','relation','resource','URL']}
                else:
                    row['total_count']=d.get('total_count')
                    row['items']=[{k:x.get(k) for k in ['full_name','html_url','description','homepage']} for x in d.get('items',[])[:10]]
            results.append(row)
    (OUT/'METADATA_RESULT.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))
