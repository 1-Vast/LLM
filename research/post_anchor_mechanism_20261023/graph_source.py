"""Qualify the author-linked competitor repository without executing it."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
def get(name,url):
    rec=dict(url=url,utc=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(url,timeout=35)
        (OUT/(name+'.body')).write_bytes(r.content)
        rec.update(status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
        payload=r.json() if r.ok else None
    except Exception as error:
        rec.update(error_type=type(error).__name__,error=str(error));payload=None
    (OUT/(name+'.receipt.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
    return payload
repo=get('dgp_repo','https://api.github.com/repos/bieyl/DGP-LA')
if repo:
    branch=repo['default_branch']
    ref=get('dgp_ref','https://api.github.com/repos/bieyl/DGP-LA/commits/'+branch)
    if ref:
        tree=get('dgp_tree','https://api.github.com/repos/bieyl/DGP-LA/git/trees/'+ref['sha']+'?recursive=1')
        print(json.dumps(dict(sha=ref['sha'],default_branch=branch,paths=[r['path'] for r in (tree or {}).get('tree',[])]),indent=2))
