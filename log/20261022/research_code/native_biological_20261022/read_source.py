from pathlib import Path
import requests,json,hashlib,datetime,xml.etree.ElementTree as E
out=Path('D:/MAESTRO/log/20261022/native_operation/biology')
u='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8376399/fullTextXML'
r=requests.get(u,timeout=40);(out/'frangieh2021.xml').write_bytes(r.content)
(out/'fulltext_receipt.json').write_text(json.dumps({'url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
root=E.fromstring(r.content)
lines=[' '.join(x.itertext()) for x in root.findall('.//p')]
(out/'frangieh2021_paragraphs.txt').write_text('\n\n'.join(f'{i}: {x}' for i,x in enumerate(lines)),encoding='utf8')
for i,x in enumerate(lines):
 if any(s.lower() in x.lower() for s in ['data availability','GSE','48 h','CD58','co-culture condition','interferon','cytotoxicity','github']):
  print(f'{i}: {x}')
