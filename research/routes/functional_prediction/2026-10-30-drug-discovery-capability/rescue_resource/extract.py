from pathlib import Path
import xml.etree.ElementTree as ET
p=Path(__file__).parent;r=ET.fromstring((p/'request02-egfr-primary.body').read_bytes())
lines=[]
for el in r.iter():
 if el.tag in ('article-title','title','p','caption'):
  s=' '.join(''.join(el.itertext()).split())
  if s:lines.append(el.tag+' '+str(el.attrib)+' '+s)
(p/'egfr-primary-text.txt').write_text('\n'.join(lines),encoding='utf-8')
for i,x in enumerate(lines):
 if any(t in x.lower() for t in ['resistant cell','mtt','data availability','availability of data','selection','combination index','synerg','silencing','proteomexchange','pride','independent','figshare','deposited']):print(i+1,x)
