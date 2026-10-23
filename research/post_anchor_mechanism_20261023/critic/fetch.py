import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import urllib.request
import urllib.error

out = Path('D:/MAESTRO/log/20261023/post_anchor_mechanism/critic')
label, url = sys.argv[1:]
start = datetime.now(timezone.utc).isoformat()
try:
    response = urllib.request.urlopen(url, timeout=45)
except urllib.error.HTTPError as error:
    response = error
blob = response.read()
(out/(label+'.body')).write_bytes(blob)
(out/(label+'.receipt.json')).write_text(json.dumps({'url':url,'start':start,'end':datetime.now(timezone.utc).isoformat(),'status':response.status,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()},indent=2))
print(label,response.status,len(blob))
