"""Official bounded source retrieval only; never open response arrays."""
import sys,json,hashlib
from pathlib import Path
from urllib.request import Request,urlopen
from datetime import datetime,timezone
name,url=sys.argv[1:]
out=Path('log/20261023/mechanism_reentry/source');out.mkdir(parents=True,exist_ok=True)
r={'url':url,'utc':datetime.now(timezone.utc).isoformat()}
try:
    with urlopen(Request(url,headers={'User-Agent':'MAESTRO-task-qualification/1'}),timeout=45) as response:
        body=response.read();r.update(status=response.status,final_url=response.url,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),headers=dict(response.headers))
    (out/(name+'.body')).write_bytes(body)
except Exception as e:r['error']=repr(e)
(out/(name+'.receipt.json')).write_text(json.dumps(r,indent=2),encoding='utf8')
print({k:v for k,v in r.items() if k!='headers'})
