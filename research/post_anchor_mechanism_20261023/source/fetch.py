"""Bounded official primary-index retrieval, no response dataset values."""
from pathlib import Path
import hashlib,json,sys
from urllib.request import Request,urlopen
from datetime import datetime,timezone
out=Path('log/20261023/post_anchor_mechanism/source');out.mkdir(parents=True,exist_ok=True)
name,url=sys.argv[1:]
receipt={'url':url,'utc':datetime.now(timezone.utc).isoformat()}
try:
    with urlopen(Request(url,headers={'User-Agent':'MAESTRO-source-qualification/1'}),timeout=45) as r:
        body=r.read();receipt.update(status=r.status,final_url=r.url,headers=dict(r.headers),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    (out/(name+'.body')).write_bytes(body)
except Exception as e:receipt['error']=repr(e)
(out/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='headers'},indent=2))
