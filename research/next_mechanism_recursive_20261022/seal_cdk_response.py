"""Preserve the CDK original and bind its observation-law clarification."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('log/20261022/next_mechanism/recursive/cdk_mechanism')
original = root/'INDEPENDENT.md'
expected = 'bb4142bc58adc7f7a47b66fa3b23919e3d93692bb7a2cfe536caca7be2f13baa'
assert hashlib.sha256(original.read_bytes()).hexdigest() == expected
response = root/'OBSERVATION_LAW_RESPONSE.md'
receipt = dict(utc=datetime.now(timezone.utc).isoformat(), original_preserved_sha256=expected,
    response_sha256=hashlib.sha256(response.read_bytes()).hexdigest(),
    response_bytes=response.stat().st_size, new_experiments=0, biological_scalar_decode=False)
(root/'OBSERVATION_LAW_SEAL.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
