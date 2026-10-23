"""Seal the new CDK mechanism original before new source-role conclusions."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('log/20261022/next_mechanism/recursive/cdk_mechanism')
paths = [root/'INDEPENDENT.md', Path('log/20261022/next_mechanism/root/SOURCE_UPDATE.md'),
         Path('log/20261022/next_mechanism/root/literature/cdk_epmc.txt'), Path(__file__)]
receipt = dict(sealed_utc=datetime.now(timezone.utc).isoformat(),
    statement='New independent mechanism original sealed before reading new source/cdk_review or peer CDK conclusions.',
    files=[dict(path=p.as_posix(), bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths],
    new_experiments=0, biological_scalar_decode=False, new_http_requests=0)
(root/'SEAL.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(receipt['files'][0])
