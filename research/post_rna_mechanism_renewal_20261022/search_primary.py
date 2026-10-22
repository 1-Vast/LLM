"""Bounded primary-index discovery after RNA STOP; metadata is not data qualification."""
import hashlib,json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/post_rna_mechanism_renewal/sources'
QUERIES={
 'paired_function':'("single-cell" OR transcriptomic OR "cell state") AND (drug OR compound) AND (viability OR fitness OR secretion) AND (perturbation OR screening) AND FIRST_PDATE:[2025-01-01 TO 2026-10-22]',
 'adaptive_function':'("cell state" OR "virtual cell") AND ("closed-loop" OR "active learning" OR "experimental design") AND (drug OR treatment OR perturbation) AND FIRST_PDATE:[2025-01-01 TO 2026-10-22]',
 'paired_assay':'(transcriptome OR transcriptomic OR morphology) AND ("paired" OR "multimodal") AND viability AND perturbation AND FIRST_PDATE:[2023-01-01 TO 2026-10-22]',
 'latest_perturbation':'("perturbation model" OR "virtual cell" OR "cellular world model") AND FIRST_PDATE:[2026-10-01 TO 2026-10-22]'}

def search(item):
    name,query=item;receipt=dict(utc_started=datetime.now(timezone.utc).isoformat(),query=query,method='GET',status='NOT_SENT')
    try:
        r=requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',params=dict(query=query,format='json',resultType='core',pageSize=25,sort='FIRST_PDATE_D desc'),timeout=45)
        body=r.content
        with (P/(name+'.body')).open('xb') as f:f.write(body)
        receipt.update(status=r.status_code,url=r.url,final_url=r.url,bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        r.raise_for_status();payload=r.json()
        rows=[{k:row.get(k) for k in ['id','source','pmcid','doi','title','firstPublicationDate','authorString','abstractText']} for row in payload['resultList']['result']]
        with (P/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(dict(hit_count=payload.get('hitCount'),results=rows),f,ensure_ascii=False,indent=2)
        receipt.update(outcome='INDEX_RETAINED_NOT_FULL_TEXT_OR_DATA_QUALIFIED',hit_count=payload.get('hitCount'))
    except Exception as e:receipt.update(outcome='FAILED_RETAINED',error_type=type(e).__name__)
    receipt['utc_finished']=datetime.now(timezone.utc).isoformat()
    with (P/(name+'.http.json')).open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    return dict(query=name,outcome=receipt['outcome'],hit_count=receipt.get('hit_count'))

def main():
    P.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(search,QUERIES.items()):print(json.dumps(result),flush=True)

if __name__=='__main__':main()
