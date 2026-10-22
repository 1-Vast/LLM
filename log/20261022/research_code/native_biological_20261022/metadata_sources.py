from pathlib import Path
import requests,json,hashlib,datetime,concurrent.futures
out=Path('D:/MAESTRO/log/20261022/native_operation/biology')
urls={'repo':'https://api.github.com/repos/klarman-cell-observatory/Perturb-CITE-Seq/contents','supplement_head':'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-021-00779-1/MediaObjects/41588_2021_779_MOESM3_ESM.xlsx','scp':'https://singlecell.broadinstitute.org/single_cell/study/SCP1064/multi-modal-pooled-perturb-cite-seq-screens-in-patient-models-define-novel-mechanisms-of-cancer-immune-evasion'}
def get(pair):
 name,u=pair
 try:
  r=requests.head(u,timeout=30) if name.endswith('head') else requests.get(u,timeout=30)
  (out/(name+'.txt')).write_bytes(r.content)
  receipt={'url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'headers':dict(r.headers),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except requests.RequestException as e:receipt={'url':u,'error':str(e)}
 (out/(name+'_receipt.json')).write_text(json.dumps(receipt,indent=2));return name,receipt.get('status'),receipt.get('bytes'),receipt.get('headers',{}).get('Content-Length')
for x in concurrent.futures.ThreadPoolExecutor(3).map(get,urls.items()):print(x)
