"""Seal the cross-review and verify the independent original stayed intact."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('log/20261022/rsi_external_proposal_review')
expected = '8e2bfec984dd23517195afc3cd5aeb2e4b56615d580d211c7acfadc4bfe38b82'
assert hashlib.sha256((root/'RECURSION_REVIEW.md').read_bytes()).hexdigest() == expected
paths = [root/name for name in ['CROSS_RECURSION.md', 'NOVELTY_REVIEW.md', 'DATA_REVIEW.md']]
receipt = dict(utc=datetime.now(timezone.utc).isoformat(), independent_original_preserved=expected,
    files=[dict(path=p.as_posix(), bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths],
    actual_peer_reply='frontier_distinct', new_experiments=0, new_requests=0)
(root/'CROSS_RECURSION_SEAL.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(receipt['files'][0])
