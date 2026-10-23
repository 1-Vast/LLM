"""Seal independent external-proposal review before cross-reading peer reviews."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('log/20261022/rsi_external_proposal_review')
paths = [root/'RECURSION_REVIEW.md',
    Path('C:/Users/59964/.codex/attachments/ad165509-4408-4a55-93da-65941cedc713/已粘贴的文本.txt'),
    root/'primary/aide2.txt', root/'primary/failure_feedback.txt']
receipt = dict(utc=datetime.now(timezone.utc).isoformat(),
    independent=True, other_new_role_reviews_read=False,
    new_requests_or_experiments=0,
    files=[dict(path=p.as_posix(), bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths])
(root/'RECURSION_REVIEW_SEAL.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(receipt['files'][0])
