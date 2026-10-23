import datetime
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

out = Path('log/20261023/rank_reversal_mechanism/critic')
out.mkdir(parents=True,exist_ok=True)
name,url = sys.argv[1:]
try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MAESTRO primary research'}),timeout=40) as response:
        body,status = response.read(),response.status
except urllib.error.HTTPError as error:
    body,status = error.read(),error.code
except Exception as error:
    (out/(name+'.receipt.json')).write_text(json.dumps({'url':url,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':repr(error)},indent=2),encoding='utf-8')
    raise SystemExit(0)
(out/(name+'.body')).write_bytes(body)
r = {'url':url,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
(out/(name+'.receipt.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps(r))
