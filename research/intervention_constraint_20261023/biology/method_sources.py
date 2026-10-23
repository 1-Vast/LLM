"""Fetch pinned author method text without notebooks or numeric assay assets."""
from pathlib import Path
import hashlib
import json
import requests

out = Path('log/20261023/intervention_constraint/biology')
sha = json.loads((out / 'repo_tree.body').read_text())['sha']
paths = ['README.md', 'data/README.md', 'src/decipher/scores/interactions.py',
         'src/decipher/scores/aggregate.py', 'src/decipher/datasets/hierarchy.py',
         'scripts/scores/1_score_interactions.py', 'scripts/scores/3_select_hits.py']
receipts = []
for path in paths:
    url = f'https://raw.githubusercontent.com/samsonfong/SCHEMATIC/{sha}/{path}'
    r = requests.get(url, timeout=60)
    filename = 'author_' + path.replace('/', '_') + '.body'
    (out / filename).write_bytes(r.content)
    receipts.append(dict(path=path, commit=sha, url=url, status=r.status_code,
                         bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest()))
(out / 'METHOD_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
print(json.dumps(receipts, indent=2))
