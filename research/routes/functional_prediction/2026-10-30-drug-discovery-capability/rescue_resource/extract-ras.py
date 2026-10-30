from pathlib import Path
import xml.etree.ElementTree as ET
p=Path(__file__).parent;r=ET.fromstring((p/'request03-ras-primary.body').read_bytes())
lines=[]
for el in r.iter():
 if el.tag in ('article-title','title','p','caption'):
  s=' '.join(''.join(el.itertext()).split())
  if s:lines.append(el.tag+' '+str(el.attrib)+' '+s)
(p/'ras-primary-text.txt').write_text('\n'.join(lines),encoding='utf-8')
for i,x in enumerate(lines):
 if x.startswith('title') or any(t in x.lower() for t in ['data availability','zenodo','figshare','deposited','engineered','lentivir','overexpress','resistant cell lines','cell viability','celltiter','independent clone','independent cultures']):print(i+1,x)
