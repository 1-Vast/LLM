"""Header-only stream and source-code acquisition; no numeric rows emitted."""
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'log/20261023/feedback_shift_mechanism/source'
TASKS={
    'myo_harmony_header':('https://zenodo.org/api/records/10623852/files/Harmony-Myoblasts.csv/content','header'),
    'myo_cp_header':('https://zenodo.org/api/records/10623852/files/CellProfiler-Myoblasts.csv/content','header'),
    'myo_readme':('https://raw.githubusercontent.com/romlambert/CytotoxPred/main/README.md','text'),
    'myo_ctg_code':('https://raw.githubusercontent.com/romlambert/CytotoxPred/main/CTG/CTGtoCSVwMetadata.ipynb','notebook'),
    'myo_auto_code':('https://raw.githubusercontent.com/romlambert/CytotoxPred/main/AUTO%20-%20Viability%20and%20cell%20count%20prediction.py','text'),
    'eu_readme':('https://raw.githubusercontent.com/schmiedc/EU-OS_bioactives/main/README.md','text'),
}


def get(item):
    name,(url,kind)=item;receipt=dict(url=url,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=kind)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MAESTRO-source-audit'}),timeout=45) as response:
            receipt['status']=response.status
            raw=response.readline(262144) if kind=='header' else response.read()
        (OUT/(name+'.body')).write_bytes(raw)
        receipt.update(bytes_retained=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if kind=='notebook':
            obj=json.loads(raw);code='\n'.join(''.join(c.get('source',[])) for c in obj['cells'] if c.get('cell_type')=='code')
            (OUT/(name+'.source.txt')).write_text(code,encoding='utf-8');print(name,code)
        elif kind=='header':
            fields=raw.decode('utf-8-sig').strip().split(',')
            print(name,'field_count',len(fields),'selected',[f for f in fields if any(k in f.lower() for k in ('meta','count','viab','lum','plate','well','cond','drug','conc','batch','date','ctg'))])
        else:print(name,raw.decode('utf-8-sig')[:16000])
    except Exception as e:
        receipt['error']=repr(e);print(name,json.dumps(receipt))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(get,TASKS.items()))
