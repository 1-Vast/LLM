"""Extract repository file identities only, not molecular values."""
from pathlib import Path
import collections
import hashlib
import json
import re

OUT=Path(__file__).resolve().parents[2]/'log/20261022/decrypte_feedback_pilot/molecular'
raw=(OUT/'massive_files.body').read_bytes()
match=re.search(r'var dataset_files = (\{.*?\});',raw.decode(),re.S)
data=json.loads(match.group(1))
rows=data['row_data']
(OUT/'FILELIST.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
groups=collections.Counter('/'.join(r['relative_path'].split('/')[:2]) for r in rows)
selected=[r for r in rows if r['collection']=='metadata' or (r['collection']=='other' and any(s in r['name'].lower() for s in ['all.txt','rds','csv','xlsx','rdata']))]
(OUT/'PROCESSED_IDENTITIES.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
(OUT/'FILELIST_SUMMARY.json').write_text(json.dumps({'body_sha256':hashlib.sha256(raw).hexdigest(),'total':len(rows),'groups':dict(groups),'selected':len(selected)},indent=2),encoding='utf-8')
print(json.dumps({'total':len(rows),'groups':dict(groups),'selected':len(selected)},indent=2))
for r in selected[:12]:
    print(r['file_descriptor'],r['size'])
