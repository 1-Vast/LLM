import json, time, urllib.request, urllib.parse, hashlib
from pathlib import Path
from urllib.error import HTTPError
ROOT=Path('log/20261023/inherited_update_renewal/biology')
base='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
q='(organoid AND drug AND (single-cell OR transcriptomic) AND (viability OR growth)) AND 2025:2026[dp]'
receipts=[]
def get(url,name):
 start=time.time()
 try:
  with urllib.request.urlopen(url,timeout=45) as r: body=r.read(); status=r.status
 except HTTPError as e:
  body=e.read(); status=e.code
 (ROOT/name).write_bytes(body)
 receipts.append(dict(url=url,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),seconds=time.time()-start))
 (ROOT/'PUBMED_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
 return body,status
b,s=get(base+'esearch.fcgi?'+urllib.parse.urlencode(dict(db='pubmed',term=q,retmode='json',retmax=35,sort='relevance')),'pubmed_search.json')
if s==200:
 ids=json.loads(b)['esearchresult']['idlist']
 print(ids)
 if ids:
  b,s=get(base+'efetch.fcgi?'+urllib.parse.urlencode(dict(db='pubmed',id=','.join(ids),retmode='xml')),'pubmed_records.xml')
  if s==200:
   import xml.etree.ElementTree as ET
   for a in ET.fromstring(b).findall('.//PubmedArticle'):
    print(a.findtext('.//PMID'), ''.join(a.find('.//ArticleTitle').itertext()))
