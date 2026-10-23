import sys,requests,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
out=Path('log/20261022/post_decrypte_renewal/assay/source');out.mkdir(parents=True,exist_ok=True)
name,url=sys.argv[1:3];receipt={'url':url,'utc':datetime.now(timezone.utc).isoformat()}
try:
 r=requests.get(url,timeout=40);b=r.content;(out/(name+'.body')).write_bytes(b);receipt.update(status=r.status_code,bytes=len(b),sha256=hashlib.sha256(b).hexdigest());print(json.dumps(receipt))
except Exception as e:receipt['failure']=repr(e);print(receipt)
(out/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
