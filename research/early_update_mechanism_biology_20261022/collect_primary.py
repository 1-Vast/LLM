"""Bounded exact-title primary-literature lookup; no biological numeric tables."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

OUT=Path('D:/MAESTRO/log/20261022/early_update_mechanism/biology')
OUT.mkdir(parents=True,exist_ok=True)
QUERIES={
 'decryptE_epmc':'TITLE:"Decrypting the molecular basis of cellular drug phenotypes by dose-resolved expression proteomics"',
 'state_epmc':'TITLE:"Predicting cellular responses to perturbation across diverse contexts with State"',
 'decryptM_epmc':'TITLE:"Decrypting drug actions and protein modifications by dose- and time-resolved proteomics"'}

def fetch(item):
    name,query=item
    target=OUT/(name+'.body')
    assert not target.exists()
    url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urlencode(dict(query=query,format='json',resultType='core',pageSize=5))
    record=dict(url=url,started_utc=datetime.now(timezone.utc).isoformat(),retries=0,scope='publication text/metadata only')
    try:
        with urlopen(Request(url,headers={'User-Agent':'Primary-source mechanism review/1.0'}),timeout=40) as response:
            body=response.read(4*1024*1024+1)
            assert len(body)<=4*1024*1024
            record.update(status=response.status,final_url=response.geturl())
        target.write_bytes(body)
        record.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    except Exception as error:
        record.update(error_type=type(error).__name__,error=str(error))
    record['ended_utc']=datetime.now(timezone.utc).isoformat()
    (OUT/(name+'.receipt.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(fetch,QUERIES.items())),indent=2))
