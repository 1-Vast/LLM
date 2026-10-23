"""At most three new paper-only requests; no data/weights."""
import hashlib
import json
from pathlib import Path
import time
import requests
import sys

base = Path('log/20261022/update_rule_renewal/frontier/sources')
def get(name, url, params=None):
    assert len(list(base.glob('*.receipt.json'))) < 3, 'Source request cap'
    record = {'name':name,'url':url,'params':params,'started':time.time()}
    try:
        r=requests.get(url,params=params,timeout=50)
        (base/(name+'.body')).write_bytes(r.content)
        record.update(status=r.status_code,final_url=r.url,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
    except Exception as exc:
        record['error']=repr(exc)
    record['elapsed']=time.time()-record['started']
    (base/(name+'.receipt.json')).write_text(json.dumps(record,indent=2),encoding='utf8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':
    get('ttt_query','https://export.arxiv.org/api/query',{'search_query':'(all:"test-time training" AND (all:"noise" OR all:"memory" OR all:"optimizer")) AND submittedDate:[202501010000 TO 202610222359]','max_results':12,'sortBy':'submittedDate','sortOrder':'descending'})
