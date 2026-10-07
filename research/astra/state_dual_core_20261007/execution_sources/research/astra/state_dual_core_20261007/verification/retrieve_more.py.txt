from pathlib import Path
import requests,time,json,hashlib
from html.parser import HTMLParser
class Plain(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,d):self.parts.append(d)
O=Path(r'D:/MAESTRO/research/astra/state_dual_core_20261007/verification/sources');rs=[]
for k,u in [('state_manuscript','https://arcinstitute.org/manuscripts/State'),('state_preprint','https://www.biorxiv.org/content/10.1101/2025.06.26.661135v2.full'),('systema_fulltext','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13271886/fullTextXML')]:
 t=time.perf_counter()
 try:
  r=requests.get(u,timeout=30);(O/(k+'.txt')).write_bytes(r.content);rs.append(dict(id=k,url=u,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),seconds=time.perf_counter()-t,path=k+'.txt'))
 except Exception as e:rs.append(dict(id=k,url=u,status='FAILED',error=type(e).__name__,bytes=0,seconds=time.perf_counter()-t))
(O/'retrieval_receipts_round2.json').write_text(json.dumps(rs,indent=2)+'\n');print(json.dumps(rs,indent=2))
for name in ['state_release','state_manuscript','directional_design','decision_rank']:
 p=O/(name+'.txt')
 if p.exists():
  soup=Plain();soup.feed(p.read_text(encoding='utf8'));text=' '.join(soup.parts);(O/(name+'_plain.txt')).write_text(text,encoding='utf8')
  print('\nSOURCE',name, text[:7000])
