from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path('D:/MAESTRO')
out = root / 'log/20261022/native_operation/biology'
paths = [
    out / 'INDEPENDENT_CROSS_CRITIQUE.md',
    out / 'INDEPENDENT_POSITION.md',
    out / 'INDEPENDENT_SEAL.json',
    root / 'log/20261022/native_operation/proposer/INDEPENDENT_INITIAL.md',
    root / 'log/20261022/native_operation/proposer/EXACT_FALSIFIER_RESULT.json',
    root / 'log/20261022/native_operation/improver/INDEPENDENT_INITIAL.md',
    root / 'log/20261022/native_operation/improver/OPERATION_CHECK.json',
    Path(__file__),
]
target = out / 'CROSS_CRITIQUE_SEAL.json'
assert not target.exists()
target.write_text(json.dumps({
    'utc': datetime.now(timezone.utc).isoformat(),
    'before_peer_debate_reads': True,
    'root_source_reading_not_read': True,
    'files': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in paths],
}, indent=2), encoding='utf8')
print(hashlib.sha256(target.read_bytes()).hexdigest())
