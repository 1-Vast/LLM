"""Seal independent result interpretation before peer result exposure."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/reciprocity_resolution/identity'
files = [OUT / 'RESULT_REVIEW.md', OUT / 'RESULT_CHECK.json', Path(__file__).with_name('check_result.py')]
record = {'utc': datetime.now(timezone.utc).isoformat(), 'peer_result_review_read': False,
          'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(OUT / 'RESULT_REVIEW_SEAL.json').write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
