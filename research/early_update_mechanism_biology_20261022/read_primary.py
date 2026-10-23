"""Inspect publication text metadata only."""
from pathlib import Path
import json

out=Path('D:/MAESTRO/log/20261022/early_update_mechanism/biology')
result={}
for path in sorted(out.glob('*_epmc.body')):
    body=json.loads(path.read_text(encoding='utf-8'))
    result[path.stem]=[dict(title=r.get('title'),doi=r.get('doi'),pmcid=r.get('pmcid'),isOpenAccess=r.get('isOpenAccess'),
        abstract=r.get('abstractText'),fullTextUrlList=r.get('fullTextUrlList'),firstPublicationDate=r.get('firstPublicationDate'))
        for r in body['resultList']['result']]
target=out/'PRIMARY_LOCATIONS.json'
assert not target.exists()
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
