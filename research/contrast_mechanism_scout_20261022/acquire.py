"""Retain exact public primary-source HTTP bodies, metadata and search results."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
import hashlib
import json
import sys
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

OUT=Path('D:/MAESTRO/log/20261022/contrast_mechanism_scout/sources')
def fetch(label,url):
    receipt=dict(label=label,requested_url=url,utc=datetime.now(timezone.utc).isoformat())
    try:
        r=requests.get(url,timeout=60,headers={'User-Agent':'MAESTRO primary source qualification/1.0'})
        (OUT/(label+'.body')).write_bytes(r.content)
        receipt.update(status=r.status_code,final_url=r.url,headers=dict(r.headers),bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
        parser='xml' if 'xml' in r.headers.get('content-type','') else 'html.parser'
        if 'json' not in r.headers.get('content-type',''):
            (OUT/(label+'.txt')).write_text(BeautifulSoup(r.content,parser).get_text(' ',strip=True),encoding='utf-8')
    except Exception as e:receipt['error_type']=type(e).__name__
    (OUT/(label+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='headers'}),flush=True)

def search():
    queries=[
      ('compositional2025','submittedDate:[202501010000 TO 202512312359] AND (all:"compositional generalization" OR all:"counterfactual planning") AND (cat:cs.CV OR cat:cs.RO OR cat:cs.CL)'),
      ('compositional2026','submittedDate:[202601010000 TO 202610222359] AND (all:"compositional generalization" OR all:"counterfactual planning") AND (cat:cs.CV OR cat:cs.RO OR cat:cs.CL)'),
      ('intervention2026','submittedDate:[202501010000 TO 202610222359] AND (all:"drug discovery" OR all:"perturbation") AND (all:"active learning" OR all:"intervention" OR all:"synthetic lethality")'),
    ]
    for label,q in queries:
        fetch(label,'https://export.arxiv.org/api/query?'+urlencode(dict(search_query=q,max_results=10,sortBy='submittedDate',sortOrder='descending')))
    rows=[];ns={'a':'http://www.w3.org/2005/Atom'}
    for label,_ in queries:
        try:
            for item in ET.fromstring((OUT/(label+'.body')).read_bytes()).findall('a:entry',ns):
                rows.append(dict(source=label,**{k:item.findtext('a:'+k,namespaces=ns) for k in ['id','title','published','updated','summary']}))
        except Exception as e:rows.append(dict(source=label,error_type=type(e).__name__))
    (OUT.parent/'SEARCH_RESULTS.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
if __name__=='__main__':
    if len(sys.argv)==1:search()
    else:fetch(sys.argv[1],sys.argv[2])
