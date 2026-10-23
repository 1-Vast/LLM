import requests, json, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode

out=Path('log/20261022/post_decrypte_renewal/assay/source')
out.mkdir(parents=True,exist_ok=True)
name, query=sys.argv[1:3]
url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urlencode({'query':query,'format':'json','pageSize':12,'resultType':'core'})
r={'url':url,'utc':datetime.now(timezone.utc).isoformat()}
try:
    response=requests.get(url,timeout=40)
    body=response.content
    (out/(name+'.body')).write_bytes(body)
    r.update(status=response.status_code,bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    data=response.json()
    summaries=[{k:p.get(k) for k in ['id','source','pmcid','doi','title','firstPublicationDate','abstractText','authorString']} for p in data.get('resultList',{}).get('result',[])]
    (out/(name+'.summary.json')).write_text(json.dumps(summaries,indent=2),encoding='utf-8')
    print(json.dumps(summaries,indent=2))
except Exception as e:
    r['failure']=repr(e)
(out/(name+'.receipt.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
