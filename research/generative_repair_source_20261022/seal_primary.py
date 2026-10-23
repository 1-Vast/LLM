"""Seal the independent text-only PTV source conclusion before archive follow-up."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('D:/MAESTRO')
out = root / 'log/20261022/generative_repair_renewal/source'
paths = sorted(path for path in out.iterdir() if path.is_file() and path.name != 'INDEPENDENT_SEAL.json')
paths += sorted((root / 'research/generative_repair_source_20261022').glob('*.py'))
record = dict(created_utc=datetime.now(timezone.utc).isoformat(),
              scope='Independent existing primary text and exact DOI metadata; no matrix/table outcomes',
              files=[dict(path=str(path.relative_to(root)), bytes=path.stat().st_size,
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths])
(out / 'INDEPENDENT_SEAL.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(paths), report_sha256=hashlib.sha256((out / 'INDEPENDENT.md').read_bytes()).hexdigest())))
