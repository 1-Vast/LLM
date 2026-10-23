"""Seal the bounded full-PTDS metadata record without data-payload access."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('D:/MAESTRO')
out = root / 'log/20261022/repair_information_opportunity/source'
paths = sorted(path for path in out.iterdir() if path.is_file() and path.name != 'SEAL.json')
paths += sorted((root / 'research/repair_information_source_20261022').glob('*.py'))
receipts = [json.loads(path.read_text(encoding='utf-8')) for path in sorted(out.glob('request_*.receipt.json'))]
assert len(receipts) == 3
record = dict(created_utc=datetime.now(timezone.utc).isoformat(),
              requests_used=len(receipts), request_2_incomplete=True,
              no_matrix_or_outcome_opened=True,
              disposition='INDEPENDENCE_UNKNOWN_EXACT_METADATA_PATH_IDENTIFIED',
              files=[dict(path=str(path.relative_to(root)), bytes=path.stat().st_size,
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths])
(out / 'SEAL.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(paths), report_sha256=hashlib.sha256((out / 'FINAL_RESULT.md').read_bytes()).hexdigest())))
