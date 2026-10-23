import json, time, urllib.request, urllib.parse, hashlib
from pathlib import Path
from urllib.error import HTTPError
import xml.etree.ElementTree as ET
ROOT=Path('log/20261023/inherited_update_renewal/biology')
receipts=[]
for pmc in ['PMC12205652','PMC12635425']:
 url='https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/'+pmc+'/unicode'
 start=time.time()
 try:
  with urllib.request.urlopen(url,timeout=45) as r: body=r.read(); status=r.status
 except HTTPError as e:
  body=e.read(); status=e.code
 (ROOT/(pmc+'.xml')).write_bytes(body)
 receipts.append(dict(url=url,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),seconds=time.time()-start))
 (ROOT/'PRIMARY_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
 if status==200:
  e=ET.fromstring(body)
  texts=[''.join(n.itertext()) for n in e.findall('.//passage/text')]
  (ROOT/(pmc+'.txt')).write_text('\n\n'.join(texts),encoding='utf-8')
  for t in texts:
   if any(x in t.lower() for x in ['data availability','accession','geo','23 organoids','23 pdto','growth rate','two-step','transcriptomic','data supporting','data generated']):
    print(pmc,t[:2500])
