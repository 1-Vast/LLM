"""Acquire pinned author-code text and lineage metadata only; never execute it."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
SHA='2e87ceee1e73eb81d2c9b4481af454e26faea014'
ITEMS=[('dgp_model','https://raw.githubusercontent.com/bieyl/DGP-LA/'+SHA+'/src/dgpla/model.py'),
       ('dgp_prior','https://raw.githubusercontent.com/bieyl/DGP-LA/'+SHA+'/src/dgpla/prior.py'),
       ('dgp_repro','https://raw.githubusercontent.com/bieyl/DGP-LA/'+SHA+'/docs/REPRODUCIBILITY.md'),
       ('aml_commit','https://api.github.com/repos/mckennalab/AML_lineage_tracing/commits/main')]
def get(item):
    name,url=item
    rec=dict(url=url,utc=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(url,timeout=35)
        (OUT/(name+'.body')).write_bytes(r.content)
        rec.update(status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
    except Exception as error:rec.update(error_type=type(error).__name__,error=str(error))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
    return rec
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:print(json.dumps(list(pool.map(get,ITEMS)),indent=2))
    path=OUT/'aml_commit.body'
    if json.loads((OUT/'aml_commit.receipt.json').read_text()).get('status')==200:
        sha=json.loads(path.read_text())['sha']
        rec=get(('aml_tree','https://api.github.com/repos/mckennalab/AML_lineage_tracing/git/trees/'+sha+'?recursive=1'))
        print(json.dumps(rec))
        if rec.get('status')==200:
            tree=json.loads((OUT/'aml_tree.body').read_text())
            print(json.dumps(dict(commit=sha,tree_sha=tree['sha'],truncated=tree.get('truncated'),
                paths=[dict(path=p['path'],size=p.get('size')) for p in tree['tree']]),indent=2))
