import hashlib,json,re,time
from pathlib import Path
from urllib.request import Request,urlopen
out=Path('log/20261023/action_rule_search/frontier')
receipts=[]
for ident in ['2609.36107v1','2610.12468v1','2609.30264v1']:
    url='https://arxiv.org/html/'+ident
    start=time.perf_counter()
    try:
        with urlopen(Request(url,headers={'User-Agent':'MAESTRO primary research'}),timeout=45) as r:
            body=r.read(); status=r.status; final=r.url
        (out/(ident+'.html')).write_bytes(body)
        text=re.sub('<[^>]+>',' ',body.decode('utf-8','replace'))
        text=re.sub(r'\s+',' ',text)
        (out/(ident+'.txt')).write_text(text,encoding='utf-8')
        receipts.append(dict(id=ident,url=url,final_url=final,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),elapsed=time.perf_counter()-start))
    except Exception as e:
        receipts.append(dict(id=ident,url=url,error=repr(e),elapsed=time.perf_counter()-start))
(out/'PRIMARY_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
print(json.dumps(receipts,indent=2))
