"""Primary-source metadata searches; all HTTP evidence retained."""
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'log/20261023/feedback_shift_mechanism/source'
QUERIES = {
    'search1':'FIRST_PDATE:[2025-01-01 TO 2026-12-31] AND ("drug screening" OR "drug response") AND ("batch" OR "plate controls") AND OPEN_ACCESS:Y',
    'search2':'FIRST_PDATE:[2025-01-01 TO 2026-12-31] AND ("reference compounds" OR "reference drugs") AND ("viability" OR "organoid") AND OPEN_ACCESS:Y',
}


def request(item):
    name,query=item
    url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode(dict(query=query,format='json',pageSize=30,resultType='core'))
    receipt=dict(url=url,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        with urllib.request.urlopen(url,timeout=45) as response:
            raw=response.read();receipt['status']=response.status
        (OUT/(name+'.body')).write_bytes(raw)
        receipt.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        parsed=json.loads(raw)
        print(json.dumps(dict(name=name,hits=parsed.get('hitCount'),results=[{k:r.get(k) for k in ('title','doi','pmcid','authorString','firstPublicationDate')} for r in parsed.get('resultList',{}).get('result',[])])))
    except Exception as e:
        receipt['error']=repr(e);print(json.dumps(receipt))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(request,QUERIES.items()))
