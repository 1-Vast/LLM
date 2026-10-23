import urllib.request, urllib.parse, hashlib, json, datetime
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path('log/20261023/inherited_update_renewal/frontier')
queries={
 'optimizer':'(all:"learned optimizer" OR all:"algorithm discovery" OR all:"learning to optimize") AND submittedDate:[202501010000 TO 202610232359]',
 'meta':'(all:"DiscoRL" OR all:"AlphaEvolve" OR all:"meta-update" OR all:"simulator adaptation") AND submittedDate:[202501010000 TO 202610232359]'}
receipts=[]
for key,q in queries.items():
 url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':q,'start':0,'max_results':35,'sortBy':'submittedDate','sortOrder':'descending'})
 try:
  with urllib.request.urlopen(url,timeout=70) as r: data=r.read(); status=r.status
  (root/(key+'.xml')).write_bytes(data)
  receipts.append({'url':url,'status':status,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
  ns={'a':'http://www.w3.org/2005/Atom'}
  entries=[{'id':e.findtext('a:id',namespaces=ns),'title':e.findtext('a:title',namespaces=ns),'summary':e.findtext('a:summary',namespaces=ns)} for e in ET.fromstring(data).findall('a:entry',ns)]
  (root/(key+'_entries.json')).write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps(entries,ensure_ascii=False))
 except Exception as e: receipts.append({'url':url,'error':repr(e)}); print(repr(e))
(root/'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
