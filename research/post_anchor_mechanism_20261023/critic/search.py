import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

out = Path('D:/MAESTRO/log/20261023/post_anchor_mechanism/critic')
query = 'submittedDate:[202501010000 TO 202610232359] AND (all:"sparse mechanism shift" OR all:"mechanism adaptation" OR all:"modular adaptation")'
url = 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode({'search_query':query,'max_results':8,'sortBy':'submittedDate','sortOrder':'descending'})
start = datetime.now(timezone.utc).isoformat()
try:
    response = urllib.request.urlopen(url,timeout=45)
except urllib.error.HTTPError as error:
    response = error
blob = response.read()
(out/'search.body').write_bytes(blob)
(out/'search.receipt.json').write_text(json.dumps({'url':url,'start':start,'end':datetime.now(timezone.utc).isoformat(),'status':response.status,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()},indent=2))
print('status',response.status)
if response.status == 200:
    root = ET.fromstring(blob)
    ns = {'a':'http://www.w3.org/2005/Atom'}
    entries = [{'id':x.findtext('a:id',namespaces=ns),'title':' '.join(x.findtext('a:title',namespaces=ns).split()),'summary':' '.join(x.findtext('a:summary',namespaces=ns).split())} for x in root.findall('a:entry',ns)]
    (out/'search.entries.json').write_text(json.dumps(entries,indent=2))
    print(json.dumps(entries,indent=2))
