"""Retrieve two primary articles; expose only methods and metadata in console."""
from pathlib import Path
import hashlib
import json
import requests
import time
import xml.etree.ElementTree as ET

OUT=Path('log/20261023/action_rule_search/constructive')
receipts=[]
for pmc in ('PMC13434641','PMC13663777'):
    url=f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML'
    start=time.perf_counter()
    r=requests.get(url,timeout=45)
    (OUT/f'{pmc}.xml').write_bytes(r.content)
    receipts.append({'url':url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'seconds':time.perf_counter()-start})
    print(pmc,r.status_code)
    if not r.ok: continue
    root=ET.fromstring(r.content)
    print('TITLE',' '.join(root.find('.//article-title').itertext()))
    parts=[]
    for sec in root.findall('.//body/sec'):
        title=sec.find('title')
        heading=' '.join(title.itertext()) if title is not None else ''
        if any(w in heading.lower() for w in ('method','availability')):
            parts.append(' '.join(sec.itertext()))
    text='\n\n'.join(parts)
    (OUT/f'{pmc}_methods.txt').write_text(text,encoding='utf-8')
    print(text[:26000])
(OUT/'METHOD_REQUESTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
