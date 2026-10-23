"""Seal the independent CDK metadata-only source result before peer reading."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
root=Path('D:/MAESTRO')
out=root/'log/20261022/next_mechanism/source/cdk_review'
paths=sorted(p for p in out.iterdir() if p.is_file())
paths.extend([root/'research/next_mechanism_source_20261022/qualify_cdk.py',Path(__file__).resolve()])
record={'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'Independent primary source and Table S3 header review; no peer new CDK conclusions read.',
        'files':[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
(out/'ADDENDUM_SEAL.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({'files':len(paths),'report_sha256':hashlib.sha256((out/'ADDENDUM.md').read_bytes()).hexdigest()}))
