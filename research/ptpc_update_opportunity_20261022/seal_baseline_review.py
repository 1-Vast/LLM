"""Seal independent protocol review without reading abundance or predictions."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('D:/MAESTRO')
out = root/'log/20261022/ptpc_update_opportunity/source'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
paths = [out/'BASELINE_PROTOCOL_REVIEW.md', Path(__file__).resolve()]
seal = out/'BASELINE_PROTOCOL_REVIEW_SEAL.json'
assert not seal.exists()
record = dict(created_utc=datetime.now(timezone.utc).isoformat(),
              reviewed_protocol_path='log/20261022/ptpc_update_opportunity/DEVELOPMENT_BASELINE_PROTOCOL.md',
              reviewed_protocol_sha256='691e414a2efdfb89954214900a1c1ec75ecb3f977170c10a7c09311746f9b2f8',
              reviewed_label_gate_seal_sha256=sha(out/'LABEL_GATE_SEAL.json'),
              abundance_or_predictions_read=False, mechanism_drafts_read=False,
              files=[dict(path=str(p.relative_to(root)), sha256=sha(p)) for p in paths])
seal.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(report_sha256=sha(paths[0]), seal_sha256=sha(seal))))
