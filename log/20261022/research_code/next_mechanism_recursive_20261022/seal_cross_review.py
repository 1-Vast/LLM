"""Check independent-file preservation and seal the postseal discussion."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('log/20261022/next_mechanism/recursive')
original = json.loads((root/'INDEPENDENT_SEAL.json').read_text(encoding='utf-8'))
checks = []
for row in original['files']:
    p = Path(row['path'])
    checks.append(dict(path=row['path'], matches=p.is_file() and p.stat().st_size == row['bytes']
                      and hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256']))
assert all(x['matches'] for x in checks)
path = root/'CROSS_REVIEW.md'
receipt = dict(utc=datetime.now(timezone.utc).isoformat(),
    cross_review_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    cross_review_bytes=path.stat().st_size, original_preservation=checks,
    new_experiments=0, biological_response_decode=False)
(root/'CROSS_REVIEW_SEAL.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(dict(original_entries_preserved=len(checks),
    cross_review_sha256=receipt['cross_review_sha256'], new_experiments=0), indent=2))
