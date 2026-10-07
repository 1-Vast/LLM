from pathlib import Path
from html.parser import HTMLParser
import re,xml.etree.ElementTree as ET
O=Path(r'D:/MAESTRO/research/astra/state_dual_core_20261007/verification/sources')
class P(HTMLParser):
 def __init__(self):super().__init__();self.inp=False;self.parts=[];self.rows=[]
 def handle_starttag(self,t,a):
  if t=='p':self.inp=True;self.parts=[]
 def handle_endtag(self,t):
  if t=='p' and self.inp:self.rows.append(' '.join(self.parts));self.inp=False
 def handle_data(self,d):
  if self.inp:self.parts.append(d)
for name,terms in [('state_preprint','Tahoe|zero-shot|generalization|batch|dose|HVG|highly variable|control|encoding|fingerprint|held-out'),('systema_fulltext','systematic|baseline|perturbation-specific|evaluation')]:
 p=O/(name+'.txt');h=P();h.feed(p.read_text(encoding='utf8'));rows=[x for x in h.rows if re.search(terms,x,re.I)];(O/(name+'_selected.txt')).write_text('\n\n'.join(rows),encoding='utf8');print(name,len(rows));print('\n\n'.join(rows)[:28000])
