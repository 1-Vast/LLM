"""Read exact author files needed for sample/clone joins, not expression data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
SHA='3d5ef9070a259fb902feccbc5948f10e6a9d44ae'
ITEMS=[('aml_readme','README.md'),('aml_lineage','R_scripts/single_cell_lineage_analysis.R'),
       ('aml_gex','R_scripts/single_cell_GEX_initial_processing.R')]
def get(item):
    name,path=item
    url='https://raw.githubusercontent.com/mckennalab/AML_lineage_tracing/'+SHA+'/'+path
    rec=dict(url=url,utc=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(url,timeout=35)
        (OUT/(name+'.body')).write_bytes(r.content)
        rec.update(status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
    except Exception as error:rec.update(error_type=type(error).__name__,error=str(error))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
    return rec
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:print(json.dumps(list(pool.map(get,ITEMS)),indent=2))
