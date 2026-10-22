"""Retain selected primary full texts/author metadata after bounded index screening."""
import hashlib,json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/post_rna_mechanism_renewal/primary'
SOURCES={
 'labcompass_doi':'https://doi.org/10.64898/2026.10.07.756550',
 'labcompass_author_metadata':'https://api.biorxiv.org/details/biorxiv/2026.10.07.756550',
 'resolution_doi':'https://doi.org/10.64898/2026.09.30.755756',
 'resolution_author_metadata':'https://api.biorxiv.org/details/biorxiv/2026.09.30.755756',
 'caf_fulltext':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13680625/fullTextXML',
 'subcellpert_readme':'https://raw.githubusercontent.com/king159/SubcellPert/main/README.md'}

def fetch(item):
    name,url=item;rct=dict(url=url,method='GET',utc_started=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(url,timeout=45);raw=r.content
        with (P/(name+'.body')).open('xb') as f:f.write(raw)
        rct.update(status=r.status_code,final_url=r.url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=r.headers.get('Content-Type'),outcome='BODY_RETAINED_REQUIRES_CONTENT_INSPECTION')
    except Exception as e:rct.update(outcome='FAILED_RETAINED',error_type=type(e).__name__)
    rct['utc_finished']=datetime.now(timezone.utc).isoformat()
    with (P/(name+'.http.json')).open('x',encoding='utf-8') as f:json.dump(rct,f,indent=2)
    return dict(name=name,**rct)

def main():
    P.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(fetch,SOURCES.items()):print(json.dumps(result),flush=True)

if __name__=='__main__':main()
