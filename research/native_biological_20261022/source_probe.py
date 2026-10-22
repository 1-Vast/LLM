from pathlib import Path
import requests,json,hashlib,datetime
out=Path('D:/MAESTRO/log/20261022/native_operation/biology')
query='TITLE_ABS:"Perturb-CITE-seq"'
u='https://www.ebi.ac.uk/europepmc/webservices/rest/search'
r=requests.get(u,params={'query':query,'format':'json','resultType':'core'},timeout=40)
p=out/'europepmc_search.json';p.write_bytes(r.content)
(out/'search_receipt.json').write_text(json.dumps({'url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
for a in r.json().get('resultList',{}).get('result',[]):
 print(a.get('title'),a.get('doi'),a.get('pmcid'),a.get('firstPublicationDate'))
 print(a.get('abstractText','')[:700])
