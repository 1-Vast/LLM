import hashlib,json,re,time
from pathlib import Path
from urllib.request import Request,urlopen
out=Path('log/20261023/functional_rule_discovery/frontier')
receipts=[]
for ident in ['2602.12112v1','2609.39751v1']:
    url='https://arxiv.org/html/'+ident;t=time.perf_counter()
    try:
        with urlopen(Request(url,headers={'User-Agent':'MAESTRO primary research'}),timeout=45) as r:
            body=r.read();status=r.status;final=r.url
        (out/(ident+'.html')).write_bytes(body)
        bodytext=re.sub(r'<script\b[^>]*>.*?</script>','',body.decode('utf-8','replace'),flags=re.S)
        bodytext=re.sub(r'<style\b[^>]*>.*?</style>','',bodytext,flags=re.S)
        text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',bodytext))
        (out/(ident+'.txt')).write_text(text,encoding='utf-8')
        receipts.append(dict(id=ident,url=url,final_url=final,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),seconds=time.perf_counter()-t))
    except Exception as e:
        receipts.append(dict(id=ident,url=url,error=repr(e),seconds=time.perf_counter()-t))
(out/'PRIMARY_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
print(json.dumps(receipts,indent=2))
