"""Retain bounded primary bodies and plain-text projections."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests
from html.parser import HTMLParser

class TextProjection(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_data(self,data):
        if data.strip():self.parts.append(data.strip())

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
SOURCES=[('webevolver','https://aclanthology.org/2025.emnlp-main.454/'),
         ('found','https://www.biorxiv.org/content/10.64898/2026.04.10.717768v1.full'),
         ('graph_adaptation','https://doi.org/10.1093/bioinformatics/btag747')]
def get(item):
    name,url=item
    rec=dict(name=name,url=url,utc=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(url,timeout=40)
        (OUT/(name+'.body')).write_bytes(r.content)
        rec.update(status=r.status_code,final_url=r.url,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
        if r.ok:
            projection=TextProjection()
            projection.feed(r.text)
            (OUT/(name+'.txt')).write_text('\n'.join(projection.parts),encoding='utf-8')
    except Exception as error:rec.update(error_type=type(error).__name__,error=str(error))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
    return rec
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(get,SOURCES))
    print(json.dumps(results,indent=2))
