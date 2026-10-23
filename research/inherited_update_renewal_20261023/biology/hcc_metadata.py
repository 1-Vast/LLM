import urllib.request,json,hashlib,re,time
from pathlib import Path
from urllib.error import HTTPError
ROOT=Path('log/20261023/inherited_update_renewal/biology')
urls=[('hcc_page.html','https://pmc.ncbi.nlm.nih.gov/articles/PMC12205652/'),('hcc_jats.xml','https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12205652')]
receipts=[]
for name,url in urls:
 start=time.time()
 try:
  with urllib.request.urlopen(url,timeout=45) as r: body=r.read();status=r.status
 except HTTPError as e: body=e.read();status=e.code
 (ROOT/name).write_bytes(body)
 receipts.append(dict(url=url,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),seconds=time.time()-start))
 (ROOT/'HCC_META_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf8')
 if status==200 and name.endswith('html'):
  html=body.decode('utf8',errors='replace')
  for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html,re.S):
   if any(x in m.group(1).lower() for x in ['mmc','supp','xlsx','docx','zip','csv']):
    print(m.group(1),re.sub('<[^>]+>','',m.group(2))[:300])
 if name.endswith('xml'): print(body.decode()[:1500])
