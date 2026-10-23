"""Seal the append-only identity result and verify all original source files."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('D:/MAESTRO')
out = root / 'log/20261022/next_mechanism/source/cdk_review'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
original = json.loads((out / 'ADDENDUM_SEAL.json').read_text(encoding='utf-8'))
verification = [dict(path=item['path'], unchanged=digest(root / item['path']) == item['sha256'])
                for item in original['files']]
assert all(item['unchanged'] for item in verification)
paths = [out / name for name in ['S4_PROTOCOL.md', 'S4_ADDENDUM.md', 'table_s4.body',
                                 'table_s4.receipt.json', 'TABLE_S4_HEADERS.json', 'ADDENDUM_SEAL.json']]
paths += [root / 'research/next_mechanism_source_20261022/qualify_cdk_s4.py', Path(__file__).resolve()]
record = dict(created_utc=datetime.now(timezone.utc).isoformat(),
              scope='Append-only S4 labels only; numerical cells suppressed.',
              original_verification=verification,
              files=[dict(path=str(path.relative_to(root)), bytes=path.stat().st_size,
                          sha256=digest(path)) for path in paths])
(out / 'S4_SEAL.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(paths), original_files_unchanged=len(verification),
                      report_sha256=digest(out / 'S4_ADDENDUM.md'))))
