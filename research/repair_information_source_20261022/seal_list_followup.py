"""Seal the exact-list follow-up and check original 20-file evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('D:/MAESTRO')
source = root / 'log/20261022/repair_information_opportunity/source'
out = source / 'list_followup'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
original = json.loads((source / 'SEAL.json').read_text(encoding='utf-8'))
verification = [dict(path=item['path'], unchanged=digest(root / item['path']) == item['sha256'])
                for item in original['files']]
assert len(verification) == 20 and all(item['unchanged'] for item in verification)
assert len(list(out.glob('request_*.receipt.json'))) == 2
paths = sorted(path for path in out.iterdir() if path.is_file() and path.name != 'SEAL.json')
paths += [source / 'SEAL.json', Path(__file__).resolve(),
          root / 'research/repair_information_source_20261022/list_followup.py']
record = dict(created_utc=datetime.now(timezone.utc).isoformat(), requests_used=2,
              original_verification=verification,
              disposition='NAMED_SAMPLE_METADATA_CANDIDATE_WITHOUT_PUBLIC_FILE_URL_INDEPENDENCE_UNKNOWN',
              files=[dict(path=str(path.relative_to(root)), bytes=path.stat().st_size,
                          sha256=digest(path)) for path in paths])
(out / 'SEAL.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(paths), original_unchanged=len(verification),
                      report_sha256=digest(out / 'RESULT.md'))))
