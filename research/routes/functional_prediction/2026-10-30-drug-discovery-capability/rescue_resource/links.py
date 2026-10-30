import xml.etree.ElementTree as E
from pathlib import Path
p=Path(__file__).parent
for fn in ['request02-egfr-primary.body','request03-ras-primary.body']:
 r=E.fromstring((p/fn).read_bytes());print(fn)
 for e in r.iter():
  if e.tag in ('supplementary-material','media','ext-link'):
   h=e.attrib.get('{http://www.w3.org/1999/xlink}href','')
   if h and (e.tag!='ext-link' or any(s in h.lower() for s in ['zenodo','figshare','ncbi','source'])):print(e.tag,e.attrib,' '.join(''.join(e.itertext()).split())[:260])
 print('identity',[(e.tag,e.attrib,e.text) for e in r.iter() if e.tag in ('article-id','pub-date','license')][:12])
