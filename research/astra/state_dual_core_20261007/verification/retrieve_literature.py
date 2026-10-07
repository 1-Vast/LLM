import requests,time,json,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
O=Path(r'D:/MAESTRO/research/astra/state_dual_core_20261007/verification/sources')
urls={
 'state_readme':'https://raw.githubusercontent.com/ArcInstitute/state/main/README.md',
 'state_cell_metadata':'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1016/j.cell.2026.07.052&format=json',
 'decision_rank':'https://proceedings.mlr.press/v162/mandi22a.html',
 'shift_uncertainty':'https://proceedings.neurips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html',
 'state_release':'https://arcinstitute.org/news/virtual-cell-model-state',
 'directional_design':'https://arxiv.org/html/2602.05340v1',
 'systema_metadata':'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41587-025-02777-8&format=json'}
def get(kv):
 k,u=kv;t=time.perf_counter()
 try:
  r=requests.get(u,timeout=35);p=O/(k+'.txt');p.write_bytes(r.content)
  return dict(id=k,url=u,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),seconds=time.perf_counter()-t,path=p.name,content_type=r.headers.get('content-type'),reading_depth='retrieved; not yet read')
 except Exception as e:return dict(id=k,url=u,status='FAILED',error=type(e).__name__,seconds=time.perf_counter()-t,bytes=0)
with ThreadPoolExecutor(max_workers=3) as pool: receipts=list(pool.map(get,urls.items()))
(O/'retrieval_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n');print(json.dumps(receipts,indent=2))
