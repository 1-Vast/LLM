"""Metadata-only acquisition for two selected primary assets."""
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'log/20261023/feedback_shift_mechanism/source'
URLS={
    'eu_zenodo':'https://zenodo.org/api/records/14776021',
    'myo_zenodo':'https://zenodo.org/api/records/10623852',
    'eu_tree':'https://api.github.com/repos/schmiedc/EU-OS_bioactives/git/trees/main?recursive=1',
    'myo_tree':'https://api.github.com/repos/romlambert/CytotoxPred/git/trees/main?recursive=1',
}


def get(item):
    name,url=item;receipt=dict(url=url,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MAESTRO-source-audit'}),timeout=45) as response:
            raw=response.read();receipt['status']=response.status
        (OUT/(name+'.body')).write_bytes(raw)
        receipt.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        obj=json.loads(raw)
        if 'files' in obj:print(name,json.dumps([{'key':f['key'],'size':f['size'],'links':f.get('links')} for f in obj['files']]))
        if 'tree' in obj:print(name,obj['sha'],json.dumps([{'path':f['path'],'size':f.get('size')} for f in obj['tree'] if f['type']=='blob']))
    except Exception as e:
        receipt['error']=repr(e);print(name,json.dumps(receipt))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(get,URLS.items()))
