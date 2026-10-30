import urllib.request,urllib.error,json,sys,time
from pathlib import Path
base=Path(__file__).parent
url,label=sys.argv[1:3]
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): return None
start=time.monotonic();body=b''; status=None;error=None
try:
 req=urllib.request.Request(url,headers={'User-Agent':'MAESTRO-literature-research/1.0 (public source reading)'})
 with urllib.request.build_opener(NoRedirect).open(req,timeout=24) as r:
  status=r.status
  while True:
   chunk=r.read(65536)
   if not chunk: break
   body+=chunk
   if len(body)>8*1024*1024: raise RuntimeError('per-body cap exceeded')
   if time.monotonic()-start>24: raise TimeoutError('deadline')
except Exception as e:
 error=str(e)
 if isinstance(e,urllib.error.HTTPError):
  status=e.code
  print('HTTP_LOCATION',e.headers.get('Location'))
  body=e.read(65536)
(base/(label+'.body')).write_bytes(body)
record={'label':label,'url':url,'status':status,'bytes':len(body),'elapsed_s':round(time.monotonic()-start,3),'error':error,'date':'2026-10-30','redirects_followed':0}
with (base/'requests.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
print(json.dumps(record))
