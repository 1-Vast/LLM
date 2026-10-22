from pathlib import Path
import requests,json,hashlib,datetime,concurrent.futures
out=Path('D:/MAESTRO/log/20261022/native_operation/biology')
urls={'nature':'https://www.nature.com/articles/s41588-021-00779-1','bioc':'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC8376399/unicode'}
def get(pair):
 name,u=pair
 try:
  r=requests.get(u,timeout=35);p=out/(name+'.txt');p.write_bytes(r.content)
  receipt={'url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except requests.RequestException as e: receipt={'url':u,'error':str(e)}
 (out/(name+'_receipt.json')).write_text(json.dumps(receipt,indent=2));return name,receipt
for x in concurrent.futures.ThreadPoolExecutor(2).map(get,urls.items()):print(x)
