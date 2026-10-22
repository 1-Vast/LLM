"""Preserve independently sealed source originals and bind the later exchange."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path('D:/MAESTRO')
out = root/'log/20261022/next_mechanism/source'
original = json.loads((out/'INDEPENDENT_SEAL.json').read_text(encoding='utf-8'))
checks = []
for entry in original['files']:
    path = root/entry['path']
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    checks.append({'path':entry['path'],'unchanged':sha == entry['sha256'] and path.stat().st_size == entry['bytes']})
assert all(c['unchanged'] for c in checks)
paths = [out/'CROSS_REVIEW.md',out/'INDEPENDENT_SEAL.json',Path(__file__).resolve(),
         root/'log/20261022/next_mechanism/root/OPPOSING_POSITION.md',
         root/'log/20261022/next_mechanism/recursive/INDEPENDENT.md',
         root/'log/20261022/next_mechanism/root/literature/weak_pde.txt',
         root/'log/20261022/next_mechanism/root/literature/wound_names.json']
record = {'created_utc':datetime.now(timezone.utc).isoformat(),'original_preservation':checks,
          'bindings':[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,
                       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
          'scope':'Actual postseal cross-review and source/recursive exchange, no new experimental result.'}
(out/'CROSS_REVIEW_SEAL.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({'originals_unchanged':len(checks),'cross_review_sha256':record['bindings'][0]['sha256']}))
