"""Bounded public Figshare metadata search for the newly named source."""
from datetime import datetime, timezone
import hashlib
import json
import requests
from metadata import OUT

if __name__=='__main__':
    path=OUT/'figshare_search.body'
    assert not path.exists()
    query={'search_for':'Dissecting context-dependent cancer vulnerabilities','limit':10}
    start=datetime.now(timezone.utc).isoformat()
    r=requests.post('https://api.figshare.com/v2/articles/search',json=query,timeout=(15,35))
    path.write_bytes(r.content)
    receipt=dict(url=r.url, method='POST',purpose='read-only public catalog query',request=query,
        start=start,end=datetime.now(timezone.utc).isoformat(),status=r.status_code,
        bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
    (OUT/'figshare_search.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    if r.status_code==200:
        data=r.json()
        result=[{k:x.get(k) for k in ['id','title','url','doi','url_public_html']} for x in data]
        (OUT/'FIGSHARE_SEARCH_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    else:
        print(r.status_code)
