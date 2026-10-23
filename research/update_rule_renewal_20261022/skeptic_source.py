from pathlib import Path
import requests,json,hashlib,datetime
p=Path('log/20261022/update_rule_renewal/skeptic/primary')
u='https://arxiv.org/html/2502.16982v1'
r=requests.get(u,timeout=45)
(p/'muon.body').write_bytes(r.content)
receipt=dict(url=u,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(p/'muon.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
from html.parser import HTMLParser
class T(HTMLParser):
 def __init__(self):super().__init__();self.t=[]
 def handle_data(self,d):self.t.append(d)
t=T();t.feed(r.text);s=' '.join(' '.join(t.t).split());(p/'muon.txt').write_text(s,encoding='utf-8')
print(s[:300]);print(receipt)
for term in ['Abstract','Newton','spectral','Adam','learning rate']:
 j=s.find(term,5000);print(term,s[max(0,j-100):j+1400])
