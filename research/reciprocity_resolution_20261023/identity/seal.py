"""Seal the independent identity report before peer exposure."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/reciprocity_resolution/identity'
files = [OUT / 'INDEPENDENT.md', OUT / 'METADATA_AUDIT.json', Path(__file__).with_name('inspect_identity.py')]
seal = {'utc': datetime.now(timezone.utc).isoformat(), 'peer_reports_read': False,
        'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(OUT / 'INDEPENDENT_SEAL.json').write_text(json.dumps(seal, indent=2))
print(json.dumps(seal, indent=2))
