"""Compact exact source identities from preserved Europe PMC search responses."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/grounded_feedback_renewal/root'
label = sys.argv[1]
data = json.loads((OUT/(label+'.body')).read_text(encoding='utf-8'))
results = [{k: row.get(k) for k in ['title', 'doi', 'pmcid', 'id', 'firstPublicationDate', 'isOpenAccess']}
           for row in data['resultList']['result']]
record = dict(total=data.get('hitCount'), results=results)
(OUT/(label+'.index.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
