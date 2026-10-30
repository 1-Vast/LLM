import urllib.request,urllib.error,time,json,hashlib,pathlib,sys
root=pathlib.Path(__file__).parent
label,url=sys.argv[1:3]
req=urllib.request.Request(url,headers={'User-Agent':'Research source verification (public text only)'})
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): return None
op=urllib.request.build_opener(NoRedirect)
t=time.time(); status=None; headers={}; error=None; data=b''
try:
 try: response=op.open(req,timeout=25)
 except urllib.error.HTTPError as e: response=e
 status=response.code; headers=dict(response.headers)
 data=response.read(3000001)
 if len(data)>3000000: error='per-request body cap reached'
except Exception as e: error=str(e)
(root/(label+'.body')).write_bytes(data)
record={'url':url,'status':status,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(t)),'elapsed_s':round(time.time()-t,3),'bytes_read':len(data),'sha256':hashlib.sha256(data).hexdigest(),'headers':headers,'error':error,'redirect_policy':'not followed; counted next request if needed','retries':0}
(root/(label+'.receipt.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
