import datetime, hashlib, json, pathlib
from concurrent.futures import ThreadPoolExecutor
import requests
from html.parser import HTMLParser
class Extract(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,data): self.parts.append(data)
ROOT=pathlib.Path('log/20261023/function_update_renewal/skeptic')
def fetch(ident):
    url='https://arxiv.org/html/'+ident
    try:
        r=requests.get(url,timeout=60)
        (ROOT/(ident+'.html')).write_bytes(r.content)
        if r.status_code==200:
            parser=Extract(); parser.feed(r.text)
            (ROOT/(ident+'.txt')).write_text(' '.join(parser.parts),encoding='utf-8')
        return dict(id=ident,url=url,final_url=r.url,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except Exception as e: return dict(id=ident,url=url,error=repr(e))
with ThreadPoolExecutor(max_workers=4) as pool:
    receipts=list(pool.map(fetch,['2610.22364v1','2610.17370v1','2610.22122v2','2610.28945v1']))
(ROOT/'FULLTEXT_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
print(json.dumps(receipts,indent=2))
