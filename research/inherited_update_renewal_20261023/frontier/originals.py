import urllib.request, hashlib, json
from pathlib import Path
from html.parser import HTMLParser
root=Path('log/20261023/inherited_update_renewal/frontier')
class Parser(HTMLParser):
 def __init__(self): super().__init__(); self.parts=[]
 def handle_data(self,data):
  if data.strip(): self.parts.append(data.strip())
receipts=[]
for paper in ['2609.12278v2','2610.17370v1','2610.29303v1']:
 url='https://arxiv.org/html/'+paper
 try:
  with urllib.request.urlopen(url,timeout=75) as r: data=r.read(); status=r.status
  (root/(paper+'.html')).write_bytes(data)
  p=Parser(); p.feed(data.decode('utf-8'))
  (root/(paper+'.txt')).write_text('\n'.join(p.parts),encoding='utf-8')
  receipts.append({'url':url,'status':status,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
  print(paper,len(data))
 except Exception as e: receipts.append({'url':url,'error':repr(e)}); print(paper,repr(e))
(root/'ORIGINAL_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
