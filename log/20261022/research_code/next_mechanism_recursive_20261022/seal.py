"""Bind the independent original before cross-reading or debate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('log/20261022/next_mechanism/recursive')
code = Path('research/next_mechanism_recursive_20261022')
paths = sorted([p for p in root.iterdir() if p.is_file() and p.name != 'INDEPENDENT_SEAL.json']
               + list(code.glob('*.py')))
seal = dict(sealed_utc=datetime.now(timezone.utc).isoformat(),
    statement='Independent original sealed before peer new conclusions were read or scientific conclusions sent.',
    files=[dict(path=p.as_posix(), bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths])
(root/'INDEPENDENT_SEAL.json').write_text(json.dumps(seal, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(paths), independent_sha256=hashlib.sha256((root/'INDEPENDENT.md').read_bytes()).hexdigest()), indent=2))
