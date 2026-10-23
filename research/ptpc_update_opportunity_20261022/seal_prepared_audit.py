"""Seal independent data audit and the parser-dependency repair record."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import lxml
import numpy

root = Path('D:/MAESTRO')
out = root/'log/20261022/ptpc_update_opportunity/source'
code = root/'research/ptpc_update_opportunity_20261022'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
paths = [out/name for name in ('BASELINE_PREPARED_AUDIT.json', 'BASELINE_AUDIT_ATTEMPTS.md', 'AUDIT_DEPENDENCY_INSTALL.log')]
paths += [code/'audit_baseline_prepared.py', Path(__file__).resolve()]
audit = json.loads(paths[0].read_text())
assert audit['status'] == 'PASS' and audit['audit_script_sha256'] == sha(code/'audit_baseline_prepared.py')
seal = out/'BASELINE_PREPARED_AUDIT_SEAL.json'
assert not seal.exists()
seal.write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
    lxml_version=lxml.__version__, numpy_version=numpy.__version__,
    files=[dict(path=str(p.relative_to(root)), bytes=p.stat().st_size, sha256=sha(p)) for p in paths]), indent=2), encoding='utf-8')
print(json.dumps(dict(audit_sha256=sha(paths[0]), seal_sha256=sha(seal), lxml_version=lxml.__version__)))
