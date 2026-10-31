import requests,json,hashlib,datetime
from pathlib import Path
p=Path('research/routes/functional_prediction/2026-10-31-crossfield-state-learning'); (p/'root_sources').mkdir(exist_ok=True)
targets=[('dreamer_crossref','https://api.crossref.org/works/10.1038/s41586-025-08744-2'),('dreamer_original','https://www.nature.com/articles/s41586-025-08744-2'),('spo_crossref','https://api.crossref.org/works?query.title=Smart%20Predict%20then%20Optimize&rows=3')]
for name,url in targets:
 rec={'name':name,'url':url,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  r=requests.get(url,timeout=35); b=r.content; (p/'root_sources'/f'{name}.body').write_bytes(b); rec.update(status=r.status_code,final_url=r.url,content_type=r.headers.get('Content-Type'),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  if 'crossref' in name and r.ok:
   j=r.json()['message']; items=j.get('items',[j]); print(name,[(a.get('title'),a.get('DOI'),a.get('published')) for a in items])
  else: print(name,rec['status'],len(b))
 except Exception as e: rec['error']=str(e); print(name,str(e))
 with (p/'root_receipts.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(rec)+'\n')
