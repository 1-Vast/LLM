"""Seal completed CDK debate without changing either original receipt."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('log/20261022/next_mechanism/recursive/cdk_mechanism')
expected = {
    'INDEPENDENT.md': 'bb4142bc58adc7f7a47b66fa3b23919e3d93692bb7a2cfe536caca7be2f13baa',
    'OBSERVATION_LAW_RESPONSE.md': '5687fbd59dd58b97e618ac2410ce42a0f66a933ff02280f868fff5d2ea5884a4',
}
for name, digest in expected.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest
path = root/'CROSS_REVIEW.md'
receipt = dict(utc=datetime.now(timezone.utc).isoformat(), preserved=expected,
    cross_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    cross_bytes=path.stat().st_size, new_experiments=0, biological_scalar_decode=False,
    actual_peer_responses=['frontier_distinct', 'fm03_chronology'])
(root/'CROSS_SEAL.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
