import json, time, urllib.request, urllib.parse, hashlib
from pathlib import Path
ROOT = Path('log/20261023/inherited_update_renewal/biology')
queries = [
 '(organoid AND drug AND (single-cell OR transcriptomic) AND (viability OR growth)) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
 '("optical pooled" AND (drug OR therapeutic)) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
 '("drug response" AND ("cell state" OR "single-cell") AND ("functional" OR "viability") AND "patient") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
]
receipts=[]
for i,q in enumerate(queries):
 url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode(dict(query=q,format='json',pageSize=30,resultType='core',sort='RELEVANCE'))
 start=time.time()
 try:
  with urllib.request.urlopen(url,timeout=45) as response:
   body=response.read(); status=response.status
  (ROOT/f'search_{i}.json').write_bytes(body)
  payload=json.loads(body)
  print(i,payload.get('hitCount'))
  for r in payload.get('resultList',{}).get('result',[]):
   print(r.get('id'),r.get('pmcid'),r.get('doi'),r.get('title'))
  receipts.append(dict(url=url,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),seconds=time.time()-start))
 except Exception as e:
  receipts.append(dict(url=url,error=repr(e),seconds=time.time()-start))
 (ROOT/'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
